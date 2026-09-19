#!/usr/bin/env python3
"""Phase 3b of djachenko/PLAN.md: the page text from the witnesses on scan A's segmentation (step 1) and the
headwords read from crops (step 2).

    python3 tools/dj_heads.py text [--pages 45,517-520] [--force]   # step 1, every main/supplement page not yet done
    python3 tools/dj_heads.py show 45 7                              # A / D / merged text of paragraph 7 of leaf 45
    python3 tools/dj_heads.py crops --pages 45                       # step 2: write the entry crops (cache/crops/)
    python3 tools/dj_heads.py sheet 45                               # numbered contact sheets for reading in a session
    python3 tools/dj_heads.py enter 45 readings.txt                  # store readings made by hand (one per line)
    python3 tools/dj_heads.py read --pages 45,517 [--effort medium]  # API: read the crops page by page, store
    python3 tools/dj_heads.py read --batch [--pages ...]             # API: submit Message Batches (50 % price)
    python3 tools/dj_heads.py collect                                # API: fetch finished batches, store
    python3 tools/dj_heads.py check [--pages ...]                    # confirm the headwords against B, C, D, A
    python3 tools/dj_heads.py report                                 # what is done, from ocr/*.json

Why (eval/RESULTS.md): Google's text layer of witness D (Cornell copy) reads the civil text at 1.5 % CER against
ABBYY's 3.8 % on A and has both margins on every page, while A's geometry segments the entries almost perfectly. Where
D and B agree (95 % of characters) the text is right in 99.9 %; where they disagree, a vote with A decides. The
headwords (Church Slavonic type) no OCR reads better than ~50 %; a vision model reading crops got 25/25.

Step 1, per page (leaf of scan A, main and supplement only):
  1. A's paragraphs (ocr/NNNN.json) are joined to one text per column side (left a, right b) with their offsets.
  2. D's, B's and C's body text is rebuilt from their word boxes (dj_witness.reading_order), also per side —
     everything below runs per side, so that a page split into bands differently by a witness cannot matter.
  3. A is aligned to D (Levenshtein on the "norm" level); every paragraph start of A is carried to D and snapped to
     the nearest line start of D within CUT_TOL characters (a paragraph always starts a printed line, and the
     headword — where A is least reliable — is exactly what the alignment gets wrong). D's text is cut there.
  4. B, A and C are aligned to D; per character, if B differs from D, A reads like B and C does not confirm D,
     B's reading replaces D's ("fixed"); every other place where B differs from D stays D's but is "disputed".
  5. Written into the page JSON, per paragraph: text_d (D's raw text), text_merged (after the vote), disputed
     (spans [start, end) in text_merged where D and B disagree), italic (spans of words ABBYY flagged italic on A,
     carried over through the alignment — the book's sources and quotations), fixed (count), d_cut ("line" snapped to a D line
     start, "aligned" not snapped, "forced" pushed to keep the order), d_line (box of the paragraph's first line
     in D, 600 ppi pixels — for the headword crops of step 2); and per page: witness {version, d_page, b_page,
     c_page, chars, cuts, disputed, fixed, odd = [col, para, length ratio] of paragraphs whose D text is much
     shorter or longer than A's}. dj_abbyy.py carries all of this over when it regenerates a page.

Step 2, per page: one crop per entry candidate (entries_hint = hanging paragraph): the start of its first line
from A's 600 ppi image (headword box + 350 px, at least 1000 px wide), or from D's page rendered at 600 ppi on the
242 pages whose left margin is cut in A (via d_line). The crops go to the model as separate images (full resolution,
~100 tokens each; cheaper and sharper than a contact sheet), one request per page, with a few examples from the
ground-truth pages as a cached prefix; the answer is a JSON list with one headword (in the convention of
eval/README.md: letters as printed, no diacritics) or null (not an entry start) per image. Stored in
entries_hint[]: headword, headword_source (model id or "manual"), check ("confirmed" when B, C, D or A read the
same at norm level, "disputed" otherwise, "no_entry" for null) and confirmed_by. `sheet` + `enter` do the same
by hand. `read --batch` submits Message Batches and records their ids in djachenko/heads_batches.tsv, so that
`collect` can fetch them in a later session; every step writes page by page and skips what is done.
"""
import argparse, base64, bisect, csv, glob, io, json, re, subprocess, sys, time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import (CORNELL, DJ, OCR, PDF_DPI, align, b_page, c_page, d_page, join_lines,  # noqa: E402
                        load_page, norm_char, norm_seq, page_text, side_texts)
