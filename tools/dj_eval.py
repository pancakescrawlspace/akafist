#!/usr/bin/env python3
"""Phase 2 of djachenko/PLAN.md: score OCR candidates against the hand-made ground truth in djachenko/eval/gt/.

    python3 tools/dj_eval.py                  # extract all candidates, score them, write eval/results.tsv + print
    python3 tools/dj_eval.py --show google_D 660     # aligned differences for one candidate and one GT leaf
    python3 tools/dj_eval.py --show abbyy_A 660 --zone hw

Candidates (text per page in reading order, cached in djachenko/eval/cand/<name>/NNNN.txt, NNNN = leaf of scan A):
    abbyy_A    archive.org's ABBYY layer of scan A, in the reading order of ocr/NNNN.json (Phase 3a)
    djvu_B     the hidden text layer of the 1993 reprint's DjVu (witness B; the uploader's FineReader OCR)
    google_D   Google's text layer of the Cornell PDF (witness D)
    google_C   Google's text layer of the Indiana PDFs (witness C)
For B, C and D the reading order is rebuilt from word coordinates: gutter, header/footer, bands split by headings.

Scores (edit distance after alignment; whitespace is ignored throughout):
    strict   NFC text as printed (markup of the GT removed)
    norm     + dashes and quotes unified, CS letters mapped to civil ones (ѡ→о, ꙋ/оу/ү→у, ѧ/ꙗ/ѩ→я, ѫ→у, …),
             Latin look-alikes mapped to Cyrillic, diacritics removed (so Greek accents do not count)
Zones of the GT: hw = the headword of each entry (first {…}, or the text before "=", "—", "(" if not CS type),
grc = Greek letters, def = everything else. Per zone: CER = edits charged to that zone / GT characters in it;
hw_exact = share of headwords read exactly (norm). For abbyy_A also the entry segmentation: GT entry starts found
among the hanging paragraphs of ocr/*.json (recall) and hanging paragraphs that are GT entry starts (precision).
"""
import argparse, glob, html, json, re, subprocess, sys, unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DJ = ROOT / 'djachenko'
EVAL, OCR = DJ / 'eval', DJ / 'ocr'
GT_DIR, CAND_DIR = EVAL / 'gt', EVAL / 'cand'
REPRINT = DJ / 'scan' / 'reprint1993' / 'Dyachenko G., Polnyj cerkovnoslavyanskij slovar (M., 1993, 1159p).djvu'
CORNELL = DJ / 'scan' / 'google' / 'google_cornell.pdf'
INDIANA = (DJ / 'scan' / 'google' / 'google_indiana_v1.pdf', DJ / 'scan' / 'google' / 'google_indiana_v2.pdf')
OFFSET = 37                                   # printed page = leaf of scan A - 37


def page_of(leaf):
    return leaf - OFFSET


# ---------------------------------------------------------------- ground truth

GREEK = re.compile(r'[Ͱ-Ͽἀ-῿]')


def parse_gt(path):
    """-> list of (char, zone, entry_start) for the page in reading order, and the list of headword spans."""
    out = []
    for raw in path.read_text(encoding='utf-8').splitlines():
        if not raw.strip() or raw.startswith(('#', '@')):
            continue
        cont = raw.startswith('+ ')
        line = raw[2:] if cont else raw
        line = line.replace('[?]', '')
        # headword span (in the line with markup)
        hw_end = 0
        if not cont:
            if line.startswith('{'):
                hw_end = line.index('}') + 1
            else:
                m = re.search(r'=|—|–|\s-\s|\(', line)
                hw_end = m.start() if m else len(line)
        chars = []
        for k, ch in enumerate(line):
            if ch in '{}‹›':
                continue
            zone = 'hw' if k < hw_end else 'grc' if GREEK.match(ch) else 'def'
            chars.append([ch, zone, False])
        if not cont:
            first = next((c for c in chars if not c[0].isspace()), None)
            if first:
                first[2] = True
        if out:
            out.append([' ', 'def', False])
        out.extend(chars)
    return out


