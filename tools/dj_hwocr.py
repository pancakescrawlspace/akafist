#!/usr/bin/env python3
"""Phase 3b step 2, option (C) of djachenko/PLAN.md: our own OCR model for the Church Slavonic headwords, trained
with Kraken on line images. This script prepares the training data; the training itself runs in Kraken's own Python
environment (~/.venvs/kraken — PLAN.md has the commands).

    python3 tools/dj_hwocr.py data [--synth 8000] [--workers 14]    # the training data -> djachenko/cache/hwocr/
    python3 tools/dj_hwocr.py data --only gt,synth                   # rebuild some sets, keep the others
    python3 tools/dj_hwocr.py sheet agree [--n 30] [--split val]     # a contact sheet: samples and their labels

A sample is one printed line: an image (scan A at 400 ppi, greyscale, the paper brought to white) and its text in
a .gt.txt file beside it, the form `ketos train -f path` reads. Three kinds:

  gt     every printed line of the ground-truth pages (eval/gt/): its `¦` markers pair the GT's lines one to one
         with scan A's (dj_inspect.py gtlines). Exact labels. Letters the GT supplies from another copy (‹…›) are
         not in A's image and are left out of the label; such a line is flagged `partial`.
  agree  labelled with the voted text of ocr/*.json, where witnesses D and B agree (no `disputed` span, VOTE.md):
         the first line of an entry wherever they read its head alike (the rest of the line is the vote's; on the
         GT pages such a head is right in ~83 %, the line's characters in ~99 % — `data` prints it), and 8 % of the
         continuation lines they read alike throughout (the book's civil type). Not from a GT page, not from a
         column side whose margin the scan cuts off (the image would lack letters the label has).
  synth  first lines set by Typst: a head in one of five Church Slavonic faces, accented as the book accents its
         headwords, a separator, then real definition text in Old Standard; exact labels by construction, the image
         roughened to look like a scan. They teach the letters the other two kinds have too few of.

Labels are written at the norm level (dj_witness.norm_char: Church Slavonic letters folded to civil ones, look-alikes
and dashes unified, оу -> у; spaces kept) — "stage 1": the level of the automatic labels, and the level at which the
headwords are benchmarked (eval/RESULTS.md). manifest.tsv keeps the strict label (letters as printed) wherever it is
known, and for the synthetic lines also the label with the accents set (`marked`), for later stages: the Phase 0
decision to leave accents and titla out of the headwords is not final.

Splits: `test` = the two held-out GT pages (leaves 283 and 696, eval/README.md) and nothing else from them; `val` =
the agree samples of every 20th leaf, for Kraken to choose its best checkpoint by; `train` = everything else.
"""
import argparse, csv, json, random, re, shutil, subprocess, sys, unicodedata, zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import DJ, OCR, align, norm_char  # noqa: E402
from dj_abbyy import CLIPPED  # noqa: E402
from dj_build import GT_DIR, gt_leaves, gt_part, esc  # noqa: E402

OUT = DJ / 'cache' / 'hwocr'
ENTRIES = DJ / 'entries.tsv'
FONTS = DJ / 'fonts'
HELD_OUT = (283, 696)                   # the GT pages never used to fit anything (eval/README.md): the test set
VAL_EVERY = 20                          # every 20th leaf's agree samples are the validation set
CONT_RATE = 8                           # % of the undisputed continuation lines taken (the book's civil type, real)
SCALE = 2 / 3                           # scan A's 600 ppi -> 400 ppi
PPI = 400
PAD = 12                                # px at 600 ppi around A's line box
CS_FONTS = ('Ponomar Unicode', 'Pochaevsk Unicode', 'Monomakh Unicode', 'Menaion Unicode', 'Fedorovsk Unicode')
SEP = re.compile(r'=|—|–|\s-\s|\(')
# One symbol per printed glyph. The OCR layers write look-alikes the book does not have (session 6, from Kraken's
# alphabet warning): fita as barred o, І as palochka, h and j as Cyrillic shha and je; braces where the book prints
# brackets. Spacing accents (a Greek breathing standing alone) go the way the norm level sends every accent.
FOLD = str.maketrans({'Ө': 'Ѳ', 'ө': 'ѳ', 'Ӏ': 'І', 'ӏ': 'і', 'һ': 'h', 'Һ': 'H', 'ј': 'j', 'Ј': 'J',
                      '{': '(', '}': ')'})
