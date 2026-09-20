#!/usr/bin/env python3
"""Phase 4 of djachenko/PLAN.md: ocr/*.json -> djachenko/entries.tsv, with a validation report (FLAGS.md).

    python3 tools/dj_parse.py            # write entries.tsv and FLAGS.md, print the summary
    python3 tools/dj_parse.py --check    # the summary only, nothing written

Deterministic; re-run after every batch of dj_heads.py (step 1 texts, step 2 headwords).

Entries. An entry starts at every hanging paragraph of a main/supplement page (Phase 3a geometry), unless the
headword reading of step 2 says the line is not an entry start (null) — then the paragraph continues the previous
entry, as does every non-hanging paragraph (the first of a column or page). The entry's text is the paragraphs'
`text_merged` (Phase 3b step 1: witness D voted with B, A, C), joined; a hyphen at a paragraph end joins the word.
The text is split at a separator (=, —, –, " - " or "("): with a headword read in step 2, at the first one right
after the headword's own words (else the text is cut there, flag `hw_cut`, so that head text beyond the headword —
a gloss or a quotation D ran into the head when it dropped the "=" — stays in the definition instead of being
lost); with a provisional headword, at the first separator in the first 80 characters. Before it D's reading of the
head, after it the definition. Typography is tidied (spaces before . , ; : ) and after "(" removed);
in the definition the quotation marks are attached to their quotation and written as the book prints them
(fix_quotes; djachenko/QUOTES.md): „…“, and «…» where the book has them (≈30 places, sometimes mixed «…“).
The headword is the step-2 reading when there is one (`entries_hint[].headword`, source vision/manual), else D's
head text is used provisionally and the entry is flagged `hw_provisional`.

Columns of entries.tsv (tab-separated, UTF-8, one entry per line; no quoting — read it with csv.QUOTE_NONE, the
definitions contain quotation marks):
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
    italic         spans "start-end;…" in `definition` printed in italics (sources, quotations; from ABBYY's word
                   flags on A, carried over in step 1 — incomplete: ABBYY misses part of the italics)
    status         raw (Phase 5 sets checked)
    flags          ;-separated: hw_provisional, hw_disputed (step 2 reading confirmed by no witness), hw_missing,
                   guessed (entry start decided from text features, cut-margin page), no_sep (no separator found),
                   eq_from_A (D dropped the "=" A saw; the head cut after as many words as ABBYY read), empty,
                   joined_null (a hanging paragraph that step 2 called "not an entry" was joined to this entry),
                   no_eq (A saw no "=" in the first two lines), order (headword out of alphabetical order: not in
                   the longest non-decreasing subsequence of its part), parens (unbalanced parentheses in the
                   definition), odd_len (D's text much shorter/longer than A's for a paragraph of the entry),
                   quotes (quotation marks unbalanced after fix_quotes: the OCR dropped or misplaced one, or a
                   letter was misread as « or »), hw_cut (a step-2 headword with no separator after it: the text
                   was cut after the headword's words), caps (a word mostly in capitals that is not a Roman
                   numeral) and script (a word mixing Greek and Cyrillic letters) — both are usually the Old
                   Church Slavonic citation type, which no OCR reads; they await a reading pass

FLAGS.md: counts per flag and the entries flagged order/parens/no_sep/quotes. (A check of pages with an unusual
number of entries was tried and dropped: a page of 81 short Въз- entries and a page of one long article are both
normal.)
"""
import argparse, bisect, csv, json, re, sys, unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_witness import DJ, LOOKALIKE, OCR, join_lines  # noqa: E402

ENTRIES = DJ / 'entries.tsv'
FLAGS = DJ / 'FLAGS.md'
COLUMNS = ['id', 'part', 'page', 'col', 'headword', 'headword_civil', 'headword_key', 'hw_source', 'sep', 'gram',
           'definition', 'disputed', 'italic', 'status', 'flags']

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
QUOTES = '"„“”«»'                    # double quotation marks as the OCR emits them (’ ‘ ' are left alone)
# the Old Church Slavonic citation type of the book (a heavy uncial face, e.g. p. 223 "иноѹадыи вм. єдиноѹадыи"):
# no OCR reads it — Google renders its letters as capitals or as Greek look-alikes, ABBYY as noise. Not repairable
# by rule; the entries that show it are flagged so that the reading pass and the proofreading can find them.
LETTERS = re.compile(r'[\u0370-\u03ff\u1f00-\u1fff\u0400-\u052fA-Za-z\u0300-\u036f]+')
GREEK_L = re.compile(r'[\u0370-\u03ff\u1f00-\u1fff]')
CYRIL_L = re.compile(r'[\u0400-\u052f]')
# Roman numerals, including the OCR's Cyrillic look-alikes and its ligature readings (ХП = XII, ХШ = XIII)
ROMAN_MAP = str.maketrans({'Х': 'X', 'І': 'I', 'Ѵ': 'V', 'С': 'C', 'М': 'M', 'Д': 'D', 'П': 'II', 'Ш': 'III'})
ROMAN = re.compile(r'^[IVXLCDM]+$')


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