# ---------------------------------------------------------------- candidates

FOOT_RE = re.compile(r'Ц[еѳe]рк\W{0,3}сла|словарь,?\s*свящ|Дьяченко\.?$', re.I)


def join_lines(lines):
    """Lines of one column/band -> text; a hyphen (or ¬) at a line end joins the word."""
    out = ''
    for t in lines:
        t = t.strip()
        if not t:
            continue
        if out.endswith(('-', '¬', '‐')) and not out.endswith(' -'):
            out = out[:-1] + t
        else:
            out = (out + ' ' + t) if out else t
    return out


def reading_order(words, W, H):
    """words: [(text, x0, y0, x1, y1)] top-left origin -> (text, starts) with the body text in reading order:
    band by band, left column before right; header, footer and full-width headings left out. `starts` is empty
    (generic witnesses carry no paragraph structure)."""
    words = [w for w in words if w[0].strip()]
    if not words:
        return '', []
    hs = sorted(w[4] - w[2] for w in words)
    wh = hs[len(hs) // 2] or 1
    # gutter: x in the middle of the page crossed by the fewest words
    xs = range(int(0.35 * W), int(0.65 * W), max(1, int(W / 400)))
    cover = [(sum(1 for w in words if w[1] < x < w[3]), abs(x - W / 2), x) for x in xs]
    g = min(cover)[2]
    # lines per column
    cols = {'a': [], 'b': [], 'w': []}
    for w in words:
        side = 'w' if (w[1] < g - 0.02 * W and w[3] > g + 0.02 * W) else 'a' if (w[1] + w[3]) / 2 < g else 'b'
        cols[side].append(w)
    lines = []
    for side, ws in cols.items():
        ws.sort(key=lambda w: (w[2] + w[4]) / 2)
        cur = []
        for w in ws:
            cy = (w[2] + w[4]) / 2
            if cur and abs(cy - sum((v[2] + v[4]) / 2 for v in cur) / len(cur)) > 0.6 * wh:
                lines.append((side, cur))
                cur = []
            cur.append(w)
        if cur:
            lines.append((side, cur))
    L = []
    for side, ws in lines:
        ws.sort(key=lambda w: w[1])
        L.append(dict(side=side, text=' '.join(w[0] for w in ws), n=len(ws),
                      y0=min(w[2] for w in ws), y1=max(w[4] for w in ws)))
    body = [l for l in L if l['side'] != 'w' and (l['n'] >= 3 or len(l['text']) >= 15)]
    top = min(l['y0'] for l in body) if body else 0
    foot = [l for l in L if FOOT_RE.search(l['text']) and l['y0'] > 0.85 * H]
    bottom = min(l['y0'] for l in foot) - 0.3 * wh if foot else H
    keep = [l for l in L if l['y1'] > top - 0.3 * wh and l['y0'] < bottom]
    last = max((l['y1'] for l in keep if l['side'] != 'w'), default=H)
    keep = [l for l in keep if not (l['n'] <= 2 and l['y0'] > last - 0.2 * wh and len(l['text']) <= 6)]
    # bands: cut at full-width lines (headings) and at gaps of > 3 line heights in both columns
    heads = sorted((l['y0'] + l['y1']) / 2 for l in keep if l['side'] == 'w')
    ys = sorted((l['y0'], l['y1']) for l in keep if l['side'] != 'w')
    cuts, reach = list(heads), None
    for y0, y1 in ys:
        if reach is not None and y0 - reach > 3 * wh:
            cuts.append((reach + y0) / 2)
        reach = y1 if reach is None else max(reach, y1)
    cuts.sort()
    parts = []
    for band in range(len(cuts) + 1):
        lo = cuts[band - 1] if band else -1e9
        hi = cuts[band] if band < len(cuts) else 1e9
        for side in 'ab':
            sel = sorted((l for l in keep if l['side'] == side and lo <= (l['y0'] + l['y1']) / 2 < hi),
                         key=lambda l: l['y0'])
            if sel:
                parts.append(join_lines(l['text'] for l in sel))
    return ' '.join(parts), []


def cand_abbyy_A(leaf):
    """Scan A's ABBYY text in the reading order of ocr/NNNN.json; starts = (char offset, guessed) of every hanging
    paragraph."""
    pg = json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))
    text, starts = '', []
    for c in pg['columns']:
        for p in c['paragraphs']:
            para = join_lines(ln['text'] for ln in p['lines'])
            if not para:
                continue
            if text and not (text.endswith(('-', '¬')) and not p['hanging']):
                text += ' '
            elif text:
                text = text[:-1]
            if p['hanging']:
                starts.append((len(text), bool(p.get('guessed'))))
            text += para
    return text.replace('￼', ''), starts