import dj_abbyy  # noqa: E402  (dump, iou)

VERSION = 5            # of the witness block; bump to redo every page (5 = + italic spans from ABBYY's word flags)
CUT_TOL = 15           # characters: how far a paragraph start may move to reach a line start of D
PARA_KEYS = ('text_d', 'text_merged', 'disputed', 'italic', 'fixed', 'd_cut', 'd_line')

PAGES = DJ / 'pages'
CACHE = DJ / 'cache'                  # rendered D pages, crops (git-ignored)
BATCHES = DJ / 'heads_batches.tsv'    # Message Batches submitted by `read --batch`, for `collect` (committed)
MODEL = 'claude-opus-5'
CROP_SCALE = 2 / 3                    # 600 ppi -> 400 ppi for the images sent to the model
# few-shot examples for the model: (leaf, hint index, answer) from ground-truth pages whose hints match the GT 1:1;
# hint index 'cont' = the second line of hint 0's paragraph, i.e. not an entry start -> null
GT_EXAMPLES = [(517, 0, 'Предгрѧдꙋ'), (517, 1, 'Преддверїе'), (517, 18, 'Предиковать'), (660, 0, 'Смокноути'),
               (660, 14, 'мꙋгленый'), (660, 26, 'Смѣйна'), (660, 'cont', None)]


# ---------------------------------------------------------------- A

HYPHENS_A = ('-', '¬', '‐')


def line_tags(ln):
    """Per character of the line's text: True where ABBYY flagged the word italic."""
    text, tags, cur = ln['text'], [False] * len(ln['text']), 0
    for w in ln['words']:
        k = text.find(w[0], cur)
        if k < 0:
            continue
        if 'i' in (w[6] or ''):
            for i in range(k, k + len(w[0])):
                tags[i] = True
        cur = k + len(w[0])
    return tags


def join_tagged(lines):
    """join_lines() for (text, tags) pairs: the same text, with the tags carried along."""
    out, tags = '', []
    for t, tg in lines:
        lead = len(t) - len(t.lstrip())
        t2 = t.strip()
        tg = tg[lead:lead + len(t2)]
        if not t2:
            continue
        if out.endswith(HYPHENS_A) and not out.endswith(' -'):
            out, tags = out[:-1] + t2, tags[:-1] + tg
        else:
            out, tags = ((out + ' ' + t2), (tags + [False] + tg)) if out else (t2, tg)
    return out, tags


def a_paragraphs(pg, side):
    """-> (text of A's paragraphs on one column side, top to bottom, its per-character italic tags,
    [dict(col, para, start, text, hanging)]): paragraphs joined with a space, a hyphenated paragraph end joined to a
    continuation (the text is the same as dj_eval.cand_abbyy_A builds)."""
    text, tags, paras = '', [], []
    for ci, c in enumerate(pg['columns']):
        if c['side'] != side:
            continue
        for pi, p in enumerate(c['paragraphs']):
            para, ptags = join_tagged((ln['text'], line_tags(ln)) for ln in p['lines'])
            if '￼' in para:
                ptags = [t for ch, t in zip(para, ptags) if ch != '￼']
                para = para.replace('￼', '')
            if para:
                if text and not (text.endswith(('-', '¬')) and not p['hanging']):
                    text, tags = text + ' ', tags + [False]
                elif text:
                    text, tags = text[:-1], tags[:-1]
            paras.append(dict(col=ci, para=pi, start=len(text), text=para, hanging=p['hanging']))
            text, tags = text + para, tags + ptags
    return text, tags, paras


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

