#!/usr/bin/env python3
"""Consolidation for Phase 3b: the headword of every entry, located and cropped in all four witnesses.

    python3 tools/dj_crops.py index                    # djachenko/headwords.tsv — the boxes (fast, no images)
    python3 tools/dj_crops.py crops [--pages 45,341]   # djachenko/crops/<W>/NNNN.png — one strip per page
    python3 tools/dj_crops.py crops --witness AD --ppi 300 --workers 8
    python3 tools/dj_crops.py report                   # what exists, and what it costs on disk

Why strips and not one file per headword: git handles a few thousand files far better than a hundred thousand
(24,841 headwords × 4 witnesses). Size is not the reason — measured (session 6), one 1-bit PNG per headword holds
the same 3 % either way, though it occupies 2.7× on disk (a ~1.4 KB file in a 4 KB block: ~400 MB for the book);
an earlier estimate here of "about a gigabyte" was for greyscale JPEG. crops/ is now git-ignored, so either would
do. Each page and witness therefore gets ONE image, the page's headwords stacked in entry order, and
`headwords.tsv` says which rows of that strip belong to which entry (`y0s`, `y1s`). Slicing one headword out is
then a crop of the strip, with no need for the scans:

    im = Image.open('djachenko/crops/A/0341.png').crop((0, y0s, width, y1s))

Where the boxes come from:
    A  the Church Slavonic type run that ABBYY marks at the start of the entry (`entries_hint[].bbox`), which is
       the headword itself — the same box Phase 3b step 2 crops from — with its left edge pulled out to the
       column's flush edge, since ABBYY's box begins at the first character it managed to read and the headword
       begins at the flush edge (it matters on the entries only witnesses C and D could see: PLAN.md Rev. 7).
    D  the entry's first line in D (`paragraphs[].d_line`, written by dj_heads step 1), cut as far along the
       line as the entry's head in entries.tsv is long (head_box: the line's words counted at the norm level,
       and cut inside the word where the head ends there — "альбо—польск." — so run dj_parse.py first).
    B, C  the same, after aligning that witness's column text to A's (dj_witness.align, as in dj_heads.merge):
       A's paragraph start maps to a position in the witness's text, which gives the line, and the line gives
       the words.
    C and D's boxes are then made full height (`full_height`): Google's word boxes span the lowercase letters
    only, so a crop cut to them loses the top of every capital and accent. And B's, C's and D's are pulled out
    to the start of the nearest flush line, since their OCR drops a big initial capital from the word box as
    ABBYY does (B p. 7: `Адонъ` boxed from 32 px inside the column edge).
    Session 6 (2026-09-21): before these two changes B's, C's and D's boxes cut at their own separators or
    after four words and ran into the definition — median widths 577/593/600 px against A's 454, a quarter of
    C's and D's more than twice the median — and C's and D's lost the top of the letters. Now all four have
    median width 380–470 px and ~6 % over twice it. B's boxes were besides flipped about the wrong page
    height (dj_witness.djvu_words, fixed there), which put its crops as much as 710 px too high.
Coordinates are in each witness's own pixel space at `ppi` (A: the 600 ppi JP2; B: the DjVu page as ddjvu renders
it; C and D: the Google PDFs rendered at 600 ppi), so a box can be used against the sources directly.

Columns of headwords.tsv (tab-separated, one row per entry and witness; entries in the order of entries.tsv):
    id        the entry id of entries.tsv (leaf-column-paragraph), e.g. 0341-1-02
    witness   A | B | C | D
    page      the page inside that witness's source: leaf (A), DjVu page (B), "v1:350"/"v2:…" (C), PDF page (D)
    x0 y0 x1 y1   the headword box in that witness, at `ppi`
    ppi       the resolution the box is expressed in
    strip     the page strip this headword is in (empty until `crops` has run for that page and witness)
    y0s y1s   the rows of this headword inside the strip
    how       abbyy (A), dline (D), aligned (B, C), none (not found — box and strip empty)
"""
import argparse, csv, json, subprocess, sys
from multiprocessing import Pool
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import (CORNELL, DJ, OCR, PDF_DPI, REPRINT, align, b_page, c_page, d_page,  # noqa: E402
                        indent_levels, norm_seq, page_text, side_texts)