def cand_djvu_B(leaf):
    p = page_of(leaf)
    out = subprocess.run(['djvused', '-u', str(REPRINT), '-e', f'select {p}; print-txt'],
                         capture_output=True, text=True, check=True).stdout
    m = re.match(r'\(page (\d+) (\d+) (\d+) (\d+)', out)
    H = int(m.group(4)) + int(m.group(2))
    W = int(m.group(3)) + int(m.group(1))
    words = []
    for mm in re.finditer(r'\(word (\d+) (\d+) (\d+) (\d+) "((?:[^"\\]|\\.)*)"\)', out):
        x0, y0, x1, y1 = map(int, mm.group(1, 2, 3, 4))
        t = re.sub(r'\\(.)', lambda e: {'n': ' ', 't': ' '}.get(e.group(1), e.group(1)), mm.group(5))
        words.append((t.replace('\n', ' ').strip(), x0, H - y1, x1, H - y0))
    return reading_order(words, W, H)


def pdf_words(pdf, page):
    out = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-bbox', str(pdf), '-'],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', out)
    W, H = float(m.group(1)), float(m.group(2))
    words = [(html.unescape(t), float(a), float(b), float(c), float(d)) for a, b, c, d, t in
             re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', out)]
    return words, W, H


def cand_google_D(leaf):
    words, W, H = pdf_words(CORNELL, page_of(leaf) + 48)
    return reading_order(words, W, H)


def cand_google_C(leaf):
    p = page_of(leaf)
    pdf, page = (INDIANA[0], p + 46) if p <= 572 else (INDIANA[1], p - 558)
    words, W, H = pdf_words(pdf, page)
    return reading_order(words, W, H)


CANDIDATES = {'abbyy_A': cand_abbyy_A, 'djvu_B': cand_djvu_B, 'google_D': cand_google_D, 'google_C': cand_google_C}


def candidate(name, leaf, refresh=False):
    path = CAND_DIR / name / f'{leaf:04d}.txt'
    starts_path = path.with_suffix('.starts.json')
    if refresh or not path.exists():
        text, starts = CANDIDATES[name](leaf)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + '\n', encoding='utf-8')
        if starts:
            starts_path.write_text(json.dumps(starts) + '\n', encoding='utf-8')
    text = path.read_text(encoding='utf-8').rstrip('\n')
    starts = json.loads(starts_path.read_text(encoding='utf-8')) if starts_path.exists() else []
    return text, starts


# ---------------------------------------------------------------- normalisation

CS_CIVIL = {'ѡ': 'о', 'Ѡ': 'О', 'ѿ': 'от', 'Ѿ': 'От', 'ѻ': 'о', 'ꙩ': 'о', 'ꙋ': 'у', 'Ꙋ': 'У', 'ѹ': 'у', 'Ѹ': 'У',
            'ү': 'у', 'Ү': 'У', 'ѕ': 'з', 'Ѕ': 'З', 'ꙁ': 'з', 'Ꙁ': 'З', 'є': 'е', 'Є': 'Е', 'ѥ': 'е', 'Ѥ': 'Е',
            'ї': 'і', 'Ї': 'І', 'ѧ': 'я', 'Ѧ': 'Я', 'ꙗ': 'я', 'Ꙗ': 'Я', 'ѩ': 'я', 'Ѩ': 'Я', 'ѫ': 'у', 'Ѫ': 'У',
            'ѭ': 'ю', 'Ѭ': 'Ю', 'ѯ': 'кс', 'Ѯ': 'Кс', 'ѱ': 'пс', 'Ѱ': 'Пс', 'ꙑ': 'ы', 'ѷ': 'ѵ'}
