#!/usr/bin/env python3
"""Phase 4 of djachenko/PLAN.md: ocr/*.json -> djachenko/entries.tsv, with a validation report (FLAGS.md).

    python3 tools/dj_parse.py            # write entries.tsv and FLAGS.md, print the summary
    python3 tools/dj_parse.py --check    # the summary only, nothing written

Deterministic; re-run after every batch of dj_heads.py (step 1 texts, step 2 headwords).

Entries. An entry starts at every hanging paragraph of a main/supplement page (Phase 3a geometry), unless the
headword reading of step 2 says the line is not an entry start (null) — then the paragraph continues the previous
entry, as does every non-hanging paragraph (the first of a column or page). The entry's text is the paragraphs'
`text_merged` (Phase 3b step 1: witness D voted with B, A, C), joined; a hyphen at a paragraph end joins the word.
The text is split at the first separator (=, —, –, " - " or "(") within its first 80 characters: before it D's
reading of the head, after it the definition. The headword is the step-2 reading when there is one
(`entries_hint[].headword`, source vision/manual), else D's head text is used provisionally and the entry is flagged
`hw_provisional`.

Columns of entries.tsv (tab-separated, UTF-8, one entry per line):
    id             leaf-column-paragraph of the entry's first paragraph, e.g. 0341-1-02 (stable across runs)
    part           main | supplement (two alphabetical sequences)
    page           printed page of the entry's start;  col  a | b
    headword       as printed (Church Slavonic letters, no diacritics — eval/README.md), from step 2 or provisional
    headword_civil civil pre-reform form (Phase 0.2): ѡ ѻ→о, ѿ→от, ꙋ ѹ оу→у, ѕ ꙁ→з, є ѥ→е, ї→і, ѧ ꙗ ѩ→я, ѫ→у, ѭ→ю,
                   ѯ→кс, ѱ→пс; ѣ ѳ ѵ і ъ ь stay
    headword_key   modern lookup key: lowercase civil with ѣ→е, і→и, ѳ→ф, ѵ→и (в after а/е), final ъ dropped
    hw_source      vision | manual | D (provisional)
    sep            the separator found: = — ( (all dashes written —) or empty
    gram           the tag right after the separator: a parenthesised group "(греч. …)" or an abbreviation "гл."
    definition     the text after the separator (all of it; the gram tag is not removed)
    disputed       spans "start-end;…" in `definition` where witnesses D and B disagree (from step 1)
    status         raw (Phase 5 sets checked)
    flags          ;-separated: hw_provisional, hw_disputed (step 2 reading confirmed by no witness), hw_missing,
                   guessed (entry start decided from text features, cut-margin page), no_sep (no separator found),
                   eq_from_A (D dropped the "=" A saw; the head cut after as many words as ABBYY read), empty,
                   joined_null (a hanging paragraph that step 2 called "not an entry" was joined to this entry),
                   no_eq (A saw no "=" in the first two lines), order (headword out of alphabetical order: not in
                   the longest non-decreasing subsequence of its part), parens (unbalanced parentheses in the
                   definition), odd_len (D's text much shorter/longer than A's for a paragraph of the entry)

FLAGS.md: counts per flag and the entries flagged order/parens/no_sep. (A check of pages with an unusual number
of entries was tried and dropped: a page of 81 short Въз- entries and a page of one long article are both normal.)
"""
import argparse, bisect, csv, json, re, sys, unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import DJ, LOOKALIKE, OCR, join_lines  # noqa: E402

ENTRIES = DJ / 'entries.tsv'
FLAGS = DJ / 'FLAGS.md'
COLUMNS = ['id', 'part', 'page', 'col', 'headword', 'headword_civil', 'headword_key', 'hw_source', 'sep', 'gram',
           'definition', 'disputed', 'status', 'flags']

# the book's letter order (from its table of contents; ѕ and ѡ have no sections of their own)
COLLATION = 'абвгдежзиіклмнопрстуфхцчшщъыьѣэюяѥѫѩѭѯѱѳѵ'
RANK = {c: i for i, c in enumerate(COLLATION)}

