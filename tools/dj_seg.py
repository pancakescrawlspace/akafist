#!/usr/bin/env python3
"""Phase 3a/3b of djachenko/PLAN.md: where the entries begin, read off witnesses C and D.

    python3 tools/dj_seg.py                      # write djachenko/segmentation.tsv and print the summary
    python3 tools/dj_seg.py --pages 57,58        # only those leaves (the file is rewritten for them alone)
    python3 tools/dj_seg.py --check              # the summary only, nothing written
    python3 tools/dj_seg.py --show 57 a          # every line of one column side, with each witness's verdict

Why.  An entry begins at a flush line and continues at the hanging indent, so scan A's geometry (Phase 3a) is what
segments the dictionary.  But A's left margin is cut on 242 pages and its right margin on 313, and even on an
intact page ABBYY drops the left half of a line under a stain (p. 20: the line `Аполинъ` measures as indented, so
no entry begins and the lemma disappears into `Апокрифы`).  Witnesses C (Indiana) and D (Cornell) have both
margins on every page — C's narrowest outer margin is 27 pt and no line of it touches an image edge — and the four
witnesses are one typesetting (COPIES.md), so their indentation says where the printed paragraphs begin.

Method, per column side: the voted text of Phase 3b step 1 is aligned to the witness's text (Levenshtein on the
"norm" level) and every printed line start of A (`breaks`) carried over and snapped to a line start of the
witness within LINE_TOL; that witness line's indentation level comes from dj_witness.indent_levels, which
deskews the column first (the Google columns drift by up to 13 pt, more than the indent itself).  Which of a
column's two levels is the flush one the geometry cannot say — a column may lie wholly inside one long article,
or hold nothing but one-line entries — so A settles that: one yes/no per column decided by ~50 lines it reads
right 99 % of the time (flush_level).  C and D then vote line by line: where both call a line flush an entry
begins there, where both call it indented it continues one, and where they differ A keeps its own reading.

djachenko/segmentation.tsv — the verdict on every printed line C and D agree about (98 % of them), which
dj_abbyy.py applies when it groups lines into paragraphs.  A line is keyed by its baseline in the 600 ppi image,
which no re-run changes.  It is the witnesses' reading, not a list of corrections: it does not depend on what A
made of the page, so re-running this and dj_abbyy.py in either order gives the same book.  The file is committed,
so dj_abbyy.py reproduces the segmentation without the witnesses' scans, which git does not hold.
    leaf side base verdict       verdict: start = an entry begins at this line; continue = it continues one
Lines where the two disagree, or that the alignment cannot carry over, are left out and A decides them alone.
`--show LEAF SIDE` prints a column with the witnesses' reading of every line, which is where to check one by eye.

Order: dj_abbyy.py, dj_heads.py text (which this needs: `text_merged` and `breaks`), dj_seg.py, then dj_abbyy.py
again — it reads segmentation.tsv when it groups lines into paragraphs — and dj_heads.py text once more, for the
pages whose paragraphs moved.  One pass reaches the fixed point; the summary's last figure says so (0 lines
differing from what is in ocr/*.json).
"""
import argparse, bisect, csv, re, sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import DJ, OCR, align, indent_levels, load_page, norm_seq, page_text, side_texts

SEG = DJ / 'segmentation.tsv'
COLUMNS = ['leaf', 'side', 'base', 'verdict']
LINE_TOL = 4           # characters: how far an A line start may move to reach a line start of the witness
MIN_LETTERS = 4        # a line ABBYY read as fewer letters than this is a speck or a stray mark, not a line:
#                        it has nothing to align, and a paragraph started on one would hold no text at all
LETTER = re.compile(r'[^\W\d_]', re.UNICODE)
WITNESSES = ('C', 'D')


def a_lines(pg, side):
    """A's printed lines of one column side, top to bottom -> (text, [(line, start offset in text)]).

    The text is the voted text of Phase 3b step 1 (`text_merged`, witness D corrected by B/A/C), not ABBYY's own
    reading: ABBYY is at its worst on the headwords, which is exactly where the line starts are, so aligning its
    text to a witness misplaces them.  `breaks` gives the offset of every printed line in it, one per line of
    A's paragraph, in order.  -> (None, None) for a page dj_heads.py has not done yet."""
    text, out = '', []
    for c in pg['columns']:
        if c['side'] != side:
            continue
        for p in c['paragraphs']:
            if 'breaks' not in p or 'text_merged' not in p:
                return '', []
            if not p['text_merged'].strip():
                continue
            if text:
                text += ' '
            base = len(text)
            if len(p['lines']) != len(p['breaks']):
                return '', []
            for ln, brk in zip(p['lines'], p['breaks']):
                if len(LETTER.findall(ln['text'])) >= MIN_LETTERS:   # not a speck ABBYY read as a line of its own
                    out.append((ln, base + brk[0]))
            text += p['text_merged'].strip()
    return text, out


