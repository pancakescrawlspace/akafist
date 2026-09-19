#!/usr/bin/env python3
"""Phase 3a of djachenko/PLAN.md: turn the ABBYY FineReader XML of the archive.org scan into one
djachenko/ocr/NNNN.json per leaf, and fill the section/letter columns of djachenko/manifest.tsv.

    python3 tools/dj_abbyy.py                  # all leaves -> ocr/NNNN.json (parallel), then ocr/report.tsv
    python3 tools/dj_abbyy.py --pages 140-160  # only these leaves (ranges, comma-separated)
    python3 tools/dj_abbyy.py --manifest       # section + letter columns from the book's table of contents,
                                               # cross-checked against the letter headings found in ocr/*.json
    python3 tools/dj_abbyy.py --report         # rewrite ocr/report.tsv from ocr/*.json and print a summary

Deterministic, no network. Re-running is safe: headwords filled in later (Phase 3b, `entries_hint[].headword`) are
carried over to the new file by position; hints that no longer match are kept under `orphan_hints`.

Page JSON (all coordinates in pixels of the 600 ppi leaf, as in the JP2 files; halve them for pages/NNNN.jpg):

    idx, printed_page, section           leaf number, printed page (from manifest.tsv), front|main|blank|supplement|back
    size, dpi, source                    [4252, 6520], 600, "abbyy"
    rule                                 column rule x = rule[0] + rule[1]·y, or null (no two-column layout found)
    header                               {page_number, running_title, guide_words: [left, right]} — raw OCR text
    footer                               signature line(s) at the foot of the page, raw text
    headings                             [{bbox, kind: text|picture, text, before_col}] big letter initials, titles;
                                         before_col = n of the first column below it (null: none follows)
    figures                              [bbox] other picture blocks (ornaments, stains)
    columns                              [{n, side: a|b, band, bbox, flush, indent, paragraphs}] in reading order:
                                         band by band (bands are separated by headings), left column first.
                                         flush = x of the column's flush edge at y=0 relative to the rule;
                                         indent = hanging indent in px
      paragraphs                         [{bbox, hanging, [guessed], lines}]: a new paragraph starts at every
                                         flush line; hanging = starts flush (an entry candidate); the first
                                         paragraph of a column with hanging=false continues the previous column;
                                         guessed = the start was decided from text features (margin cut off in
                                         the scan, or a dropped first letter), not from the geometry
        lines                            {bbox, base, ind, fs, text, words}; ind 0 = flush, 1 = indented,
                                         2 = deeper; fs = dominant ABBYY font size; text = ABBYY characters as is
                                         (¬ marks a hyphen at the line end)
          words                          [text, l, t, r, b, conf, flags, fs]; conf = mean ABBYY char confidence
                                         (0–100, -1 unknown); flags: i italic, b bold, s smallcaps,
                                         o lang=RussianOldSpelling, d word in ABBYY's dictionary, ? mostly suspicious
    noise                                [{bbox, text}] tiny fragments left out of the columns
    entries_hint                         one per hanging paragraph in main/supplement pages:
                                         {col, para, bbox, abbyy, abbyy_conf, eq, headword, headword_source, conf}
                                         col = columns[].n, para = 1-based paragraph number in that column,
                                         bbox/abbyy = the text before the first "=", "—" or "(" on the first line
                                         (ABBYY's reading of the headword, usually garbled), eq = "=" in the first
                                         two lines; headword/headword_source/conf are filled by Phase 3b
    warnings                             [str]
"""
import argparse, csv, gzip, json, re, statistics
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DJ = ROOT / 'djachenko'
OCR, MANIFEST = DJ / 'ocr', DJ / 'manifest.tsv'
ABBYY = DJ / 'scan' / 'Дьяченко. Полный церковнославянский словарь_abbyy.gz'

# Leaf ranges (0-based leaf numbers; printed page = leaf - 37 from leaf 38 on, see SOURCE.md).
FRONT, MAIN, BLANK, SUPP, BACK = range(0, 38), range(38, 901), (901,), range(902, 1158), (1158,)

# Letter page ranges from the book's table of contents (leaf 37). Letters in civil script: the book's Є, Ꙁ, Ꙋ, Ѧ
# are given as Е, З, У, Я; the rare letters at the end keep their own form. The TOC prints Ѩ as "826—857", a misprint
# for 856—857.
MAIN_LETTERS = [
    ('А', 1, 30), ('Б', 31, 65), ('В', 65, 118), ('Г', 118, 135), ('Д', 135, 164), ('Е', 164, 178),
    ('Ж', 178, 188), ('З', 189, 208), ('И', 208, 233), ('І', 233, 240), ('К', 240, 277), ('Л', 277, 294),
    ('М', 295, 326), ('Н', 326, 359), ('О', 359, 402), ('П', 402, 533), ('Р', 533, 567), ('С', 567, 705),
    ('Т', 705, 745), ('У', 745, 772), ('Ф', 772, 780), ('Х', 780, 799), ('Ц', 799, 807), ('Ч', 808, 830),
    ('Ш', 830, 837), ('Щ', 837, 839), ('Ъ', 839, 840), ('Ы', 840, 840), ('Ь', 840, 840), ('Ѣ', 841, 842),
    ('Ю', 842, 846), ('Я', 846, 854), ('Ѥ', 854, 854), ('Ѫ', 855, 856), ('Ѩ', 856, 857), ('Ѭ', 857, 857),
    ('Ѯ', 858, 858), ('Ѱ', 858, 858), ('Ѳ', 858, 862), ('Ѵ', 862, 863)]