JUNK = set('■|')                        # OCR debris (a column rule read as |): a line with it is left out


def fold(s):
    return ''.join(ch for ch in s.translate(FOLD) if unicodedata.category(ch) not in ('Sk', 'Lm'))


# ---------------------------------------------------------------- labels

def norm(s):
    """A label at the norm level: norm_char per character, runs of whitespace kept as one space, оу -> у."""
    out = []
    for ch in s:
        if ch.isspace():
            if out and out[-1] != ' ':
                out.append(' ')
            continue
        out.append(norm_char(ch))
    t = fold(''.join(out)).strip()
    return t.replace('оу', 'у').replace('Оу', 'У').replace('ОУ', 'У')


def clean(s):
    """The voted text's spacing as printed: no space before . , ; : ! ? ) or after ( „ (D's text layer puts them)."""
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\s+([.,;:!?)])', r'\1', s)
    return re.sub(r'([(„])\s+', r'\1', s)


def letters(s):
    return sum(ch.isalpha() for ch in s)


# ---------------------------------------------------------------- images

def normalise_image(a):
    """Greyscale array -> the ink kept, the paper brought to white: stretch the 1st percentile (ink) to 0 and the
    60th (paper; a line image is mostly paper) to 255."""
    a = a.astype(np.float32)
    lo, hi = np.percentile(a, [1, 60])
    a = (a - lo) / max(1.0, hi - lo) * 255
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def a_line_image(im, box):
    x0, y0, x1, y1 = box
    crop = im.crop((max(0, x0 - PAD), max(0, y0 - PAD), min(im.size[0], x1 + PAD), min(im.size[1], y1 + PAD)))
    crop = crop.resize((round(crop.size[0] * SCALE), round(crop.size[1] * SCALE)), Image.LANCZOS)
    return normalise_image(np.asarray(crop))


def save(kind, sid, img, label):
    d = OUT / kind
    img.save(d / f'{sid}.png', optimize=True)
    (d / f'{sid}.gt.txt').write_text(label + '\n', encoding='utf-8')
    return str((d / f'{sid}.png').relative_to(OUT))


# ---------------------------------------------------------------- the ground truth, line by line

def gt_lines(leaf):
    """eval/gt/NNNN.txt -> {column: [(strict label, first, flags)]} per printed line, in order."""
    cols, n = {}, None
    for raw in (GT_DIR / f'{leaf:04d}.txt').read_text(encoding='utf-8').splitlines():
        if raw.startswith('@ col'):
            n = int(raw.split()[2])
            cols[n] = []
        elif raw.strip() and not raw.startswith(('#', '@')) and n is not None:
            cont = raw.startswith('+ ')
            text, regions, cuts = gt_part(raw[2:] if cont else raw)
            hidden = {k for a, b, kind in regions if kind in ('o', 'q') for k in range(a, b)}
            for j, a in enumerate(cuts):
                b = cuts[j + 1] if j + 1 < len(cuts) else len(text)
                label = ''.join(ch for k, ch in enumerate(text[a:b], a) if k not in hidden).strip()
                if 0 < b < len(text) and text[b - 1].isalpha() and text[b].isalpha():
                    label += '-'                                 # the print broke the word with a hyphen
                flags = []
                if any(a <= k < b for k, _, kind in regions if kind == 'o'):
                    flags.append('partial')                     # letters cut off in A, read in another copy
                if any(a <= k < b for k, _, kind in regions if kind == 'q'):
                    flags.append('uncertain')
                cols[n].append((label, j == 0 and not cont, flags))
    return cols


def a_columns(pg):
    return {c['n']: [(pi, ln) for pi, p in enumerate(c['paragraphs'], 1) for ln in p['lines']] for c in pg['columns']}


# ---------------------------------------------------------------- one leaf: its gt and agree samples

_ids = None


def entry_ids():
    global _ids
    if _ids is None:
        _ids = {r['id'] for r in csv.DictReader(open(ENTRIES, encoding='utf-8'), delimiter='\t',
                                                quoting=csv.QUOTE_NONE)}
    return _ids