LOOKALIKE = dict(zip('aceopxyABCEHKMOPTXiIëė', 'асеорхуАВСЕНКМОРТХіІее'))
DASHES, QUOTES = set('—–‐‑−-'), set('„“”"«»‘’\'`')


def normalise(chars, level):
    """chars: [(char, tag)] -> [(char, tag)]; whitespace dropped; `level` strict or norm."""
    out = []
    for ch, tag in chars:
        ch = unicodedata.normalize('NFC', ch)
        if ch.isspace() or ch in '¬￼':
            continue
        if level == 'norm':
            if ch in DASHES:
                ch = '-'
            elif ch in QUOTES:
                ch = '"'
            ch = CS_CIVIL.get(ch, ch)
            ch = ''.join(LOOKALIKE.get(c, c) for c in ch)
            ch = ''.join(c for c in unicodedata.normalize('NFD', ch) if not unicodedata.combining(c))
            ch = unicodedata.normalize('NFC', ch)
        for c in ch:
            out.append((c, tag))
    if level == 'norm':                   # оу -> у
        res = []
        for c, tag in out:
            if c in 'уУ' and res and res[-1][0] in 'оО':
                res[-1] = ('у' if res[-1][0] == 'о' else 'У', res[-1][1])
                continue
            res.append((c, tag))
        out = res
    return out


# ---------------------------------------------------------------- alignment

