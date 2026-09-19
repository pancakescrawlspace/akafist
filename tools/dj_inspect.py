#!/usr/bin/env python3
"""Helpers for looking at pages of the Дьяченко scans while checking OCR output and ground truth.

    python3 tools/dj_inspect.py dump 150                 # text of ocr/0150.json by column/paragraph, entry hints
    python3 tools/dj_inspect.py overlay 150,902          # page image(s) with columns, paragraphs, hints, headings
    python3 tools/dj_inspect.py lines 660 2 19 36        # crop lines 19-36 of column 2 (600 ppi) + ABBYY's text
    python3 tools/dj_inspect.py find 45 Азкъ Азвѣди      # crop the words in every witness (A, B, C, D) side by side
    python3 tools/dj_inspect.py find 45 барсукъ --in D --zoom 2 --lines 1
    python3 tools/dj_inspect.py gtcheck                  # sanity checks of djachenko/eval/gt/*.txt
    python3 tools/dj_inspect.py segcheck                 # likely false / missed entry starts in ocr/*.json

Images are written to djachenko/inspect/ (git-ignored); the path is printed. LEAF is always the leaf number of scan
A (printed page = leaf − 37). Witnesses: A = scan A (600 ppi JP2), B = 1993 reprint (DjVu), C = Indiana PDFs,
D = Cornell PDF (see djachenko/COPIES.md). `find` locates words through each witness's own text layer (ABBYY for A,
the DjVu text for B, Google's for C and D), so it finds what that OCR read; give several spellings if needed.
"""
import argparse, glob, html, json, re, statistics, subprocess, sys, unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DJ = ROOT / 'djachenko'
OCR, PAGES, OUT = DJ / 'ocr', DJ / 'pages', DJ / 'inspect'
GT_DIR = DJ / 'eval' / 'gt'
REPRINT = DJ / 'scan' / 'reprint1993' / 'Dyachenko G., Polnyj cerkovnoslavyanskij slovar (M., 1993, 1159p).djvu'
CORNELL = DJ / 'scan' / 'google' / 'google_cornell.pdf'
INDIANA = (DJ / 'scan' / 'google' / 'google_indiana_v1.pdf', DJ / 'scan' / 'google' / 'google_indiana_v2.pdf')
OFFSET = 37


def load(leaf):
    return json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))


def jp2(leaf):
    return Image.open(glob.glob(str(PAGES / 'jp2' / f'*_{leaf:04d}.jp2'))[0]).convert('L')