SUPP_LETTERS = [
    ('А', 865, 883), ('Б', 883, 912), ('В', 912, 942), ('Г', 942, 957), ('Д', 957, 974), ('Е', 974, 978),
    ('Ж', 978, 981), ('З', 981, 993), ('И', 993, 1001), ('І', 1001, 1003), ('К', 1004, 1031), ('Л', 1031, 1040),
    ('М', 1040, 1051), ('Н', 1052, 1062), ('О', 1062, 1078), ('П', 1078, 1097), ('Р', 1097, 1101),
    ('С', 1101, 1111), ('Т', 1111, 1115), ('У', 1115, 1116), ('Ф', 1116, 1117), ('Х', 1117, 1117),
    ('Ц', 1118, 1118), ('Ч', 1118, 1119), ('Ш', 1119, 1119), ('Ѣ', 1119, 1119), ('Ю', 1120, 1120),
    ('Я', 1120, 1120)]

# Geometry, measured over the whole book (600 ppi): flush text of the right column starts ~62 px right of the column
# rule; the hanging indent is ~100-130 px; printed column width ~1930 px.
RULE_TO_B = 62
INDENT = 115
COL_WIDTH = 1930
WIDTH_A_MINUS_B = {0: -38, 1: 59}   # left minus right column width in the scan, by leaf parity (page curvature)
GUTTER = (40, 30)               # characters centred between rule-40 and rule+30 are specks in the gutter
SPECKS = set('■|*•\'`,.;:!/\\~^°')
BIG = 110                       # median character height (px) from which a line counts as big type
CLIPPED = 4                     # a line starting at x <= 4 touches the image edge: the scan cut the margin off
FOOT_RE = re.compile(r'Ц[еѳ]рк\W{0,3}сла|словарь,?\s*свящ', re.I)
FOOT_TAIL = re.compile(r'^\W*Дь[яа]ч')
HW_END = re.compile(r'=|—|–|\(|\s-\s|\s-$')


def section_of(leaf):
    for name, rng in (('front', FRONT), ('main', MAIN), ('blank', BLANK), ('supplement', SUPP), ('back', BACK)):
        if leaf in rng:
            return name
    return ''


# ---------------------------------------------------------------- reading the ABBYY file

def page_chunks(wanted=None):
    """Yield (leaf, xml) for each <page> element of the ABBYY file, in document order (= leaf order)."""
    leaf, buf, keep = -1, None, False
    with gzip.open(ABBYY, 'rt', encoding='utf-8-sig') as f:
        for line in f:
            if buf is None:
                i = line.find('<page ')
                if i < 0:
                    continue
                leaf += 1
                keep = wanted is None or leaf in wanted
                buf, line = [], line[i:]
            j = line.find('</page>')
            if j >= 0:
                if keep:
                    buf.append(line[:j + 7])
                    yield leaf, ''.join(buf)
                buf = None
            elif keep:
                buf.append(line)


def box(e):
    return [int(e.get('l')), int(e.get('t')), int(e.get('r')), int(e.get('b'))]


def union(boxes):
    boxes = list(boxes)
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def parse_page(xml):
    """ABBYY <page> -> dict(width, height, lines, pictures, seps). A line is a dict with box, base and chars; a char is
    (text, box, conf, suspicious, word_first, from_dictionary, fmt) with fmt = (fs, flags)."""
    root = ET.fromstring(xml)
    pg = dict(width=int(root.get('width')), height=int(root.get('height')), lines=[], pictures=[], seps=[])
    for blk in root.iter('block'):
        bt = blk.get('blockType')
        if bt == 'Picture':
            pg['pictures'].append(box(blk))
        elif bt == 'Separator':
            for s in blk.iter('separator'):
                a, b = s.find('start'), s.find('end')
                pg['seps'].append((int(a.get('x')), int(a.get('y')), int(b.get('x')), int(b.get('y'))))
        for ln in blk.iter('line'):
            chars = []
            for fm in ln.iter('formatting'):
                flags = ''.join(f for f, on in (('i', fm.get('italic')), ('b', fm.get('bold')),
                                                ('s', fm.get('smallcaps')),
                                                ('o', fm.get('lang') == 'RussianOldSpelling' or None)) if on)
                fmt = (float(fm.get('fs', 0)), flags)
                for c in fm.iter('charParams'):
                    chars.append((c.text or '', box(c), int(c.get('charConfidence', -1)), c.get('suspicious') == '1',
                                  c.get('wordFirst') == '1', c.get('wordFromDictionary') == '1', fmt))
            if chars:
                pg['lines'].append(dict(box=box(ln), base=int(ln.get('baseline')), chars=chars))
    return pg


# ---------------------------------------------------------------- lines and words

def text_of(chars):
    return ''.join(c[0] for c in chars)


def nonspace(chars):
    return [c for c in chars if c[0].strip()]


def dominant(values):
    values = list(values)
    return max(sorted(set(values)), key=values.count) if values else None


def mean_conf(chars):
    cs = [c[2] for c in chars if c[2] >= 0]
    return round(sum(cs) / len(cs)) if cs else -1


def fs_of(chars):
    fs = dominant(c[6][0] for c in nonspace(chars))
    return int(fs) if fs is not None and fs == int(fs) else fs


def leading_speck(chars):
    """Number of chars at the start of a line that form a speck: a first "word" of at most two characters that lies
    wholly below the baseline (dust, bleed-through), or that is tiny or made of speck-like marks and stands more than
    60 px left of the next word; else 0."""
    ns = [i for i, c in enumerate(chars) if c[0].strip()]
    if len(ns) < 2:
        return 0
    first = [ns[0]]
    for i in ns[1:]:
        if chars[i][4] or i != first[-1] + 1:
            break
        first.append(i)
    nxt = [i for i in ns if i > first[-1]]
    if len(first) > 2 or not nxt:
        return 0
    fw = [chars[i] for i in first]
    b = union(c[1] for c in fw)
    t = text_of(fw)
    gap = chars[nxt[0]][1][0] - b[2]
    if any(ch in '—–-' for ch in t):                # a dash may legitimately open a line
        return 0
    if any(ch in '(„"«[' for ch in t):              # so may a bracket or quote (up to ~30 px before italics)
        return nxt[0] if gap > 45 and all(ch in '(„"«[,.\'' for ch in t) else 0
    base = statistics.median(chars[i][1][3] for i in nxt)     # ABBYY's own baseline is not always right
    if b[1] >= base - 12:
        return nxt[0]
    speck = (b[2] - b[0] < 35 and b[3] - b[1] < 35) or all(ch in SPECKS for ch in t)
    return nxt[0] if speck and gap > 60 else 0


