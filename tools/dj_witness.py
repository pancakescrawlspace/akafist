#!/usr/bin/env python3
"""Shared access to the four witnesses of Дьяченко's dictionary (djachenko/COPIES.md) and the text machinery that
dj_eval.py (Phase 2) and dj_heads.py (Phase 3b) both use. Not a command; import it.

    A  scan A (archive.org, 600 ppi): text and geometry from ocr/NNNN.json (Phase 3a)
    B  the 1993 reprint DjVu: `djvused print-txt`, words with boxes
    C  the Indiana PDFs (Google Books): `pdftotext -bbox`
    D  the Cornell PDF (Google Books): `pdftotext -bbox`     <- the primary text since Phase 2 (eval/RESULTS.md)

`indent_levels(page)` reads the printed paragraphs off a witness: which lines are flush (an entry begins) and
which are of the hanging indent.  C and D have both margins on every page, where scan A has neither on 551 of
them, so they — not A's geometry — say where the entries begin (PLAN.md Phase 3b step 1c).

Everything is addressed by the LEAF number of scan A; printed page = leaf - 37. Page mapping into the witnesses
(checked over the whole book, session 3): D's PDF page = printed page + 48; B's DjVu page = printed page; C: volume 1
page = p + 46 up to p. 566, then volume 2 page = p - 558 (both volumes print p. 567 — v1's last page, whose text layer
is truncated, and v2's page 9, which reads fully — so p. 567 is taken from v2).

`reading_order(words, W, H)` rebuilds the body text of a page from word boxes: gutter, header and footer removed,
bands (a letter initial splits the page), left column before right, lines joined with hyphenation repaired. It returns
the flat text plus the line and word spans in it, so that a position in the text can be traced back to a word box.

`norm_seq(text)` and `align(a, b)` are the comparison tools: normalisation to the "norm" level of eval/RESULTS.md
(CS letters to civil ones, look-alikes, no diacritics, no whitespace) with a back-pointer to the raw index, and a
Levenshtein alignment that charges every edit to a position of the first sequence.
"""
import bisect, cmath, html, json, math, re, statistics, subprocess, unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DJ = ROOT / 'djachenko'
OCR = DJ / 'ocr'
REPRINT = DJ / 'scan' / 'reprint1993' / 'Dyachenko G., Polnyj cerkovnoslavyanskij slovar (M., 1993, 1159p).djvu'
CORNELL = DJ / 'scan' / 'google' / 'google_cornell.pdf'
INDIANA = (DJ / 'scan' / 'google' / 'google_indiana_v1.pdf', DJ / 'scan' / 'google' / 'google_indiana_v2.pdf')
OFFSET = 37                                   # printed page = leaf of scan A - 37
PDF_DPI = 600                                 # the Google PDFs are 600 ppi bilevel; boxes come in points (72/inch)


def page_of(leaf):
    return leaf - OFFSET


def d_page(leaf):
    return page_of(leaf) + 48


def b_page(leaf):
    return page_of(leaf)


def c_page(leaf):
    p = page_of(leaf)
    return (INDIANA[0], p + 46) if p <= 566 else (INDIANA[1], p - 558)


# ---------------------------------------------------------------- word boxes of B, C, D