def tidy(text, *span_lists):
    """Remove the OCR's spaces before . , ; : ) and after (, and double spaces; the span lists follow the text."""
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
    return (''.join(out),) + tuple([[new_at[a], max(new_at[a], new_at[b])] for a, b in spans] for spans in span_lists)


def quote_class(c):
    """Context of a quotation mark: S space/edge, O opening bracket, W letter/digit, P punctuation, = dash, Q quote."""
    if c is None or c.isspace():
        return 'S'
    if c in '([':
        return 'O'
    if c.isalnum():
        return 'W'
    if c in '.,;:!?)]':
        return 'P'
    if c in '=—–-':
        return '='
    return 'Q' if c in QUOTES else 'X'


def quote_roles(text, start, end):
    """Role of every quotation mark in text[start:end]: {index: 'open' | 'close' | 'keep'}, and whether the entry's
    quotes are unbalanced. „ « open and “ » ” close as printed (QUOTES.md: the book prints „…“ and, in about 30
    places, «…», also mixed); a straight " is decided by its spacing, and where it floats (spaces on both sides)
    by the next printed character (a reference "(…)" or punctuation follows a closing mark), a ":" before it, then
    the depth — closing if a quote is open. A » in an opening position with nothing open is a misread „."""
    roles, depth, bad = {}, 0, False
    for i in range(start, end):
        ch = text[i]
        if ch not in QUOTES:
            continue
        L = quote_class(text[i - 1] if i > start else None)
        R = quote_class(text[i + 1] if i + 1 < len(text) else None)
        if L == 'O' and R == 'P' or L == R == 'W' and ch != '"' or 'X' in (L, R):
            roles[i] = 'keep'                         # "(")" names the sign itself; „ » inside a word is noise
            bad = bad or L != 'O'
            continue
        if ch in '„«':
            role = 'open'
        elif ch == '»' and L in 'SO' and R == 'W' and depth == 0:
            role = 'open'
        elif ch in '“»”':
            role = 'close'
        elif L in 'WP' and R in 'P=SQO' or R in 'P=':
            role = 'close'
        elif R == 'W' and L != 'W':
            role = 'open'
        else:                                         # floating: the next/previous printed character, then depth
            nxt, prv = text[i + 1:].lstrip()[:1], text[start:i].rstrip()[-1:]
            if nxt and nxt in '(.,;:)=—–-':
                role = 'close'                        # „… " (Источникъ)  —  a source reference follows
            elif prv == ':' and nxt.isalnum():
                role = 'open'                         # говоритъ: " слово…
            else:
                role = 'close' if depth else 'open'
        if role == 'open':
            depth += 1
        elif depth:
            depth -= 1
        else:
            bad = True                                # a closing quote with nothing open
        roles[i] = role
    return roles, bad or depth != 0


def fix_quotes(text, start, end, *span_lists):
    """Attach the quotation marks of text[start:end] to their quotation and write them as the book does: an opening
    " → „, a closing " or ” → “, a misread opening » → „ (« » kept). Spaces go after an opening and before a
    closing mark; one is added before an opening mark that follows a word or punctuation, and after a closing mark
    that a word, "(" or an opening mark follows. Returns the text, the span lists remapped, and the unbalanced flag."""
    roles, bad = quote_roles(text, start, end)
    drop = set()
    for q, role in roles.items():
        step = 1 if role == 'open' else -1 if role == 'close' else 0
        j = q + step
        while step and start <= j < end and text[j] == ' ':
            drop.add(j)
            j += step
    out, new_at = [], [0] * (len(text) + 1)
    for i, ch in enumerate(text):
        role = roles.get(i)
        if role == 'open' and i > start and out and quote_class(out[-1]) in 'WPQ' and out[-1] not in '„«':
            out.append(' ')
        new_at[i] = len(out)
        if i in drop:
            continue
        if role == 'open':
            ch = '„' if ch in '"»' else ch
        elif role == 'close':
            ch = '“' if ch in '"”' else ch
        out.append(ch)
        if role == 'close' and i + 1 < len(text) and (text[i + 1].isalnum() or text[i + 1] == '('
                                                      or roles.get(i + 1) == 'open'):
            out.append(' ')
    new_at[len(text)] = len(out)
    return (''.join(out),) + tuple([[new_at[a], max(new_at[a], new_at[b])] for a, b in spans]
                                   for spans in span_lists) + (bad,)