CS_TO_CIVIL = {'ѡ': 'о', 'Ѡ': 'О', 'ѻ': 'о', 'Ѻ': 'О', 'ꙩ': 'о', 'ѿ': 'от', 'Ѿ': 'От', 'ꙋ': 'у', 'Ꙋ': 'У', 'ѹ': 'у',
               'Ѹ': 'У', 'ѕ': 'з', 'Ѕ': 'З', 'ꙁ': 'з', 'Ꙁ': 'З', 'є': 'е', 'Є': 'Е', 'ѥ': 'е', 'Ѥ': 'Е', 'ї': 'і',
               'Ї': 'І', 'ѧ': 'я', 'Ѧ': 'Я', 'ꙗ': 'я', 'Ꙗ': 'Я', 'ѩ': 'я', 'Ѩ': 'Я', 'ѫ': 'у', 'Ѫ': 'У', 'ѭ': 'ю',
               'Ѭ': 'Ю', 'ѯ': 'кс', 'Ѯ': 'Кс', 'ѱ': 'пс', 'Ѱ': 'Пс', 'ꙑ': 'ы', 'ѷ': 'ѵ', 'ү': 'у', 'Ү': 'У'}
# the separator after the head: =, dashes, "(", and D's glued forms "Слово-см.", "Слово-греч.", "Слово.-Первыя"
ABBR = r'(?:греч|евр|лат|нѣм|санскр|перс|араб|тур|польск|др\.?-рус|ст\.?-слав|древ\.?-слав|церк\.?-слав|прил|сущ|гл|' \
       r'нар|нарѣч|мѣст|предл|союз|межд|прич|дѣепр|им|соб|см)'
SEP_RE = re.compile(r'=|—|–|--|\s-\s|\(|(?<=\S)-(?=\s*' + ABBR + r'\.)|(?<=\.)\s?-(?=\s?\S)')
GRAM_RE = re.compile(r'^(?:\((?P<par>[^()]{1,60})\)|(?P<abbr>' + ABBR + r'\.))')
SENSE_RE = re.compile(r'(?:^|(?<=[\s=—;:,.]))(?:\d{1,2}|[а-я])$')      # "1)", "а)" — a sense number before ")"


# ---------------------------------------------------------------- headword forms

def civil(hw):
    """Church Slavonic letters as printed -> civil pre-reform script; diacritics dropped; spaces normalised."""
    s = unicodedata.normalize('NFD', hw)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = ''.join(CS_TO_CIVIL.get(c, c) for c in s)
    s = ''.join(LOOKALIKE.get(c, c) for c in s)                              # Latin a, c, e, o, p … from OCR
    s = re.sub(r'[Оо]у', lambda m: 'У' if m.group(0)[0] == 'О' else 'у', s)   # оу -> у
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s)).strip()


def modern_key(hw_civil):
    s = hw_civil.lower()
    s = re.sub(r'(?<=[ае])ѵ', 'в', s)
    s = s.translate(str.maketrans({'ѣ': 'е', 'і': 'и', 'ѳ': 'ф', 'ѵ': 'и'}))
    s = re.sub(r'ъ(?=$|[\s\-,;])', '', s)
    s = re.sub(r'[^\w\s\-]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def sort_key(hw_civil):
    """Ranks of the letters in the book's order (other characters ignored; letters the book has no section for,
    e.g. Latin, sort last)."""
    return tuple(RANK.get(c, len(COLLATION)) for c in hw_civil.lower() if c.isalpha())


# ---------------------------------------------------------------- assembly

def pages():
    out = []
    for f in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] in ('main', 'supplement'):
            out.append(pg)
    return out


def para_text(p):
    t = p.get('text_merged')
    if t is None:
        t = join_lines(ln['text'] for ln in p['lines']).replace('￼', '')
    return t.strip()


def tidy(text, spans):
    """Remove the OCR's spaces before . , ; : ) and after (, and double spaces; the spans follow the text."""
    out, new_at, i = [], [0] * (len(text) + 1), 0
    while i < len(text):
        new_at[i] = len(out)
        ch = text[i]
        if ch == ' ' and (i + 1 < len(text) and text[i + 1] in '.,;:)' or (out and out[-1] in '( ') or i + 1 == len(text)):
            i += 1
            continue
        out.append(ch)
        i += 1
    new_at[len(text)] = len(out)
    return ''.join(out), [[new_at[a], max(new_at[a], new_at[b])] for a, b in spans]