def pdf_words(pdf, page):
    """-> ([(text, x0, y0, x1, y1)] in points, top-left origin, W, H)."""
    out = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-bbox', str(pdf), '-'],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', out)
    W, H = float(m.group(1)), float(m.group(2))
    words = [(html.unescape(t), float(a), float(b), float(c), float(d)) for a, b, c, d, t in
             re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', out)]
    return words, W, H


def djvu_words(page):
    """-> ([(text, x0, y0, x1, y1)] in DjVu pixels, top-left origin, W, H).

    DjVu counts y upwards from the foot of the page, so the boxes are flipped about the page height, which comes
    from `size`. It must not come from the `(page …)` rectangle that `print-txt` opens with: that is the
    bounding box of the text layer, not the page (on p. 1: `(page 31 21 1608 1906)` against a page of
    1647 × 2637), and flipping about it put every box of witness B as much as 710 px too high — which the
    text never showed, since reading order is relative, but every crop of B did (fixed 2026-09-21)."""
    out = subprocess.run(['djvused', '-u', str(REPRINT), '-e', f'select {page}; size; print-txt'],
                         capture_output=True, text=True, check=True).stdout
    m = re.match(r'width=(\d+)\s+height=(\d+)', out)
    if not m:
        return [], 1, 1
    W, H = int(m.group(1)), int(m.group(2))
    words = []
    for mm in re.finditer(r'\(word (\d+) (\d+) (\d+) (\d+) "((?:[^"\\]|\\.)*)"\)', out):
        x0, y0, x1, y1 = map(int, mm.group(1, 2, 3, 4))
        t = re.sub(r'\\(.)', lambda e: {'n': ' ', 't': ' '}.get(e.group(1), e.group(1)), mm.group(5))
        words.append((t.replace('\n', ' ').strip(), x0, H - y1, x1, H - y0))
    return words, W, H


def words_D(leaf):
    return pdf_words(CORNELL, d_page(leaf))


def words_C(leaf):
    return pdf_words(*c_page(leaf))


def words_B(leaf):
    return djvu_words(b_page(leaf))


# ---------------------------------------------------------------- reading order

FOOT_RE = re.compile(r'Ц[еѳe]рк\W{0,3}сла|словарь,?\s*свящ|Дьяченко\.?$', re.I)
HYPHENS = ('-', '¬', '‐')
SIG_RE = re.compile(r"\d{1,2}[*°'’`·.,]?")     # the printer's sheet signature: "32", "32*", "64°" as the OCR reads it


def ascii_digits(s):
    """Digits of another script as their value: the book prints Arabic numerals only, so a Bengali ১ or a Devanagari
    ४ is the OCR misreading one of them (seen on the signature of p. 115)."""
    return ''.join(str(unicodedata.decimal(c)) if c.isdigit() and not c.isascii() else c for c in s)


def join_lines(lines):
    """Lines of one column/band (texts) -> text; a hyphen (or ¬) at a line end joins the word."""
    out = ''
    for t in lines:
        t = t.strip()
        if not t:
            continue
        if out.endswith(HYPHENS) and not out.endswith(' -'):
            out = out[:-1] + t
        else:
            out = (out + ' ' + t) if out else t
    return out


def reading_order(words, W, H, mixed_lines=False, signature=False, footer=False):
    """words: [(text, x0, y0, x1, y1)] top-left origin -> dict(text, lines, words):
    text   the body text in reading order: band by band, left column before right; header, footer and full-width
           headings left out; lines joined, hyphenation repaired (as join_lines)
    lines  [dict(start, end, side, y0, y1, x0, x1, n)] span of every printed line in `text` (end excludes the
           following space), in text order; a line that lost its hyphen ends one character earlier
    words  [dict(start, end, box)] span of every word in `text` with its original box
    The text is identical to what join_lines gives per band and side, joined with single spaces.
    mixed_lines: also keep a word on a line when its box overlaps the line's band although its centre is off — for
    a Church Slavonic headword beside civil text; only for witnesses with precise boxes (Google's C and D), on B's
    coarse boxes it pulls in noise.
    signature: the page is one of those that carry the printer's sheet signature at the foot (every 16th page and
    the third page of the sheet), so a signature merged into the lowest printed line may be taken off its end.
    footer: the page carries the footer line "Церк.-славян. словарь свящ. Г. Дьяченко." — the first page of every
    sheet, printed page ≡ 1 mod 16, and no other (checked in B, C and D: 70 pages, all ≡ 1). Only there is FOOT_RE
    looked for, and the cut made at the LOWEST line it matches, since the footer lies below all text: the pattern
    also matches the abbreviation "(церк.-слав.)" in the text, and before this (session 6) a match anywhere in
    the bottom 15 % of any page cut off that line and all below it in both columns — ~18 printed lines lost from
    every witness on pp. 387, 774, 840, 1030 and 1093, the headword Фата among them (MISSING_HEADWORDS.md)."""
    words = [(w[0].strip(),) + tuple(w[1:]) for w in words if w[0].strip()]
    if not words:
        return dict(text='', lines=[], words=[])
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
            if cur:
                # same line when the centre is close, or — for a word much taller or shorter than the line's
                # words (a Church Slavonic headword beside civil text) — when its box overlaps the line's band
                lcy = sum((v[2] + v[4]) / 2 for v in cur) / len(cur)
                lh = sorted(v[4] - v[2] for v in cur)[len(cur) // 2]
                overlap = min(w[4], lcy + lh / 2) - max(w[2], lcy - lh / 2)
                mixed = mixed_lines and max(w[4] - w[2], lh) > 1.3 * min(w[4] - w[2], lh)
                if abs(cy - lcy) > 0.6 * wh and not (mixed and overlap >= 0.4 * min(w[4] - w[2], lh)):
                    lines.append((side, cur))
                    cur = []
            cur.append(w)
        if cur:
            lines.append((side, cur))
    L = []
    for side, ws in lines:
        ws.sort(key=lambda w: w[1])
        L.append(dict(side=side, words=ws, text=' '.join(w[0] for w in ws), n=len(ws),
                      y0=min(w[2] for w in ws), y1=max(w[4] for w in ws),
                      x0=min(w[1] for w in ws), x1=max(w[3] for w in ws)))
    body = [l for l in L if l['side'] != 'w' and (l['n'] >= 3 or len(l['text']) >= 15)]
    top = min(l['y0'] for l in body) if body else 0
    foot = [l for l in L if footer and FOOT_RE.search(l['text']) and l['y0'] > 0.85 * H]
    bottom = max(l['y0'] for l in foot) - 0.3 * wh if foot else H
    keep = [l for l in L if l['y1'] > top - 0.3 * wh and l['y0'] < bottom]
    # page furniture at the foot: a line of one or two short words lying below every other line of the page — the
    # printer's signature ("32 *", on every third page of a sheet), a stray page number, a speck. Each candidate is
    # compared with the other lines only, so that a short last line of a column (a word continued from the line
    # above, e.g. "ство .") is not taken for furniture when the other column ends just as low.
    bot = sorted((l['y1'] for l in keep if l['side'] != 'w'), reverse=True)[:2]
    others = lambda l: (bot[1] if len(bot) > 1 else H) if bot and l['y1'] == bot[0] else (bot[0] if bot else H)
    keep = [l for l in keep
            if not (l['side'] != 'w' and l['n'] <= 2 and len(l['text']) <= 6 and l['y0'] > others(l) - 0.2 * wh)]
    if signature:
        # the signature can also sit level with the lowest line of a column and be clustered into it; there it is
        # the last word, printed in smaller type than the text (p. 115: "Іисусь-Христо- ১*")
        for side in 'ab':
            sel = [l for l in keep if l['side'] == side]
            if not sel:
                continue
            low = max(sel, key=lambda l: l['y1'])
            w = low['words'][-1] if low['n'] >= 2 else None
            lh = sorted(v[4] - v[2] for v in low['words'])[low['n'] // 2] if w else 0
            if w and w[4] - w[2] <= 0.8 * lh and SIG_RE.fullmatch(ascii_digits(w[0])):
                ws = low['words'][:-1]
                low.update(words=ws, text=' '.join(v[0] for v in ws), n=len(ws), y0=min(v[2] for v in ws),
                           y1=max(v[4] for v in ws), x0=min(v[1] for v in ws), x1=max(v[3] for v in ws))
    # bands: cut at full-width lines (headings) and at gaps of > 3 line heights in both columns
    heads = sorted((l['y0'] + l['y1']) / 2 for l in keep if l['side'] == 'w')
    ys = sorted((l['y0'], l['y1']) for l in keep if l['side'] != 'w')
    cuts, reach = list(heads), None
    for y0, y1 in ys:
        if reach is not None and y0 - reach > 3 * wh:
            cuts.append((reach + y0) / 2)
        reach = y1 if reach is None else max(reach, y1)
    cuts.sort()
    # assemble the text, tracking line and word spans
    text, out_lines, out_words = '', [], []
    for band in range(len(cuts) + 1):
        lo = cuts[band - 1] if band else -1e9
        hi = cuts[band] if band < len(cuts) else 1e9
        for side in 'ab':
            sel = sorted((l for l in keep if l['side'] == side and lo <= (l['y0'] + l['y1']) / 2 < hi),
                         key=lambda l: l['y0'])
            first = True                                     # parts (band x side) are joined with one space
            for l in sel:
                if not first and text.endswith(HYPHENS) and not text.endswith(' -'):
                    text = text[:-1]                         # the hyphenated word continues on this line
                    out_words[-1]['end'] -= 1
                    out_lines[-1]['end'] -= 1
                elif text:
                    text += ' '
                first = False
                start = len(text)
                for w in l['words']:
                    ws = len(text)
                    text += w[0]
                    out_words.append(dict(start=ws, end=len(text), box=[w[1], w[2], w[3], w[4]]))
                    text += ' '
                text = text[:-1]
                out_lines.append(dict(start=start, end=len(text), side=side, y0=l['y0'], y1=l['y1'],
                                      x0=l['x0'], x1=l['x1'], n=l['n'], raw=l['text']))
    return dict(text=text, lines=out_lines, words=out_words)


def side_texts(page):
    """reading_order()/page_text() result -> {'a': dict(text, lines), 'b': ...}: the lines of each column side in
    top-to-bottom order (all bands), joined as join_lines does, with the lines' spans in that side's text. Aligning
    per side makes the result independent of how a witness's page was split into bands."""
    out = {}
    for side in 'ab':
        lines = sorted((l for l in page['lines'] if l['side'] == side), key=lambda l: (l['y0'], l['x0']))
        text, spans = '', []
        for l in lines:
            t = l['raw'].strip()
            if not t:
                continue
            if text.endswith(HYPHENS) and not text.endswith(' -'):
                text = text[:-1]
                spans[-1]['end'] -= 1
            elif text:
                text += ' '
            spans.append(dict(l, start=len(text), end=len(text) + len(t)))
            text += t
        out[side] = dict(text=text, lines=spans)
    return out


INDENT = 11.1      # points at W = 450: the hanging indent of the printed columns, measured over the book in C and D


def indent_levels(page, side=None):
    """The indentation level of every printed line of witness B, C or D: 0 for a flush line — the first line of a
    printed paragraph, i.e. of an entry — 1 for a line of the hanging indent, more for a deeper one.

    page: a page_text() result (its `lines` carry x0/y0 and its `words` the word boxes).  -> {(side, y0): level};
    a side whose lines give no level structure is left out, as is a line of it.  The key survives side_texts(),
    which copies the line dicts.

    The columns of both Google scans are skewed, on some pages by more than a whole indent, so the levels cannot
    be read off an absolute edge.  The skew is found by folding the left edges modulo the indent: at the right
    skew the two levels fall on one peak, whatever their proportion (a column of one-line entries is nearly all
    flush, a column inside a long article nearly all hanging).  A speck in the margin, which the OCR reads as a
    word of its own, would make a hanging line look flush: where the first word is one character and the rest of
    the line begins a whole indent further right, the line is measured without it.
    """
    starts = [w['start'] for w in page['words']]
    u = page['W'] / 450.0
    out = {}
    for s in ('ab' if side is None else side):
        lines = [l for l in page['lines'] if l['side'] == s]
        if len(lines) < 6:
            continue
        xs = []
        for l in lines:
            x0 = l['x0']
            i = bisect.bisect_left(starts, l['start'])
            if i + 1 < len(page['words']):
                w0, w1 = page['words'][i], page['words'][i + 1]
                if (w0['start'] == l['start'] and w1['end'] <= l['end'] and w0['end'] - w0['start'] <= 1
                        and w1['box'][0] - w0['box'][0] > 0.7 * INDENT * u):
                    x0 = w1['box'][0]
            xs.append(x0)
        ys = [l['y0'] for l in lines]
        y0 = statistics.median(ys)
        I = INDENT * u
        best = None
        for step, lo, hi in ((4e-4, -2.4e-2, 2.4e-2), (2e-5, None, None)):
            if lo is None:
                lo, hi = best[1] - 4e-4, best[1] + 4e-4
            b = lo
            while b <= hi:
                z = sum(cmath.exp(2j * math.pi * (x - b * (y - y0)) / I) for x, y in zip(xs, ys))
                if best is None or abs(z) > best[0]:
                    best = (abs(z), b)
                b += step
        conc, b = best
        if conc / len(lines) < 0.55:                       # the left edges do not fall into levels: no verdict
            continue
        v = [x - b * (y - y0) for x, y in zip(xs, ys)]
        c = cmath.phase(sum(cmath.exp(2j * math.pi * t / I) for t in v)) * I / (2 * math.pi)
        k = [round((t - c) / I) for t in v]
        lo = min(k)
        for l, kk in zip(lines, k):
            out[(l['side'], l['y0'])] = kk - lo
    return out


def page_text(name, leaf):
    """Body text of witness B, C or D for a leaf, with spans (reading_order)."""
    words, W, H = {'B': words_B, 'C': words_C, 'D': words_D}[name](leaf)
    r = reading_order(words, W, H, mixed_lines=name in 'CD', signature=page_of(leaf) % 16 in (1, 3),
                      footer=page_of(leaf) % 16 == 1)
    r.update(W=W, H=H)
    return r


# ---------------------------------------------------------------- normalisation

CS_CIVIL = {'ѡ': 'о', 'Ѡ': 'О', 'ѿ': 'от', 'Ѿ': 'От', 'ѻ': 'о', 'ꙩ': 'о', 'ꙋ': 'у', 'Ꙋ': 'У', 'ѹ': 'у', 'Ѹ': 'У',
            'ү': 'у', 'Ү': 'У', 'ѕ': 'з', 'Ѕ': 'З', 'ꙁ': 'з', 'Ꙁ': 'З', 'є': 'е', 'Є': 'Е', 'ѥ': 'е', 'Ѥ': 'Е',
            'ї': 'і', 'Ї': 'І', 'ѧ': 'я', 'Ѧ': 'Я', 'ꙗ': 'я', 'Ꙗ': 'Я', 'ѩ': 'я', 'Ѩ': 'Я', 'ѫ': 'у', 'Ѫ': 'У',
            'ѭ': 'ю', 'Ѭ': 'Ю', 'ѯ': 'кс', 'Ѯ': 'Кс', 'ѱ': 'пс', 'Ѱ': 'Пс', 'ꙑ': 'ы', 'ѷ': 'ѵ'}
LOOKALIKE = dict(zip('aceopxyABCEHKMOPTXiIëė', 'асеорхуАВСЕНКМОРТХіІее'))
DASHES, QUOTES = set('—–‐‑−-'), set('„“”"«»‘’\'`')


def norm_char(ch, level='norm'):
    """One raw character -> its normalised form (0-2 characters; '' for whitespace and fillers)."""
    ch = unicodedata.normalize('NFC', ch)
    if ch.isspace() or ch in '¬￼':
        return ''
    if level == 'norm':
        if ch in DASHES:
            ch = '-'
        elif ch in QUOTES:
            ch = '"'
        # diacritics first, then the look-alikes: an accented Latin letter (á in the Sanskrit etymologies) must
        # fold to Cyrillic like a plain one, or it counts as an error against every candidate that reads it plain
        ch = ''.join(c for c in unicodedata.normalize('NFD', ch) if not unicodedata.combining(c))
        ch = CS_CIVIL.get(ch, ch)
        ch = ''.join(LOOKALIKE.get(c, c) for c in ch)
        ch = unicodedata.normalize('NFC', ch)
    return ch


def normalise(chars, level):
    """chars: [(char, tag)] -> [(char, tag)]; whitespace dropped; `level` strict or norm."""
    out = []
    for ch, tag in chars:
        for c in norm_char(ch, level):
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


def norm_seq(text, level='norm'):
    """text -> (norm chars as a list, raw index of each). No оу-merge, so every norm char has one raw origin."""
    seq, idx = [], []
    for i, ch in enumerate(text):
        for c in norm_char(ch, level):
            seq.append(c)
            idx.append(i)
    return seq, idx


# ---------------------------------------------------------------- alignment

def align(a, b):
    """Levenshtein alignment of sequences a and b. Returns (distance, cost_at, j_at): cost_at[i] = edits charged
    to position i of a (substitution/deletion of a[i], plus insertions just before it), j_at[i] = the position of b
    aligned with a[i] (for a deleted a[i]: the position of b where it would be)."""
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


def readings(a, b):
    """For every position of a: what b has there — the aligned character plus insertions before the next position
    of a ('' for a deletion). Uses align(a, b)."""
    _, cost_at, j_at = align(a, b)
    out = []
    for i in range(len(a)):
        j0 = j_at[i]
        j1 = j_at[i + 1] if i + 1 < len(a) else len(b)
        out.append(''.join(b[j0:j1]) if j1 > j0 else '')
    return out, cost_at, j_at


def load_page(leaf):
    return json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))