def save(im, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    im.save(path, quality=90)
    print(path.relative_to(ROOT), im.size)
    return path


# ---------------------------------------------------------------- dump / overlay / lines

def cmd_dump(a):
    pg = load(a.leaf)
    print('header', pg['header'], '| footer', pg['footer'], '| rule', pg['rule'])
    for h in pg['headings']:
        print('HEADING', h)
    for c in pg['columns']:
        print(f"== col {c['n']} side {c['side']} band {c['band']} flush {c['flush']} indent {c['indent']} "
              f"bbox {c['bbox']}")
        for i, p in enumerate(c['paragraphs'], 1):
            for j, ln in enumerate(p['lines']):
                mark = (('G' if p.get('guessed') else 'H') if p['hanging'] else 'C') if j == 0 else ' '
                print(f"{i:3}{mark} {ln['ind']} {ln['bbox'][0]:5} {ln['text']}")
    for h in pg['entries_hint']:
        print('HINT', h['col'], h['para'], repr(h['abbyy']), h['abbyy_conf'], 'eq' if h['eq'] else '')
    print('noise', [n['text'] for n in pg['noise']])
    print('warnings', pg['warnings'])


def overlay_one(leaf):
    pg = load(leaf)
    im = Image.open(PAGES / f'{leaf:04d}.jpg').convert('RGB')
    d = ImageDraw.Draw(im)

    def f(b):
        return [v / 2 for v in b]                     # 600 ppi coordinates -> 300 ppi working image
    for c in pg['columns']:
        d.rectangle(f(c['bbox']), outline=(0, 0, 255), width=2)
        d.text((c['bbox'][0] / 2 + 5, c['bbox'][1] / 2 - 12), f"col{c['n']}", fill=(0, 0, 255))
        for p in c['paragraphs']:
            colour = (230, 120, 0) if p.get('guessed') else (0, 170, 0) if p['hanging'] else (0, 120, 255)
            d.rectangle(f(p['bbox']), outline=colour, width=3 if p['hanging'] else 1)
    for h in pg['entries_hint']:
        d.rectangle(f(h['bbox']), outline=(255, 140, 0), width=2)
    for h in pg['headings']:
        d.rectangle(f(h['bbox']), outline=(255, 0, 0), width=4)
    for n in pg['noise']:
        d.rectangle(f(n['bbox']), outline=(255, 0, 255), width=3)
    if pg['rule']:
        g0, g1 = pg['rule']
        d.line([(g0 / 2, 0), ((g0 + g1 * 6520) / 2, 3260)], fill=(255, 0, 0), width=1)
    return im.resize((im.width // 2, im.height // 2))


def cmd_overlay(a):
    leaves = [int(x) for x in a.leaves.split(',')]
    ims = [overlay_one(l) for l in leaves]
    out = Image.new('RGB', (sum(i.width for i in ims) + 10 * len(ims), max(i.height for i in ims)), 'white')
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + 10
    save(out, f'overlay_{"_".join(map(str, leaves))}.jpg')


def cmd_lines(a):
    pg = load(a.leaf)
    c = [c for c in pg['columns'] if c['n'] == a.col][0]
    lines = [(pi, ln) for pi, p in enumerate(c['paragraphs'], 1) for ln in p['lines']]
    sel = lines[a.first - 1:a.last]
    x0 = min(c['bbox'][0], min(ln['bbox'][0] for _, ln in sel)) - 40
    x1 = max(c['bbox'][2], max(ln['bbox'][2] for _, ln in sel)) + 30
    y0, y1 = sel[0][1]['bbox'][1] - 25, sel[-1][1]['bbox'][3] + 20
    im = jp2(a.leaf).crop((max(0, x0), max(0, y0), x1, y1))
    if a.scale != 1:
        im = im.resize((round(im.width * a.scale), round(im.height * a.scale)), Image.LANCZOS)
    save(im, f'lines_{a.leaf}_{a.col}_{a.first}.jpg')
    for i, (pi, ln) in enumerate(sel, a.first):
        print(f'{i:3} p{pi:<3} {"H" if ln["ind"] == 0 else " "} {ln["text"]}')


# ---------------------------------------------------------------- find a word in all witnesses

def words_A(leaf):
    pg = load(leaf)
    out = []
    for c in pg['columns']:
        for p in c['paragraphs']:
            for ln in p['lines']:
                for w in ln['words']:
                    out.append((w[0], w[1], w[2], w[3], w[4]))
    return out, jp2(leaf), 1.0


def pdf_page_words(pdf, page, dpi=600):
    out = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-bbox', str(pdf), '-'],
                         capture_output=True, text=True, check=True).stdout
    k = dpi / 72
    words = [(html.unescape(t), float(x0) * k, float(y0) * k, float(x1) * k, float(y1) * k) for x0, y0, x1, y1, t in
             re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', out)]
    tmp = OUT / f'.pdfpage_{Path(pdf).stem}_{page}'
    OUT.mkdir(parents=True, exist_ok=True)
    if not tmp.with_suffix('.pgm').exists():
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', str(dpi), '-gray', '-singlefile', str(pdf),
                        str(tmp)], check=True)
    return words, Image.open(tmp.with_suffix('.pgm')), 1.0


def words_D(leaf):
    return pdf_page_words(CORNELL, leaf - OFFSET + 48)


def words_C(leaf):
    p = leaf - OFFSET
    return pdf_page_words(*((INDIANA[0], p + 46) if p <= 572 else (INDIANA[1], p - 558)))


def words_B(leaf):
    p = leaf - OFFSET
    out = subprocess.run(['djvused', '-u', str(REPRINT), '-e', f'select {p}; print-txt'],
                         capture_output=True, text=True, check=True).stdout
    m = re.match(r'\(page (\d+) (\d+) (\d+) (\d+)', out)
    H = int(m.group(4)) + int(m.group(2))
    words = [(re.sub(r'\\(.)', lambda e: ' ' if e.group(1) == 'n' else e.group(1), t).strip(),
              int(x0), H - int(y1), int(x1), H - int(y0))
             for x0, y0, x1, y1, t in re.findall(r'\(word (\d+) (\d+) (\d+) (\d+) "((?:[^"\\]|\\.)*)"\)', out)]
    tif = OUT / f'.djvu_{p}.tif'
    OUT.mkdir(parents=True, exist_ok=True)
    if not tif.exists():
        subprocess.run(['ddjvu', '-format=tiff', f'-page={p}', str(REPRINT), str(tif)], check=True)
    return words, Image.open(tif).convert('L'), 2.0          # ~237 ppi: show it at double size


WITNESS = {'A': words_A, 'B': words_B, 'C': words_C, 'D': words_D}


def label_font(size=22):
    for f in ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', '/Library/Fonts/Arial Unicode.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def line_box(words, w, extra):
    """Bounding box of the printed line (within its column) that holds word w, plus `extra` lines above/below."""
    h = max(20, w[4] - w[2])
    cy = (w[2] + w[4]) / 2
    row = sorted((v for v in words if abs((v[2] + v[4]) / 2 - cy) < 0.6 * h), key=lambda v: v[1])
    k = row.index(w)
    lo = hi = k
    while lo > 0 and row[lo][1] - row[lo - 1][3] < 2.5 * h:
        lo -= 1
    while hi < len(row) - 1 and row[hi + 1][1] - row[hi][3] < 2.5 * h:
        hi += 1
    x0, x1 = row[lo][1], row[hi][3]
    return (max(0, int(x0 - 0.5 * h)), max(0, int(min(v[2] for v in row[lo:hi + 1]) - (0.6 + 1.2 * extra) * h)),
            int(x1 + 0.5 * h), int(max(v[4] for v in row[lo:hi + 1]) + (0.4 + 1.2 * extra) * h))


def fold(s):
    s = unicodedata.normalize('NFD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


def cmd_find(a):
    tiles = []
    for wit in a.within:
        try:
            words, im, scale = WITNESS[wit](a.leaf)
        except Exception as e:                          # a witness may be missing on disk
            print(f'{wit}: {e}')
            continue
        hits = [w for w in words if any(fold(t) in fold(w[0]) for t in a.text)]
        if not hits:
            print(f'{wit}: not found in its text layer ({", ".join(a.text)})')
            continue
        for w in hits[:a.max]:
            t = im.crop(line_box(words, w, a.lines))
            z = a.zoom * scale
            t = t.resize((max(1, round(t.width * z)), max(1, round(t.height * z))), Image.LANCZOS)
            lab = Image.new('L', (max(t.width, 400), 30), 255)
            ImageDraw.Draw(lab).text((4, 3), f'{wit}: {w[0]}', fill=0, font=label_font())
            tile = Image.new('L', (max(t.width, 400), t.height + 30), 255)
            tile.paste(lab, (0, 0))
            tile.paste(t, (0, 30))
            tiles.append(tile)
            print(f'{wit}: {w[0]!r} at {[round(v) for v in w[1:]]}')
    if tiles:
        W = max(t.width for t in tiles)
        out = Image.new('L', (W, sum(t.height for t in tiles) + 10 * len(tiles)), 255)
        y = 0
        for t in tiles:
            out.paste(t, (0, y))
            y += t.height + 10
        save(out, f'find_{a.leaf}_{fold(a.text[0])[:20]}.png')


# ---------------------------------------------------------------- checks

def cmd_gtcheck(a):
    files = a.files or sorted(str(p) for p in GT_DIR.glob('*.txt'))
    for f in files:
        raw = open(f, encoding='utf-8').read()
        if unicodedata.normalize('NFC', raw) != raw:
            print(f, 'not NFC')
        body = ''.join(l if not l.startswith(('#', '@')) else '\n' for l in raw.splitlines(True))
        for m in re.finditer(r'[^\s\d.,;:()\[\]{}=+—–\-‹›„“"!?/§№*…\']+', body):
            w = m.group(0)
            scripts = {('LAT' if 'LATIN' in n else 'CYR' if 'CYRILLIC' in n else 'GRK' if 'GREEK' in n else 'OTHER:' + n)
                       for n in (unicodedata.name(ch, '?') for ch in w)}
            if len(scripts) > 1 or any(s.startswith('OTHER') for s in scripts):
                print(f'{f}:{body.count(chr(10), 0, m.start()) + 1}: mixed {sorted(scripts)} {w!r}')
        for k, line in enumerate(raw.splitlines(), 1):
            if line.startswith(('#', '@')) or not line.strip():
                continue
            if line.count('{') != line.count('}') or line.count('‹') != line.count('›'):
                print(f'{f}:{k}: unbalanced markup')
            # parentheses: a ")" at depth 0 after "1", "12" or "а" is a sense number, anything else is stray
            depth, stray = 0, 0
            for m in re.finditer(r'[()]', line):
                if m.group() == '(':
                    depth += 1
                elif depth:
                    depth -= 1
                elif not re.search(r'(?:^|[\s=—;:,.])(?:\d{1,2}|[а-я])$', line[:m.start()]):
                    stray += 1
            if stray or (depth and not line.rstrip().endswith('-')):
                print(f'{f}:{k}: parentheses: {depth} left open, {stray} stray ")" (sense numbers "1)" not counted)')
        print(f, 'Latin words:', sorted(set(re.findall(r'\b[A-Za-zäöüÄÖÜ]+\b', body))))


def cmd_segcheck(a):
    """Entry starts that look wrong: a start after a hyphenated line end without '=' or a dash (likely false), and an
    indented line with '=' early after a short sentence-final line (likely missed)."""
    for f in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] not in ('main', 'supplement'):
            continue
        for c in pg['columns']:
            lines = [(ln, p['hanging'] and j == 0) for p in c['paragraphs'] for j, ln in enumerate(p['lines'])]
            if len(lines) < 4:
                continue
            R = statistics.median(sorted(ln['bbox'][2] for ln, _ in lines)[len(lines) // 3:])
            for i, (ln, start) in enumerate(lines[1:], 1):
                prev, t = lines[i - 1][0], ln['text']
                e = t.find('=')
                if not start and ln['ind'] == 1 and 0 <= e < len(t) * 0.4 and prev['bbox'][2] < R - 120:
                    print(f'{pg["idx"]} missed? | {prev["text"][-20:]} | {t[:50]}')
                if start and '=' not in t and not re.search(r'\s[—-]\s', t) and prev['text'].endswith(('¬', '-')):
                    print(f'{pg["idx"]} false? | {prev["text"][-20:]} | {t[:50]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('dump')
    s.add_argument('leaf', type=int)
    s = sub.add_parser('overlay')
    s.add_argument('leaves')
    s = sub.add_parser('lines')
    for k in ('leaf', 'col', 'first', 'last'):
        s.add_argument(k, type=int)
    s.add_argument('--scale', type=float, default=0.85)
    s = sub.add_parser('find')
    s.add_argument('leaf', type=int)
    s.add_argument('text', nargs='+')
    s.add_argument('--in', dest='within', default='ADBC', help='witnesses to search, e.g. AD (default ADBC)')
    s.add_argument('--zoom', type=float, default=1.0)
    s.add_argument('--lines', type=int, default=0, help='extra lines of context above and below')
    s.add_argument('--max', type=int, default=2, help='hits per witness')
    s = sub.add_parser('gtcheck')
    s.add_argument('files', nargs='*')
    sub.add_parser('segcheck')
    a = ap.parse_args()
    {'dump': cmd_dump, 'overlay': cmd_overlay, 'lines': cmd_lines, 'find': cmd_find, 'gtcheck': cmd_gtcheck,
     'segcheck': cmd_segcheck}[a.cmd](a)


if __name__ == '__main__':
    main()