def append_text(entry, text, disputed):
    """Join a paragraph's text to the entry; disputed spans are shifted into the entry's coordinates."""
    if not text:
        return
    base = entry['text']
    if base and base.endswith(('-', '¬')) and not base.endswith(' -'):
        base = base[:-1]
        off = len(base)
    elif base:
        base += ' '
        off = len(base)
    else:
        off = 0
    entry['text'] = base + text
    entry['spans'].extend([s + off, e + off] for s, e in disputed)


def build_entries(pgs):
    entries, cur = [], None
    for pg in pgs:
        hints = {(h['col'], h['para']): h for h in pg['entries_hint']}
        odd = {(pg['columns'][c]['n'], p + 1) for c, p, _ in pg.get('witness', {}).get('odd', [])}
        for col in pg['columns']:
            for pi, p in enumerate(col['paragraphs'], 1):
                h = hints.get((col['n'], pi))
                read = bool(h and h.get('headword_source'))
                start = p['hanging'] and not (read and h['headword'] is None)
                if start or cur is None:
                    cur = dict(id=f"{pg['idx']:04d}-{col['n']}-{pi:02d}", part=pg['section'],
                               page=pg['printed_page'], col=col['side'], text='', spans=[], hint=h, flags=set(),
                               leaf=pg['idx'])
                    if p.get('guessed'):
                        cur['flags'].add('guessed')
                    if h and not h['eq']:
                        cur['flags'].add('no_eq')
                    entries.append(cur)
                elif read and h['headword'] is None:
                    cur['flags'].add('joined_null')
                if (col['n'], pi) in odd:
                    cur['flags'].add('odd_len')
                append_text(cur, para_text(p), p.get('disputed') or [])
    return entries


def paren_balance(text):
    """(unclosed '(', stray ')') — a ')' at depth 0 right after a sense number "1)" or "а)" does not count."""
    depth = stray = 0
    for m in re.finditer(r'[()]', text):
        if m.group() == '(':
            depth += 1
        elif depth:
            depth -= 1
        elif not SENSE_RE.search(text[:m.start()]):
            stray += 1
    return depth, stray


def split_entry(e):
    """Head text / separator / definition; the headword from step 2 or provisionally from D's head text."""
    e['text'], e['spans'] = tidy(e['text'], e['spans'])
    text = e['text']
    h = e['hint']
    m = SEP_RE.search(text, 0, min(len(text), 80))
    if m:
        head, sep, rest = text[:m.start()], m.group(0).strip(), text[m.end():]
        if sep == '(':
            rest = '(' + rest
        cut = m.start() if sep == '(' else m.end()
    elif h and h['eq'] and h['abbyy']:
        # D dropped the "=" that A saw: the head has as many words as ABBYY's reading of it
        n = min(4, max(1, len(h['abbyy'].split())))
        words = text.split(' ', n)
        head, rest = ' '.join(words[:n]), (words[n] if len(words) > n else '')
        sep, cut = '', len(head)
        e['flags'].add('eq_from_A')
    else:
        head, sep, rest, cut = '', '', text, 0
        e['flags'].add('no_sep')
    if not text:
        e['flags'].add('empty')
    e['sep'] = '—' if sep in ('—', '–', '--', '-') else sep
    e['definition'] = rest.strip()
    lead = len(rest) - len(rest.lstrip())
    d0 = cut + lead
    e['disputed'] = ';'.join(f'{max(s, d0) - d0}-{e_ - d0}' for s, e_ in e['spans'] if e_ > d0 and s < len(text))
    if h and h.get('headword_source'):
        e['headword'] = h['headword'] or ''
        e['hw_source'] = 'manual' if h['headword_source'] == 'manual' else 'vision'
        if h.get('check') == 'disputed':
            e['flags'].add('hw_disputed')
    else:
        e['headword'] = re.sub(r'^[\W_]+|[\s,;:.\-–—]+$', '', head).strip()
        e['hw_source'] = 'D'
        e['flags'].add('hw_provisional')
    if not e['headword']:
        e['flags'].add('hw_missing')
    e['headword_civil'] = civil(e['headword'])
    e['headword_key'] = modern_key(e['headword_civil'])
    g = GRAM_RE.match(e['definition'])
    e['gram'] = (('(' + g.group('par') + ')') if g and g.group('par') else g.group('abbr')) if g else ''
    if any(paren_balance(e['definition'])):
        e['flags'].add('parens')


