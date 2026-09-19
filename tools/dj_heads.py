#!/usr/bin/env python3
"""Phase 3b of djachenko/PLAN.md, step 1: the page text from the witnesses, on top of scan A's segmentation.

    python3 tools/dj_heads.py                      # every main/supplement page not yet done (parallel; resumable)
    python3 tools/dj_heads.py --pages 45,517-520   # these leaves (add --force to redo pages already done)
    python3 tools/dj_heads.py --show 45 7          # A / D / B / merged text of paragraph 7 of leaf 45
    python3 tools/dj_heads.py --report             # what is done, and the totals, from ocr/*.json

Why (eval/RESULTS.md): Google's text layer of witness D (Cornell copy) reads the civil text at 1.5 % CER against
ABBYY's 3.8 % on A and has both margins on every page, while A's geometry segments the entries almost perfectly. Where
D and B agree (95 % of characters) the text is right in 99.9 %; where they disagree, a vote with A decides.

Per page (leaf of scan A, main and supplement only):
  1. A's paragraphs (ocr/NNNN.json) are joined to one text per column side (left a, right b) with their offsets.
  2. D's, B's and C's body text is rebuilt from their word boxes (dj_witness.reading_order), also per side —
     everything below runs per side, so that a page split into bands differently by a witness cannot matter.
  3. A is aligned to D (Levenshtein on the "norm" level); every paragraph start of A is carried to D and snapped to
     the nearest line start of D within CUT_TOL characters (a paragraph always starts a printed line, and the
     headword — where A is least reliable — is exactly what the alignment gets wrong). D's text is cut there.
  4. B, A and C are aligned to D; per character, if B differs from D, A reads like B and C does not confirm D,
     B's reading replaces D's ("fixed"); every other place where B differs from D stays D's but is "disputed".
  5. Written into the page JSON, per paragraph: text_d (D's raw text), text_merged (after the vote), disputed
     (spans [start, end) in text_merged where D and B disagree), fixed (count), d_cut ("line" snapped to a D line
     start, "aligned" not snapped, "forced" pushed to keep the order), d_line (box of the paragraph's first line
     in D, 600 ppi pixels — for the headword crops of step 2); and per page: witness {version, d_page, b_page,
     c_page, chars, cuts, disputed, fixed, odd = [col, para, length ratio] of paragraphs whose D text is much
     shorter or longer than A's}. dj_abbyy.py carries all of this over when it regenerates a page.
Resumable: a page whose witness.version is current is skipped; each page is written atomically. Rerunning is safe.
"""
import argparse, bisect, json, re, sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import (OCR, PDF_DPI, align, b_page, c_page, d_page, join_lines, load_page, norm_seq,  # noqa: E402
                        page_text, side_texts)
import dj_abbyy  # noqa: E402  (dump, iou)

VERSION = 4            # of the witness block; bump to redo every page (4 = per-side alignment; mixed lines for C, D)
CUT_TOL = 15           # characters: how far a paragraph start may move to reach a line start of D
PARA_KEYS = ('text_d', 'text_merged', 'disputed', 'fixed', 'd_cut', 'd_line')


# ---------------------------------------------------------------- A

def a_paragraphs(pg, side):
    """-> (text of A's paragraphs on one column side, top to bottom, [dict(col, para, start, text, hanging)]):
    paragraphs joined with a space, a hyphenated paragraph end joined to a continuation (as dj_eval.cand_abbyy_A)."""
    text, paras = '', []
    for ci, c in enumerate(pg['columns']):
        if c['side'] != side:
            continue
        for pi, p in enumerate(c['paragraphs']):
            para = join_lines(ln['text'] for ln in p['lines']).replace('￼', '')
            if para:
                if text and not (text.endswith(('-', '¬')) and not p['hanging']):
                    text += ' '
                elif text:
                    text = text[:-1]
            paras.append(dict(col=ci, para=pi, start=len(text), text=para, hanging=p['hanging']))
            text += para
    return text, paras


# ---------------------------------------------------------------- cutting D at A's paragraph starts

def cut_positions(a_text, paras, d_text, d_lines):
    """-> [(raw offset in d_text, how)] for every paragraph of A, non-decreasing."""
    a_seq, a_idx = norm_seq(a_text)
    d_seq, d_idx = norm_seq(d_text)
    if not a_seq or not d_seq:
        return [(0, 'forced')] * len(paras)
    _, _, j_at = align(a_seq, d_seq)
    line_starts = sorted(l['start'] for l in d_lines)
    cuts, prev = [], 0
    for p in paras:
        if not p['text']:
            cuts.append((prev, 'forced'))
            continue
        i = bisect.bisect_left(a_idx, p['start'])
        if i >= len(a_seq):
            raw = len(d_text)
        else:
            j = j_at[i]
            raw = d_idx[j] if j < len(d_seq) else len(d_text)
        k = bisect.bisect_left(line_starts, raw)
        near = [ls for ls in line_starts[max(0, k - 1):k + 1] if abs(ls - raw) <= CUT_TOL]
        if near:
            raw, how = min(near, key=lambda ls: (abs(ls - raw), ls > raw)), 'line'
        else:
            # not at a line start: at least start at a word boundary
            while raw > 0 and raw < len(d_text) and not d_text[raw - 1].isspace():
                raw -= 1
            how = 'aligned'
        if raw < prev:
            raw, how = prev, 'forced'
        cuts.append((raw, how))
        prev = raw
    return cuts