def align(a, b):
    """Levenshtein alignment of sequences a (GT) and b (candidate). Returns (distance, cost_at, j_at): cost_at[i] =
    edits charged to GT position i (substitution/deletion of a[i], plus insertions just before it), j_at[i] = the
    candidate position aligned with a[i]."""
    n, m = len(a), len(b)
    vocab = {c: k for k, c in enumerate(sorted(set(a) | set(b)))}
    A = np.array([vocab[c] for c in a], dtype=np.int32)
    B = np.array([vocab[c] for c in b], dtype=np.int32)
    D = np.empty((n + 1, m + 1), dtype=np.int32)
    D[0] = np.arange(m + 1)
    ar = np.arange(m + 1, dtype=np.int32)
    for i in range(1, n + 1):
        row = np.empty(m + 1, dtype=np.int32)
        row[0] = i
        if m:
            row[1:] = np.minimum(D[i - 1, :-1] + (B != A[i - 1]), D[i - 1, 1:] + 1)
        D[i] = np.minimum.accumulate(row - ar) + ar
    cost_at = [0] * (n + 1)
    j_at = [0] * (n + 1)
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i, j] == D[i - 1, j - 1] + (A[i - 1] != B[j - 1]):
            cost_at[i - 1] += int(A[i - 1] != B[j - 1])
            j_at[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif i > 0 and D[i, j] == D[i - 1, j] + 1:
            cost_at[i - 1] += 1
            j_at[i - 1] = j
            i -= 1
        else:
            cost_at[min(i, n - 1) if n else 0] += 1
            j -= 1
    return int(D[n, m]), cost_at[:n], j_at[:n]


# ---------------------------------------------------------------- scoring

def gt_leaves():
    return sorted(int(p.stem) for p in GT_DIR.glob('[0-9][0-9][0-9][0-9].txt'))


def score(name, leaf, level):
    gt = parse_gt(GT_DIR / f'{leaf:04d}.txt')
    text, starts = candidate(name, leaf)
    ga = normalise([(c, (z, s)) for c, z, s in gt], level)
    # candidate: tag each char with "starts a hanging paragraph"
    start_at = {pos: g for pos, g in starts}
    ca = normalise([(c, start_at.get(k)) for k, c in enumerate(text)], level)
    a = [c for c, _ in ga]
    b = [c for c, _ in ca]
    dist, cost_at, j_at = align(a, b)
    res = dict(cand=name, leaf=leaf, level=level, n=len(a), dist=dist)
    for zone in ('hw', 'def', 'grc'):
        idx = [k for k, (_, (z, _)) in enumerate(ga) if z == zone]
        res[f'{zone}_n'] = len(idx)
        res[f'{zone}_err'] = sum(cost_at[k] for k in idx)
    # headwords read exactly
    spans, cur = [], []
    for k, (_, (z, _)) in enumerate(ga):
        if z == 'hw':
            cur.append(k)
        elif cur:
            spans.append(cur)
            cur = []
    if cur:
        spans.append(cur)
    res['hw_count'] = len(spans)
    res['hw_exact'] = sum(1 for sp in spans if all(cost_at[k] == 0 for k in sp))
    # entry segmentation (abbyy_A only)
    if starts:
        gt_starts = [k for k, (_, (_, s)) in enumerate(ga) if s]
        cand_starts = {k: g for k, (_, g) in enumerate(ca) if g is not None}
        # a GT entry start and a candidate paragraph start match when the candidate position aligned with the GT
        # start lies within TOL characters of it (headwords are where the OCR garbles most, so allow some slack)
        TOL = 4
        found = sum(1 for i in gt_starts if any(abs(j_at[i] - j) <= TOL for j in cand_starts))
        good = sum(1 for j in cand_starts if any(abs(j_at[i] - j) <= TOL for i in gt_starts))
        res.update(seg_gt=len(gt_starts), seg_found=found, seg_cand=len(cand_starts), seg_good=good,
                   seg_guessed=sum(1 for g in cand_starts.values() if g))
    return res


def headword_readings(leaf, names, level='norm'):
    """For every GT headword on the page: the GT form and each candidate's aligned reading (norm)."""
    gt = parse_gt(GT_DIR / f'{leaf:04d}.txt')
    ga = normalise([(c, z) for c, z, s in gt], level)
    a = [c for c, _ in ga]
    spans, cur = [], []
    for k, (_, z) in enumerate(ga):
        if z == 'hw':
            cur.append(k)
        elif cur:
            spans.append(cur)
            cur = []
    if cur:
        spans.append(cur)
    rows = [dict(gt=''.join(a[k] for k in sp)) for sp in spans]
    for name in names:
        text, _ = candidate(name, leaf)
        b = [c for c, _ in normalise([(c, None) for c in text], level)]
        _, cost_at, j_at = align(a, b)
        for row, sp in zip(rows, spans):
            nxt = sp[-1] + 1
            j1 = j_at[nxt] if nxt < len(a) else len(b)
            row[name] = ''.join(b[j_at[sp[0]]:j1])
            row[name + '_ok'] = all(cost_at[k] == 0 for k in sp)
    return rows


def vote(names):
    """Triangulation of the headwords: how often do independent readings agree, and are they right then?"""
    rows = [r for leaf in gt_leaves() for r in headword_readings(leaf, names)]
    n = len(rows)
    print(f'{n} headwords (norm). Exactly right per candidate: ' +
          ', '.join(f'{m} {sum(r[m + "_ok"] for r in rows)}' for m in names))
    pairs = [(x, y) for i, x in enumerate(names) for y in names[i + 1:]]
    for x, y in pairs:
        agree = [r for r in rows if r[x] == r[y]]
        right = sum(1 for r in agree if r[x + '_ok'])
        print(f'  {x} = {y}: agree on {len(agree)}/{n}, of which right {right} '
              f'({right / max(1, len(agree)):.0%}); right in either: {sum(1 for r in rows if r[x + "_ok"] or r[y + "_ok"])}')
    # majority of all candidates (ties: prefer the order of `names`)
    maj_ok = 0
    for r in rows:
        counts = {}
        for m in names:
            counts.setdefault(r[m], []).append(m)
        best = max(counts.items(), key=lambda kv: (len(kv[1]), -min(names.index(m) for m in kv[1])))
        maj_ok += r[best[1][0] + '_ok']
    print(f'  majority vote of {"+".join(names)}: right {maj_ok}/{n} ({maj_ok / n:.0%}); '
          f'right in at least one: {sum(1 for r in rows if any(r[m + "_ok"] for m in names))}')
    return rows


def suspects(names=('google_D', 'djvu_B'), level='norm', context=12):
    """Places where independent candidates agree with each other but not with the GT: likely GT errors (or errors
    shared by both OCRs). Prints them with context, for checking against the images."""
    total = 0
    for leaf in gt_leaves():
        gt = parse_gt(GT_DIR / f'{leaf:04d}.txt')
        ga = normalise([(c, z) for c, z, s in gt], level)
        a = [c for c, _ in ga]
        per = []
        for name in names:
            text, _ = candidate(name, leaf)
            b = [c for c, _ in normalise([(c, None) for c in text], level)]
            _, cost_at, j_at = align(a, b)
            # reading of each GT position: the aligned char, plus inserted chars before the next GT position
            reading = []
            for i in range(len(a)):
                j0 = j_at[i]
                j1 = j_at[i + 1] if i + 1 < len(a) else len(b)
                sub = ''.join(b[j0:j1]) if j1 > j0 else ''
                reading.append(sub)
            per.append(reading)
        i = 0
        while i < len(a):
            rs = [r[i] for r in per]
            if len(set(rs)) == 1 and rs[0] != a[i]:
                s0 = i
                while i + 1 < len(a) and len({r[i + 1] for r in per}) == 1 and per[0][i + 1] != a[i + 1]:
                    i += 1
                gt_s = ''.join(a[s0:i + 1])
                oc_s = ''.join(per[0][s0:i + 1])
                ctx = ''.join(a[max(0, s0 - context):s0]) + '[' + gt_s + ']' + ''.join(a[i + 1:i + 1 + context])
                print(f'leaf {leaf} [{ga[s0][1]}] GT {gt_s!r:10} OCR {oc_s!r:10}  {ctx}')
                total += 1
            i += 1
    print(f'{total} places where {" and ".join(names)} agree against the GT ({level})')


def show(name, leaf, level, zone=None):
    gt = parse_gt(GT_DIR / f'{leaf:04d}.txt')
    text, _ = candidate(name, leaf)
    ga = normalise([(c, z) for c, z, s in gt], level)
    ca = normalise([(c, None) for c in text], level)
    a, b = [c for c, _ in ga], [c for c, _ in ca]
    dist, cost_at, j_at = align(a, b)
    # print GT stretches with errors and the candidate stretch aligned to them
    k = 0
    while k < len(a):
        if cost_at[k] and (zone is None or ga[k][1] == zone):
            s = k
            while k < len(a) and (cost_at[k] or any(cost_at[k + d] for d in range(1, 3) if k + d < len(a))):
                k += 1
            ctx0, ctx1 = max(0, s - 6), min(len(a), k + 6)
            j0, j1 = j_at[ctx0], j_at[ctx1 - 1] + 1
            print(f'{s:5} [{ga[s][1]}] GT: {"".join(a[ctx0:ctx1])}\n{"":13}->  {"".join(b[j0:j1])}')
        k += 1
    print(f'{name} leaf {leaf} ({level}): distance {dist} over {len(a)} GT characters = CER {dist / max(1, len(a)):.1%}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--show', nargs=2, metavar=('CANDIDATE', 'LEAF'))
    ap.add_argument('--zone', choices=('hw', 'def', 'grc'))
    ap.add_argument('--level', default='norm', choices=('strict', 'norm'))
    ap.add_argument('--refresh', action='store_true', help='re-extract the candidate texts')
    ap.add_argument('--only', help='comma-separated candidate names')
    ap.add_argument('--vote', action='store_true', help='headword triangulation across the candidates')
    ap.add_argument('--suspects', action='store_true',
                    help='places where independent candidates agree against the GT (default google_D, djvu_B)')
    a = ap.parse_args()
    if getattr(a, 'suspects', False):
        suspects(tuple(a.only.split(',')) if a.only else ('google_D', 'djvu_B'), a.level)
        return
    if a.vote:
        vote(a.only.split(',') if a.only else ['google_D', 'google_C', 'djvu_B', 'abbyy_A'])
        return
    if a.show:
        show(a.show[0], int(a.show[1]), a.level, a.zone)
        return
    names = a.only.split(',') if a.only else list(CANDIDATES)
    rows = []
    for name in names:
        for leaf in gt_leaves():
            candidate(name, leaf, refresh=a.refresh)
            for level in ('strict', 'norm'):
                rows.append(score(name, leaf, level))
    cols = ['cand', 'leaf', 'level', 'n', 'dist', 'hw_n', 'hw_err', 'hw_count', 'hw_exact', 'def_n', 'def_err',
            'grc_n', 'grc_err', 'seg_gt', 'seg_found', 'seg_cand', 'seg_good', 'seg_guessed']
    tmp = EVAL / 'results.tmp'
    tmp.write_text('\t'.join(cols) + '\n' + ''.join('\t'.join(str(r.get(c, '')) for c in cols) + '\n' for r in rows),
                   encoding='utf-8')
    tmp.rename(EVAL / 'results.tsv')
    # summary
    def pct(e, n):
        return f'{e / n:6.1%}' if n else '     -'
    print(f'{"candidate":10} {"level":6} {"CER all":>8} {"hw CER":>7} {"hw exact":>9} {"def CER":>8} {"grc CER":>8}')
    for name in names:
        for level in ('strict', 'norm'):
            rs = [r for r in rows if r['cand'] == name and r['level'] == level]
            t = {k: sum(r[k] for r in rs) for k in ('n', 'dist', 'hw_n', 'hw_err', 'hw_count', 'hw_exact', 'def_n',
                                                     'def_err', 'grc_n', 'grc_err')}
            print(f'{name:10} {level:6} {pct(t["dist"], t["n"]):>8} {pct(t["hw_err"], t["hw_n"]):>7} '
                  f'{t["hw_exact"]:4}/{t["hw_count"]:<4} {pct(t["def_err"], t["def_n"]):>8} '
                  f'{pct(t["grc_err"], t["grc_n"]):>8}')
    print('\nper page (norm, CER all / hw CER):')
    print(f'{"leaf":>6} ' + ' '.join(f'{n:>16}' for n in names))
    for leaf in gt_leaves():
        cells = []
        for name in names:
            r = next(r for r in rows if r['cand'] == name and r['leaf'] == leaf and r['level'] == 'norm')
            cells.append(f'{pct(r["dist"], r["n"])} /{pct(r["hw_err"], r["hw_n"])}')
        print(f'{leaf:>6} ' + ' '.join(f'{c:>16}' for c in cells))
    seg = [r for r in rows if r['cand'] == 'abbyy_A' and r['level'] == 'norm' and 'seg_gt' in r]
    if seg:
        print('\nentry segmentation of ocr/*.json (abbyy_A):')
        for r in seg:
            print(f'  leaf {r["leaf"]}: GT entries {r["seg_gt"]}, found {r["seg_found"]} '
                  f'(recall {pct(r["seg_found"], r["seg_gt"])}); candidate starts {r["seg_cand"]}, correct '
                  f'{r["seg_good"]} (precision {pct(r["seg_good"], r["seg_cand"])}); guessed {r["seg_guessed"]}')
        T = {k: sum(r[k] for r in seg) for k in ('seg_gt', 'seg_found', 'seg_cand', 'seg_good')}
        print(f'  all: recall {pct(T["seg_found"], T["seg_gt"])}, precision {pct(T["seg_good"], T["seg_cand"])}')


if __name__ == '__main__':
    main()