def agree_lines(pg):
    """The first lines of entries whose head D and B read alike: [(column n, line index in the column, label,
    disputed characters in the rest of the line)]. Requiring the whole line to agree would leave one line in ten
    (a comma, a dropped "=" is enough); the rest of the line is the vote's, right in ~99 % of its characters."""
    ids, out = entry_ids(), []
    cut = {w.split(':')[0].split()[1] for w in pg['warnings'] if 'margin cut off' in w}
    W = pg['size'][0]
    for c in pg['columns']:
        if c['side'] in cut:
            continue
        k = 0
        for pi, par in enumerate(c['paragraphs'], 1):
            first_k, k = k, k + len(par['lines'])
            if f"{pg['idx']:04d}-{c['n']}-{pi:02d}" not in ids or not par.get('breaks') or not par['lines']:
                continue
            ln, text, br = par['lines'][0], par.get('text_merged', ''), par['breaks']
            b0, hy = br[0]
            b1 = br[1][0] if len(br) > 1 else len(text)
            m = SEP.search(text, b0, b1)
            if not m or letters(text[b0:m.start()]) < 2:
                continue                                        # no separator in the line: the head is unclear
            dis = par.get('disputed', [])
            if any(s < m.start() and e > b0 for s, e, *_ in dis):
                continue                                        # D and B read the head differently
            tail = sum(min(e, b1) - max(s, m.start()) for s, e, *_ in dis if s < b1 and e > m.start())
            if ln['bbox'][0] <= CLIPPED or ln['bbox'][2] >= W - CLIPPED:
                continue
            label = clean(text[b0:b1]) + ('-' if hy else '')
            if letters(label) < 4 or not 0.7 <= len(label) / max(1, len(ln['text'].strip())) <= 1.4:
                continue                                        # a line start carried over badly
            if JUNK & set(label):
                continue
            out.append((c['n'], first_k, label, tail))
    return out


def cont_lines(pg):
    """A sample of the continuation lines D and B read alike throughout (the voted text is wrong in ~0.13 % of such
    characters): [(column n, line index in the column, label)]. They show the model the book's own civil type."""
    out = []
    cut = {w.split(':')[0].split()[1] for w in pg['warnings'] if 'margin cut off' in w}
    W = pg['size'][0]
    for c in pg['columns']:
        if c['side'] in cut:
            continue
        k = 0
        for par in c['paragraphs']:
            text, br, dis = par.get('text_merged', ''), par.get('breaks') or [], par.get('disputed', [])
            for j in range(1, min(len(br), len(par['lines']))):
                if zlib.crc32(f"{pg['idx']}-{c['n']}-{k + j}".encode()) % 100 >= CONT_RATE:
                    continue
                b0, hy = br[j]
                b1 = br[j + 1][0] if j + 1 < len(br) else len(text)
                ln = par['lines'][j]
                if any(s < b1 and e > b0 for s, e, *_ in dis) or ln['bbox'][2] >= W - CLIPPED:
                    continue
                label = clean(text[b0:b1]) + ('-' if hy else '')
                if letters(label) >= 4 and 0.7 <= len(label) / max(1, len(ln['text'].strip())) <= 1.4 \
                        and not JUNK & set(label):
                    out.append((c['n'], k + j, label))
            k += len(par['lines'])
    return out


