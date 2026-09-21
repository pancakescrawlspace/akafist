#!/usr/bin/env python3
"""Phase 6 of djachenko/PLAN.md: entries.tsv -> djachenko/djachenko.typ (+ PDF), set like the 1900 original.

    python3 tools/dj_build.py                        # the whole dictionary (main part + supplement)
    python3 tools/dj_build.py --subset links         # only the entries linked to the akathist lemmas (links.tsv)
    python3 tools/dj_build.py --leaves 38-60         # a range of leaves of scan A, for a quick look
    python3 tools/dj_build.py --marks                # underline the places where the witnesses disagree
    python3 tools/dj_build.py --no-refs --no-pdf     # without the grey page references; .typ only
    python3 tools/dj_build.py --facsimile [--leaves 140-160] [--size 12] [--scale 1.08]
                                                     # Rev. 6: djachenko/facsimile.typ + .pdf, line for line
    python3 tools/dj_build.py --gt [45 146 …]        # the ground-truth pages as facsimile pages, to proofread:
                                                     # djachenko/facsimile-P<printed page>.pdf (eval/README.md)

The page follows the original (measured on scan A, 600 ppi): A4 with the original's text block of 169 x 249 mm,
two columns of 82.5 mm with a 5.3 mm gutter and a rule between them, 12.6 pt line pitch, a hanging indent of
4.9 mm; the page number centred at the top over a short double rule, the guide words (first three letters of the
first and last headword, with a dash) in Church Slavonic type at the outer ends; the running title "Церк.-славян.
словарь свящ. Г. Дьяченко." with the signature number at the foot of every sixteenth page, as in the book. A letter
section begins with a large initial (in the column — the original centres it across both). Headwords are set in
Ponomar Unicode (the Synodal Church Slavonic typeface), everything else in Old Standard TT (a revival of the civil
type of the period, with the pre-reform letters and polytonic Greek); both fonts are OFL and fetched into
djachenko/fonts/ when missing.

Marks of the digital edition (not in the original): a headword that has not yet been read from the image (Phase 3b
step 2 pending; hw_provisional in entries.tsv) is printed grey; the italics are those ABBYY detected (incomplete);
at the end of every entry a small grey ¶ with the page and column of the 1900 edition (--no-refs to drop it); with
--marks the spans where witnesses D and B disagree are underlined. The front matter states all of this.

The facsimile (--facsimile, PLAN.md Phase 6 Rev. 6) sets the book page by page as the 1900 printer did: every
printed line of `entries.tsv` (its `lines` column, from ocr/*.json) is placed at its measured baseline and column
position (scan A's geometry, 600 ppi, deskewed on the column rule), justified to the column width with a forced
break, so that page 113 of the PDF is page 113 of the book, line for line; the page number, guide words,
signature line and letter initials sit where the scan has them (`header.base`, `guide_base`, `footer_base`,
`headings`). The type is Old Standard TT at --size (default 12 pt: the book's face is bigger than the 10 pt of
the flowing rendition — x-height 6.2 pt, cap height 8.9 pt) on a page scaled by --scale (default 1.08: the
original's 82.5 mm columns are too narrow for Old Standard at 12 pt; the page grows to ~215 × 320 mm). A line
whose natural width still exceeds the column is condensed to fit and reported (`typst query` of <over>; the build
prints the count). Not in the facsimile yet: the front matter of the book (its lines are in ocr/ but not voted),
the Church Slavonic type inside entries (cross-references), and the italics beyond what ABBYY flagged.

With --gt the text of a page is its ground truth (eval/gt/NNNN.txt) instead of entries.tsv: its entries as the GT
divides them, each printed line where its `¦` marker says, set on scan A's lines in order, column by column (the
markers were placed so that the counts agree; a column where they do not is reported). The Church Slavonic type is
the GT's own `{…}` markup, in the head at the headword's size, in the text at the text's; letters read in another
copy (`‹…›`) are grey, an uncertain reading (`[?]`) is followed by a small grey ?, and a note at the foot names
the file and its status. One PDF per page, facsimile-P0008.pdf for p. 8, the .typ in djachenko/cache/.
"""
import argparse, csv, datetime, difflib, json, re, shutil, subprocess, sys, urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dj_abbyy  # noqa: E402  (the letter tables)
from dj_witness import DJ, OCR, norm_seq  # noqa: E402

ROOT = DJ.parent
ENTRIES, LINKS = DJ / 'entries.tsv', DJ / 'links.tsv'
TYP, PDF = DJ / 'djachenko.typ', DJ / 'djachenko.pdf'
FTYP, FPDF = DJ / 'facsimile.typ', DJ / 'facsimile.pdf'
FONTS = DJ / 'fonts'
FONT_FILES = {
    'PonomarUnicode.otf': 'https://raw.githubusercontent.com/typiconman/fonts-cu/master/Ponomar/PonomarUnicode.otf',
    'OFL-fonts-cu.txt': 'https://raw.githubusercontent.com/typiconman/fonts-cu/master/OFL.txt',
    'OldStandard-Regular.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/oldstandardtt/OldStandard-Regular.ttf',
    'OldStandard-Italic.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/oldstandardtt/OldStandard-Italic.ttf',
    'OldStandard-Bold.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/oldstandardtt/OldStandard-Bold.ttf',
    'OFL-oldstandard.txt': 'https://raw.githubusercontent.com/google/fonts/main/ofl/oldstandardtt/OFL.txt',
}
FRONT_PAGES = 2                         # title page + note; the dictionary's own page numbers start after them