def levels_of(pg, side, name):
    """-> {baseline of an A line: (indentation level in the witness, the witness's reading of the line)}; a line
    for which neither the alignment nor the line count reaches the witness is left out.  Level 0 is the lowest
    indentation the column shows, which is not by itself the flush one — see flush_level()."""
    a_text, lines = a_lines(pg, side)
    if not a_text:
        return {}
    P = page_text(name, leaf_of(pg))
    lv = indent_levels(P)
    S = side_texts(P)[side]
    w_text, w_lines = S['text'], S['lines']
    if not w_text or not w_lines:
        return {}
    a_seq, a_idx = norm_seq(a_text)
    w_seq, w_idx = norm_seq(w_text)
    if not a_seq or not w_seq:
        return {}
    _, _, j_at = align(a_seq, w_seq)
    order = sorted(range(len(w_lines)), key=lambda q: w_lines[q]['start'])
    keys = [w_lines[q]['start'] for q in order]
    at = []                                        # per A line: the index into `order` it snapped to, or None
    for ln, off in lines:
        i = bisect.bisect_left(a_idx, off)
        if i >= len(a_seq):
            at.append(None)
            continue
        j = j_at[i]
        raw = w_idx[j] if j < len(w_seq) else len(w_text)
        k = bisect.bisect_left(keys, raw)
        near = [q for q in (k - 1, k) if 0 <= q < len(keys) and abs(keys[q] - raw) <= LINE_TOL]
        at.append(min(near, key=lambda q: abs(keys[q] - raw)) if near else None)
    # ABBYY reads only part of a line where the page is stained or the margin is cut, so its start cannot be
    # carried over; between two anchored lines the witness's k-th line is the answer when it has as many as A
    # (the same rule as dj_heads.break_positions).  Anchors must not cross each other.
    anchors = [(i, q) for i, q in enumerate(at) if q is not None]
    anchors = [(i, q) for n, (i, q) in enumerate(anchors)
               if all(anchors[m][1] < q for m in range(n))
               and all(anchors[m][1] > q for m in range(n + 1, len(anchors)))]
    bounds = [(-1, -1)] + anchors + [(len(lines), len(keys))]
    for (i0, q0), (i1, q1) in zip(bounds, bounds[1:]):
        gap = [i for i in range(i0 + 1, i1) if at[i] is None]
        if gap and len(gap) == q1 - q0 - 1:
            for n, i in enumerate(gap):
                at[i] = q0 + 1 + n
    # one typesetting means one line of A per line of the witness: where ABBYY's reading is so damaged that two
    # of A's lines reach for the same line of the witness, neither is decided (it is what made the verdict on
    # p. 167 `Євшанъ` depend on the segmentation it was meant to correct).
    claimed = Counter(q for q in at if q is not None)
    out = {}
    for (ln, _), q in zip(lines, at):
        if q is None or claimed[q] > 1:
            continue
        wl = w_lines[order[q]]
        level = lv.get((wl['side'], wl['y0']))
        if level is not None:
            out[ln['base']] = (level, wl['raw'])
    return out


def flush_level(levels, a_starts):
    """Which indentation level of a column is the flush one — the only thing the witness's geometry cannot say by
    itself: a column may show both levels, or only the hanging one (it lies inside one long article), or only the
    flush one (a column of one-line entries), and a speck read as a word can push a flush line below the level.

    A settles it.  Its segmentation is right on ~99 % of the lines, and this is one yes/no per column decided by
    ~50 of them, so the majority is safe even on the cut-margin pages, where A guesses and is right on ~81 %.
    -> the level at or below which a line is flush, or None when A and the witness do not agree well enough to
    tell (F1 under 0.5); flush levels are compared as "level <= f".
    """
    if not levels:
        return None
    best = None
    for f in (-1, 0, 1):
        pred = {b for b, (lv, _) in levels.items() if lv <= f}
        hit = len(pred & a_starts)
        f1 = 2 * hit / (len(pred) + len(a_starts)) if (pred or a_starts) else 1.0
        if best is None or f1 > best[0]:
            best = (f1, f)
    return best[1] if best[0] >= 0.5 else None


def verdicts(pg, side, name):
    """-> {baseline of an A line: (True when the witness begins a paragraph there, its reading of the line)}."""
    levels = levels_of(pg, side, name)
    a_starts = {p['lines'][0]['base'] for c in pg['columns'] if c['side'] == side
                for p in c['paragraphs'] if p['hanging'] and p['lines']}
    f = flush_level(levels, a_starts)
    if f is None:
        return {}
    return {b: (lv <= f, raw) for b, (lv, raw) in levels.items()}


def leaf_of(pg):
    return pg['idx']