# ---------------------------------------------------------------- the vote

def merge(d_text, b_text, a_text, c_text):
    """-> (merged text, out_at, disputed): out_at[r] = offset in the merged text of D's raw index r (len(d_text)+1
    entries); disputed = [(start, end, fixed)] in merged coordinates, one per place where B differs from D — fixed
    means B's reading replaced D's (the span is then B's text, possibly empty). A fix needs B and A to agree AND C
    not to confirm D: A and B are both FineReader and share the CS-type confusions (и/н, а/л, . for ,), C and D
    are both Google; two engines against two is a tie, and Google measured better (eval/RESULTS.md). Two exceptions
    where Google is systematically weak and the FineReader pair was right 19:0 and 9:3 on the ground truth: the "="
    after the headword (Google reads a third of them) and final ъ/ь."""
    d_seq, d_idx = norm_seq(d_text)
    n = len(d_seq)

    def readings_of(text):
        """Per norm position of D: the witness's reading there, normalised and raw."""
        seq, idx = norm_seq(text)
        if not n or not seq:
            return [''] * n, [''] * n
        _, _, j_at = align(d_seq, seq)
        norm, raw = [], []
        for k in range(n):
            j0 = j_at[k]
            j1 = j_at[k + 1] if k + 1 < n else len(seq)
            norm.append(''.join(seq[j0:j1]) if j1 > j0 else '')
            raw.append(text[idx[j0]:idx[j1 - 1] + 1] if j1 > j0 else '')
        return norm, raw

    rB, rawB = readings_of(b_text)
    rA, _ = readings_of(a_text)
    rC, _ = readings_of(c_text)
    pieces, piece_at, flagged = [], [0] * (len(d_text) + 1), []
    pos = k = 0
    while k < n:
        r = d_idx[k]
        k1 = k
        while k1 < n and d_idx[k1] == r:          # one raw character can carry two norm characters (ѿ -> от)
            k1 += 1
        while pos < r:                            # whitespace and other characters without a norm form
            piece_at[pos] = len(pieces)
            pieces.append(d_text[pos])
            pos += 1
        piece_at[r] = len(pieces)
        dn, bn, an, cn = (''.join(x[k:k1]) for x in (d_seq, rB, rA, rC))
        if bn == dn:
            pieces.append(d_text[r])
        elif bn == an and (cn != dn or ('=' in bn and '=' not in dn) or {bn, dn} == {'ъ', 'ь'}):
            flagged.append((len(pieces), True))
            pieces.append(''.join(rawB[k:k1]))
        else:
            flagged.append((len(pieces), False))
            pieces.append(d_text[r])
        pos, k = r + 1, k1
    while pos < len(d_text):
        piece_at[pos] = len(pieces)
        pieces.append(d_text[pos])
        pos += 1
    piece_at[len(d_text)] = len(pieces)
    offs, acc = [], 0
    for s in pieces:
        offs.append(acc)
        acc += len(s)
    offs.append(acc)
    return ''.join(pieces), [offs[i] for i in piece_at], [(offs[i], offs[i + 1], f) for i, f in flagged]


# ---------------------------------------------------------------- one page

def build_page(leaf, pg=None):
    pg = pg or load_page(leaf)
    W = {name: side_texts(page_text(name, leaf)) for name in 'DBC'}
    k = PDF_DPI / 72
    stats = dict(line=0, aligned=0, forced=0)
    n_disputed = n_fixed = n_chars = 0
    odd = []                                   # paragraphs whose D text is much shorter/longer than A's
    for side in 'ab':
        a_text, paras = a_paragraphs(pg, side)
        D, B, C = (W[n][side] for n in 'DBC')
        d_text = D['text']
        n_chars += len(d_text)
        cuts = cut_positions(a_text, paras, d_text, D['lines'])
        merged, out_at, disputed = merge(d_text, B['text'], a_text, C['text'])
        n_disputed += len(disputed)
        n_fixed += sum(1 for _, _, f in disputed if f)
        line_at = {l['start']: l for l in D['lines']}
        build_side(pg, paras, cuts, d_text, merged, out_at, disputed, line_at, k, stats, odd)
    pg['witness'] = dict(version=VERSION, d_page=d_page(leaf), b_page=b_page(leaf), c_page=list(c_page(leaf)[1:]),
                         chars=n_chars, cuts=stats, disputed=n_disputed, fixed=n_fixed, odd=odd)
    return pg


