#!/usr/bin/env python3
"""Crops for transcribing Дьяченко's errata table (front matter, leaves 32-36) into djachenko/errata.tsv.

    python3 tools/dj_errata_bands.py 32 10          # full-width bands of 10 table rows (locators + corrections)
    python3 tools/dj_errata_bands.py 32 6 --right   # the Напечатано | Слѣдуетъ читать block alone, 6 rows
    python3 tools/dj_errata_bands.py 32 1 --right --width 2200   # one row, for a diacritic

The table is Стран. | Строка. | Столб. | Напечатано: | Слѣдуетъ читать:, and ABBYY reads it as a jumble (and
garbles the Greek), so it is transcribed by eye from these crops. Many corrections are a single accent or
breathing, so read the doubtful ones at the highest zoom. Images are written to the scratch directory given by
--out (default: the current directory).
"""

import sys, json
sys.path.insert(0, 'tools')
import dj_inspect as I
from PIL import Image
args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = [a for a in sys.argv[1:] if a.startswith('--')]
leaf, per = int(args[0]), int(args[1])
RIGHT = '--right' in opts
WIDTH = next((int(o.split('=')[1]) for o in opts if o.startswith('--width=')), 1500)
OUT = next((o.split('=')[1] for o in opts if o.startswith('--out=')), '.')
pg = json.load(open(f'djachenko/ocr/{leaf:04d}.json'))
rows = sorted((ln['bbox'] for c in pg['columns'] for p in c['paragraphs'] for ln in p['lines']), key=lambda b: b[1])
# group line boxes into table rows by vertical overlap
bands, cur = [], []
for b in rows:
    if cur and b[1] > cur[-1][3] - 8:
        bands.append(cur); cur = []
    cur.append(b)
if cur: bands.append(cur)
im = I.jp2(leaf)
x0 = min(b[0] for b in rows) - 20; x1 = max(b[2] for b in rows) + 20
out = []
for k in range(0, len(bands), per):
    chunk = bands[k:k + per]
    y0 = min(b[1] for band in chunk for b in band) - 12
    y1 = max(b[3] for band in chunk for b in band) + 12
    c = im.crop((max(0, x0), max(0, y0), x1, y1))
    z = 1500 / c.width
    c = c.resize((1500, max(1, round(c.height * z))), Image.LANCZOS)
    p = f'/private/tmp/claude-501/-Users-rene-dev-akafist/ec9e53d2-c5d6-4593-868c-cf36aa7fca2e/scratchpad/e{leaf}_{k:03d}.png'
    c.save(p); out.append((k, len(chunk), p, c.size))
print(f'{len(bands)} table rows → {len(out)} bands')
for k, n, p, s in out: print(f'  rows {k+1}-{k+n}: {p.split("/")[-1]} {s}')
