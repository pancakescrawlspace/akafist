#!/usr/bin/env python3
"""Дьяченко's own errata table applied to the entries (Phase 4).

    python3 tools/dj_errata.py report            # what locates, what matches, what does not — no writing
    python3 tools/dj_errata.py report --show     # with the text round every failure

`djachenko/errata.tsv` (transcribed from leaves 32–36, see PROGRESS.md) names a place in the book — printed page,
column (лѣвый/правый) and line counted from the top or the bottom — and gives напечатано → слѣдуетъ читать.
`dj_parse.py` imports `for_page()` and `apply_to()` from here and applies the rows while it builds entries.tsv,
so the corrections survive a regeneration; a corrected entry is flagged `errata`.

Locating a row: the page's columns of that side, in reading order, give the printed lines; line N from the top is
the Nth of them, N from the bottom the Nth from the end; the paragraph holding that line is the entry to correct.
The line count is the book's own, so it can be off by one against A's line segmentation — which is why the string
decides in the end: the row is applied where `printed` is found, first exactly, then at the "norm" level of
dj_witness (look-alikes folded, diacritics dropped), searching the entry named by the line and then its
neighbours. A row whose string is nowhere in reach is reported, never guessed at.

Rows not applied: the 13 that are not entry text (guide words at the head of a page, page numbers in the running
head, the two instructions — they carry a `note` saying so), and any row with a `[?]` cell, which is a reading
still to be checked. Braces {…} in the table mark Church Slavonic type and are stripped for matching.
"""
import argparse, csv, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import DJ, norm_seq  # noqa: E402

ERRATA = DJ / 'errata.tsv'
SIDES = {'лѣвый': 'a', 'правый': 'b'}
SKIP_NOTE = re.compile(r'guide word|page number|instruction|not text')