def do_leaf(leaf):
    """-> (manifest rows, label checks): the leaf's gt samples (a GT page) or agree samples (any other), and on a
    GT page also each agree-style label beside the GT's line, to measure the automatic labels."""
    pg = json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))
    if pg['section'] not in ('main', 'supplement') or not pg['columns']:
        return [], []
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from dj_crops import witness_image
    im, rows, checks = None, [], []
    acols = a_columns(pg)
    if leaf in GT_LEAVES:
        split = 'test' if leaf in HELD_OUT else 'train'
        g = gt_lines(leaf)
        for n, lines in g.items():
            if len(lines) != len(acols.get(n, [])):
                print(f'  leaf {leaf} column {n}: {len(lines)} GT lines, {len(acols.get(n, []))} in A — skipped')
                continue
            for k, ((label, first, flags), (_, ln)) in enumerate(zip(lines, acols[n])):
                if not letters(label):
                    continue
                im = im or witness_image(leaf, 'A')
                sid = f'{leaf:04d}-{n}-{k:03d}'
                path = save('gt', sid, a_line_image(im, ln['bbox']), norm(label))
                rows.append(dict(id=sid, set='gt', split=split, leaf=leaf, first=int(first),
                                 flags=';'.join(flags), image=path, norm=norm(label), strict=label))
        for n, k, label, _ in agree_lines(pg):                  # the automatic label, against the GT's
            if n in g and k < len(g[n]):
                checks.append((norm(label), norm(g[n][k][0]), 'partial' in g[n][k][2]))
        return rows, checks
    if leaf in HELD_OUT:
        return [], []
    split = 'val' if leaf % VAL_EVERY == 7 else 'train'
    for n, k, label, tail in agree_lines(pg):
        im = im or witness_image(leaf, 'A')
        sid = f'{leaf:04d}-{n}-{k:03d}'
        path = save('agree', sid, a_line_image(im, acols[n][k][1]['bbox']), norm(label))
        rows.append(dict(id=sid, set='agree', split=split, leaf=leaf, first=1,
                         flags=f'tail_disputed={tail}' if tail else '', image=path, norm=norm(label), strict=''))
    for n, k, label in cont_lines(pg):
        im = im or witness_image(leaf, 'A')
        sid = f'{leaf:04d}-{n}-{k:03d}'
        path = save('agree', sid, a_line_image(im, acols[n][k][1]['bbox']), norm(label))
        rows.append(dict(id=sid, set='agree', split=split, leaf=leaf, first=0, flags='', image=path,
                         norm=norm(label), strict=''))
    return rows, checks


GT_LEAVES = set(gt_leaves())


# ---------------------------------------------------------------- synthetic first lines

VOWELS = 'аеиоуыэюяѣіѡєѧꙗѫѭѵїАЕИОУЯІѠЄѦꙖѪѴ'
PSILI, OXIA, VARIA = '҆', '́', '̀'


def cs_ify(word, rnd, spell=True):
    """A civil word spelled the Church Slavonic way at random (spell=False: a word already so spelled), with the
    book's headword accents: the label (letters as printed, no marks) and the text to set. The letters the GT has
    too few examples of come up more often than in real text, so that each is seen a few hundred times."""
    w = word.lower() if spell else ''
    out = [] if spell else [word]
    i = 0
    while i < len(w):
        ch, nxt, first = w[i], w[i + 1: i + 2], i == 0
        r = rnd.random()
        if w.startswith('от', i) and first and r < .5:
            out.append('ѿ'); i += 2; continue                  # noqa: E702
        if w.startswith('кс', i) and r < .7:
            out.append('ѯ'); i += 2; continue                  # noqa: E702
        if w.startswith('пс', i) and r < .7:
            out.append('ѱ'); i += 2; continue                  # noqa: E702
        if ch == 'у':
            ch = 'оу' if first and r < .5 else 'ꙋ' if r < .55 else 'ѹ' if r < .62 else 'ѫ' if r < .75 else 'у'
        elif ch == 'о':
            ch = 'ѡ' if (first and r < .35) or r < .1 else 'ѻ' if r < .12 else 'о'
        elif ch == 'я':
            ch = 'ꙗ' if first and r < .6 else 'ѧ' if r < .6 else 'ѩ' if r < .75 else 'я'
        elif ch == 'е':
            ch = 'є' if (first and r < .8) or r < .08 else 'ѥ' if r < .2 else 'е'
        elif ch == 'ю':
            ch = 'ѭ' if r < .25 else 'ю'
        elif ch == 'и':
            ch = 'ї' if nxt in tuple('аеиоуюяѣ') and r < .7 else 'ѵ' if r < .08 else 'и'
        elif ch == 'з':
            ch = 'ѕ' if r < .08 else 'ꙁ' if r < .12 else 'з'
        elif ch == 'ф':
            ch = 'ѳ' if r < .4 else 'ф'
        out.append(ch)
        i += 1
    s = ''.join(out)
    if spell and word[:1].isupper():
        s = (s[0].upper() + s[1:]) if not s.startswith('оу') else 'Оу' + s[2:]
    # the accents: a breathing on an initial vowel, an acute on one vowel (a grave on a final one now and then)
    marks = [''] * len(s)
    if s[0] in VOWELS:
        marks[0] += PSILI
    vs = [k for k, ch in enumerate(s) if ch in VOWELS and not (k > 0 and s[k - 1:k + 1] in ('оу', 'Оу'))]
    if vs and rnd.random() < .95:
        k = rnd.choice(vs)
        marks[k] += VARIA if k == vs[-1] and k == len(s) - 1 and rnd.random() < .3 else OXIA
    return s, ''.join(ch + m for ch, m in zip(s, marks))