def entry_start_score(ln, prev, redge):
    """Log-odds that a line starts an entry, from features that survive a cut-off margin (naive Bayes, fitted on the
    pages where the geometry is unambiguous: recall 0.89, precision 0.97)."""
    t = text_of(ln['chars']).strip()
    ws = words_of(ln['chars'])
    score = -1.22
    for on, (yes, no) in (('=' in t, (3.91, -1.69)),
                          (bool(re.search(r'^\S+(\s\S+)?\s[—-]\s', t)), (2.36, -0.17)),
                          (bool(ws) and 's' in ws[0][6], (5.25, -0.28))):
        score += yes if on else no
    if prev is not None:
        pt = text_of(prev['chars']).strip()
        for on, (yes, no) in ((prev['box'][2] < redge - 120, (5.95, -1.36)),
                              (pt.endswith(('¬', '-')), (-2.36, 0.36)),
                              (pt.endswith(('.', ')', '»', '“')), (1.94, -1.99))):
            score += yes if on else no
    return score


def char_height(chars):
    ns = nonspace(chars)
    return statistics.median(c[1][3] - c[1][1] for c in ns) if ns else 0


def big(ln):
    """Big type: letter initials (136-304 px high) and titles; ordinary text is at most ~70 px."""
    return char_height(ln['chars']) >= BIG


def make_line(chars, base):
    return dict(box=union(c[1] for c in nonspace(chars) or chars), base=base, chars=chars)


def words_of(chars):
    words, cur = [], []
    for c in chars:
        if not c[0].strip():
            if cur:
                words.append(cur)
            cur = []
            continue
        if c[4] and cur:
            words.append(cur)
            cur = []
        cur.append(c)
    if cur:
        words.append(cur)
    out = []
    for w in words:
        fl = dominant(c[6][1] for c in w) or ''
        if w[0][5]:
            fl += 'd'
        if sum(c[3] for c in w) * 2 >= len(w):
            fl += '?'
        b = union(c[1] for c in w)
        out.append([text_of(w), *b, mean_conf(w), fl, fs_of(w)])
    return out


def line_json(ln, ind):
    return dict(bbox=ln['box'], base=ln['base'], ind=ind, fs=fs_of(ln['chars']), text=text_of(ln['chars']).strip(),
                words=words_of(ln['chars']))


# ---------------------------------------------------------------- page layout

def fit_rule(seps, W):
    """The vertical column rule: x = g0 + g1*y from the longest near-central vertical separator (and its collinear
    pieces)."""
    vs = [s for s in seps if abs(s[0] - s[2]) < 60 and abs(s[3] - s[1]) > 400 and 0.3 * W < (s[0] + s[2]) / 2 < 0.7 * W]
    if not vs:
        return None
    longest = max(vs, key=lambda s: abs(s[3] - s[1]))
    mid = (longest[0] + longest[2]) / 2
    vs = [s for s in vs if abs((s[0] + s[2]) / 2 - mid) < 60]
    pts = [(p, w) for s in vs for p, w in (((s[0], s[1]), abs(s[3] - s[1])), ((s[2], s[3]), abs(s[3] - s[1])))]
    sw = sum(w for _, w in pts)
    my = sum(p[1] * w for p, w in pts) / sw
    mx = sum(p[0] * w for p, w in pts) / sw
    vy = sum(w * (p[1] - my) ** 2 for p, w in pts)
    g1 = sum(w * (p[1] - my) * (p[0] - mx) for p, w in pts) / vy if vy else 0.0
    g1 = max(-0.01, min(0.01, g1))
    return [round(mx - g1 * my, 1), round(g1, 5)]


def gutter_from_lines(lines, W):
    """No rule: the x in the middle of the page crossed by the fewest body lines, or None for a single column."""
    body = [ln['box'] for ln in lines if ln['box'][2] - ln['box'][0] > 300]
    if len(body) < 10:
        return None
    best = min(range(int(0.3 * W), int(0.7 * W), 10),
               key=lambda x: (sum(1 for b in body if b[0] < x < b[2]), abs(x - W / 2)))
    crossing = sum(1 for b in body if b[0] < best < b[2])
    return [float(best), 0.0] if crossing <= 0.1 * len(body) else None


def flush_edge(rels, prior, slack=None, per_line=10):
    """Most plausible (flush edge, indent) for a column's line starts `rels` (relative to the rule). A line scores +1
    when flush (within ±35 px of the edge) or indented (within ±45 px of the indent, itself the median offset of the
    lines 50-230 px right of the edge), 0 when deeper, -1 otherwise. Ties — e.g. a column without a single entry
    start, where "all flush" and "all indented" explain the lines equally well — go to the candidate nearest the
    prior. With `slack`, an edge further than `slack` px from the prior costs one line per `per_line` px beyond it
    (deeper-set quotations must not pull the edge to the indent of a long article)."""
    cands = {round(r) - k for r in rels for k in (0, 90, 120, 150)} | {round(prior)}

    def fit(F):
        ds = [r - F for r in rels]
        ind = [d for d in ds if 50 <= d <= 230]
        ind = statistics.median(ind) if ind else INDENT
        s = sum(1 if abs(d) <= 35 or abs(d - ind) <= 45 else 0 if d > ind else -1 for d in ds)
        pen = max(0, abs(F - prior) - slack) / per_line if slack is not None else 0
        return s - pen - abs(F - prior) / 1000, ind
    F = max(sorted(cands), key=lambda F: fit(F)[0])
    flush = [r - F for r in rels if abs(r - F) <= 35]
    if flush:                                   # centre the edge on the flush lines themselves
        F += statistics.median(flush)
    return F, fit(F)[1]