PREAMBLE = r'''// Generated by tools/dj_build.py from djachenko/entries.tsv — do not edit; re-run the script.
// Compile with:  typst compile --font-path djachenko/fonts djachenko/djachenko.typ
#set document(title: "Полный церковно-славянскій словарь (Г. Дьяченко, 1900) — digital edition")
#let cs(body) = text(font: "Ponomar Unicode", body)
#let guide(s) = cs(text(size: 10.5pt, s))
#set text(font: ("Old Standard TT", "PT Serif", "Libertinus Serif"), size: %(size)spt, lang: "ru", hyphenate: false)
#set smartquote(enabled: false)   // the text carries the book's „…“ and «…»; Typst would turn " into «»
#show regex("\p{Greek}[\p{Greek}\p{M}]*"): set text(font: ("Old Standard TT", "Libertinus Serif"))
#set par(justify: true, leading: %(leading)sem, spacing: %(leading)sem, hanging-indent: 4.9mm)
#set columns(gutter: 5.3mm)
#set page(
  paper: "a4",
  columns: 2,
  margin: (left: 20.5mm, right: 20.5mm, top: 30mm, bottom: 18mm),
  header-ascent: 3mm,
  header: context {
    let pg = counter(page).get().first()
    if pg > %(front)d {
      // the entries on this page: between the header and the footer's marker, the header coming before the
      // page's body in document order and the footer after it. (Filtering all <e> by page, per page, took 2 min.)
      let end = query(selector(<pgend>).after(here()))
      let on = query(if end.len() > 0 { selector(<e>).after(here()).before(end.first().location()) }
                     else { selector(<e>).after(here()) })
      let before = query(selector(<e>).before(here()))
      let first = if before.len() > 0 { before.last().value } else if on.len() > 0 { on.first().value } else { none }
      let last = if on.len() > 0 { on.last().value } else { first }
      align(center, stack(dir: ttb, spacing: 1.3pt,
        text(weight: "bold", size: 11.5pt, str(pg - %(front)d)),
        line(length: 10mm, stroke: 0.9pt),
        line(length: 10mm, stroke: 0.35pt)))
      v(0.4em)
      grid(columns: (1fr, 1fr), align: (left, right),
        if first != none { guide(first) }, if last != none { guide(last) })
    }
  },
  footer: context {
    [#metadata(none)<pgend>]
    let pg = counter(page).get().first()
    if pg > %(front)d and calc.rem(pg - %(front)d - 1, 16) == 0 {
      set text(size: 8pt)
      [Церк.-славян. словарь свящ. Г. Дьяченко.]
      h(1fr)
      [#(calc.quo(pg - %(front)d - 1, 16) + 1)]
    }
  },
  background: context {
    if counter(page).get().first() > %(front)d {
      place(top + left, dx: 105mm, dy: 30mm, line(angle: 90deg, length: 249mm, stroke: 0.35pt))
    }
  },
)
#let e(g, hw, prov, sep, body, ref) = par(hanging-indent: 4.9mm)[
  #metadata(g)<e>#text(size: %(hwsize)spt, fill: if prov { luma(120) } else { black })[#hw]#sep#body#ref
]
#let letter(l) = block(width: 100%%, above: 1.6em, below: 0.9em, breakable: false,
  align(center, cs(text(size: 32pt, l + "."))))
#let dis(body) = underline(stroke: 0.35pt + luma(150), offset: 1.6pt, body)
#let ref(s) = text(size: 6.2pt, fill: luma(150))[ ¶#s]

// ---------------------------------------------------------------- title page and note (not in the original)
#page(columns: 1, header: none, footer: none, background: none)[
  #set align(center)
  #v(4fr)
  #block(text(size: 15pt, tracking: 0.15em)[ПОЛНЫЙ])
  #v(0.4em)
  #block(text(size: 22pt, weight: "bold", tracking: 0.08em)[ЦЕРКОВНО-СЛАВЯНСКІЙ СЛОВАРЬ])
  #v(0.6em)
  #block(text(size: 10.5pt)[(со внесеніемъ въ него важнѣйшихъ древне-русскихъ словъ и выраженій)])
  #v(2.2em)
  #block(text(size: 11pt)[Составилъ священникъ магистръ Григорій Дьяченко])
  #v(3fr)
  #block(text(size: 11pt)[МОСКВА · 1900])
  #v(2fr)
  #line(length: 30%%, stroke: 0.4pt)
  #v(1em)
  #block(text(size: 9.5pt)[Digital edition — work in progress \ %(subset_note)s \ generated %(date)s from `djachenko/entries.tsv`])
  #v(3fr)
]
#page(columns: 1, header: none, footer: none, background: none)[
  #set text(size: 9.5pt, lang: "en")
  #set par(hanging-indent: 0pt, justify: true)
  = About this edition
  %(note)s
]
#counter(page).update(%(front)d + 1)
'''

NOTE = r'''
The text was produced from scans of the 1900 edition (Москва, 1900; the author †1903 — public domain). The
segmentation into entries comes from the geometry of the Russian State Library copy (archive.org, 600 ppi); the
wording comes from the text layers of four copies read by two OCR engines, voted character by character
(Cornell University's copy as the primary witness, checked against the 1993 reprint and the Indiana University copy).
On six hand-transcribed test pages the definition text has about one error per hundred characters; most of the
remaining errors sit where the witnesses disagree.

*Headwords.* The Church Slavonic headwords are what no OCR reads reliably. In this build %(n_read)s of %(n_entries)s
headwords have been read from the page images; the remaining %(n_prov)s are printed *grey*: they are the primary
witness's provisional reading and may be garbled or missing. When the reading of the headwords is complete, the
grey will disappear and the alphabetical order will be checked.

*Typography.* The page reproduces the original's setting: its text block, two columns with a rule, the guide
words in Church Slavonic type, the page number over a double rule, the running title with the signature number on
every sixteenth page. Headwords are set in Ponomar Unicode, the rest in Old Standard TT; both fonts are free
(SIL Open Font License). The italics of the original (sources and quotations) are those the OCR detected and are
incomplete. Accents and titla of the Church Slavonic headwords are not reproduced (the letters are).

*Marks.* A small grey ¶ at the end of each entry gives the page and column of the 1900 edition, so that anything
can be verified against the scan.%(marks_note)s Nothing has been proofread yet; a later stage will check the entries
linked to the akathist dictionary (%(n_linked)s lemmas linked so far) and mark them as such.

*Status of the work* (%(date)s): scans and OCR layers acquired; segmentation done; text merged for all %(n_pages)s
pages; headword reading %(pct_read)s complete; structured file `entries.tsv` with %(n_entries)s entries
(%(n_main)s in the main part, %(n_supp)s in the supplement) and %(n_flags)s flagged for checking; errata of the
author not yet applied; proofreading not started.
'''


def fetch_fonts():
    FONTS.mkdir(exist_ok=True)
    for name, url in FONT_FILES.items():
        path = FONTS / name
        if path.exists() and path.stat().st_size > 1000:
            continue
        req = urllib.request.Request(url, headers={'User-Agent': 'akafist-dictionary-build'})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
        print('fetched', path.relative_to(ROOT))


def esc(s):
    """Text -> Typst markup-safe text (content context)."""
    s = s.replace('\\', '\\\\')
    for ch in '#$*_`<>@[]~':
        s = s.replace(ch, '\\' + ch)
    s = s.replace('//', '\\/\\/').replace('/*', '/\\*')
    s = re.sub(r'(?<=\S) - (?=\S)', ' — ', s.replace('--', '—'))
    if s[:1] in ('-', '+', '=', '/'):           # would start a list item, a heading or a comment
        s = '\\' + s
    s = re.sub(r'^(\d+)\.(?=\s)', r'\1\\.', s)   # "1. " would start an enumeration
    return s


def spans_of(s):
    return [tuple(int(x) for x in part.split('-')) for part in s.split(';') if part]


