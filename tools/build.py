#!/usr/bin/env python3
"""Build dictionary/dictionary.md, dictionary/forms-index.tsv and dictionary/dictionary.typ (+ .pdf if the
`typst` binary is available) from dictionary/dictionary.psv, and verify that every word-form in the Church Slavonic
source text is covered by exactly one entry (except for the intentional homonyms listed in HOMONYMS).

Usage: python3 tools/build.py [--paper a5|a4|...] [--no-pdf]"""
import argparse, collections, datetime, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'source' / 'akafist-kazanskaja-cs.txt'
PSV = ROOT / 'dictionary' / 'dictionary.psv'
MD = ROOT / 'dictionary' / 'dictionary.md'
IDX = ROOT / 'dictionary' / 'forms-index.tsv'
TYP = ROOT / 'dictionary' / 'dictionary.typ'
PDF = ROOT / 'dictionary' / 'dictionary.pdf'
FIELDS = ['lemma', 'pos', 'forms', 'ru', 'en', 'nl', 'notes']
HOMONYMS = {'мир', 'о'}          # forms deliberately claimed by two entries


def strip_accents(s):
    return s.replace('́', '')


def tokenize(text):
    text = re.sub(r'^#.*$|^## .*$', '', text, flags=re.M)
    text = strip_accents(text)
    return collections.Counter(w.lower() for w in re.findall(r'[А-Яа-яЁё]+', text))