def layout(leaf, pg, printed):
    W, H = pg['width'], pg['height']
    sec = section_of(leaf)
    warnings = []
    lines = pg['lines']

    # -- column rule
    rule = fit_rule(pg['seps'], W)
    if rule is None:
        rule = gutter_from_lines(lines, W)
        if sec in ('main', 'supplement'):
            warnings.append('no column rule found' + ('; gutter from line positions' if rule else '; single column'))

    def gx(y):
        return rule[0] + rule[1] * y if rule else None

    # -- header: short lines above the first body line near the top of the page
    def body_like(ln):
        b, t = ln['box'], text_of(ln['chars']).strip()
        return b[2] - b[0] > 1000 and len(t) > (b[2] - b[0]) / 80 and (fs_of(ln['chars']) or 0) < 16
    first_base = min((ln['base'] for ln in lines if body_like(ln)), default=H)
    centre_x = (lambda y: gx(y)) if rule else (lambda y: W / 2)

    def initial_like(ln):
        """Big type standing on the column rule (a letter initial), not a tall letter inside a headword."""
        b = ln['box']
        g = centre_x(ln['base'])
        return big(ln) and b[2] - b[0] >= 80 and b[0] < g - 20 and b[2] > g - 60

    def title_like(ln):
        t = text_of(ln['chars']).strip()
        return (fs_of(ln['chars']) or 0) >= 20 and len(t) >= 20 and char_height(ln['chars']) >= 85
    header = [ln for ln in lines if ln['box'][1] < 0.12 * H and ln['base'] < first_base - 40 and not initial_like(ln)]
    hids = {id(ln) for ln in header}
    rest = [ln for ln in lines if id(ln) not in hids]

    # -- footer: the signature line ("Церк.-славян. словарь свящ. Г. Дьяченко.", on the first page of each sheet), the
    #    signature number level with it, and anything below it
    foot = [ln for ln in rest if ln['box'][1] > 0.88 * H and FOOT_RE.search(text_of(ln['chars']))]
    footer = []
    if foot:
        fb = min(ln['base'] for ln in foot) - 50
        fbot = max(ln['box'][3] for ln in foot)
        fids = {id(ln) for ln in foot}
        footer = [ln for ln in rest if id(ln) in fids or ln['box'][1] > fbot or
                  (ln['base'] >= fb and (len(nonspace(ln['chars'])) <= 6 or FOOT_TAIL.search(text_of(ln['chars']))))]
        fids = {id(ln) for ln in footer}
        rest = [ln for ln in rest if id(ln) not in fids]
    header_bottom = max((ln['box'][3] for ln in header), default=0)

    # -- headings: big type (letter initials, the supplement's title), and pictures across the column rule (letter
    #    initials ABBYY did not read); they cut the page into bands. ABBYY also turned some headwords with tall
    #    superscripts into pictures: those stay in the text as a placeholder word (U+FFFC, flag p) where they stand.
    headings, figures, cuts, inline = [], [], [], []
    body = []
    for ln in rest:
        b = ln['box']
        t = text_of(ln['chars']).strip()
        if initial_like(ln) or title_like(ln):
            headings.append(dict(bbox=b, kind='text', text=t))
        else:
            body.append(ln)
    body_bottom = fb if foot else H
    for p in pg['pictures']:
        w, h = p[2] - p[0], p[3] - p[1]
        g = gx((p[1] + p[3]) / 2) if rule else None
        inside = p[1] > header_bottom and p[3] < body_bottom + 50
        if inside and rule and p[0] < g - 50 and p[2] > g + 50 and 100 < h < 1000 and w < 2000:
            headings.append(dict(bbox=p, kind='picture', text=''))
        else:
            figures.append(p)
            if inside and sec in ('main', 'supplement') and h < 400 and w < 1500 and \
                    (not rule or p[2] <= g + 30 or p[0] >= g - 30):
                inline.append(p)
    # letter initials ABBYY recorded neither as text nor as picture: a gap of 250-900 px across both columns, with text
    # of both columns above and below it
    if rule and sec in ('main', 'supplement'):
        occ = sorted(ln['box'][1:4:2] for ln in body if len(nonspace(ln['chars'])) >= 3)
        top_b = None
        for t, b in occ:
            if top_b is not None and top_b + 250 < t < top_b + 900 and \
                    not any(h['bbox'][1] < t and h['bbox'][3] > top_b for h in headings):
                sides = lambda sel: {'a' if (ln['box'][0] + ln['box'][2]) / 2 < gx(ln['base']) else 'b' for ln in sel}
                if sides(ln for ln in body if ln['box'][3] <= top_b) == {'a', 'b'} == \
                        sides(ln for ln in body if ln['box'][1] >= t):
                    g = gx((top_b + t) / 2)
                    headings.append(dict(bbox=[round(g - 250), top_b, round(g + 250), t], kind='gap', text=''))
            top_b = b if top_b is None else max(top_b, b)
    headings.sort(key=lambda h: h['bbox'][1])
    cuts = [(h['bbox'][1] + h['bbox'][3]) / 2 for h in headings]
    if rule:
        for s in pg['seps']:
            if abs(s[1] - s[3]) < 60 and abs(s[2] - s[0]) > 0.3 * W and min(s[0], s[2]) < gx(s[1]) < max(s[0], s[2]) \
                    and s[1] > header_bottom:
                cuts.append((s[1] + s[3]) / 2)
    cuts.sort()

    # -- drop specks in the gutter (the strip around the rule), split lines that run across the rule; set tiny
    #    fragments aside as noise
    noise, placed = [], []
    for ln in body:
        g = gx(ln['base'])
        if rule and sec in ('main', 'supplement'):
            gut = [c for c in ln['chars'] if c[0].strip() and g - GUTTER[0] < (c[1][0] + c[1][2]) / 2 < g + GUTTER[1]]
            if gut:
                noise.append(dict(bbox=union(c[1] for c in gut), text=text_of(gut)))
                keep = [c for c in ln['chars'] if not any(c is x for x in gut)]
                if not nonspace(keep):
                    continue
                ln = make_line(keep, ln['base'])
        k = leading_speck(ln['chars']) if sec in ('main', 'supplement') else 0
        if k:
            sp = ln['chars'][:k]
            noise.append(dict(bbox=union(c[1] for c in nonspace(sp)), text=text_of(sp).strip()))
            ln = make_line(ln['chars'][k:], ln['base'])
        b = ln['box']
        if rule and b[0] < g - 30 and b[2] > g + 30:
            left = [c for c in ln['chars'] if (c[1][0] + c[1][2]) / 2 < g]
            right = [c for c in ln['chars'] if (c[1][0] + c[1][2]) / 2 >= g]
            parts = [p for p in (left, right) if nonspace(p)]
        else:
            parts = [ln['chars']]
        for p in parts:
            part = make_line(p, ln['base'])
            ns = nonspace(p)
            tiny = sec in ('main', 'supplement') and len(ns) <= 2 and \
                (fs_of(p) <= 8 or 0 <= mean_conf(p) < 40 or not any(c[0].isalnum() for c in ns))
            if tiny or (len(parts) > 1 and len(ns) <= 2 and abs((part['box'][0] + part['box'][2]) / 2 - g) < 200):
                noise.append(dict(bbox=part['box'], text=text_of(p).strip()))
            else:
                placed.append(part)

    # -- headword pictures: prepend a placeholder to the line they start, or make them a line of their own
    for p in inline:
        pc = ('\ufffc', list(p), -1, False, True, False, (0, 'p'))
        side_p = None if not rule else ('a' if (p[0] + p[2]) / 2 < gx((p[1] + p[3]) / 2) else 'b')

        def overlap(ln):
            return min(ln['box'][3], p[3]) - max(ln['box'][1], p[1])
        cands = [ln for ln in placed if overlap(ln) > 0.4 * (ln['box'][3] - ln['box'][1]) and
                 ln['box'][0] >= p[2] - 30 and ln['box'][0] - p[2] < 300 and
                 (side_p is None or ('a' if (ln['box'][0] + ln['box'][2]) / 2 < gx(ln['base']) else 'b') == side_p)]
        if cands:
            ln = max(cands, key=overlap)
            sp = (' ', [p[2], ln['box'][1], ln['box'][0], ln['box'][3]], -1, False, False, False, (0, ''))
            new = make_line([pc, sp] + ln['chars'], ln['base'])
            placed[next(i for i, x in enumerate(placed) if x is ln)] = new
        else:
            placed.append(make_line([pc], p[3]))

    # -- columns: (band, side); merge fragments of one printed line
    groups = {}
    for ln in placed:
        cy = (ln['box'][1] + ln['box'][3]) / 2
        band = 1 + sum(1 for c in cuts if c < cy)
        side = 'a' if not rule or (ln['box'][0] + ln['box'][2]) / 2 < gx(ln['base']) else 'b'
        groups.setdefault((band, side), []).append(ln)
    for key, lns in groups.items():
        lns.sort(key=lambda ln: (ln['base'], ln['box'][0]))
        # a tall letter of a headword (Ѱ, ѵ with superscripts) can come out as a line of its own: put it back
        small = [ln for ln in lns if len(nonspace(ln['chars'])) <= 3]
        for sm in small:
            host = max((ln for ln in lns if ln is not sm and len(nonspace(ln['chars'])) > 3),
                       key=lambda ln: min(ln['box'][3], sm['box'][3]) - max(ln['box'][1], sm['box'][1]), default=None)
            h = sm['box'][3] - sm['box'][1]
            if host is not None and min(host['box'][3], sm['box'][3]) - max(host['box'][1], sm['box'][1]) >= 0.5 * h \
                    and host['box'][0] - 150 <= sm['box'][0] <= host['box'][2]:
                chars = sorted(host['chars'] + [c for c in sm['chars'] if c[0].strip()],
                               key=lambda c: (c[1][0] + c[1][2]) / 2)
                lns[next(i for i, x in enumerate(lns) if x is host)] = make_line(chars, host['base'])
                lns.remove(sm)
        merged = []
        for ln in lns:
            prev = merged[-1] if merged else None
            if prev and abs(ln['base'] - prev['base']) < 25 and \
                    (ln['box'][0] >= prev['box'][2] - 10 or ln['box'][2] <= prev['box'][0] + 10):
                a, b = sorted((prev, ln), key=lambda x: x['box'][0])
                gap = (' ', [b['box'][0] - 1, a['box'][1], b['box'][0], a['box'][3]], -1, False, False, False, (0, ''))
                merged[-1] = make_line(a['chars'] + [gap] + b['chars'], min(a['base'], b['base']))
            else:
                merged.append(ln)
        groups[key] = merged

    # -- flush edge and indent per side, over all bands (relative to the rule, which removes the page skew)
    def rel(ln):
        return ln['box'][0] - (gx(ln['base']) if rule else 0)

    def right(ln):
        return ln['box'][2] - (gx(ln['base']) if rule else 0)
    edges = {}
    for side in ('b', 'a'):
        lns = [ln for (band, s), l in groups.items() if s == side for ln in l]
        if not lns:
            continue
        rs = sorted(right(ln) for ln in lns)
        redge = statistics.median(rs[len(rs) // 3:])
        clipped = [ln for ln in lns if ln['box'][0] <= CLIPPED]
        free = [rel(ln) for ln in lns if ln['box'][0] > CLIPPED]
        mode = 'fit'
        if not rule:
            prior = min(free) if free else 0
        elif side == 'b':
            prior = RULE_TO_B
        else:
            wb = edges.get('b', {}).get('width')
            if not wb or not 1830 <= wb <= 2040:        # right margin cut off, or no flush lines on the right
                wb = COL_WIDTH
            prior = redge - (wb + WIDTH_A_MINUS_B[leaf % 2])
            if len(clipped) >= 3:   # the scan cut the left margin off: several lines start at the image edge
                mode = 'cut'
        if mode == 'cut':
            # the flush lines lost their start; where the indented lines still show a common edge, take it
            F, ind = prior, edges.get('b', {}).get('indent') or INDENT
            xs = [ln['box'][0] for ln in lns]
            mid = [x for x in xs if 25 < x < 200]
            iobs = statistics.median(mid) if len(mid) >= 0.3 * len(xs) else None
            nflush = None
        else:
            iobs = None
            slack, per_line = (None, 10) if not rule else (30, 10) if side == 'b' else (60, 15)
            F, ind = flush_edge(free, prior, slack, per_line) if free else (prior, INDENT)
            # a column of one long article (no entry start, quotations set deeper) can pass for flush lines with a
            # deeper indent; real entry starts nearly always have "=" (82 %), continuation lines hardly ever (2 %)
            fl = [ln for ln in lns if ln['box'][0] > CLIPPED and rel(ln) - F < 45]
            if len(fl) >= 5 and len(fl) > 0.5 * len(lns) and \
                    sum('=' in text_of(ln['chars']) for ln in fl) < 0.25 * len(fl):
                other = edges.get('b', {}).get('indent')
                F -= other if other and 80 <= other <= 150 else INDENT
                ds = [r - F for r in free if 50 <= r - F <= 230]
                ind = statistics.median(ds) if ds else INDENT
                warnings.append(f'side {side}: lines at the edge lack "=", taken as continuation lines')
            nflush = sum(1 for r in free if r - F < 45) + len(clipped)
            if nflush == 0 and sec in ('main', 'supplement'):
                warnings.append(f'side {side}: no flush line (edge from prior)')
        width = (redge - F) if nflush and nflush >= 3 else None
        edges[side] = dict(F=F, indent=ind, width=width, redge=redge, mode=mode, iobs=iobs)
        if mode == 'cut':
            warnings.append(f'side {side}: margin cut off in the scan ({len(clipped)} lines at the image edge); '
                            f'entry starts from position and text features')

    def ind_of(ln, side, prev):
        """0 flush, 1 indented, 2 deeper; plus whether the decision is a guess from text features."""
        e = edges[side]
        if e['mode'] == 'fit':
            if ln['box'][0] <= CLIPPED:
                return 0, False
            d = rel(ln) - e['F']
            return (0 if d < max(35, min(70, e['indent'] / 2)) else 1 if d < e['indent'] + 110 else 2), False
        x, io = ln['box'][0], e['iobs']
        if io is not None and x > io + 110:
            return 2, False
        # log-odds from the position, measured on these pages against confident text decisions
        geo = 0.0
        if x <= 12:
            geo = 3.7
        elif io is not None:
            dx = x - io
            geo = 3.6 if dx < -30 else 0.4 if dx < -20 else -3.7 if dx <= 20 else -1.0
        s = entry_start_score(ln, prev, e['redge'] + (gx(ln['base']) if rule else 0)) + geo
        return (0 if s > 0 else 1), True

    def margin_speck(ln, side):
        """A letter-like speck at the flush edge in front of an indented line (bleed-through, dirt): the first word
        has at most two characters, the next word starts at the indent, and there is no "=" early in the line."""
        e = edges[side]
        if e['mode'] != 'fit' or sec not in ('main', 'supplement'):
            return 0
        ch = ln['chars']
        k = next((i for i, c in enumerate(ch) if i and (not c[0].strip() or c[4])), 0)
        nxt = next((i for i in range(k, len(ch)) if ch[i][0].strip()), None)
        if not k or nxt is None or len(nonspace(ch[:k])) > 2 or '\ufffc' in text_of(ch[:k]):
            return 0
        t = text_of(ch).strip()
        if 0 <= t.find('=') < 0.4 * len(t) or any(c in text_of(ch[:k]) for c in '—–-'):
            return 0
        off = gx(ln['base']) if rule else 0
        d1 = ln['box'][0] - off - e['F']
        d2 = ch[nxt][1][0] - off - e['F']
        return nxt if d1 < 45 and abs(d2 - e['indent']) <= 45 and ch[nxt][1][0] - ch[k - 1][1][2] > 50 else 0

    def missed_start(ln, prev, side):
        """An indented line that looks like an entry start whose first letter ABBYY dropped: "=" in the first 40 %,
        after a short line that ends a sentence."""
        if prev is None:
            return False
        t, pt = text_of(ln['chars']).strip(), text_of(prev['chars']).strip()
        off = gx(ln['base']) if rule else 0
        return 0 <= t.find('=') < 0.4 * len(t) and prev['box'][2] - off < edges[side]['redge'] - 120 and \
            pt.endswith(('.', ')', '»', '“'))

    # -- paragraphs
    columns = []
    for (band, side) in sorted(groups):
        paras, prev = [], None
        for i, ln in enumerate(groups[(band, side)]):
            k = margin_speck(ln, side)
            if k:
                noise.append(dict(bbox=union(c[1] for c in nonspace(ln['chars'][:k])),
                                  text=text_of(ln['chars'][:k]).strip()))
                ln = groups[(band, side)][i] = make_line(ln['chars'][k:], ln['base'])
            ind, guess = ind_of(ln, side, prev)
            if ind == 1 and edges[side]['mode'] == 'fit' and missed_start(ln, prev, side):
                ind, guess = 0, True
            if ind == 0 or not paras:
                paras.append(dict(bbox=None, hanging=ind == 0, guessed=guess and ind == 0, lines=[]))
            paras[-1]['lines'].append((ln, ind))
            prev = ln
        pj = []
        for p in paras:
            par = dict(bbox=union(ln['box'] for ln, _ in p['lines']), hanging=p['hanging'])
            if p['guessed']:
                par['guessed'] = True
            par.update(lines=[line_json(ln, ind) for ln, ind in p['lines']], _raw=p['lines'])
            pj.append(par)
        e = edges[side]
        columns.append(dict(n=len(columns) + 1, side=side, band=band, bbox=union(p['bbox'] for p in pj),
                            flush=round(e['F']), indent=round(e['indent']), paragraphs=pj))
    for h in headings:
        cy = h['bbox'][3]
        after = [c['n'] for c in columns if c['bbox'][1] >= cy - 50]
        h['before_col'] = min(after) if after else None

    # -- entry hints: ABBYY's reading of the headword of every hanging paragraph
    hints = []
    if sec in ('main', 'supplement'):
        for c in columns:
            for pi, p in enumerate(c['paragraphs'], 1):
                if not p['hanging']:
                    continue
                first = p['_raw'][0][0]['chars']
                t = text_of(first)
                m = HW_END.search(t, 1)
                end = m.start() if m else (t.find(' ', 1) if ' ' in t[1:] else len(t))
                hw = first[:end]
                while hw and not (hw[-1][0].isalnum() or hw[-1][0] in "'’`^|"):
                    hw = hw[:-1]
                hw = hw or first[:1]
                two = ' '.join(ln['text'] for ln in p['lines'][:2])
                hints.append(dict(col=c['n'], para=pi, bbox=union(ch[1] for ch in nonspace(hw) or hw),
                                  abbyy=text_of(hw).strip(), abbyy_conf=mean_conf(hw), eq='=' in two,
                                  headword=None, headword_source=None, conf=None))
    for c in columns:
        for p in c['paragraphs']:
            del p['_raw']

    # -- header items: split header words into groups by horizontal gaps; centre = page number / running title
    groups_h = []
    for ln in header:                   # words of one header line, split where the gap is wide
        for w in words_of(ln['chars']):
            if groups_h and groups_h[-1][0] is ln and w[1] - groups_h[-1][1][-1][3] < 150:
                groups_h[-1][1].append(w)
            else:
                groups_h.append((ln, [w]))
    groups_h = [g for _, g in groups_h]
    hdr = dict(page_number='', running_title='', guide_words=['', ''])
    centre = gx(0) if rule else W / 2
    centred = []
    for g in groups_h:
        l, r = min(w[1] for w in g), max(w[3] for w in g)
        txt = ' '.join(w[0] for w in g)
        if l < centre - 300 and r < centre - 200:
            hdr['guide_words'][0] = (hdr['guide_words'][0] + ' ' + txt).strip()
        elif l > centre + 200:
            hdr['guide_words'][1] = (hdr['guide_words'][1] + ' ' + txt).strip()
        else:
            centred.append((min(w[2] for w in g), txt))
    centred.sort()
    if centred:
        hdr['page_number'] = centred[0][1]
        hdr['running_title'] = ' '.join(t for _, t in centred[1:])
    pn = re.sub(r'\D', '', hdr['page_number'])
    if sec in ('main', 'supplement') and pn and printed and len(pn) == len(printed) and \
            sum(a != b for a, b in zip(pn, printed)) > 1:          # single-digit confusions (3/8, 5/8) are common
        warnings.append(f'page number reads {hdr["page_number"]!r}, manifest says {printed}')

    return dict(idx=leaf, printed_page=printed, section=sec, size=[W, H], dpi=600, source='abbyy', rule=rule,
                header=hdr, footer=' / '.join(text_of(ln['chars']).strip()
                                              for ln in sorted(footer, key=lambda ln: ln['box'][0])),
                headings=headings, figures=figures, columns=columns, noise=noise, entries_hint=hints,
                warnings=warnings)


# ---------------------------------------------------------------- output

def jd(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))


def dump(page):
    """One JSON object; one text line per OCR line / hint, so that diffs stay readable."""
    out = ['{']
    for k in ('idx', 'printed_page', 'section', 'size', 'dpi', 'source', 'rule', 'header', 'footer', 'headings',
              'figures', 'noise'):
        out.append(f' "{k}": {jd(page[k])},')
    out.append(' "columns": [')
    for ci, col in enumerate(page['columns']):
        head = ', '.join(f'"{k}": {jd(v)}' for k, v in col.items() if k != 'paragraphs')
        out.append(f'  {{{head}, "paragraphs": [')
        for pi, par in enumerate(col['paragraphs']):
            head = ', '.join(f'"{k}": {jd(v)}' for k, v in par.items() if k != 'lines')
            out.append(f'   {{{head}, "lines": [')
            n = len(par['lines'])
            out.extend('    ' + jd(ln) + (',' if li < n - 1 else '') for li, ln in enumerate(par['lines']))
            out.append('   ]}' + (',' if pi < len(col['paragraphs']) - 1 else ''))
        out.append('  ]}' + (',' if ci < len(page['columns']) - 1 else ''))
    out.append(' ],')
    for k in ('entries_hint', 'orphan_hints'):
        if k in page:
            out.append(f' "{k}": [')
            out.extend('  ' + jd(h) + (',' if i < len(page[k]) - 1 else '') for i, h in enumerate(page[k]))
            out.append(' ],')
    out.append(f' "warnings": {jd(page["warnings"])}')
    out.append('}')
    return '\n'.join(out) + '\n'


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua else 0


def carry_over(page, path):
    """Keep headwords already filled in (Phase 3b) when the page is regenerated."""
    if not path.exists():
        return
    old = json.loads(path.read_text(encoding='utf-8'))
    filled = [h for h in old.get('entries_hint', []) + old.get('orphan_hints', []) if h.get('headword')]
    orphans = []
    for h in filled:
        best = max(page['entries_hint'], key=lambda n: iou(n['bbox'], h['bbox']), default=None)
        if best is not None and iou(best['bbox'], h['bbox']) > 0.3 and not best['headword']:
            for k in ('headword', 'headword_source', 'conf'):
                best[k] = h[k]
        else:
            orphans.append(h)
    if orphans:
        page['orphan_hints'] = orphans
        page['warnings'].append(f'{len(orphans)} filled headword(s) no longer match a paragraph: see orphan_hints')


def read_manifest():
    rows = list(csv.reader(MANIFEST.open(encoding='utf-8'), delimiter='\t'))
    return rows[0], rows[1:]


def convert(item):
    leaf, xml, printed = item
    page = layout(leaf, parse_page(xml), printed)
    path = OCR / f'{leaf:04d}.json'
    carry_over(page, path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(dump(page), encoding='utf-8')
    tmp.rename(path)
    return leaf


def parse_ranges(s):
    out = set()
    for part in s.split(','):
        a, _, b = part.partition('-')
        out.update(range(int(a), int(b or a) + 1))
    return out


def run(wanted, workers=None):
    OCR.mkdir(parents=True, exist_ok=True)
    _, rows = read_manifest()
    printed = {int(r[0]): r[1] for r in rows}
    items = ((leaf, xml, printed.get(leaf, '')) for leaf, xml in page_chunks(wanted))
    n = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        batch = []
        for it in items:                      # bounded batches: the whole XML is ~940 MB
            batch.append(it)
            if len(batch) == 64:
                n += len(list(ex.map(convert, batch)))
                batch = []
        n += len(list(ex.map(convert, batch)))
    print(f'{n} pages written to {OCR.relative_to(ROOT)}/')


# ---------------------------------------------------------------- report and manifest

def load(leaf):
    p = OCR / f'{leaf:04d}.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def letter_headings(page):
    """Headings that look like a single letter initial (a picture, or big type with at most three characters)."""
    return [h for h in page['headings'] if h['kind'] in ('picture', 'gap') or len(re.sub(r'\W', '', h['text'])) <= 3]


def report():
    cols = ['idx', 'printed_page', 'section', 'columns', 'lines', 'paragraphs', 'hints', 'hints_eq', 'eq_signs',
            'headings', 'noise', 'warnings']
    rows, tot = [], dict(lines=0, hints=0, hints_eq=0, eq=0, warn=0)
    for p in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(p.read_text(encoding='utf-8'))
        lines = [ln for c in pg['columns'] for par in c['paragraphs'] for ln in par['lines']]
        paras = sum(len(c['paragraphs']) for c in pg['columns'])
        eq = sum(ln['text'].count('=') for ln in lines)
        heq = sum(1 for h in pg['entries_hint'] if h['eq'])
        rows.append([pg['idx'], pg['printed_page'], pg['section'], len(pg['columns']), len(lines), paras,
                     len(pg['entries_hint']), heq, eq, len(pg['headings']), len(pg['noise']),
                     '; '.join(pg['warnings'])])
        if pg['section'] in ('main', 'supplement'):
            tot['lines'] += len(lines)
            tot['hints'] += len(pg['entries_hint'])
            tot['hints_eq'] += heq
            tot['eq'] += eq
            tot['warn'] += bool(pg['warnings'])
    tmp = OCR / 'report.tmp'
    tmp.write_text('\t'.join(cols) + '\n' + ''.join('\t'.join(map(str, r)) + '\n' for r in rows), encoding='utf-8')
    tmp.rename(OCR / 'report.tsv')
    print(f'{len(rows)} pages; main+supplement: {tot["lines"]} lines, {tot["hints"]} entry candidates '
          f'({tot["hints_eq"]} with "=" in their first two lines), {tot["eq"]} "=" signs in all; '
          f'{tot["warn"]} pages with warnings (see ocr/report.tsv)')


def letters_on(printed):
    try:
        p = int(printed)
    except ValueError:
        return [], []
    table = MAIN_LETTERS if p <= 863 else SUPP_LETTERS
    return [L for L, a, b in table if a <= p <= b], [L for L, a, b in table if a == p]


def manifest():
    head, rows = read_manifest()
    problems = []
    for r in rows:
        leaf = int(r[0])
        r[2] = section_of(leaf)
        on, starts = letters_on(r[1]) if r[2] in ('main', 'supplement') else ([], [])
        r[3] = ','.join(on)
        pg = load(leaf)
        if pg is None or r[2] not in ('main', 'supplement'):
            continue
        found = letter_headings(pg)
        if len(found) != len(starts):
            problems.append(f'leaf {leaf} (p. {r[1]}): TOC starts {starts or "no letter"}, '
                            f'found {len(found)} letter heading(s) ' +
                            ', '.join(f'{h["kind"]} {h["text"]!r} at y={h["bbox"][1]}' for h in found))
    tmp = MANIFEST.with_suffix('.tmp')
    tmp.write_text('\t'.join(head) + '\n' + ''.join('\t'.join(r) + '\n' for r in rows), encoding='utf-8')
    tmp.rename(MANIFEST)
    print(f'manifest: section and letter columns written; {len(problems)} pages where the letter headings found '
          f'do not match the table of contents:')
    for p in problems:
        print('  ' + p)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--pages', help='leaf ranges, e.g. 38-60,150')
    ap.add_argument('--manifest', action='store_true')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--workers', type=int)
    a = ap.parse_args()
    if not (a.manifest or a.report) or a.pages:
        run(parse_ranges(a.pages) if a.pages else None, a.workers)
        report()
    if a.report and not a.pages:
        report()
    if a.manifest:
        manifest()


if __name__ == '__main__':
    main()