CROPS = DJ / 'crops'
INDEX = DJ / 'headwords.tsv'
PAGES = DJ / 'pages'
COLUMNS = ['id', 'witness', 'page', 'x0', 'y0', 'x1', 'y1', 'ppi', 'strip', 'y0s', 'y1s', 'how']
PAD = 15                      # px of white kept round a box, in the witness's own pixels (A, C, D: 600 ppi)
PAD_Y = {'B': 3}              # except above and below B's: its DjVu word boxes already span 95 % of its line
#                               pitch (41 px of 43, the page at ~250 ppi), so 15 px more took in two-thirds of
#                               the lines either side — the noise the user saw in crops/B (session 6). The
#                               horizontal pad stays: it keeps the last letter where the head's cut lands tight.
THRESHOLD = 165               # grey level below which a pixel is ink (see strip_page)
SEPS = '=—–'                  # what ends the headword on the line ("Метехати = …", "Метненїе—…")


def pages_of(a=None):
    leaves = []
    for f in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] in ('main', 'supplement'):
            leaves.append(pg['idx'])
    if a and a.pages:
        want = set()
        for part in a.pages.split(','):
            if '-' in part:
                lo, hi = part.split('-')
                want.update(range(int(lo), int(hi) + 1))
            else:
                want.add(int(part))
        leaves = [l for l in leaves if l in want]
    return leaves


# ---------------------------------------------------------------- locating the headwords

def a_sides(pg):
    """A's text per column side, with the start offset of every hanging paragraph: {side: (text, [(pos, hint)])}."""
    out = {}
    for col in pg['columns']:
        text, starts = out.get(col['side'], ('', []))
        for pi, p in enumerate(col['paragraphs'], 1):
            if text:
                text += ' '
            starts.append((len(text), (col['n'], pi)))
            text += ' '.join(ln['text'].replace('¬', '') for ln in p['lines'])
        out[col['side']] = (text, starts)
    return out


def line_of(side, pos):
    """The line of a witness side (side_texts result) that holds character `pos`."""
    for ln in side['lines']:
        if ln['start'] <= pos <= ln['end']:
            return ln
    return None


def words_in(words, box):
    """The witness's words whose centre lies in `box`, both in that witness's own units, left to right."""
    x0, y0, x1, y1 = box
    sel = [w for w in words if y0 - 1 <= (w['box'][1] + w['box'][3]) / 2 <= y1 + 1
           and x0 - 1 <= (w['box'][0] + w['box'][2]) / 2 <= x1 + 1]
    return sorted(sel, key=lambda w: w['box'][0])


HEADS = None


def heads():
    """{entry id: head text} from entries.tsv — the head as dj_parse.py cut it (run that first)."""
    global HEADS
    if HEADS is None:
        HEADS = {}
        path = DJ / 'entries.tsv'
        if path.exists():
            with path.open(encoding='utf-8') as f:
                for r in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
                    HEADS[r['id']] = r['headword']
    return HEADS