# ---------------------------------------------------------------- validation

def lis_flags(entries):
    """Entries whose headword is not in the longest non-decreasing subsequence of sort keys (per part)."""
    for part in ('main', 'supplement'):
        idx = [i for i, e in enumerate(entries) if e['part'] == part and e['headword']]
        keys = [entries[i]['headword_civil'] and sort_key(entries[i]['headword_civil']) for i in idx]
        # patience sorting, non-decreasing (bisect_right)
        tails, tails_idx, prev = [], [], [-1] * len(keys)
        for k, key in enumerate(keys):
            j = bisect.bisect_right(tails, key)
            if j == len(tails):
                tails.append(key)
                tails_idx.append(k)
            else:
                tails[j] = key
                tails_idx[j] = k
            prev[k] = tails_idx[j - 1] if j else -1
        keep = set()
        k = tails_idx[-1] if tails_idx else -1
        while k >= 0:
            keep.add(k)
            k = prev[k]
        for k, i in enumerate(idx):
            if k not in keep:
                entries[i]['flags'].add('order')


# ---------------------------------------------------------------- output

def write_tsv(entries):
    tmp = ENTRIES.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(COLUMNS) + '\n')
        for e in entries:
            row = dict(e, status='raw', flags=';'.join(sorted(e['flags'])))
            f.write('\t'.join(str(row[c]).replace('\t', ' ') for c in COLUMNS) + '\n')
    tmp.rename(ENTRIES)


def report(entries, write):
    n = len(entries)
    flag_counts = Counter(f for e in entries for f in e['flags'])
    src = Counter(e['hw_source'] for e in entries)
    parts = Counter(e['part'] for e in entries)
    lines = [f'# Validation report of dj_parse.py', '',
             f'{n} entries ({parts["main"]} main, {parts["supplement"]} supplement); headword source: '
             + ', '.join(f'{k} {v}' for k, v in sorted(src.items())) + '.', '',
             '| flag | entries |', '|---|---:|']
    lines += [f'| {k} | {v} |' for k, v in sorted(flag_counts.items(), key=lambda kv: -kv[1])]
    read = [e for e in entries if e['hw_source'] != 'D']
    if read:
        lines += ['', f'Entries with a step-2 headword: {len(read)}; of them out of order: '
                      f'{sum("order" in e["flags"] for e in read)}, hw_disputed: '
                      f'{sum("hw_disputed" in e["flags"] for e in read)}.']
    for flag in ('no_sep', 'parens', 'order'):
        sel = [e for e in entries if flag in e['flags'] and (flag != 'order' or e['hw_source'] != 'D')]
        title = f'## {flag} ({len(sel)}' + (', step-2 headwords only' if flag == 'order' else '') + ')'
        lines += ['', title, '']
        lines += [f"- `{e['id']}` p. {e['page']}{e['col']} **{e['headword']}** {e['sep']} "
                  f"{e['definition'][:70]}{'…' if len(e['definition']) > 70 else ''}" for e in sel[:300]]
        if len(sel) > 300:
            lines.append(f'- … and {len(sel) - 300} more (see entries.tsv)')
    text = '\n'.join(lines) + '\n'
    if write:
        FLAGS.write_text(text, encoding='utf-8')
    print('\n'.join(lines[:8 + len(flag_counts)]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--check', action='store_true', help='report only, write nothing')
    a = ap.parse_args()
    entries = build_entries(pages())
    for e in entries:
        split_entry(e)
    lis_flags(entries)
    if not a.check:
        write_tsv(entries)
    report(entries, not a.check)
    if not a.check:
        print(f'written: {ENTRIES.relative_to(DJ.parent)} ({ENTRIES.stat().st_size // 1024} KB), '
              f'{FLAGS.relative_to(DJ.parent)}')


if __name__ == '__main__':
    main()