CS_ONLY = set('ѡѿѻꙋѹѧꙗєѥїѵѳѯѱѫѭѩѕꙁ')


def synth_texts(n, rnd, heads, civil):
    """n synthetic first lines: (strict label, the same with its accents, Typst markup). A quarter have a head in the
    civil type (bold, as the book sets the Russian words it lists, e.g. Выбойка), the rest one in Church Slavonic."""
    out = []
    for _ in range(n):
        if rnd.random() < .25:
            w = rnd.choice(civil)
            head_lab, head_marked, head_typ = w, w, f'#strong[{esc(w)}];'
        else:
            words = [rnd.choice(heads)] + ([rnd.choice(heads).lower()] if rnd.random() < .15 else [])
            pieces = [cs_ify(w, rnd, spell=not (CS_ONLY & set(w.lower()))) for w in words]
            joint = ', ' if len(pieces) > 1 and rnd.random() < .5 else ' '
            head_lab = joint.join(p[0] for p in pieces)
            head_marked = joint.join(p[1] for p in pieces)
            head_typ = joint.join(f'#cs[{esc(p[1])}];' for p in pieces)
        tail = rnd.choice(TAILS)
        sep = rnd.choices([' = ', '=', ' — ', ' ('], [60, 15, 15, 10])[0]
        start = rnd.randrange(0, max(1, len(tail) - 60))
        start = tail.find(' ', start) + 1 if start else 0
        want = rnd.randint(18, 44) - len(head_lab)
        seg = tail[start:]
        cut = seg.find(' ', max(4, want))
        seg = (seg[:cut] if cut > 0 else seg[:want]).strip().lstrip('=—–- ')
        words_t = seg.split(' ')
        if len(words_t) > 3 and rnd.random() < .25:              # an italic source or quotation, as printed
            a = rnd.randrange(1, len(words_t))
            b = min(len(words_t), a + rnd.randint(1, 3))
            seg_typ = ' '.join(esc(x) for x in words_t[:a]) + ' #emph[' + ' '.join(esc(x) for x in words_t[a:b]) + '];' + \
                (' ' + ' '.join(esc(x) for x in words_t[b:]) if b < len(words_t) else '')
        else:
            seg_typ = esc(seg)
        label = head_lab + sep + seg
        out.append((label, head_marked + sep + seg, f'{head_typ}{esc(sep) if sep.strip() else sep}{seg_typ}'))
    return out


def roughen(path, seed):
    """A clean Typst rendering -> a scan-like line: cropped to its ink like A's lines, ink and paper of random
    darkness, the ink spread now and then, a slight rotation, blur and noise; then the same normalisation as scan
    A's lines."""
    rnd = np.random.default_rng(seed)
    im = Image.open(path).convert('L')
    ys, xs = np.nonzero(np.asarray(im) < 160)                  # to the ink, with the margin A's lines get, so
    if len(ys):                                                 # that the letters come out the same size in both
        m = round(PAD * SCALE)
        im = im.crop((max(0, xs.min() - m), max(0, ys.min() - m), min(im.size[0], xs.max() + m + 1),
                      min(im.size[1], ys.max() + m + 1)))
    if rnd.random() < .3:                                       # heavier ink (thinning ate the strokes of Old
        im = im.filter(ImageFilter.MinFilter(3))                # Standard at 400 ppi; the book's print is heavy)
    im = im.rotate(rnd.uniform(-.5, .5), resample=Image.BICUBIC, expand=False, fillcolor=255)
    im = im.filter(ImageFilter.GaussianBlur(rnd.uniform(.3, 1.1)))
    a = np.asarray(im).astype(np.float32) / 255
    ink, paper = rnd.uniform(10, 70), rnd.uniform(195, 245)
    a = paper - (paper - ink) * (1 - a)
    a += rnd.normal(0, rnd.uniform(3, 12), a.shape)
    return normalise_image(a)