def head_box(words, text, head=''):
    """Box round the headword part of a line.

    With the entry's head (from entries.tsv): as far along the line as the head is long. The line's words are
    walked in reading order, counting their characters at the norm level (so that one OCR's spacing or look-
    alikes do not matter) until the head's count is reached; where the head ends inside a word — the separator
    glued to it, "альбо—польск.", "Я—первая" — the box is cut inside that word, in proportion. The user's
    proposal (session 6): B's, C's and D's own separators and word counts had taken in the definition, making
    their boxes ~32 % wider than A's, whose box is the headword's own type run.

    Without one, the old rule: up to the separator where the line has one — before the word when the separator
    stands alone ("Метехати = …"), including it when it is glued to the headword ("Метненїе—…") — else the
    first four words."""
    if not words:
        return None
    need = len(norm_seq(head)[0]) if head else 0
    if need:
        have = 0
        for i, w in enumerate(words):
            n = len(norm_seq(text[w['start']:w['end']])[0])
            if n and have + n >= need:
                x0, y0, x1, y1 = w['box']
                frac = (need - have) / n
                sel = words[:i + 1]
                cut = x0 + frac * (x1 - x0) + 0.15 * (x1 - x0) / max(1, n)   # and a sliver: no clipped last letter
                return (min(v['box'][0] for v in sel), min(v['box'][1] for v in sel), min(x1, round(cut)),
                        max(v['box'][3] for v in sel))
            have += n
        # the line is shorter than the head (a head broken over two lines): all of it
        return (min(w['box'][0] for w in words), min(w['box'][1] for w in words),
                max(w['box'][2] for w in words), max(w['box'][3] for w in words))
    upto = None
    for i, w in enumerate(words):
        t = text[w['start']:w['end']]
        if any(c in t for c in SEPS):
            upto = i if t[0] in SEPS else i + 1
            break
    sel = words[:max(1, upto if upto is not None else min(4, len(words)))]
    return (min(w['box'][0] for w in sel), min(w['box'][1] for w in sel),
            max(w['box'][2] for w in sel), max(w['box'][3] for w in sel))


def full_height(box, witness):
    """Google's word boxes (C, D) span the lowercase letters only — 54 px at 600 ppi against A's 94, where the
    box is the whole type run — so a crop cut to them loses the top of every capital, ascender and accent.
    They are extended up by 45 % and down by 15 % of their height, measured on pp. 1, 109 and 480 against the
    images. B's DjVu boxes are full height already (41 px at ~237 ppi, i.e. ~104 at 600)."""
    if witness not in 'CD':
        return box
    x0, y0, x1, y1 = box
    h = y1 - y0
    return (x0, round(y0 - 0.45 * h), x1, round(y1 + 0.15 * h))