def markup(text, italic, disputed, marks):
    """The definition as markup with emph over the italic spans and (optionally) underlines over the disputed."""
    cuts = {0, len(text)}
    for a, b in italic + (disputed if marks else []):
        cuts.update((min(a, len(text)), min(b, len(text))))
    cuts = sorted(cuts)
    out = []
    for a, b in zip(cuts, cuts[1:]):
        seg = esc(text[a:b])
        if any(s <= a and b <= e for s, e in italic):
            seg = f'#emph[{seg}];'
        if marks and any(s <= a and b <= e for s, e in disputed):
            seg = f'#dis[{seg}];'
        out.append(seg)
    return ''.join(out)


def guide_of(hw):
    letters = [c for c in hw if c.isalpha()]
    return ''.join(letters[:3]) + '—' if letters else ''


def load(subset, leaves):
    rows = list(csv.DictReader(open(ENTRIES, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    if subset == 'links' and LINKS.exists():
        ids = set()
        for r in csv.DictReader(open(LINKS, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE):
            ids.update(x for x in r['ids'].split(';') if x)
        rows = [r for r in rows if r['id'] in ids]
    if leaves:
        rows = [r for r in rows if int(r['id'][:4]) in leaves]
    return rows


def letter_headings(rows):
    """{row index: letter}: where each letter section begins. The manifest names the letters on every leaf; a
    letter that starts on a leaf ("Б,В") is placed before the first entry of that leaf whose headword begins with
    it, else before the first entry of the next leaf. Each letter is placed once per part."""
    letters = {}
    for r in csv.DictReader(open(DJ / 'manifest.tsv', encoding='utf-8'), delimiter='\t'):
        letters[int(r['idx'])] = r['letter'].replace(',', ' ').split()
    out, placed, pending = {}, set(), []
    for i, r in enumerate(rows):
        leaf = int(r['id'][:4])
        Ls = letters.get(leaf, [])
        starts_leaf = i == 0 or int(rows[i - 1]['id'][:4]) != leaf
        if i == 0 or rows[i - 1]['part'] != r['part']:
            placed, pending = set(), []
        for L in Ls:
            if L not in placed and L not in pending:
                pending.append(L)
        if pending:
            first = (r['headword_civil'][:1] or '').lower()
            if first == pending[0].lower() or (starts_leaf and (Ls[:1] == [pending[0]] or pending[0] not in Ls)):
                out[i] = pending.pop(0)
                placed.add(out[i])
    return out


def build(rows, refs, marks, size, leading, hwsize, subset):
    all_rows = list(csv.DictReader(open(ENTRIES, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    n_entries = len(all_rows)
    n_prov = sum('hw_provisional' in r['flags'] for r in all_rows)
    n_linked = 0
    if LINKS.exists():
        n_linked = sum(1 for r in csv.DictReader(open(LINKS, encoding='utf-8'), delimiter='\t',
                                                   quoting=csv.QUOTE_NONE) if r['match'] != 'none')
    parts = Counter(r['part'] for r in all_rows)
    n_flags = sum(1 for r in all_rows if set(r['flags'].split(';')) - {'hw_provisional', 'order', 'guessed', ''})
    note = NOTE % dict(n_read=f'{n_entries - n_prov:,}', n_entries=f'{n_entries:,}', n_prov=f'{n_prov:,}',
                       n_linked=n_linked, n_pages=1119, pct_read=f'{(n_entries - n_prov) / n_entries:.0%}',
                       n_main=f'{parts["main"]:,}', n_supp=f'{parts["supplement"]:,}', n_flags=f'{n_flags:,}',
                       date=datetime.date.today().isoformat(),
                       marks_note=(' The places where the witnesses disagree are underlined in grey.' if marks else ''))
    subset_note = {'all': 'main part and supplement, complete',
                   'links': 'the entries linked to the akathist dictionary only'}.get(subset, subset)
    out = [PREAMBLE % dict(size=size, leading=leading, hwsize=hwsize, front=FRONT_PAGES, note=note.strip(),
                           subset_note=subset_note, date=datetime.date.today().isoformat())]
    heading_before = letter_headings(rows)
    part = None
    for i, r in enumerate(rows):
        if r['part'] != part:
            part = r['part']
            if part == 'supplement':
                out.append('#pagebreak()\n#block(width: 100%, above: 0.5em, below: 1.2em, '
                           'align(center, text(size: 14pt, tracking: 0.1em)[ПРИБАВЛЕНІЕ.]))\n')
        if i in heading_before:
            out.append(f'#letter("{heading_before[i]}")\n')
        hw = r['headword'] or '□'
        prov = 'true' if r['hw_source'] == 'D' else 'false'
        sep = {'=': ' = ', '—': ' — ', '(': ' '}.get(r['sep'], ' ')
        body = markup(r['definition'], spans_of(r['italic']), spans_of(r['disputed']), marks)
        ref = f'ref("{r["page"]}{r["col"]}")' if refs else 'none'
        g = guide_of(hw)
        out.append(f'#e("{esc_str(g)}", [{head_markup(hw)}], {prov}, "{sep}", [{body}], {ref})\n')
    TYP.write_text(''.join(out), encoding='utf-8')


def esc_str(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def compile_pdf():
    typst = shutil.which('typst')
    if not typst:
        print('typst not found; skipping PDF')
        return
    r = subprocess.run([typst, 'compile', '--font-path', str(FONTS), str(TYP), str(PDF)], capture_output=True,
                       text=True)
    if r.returncode != 0:
        print('typst compile failed:\n', r.stderr[:3000])
        return
    if r.stderr.strip():
        print(r.stderr.strip()[:2000])
    print('wrote', PDF.relative_to(ROOT), f'({PDF.stat().st_size // 1024} KB)')


# ---------------------------------------------------------------- the facsimile (Rev. 6)

PX = 25.4 / 600                       # mm per pixel of scan A
COLW = 1927                           # printed column width, px (median of the justified lines of the book)
FLUSH_A, FLUSH_B = -2001, 66          # the columns' flush edges relative to the rule, px (book-wide medians: the
#                                       per-page fits vary with the page's curl in the scan and are unusable on the
#                                       242 pages whose left margin is cut off)
HEAD_DY, GUIDE_DY, FOOT_DY = 240, 125, 187   # page number, guide words above / signature line below the text, px
BLOCK_H = 5892                        # nominal first baseline -> lowest last baseline over the book, px
BLOCK_W = 3969                        # left flush edge of column a -> right edge of column b, px
MARGIN = dict(left=17, right=17, top=14, bottom=12)     # mm, around number/text block/signature line

FACS_PREAMBLE = r"""// Generated by tools/dj_build.py --facsimile from djachenko/entries.tsv and ocr/*.json — do not edit.
// Compile with:  typst compile --font-path djachenko/fonts djachenko/facsimile.typ
#set document(title: "Полный церковно-славянскій словарь (Г. Дьяченко, 1900) — facsimile")
#let cs(body) = text(font: "Ponomar Unicode", body)
#set text(font: ("Old Standard TT", "PT Serif", "Libertinus Serif"), size: %(size)spt, lang: "ru", hyphenate: false,
  top-edge: "baseline", bottom-edge: "baseline")
#set smartquote(enabled: false)
#show regex("\p{Greek}[\p{Greek}\p{M}]*"): set text(font: ("Old Standard TT", "Libertinus Serif"))
#set par(justify: false, leading: 0pt, spacing: 0pt, hanging-indent: 0pt, first-line-indent: 0pt)
#set page(width: %(pw).1fmm, height: %(ph).1fmm, margin: 0mm, header: none, footer: none)
#let hw(prov, body) = cs(text(size: %(hwsize)spt, fill: if prov { luma(120) } else { black }, body))
#let dis(body) = underline(stroke: 0.35pt + luma(150), offset: 1.6pt, body)
// a printed line: at (x, y) = its left edge and baseline, w = the column's width from there; justified unless it
// is the entry's last; condensed when its natural width exceeds w (and reported through <over>)
#let L(x, y, w, j, id, body) = place(top + left, dx: x, dy: y, context {
  let nat = measure(box(body)).width
  if nat > w {
    [#box(width: w, scale(x: w / nat * 100%%, reflow: true, body))#metadata((id: id, over: nat / w))<over>]
  } else if j {
    box(width: w, par(justify: true)[#body#linebreak(justify: true)])
  } else {
    box(width: w, body)
  }
})
#let T(x, y, body) = place(top + left, dx: x, dy: y, body)
// a paragraph ABBYY stored as a picture: no lines in A, so the text flows from its first baseline at the pitch
#let P(x, y, w, lead, body) = place(top + left, dx: x, dy: y, box(width: w, par(justify: true, leading: lead)[#body]))
#let C(x, y, body) = place(top + left, dx: x, dy: y, box(width: 0pt, align(center, box(body))))
// a heading (letter initial, title) fitted into its measured box: x = centre, y = baseline, w × h = the box
#let H(x, y, w, h, body) = place(top + left, dx: x, dy: y, context {
  let b = box(text(top-edge: "cap-height", bottom-edge: "baseline", body))
  let m = measure(b)
  let f = calc.min(w / m.width, h / calc.max(m.height, 1pt))
  move(dx: -m.width * f / 2, dy: -m.height * f, box(width: m.width * f, scale(f * 100%%, reflow: true, b)))
})
#let R(x, y, body) = place(top + left, dx: x, dy: y, box(width: 0pt, align(right, box(body))))
#let rule(x, y0, y1) = place(top + left, dx: x, dy: y0, line(angle: 90deg, length: y1 - y0, stroke: 0.35pt))
#let hr(x, y, l, s) = place(top + left, dx: x, dy: y, line(length: l, stroke: s))

#page(margin: 20mm)[
  #set text(top-edge: "cap-height", bottom-edge: "baseline")
  #set align(center)
  #v(4fr)
  #block(text(size: 15pt, tracking: 0.15em)[ПОЛНЫЙ])
  #v(0.4em)
  #block(text(size: 22pt, weight: "bold", tracking: 0.08em)[ЦЕРКОВНО-СЛАВЯНСКІЙ СЛОВАРЬ])
  #v(0.6em)
  #block(text(size: 10.5pt)[(со внесеніемъ въ него важнѣйшихъ древне-русскихъ словъ и выраженій)])
  #v(2.2em)
  #block(text(size: 11pt)[Составилъ священникъ магистръ Григорій Дьяченко])
  #v(3fr)
  #block(text(size: 11pt)[МОСКВА · 1900])
  #v(2fr)
  #line(length: 30%%, stroke: 0.4pt)
  #v(1em)
  #block(text(size: 9.5pt)[Digital facsimile — work in progress \ line for line as the 1900 edition, %(subset_note)s \ generated %(date)s from `djachenko/entries.tsv`])
  #v(3fr)
]
#page(margin: 20mm)[
  #set text(size: 9.5pt, lang: "en", top-edge: "cap-height", bottom-edge: "baseline")
  #set par(justify: true, leading: 0.65em, spacing: 1em)
  = About this facsimile
  %(note)s
]
"""

FACS_NOTE = r"""
Every printed line, column and page of this rendition is the same as in the 1900 edition: the lines were located
in the scan of the Russian State Library copy (600 ppi) and the text of each was placed at the line's own position
on the page, so that page 113 here is page 113 of the book, line for line. The text itself comes from four copies
read by two OCR engines and voted (see the flowing edition's note); nothing has been proofread yet.

*Type.* The book's face is larger than it looks — x-height 6.2 pt, cap height 8.9 pt on a 12.2 pt line — and
wider than Old Standard TT, the free revival used here. The type is therefore set at %(size)s pt and the whole
page enlarged %(pct)s (the original's text block is 169 × 249 mm). A line that Old Standard still cannot fit into
the original's measure is condensed slightly: %(over)s such lines in this build. Church Slavonic headwords are in
Ponomar Unicode; a headword not yet read from the images is printed grey, and a □ stands where the OCR read no
headword at all. On the pages whose left margin the scan cuts off, some continuation lines were taken for entry
starts; they are set indented and without a head, and a few real entries there begin flush that should not.%(marks_note)s

*Status* (%(date)s): %(n_entries)s entries on %(n_pages)s pages; %(n_read)s headwords read from the images;
italics as far as the OCR flagged them; Church Slavonic type inside the entries not yet marked; the front matter
of the book not yet included.
"""


def facs_pages(leaves):
    """The ocr/*.json pages of the dictionary proper (main, blank, supplement), in order."""
    out = []
    for f in sorted(OCR.glob('[0-9][0-9][0-9][0-9].json')):
        pg = json.loads(f.read_text(encoding='utf-8'))
        if pg['section'] in ('main', 'blank', 'supplement') and (not leaves or pg['idx'] in leaves):
            out.append(pg)
    return out


def starting_letters(pg):
    """The letters whose section begins on this page, from the book's table of contents (dj_abbyy)."""
    p = int(pg['printed_page'])
    table = dj_abbyy.MAIN_LETTERS if pg['section'] == 'main' else dj_abbyy.SUPP_LETTERS
    return [L for L, a, b in table if a == p]


# Words that stand in the head but are not the headword: the print sets them in the civil type, not in the
# Church Slavonic of the lemma ("Або, иногда альбо" — the entry is Або, sometimes given as альбо). Confirmed on
# the twelve ground-truth pages, which mark the Church Slavonic type: the words that fall between two marked
# groups there are и (5), или (3) and вм. (1), and none of the four ever appears inside one.
#   или / иногда / иначе / также / вм. are never part of a lemma, whatever stands either side of them (иначе
#   checked on the scan too: p. 7 "Аермонъ, иначе Ермонъ", the two names Church Slavonic, иначе civil).
#   и can be: "Дворяне и дѣти боярскіе", "Испытаніе водою и желѣзомъ", "Полъ и Луда" are headwords in their own
#   right, so it is taken as a connective only where it joins two spellings of one word ("Мождевельникъ и
#   можжевельникъ") — measured over the book, 148 of the 240 heads that have an internal и.
HEAD_CIVIL = ('или', 'иногда', 'иначе', 'также', 'вм', 'вмѣсто')
HEAD_JOIN = ('и',)                      # only between two spellings of the same word


def variants(a, b):
    """Are these two words the same word spelled differently, rather than two words of a phrase?"""
    na, nb = (''.join(norm_seq(x.strip('.,;:()'))[0]) for x in (a, b))
    return bool(na) and bool(nb) and difflib.SequenceMatcher(None, na, nb).ratio() >= 0.55


def head_spans(head):
    """The head's Church Slavonic spans: all of it, less the explanatory words above. -> [(start, end)]."""
    words, spans, pos, keep = head.split(' '), [], 0, []
    for i, w in enumerate(words):
        bare = w.strip('.,;:()').lower()
        civil = bare in HEAD_CIVIL or (bare in HEAD_JOIN and 0 < i < len(words) - 1
                                       and variants(words[i - 1], words[i + 1]))
        keep.append((pos, pos + len(w), not civil))
        pos += len(w) + 1
    for s, e, cs in keep:                                  # merge the runs that stay Church Slavonic
        if not cs:
            continue
        if spans and s - spans[-1][1] <= 1:
            spans[-1][1] = e
        else:
            spans.append([s, e])
    return [tuple(s) for s in spans]


def head_markup(head):
    """The head as Typst markup: its Church Slavonic spans in the Church Slavonic face, the explanatory words
    between them (`или`, `иногда`, `вм.`, a connective `и`) in the civil face the print gives them."""
    out, pos = [], 0
    for s, e in (head_spans(head) if head != '\u25a1' else [(0, len(head))]):
        if s > pos:
            out.append(esc(head[pos:s]))
        out.append(f'#cs[{esc(head[s:e])}];')
        pos = e
    if pos < len(head):
        out.append(esc(head[pos:]))
    return ''.join(out)


def line_markup(text, a, b, regions, marks):
    """text[a:b] as Typst markup: regions = [(start, end, kind)] in text coordinates, kind cs (headword,
    provisional or not: 'cs'/'csp'), 'i' (italic) and 'd' (disputed); on a ground-truth page (--gt) also 'cst'
    (Church Slavonic type inside the definition), 'o' (letters read in another copy) and 'q' (an uncertain reading)."""
    cuts = {a, b}
    for s, e, _ in regions:
        if s < b and e > a:
            cuts.update((max(a, s), min(b, e)))
    out = []
    for x, y in zip(sorted(cuts), sorted(cuts)[1:]):
        seg = esc(text[x:y])
        if not seg:
            continue
        kinds = {k for s, e, k in regions if s <= x and y <= e}
        if 'q' in kinds:
            seg = f'#text(fill: luma(120), size: 0.7em, baseline: -0.35em)[{seg}];'
        if 'o' in kinds:
            seg = f'#text(fill: luma(120))[{seg}];'
        if 'i' in kinds:
            seg = f'#emph[{seg}];'
        if marks and 'd' in kinds:
            seg = f'#dis[{seg}];'
        if 'cs' in kinds or 'csp' in kinds:
            seg = f'#hw({"true" if "csp" in kinds else "false"})[{seg}];'
        elif 'cst' in kinds:
            seg = f'#cs[{seg}];'
        out.append(seg)
    return ''.join(out)


def entry_lines(r, marks):
    """-> (text, regions, [(start, end, hyphen, last)], cont) of an entry: the text as HEAD + definition, the
    style regions, the printed lines as spans of the text (offsets of the `lines` column made absolute), and
    cont = True for an "entry" that is really a continuation line the segmentation took for an entry start: set
    without a head, indented.  Only an entry whose start no witness could confirm qualifies (flag `guessed`: a
    cut-margin page where A decided from text features alone) and that has neither headword nor separator.  Every
    other entry begins an entry — witnesses C and D read the printed indentation, dj_seg.py — and a headword the
    OCR did not read is printed as □ rather than made to disappear into the article above."""
    cont = not r['headword'] and not r['sep'] and 'guessed' in r['flags'].split(';')
    hw_ = r['headword'] or ('' if cont else '□')
    sep = {'=': ' = ', '—': ' — ', '(': ' '}.get(r['sep'], ' ') if not cont else ''
    head = hw_ + sep
    text = head + r['definition']
    d0 = len(head)
    kind = 'csp' if r['hw_source'] == 'D' else 'cs'
    regions = [(s, e, kind) for s, e in head_spans(hw_)] if hw_ != '□' else [(0, len(hw_), kind)]
    regions += [(d0 + a, d0 + b, 'i') for a, b in spans_of(r['italic'])]
    if marks:
        regions += [(d0 + a, d0 + b, 'd') for a, b in spans_of(r['disputed'])]
    items = [x for x in r['lines'].split(';') if x]
    starts = [max(0, min(len(text), d0 + int(x.rstrip('h')))) for x in items]
    starts[0:1] = [0]
    lines = []
    for k, x in enumerate(items):
        s = starts[k]
        e = starts[k + 1] if k + 1 < len(items) else len(text)
        lines.append((s, max(s, e), x.endswith('h'), k == len(items) - 1))
    return text, regions, lines, cont


def build_facsimile(rows, marks, size, scale, hwsize, leaves, gt=None, typ=FTYP):
    """The facsimile of `leaves` (all pages when None) into `typ`. With gt (one ground-truth page, gt_page()) the
    text is the GT's instead of entries.tsv's, line for line on scan A's lines, and only the page itself is set."""
    k = PX * scale                                              # mm per px of the scan
    left, top = MARGIN['left'], MARGIN['top'] + HEAD_DY * k    # x of column a's flush edge, y of the first baseline
    pw = MARGIN['left'] + BLOCK_W * k + MARGIN['right']
    ph = top + (BLOCK_H + FOOT_DY) * k + MARGIN['bottom']
    pages = facs_pages(leaves)
    by_id = {r['id']: r for r in rows}
    out, n_lines, n_pages, over_guess = [], 0, 0, 0
    cur = None                                                  # (entry, its lines, text, regions, next line index)
    for pg in pages:
        n_pages += 1
        p = int(pg['printed_page']) if pg['printed_page'] else 0
        if pg['section'] == 'blank' or not pg['columns']:
            out.append('#page[]\n')
            continue
        rule0, rule1 = pg['rule'] or (pg['size'][0] / 2, 0)
        gx = lambda y: rule0 + rule1 * y                        # noqa: E731 — x of the column rule at height y
        cols = pg['columns']
        flush = {'a': FLUSH_A, 'b': FLUSH_B}
        # the nominal first baseline of the text block: the first line's, since every column starts at the block
        # top — unless a heading stands above it (p. 1, p. 865 …), then the page number's baseline + HEAD_DY when
        # the number was read (a speck or a guide word can pass for one: the digits are the check), else a guess
        hdr = pg['header']
        first_base = min(c['paragraphs'][0]['lines'][0]['base'] for c in cols if c['paragraphs'])
        tops = [h['bbox'][1] for h in pg['headings'] if h['bbox'][1] < first_base - 150]
        if not tops:
            y_ref = first_base
        elif hdr.get('base') and re.search(r'\d', hdr['page_number']):
            y_ref = hdr['base'] + HEAD_DY
        else:
            y_ref = min(tops) + 190
        X = lambda x: left + (x - gx(y_ref) - flush['a']) * k     # noqa: E731 — page x of a deskewed scan x
        Y = lambda y: top + (y - y_ref) * k                       # noqa: E731
        col_x = {'a': X(gx(y_ref) + flush['a']), 'b': X(gx(y_ref) + flush['b'])}
        items = []
        # furniture: page number over a short double rule, guide words, the column rule
        first_hw = last_hw = None
        for c in cols:
            for pi, par in enumerate(c['paragraphs'], 1):
                r = by_id.get(f"{pg['idx']:04d}-{c['n']}-{pi:02d}")
                if r and r['headword']:
                    first_hw = first_hw or r['headword']
                    last_hw = r['headword']
        gsize = f'size: {size * 1.05:.1f}pt'
        guides = [f'cs(text({gsize})[{esc(guide_of(hw))}])' if hw else None for hw in (first_hw, last_hw)]
        if gt:
            guides = [f'text({gsize})[{g}]' for g in gt['guides']]
        above = [h for h in pg['headings'] if h['bbox'][1] < first_base - 150]
        # the number is printed where the OCR read one, or where nothing but the OCR's miss says it is absent;
        # p. 1 opens with the letter's initial and has none (the OCR's "number" there is bleed-through)
        if p and (re.search(r'\d', hdr['page_number']) or not above):
            xc = X(gx(y_ref))
            yn = Y(y_ref - HEAD_DY)
            items.append(f'#C({xc:.2f}mm, {yn:.2f}mm, text(weight: "bold", size: {size * 1.15:.1f}pt)[{p}])')
            # the supplement sets its running title just below: there the rules sit close under the number
            r0, r1 = (0.8, 1.4) if pg['section'] == 'supplement' else (1.6, 2.4)
            items.append(f'#hr({xc - 5:.2f}mm, {yn + r0:.2f}mm, 10mm, 0.9pt)')
            items.append(f'#hr({xc - 5:.2f}mm, {yn + r1:.2f}mm, 10mm, 0.35pt)')
            yg = Y(y_ref - GUIDE_DY)
            if pg['section'] == 'supplement':                  # the supplement's running title, on every page
                items.append(f'#C({xc:.2f}mm, {yg:.2f}mm, text(size: {size * 0.85:.1f}pt, tracking: 0.12em)[Прибавленіе.])')
            if guides[0]:
                items.append(f'#T({col_x["a"] + 220 * k:.2f}mm, {yg:.2f}mm, {guides[0]})')
            if guides[1]:
                items.append(f'#R({col_x["b"] + (COLW - 300) * k:.2f}mm, {yg:.2f}mm, {guides[1]})')
        last_base = max(c['paragraphs'][-1]['lines'][-1]['base'] for c in cols if c['paragraphs'])
        items.append(f'#rule({X(gx(y_ref)):.2f}mm, {Y(y_ref - 90):.2f}mm, {Y(last_base + 30):.2f}mm)')
        # the signature line (first page of a sheet) and the asterisked sheet number (its third page)
        if p and p % 16 == 1:
            yf = Y(pg['footer_base'] or last_base + FOOT_DY)
            items.append(f'#T({col_x["a"]:.2f}mm, {yf:.2f}mm, text(size: {size * 0.75:.1f}pt)[Церк.-славян. словарь свящ. Г. Дьяченко.])')
            items.append(f'#R({col_x["b"] + COLW * k:.2f}mm, {yf:.2f}mm, text(size: {size * 0.75:.1f}pt)[{(p - 1) // 16 + 1}])')
        elif p and p % 16 == 3:
            yf = Y(last_base + FOOT_DY)
            items.append(f'#R({col_x["b"] + COLW * k:.2f}mm, {yf:.2f}mm, text(size: {size * 0.75:.1f}pt)[{(p - 3) // 16 + 1}\*])')
        # letter initials and titles, each fitted into its box on the scan
        letters = starting_letters(pg)
        for h in pg['headings']:
            x0, y0, x1, y1 = h['bbox']
            t = (h.get('text') or '').strip().rstrip('.').strip()
            if len(t) <= 2 or h['kind'] == 'picture':
                t = letters.pop(0) if letters else t
                body = f'cs(text(size: 40pt)[{esc(t)}.])'
                w, hh = (x1 - x0) * 1.3, (y1 - y0) * 0.92                # the box holds the letter; the dot is extra
            else:
                body = f'text(size: 20pt, tracking: 0.08em)[{esc(t)}]'
                w, hh = x1 - x0, (y1 - y0) * 0.8                          # the box has descenders in it
            items.append(f'#H({X((x0 + x1) / 2):.2f}mm, {Y(y1 - 0.08 * (y1 - y0)):.2f}mm, {w * k:.2f}mm, {hh * k:.2f}mm, {body})')
        # the lines: an entry begins at its first paragraph (the ground truth: at the line its first part begins
        # on, counted through the column) and is set on the lines that follow until its own lines run out
        for c in cols:
            side = c['side']
            starts = gt['starts'].get(c['n'], {}) if gt else {}
            n_col = 0                                           # the column's lines so far
            for pi, par in enumerate(c['paragraphs'], 1):
                eid = f"{pg['idx']:04d}-{c['n']}-{pi:02d}"
                if not gt and eid in by_id:
                    r = by_id[eid]
                    text, regions, lines, cont = entry_lines(r, marks)
                    cur = [r['id'], lines, text, regions, 0, cont]
                picture = all(ln['text'].strip() in ('', '\ufffc') for ln in par['lines'])
                for ln in par['lines']:
                    if n_col in starts:
                        cur = list(starts[n_col])
                    n_col += 1
                    if cur is None or cur[4] >= len(cur[1]):
                        continue
                    rid, lines, text, regions, at, cont = cur
                    s, e, hyph, last = lines[at]
                    cur[4] = at = at + 1
                    seg = text[s:e].strip()
                    if not seg:
                        continue
                    ind = ln['ind']
                    if at == 1 and cont:                       # a continuation line taken for an entry start
                        ind = max(ind, 1)
                    if gt:                                      # the GT knows the entry starts: flush, the rest hang
                        ind = 0 if at == 1 and not cont else max(ind, 1)
                    if picture and len(seg) > 50:              # the whole paragraph in one placeholder line
                        x = col_x[side] + ind * c['indent'] * k
                        body = line_markup(text, s, e, regions, marks)
                        items.append(f'#P({x:.2f}mm, {Y(ln["base"]):.2f}mm, {(COLW - ind * c["indent"]) * k:.2f}mm, '
                                     f'{102 * k:.3f}mm, [{body}])')
                        n_lines += 1
                        continue
                    # ind 2 ("deeper") is mostly ABBYY starting a line late (an unread headword, a stain): only a
                    # short line set well inside the column keeps its own position (a verse, a formula)
                    rel = min(ind, 1) * c['indent']
                    if ind >= 2 and len(seg) <= 20:
                        rel = max(rel, min(ln['bbox'][0] - gx(ln['base']) - flush[side], COLW - 300))
                    x = col_x[side] + rel * k
                    w = (COLW - rel) * k
                    body = line_markup(text, s, e, regions, marks)
                    if hyph and not seg.endswith(('-', '¬')):
                        body += '-'
                    items.append(f'#L({x:.2f}mm, {Y(ln["base"]):.2f}mm, {w:.2f}mm, {"true" if not last else "false"}, '
                                 f'"{rid}/{at - 1}", [{body}])')
                    n_lines += 1
        if gt:
            items.append(f'#place(top + left, dx: {left:.2f}mm, dy: {ph - 9:.2f}mm, block(width: {BLOCK_W * k:.2f}mm, '
                         f'text(size: 7pt, fill: luma(110), top-edge: "ascender", bottom-edge: "descender")'
                         f'[#set par(leading: 0.3em); {gt["caption"]}]))')
        out.append('#page[\n' + '\n'.join(items) + '\n]\n')
    n_entries = len(rows)
    n_prov = sum(r['hw_source'] == 'D' for r in rows)
    note = FACS_NOTE % dict(size=size, pct=f'{scale - 1:.0%}', over='%(over)s', date=datetime.date.today().isoformat(),
                            n_entries=f'{n_entries:,}', n_pages=n_pages, n_read=f'{n_entries - n_prov:,}',
                            marks_note=(' The places where the witnesses disagree are underlined in grey.' if marks else ''))
    pre = FACS_PREAMBLE % dict(size=size, hwsize=hwsize, pw=pw, ph=ph, note=note.strip(),
                               subset_note=('complete' if not leaves else f'leaves {min(leaves)}–{max(leaves)}'),
                               date=datetime.date.today().isoformat())
    if gt:                                                      # the page alone: no title page, no note
        pre = pre[:pre.index('#page(margin: 20mm)[')]
    typ.write_text(pre + ''.join(out), encoding='utf-8')
    print(f'wrote {typ.relative_to(ROOT)}: {n_pages} pages, {n_lines} lines; page {pw:.0f} × {ph:.0f} mm, '
          f'{size} pt, scale {scale}')
    return n_lines


def compile_facsimile():
    typst = shutil.which('typst')
    if not typst:
        print('typst not found; skipping PDF')
        return
    src = FTYP.read_text(encoding='utf-8')
    # two passes: the count of condensed lines goes into the note
    for n_over in (None, 0):
        if n_over is not None:
            FTYP.write_text(src.replace('%(over)s', f'{n_over:,}'), encoding='utf-8')
            r = subprocess.run([typst, 'compile', '--font-path', str(FONTS), str(FTYP), str(FPDF)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print('typst compile failed:\n', r.stderr[:3000])
                return
            if r.stderr.strip():
                print(r.stderr.strip()[:2000])
            print('wrote', FPDF.relative_to(ROOT), f'({FPDF.stat().st_size // 1024} KB)')
            return
        FTYP.write_text(src.replace('%(over)s', '…'), encoding='utf-8')
        q = subprocess.run([typst, 'query', '--font-path', str(FONTS), str(FTYP), '<over>', '--field', 'value'],
                           capture_output=True, text=True)
        if q.returncode != 0:
            print('typst query failed:\n', q.stderr[:3000])
            return
        over = json.loads(q.stdout or '[]')
        n_over = len(over)
        worst = sorted(over, key=lambda o: -o['over'])[:8]
        print(f'condensed lines: {n_over}' + (': worst ' + ', '.join(f'{o["id"]} ×{o["over"]:.2f}' for o in worst) if over else ''))
        (DJ / 'facsimile_over.tsv').write_text('id\tline\tover\n' + ''.join(
            f'{o["id"].split("/")[0]}\t{o["id"].split("/")[1]}\t{o["over"]:.3f}\n' for o in sorted(over, key=lambda o: -o['over'])),
            encoding='utf-8')


# ---------------------------------------------------------------- the ground-truth pages as facsimile pages

GT_DIR = DJ / 'eval' / 'gt'
GT_BREAK = '¦'                          # eval/README.md: a printed line begins here inside an entry line
GT_SEP = re.compile(r'=|—|–|\s-\s|\(')   # the end of the head (as dj_eval.parse_gt has it)
GT_NOTE = ('Ground truth eval/gt/%s — %s · in grey: letters read in another copy (not in scan A), guide words not '
           'transcribed (taken from the first and last headword) · a small ? follows an uncertain reading')


def gt_leaves():
    return sorted(int(f.stem) for f in GT_DIR.glob('[0-9][0-9][0-9][0-9].txt'))


def gt_part(raw):
    """One entry line of a GT file, its '+ ' taken off -> (text, regions, cuts): the text without the markup; the
    regions ('cs' Church Slavonic type, 'o' letters read in another copy, 'q' the ? that marks an uncertain
    reading); the positions where printed lines begin."""
    text, regions, cuts, opened = '', [], [0], {}
    pair = {'}': '{', '›': '‹'}
    i = 0
    while i < len(raw):
        if raw.startswith('[?]', i):
            regions.append((len(text), len(text) + 1, 'q'))
            text += '?'
            i += 3
            continue
        ch = raw[i]
        if ch in '{‹':
            opened[ch] = len(text)
        elif ch in pair:
            if pair[ch] in opened:
                regions.append((opened.pop(pair[ch]), len(text), 'cs' if ch == '}' else 'o'))
        elif ch == GT_BREAK:
            cuts.append(len(text))
        else:
            text += ch
        i += 1
    for ch, a in opened.items():                # markup left open (gtcheck reports it): to the end of the line
        regions.append((a, len(text), 'cs' if ch == '{' else 'o'))
    return text, regions, cuts


def gt_page(leaf):
    """eval/gt/NNNN.txt -> the page's ground truth for build_facsimile: 'starts' = {column: {line of the column:
    [id, lines, text, regions, 0, cont]}} (an entry part and its printed lines as entry_lines gives them, from the
    GT's line markers — dj_inspect.py gtlines), 'count' = the printed lines per column, 'guides' and 'caption' as
    markup."""
    raw = (GT_DIR / f'{leaf:04d}.txt').read_text(encoding='utf-8').splitlines()
    cols, n = {}, None
    for i, line in enumerate(raw, 1):
        if line.startswith('@ col'):
            n = int(line.split()[2])
            cols[n] = []
        elif line.strip() and not line.startswith(('#', '@')) and n is not None:
            cont = line.startswith('+ ')
            cols[n].append((i, cont, line[2:] if cont else line))
    order = [(n, part) for n in sorted(cols) for part in cols[n]]
    # the page's last entry goes on over the page when the next page does not begin with an entry of its own
    over = not any(r['id'] == f'{leaf + 1:04d}-1-01' for r in load('all', {leaf + 1}))
    starts, count, heads = {}, {}, []
    for k, (n, (lno, cont, body)) in enumerate(order):
        text, regions, cuts = gt_part(body)
        going_on = order[k + 1][1][1] if k + 1 < len(order) else over
        head_end = 0
        if not cont:                            # CS type in the head is the headword's, after it the text's
            head_end = next((m.start() for m in GT_SEP.finditer(text)
                             if not any(a <= m.start() < b for a, b, kind in regions if kind == 'cs')), len(text))
            heads.append(text[:head_end])
        regions = [(a, b, 'cst' if kind == 'cs' and a >= head_end else kind) for a, b, kind in regions]
        lines = []
        for j, a in enumerate(cuts):
            b = cuts[j + 1] if j + 1 < len(cuts) else len(text)
            hyph = 0 < b < len(text) and text[b - 1].isalpha() and text[b].isalpha()   # a word broken at the line end
            lines.append((a, b, hyph, j == len(cuts) - 1 and not going_on))
        starts.setdefault(n, {})[count.get(n, 0)] = [f'gt{leaf:04d}:{lno}', lines, text, regions, 0, cont]
        count[n] = count.get(n, 0) + len(lines)
    m = re.search(r'guide words: (.+?) \| (.+?)$', raw[0])
    if m:                                       # as transcribed: {…} is the Church Slavonic type
        guides = [''.join(f'#cs[{esc(t[1:-1])}];' if t.startswith('{') else esc(t)
                          for t in re.split(r'(\{[^}]*\})', x) if t) for x in m.groups()]
    else:
        guides = [f'#text(fill: luma(120))[#cs[{esc(guide_of(h))}]]' if h else '' for h in (heads[:1] + heads[-1:])]
    status = next((x.split(':', 1)[1] for x in raw if x.startswith('# status:')), 'status unknown')
    status = re.split(r'[(,]', status)[0].strip().rstrip(';')
    return dict(starts=starts, count=count, guides=guides, caption=esc(GT_NOTE % (f'{leaf:04d}.txt', status)))


def build_gt(leaves, size, scale, hwsize, pdf=True):
    """--gt: each ground-truth page as its own facsimile page, djachenko/facsimile-P<printed page>.pdf, to read
    the transcription against the scan (the .typ in djachenko/cache/)."""
    typst = shutil.which('typst')
    for leaf in leaves or gt_leaves():
        gt = gt_page(leaf)
        pg = json.loads((OCR / f'{leaf:04d}.json').read_text(encoding='utf-8'))
        for c in pg['columns']:
            n_a = sum(len(par['lines']) for par in c['paragraphs'])
            if gt['count'].get(c['n'], 0) != n_a:
                print(f'  leaf {leaf}, column {c["n"]}: {gt["count"].get(c["n"], 0)} lines in the GT, {n_a} in scan A '
                      f'— the lines after the first difference are misplaced (dj_inspect.py gtlines {leaf} --force)')
        p = int(pg['printed_page'])
        typ, out = DJ / 'cache' / f'facsimile-P{p:04d}.typ', DJ / f'facsimile-P{p:04d}.pdf'
        typ.parent.mkdir(exist_ok=True)
        build_facsimile(load('all', {leaf}), False, size, scale, hwsize, {leaf}, gt=gt, typ=typ)
        if not pdf or not typst:
            continue
        r = subprocess.run([typst, 'compile', '--font-path', str(FONTS), str(typ), str(out)], capture_output=True,
                           text=True)
        if r.returncode != 0:
            print('typst compile failed:\n', r.stderr[:3000])
            continue
        print('wrote', out.relative_to(ROOT), f'({out.stat().st_size // 1024} KB)')


def parse_ranges(s):
    out = set()
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-')
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--subset', default='all', choices=('all', 'links'))
    ap.add_argument('--leaves', help='leaves of scan A to include, e.g. 38-60,150')
    ap.add_argument('--no-refs', action='store_true', help='no grey page references')
    ap.add_argument('--marks', action='store_true', help='underline the disputed spans')
    ap.add_argument('--no-pdf', action='store_true')
    ap.add_argument('--size', type=float, default=10.0, help='text size in pt')
    ap.add_argument('--leading', type=float, default=0.56, help='leading in em')
    ap.add_argument('--hwsize', type=float, default=None, help='headword size in pt (default 1.12 × size)')
    ap.add_argument('--facsimile', action='store_true', help='line for line as the 1900 edition (Rev. 6)')
    ap.add_argument('--scale', type=float, default=1.08, help='facsimile: enlargement of the page')
    ap.add_argument('--gt', nargs='*', type=int, metavar='LEAF',
                    help='facsimile pages of the ground truth (eval/gt/), all or these leaves: facsimile-P<page>.pdf')
    a = ap.parse_args()
    fetch_fonts()
    if a.gt is not None:
        size = a.size if a.size != 10.0 else 12.0
        build_gt(a.gt, size, a.scale, a.hwsize or round(size * 1.12, 1), not a.no_pdf)
        return
    if a.facsimile:
        size = a.size if a.size != 10.0 else 12.0
        rows = load('all', parse_ranges(a.leaves) if a.leaves else None)
        build_facsimile(rows, a.marks, size, a.scale, a.hwsize or round(size * 1.12, 1), parse_ranges(a.leaves) if a.leaves else None)
        if not a.no_pdf:
            compile_facsimile()
        return
    rows = load(a.subset, parse_ranges(a.leaves) if a.leaves else None)
    build(rows, not a.no_refs, a.marks, a.size, a.leading, a.hwsize or 11.2, a.subset)
    print(f'{len(rows)} entries -> {TYP.relative_to(ROOT)} ({TYP.stat().st_size // 1024} KB)')
    if not a.no_pdf:
        compile_pdf()


if __name__ == '__main__':
    main()