def roughen_one(args):
    src, dst, seed = args
    roughen(src, seed).save(dst, optimize=True)
    src.unlink()


def build_synth(n, rows_real, workers, seed=2026):
    rnd = random.Random(seed)
    # heads: the GT's own (letters as printed; not the held-out pages') and the civil heads of the agree labels
    heads = []
    for leaf in GT_LEAVES - set(HELD_OUT):
        for lines in gt_lines(leaf).values():
            for label, first, flags in lines:
                if first and not flags:
                    m = SEP.search(label)
                    h = label[:m.start()].strip() if m else ''
                    if 2 <= letters(h) and len(h.split()) == 1:
                        heads.append(h.strip(','))
    for r in rows_real:
        if r['set'] == 'agree':
            m = SEP.search(r['norm'])
            h = r['norm'][:m.start()].strip().strip(',') if m else ''
            if len(h) >= 3 and h.isalpha() and h[0].isupper():
                heads.append(h)
    global TAILS
    TAILS = [re.sub(r'\s+', ' ', ''.join(ch for ch in fold(r['definition']) if ch not in JUNK))
             for r in csv.DictReader(open(ENTRIES, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE)
             if len(r['definition']) > 80]
    civil = sorted({h for h in heads if not CS_ONLY & set(h.lower())})
    texts = synth_texts(n, rnd, heads, civil)
    tmp = OUT / 'synth_tmp'
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    pages = []
    for k, (label, _, typ) in enumerate(texts):
        font = rnd.choice(CS_FONTS)
        pages.append(f'#page[\n#set text(size: {rnd.uniform(11.2, 12.6):.1f}pt, spacing: {rnd.randint(90, 160)}%)\n'
                     f'#let cs(b) = text(font: "{font}", size: {rnd.uniform(1.08, 1.22):.2f}em, b)\n'
                     f'#box[{typ}]\n]')
    doc = ('#set page(width: auto, height: auto, margin: (x: 2mm, y: 1.6mm))\n'
           '#set text(font: "Old Standard TT", lang: "ru", hyphenate: false)\n'
           '#set smartquote(enabled: false)\n' + '\n'.join(pages) + '\n')
    (tmp / 'synth.typ').write_text(doc, encoding='utf-8')
    r = subprocess.run(['typst', 'compile', '--font-path', str(FONTS), str(tmp / 'synth.typ'),
                        str(tmp / '{0p}.png'), '--ppi', str(PPI)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('typst failed:\n' + r.stderr[:3000])
    rendered = sorted(tmp.glob('*.png'))
    assert len(rendered) == len(texts), (len(rendered), len(texts))
    rows, jobs = [], []
    for k, (src, (label, marked, _)) in enumerate(zip(rendered, texts)):
        sid = f's{k:05d}'
        jobs.append((src, OUT / 'synth' / f'{sid}.png', seed * 100000 + k))
        (OUT / 'synth' / f'{sid}.gt.txt').write_text(norm(label) + '\n', encoding='utf-8')
        rows.append(dict(id=sid, set='synth', split='train', leaf='', first=1, flags='', image=f'synth/{sid}.png',
                         norm=norm(label), strict=label, marked=marked))
    with Pool(workers) as pool:
        pool.map(roughen_one, jobs, chunksize=50)
    shutil.rmtree(tmp)
    return rows


# ---------------------------------------------------------------- commands

def read_manifest():
    with open(OUT / 'manifest.tsv', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\'))


def cmd_data(a):
    only = set(a.only.split(',')) if a.only else {'gt', 'agree', 'synth'}
    rows = [r for r in read_manifest() if r['set'] not in only] if a.only else []
    for d in only:
        shutil.rmtree(OUT / d, ignore_errors=True)
        (OUT / d).mkdir(parents=True)
    if only & {'gt', 'agree'}:
        leaves = sorted(int(f.stem) for f in OCR.glob('[0-9][0-9][0-9][0-9].json'))
        if 'agree' not in only:
            leaves = [x for x in leaves if x in GT_LEAVES]
        checks = []
        with Pool(a.workers) as pool:
            for k, (r, c) in enumerate(pool.imap_unordered(do_leaf, leaves, chunksize=4), 1):
                rows += [x for x in r if x['set'] in only]
                checks += c
                if k % 200 == 0:
                    print(f'  [{k}/{len(leaves)}] {len(rows)} samples')
        # how good are the automatic labels? each against the GT's line (norm level, spacing ignored)
        ok = [(x.replace(' ', ''), y.replace(' ', '')) for x, y, partial in checks if not partial]
        head_same = sum(1 for x, y in ok if SEP.split(x)[0] == SEP.split(y)[0])
        edits = sum(align(list(x), list(y))[0] for x, y in ok)
        print(f'automatic first-line labels on the GT pages: {len(ok)} lines; head identical to the GT in {head_same} '
              f'({head_same / max(1, len(ok)):.0%}), character error of the whole line '
              f'{edits / max(1, sum(len(y) for _, y in ok)):.2%}')
    if 'synth' in only and a.synth:
        rows += build_synth(a.synth, rows, a.workers)
    rows.sort(key=lambda r: (r['set'], r['id']))
    for r in rows:
        r.setdefault('marked', '')                              # the label with accents: synthetic lines only
    with open(OUT / 'manifest.tsv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writeheader()
        w.writerows(rows)
    for split in ('train', 'val', 'test'):
        sel = [r for r in rows if r['split'] == split and 'partial' not in r['flags']]
        (OUT / f'{split}.txt').write_text(''.join(str(OUT / r['image']) + '\n' for r in sel), encoding='utf-8')
    size = sum(p.stat().st_size for p in OUT.rglob('*.png'))
    print('samples (without the partial lines):')
    for s in ('gt', 'agree', 'synth'):
        by = {sp: sum(1 for r in rows if r['set'] == s and r['split'] == sp and 'partial' not in r['flags'])
              for sp in ('train', 'val', 'test')}
        print(f'  {s:6} ' + ', '.join(f'{k} {v}' for k, v in by.items() if v))
    print(f'written: {OUT.relative_to(DJ.parent)}/ — manifest.tsv, train/val/test.txt, {size / 1e6:.0f} MB of images')


def cmd_sheet(a):
    rows = [r for r in read_manifest() if r['set'] == a.set and (not a.split or r['split'] == a.split)]
    rows = random.Random(a.seed).sample(rows, min(a.n, len(rows)))
    font = ImageFont.truetype(str(FONTS / 'OldStandard-Regular.ttf'), 22)
    tiles = []
    for r in rows:
        im = Image.open(OUT / r['image']).convert('L')
        im = im.resize((min(900, im.size[0]) , round(im.size[1] * min(900, im.size[0]) / im.size[0])))
        t = Image.new('L', (900, im.size[1] + 34), 255)
        t.paste(im, (0, 0))
        ImageDraw.Draw(t).text((4, im.size[1] + 4), f'{r["id"]}: {r["norm"]}', fill=90, font=font)
        tiles.append(t)
    sheet = Image.new('L', (900, sum(t.size[1] + 6 for t in tiles)), 255)
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.size[1] + 6
    path = OUT / f'sheet_{a.set}{"_" + a.split if a.split else ""}.png'
    sheet.save(path)
    print('written:', path.relative_to(DJ.parent))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('data')
    s.add_argument('--synth', type=int, default=8000, help='synthetic first lines (0: none)')
    s.add_argument('--workers', type=int, default=14)
    s.add_argument('--only', help='rebuild only these sets (comma-separated: gt,agree,synth), keep the others')
    s = sub.add_parser('sheet')
    s.add_argument('set', choices=('gt', 'agree', 'synth'))
    s.add_argument('--split', choices=('train', 'val', 'test'))
    s.add_argument('--n', type=int, default=30)
    s.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    {'data': cmd_data, 'sheet': cmd_sheet}[a.cmd](a)


if __name__ == '__main__':
    main()