def load_entries():
    entries, errors = [], []
    for ln, line in enumerate(PSV.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip() or line.startswith('#'):
            continue
        if line.endswith(' |'):
            line += ' '
        parts = [p.strip() for p in line.split(' | ')]
        if len(parts) != len(FIELDS):
            errors.append(f'line {ln}: expected {len(FIELDS)} fields, got {len(parts)}')
            continue
        entries.append(dict(zip(FIELDS, parts)))
    return entries, errors


def sort_key(lemma):
    base = strip_accents(lemma).lower()
    base = re.sub(r'\s*\(.*?\)', '', base)
    return base


def check(entries, attested):
    claimed = collections.defaultdict(list)
    for e in entries:
        for f in e['forms'].split():
            claimed[f].append(e['lemma'])
    problems = []
    for w in attested:
        if w not in claimed:
            problems.append(f'attested form not in dictionary: {w}')
    for f, lemmas in claimed.items():
        if f not in attested:
            problems.append(f'dictionary form not attested in source: {f} ({", ".join(lemmas)})')
        if len(lemmas) > 1 and f not in HOMONYMS:
            problems.append(f'form claimed twice: {f} ({", ".join(lemmas)})')
    dup = [l for l, c in collections.Counter(e['lemma'] for e in entries).items() if c > 1]
    for l in dup:
        problems.append(f'duplicate lemma: {l}')
    return claimed, problems


def build_md(entries, attested):
    out = []
    out.append('# Church Slavonic dictionary of the Akathist to the Theotokos before the Kazan icon\n')
    out.append('Church Slavonic → Russian · English · Dutch. Generated from `dictionary.psv` by `tools/build.py`; '
               f'{len(entries)} entries covering all {len(attested)} distinct word-forms '
               f'({sum(attested.values())} tokens) of the source text in `source/akafist-kazanskaja-cs.txt`.\n')
    out.append('Each entry gives the lemma (headword, civil script, with stress), part of speech, the forms in which the word '
               'actually occurs in the akathist (accent-free, with number of occurrences), the three glosses, and notes on the '
               'Greek original, biblical and liturgical background, false friends with modern Russian, and Dutch Orthodox usage. '
               'Glosses separated by ";" are alternatives in descending order of preference; the notes say when a rendering '
               'should be fixed once and kept throughout.\n')
    out.append('Abbreviations: n.m/n.f/n.n noun (masc./fem./neut.), n.pl plurale tantum, n.prop proper noun, adj adjective, '
               'adj.comp/adj.sup comparative/superlative, v verb, adv adverb, part participle, pron pronoun, prep preposition, '
               'postp postposition, conj conjunction, interj interjection; voc./gen./dat./instr./loc. cases; sg./pl./dual number; '
               'aor. aorist; impf. imperfect; imper. imperative; inf. infinitive; refl. reflexive; act./pass. active/passive; '
               'Gr. Greek; LXX Septuagint (Psalm numbers follow the LXX); CS Church Slavonic; NL Dutch.\n')
    letters = []
    current = None
    for e in sorted(entries, key=lambda e: sort_key(e['lemma'])):
        first = sort_key(e['lemma'])[0].upper()
        if first != current:
            current = first
            letters.append(first)
            out.append(f'\n## {first}\n')
        forms = ', '.join(f'{f} ({attested.get(f, 0)})' for f in e['forms'].split())
        out.append(f'### {e["lemma"]}\n')
        out.append(f'*{e["pos"]}* — forms: {forms}\n')
        out.append(f'- **RU:** {e["ru"]}')
        out.append(f'- **EN:** {e["en"]}')
        out.append(f'- **NL:** {e["nl"]}')
        if e['notes']:
            out.append(f'- *Notes:* {e["notes"]}')
        out.append('')
    # letter index near top
    idx = ' · '.join(f'[{l}](#{l.lower()})' for l in letters)
    out.insert(4, f'Letters: {idx}\n')
    MD.write_text('\n'.join(out) + '\n', encoding='utf-8')


def build_index(entries, attested):
    rows = []
    for e in entries:
        for f in e['forms'].split():
            rows.append((f, attested.get(f, 0), e['lemma'], e['pos'], e['nl']))
    rows.sort(key=lambda r: (r[0], r[2]))
    with IDX.open('w', encoding='utf-8') as fh:
        fh.write('form\tcount\tlemma\tpos\tnl\n')
        for r in rows:
            fh.write('\t'.join(str(x) for x in r) + '\n')


def typ_str(s):
    """Return s as a Typst string literal, with straight double quotes turned into typographic ones."""
    out, open_q = [], True
    for ch in s:
        if ch == '"':
            out.append('“' if open_q else '”')
            open_q = not open_q
        else:
            out.append(ch)
    s = ''.join(out).replace('\\', '\\\\')
    return '"' + s + '"'


TYP_PREAMBLE = r"""// Generated by tools/build.py from dictionary/dictionary.psv — edit the .psv, not this file.
// Compile with:  typst compile dictionary/dictionary.typ
#set document(title: "Church Slavonic dictionary of the Akathist to the Theotokos before the Kazan icon")
#set page(
  paper: "%(paper)s",
  margin: (x: 11mm, top: 13mm, bottom: 12mm),
  header: context {
    if counter(page).get().first() > 2 {
      // guide words: first and last headword on this page (an entry continued from the previous page counts as first)
      let on-page = query(<entry>).filter(m => m.location().page() == here().page())
      let before = query(selector(<entry>).before(here()))
      let first = if before.len() > 0 { before.last().value } else if on-page.len() > 0 { on-page.first().value } else { none }
      let last = if on-page.len() > 0 { on-page.last().value } else { first }
      set text(size: 7.5pt)
      if first != none { strong(first) }
      h(1fr)
      counter(page).display()
      h(1fr)
      if last != none { strong(last) }
      v(-0.4em)
      line(length: 100%%, stroke: 0.4pt)
    }
  },
)
// PT Serif has proper mark anchoring for Cyrillic, so the stress marks (U+0301) sit centred on their vowels;
// Greek (absent from PT Serif) falls back to Libertinus Serif, which Typst bundles.
#set text(font: ("PT Serif", "Libertinus Serif"), size: %(size)spt, lang: "en")
// PT Serif does contain a few Greek-coded technical glyphs (π, μ, Ω …); without this rule Typst would take those from
// PT Serif and the rest of a Greek word from Libertinus. Force every Greek run into Libertinus. The run must start with
// a Greek letter so that Cyrillic combining stress marks (U+0301) are never matched on their own.
#show regex("\\p{Greek}[\\p{Greek}\\p{M}]*"): set text(font: "Libertinus Serif")
#set par(justify: true, leading: 0.42em, spacing: 0.42em)

// letter sections: a large initial in the column, no page break (as in a printed dictionary)
#show heading.where(level: 1): it => block(
  above: 1.4em, below: 0.6em, width: 100%%,
  stroke: (bottom: 0.6pt), inset: (bottom: 0.25em),
  text(size: 18pt, weight: "bold", it.body),
)

#let tag(s) = text(size: 0.78em, weight: "semibold", fill: luma(70), tracking: 0.05em, upper(s))
#let entry(lemma, pos, forms, ru, en, nl, notes) = par(hanging-indent: 1.1em)[
  #metadata(lemma)<entry>#strong(text(size: 1.08em, lemma))
  #emph(pos)
  #text(size: 0.82em, fill: luma(80))[⟨#forms⟩]
  #tag("ru") #ru
  #tag("en") #en
  #tag("nl") #nl
  #if notes != "" [ #text(size: 0.86em)[◆ #notes]]
]

#align(center)[
  #v(2fr)
  #text(size: 19pt, weight: "bold")[Church Slavonic dictionary of the Akathist to the Theotokos before the Kazan icon]
  #v(1em)
  #text(size: 12pt)[Church Slavonic → Russian · English · Dutch]
  #v(1.5em)
  #text(size: 9.5pt)[
    Акафист Пресвятой Богородице пред иконой «Казанская» \
    Source text: azbyka.ru, retrieved 2026-09-19 \
    %(n_entries)d entries · %(n_forms)d distinct word-forms · %(n_tokens)d tokens \
    Generated %(date)s
  ]
  #v(3fr)
]
#pagebreak()

#text(size: 9.5pt)[
= How to read the entries
Each entry gives the *headword* (lemma, civil script, with stress), the _part of speech_, in angle brackets the forms in which the word actually occurs in the akathist (accent-free; the number of occurrences follows in parentheses when it is more than one), then the glosses marked #tag("ru"), #tag("en") and #tag("nl"). Glosses separated by “;” are alternatives in descending order of preference. The notes after ◆ give the Greek original, biblical and liturgical background (Psalm numbers follow the Septuagint), false friends with modern Russian, and Dutch Orthodox usage; they say when a rendering should be fixed once and kept throughout. The running head shows the first and last headword of each page.

*Abbreviations.* n.m / n.f / n.n noun (masc. / fem. / neut.), n.pl plurale tantum, n.prop proper noun, adj adjective, adj.comp / adj.sup comparative / superlative, v verb, adv adverb, part participle, pron pronoun, prep preposition, postp postposition, conj conjunction, interj interjection; voc. / gen. / dat. / instr. / loc. cases; sg. / pl. / dual number; aor. aorist; impf. imperfect; imper. imperative; inf. infinitive; refl. reflexive; act. / pass. active / passive; Gr. Greek; LXX Septuagint; CS Church Slavonic; NL Dutch.

*Homonyms.* Two forms of the text belong to two entries each: _мир_ (peace / world) and _о_ (preposition / interjection); both entries are listed.
]
#pagebreak()

#show: it => columns(%(columns)d, gutter: 5mm, it)

"""

PAPER_DEFAULTS = {'a5': (2, 8.2), 'b5': (2, 8.5), 'a4': (3, 8.5), 'us-letter': (3, 8.5)}


def build_typ(entries, attested, paper, columns, size):
    out = [TYP_PREAMBLE % dict(paper=paper, columns=columns, size=size, n_entries=len(entries), n_forms=len(attested),
                               n_tokens=sum(attested.values()), date=datetime.date.today().isoformat())]
    current = None
    for e in sorted(entries, key=lambda e: sort_key(e['lemma'])):
        first = sort_key(e['lemma'])[0].upper()
        if first != current:
            current = first
            out.append(f'= {first}\n')
        forms = ', '.join(f'{f} ({attested[f]})' if attested.get(f, 0) > 1 else f for f in e['forms'].split())
        args = ', '.join(typ_str(x) for x in (e['lemma'], e['pos'], forms, e['ru'], e['en'], e['nl'], e['notes']))
        out.append(f'#entry({args})\n')
    TYP.write_text('\n'.join(out), encoding='utf-8')


def compile_pdf():
    typst = shutil.which('typst')
    if not typst:
        print('typst not found; skipping PDF')
        return
    r = subprocess.run([typst, 'compile', str(TYP), str(PDF)], capture_output=True, text=True)
    if r.returncode != 0:
        print('typst compile failed:\n', r.stderr)
    else:
        if r.stderr.strip():
            print(r.stderr.strip())
        print('wrote', PDF.relative_to(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper', default='a5', help='Typst paper size for the PDF (default: a5)')
    ap.add_argument('--columns', type=int, help='number of text columns (default: 2 for a5/b5, 3 for a4/letter)')
    ap.add_argument('--size', type=float, help='base font size in pt (default: 8.2 for a5, 8.5 otherwise)')
    ap.add_argument('--no-pdf', action='store_true', help='write the .typ file but do not run typst')
    args = ap.parse_args()
    attested = tokenize(SRC.read_text(encoding='utf-8'))
    entries, errors = load_entries()
    claimed, problems = check(entries, attested)
    for p in errors + problems:
        print('PROBLEM:', p)
    build_md(entries, attested)
    build_index(entries, attested)
    columns, size = PAPER_DEFAULTS.get(args.paper.lower(), (2, 8.5))
    build_typ(entries, attested, args.paper, args.columns or columns, args.size or size)
    if not args.no_pdf:
        compile_pdf()
    covered = sum(c for w, c in attested.items() if w in claimed)
    print(f'{len(entries)} entries; {len(attested)} forms; token coverage {covered}/{sum(attested.values())}; '
          f'{len(errors) + len(problems)} problems')
    sys.exit(1 if errors or problems else 0)


if __name__ == '__main__':
    main()