def boxes_for(leaf, pg, witness):
    """-> {(col, para): (box at PDF_DPI-equivalent px, how)} for one witness."""
    out = {}
    if witness == 'A':
        # ABBYY's box starts at the first character it read, which on a stained or cut line is not where the
        # headword starts — and on the entries the witnesses added (PLAN Rev. 7, flag `seg`) it is a median
        # 205 px too far right, so the crop would show the middle of the line instead of the lemma. A headword
        # begins at the column's flush edge by definition, so the box is extended there (deskewed on the rule,
        # clamped at the image edge, which is where a cut left margin puts it).
        rule = pg.get('rule')
        edge = {}
        for col in pg['columns']:
            edge[col['n']] = (col['flush'], col['bbox'])
        for h in pg['entries_hint']:
            x0, y0, x1, y1 = h['bbox']
            e = edge.get(h['col'])
            if e:
                gx = (rule[0] + rule[1] * (y0 + y1) / 2) if rule else 0
                x0 = max(0, min(x0, round(gx + e[0])))
            out[(h['col'], h['para'])] = ((x0, y0, x1, y1), 'abbyy')
        return out
    r = page_text(witness, leaf)
    # C and D are read in PDF points, B in DjVu pixels; the index keeps 600 ppi pixels for C and D
    to_px = PDF_DPI / 72 if witness in 'CD' else 1.0
    sides = side_texts(r)
    a = a_sides(pg)
    # The witnesses' OCR drops a big initial capital from the word box as ABBYY does (B p. 7: `Адонъ` boxed from
    # 32 px right of the column edge, the А cut in half), and a headword begins at the column's flush edge by
    # definition — so, as for A, the box is pulled out to it. The edge is the start of the NEAREST flush line
    # (dj_witness.indent_levels, level 0): not one figure per column, since the Google columns are skewed by up
    # to 13 pt top to bottom and B's indent is only ~12 px, so a percentile of the column lands on the wrong
    # level. It only ever moves the box left.
    lv = indent_levels(r)
    flush = {}
    for s, w_side in sides.items():
        flush[s] = sorted((l['y0'], l['x0']) for l in w_side['lines']
                          if lv.get((l['side'], l['y0'])) == 0 and len(l['raw'].strip()) >= 6)

    def at_edge(b, side):
        fl = flush.get(side)
        if not fl:
            return b
        yc = (b[1] + b[3]) / 2
        x = min(fl, key=lambda f: abs(f[0] - yc))[1]
        return (min(b[0], x),) + tuple(b[1:])
    if witness == 'D':                                     # D's line of each paragraph is known from step 1
        for col in pg['columns']:
            for pi, para in enumerate(col['paragraphs'], 1):
                if not para.get('d_line'):
                    continue
                box = tuple(v / to_px for v in para['d_line'])          # px -> points
                b = head_box(words_in(r['words'], box), r['text'],
                             heads().get(f"{leaf:04d}-{col['n']}-{pi:02d}", ''))
                if b:
                    b = at_edge(b, col['side'])
                    out[(col['n'], pi)] = (full_height(tuple(round(v * to_px) for v in b), witness), 'dline')
    for side, (a_text, starts) in a.items():
        if side not in sides:
            continue
        w_side = sides[side]
        a_seq, a_idx = norm_seq(a_text)
        w_seq, w_idx = norm_seq(w_side['text'])
        if not a_seq or not w_seq:
            continue
        _, _, j_at = align(a_seq, w_seq)
        a_at = {a_idx[k]: k for k in range(len(a_seq))}
        for pos, key in starts:
            k = next((a_at[p] for p in range(pos, min(pos + 40, len(a_text))) if p in a_at), None)
            if k is None:
                continue
            j = j_at[k]
            raw = w_idx[j] if j < len(w_idx) else None
            if raw is None:
                continue
            ln = line_of(w_side, raw)
            if not ln:
                continue
            if key in out:                             # D: already taken from d_line
                continue
            b = head_box(words_in(r['words'], (ln['x0'], ln['y0'], ln['x1'], ln['y1'])), r['text'],
                         heads().get(f"{leaf:04d}-{key[0]}-{key[1]:02d}", ''))
            if b is None:
                continue
            b = at_edge(b, side)
            out[key] = (full_height(tuple(round(v * to_px) for v in b), witness), 'aligned')
    return out


def witness_page(leaf, witness):
    if witness == 'A':
        return str(leaf)
    if witness == 'B':
        return str(b_page(leaf))
    if witness == 'D':
        return str(d_page(leaf))
    pdf, p = c_page(leaf)
    return ('v1:' if pdf.name.endswith('v1.pdf') else 'v2:') + str(p)


def index_page(leaf):
    """-> [row dicts] for one page, one row per entry candidate and witness."""
    pg = json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))
    rows, found = [], {}
    for witness in 'ABCD':
        try:
            found[witness] = boxes_for(leaf, pg, witness)
        except Exception as e:                            # noqa: BLE001 — a missing witness must not stop the run
            found[witness] = {}
            print(f'leaf {leaf} {witness}: {type(e).__name__}: {e}', file=sys.stderr)
    for h in pg['entries_hint']:
        key = (h['col'], h['para'])
        eid = f"{leaf:04d}-{h['col']}-{h['para']:02d}"
        for witness in 'ABCD':
            box, how = found[witness].get(key, (None, 'none'))
            rows.append(dict(id=eid, witness=witness, page=witness_page(leaf, witness),
                             x0=box[0] if box else '', y0=box[1] if box else '',
                             x1=box[2] if box else '', y1=box[3] if box else '',
                             ppi=PDF_DPI if witness != 'B' else '', strip='', y0s='', y1s='', how=how))
    return rows