def merge(d_text, b_text, a_text, c_text, a_tags=None):
    """-> (merged text, out_at, disputed, italic): out_at[r] = offset in the merged text of D's raw index r
    (len(d_text)+1 entries); disputed = [(start, end, fixed)] in merged coordinates, one per place where B differs
    from D — fixed means B's reading replaced D's (the span is then B's text, possibly empty); italic = per merged
    character, whether the A character aligned with it was flagged italic by ABBYY (a_tags, per A character).
    A fix needs B and A to agree AND C
    not to confirm D: A and B are both FineReader and share the CS-type confusions (и/н, а/л, . for ,), C and D
    are both Google; two engines against two is a tie, and Google measured better (eval/RESULTS.md). Two exceptions
    where Google is systematically weak and the FineReader pair was right 19:0 and 9:3 on the ground truth: the "="
    after the headword (Google reads a third of them) and final ъ/ь."""
    d_seq, d_idx = norm_seq(d_text)
    n = len(d_seq)

    def readings_of(text, tags=None):
        """Per norm position of D: the witness's reading there, normalised and raw (and its italic tag)."""
        seq, idx = norm_seq(text)
        if not n or not seq:
            return [''] * n, [''] * n, [False] * n
        _, _, j_at = align(d_seq, seq)
        norm, raw, ital = [], [], []
        for k in range(n):
            j0 = j_at[k]
            j1 = j_at[k + 1] if k + 1 < n else len(seq)
            norm.append(''.join(seq[j0:j1]) if j1 > j0 else '')
            raw.append(text[idx[j0]:idx[j1 - 1] + 1] if j1 > j0 else '')
            ital.append(bool(tags) and j1 > j0 and tags[idx[j0]])
        return norm, raw, ital

    rB, rawB, _ = readings_of(b_text)
    rA, _, iA = readings_of(a_text, a_tags)
    rC, _, _ = readings_of(c_text)
    pieces, piece_at, flagged, ital = [], [0] * (len(d_text) + 1), [], []
    pos = k = 0
    while k < n:
        r = d_idx[k]
        k1 = k
        while k1 < n and d_idx[k1] == r:          # one raw character can carry two norm characters (ѿ -> от)
            k1 += 1
        while pos < r:                            # whitespace and other characters without a norm form
            piece_at[pos] = len(pieces)
            pieces.append(d_text[pos])
            ital.append(None)
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
        ital.append(any(iA[k:k1]))
        pos, k = r + 1, k1
    while pos < len(d_text):
        piece_at[pos] = len(pieces)
        pieces.append(d_text[pos])
        ital.append(None)
        pos += 1
    piece_at[len(d_text)] = len(pieces)
    offs, acc, italic = [], 0, []
    for s, it in zip(pieces, ital):
        offs.append(acc)
        acc += len(s)
        italic.extend([it] * len(s))
    offs.append(acc)
    return (''.join(pieces), [offs[i] for i in piece_at], [(offs[i], offs[i + 1], f) for i, f in flagged],
            italic)


def italic_spans(text, italic, start, end):
    """Word-level italic runs within text[start:end] (spans relative to start): a word is italic when at least
    half of its letters are; runs of italic words, with the spaces between them, are joined."""
    spans, run = [], None
    for m in re.finditer(r'\S+', text[start:end]):
        flags = [italic[start + i] for i in range(m.start(), m.end()) if text[start + i].isalnum()]
        flags = [f for f in flags if f is not None]
        if flags and sum(flags) * 2 >= len(flags):
            if run and text[start + run[1]:start + m.start()].isspace():
                run[1] = m.end()
            else:
                run = [m.start(), m.end()]
                spans.append(run)
        else:
            run = None
    return [sp for sp in spans if sp[1] - sp[0] >= 2]


# ---------------------------------------------------------------- one page

def build_page(leaf, pg=None):
    pg = pg or load_page(leaf)
    W = {name: side_texts(page_text(name, leaf)) for name in 'DBC'}
    k = PDF_DPI / 72
    stats = dict(line=0, aligned=0, forced=0)
    n_disputed = n_fixed = n_chars = 0
    odd = []                                   # paragraphs whose D text is much shorter/longer than A's
    for side in 'ab':
        a_text, a_tags, paras = a_paragraphs(pg, side)
        D, B, C = (W[n][side] for n in 'DBC')
        d_text = D['text']
        n_chars += len(d_text)
        cuts = cut_positions(a_text, paras, d_text, D['lines'])
        merged, out_at, disputed, italic = merge(d_text, B['text'], a_text, C['text'], a_tags)
        n_disputed += len(disputed)
        n_fixed += sum(1 for _, _, f in disputed if f)
        line_at = {l['start']: l for l in D['lines']}
        build_side(pg, paras, cuts, d_text, merged, out_at, disputed, italic, line_at, k, stats, odd)
    pg['witness'] = dict(version=VERSION, d_page=d_page(leaf), b_page=b_page(leaf), c_page=list(c_page(leaf)[1:]),
                         chars=n_chars, cuts=stats, disputed=n_disputed, fixed=n_fixed, odd=odd)
    return pg


