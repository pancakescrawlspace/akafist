#!/usr/bin/env python3
"""Phase 2 of djachenko/PLAN.md: score OCR candidates against the hand-made ground truth in djachenko/eval/gt/.

    python3 tools/dj_eval.py                  # extract all candidates, score them, write eval/results.tsv + print
    python3 tools/dj_eval.py --show google_D 660     # aligned differences for one candidate and one GT leaf
    python3 tools/dj_eval.py --show abbyy_A 660 --zone hw
    python3 tools/dj_eval.py --heads           # Phase 3b step 2: headwords in ocr/*.json vs the GT pages

Candidates (text per page in reading order, cached in djachenko/eval/cand/<name>/NNNN.txt, NNNN = leaf of scan A):
    abbyy_A    archive.org's ABBYY layer of scan A, in the reading order of ocr/NNNN.json (Phase 3a)
    djvu_B     the hidden text layer of the 1993 reprint's DjVu (witness B; the uploader's FineReader OCR)
    google_D   Google's text layer of the Cornell PDF (witness D)
    google_C   Google's text layer of the Indiana PDFs (witness C)
    merged     the D/B/A vote written into ocr/NNNN.json by dj_heads.py (Phase 3b step 1); text_d = D cut at A's
               paragraphs, before the vote. Run `dj_eval.py --only merged,text_d --refresh` after dj_heads.py.
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
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import DJ, OCR, align, join_lines, normalise, page_text  # noqa: E402

EVAL = DJ / 'eval'
GT_DIR, CAND_DIR = EVAL / 'gt', EVAL / 'cand'


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


def cand_witness(name):
    def f(leaf):
        return page_text(name, leaf)['text'], []
    return f


def cand_json(key):
    """The witness text written into ocr/NNNN.json by dj_heads.py (Phase 3b step 1): key = text_merged or text_d.
    starts = the hanging paragraphs, so the segmentation is scored on that text too."""
    def f(leaf):
        pg = json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))
        text, starts = '', []
        for c in pg['columns']:
            for p in c['paragraphs']:
                para = (p.get(key) or '').strip()
                if not para:
                    continue
                if text:
                    text += ' '
                if p['hanging']:
                    starts.append((len(text), bool(p.get('guessed'))))
                text += para
        return text, starts
    return f


CANDIDATES = {'abbyy_A': cand_abbyy_A, 'djvu_B': cand_witness('B'), 'google_D': cand_witness('D'),
              'google_C': cand_witness('C'), 'merged': cand_json('text_merged'), 'text_d': cand_json('text_d')}


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


def gt_headword_list(leaf):
    """The headwords of a GT page in order: the first {…} of every entry line (‹› removed), else the text before
    the first = — ( ."""
    out = []
    for line in (GT_DIR / f'{leaf:04d}.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith(('#', '@', '+')):
            continue
        line = line.replace('[?]', '')
        if line.startswith('{'):
            hw = line[1:line.index('}')]
        else:
            hw = re.split(r'=|—|–|\s-\s|\(', line)[0]
        out.append(hw.replace('‹', '').replace('›', '').strip())
    return out


def heads(level='norm'):
    """Score the headwords of Phase 3b step 2 (entries_hint[].headword in ocr/*.json) against the GT pages: the two
    headword lists are aligned (a false or missed entry start shifts them), a GT headword counts as right when the
    reading aligned with it is identical at `level`."""
    def n(s):
        return ''.join(c for c, _ in normalise([(ch, None) for ch in s], level))
    tot = dict(gt=0, right=0, read=0, null=0, missing=0)
    for leaf in gt_leaves():
        pg = json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))
        hints = [h for h in pg['entries_hint'] if h.get('headword_source')]
        if not hints:
            continue
        gt = gt_headword_list(leaf)
        cand = [h['headword'] for h in hints if h['headword'] is not None]
        a, b = [n(x) for x in gt], [n(x) for x in cand]
        _, cost_at, j_at = align(a, b)
        right = sum(1 for c in cost_at if c == 0)
        wrong = [(gt[i], cand[j_at[i]] if j_at[i] < len(cand) else '—') for i, c in enumerate(cost_at) if c]
        print(f'leaf {leaf}: {right}/{len(gt)} GT headwords read exactly ({level}); {len(hints)} candidates, '
              f'{len(hints) - len(cand)} answered null; wrong: {wrong}')
        tot['gt'] += len(gt)
        tot['right'] += right
        tot['read'] += len(hints)
        tot['null'] += len(hints) - len(cand)
    if tot['gt']:
        print(f'all: {tot["right"]}/{tot["gt"]} = {tot["right"] / tot["gt"]:.1%} exact ({level}); '
              f'{tot["read"]} candidates read, {tot["null"]} null')
    else:
        print('no GT page has step-2 headwords yet (dj_heads.py read/enter)')


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
    ap.add_argument('--heads', action='store_true', help='score the step-2 headwords (dj_heads.py) on the GT pages')
    a = ap.parse_args()
    if a.heads:
        heads(a.level)
        return
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
    for name in names:
        seg = [r for r in rows if r['cand'] == name and r['level'] == 'norm' and 'seg_gt' in r]
        if not seg:
            continue
        print(f'\nentry segmentation ({name}: hanging paragraphs of ocr/*.json on that text):')
        for r in seg:
            print(f'  leaf {r["leaf"]}: GT entries {r["seg_gt"]}, found {r["seg_found"]} '
                  f'(recall {pct(r["seg_found"], r["seg_gt"])}); candidate starts {r["seg_cand"]}, correct '
                  f'{r["seg_good"]} (precision {pct(r["seg_good"], r["seg_cand"])}); guessed {r["seg_guessed"]}')
        T = {k: sum(r[k] for r in seg) for k in ('seg_gt', 'seg_found', 'seg_cand', 'seg_good')}
        print(f'  all: recall {pct(T["seg_found"], T["seg_gt"])}, precision {pct(T["seg_good"], T["seg_cand"])}')


if __name__ == '__main__':
    main()