def build_side(pg, paras, cuts, d_text, merged, out_at, disputed, line_at, k, stats, odd):
    """Write the per-paragraph results of one column side into the page; odd collects [col, para, ratio] for
    paragraphs whose merged text is < 0.75 or > 1.35 times the length of A's (a mis-cut, or a headword Google
    did not read at all)."""
    for i, (p, (raw, how)) in enumerate(zip(paras, cuts)):
        raw_end = cuts[i + 1][0] if i + 1 < len(cuts) else len(d_text)
        m0, m1 = out_at[raw], out_at[raw_end]
        mseg = merged[m0:m1]
        base = m0 + len(mseg) - len(mseg.lstrip())
        mseg = mseg.strip()
        spans, fixed = [], 0
        for s, e, f in disputed:
            if not (base <= s < base + len(mseg) or (s == e == base + len(mseg) and s > base)):
                continue
            s, e = s - base, min(e, base + len(mseg)) - base
            fixed += f
            if spans and s <= spans[-1][1]:
                spans[-1][1] = max(spans[-1][1], e)
            else:
                spans.append([s, e])
        par = pg['columns'][p['col']]['paragraphs'][p['para']]
        par['text_d'] = d_text[raw:raw_end].strip()
        par['text_merged'] = mseg
        par['disputed'] = spans
        par['fixed'] = fixed
        par['d_cut'] = how
        ln = line_at.get(raw)
        par['d_line'] = [round(ln['x0'] * k), round(ln['y0'] * k), round(ln['x1'] * k), round(ln['y1'] * k)] \
            if ln else None
        stats[how] += 1
        la, lm = len(p['text'].replace(' ', '')), len(mseg.replace(' ', ''))
        if la >= 30 and not 0.75 <= lm / la <= 1.35:
            odd.append([p['col'], p['para'], round(lm / la, 2)])


def write_page(leaf, pg):
    path = OCR / f'{leaf:04d}.json'
    tmp = path.with_suffix('.tmp')
    tmp.write_text(dj_abbyy.dump(pg), encoding='utf-8')
    tmp.rename(path)


def process(leaf):
    try:
        pg = load_page(leaf)
        pg = build_page(leaf, pg)
        write_page(leaf, pg)
        w = pg['witness']
        return leaf, f"{w['cuts']} disputed {w['disputed']} fixed {w['fixed']}"
    except Exception as e:                      # noqa: BLE001 — one bad page must not stop the run
        return leaf, f'ERROR {type(e).__name__}: {e}'


# ---------------------------------------------------------------- CLI

def parse_ranges(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-')
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def todo(force=False):
    leaves = []
    for f in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] not in ('main', 'supplement'):
            continue
        if force or pg.get('witness', {}).get('version') != VERSION:
            leaves.append(pg['idx'])
    return leaves


def show(leaf, para_no):
    pg = load_page(leaf)
    k = 0
    for c in pg['columns']:
        for p in c['paragraphs']:
            k += 1
            if k != para_no:
                continue
            print('A      :', join_lines(ln['text'] for ln in p['lines']))
            print('D      :', p.get('text_d'))
            m = p.get('text_merged') or ''
            marks = list(m)
            for s, e in reversed(p.get('disputed') or []):
                marks.insert(e, '⟩')
                marks.insert(s, '⟨')
            print('merged :', ''.join(marks))
            print('cut', p.get('d_cut'), 'd_line', p.get('d_line'), 'hanging', p['hanging'])
            return
    print('no such paragraph')


def report():
    done = tot_par = tot_disp = tot_fixed = 0
    cuts = dict(line=0, aligned=0, forced=0)
    pages = 0
    for f in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] not in ('main', 'supplement'):
            continue
        pages += 1
        w = pg.get('witness')
        if not w or w.get('version') != VERSION:
            continue
        done += 1
        for k in cuts:
            cuts[k] += w['cuts'][k]
        tot_par += sum(w['cuts'].values())
        tot_disp += w['disputed']
        tot_fixed += w['fixed']
    print(f'{done}/{pages} pages have witness text (version {VERSION}); {tot_par} paragraphs, cuts {cuts}; '
          f'{tot_disp} disputed places, {tot_fixed} fixed by B+A')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--pages', help='leaves, e.g. 45,517-520 (default: all main/supplement pages not yet done)')
    ap.add_argument('--force', action='store_true', help='redo pages that are already done')
    ap.add_argument('--show', nargs=2, type=int, metavar=('LEAF', 'PARA'))
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    if a.show:
        show(*a.show)
        return
    if a.report:
        report()
        return
    if a.pages:
        leaves = parse_ranges(a.pages)
        if not a.force:
            pending = set(todo())
            leaves = [l for l in leaves if l in pending]
    else:
        leaves = todo(a.force)
    print(f'{len(leaves)} pages to do')
    errors = 0
    with Pool(a.workers) as pool:
        for n, (leaf, msg) in enumerate(pool.imap_unordered(process, leaves), 1):
            if msg.startswith('ERROR'):
                errors += 1
            if msg.startswith('ERROR') or n % 50 == 0 or n == len(leaves):
                print(f'[{n}/{len(leaves)}] leaf {leaf}: {msg}', flush=True)
    print(f'done; {errors} errors')
    report()


if __name__ == '__main__':
    main()