def append_text(entry, text, disputed, italic):
    """Join a paragraph's text to the entry; the spans are shifted into the entry's coordinates."""
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
    entry['ispans'].extend([s + off, e + off] for s, e in italic)


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
                               page=pg['printed_page'], col=col['side'], text='', spans=[], ispans=[], hint=h,
                               flags=set(), leaf=pg['idx'])
                    if p.get('guessed'):
                        cur['flags'].add('guessed')
                    if h and not h['eq']:
                        cur['flags'].add('no_eq')
                    entries.append(cur)
                elif read and h['headword'] is None:
                    cur['flags'].add('joined_null')
                if (col['n'], pi) in odd:
                    cur['flags'].add('odd_len')
                append_text(cur, para_text(p), p.get('disputed') or [], p.get('italic') or [])
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


def word_bounds(text, k):
    """(start, end) of the k-th word of `text` (single spaces after tidy; k clamped to the words there are)."""
    parts = text.split(' ')
    k = max(1, min(k, len(parts)))
    return len(' '.join(parts[:k - 1])) + (1 if k > 1 else 0), len(' '.join(parts[:k]))


def split_entry(e):
    """Head text / separator / definition; the headword from step 2 or provisionally from D's head text."""
    e['text'], e['spans'], e['ispans'] = tidy(e['text'], e['spans'], e['ispans'])
    text = e['text']
    h = e['hint']
    # where to look for the separator: right after a headword read in step 2, else in the first 80 characters
    hw_read = (h.get('headword') or '') if h and h.get('headword_source') else ''
    if hw_read:
        lo, hi = word_bounds(text, len(hw_read.split()))
        window = (lo, min(len(text), hi + 3))
    else:
        window = (0, min(len(text), 80))
    m = SEP_RE.search(text, *window)
    # the head ends at hend, the definition starts at cut
    if m:
        sep = m.group(0).strip()
        hend, cut = m.start(), (m.start() if sep == '(' else m.end())
    elif hw_read:
        # a step-2 headword with no separator next to it (D merged words, or dropped the "=" and the next "(" is
        # far away): cut after the headword's words, so that the head text beyond it stays in the definition
        hend = word_bounds(text, len(hw_read.split()))[1]
        mm = re.match(r'\s*(=|—|–|--|-)\s*', text[hend:])
        sep, cut = (mm.group(1) if mm else ''), hend + (mm.end() if mm else 0)
        e['flags'].add('hw_cut')
    elif h and h['eq'] and h['abbyy']:
        # D dropped the "=" that A saw: the head has as many words as ABBYY's reading of it
        n = min(4, max(1, len(h['abbyy'].split())))
        words = text.split(' ', n)
        sep, hend = '', len(' '.join(words[:n]))
        cut = hend + (1 if len(words) > n else 0)
        e['flags'].add('eq_from_A')
    else:
        sep, hend, cut = '', 0, 0
        e['flags'].add('no_sep')
    # quotation marks: the definition, then D's head text on its own (its quotes are often noise, so they must not
    # upset the definition's pairing); the flag is the definition's
    text, e['spans'], e['ispans'], unbalanced = fix_quotes(text, cut, len(text), e['spans'], e['ispans'])
    text, e['spans'], e['ispans'], [[hend, cut]], _ = fix_quotes(text, 0, hend, e['spans'], e['ispans'], [[hend, cut]])
    e['text'], head, rest = text, text[:hend], text[cut:]
    if unbalanced:
        e['flags'].add('quotes')
    if not text:
        e['flags'].add('empty')
    e['sep'] = '—' if sep in ('—', '–', '--', '-') else sep
    e['definition'] = rest.strip()
    lead = len(rest) - len(rest.lstrip())
    d0 = cut + lead
    e['disputed'] = ';'.join(f'{max(s, d0) - d0}-{e_ - d0}' for s, e_ in e['spans'] if e_ > d0 and s < len(text))
    e['italic'] = ';'.join(f'{max(s, d0) - d0}-{e_ - d0}' for s, e_ in e['ispans'] if e_ > d0 and s < len(text))
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
    for m in LETTERS.finditer(e['definition']):
        w = ''.join(c for c in unicodedata.normalize('NFD', m.group(0)) if not unicodedata.combining(c))
        letters = [c for c in w if c.isalpha()]
        if len(letters) < 2:
            continue
        up = sum(c.isupper() for c in letters)
        if up >= 2 and up >= 0.7 * len(letters) and not ROMAN.match(m.group(0).translate(ROMAN_MAP)):
            e['flags'].add('caps')
        if GREEK_L.search(w) and CYRIL_L.search(w):
            e['flags'].add('script')


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
    for flag in ('no_sep', 'parens', 'quotes', 'caps', 'script', 'hw_cut', 'order'):
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
