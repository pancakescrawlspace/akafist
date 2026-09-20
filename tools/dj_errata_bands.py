#!/usr/bin/env python3
"""Crops for transcribing Дьяченко's errata table (front matter, leaves 32–36) into djachenko/errata.tsv.

    python3 tools/dj_errata_bands.py 33 --bands 10        # full width, 10 table rows at a time: the locators
    python3 tools/dj_errata_bands.py 33 --rows 13 14 16   # those rows alone, full width, at 2000 px
    python3 tools/dj_errata_bands.py 33 --right 6         # the Напечатано | Слѣдуетъ читать half, 6 rows

The table is Стран. | Строка. | Столб. | Напечатано: | Слѣдуетъ читать:. ABBYY reads the five columns as a jumble
("5 лѣвый", "20 сверху" on separate lines) and garbles the Greek entirely, so the table is transcribed by eye.

Read the full-width bands first: they give the locator columns and pair each correction with its row. Then read
any row whose correction is not obvious at that size with `--rows`, because a large part of this table is single
marks — ἀγνός → ἁγνός, χώριον → χωρίον, ὄροψος → ὄροφος, ἠγεμών → ἡγεμών — which simply cannot be seen in a band.
In this face ѧ is the triangular shape and ѫ the ж-like one (p. 7: съмѣреномѧдрье → съмѣреномѫдрье).

Rows are numbered as in errata.tsv: the header is row 0, the first correction row 1. Images go to --out
(default: the current directory).
"""
import argparse, json, sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dj_inspect as I  # noqa: E402


def row_bands(leaf):
    """The table rows of an errata page: [[line box, …]], top to bottom, header first."""
    pg = json.loads((Path('djachenko/ocr') / f'{leaf:04d}.json').read_text(encoding='utf-8'))
    boxes = sorted((ln['bbox'] for c in pg['columns'] for p in c['paragraphs'] for ln in p['lines']),
                   key=lambda b: b[1])
    bands, cur = [], []
    for b in boxes:
        if cur and b[1] > cur[-1][3] - 8:        # a new row starts where the previous one has ended
            bands.append(cur)
            cur = []
        cur.append(b)
    if cur:
        bands.append(cur)
    return bands


def save(crops, path):
    W = max(c.width for c in crops)
    out = Image.new('L', (W, sum(c.height + 8 for c in crops)), 255)
    y = 0
    for c in crops:
        out.paste(c, (0, y))
        y += c.height + 8
    out.save(path)
    print(path, out.size)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('leaf', type=int)
    ap.add_argument('--bands', type=int, metavar='ROWS', help='full-width bands of ROWS table rows')
    ap.add_argument('--rows', type=int, nargs='+', metavar='ROW', help='these rows alone, full width')
    ap.add_argument('--right', type=int, metavar='ROWS', help='the correction half only, ROWS rows at a time')
    ap.add_argument('--width', type=int, default=0, help='pixel width of the output (default: by mode)')
    ap.add_argument('--out', default='.', help='directory for the images')
    a = ap.parse_args()
    bands = row_bands(a.leaf)
    im = I.jp2(a.leaf)
    flat = [b for band in bands for b in band]
    x0, x1 = min(b[0] for b in flat) - 15, max(b[2] for b in flat) + 15
    if a.right:                                   # the right half starts at the middle of the text block
        x0 = (x0 + x1) // 2 - 40
    out = Path(a.out)

    def crop(band, width):
        y0 = min(b[1] for b in band) - 10
        y1 = max(b[3] for b in band) + 10
        c = im.crop((max(0, x0), y0, x1, y1))
        z = width / c.width
        return c.resize((width, max(1, round(c.height * z))), Image.LANCZOS)

    if a.rows:
        save([crop(bands[r], a.width or 2000) for r in a.rows if r < len(bands)],
             out / f'e{a.leaf}_rows.png')
    elif a.bands or a.right:
        per = a.bands or a.right
        width = a.width or (1500 if a.bands else 1600)
        print(f'{len(bands)} table rows (row 0 is the header)')
        for k in range(0, len(bands), per):
            chunk = [b for band in bands[k:k + per] for b in band]
            save([crop(chunk, width)], out / f'e{a.leaf}_{k:03d}.png')
    else:
        ap.error('give --bands, --rows or --right')


if __name__ == '__main__':
    main()