def cmd_index(a):
    leaves = pages_of(a)
    print(f'{len(leaves)} pages')
    rows = []
    with Pool(a.workers) as pool:
        for n, part in enumerate(pool.imap(index_page, leaves), 1):
            rows.extend(part)
            if n % 100 == 0 or n == len(leaves):
                print(f'  [{n}/{len(leaves)}]', flush=True)
    old = {}
    if INDEX.exists() and not a.force:                     # keep strip columns already written by `crops`
        for r in csv.DictReader(open(INDEX, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE):
            old[(r['id'], r['witness'])] = r
    for r in rows:
        prev = old.get((r['id'], r['witness']))
        if prev:
            r.update(strip=prev['strip'], y0s=prev['y0s'], y1s=prev['y1s'])
    write_index(rows)
    per = {}
    for r in rows:
        per.setdefault(r['witness'], []).append(r['how'] != 'none')
    print('located: ' + ', '.join(f'{w} {sum(v)}/{len(v)} ({sum(v) / len(v):.0%})' for w, v in sorted(per.items())))


def write_index(rows):
    tmp = INDEX.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(COLUMNS) + '\n')
        for r in rows:
            f.write('\t'.join(str(r[c]) for c in COLUMNS) + '\n')
    tmp.rename(INDEX)
    print(f'written: {INDEX.relative_to(DJ.parent)} ({INDEX.stat().st_size // 1024} KB, {len(rows)} rows)')


# ---------------------------------------------------------------- the crops

def witness_image(leaf, witness):
    """The witness's page as an image, in the coordinate space the index uses. The rendered page of B, C and D is
    a temporary file of several MB: it is read into memory and deleted at once, or a full run would leave tens of
    gigabytes behind."""
    if witness == 'A':
        import glob as _glob
        return Image.open(_glob.glob(str(PAGES / 'jp2' / f'*_{leaf:04d}.jp2'))[0]).convert('L')
    tmp = DJ / 'cache' / 'crops_tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    if witness == 'B':
        path = tmp / f'b_{leaf:04d}.tif'
        subprocess.run(['ddjvu', '-format=tiff', f'-page={b_page(leaf)}', str(REPRINT), str(path)], check=True)
    else:
        pdf, page = (CORNELL, d_page(leaf)) if witness == 'D' else c_page(leaf)
        stem = tmp / f'{witness.lower()}_{leaf:04d}'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', str(PDF_DPI), '-gray', '-png',
                        '-singlefile', str(pdf), str(stem)], check=True)
        path = stem.with_suffix('.png')
    im = Image.open(path).convert('L')
    im.load()
    path.unlink(missing_ok=True)
    return im


def strip_page(args):
    """Build one page strip for one witness; -> (leaf, witness, [(id, y0s, y1s)], bytes written)."""
    leaf, witness, rows, ppi, force = args
    path = CROPS / witness / f'{leaf:04d}.png'
    boxes = [r for r in rows if r['x0'] != '']
    if not boxes:
        return leaf, witness, [], 0
    if path.exists() and not force:
        return leaf, witness, None, path.stat().st_size
    try:
        im = witness_image(leaf, witness)
    except Exception as e:                                 # noqa: BLE001
        print(f'leaf {leaf} {witness}: {type(e).__name__}: {e}', file=sys.stderr)
        return leaf, witness, [], 0
    scale = ppi / PDF_DPI
    crops, spans, y = [], [], 0
    for r in boxes:
        x0, y0, x1, y1 = (int(r['x0']), int(r['y0']), int(r['x1']), int(r['y1']))
        py = PAD_Y.get(witness, PAD)
        c = im.crop((max(0, x0 - PAD), max(0, y0 - py), x1 + PAD, y1 + py))
        if scale != 1.0:
            c = c.resize((max(1, round(c.width * scale)), max(1, round(c.height * scale))), Image.LANCZOS)
        crops.append(c)
        spans.append((r['id'], y, y + c.height))
        y += c.height
    W = max(c.width for c in crops)
    out = Image.new('L', (W, y), 255)
    for c, (_, y0s, _) in zip(crops, spans):
        out.paste(c, (0, y0s))
    path.parent.mkdir(parents=True, exist_ok=True)
    # black on white: one bit keeps the letterforms. Threshold, never Pillow's dithering convert('1') — dithered
    # paper grain is noise that PNG cannot compress (a page strip of A: 169 KB dithered against 35 KB thresholded).
    out.point(lambda v: 255 if v > THRESHOLD else 0).convert('1').save(path, format='PNG', optimize=True)
    return leaf, witness, spans, path.stat().st_size