def load():
    """-> [row dicts] of errata.tsv, with `use` telling whether the row is a substitution we can apply."""
    rows = list(csv.DictReader(open(ERRATA, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    for r in rows:
        doubtful = '[?]' in r['printed'] + r['read']
        structural = bool(SKIP_NOTE.search(r['note'] or ''))
        r['printed_s'] = strip(r['printed'])
        r['read_s'] = strip(r['read'])
        r['use'] = not doubtful and not structural and bool(r['printed_s']) and r['page'].isdigit() \
            and r['col'] in SIDES and bool(r['line'])
        r['why'] = 'doubtful' if doubtful else 'not entry text' if structural else '' if r['use'] else 'no locator'
    return rows


def strip(s):
    """The table's braces mark Church Slavonic type; the text of entries.tsv has none."""
    return s.replace('{', '').replace('}', '').strip()


def for_page(rows, printed_page):
    return [r for r in rows if r['use'] and r['page'] == str(printed_page)]


def lines_of_side(pg, side):
    """Every printed line of one column side of a page, in reading order, with the paragraph it belongs to:
    [(col_n, para_index, line)]."""
    out = []
    for col in sorted((c for c in pg['columns'] if c['side'] == side), key=lambda c: c['band']):
        for pi, p in enumerate(col['paragraphs'], 1):
            for ln in p['lines']:
                out.append((col['n'], pi, ln))
    return out


def target_paragraph(pg, row):
    """-> (col_n, para_index) the row points at, or None."""
    side = SIDES.get(row['col'])
    lines = lines_of_side(pg, side) if side else []
    if not lines:
        return None
    m = re.match(r'(\d+)', row['line'])
    if not m:
        return None
    n = int(m.group(1))
    i = n - 1 if row['where'] == 'сверху' else len(lines) - n
    i = max(0, min(len(lines) - 1, i))
    return lines[i][0], lines[i][1]


def fold(text, letters_only=False):
    """-> (folded string, index of each folded character in `text`). The norm level of dj_witness (look-alikes to
    Cyrillic, diacritics dropped, whitespace dropped); with letters_only also without punctuation, because the OCR
    drops and adds full stops of its own ("Панд . Акт" for "Панд. Акт.")."""
    seq, idx = norm_seq(text)
    if letters_only:
        keep = [(c, i) for c, i in zip(seq, idx) if c.isalnum()]
        return ''.join(c for c, _ in keep), [i for _, i in keep]
    return ''.join(seq), idx


def find(text, needle):
    """(start, end) of `needle` in `text`: exactly, else folded, else folded to letters and digits alone.
    None if it is not there."""
    i = text.find(needle)
    if i >= 0:
        return i, i + len(needle)
    for letters_only in (False, True):
        a, a_idx = fold(text, letters_only)
        b, _ = fold(needle, letters_only)
        if not b or len(b) > len(a):
            continue
        j = a.find(b)
        if j >= 0:
            return a_idx[j], a_idx[j + len(b) - 1] + 1
    return None


def locate(pg, row):
    """-> (col_n, para index) to correct: the paragraph the line names if the printed string is in it, else the
    one paragraph of the page that holds the string, else the line's paragraph (so the miss is reported against
    the right entry), else None."""
    t = target_paragraph(pg, row)
    paras = [(c['n'], i, p.get('text_merged') or '')
             for c in pg['columns'] for i, p in enumerate(c['paragraphs'], 1)]
    if t:
        text = next((x for n_, i, x in paras if (n_, i) == t), '')
        if find(text, row['printed_s']):
            return t
    hits = [(n_, i) for n_, i, x in paras if find(x, row['printed_s'])]
    if len(hits) == 1:
        return hits[0]
    return t


def apply_to(text, rows, *span_lists):
    """Apply the rows to one entry's text. A substitution changes the length, so the caller's spans (the disputed
    and italic ones of entries.tsv) are moved with it: anything after the replacement shifts, anything inside it
    is clamped to its edges. -> (text, span lists, [applied rows], [rows whose string was not found])."""
    spans = [list(map(list, sl)) for sl in span_lists]
    done, missed = [], []
    for r in rows:
        span = find(text, r['printed_s'])
        if not span:
            missed.append(r)
            continue
        s, e = span
        new = r['read_s']
        delta = len(new) - (e - s)
        for sl in spans:
            for pair in sl:
                pair[0] = pair[0] if pair[0] <= s else (pair[0] + delta if pair[0] >= e else s)
                pair[1] = pair[1] if pair[1] <= s else (pair[1] + delta if pair[1] >= e else s + len(new))
        text = text[:s] + new + text[e:]
        done.append(r)
    return (text,) + tuple(spans) + (done, missed)


# ---------------------------------------------------------------- report

def cmd_report(a):
    import json
    rows = load()
    usable = [r for r in rows if r['use']]
    print(f'{len(rows)} rows: {len(usable)} to apply, '
          + ', '.join(f'{sum(1 for r in rows if r["why"] == w)} {w}'
                      for w in ('doubtful', 'not entry text', 'no locator') if any(r['why'] == w for r in rows)))
    pages = {}
    for f in sorted((DJ / 'ocr').glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] in ('main', 'supplement') and pg['printed_page']:
            pages[str(pg['printed_page'])] = pg          # printed_page is a string in ocr/*.json ('5', 'XXXIV')
    located = matched = 0
    for r in usable:
        pg = pages.get(r['page'])
        if not pg:
            print(f"  row {r['leaf']}/{r['row']}: page {r['page']} not among the OCR'd pages")
            continue
        t = target_paragraph(pg, r)
        if not t:
            print(f"  row {r['leaf']}/{r['row']}: no line for {r['page']} {r['col']} {r['line']} {r['where']}")
            continue
        located += 1
        col = next(c for c in pg['columns'] if c['n'] == t[0])
        para = col['paragraphs'][t[1] - 1]
        text = para.get('text_merged') or ''
        column = [p.get('text_merged') or '' for p in col['paragraphs']]
        page_texts = [p.get('text_merged') or '' for c in pg['columns'] for p in c['paragraphs']]
        where = ('this paragraph' if find(text, r['printed_s']) else
                 'the same column' if any(find(x, r['printed_s']) for x in column) else
                 'elsewhere on the page' if any(find(x, r['printed_s']) for x in page_texts) else None)
        if where:
            matched += 1
            if a.show:
                print(f"  ✓ {r['leaf']}/{r['row']} p.{r['page']} {r['col']} {r['line']} {r['where']}: "
                      f"{r['printed_s']!r} → {r['read_s']!r} ({where})")
        else:
            print(f"  ✗ {r['leaf']}/{r['row']} p.{r['page']} {r['col']} {r['line']} {r['where']}: "
                  f"{r['printed_s']!r} not found")
            if a.show:
                print(f"      paragraph: {text[:160]}")
    print(f'located {located}/{len(usable)}; the printed string found for {matched}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sp = sub.add_parser('report')
    sp.add_argument('--show', action='store_true')
    sp.set_defaults(fn=cmd_report)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