def build_side(pg, paras, cuts, d_text, merged, out_at, disputed, italic, line_at, k, stats, odd):
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
        par['italic'] = italic_spans(merged, italic, base, base + len(mseg))
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


# ================================================================ step 2: the headwords from crops

def hint_paragraph(pg, h):
    col = next(c for c in pg['columns'] if c['n'] == h['col'])
    return col, col['paragraphs'][h['para'] - 1]


def jp2_image(leaf):
    return Image.open(glob.glob(str(PAGES / 'jp2' / f'*_{leaf:04d}.jp2'))[0]).convert('L')


def d_image(leaf):
    """Witness D's page rendered at 600 ppi (cached under cache/d_pages/)."""
    out = CACHE / 'd_pages' / f'{leaf:04d}'
    png = out.with_suffix('.png')
    if not png.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['pdftoppm', '-f', str(d_page(leaf)), '-l', str(d_page(leaf)), '-r', str(PDF_DPI), '-gray',
                        '-png', '-singlefile', str(CORNELL), str(out)], check=True)
    return Image.open(png).convert('L')


def crop_boxes(pg):
    """-> [(hint index, source 'A'|'D', box)] for every entry candidate of the page: the start of the entry's first
    line — from the column's left edge to the headword box plus 350 px, at least 1000 px — from A, or from D where
    A's left margin is cut."""
    leftcut = any('side a: margin cut off' in w for w in pg['warnings'])
    out, d_left = [], None
    for k, h in enumerate(pg['entries_hint']):
        col, p = hint_paragraph(pg, h)
        if leftcut and col['side'] == 'a' and p.get('d_line'):
            if d_left is None:                      # the left edge of D's left column (a word box may miss the
                lines = side_texts(page_text('D', pg['idx']))['a']['lines']          # first letter), 600 ppi px
                xs = sorted(l['x0'] for l in lines)
                d_left = xs[len(xs) // 10] * PDF_DPI / 72 if xs else p['d_line'][0]
            x0, y0, x1, y1 = p['d_line']
            x0 = min(x0, d_left)
            out.append((k, 'D', (max(0, round(x0 - 25)), max(0, y0 - 35), round(min(x1 + 30, x0 + 1100)), y1 + 25)))
        else:
            x0, y0, x1, y1 = p['lines'][0]['bbox']
            x0 = min(x0, col['bbox'][0])
            out.append((k, 'A', (max(0, x0 - 25), max(0, y0 - 35), min(x1 + 30, max(h['bbox'][2] + 350, x0 + 1000)),
                                 y1 + 25)))
    return out


def crops_for(leaf, pg=None, refresh=False):
    """-> [(hint index, path)] of the entry crops of the page (cache/crops/NNNN/kk.jpg, 400 ppi), made if missing."""
    pg = pg or load_page(leaf)
    folder = CACHE / 'crops' / f'{leaf:04d}'
    boxes = crop_boxes(pg)
    paths = [(k, folder / f'{k:02d}.jpg') for k, _, _ in boxes]
    if not refresh and all(path.exists() for _, path in paths):
        return paths
    folder.mkdir(parents=True, exist_ok=True)
    images = {}
    for (k, src, box), (_, path) in zip(boxes, paths):
        if src not in images:
            images[src] = jp2_image(leaf) if src == 'A' else d_image(leaf)
        im = images[src].crop(box)
        im = im.resize((max(1, round(im.width * CROP_SCALE)), max(1, round(im.height * CROP_SCALE))), Image.LANCZOS)
        im.save(path, quality=85, optimize=True)
    return paths


def example_crop(leaf, which):
    """A few-shot example image: hint `which` of the page, or the second line of hint 0's paragraph ('cont')."""
    pg = load_page(leaf)
    if which == 'cont':
        _, p = hint_paragraph(pg, pg['entries_hint'][0])
        x0, y0, x1, y1 = p['lines'][1]['bbox']
        box = (max(0, x0 - 25), max(0, y0 - 35), min(x1 + 30, x0 + 1000), y1 + 25)
        im = jp2_image(leaf).crop(box)
        im = im.resize((round(im.width * CROP_SCALE), round(im.height * CROP_SCALE)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=85, optimize=True)
        return buf.getvalue()
    return dict(crops_for(leaf, pg))[which].read_bytes()


# ---------------------------------------------------------------- reading by hand (sheet / enter)

def label_font(size=22):
    for f in ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', '/Library/Fonts/Arial Unicode.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def cmd_sheet(a):
    """Numbered contact sheets of the page's crops, PER_SHEET crops each, for reading in a session."""
    PER_SHEET = 15
    paths = crops_for(a.leaf)
    font = label_font()
    out_dir = CACHE / 'sheets'
    out_dir.mkdir(parents=True, exist_ok=True)
    for s0 in range(0, len(paths), PER_SHEET):
        tiles = []
        for k, path in paths[s0:s0 + PER_SHEET]:
            c = Image.open(path).convert('L')
            t = Image.new('L', (70 + c.width, c.height), 255)
            ImageDraw.Draw(t).text((4, c.height // 2 - 14), f'{k + 1:2}', fill=0, font=font)
            t.paste(c, (70, 0))
            tiles.append(t)
        W = max(t.width for t in tiles)
        sheet = Image.new('L', (W, sum(t.height for t in tiles) + 6 * len(tiles)), 255)
        y = 0
        for t in tiles:
            sheet.paste(t, (0, y))
            y += t.height + 6
        out = out_dir / f'{a.leaf:04d}_{s0 // PER_SHEET + 1}.png'
        sheet.save(out)
        print(out.relative_to(DJ.parent), sheet.size)
    print(f'{len(paths)} entries; write the readings, one per line (numbered "12<TAB>word" or in order; "-" for '
          f'not an entry), then: dj_heads.py enter {a.leaf} FILE')


def cmd_enter(a):
    pg = load_page(a.leaf)
    n = len(pg['entries_hint'])
    lines = [l.rstrip('\n') for l in (sys.stdin if a.file == '-' else open(a.file, encoding='utf-8'))]
    lines = [l for l in lines if l.strip() and not l.startswith('#')]
    readings = {}
    for i, l in enumerate(lines):
        m = re.match(r'\s*(\d+)\s*[\t:.]\s*(.*)$', l)
        k, word = (int(m.group(1)) - 1, m.group(2)) if m else (i, l)
        readings[k] = word.strip()
    if set(readings) != set(range(n)):
        sys.exit(f'{n} entries on the page but readings for {sorted(k + 1 for k in readings)}')
    words = [None if readings[k] in ('-', 'null', '') else readings[k] for k in range(n)]
    store(a.leaf, pg, words, 'manual')
    print(f'leaf {a.leaf}: {sum(w is not None for w in words)} headwords stored, {sum(w is None for w in words)} null')


# ---------------------------------------------------------------- reading by the model

PROMPT = """You are transcribing headwords from a Church Slavonic–Russian dictionary printed in Moscow in 1900 \
(Дьяченко, Полный церковнославянский словарь). Each image shows the beginning of the first line of one dictionary \
entry: the headword — usually in Church Slavonic type with accents and titla, sometimes in bold civil type — followed \
by "=" or "—" and the start of the definition. The entries of a page are in alphabetical order.

For every image give the headword exactly as printed, letter by letter, in Cyrillic:
- keep the letters as printed: ѣ і ї ѳ ѵ ъ ь ѡ ѻ ѿ ꙋ (the 8-shaped uk) оу (written оу) ѕ ꙁ є ѥ ѧ ꙗ ѩ ѫ ѭ ѯ ѱ, and \
й, ы, ю, я as they stand; keep the case of the first letter;
- leave out accents, breathings, titla, pokrytie and all other marks above or beside the letters; a small letter \
printed above the line is written on the line in its place (Меѳимоны); do not expand abbreviations and do not \
correct spellings;
- when the head is a phrase, give the whole phrase without the "=" and without the definition (Метохія, метухія; \
Мехоноѳовый или мехоноѳовъ; Показать путь);
- when the image does not begin with a headword (a continuation line, a heading, a blank), answer null.
Answer with a JSON array, one element per image in the order of the images (a string or null), and nothing else."""


def image_block(data):
    return {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg',
                                        'data': base64.standard_b64encode(data).decode('ascii')}}


def example_turns():
    """The few-shot prefix: one user turn with the example images, one assistant turn with the answers."""
    content = [{'type': 'text', 'text': f'{len(GT_EXAMPLES)} images:'}]
    for leaf, which, _ in GT_EXAMPLES:
        content.append(image_block(example_crop(leaf, which)))
    content[-1]['cache_control'] = {'type': 'ephemeral'}
    answer = json.dumps([ans for _, _, ans in GT_EXAMPLES], ensure_ascii=False)
    return [{'role': 'user', 'content': content}, {'role': 'assistant', 'content': answer}]


def page_request(leaf, pg, examples, effort):
    paths = crops_for(leaf, pg)
    content = [{'type': 'text', 'text': f'{len(paths)} images, the entries of page {pg["printed_page"]} in order:'}]
    for _, path in paths:
        content.append(image_block(path.read_bytes()))
    return dict(model=MODEL, max_tokens=8000, system=PROMPT, output_config={'effort': effort},
                messages=examples + [{'role': 'user', 'content': content}])


def parse_answer(text, n):
    m = re.search(r'\[.*\]', text, re.S)
    if not m:
        raise ValueError(f'no JSON array in the answer: {text[:200]!r}')
    words = json.loads(m.group(0))
    if len(words) != n:
        raise ValueError(f'{len(words)} answers for {n} images')
    return [None if w in (None, '', 'null') else str(w).strip() for w in words]


def store(leaf, pg, words, source):
    """Write the readings into entries_hint and check them against the witnesses; save the page."""
    for h, w in zip(pg['entries_hint'], words):
        h['headword'] = w
        h['headword_source'] = source
        h['conf'] = None
    check_page(leaf, pg)
    write_page(leaf, pg)


def client():
    try:
        import anthropic                # only needed for `read` and `collect`
    except ImportError:
        sys.exit('the Anthropic SDK is not installed: pip install anthropic (and set ANTHROPIC_API_KEY)')
    return anthropic.Anthropic()


def cmd_read(a):
    leaves = pages_todo(a, key='headword')
    if not leaves:
        print('nothing to do')
        return
    examples = example_turns()
    if a.batch:
        submit_batches(leaves, examples, a.effort)
        return
    cl = client()
    usage = dict(input=0, cached=0, output=0)
    for n, leaf in enumerate(leaves, 1):
        pg = load_page(leaf)
        req = page_request(leaf, pg, examples, a.effort)
        t0 = time.time()
        resp = cl.messages.create(**req)
        text = ''.join(b.text for b in resp.content if b.type == 'text')
        u = resp.usage
        usage['input'] += u.input_tokens
        usage['cached'] += u.cache_read_input_tokens or 0
        usage['output'] += u.output_tokens
        try:
            words = parse_answer(text, len(pg['entries_hint']))
        except (ValueError, json.JSONDecodeError) as e:
            print(f'[{n}/{len(leaves)}] leaf {leaf}: NOT STORED ({e}); stop_reason {resp.stop_reason}')
            continue
        store(leaf, pg, words, resp.model)
        print(f'[{n}/{len(leaves)}] leaf {leaf}: {sum(w is not None for w in words)} headwords, '
              f'{sum(w is None for w in words)} null; {time.time() - t0:.0f} s; tokens in {u.input_tokens} '
              f'(cached {u.cache_read_input_tokens or 0}) out {u.output_tokens}', flush=True)
    print('tokens:', usage)


def submit_batches(leaves, examples, effort, per_batch=250):
    """Message Batches of `per_batch` pages (the 256 MB limit); ids recorded in heads_batches.tsv."""
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    cl = client()
    new = not BATCHES.exists()
    with open(BATCHES, 'a', encoding='utf-8') as f:
        if new:
            f.write('batch_id\tcreated\tleaves\tstatus\n')
        for i in range(0, len(leaves), per_batch):
            chunk = leaves[i:i + per_batch]
            reqs = [Request(custom_id=f'leaf-{leaf}',
                            params=MessageCreateParamsNonStreaming(**page_request(leaf, load_page(leaf), examples,
                                                                                    effort)))
                    for leaf in chunk]
            batch = cl.messages.batches.create(requests=reqs)
            f.write(f'{batch.id}\t{datetime.now(timezone.utc).isoformat(timespec="seconds")}\t'
                    f'{compact_ranges(chunk)}\tsubmitted\n')
            f.flush()
            print(f'batch {batch.id}: {len(chunk)} pages ({compact_ranges(chunk)}), status {batch.processing_status}')
    print(f'recorded in {BATCHES.relative_to(DJ.parent)}; later: dj_heads.py collect')


def compact_ranges(leaves):
    out, start, prev = [], None, None
    for x in leaves + [None]:
        if start is None:
            start = prev = x
        elif x is not None and x == prev + 1:
            prev = x
        else:
            out.append(f'{start}-{prev}' if prev != start else str(start))
            start = prev = x
    return ','.join(out)


def cmd_collect(a):
    if not BATCHES.exists():
        print('no batches recorded')
        return
    rows = list(csv.DictReader(open(BATCHES, encoding='utf-8'), delimiter='\t'))
    cl = client()
    for row in rows:
        if row['status'] == 'collected':
            continue
        batch = cl.messages.batches.retrieve(row['batch_id'])
        c = batch.request_counts
        print(f"batch {row['batch_id']} ({row['leaves']}): {batch.processing_status}; succeeded {c.succeeded}, "
              f"errored {c.errored}, processing {c.processing}")
        if batch.processing_status != 'ended':
            continue
        stored = failed = 0
        for res in cl.messages.batches.results(row['batch_id']):
            leaf = int(res.custom_id.split('-')[1])
            if res.result.type != 'succeeded':
                failed += 1
                print(f'  leaf {leaf}: {res.result.type}')
                continue
            msg = res.result.message
            pg = load_page(leaf)
            if pg['entries_hint'] and pg['entries_hint'][0].get('headword_source') and not a.force:
                continue
            text = ''.join(b.text for b in msg.content if b.type == 'text')
            try:
                words = parse_answer(text, len(pg['entries_hint']))
            except (ValueError, json.JSONDecodeError) as e:
                failed += 1
                print(f'  leaf {leaf}: NOT STORED ({e})')
                continue
            store(leaf, pg, words, msg.model)
            stored += 1
        row['status'] = 'collected' if not failed else f'collected ({failed} failed: rerun read for them)'
        print(f'  stored {stored} pages, {failed} failed')
    with open(BATCHES, 'w', encoding='utf-8') as f:
        f.write('batch_id\tcreated\tleaves\tstatus\n')
        for row in rows:
            f.write('\t'.join(row[k] for k in ('batch_id', 'created', 'leaves', 'status')) + '\n')


# ---------------------------------------------------------------- the check against the witnesses

def squash(text):
    return ''.join(norm_char(ch) for ch in text)


def check_page(leaf, pg, witness_text=None):
    """entries_hint[].check / confirmed_by: which witnesses (D = the paragraph's D text, C and B = their page texts,
    A = ABBYY's reading of the headword) contain the headword at norm level."""
    sides = witness_text or {n: side_texts(page_text(n, leaf)) for n in 'BC'}
    squashed = {n: {s: squash(sides[n][s]['text']) for s in 'ab'} for n in 'BC'}
    for h in pg['entries_hint']:
        if not h.get('headword_source'):
            continue
        if h['headword'] is None:
            h['check'], h['confirmed_by'] = 'no_entry', ''
            continue
        col, p = hint_paragraph(pg, h)
        hn = squash(h['headword'])
        by = ''
        if hn and hn in squash(p.get('text_d') or ''):
            by += 'D'
        for n in 'CB':
            if hn and hn in squashed[n][col['side']]:
                by += n
        if hn and hn == squash(h['abbyy']):
            by += 'A'
        h['check'], h['confirmed_by'] = ('confirmed' if by else 'disputed'), by


def cmd_check(a):
    leaves = parse_ranges(a.pages) if a.pages else [pg['idx'] for pg in all_pages() if pg['entries_hint']
                                                     and pg['entries_hint'][0].get('headword_source')]
    for leaf in leaves:
        pg = load_page(leaf)
        check_page(leaf, pg)
        write_page(leaf, pg)
    report()


# ---------------------------------------------------------------- CLI

def all_pages():
    for f in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] in ('main', 'supplement'):
            yield pg


def parse_ranges(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-')
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def todo(force=False, key='text'):
    """Pages still to do: step 1 (key text: witness.version not current) or step 2 (key headword: no reading)."""
    leaves = []
    for pg in all_pages():
        if key == 'text':
            done = pg.get('witness', {}).get('version') == VERSION
        else:
            done = not pg['entries_hint'] or bool(pg['entries_hint'][0].get('headword_source'))
        if force or not done:
            leaves.append(pg['idx'])
    return leaves


def pages_todo(a, key):
    if a.pages:
        leaves = parse_ranges(a.pages)
        if not a.force:
            pending = set(todo(key=key))
            leaves = [l for l in leaves if l in pending]
        return leaves
    return todo(a.force, key)


def cmd_show(a):
    pg = load_page(a.leaf)
    k = 0
    for c in pg['columns']:
        for pi, p in enumerate(c['paragraphs'], 1):
            k += 1
            if k != a.para:
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
            for h in pg['entries_hint']:
                if h['col'] == c['n'] and h['para'] == pi:
                    print('headword:', h.get('headword'), h.get('headword_source'), h.get('check'),
                          h.get('confirmed_by'), '| ABBYY:', h['abbyy'])
            return
    print('no such paragraph')


def report():
    pages = done = tot_par = tot_disp = tot_fixed = 0
    cuts = dict(line=0, aligned=0, forced=0)
    hints = read = null = confirmed = disputed = 0
    sources = {}
    for pg in all_pages():
        pages += 1
        w = pg.get('witness')
        if w and w.get('version') == VERSION:
            done += 1
            for k in cuts:
                cuts[k] += w['cuts'][k]
            tot_par += sum(w['cuts'].values())
            tot_disp += w['disputed']
            tot_fixed += w['fixed']
        for h in pg['entries_hint']:
            hints += 1
            if h.get('headword_source'):
                read += 1
                sources[h['headword_source']] = sources.get(h['headword_source'], 0) + 1
                null += h['headword'] is None
                confirmed += h.get('check') == 'confirmed'
                disputed += h.get('check') == 'disputed'
    print(f'step 1: {done}/{pages} pages have witness text (version {VERSION}); {tot_par} paragraphs, cuts {cuts}; '
          f'{tot_disp} disputed places, {tot_fixed} fixed by B+A')
    print(f'step 2: {read}/{hints} entry candidates read ({sources}); {null} not an entry, {confirmed} confirmed by '
          f'a witness, {disputed} disputed')


def cmd_text(a):
    leaves = pages_todo(a, key='text')
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


def cmd_crops(a):
    leaves = parse_ranges(a.pages) if a.pages else [pg['idx'] for pg in all_pages()]
    for leaf in leaves:
        paths = crops_for(leaf, refresh=a.force)
        print(f'leaf {leaf}: {len(paths)} crops, {sum(p.stat().st_size for _, p in paths) // 1024} KB')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name, fn in (('text', cmd_text), ('crops', cmd_crops), ('read', cmd_read), ('check', cmd_check)):
        sp = sub.add_parser(name)
        sp.add_argument('--pages', help='leaves, e.g. 45,517-520 (default: all main/supplement pages not yet done)')
        sp.add_argument('--force', action='store_true', help='redo pages that are already done')
        sp.set_defaults(fn=fn)
    sub.choices['text'].add_argument('--workers', type=int, default=4)
    sub.choices['read'].add_argument('--batch', action='store_true', help='submit Message Batches instead of reading now')
    sub.choices['read'].add_argument('--effort', default='medium', choices=('low', 'medium', 'high', 'xhigh', 'max'))
    sp = sub.add_parser('collect')
    sp.add_argument('--force', action='store_true')
    sp.set_defaults(fn=cmd_collect)
    sp = sub.add_parser('sheet')
    sp.add_argument('leaf', type=int)
    sp.set_defaults(fn=cmd_sheet)
    sp = sub.add_parser('enter')
    sp.add_argument('leaf', type=int)
    sp.add_argument('file', help='readings, one per line ("-" = stdin)')
    sp.set_defaults(fn=cmd_enter)
    sp = sub.add_parser('show')
    sp.add_argument('leaf', type=int)
    sp.add_argument('para', type=int)
    sp.set_defaults(fn=cmd_show)
    sp = sub.add_parser('report')
    sp.set_defaults(fn=lambda a: report())
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