def cmd_crops(a):
    if not INDEX.exists():
        sys.exit('run `dj_crops.py index` first')
    rows = list(csv.DictReader(open(INDEX, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    by = {}
    for r in rows:
        by.setdefault((int(r['id'][:4]), r['witness']), []).append(r)
    leaves = set(pages_of(a))
    jobs = [(leaf, w, rs, a.ppi, a.force) for (leaf, w), rs in sorted(by.items())
            if leaf in leaves and w in a.witness]
    print(f'{len(jobs)} page strips to consider ({len(leaves)} pages × {len(a.witness)} witnesses)')
    total = done = 0
    with Pool(a.workers) as pool:
        for n, (leaf, w, spans, size) in enumerate(pool.imap_unordered(strip_page, jobs), 1):
            total += size
            done += 1
            if spans:
                for eid, y0s, y1s in spans:
                    for r in by[(leaf, w)]:
                        if r['id'] == eid:
                            r.update(strip=f'crops/{w}/{leaf:04d}.png', y0s=y0s, y1s=y1s)
            if n % 50 == 0 or n == len(jobs):
                print(f'  [{n}/{len(jobs)}] {total / 1e6:.0f} MB so far', flush=True)
    write_index(rows)
    print(f'{done} strips, {total / 1e6:.1f} MB at {a.ppi} ppi')


def cmd_report(a):
    if INDEX.exists():
        rows = list(csv.DictReader(open(INDEX, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
        per = {}
        for r in rows:
            d = per.setdefault(r['witness'], dict(n=0, located=0, cropped=0))
            d['n'] += 1
            d['located'] += r['how'] != 'none'
            d['cropped'] += r['strip'] != ''
        for w, d in sorted(per.items()):
            print(f"  {w}: {d['n']} entries, located {d['located']} ({d['located'] / d['n']:.0%}), "
                  f"in a strip {d['cropped']} ({d['cropped'] / d['n']:.0%})")
    for w in 'ABCD':
        folder = CROPS / w
        if folder.exists():
            files = list(folder.glob('*.png'))
            size = sum(f.stat().st_size for f in files)
            print(f'  crops/{w}: {len(files)} strips, {size / 1e6:.1f} MB'
                  + (f' → {size / len(files) * 1119 / 1e6:.0f} MB for the whole book' if files else ''))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name, fn in (('index', cmd_index), ('crops', cmd_crops), ('report', cmd_report)):
        sp = sub.add_parser(name)
        sp.set_defaults(fn=fn)
        if name != 'report':
            sp.add_argument('--pages', help='leaves of scan A, e.g. 45,341,500-510')
            sp.add_argument('--workers', type=int, default=8)
            sp.add_argument('--force', action='store_true', help='redo what is already there')
        if name == 'crops':
            sp.add_argument('--witness', default='ABCD', help='which witnesses to crop (default ABCD)')
            sp.add_argument('--ppi', type=int, default=600, help='resolution of the crops (default 600)')
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