def check(leaf):
    """-> (leaf, [row], counts) — the witnesses' verdict on every printed line of one leaf."""
    try:
        pg = load_page(leaf)
        if pg['section'] not in ('main', 'supplement'):
            return leaf, [], {}
        rows, n = [], dict(lines=0, verdict=0, agree=0, start=0, cont=0, differs=0)
        for side in 'ab':
            V = {w: verdicts(pg, side, w) for w in WITNESSES}
            for c in pg['columns']:
                if c['side'] != side:
                    continue
                for p in c['paragraphs']:
                    for j, ln in enumerate(p['lines']):
                        n['lines'] += 1
                        vs = [V[w].get(ln['base']) for w in WITNESSES]
                        if any(v is None for v in vs):
                            continue
                        n['verdict'] += 1
                        if vs[0][0] != vs[1][0]:
                            continue
                        n['agree'] += 1
                        flush = vs[0][0]
                        n['start' if flush else 'cont'] += 1
                        if flush != (j == 0 and p['hanging']):
                            n['differs'] += 1
                        rows.append([leaf, side, ln['base'], 'start' if flush else 'continue'])
        return leaf, rows, n
    except Exception as e:                       # noqa: BLE001 — one bad page must not stop the run
        return leaf, [], dict(error=1, msg=f'leaf {leaf}: {type(e).__name__}: {e}')


def load_seg():
    """-> {(leaf, side, base): verdict} from segmentation.tsv, or {} when it is not there."""
    if not SEG.exists():
        return {}
    out = {}
    with SEG.open(encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
            if r['verdict'] in ('start', 'continue'):
                out[(int(r['leaf']), r['side'], int(r['base']))] = r['verdict']
    return out


def cmd_show(leaf, side):
    pg = load_page(leaf)
    V = {w: verdicts(pg, side, w) for w in WITNESSES}
    print(f'leaf {leaf} side {side} — p. {pg["printed_page"]}, {pg["section"]}')
    print(f'{"A":>4} {"C":>2} {"D":>2}  {"base":>6}  text')
    for c in pg['columns']:
        if c['side'] != side:
            continue
        for p in c['paragraphs']:
            for j, ln in enumerate(p['lines']):
                mark = ('S' if p['hanging'] else 'c') if j == 0 else '.'
                g = 'g' if p.get('guessed') and j == 0 else ' '
                v = [V[w].get(ln['base']) for w in WITNESSES]
                s = ' '.join('-' if x is None else ('F' if x[0] else '.') for x in v)
                print(f'{mark}{g}{ln["ind"]:>2} {s}  {ln["base"]:>6}  {ln["text"][:62]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pages', help='leaves, e.g. 45,517-520 (default: all)')
    ap.add_argument('--check', action='store_true', help='summary only, write nothing')
    ap.add_argument('--show', nargs=2, metavar=('LEAF', 'SIDE'), help='every line of one column side')
    ap.add_argument('--workers', type=int, default=8, help='parallel workers (the machine has more '
                    'cores than this on most laptops: --workers 14 is roughly 40 %% faster)')
    a = ap.parse_args()
    if a.show:
        return cmd_show(int(a.show[0]), a.show[1])
    leaves = sorted(int(p.stem) for p in OCR.glob('*.json'))
    if a.pages:
        want = set()
        for part in a.pages.split(','):
            lo, _, hi = part.partition('-')
            want.update(range(int(lo), int(hi or lo) + 1))
        leaves = [l for l in leaves if l in want]
    rows, tot, errors = [], dict(lines=0, verdict=0, agree=0, start=0, cont=0, differs=0), []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for _, rr, n in ex.map(check, leaves, chunksize=4):
            rows += rr
            if n.get('error'):
                errors.append(n['msg'])
                continue
            for k, v in n.items():
                tot[k] = tot.get(k, 0) + v
    print(f"{tot['lines']:,} printed lines; {tot['verdict']:,} carried over to both witnesses "
          f"({tot['verdict'] / max(1, tot['lines']):.1%}), {tot['agree']:,} with C and D agreeing "
          f"({tot['agree'] / max(1, tot['verdict']):.1%} of those)")
    print(f"the witnesses read {tot['start']:,} of those lines as the start of an entry and {tot['cont']:,} as "
          f"the continuation of one; {tot['differs']:,} differ from the segmentation now in ocr/*.json "
          f"(0 once dj_abbyy.py has applied the file)")
    for m in errors:
        print(f'  ERROR {m}')
    if a.check:
        return
    keep = set(leaves)
    old = []
    if SEG.exists():
        with SEG.open(encoding='utf-8') as f:
            old = [line.rstrip('\n').split('\t') for line in f]
        old = [r for r in old if r and r[0] != 'leaf' and int(r[0]) not in keep]
    out = old + [[str(v) for v in r] for r in rows]
    with SEG.open('w', encoding='utf-8') as f:
        f.write('\t'.join(COLUMNS) + '\n')
        for r in sorted(out, key=lambda r: (int(r[0]), r[1], int(r[2]))):
            f.write('\t'.join(r) + '\n')
    print(f'wrote {SEG.relative_to(DJ.parent)}: {len(out):,} rows, '
          f'{SEG.stat().st_size // 1024:,} KB')


if __name__ == '__main__':
    main()
