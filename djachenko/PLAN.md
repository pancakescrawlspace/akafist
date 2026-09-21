# Plan: a structured digital edition of Дьяченко's Полный церковнославянский словарь (1900)

Goal: a machine-readable, proofread-where-it-matters copy of Г. Дьяченко, *Полный церковнославянский словарь* (Москва 1900;
~30,000 entries, ~1,120 two-column pages + XXXVIII pages of front matter), and from it a Typst/PDF rendition in the
style of `akathist/dictionary/dictionary.typ`. The book is public domain (published 1900, author †1903).

Revision 2 (2026-09-19, after Phase 1 investigation): source scan chosen; an existing ABBYY OCR layer with word
coordinates and formatting was found, which reshapes Phases 2–4 (see "Findings" and the phases themselves).
Revision 3 (2026-09-19, after Phase 3a): the book has a large supplement (a second alphabetical sequence), an errata
table and scan defects (left margins cut off on 242 pages); Phases 2–6 amended accordingly (marked "Rev. 3").
Revision 4 (2026-09-19, session 2): other copies surveyed (`COPIES.md`); a second independent witness (the 1993
reprint, margins intact, with its own OCR) downloaded; Phase 2 gets a triangulation question (marked "Rev. 4").
Revision 5 (2026-09-19, session 3, after the Phase 2 measurements — `eval/RESULTS.md`): the route is decided. The
definition text and the Greek come from witness D's text layer (Google, Cornell copy: 1.5 % CER against ABBYY's
3.8 % on A), voted with B and A; the entry segmentation stays A's geometry (99 % recall, 100 % precision on ordinary
pages); the headwords are read from crops by a vision model (25/25 on a test page, against ~48 % for any OCR). Scan A
also lacks the *right* margin on 313 right-hand pages, so half the pages are incomplete in A. Phase 3b rewritten
(marked "Rev. 5").
Revision 6 (2026-09-20, session 5): Phase 6 gets a second target, a **line-for-line facsimile** — every printed
line, column and page of the rendition the same as in the book. Its two preconditions were checked: the four
witnesses are one typesetting (verified line for line over the whole book, `dj_inspect.py linecheck`, COPIES.md),
and the line structure is in the repository (`ocr/*.json`); what is missing is the mapping of the voted text onto
the lines, and the type is bigger than the 10 pt now used. Phase 6 amended (marked "Rev. 6").

Revision 7 (2026-09-21, session 6): **the entry segmentation is no longer A's alone.** A lemma was found missing
from the rendition (`Аполинъ` inside `Апокрифы`, p. 20): ABBYY had read only the right half of six lines under a
stain, so the flush line measured as indented and no entry began there. Witnesses C and D have both margins on
every page — C's narrowest outer margin is 27 pt, and no line of it touches an image edge, where A's margin is cut
on 551 pages — and the four are one typesetting, so their printed indentation says where the entries begin. A new
step, **Phase 3b step 1c, `tools/dj_seg.py`**, reads it line by line and writes `segmentation.tsv`, which
`dj_abbyy.py` applies; 232 entry starts were added and 636 withdrawn, and `guessed` paragraphs fell from 3,197 to
244. Phases 3a, 3b and 6 amended (marked "Rev. 7").

This plan is written to be executed over several sessions. Every phase has a *Definition of done* and a *Resume*
paragraph; all state lives in files under `djachenko/` so that a new session can read `PROGRESS.md`, the manifest and
this plan and continue without any conversational memory.

## Findings that shape the plan (verified 2026-09-19)

- No transcribed text edition exists. Azbyka.ru (`/otechnik/Grigorij_Djachenko/polnyj-tserkovnoslavyanskij-slovar/`,
  38 per-letter pages) and dhonorare.ru (`/dict/dyachenko/`) serve **page images** only. Wikisource has an index
  (`Индекс:Полный церковнославянский словарь (Протоиерей Г.Дьяченко).djvu`) with **no OCR layer** and two transcribed
  pages. So the text must be produced from a scan.
- **Chosen scan: archive.org item `20200215_20200215_0856`** (1900 edition; 1,159 leaves at 4252×6520 px = 600 ppi;
  the same scan as item `dyachenkos-dictionary-church-slavonic`). Rejected: Wikimedia Commons PDF and dhonorare.ru
  (816×1156 px, ~100 ppi), Azbyka PNGs (1119×1755 px of the 2004 reprint, 1,150 requests), archive.org
  `polnyjtserkovnoslavjanskijslovarsovne27` (OCR layer without ѣ/і) and `B-001-027-578-ALL` (182 ppi).
- The chosen item carries archive.org's own OCR, made with **ABBYY FineReader with pre-reform Russian**: the plain text
  (`_djvu.txt`, 8.5 MB) has 51,852 ѣ and 65,981 і, and reads well for the definition text
  ("крѣпленія силъ молящихся, ибо тотчасъ"). It fails, as expected, on the **Church Slavonic headwords** ("Абіе" →
  "Яеіе") and on **Greek** ("παραχρῆμα" → "тгарау р7][ла"). About 24,500 "=" signs survive (≈ number of entries).
- The same OCR is available as ABBYY XML (`_abbyy.gz`, 79 MB: characters with coordinates *and* `<formatting>` with
  font size / bold / italic), DjVu XML (`_djvu.xml`, 62 MB: words with coordinates) and hOCR (127 MB). Formatting and
  geometry make it possible to find headwords (different typeface, at the hanging-indent start of a paragraph, before
  "=") without reading the text, and to segment entries geometrically.
- `_page_numbers.json` maps leaf → printed page number with 98 % confidence (leaf 150 = p. 113, verified against the
  image); `_scandata.xml` gives leaf sizes. Page images can also be fetched singly at 300 ppi via
  `https://archive.org/download/<item>/page/n<leaf>.jpg` (used for spot checks; the bulk comes from the JP2 zip).
- Typography of the original (seen on p. 113): two columns; headwords in Church Slavonic type with titla, then "=" and
  the definition in pre-reform civil type; italic for quotations and source names; Greek, Hebrew, Latin in etymologies;
  biblical references in parentheses; guide words ("Вѣр—", "Вѣк—") in the head, page number centred, signature and the
  running title "Церк.-славян. словарь свящ. Г. Дьяченко." in the foot.
- Azbyka's robots.txt disallows automated fetching of `.epub`, `.txt`, `.djvu` files; not relevant now that archive.org
  is the source. All fetching uses a descriptive User-Agent, sequentially, with resume and checksum verification.

## Layout of `djachenko/`

```
djachenko/
  PLAN.md          this file
  PROGRESS.md      running log: date, what was done, "NEXT:" line (the first thing a new session reads)
  SOURCE.md        which scan was used, URL, checksums, page count, leaf → printed-page mapping
  COPIES.md        every other copy/scan located (witnesses A, B, C), with what was checked and what could not be
  manifest.tsv     one row per leaf: idx, printed_page, section (front/main/blank/supplement/back), letter(s) on
                   the page (from the table of contents), status, notes
                   status ∈ {new, image, ocr, parsed, checked}
  scan/            the archive.org files: metadata, OCR layers, JP2 zip (git-ignored; large);
                   scan/reprint1993/ witness B (1993 reprint DjVu + OCR), `dj_fetch.py --reprint`;
                   scan/google/ witnesses C and D (Google Books PDFs of the Indiana and Cornell copies)
  pages/           NNNN.jpg, one 300 ppi working image per leaf; pages/jp2/ the 600 ppi originals (git-ignored)
  ocr/             per-page JSON built from the ABBYY layer plus the headword/Greek passes (Phase 3 schema) — committed;
                   ocr/report.tsv: per-page statistics and warnings of the last dj_abbyy.py run
  entries.tsv      the structured dictionary (Phase 4 output) — committed; FLAGS.md its validation report
  eval/            ground-truth pages and evaluation results (Phase 2)
  cache/           rendered D pages, entry crops, contact sheets (Phase 3b step 2; git-ignored, rebuilt on demand)
  heads_batches.tsv  Message Batches submitted by `dj_heads.py read --batch`, with their status (committed)
  djachenko.typ, djachenko.pdf   Typst rendition (Phase 6; generated, 9 + 20 MB — git-ignored, rebuilt with dj_build.py)
  segmentation.tsv where every printed line begins an entry or continues one, read off witnesses C and D
                   (Phase 3b step 1c Rev. 7, `dj_seg.py`; committed — `dj_abbyy.py` needs it, the scans it does not)
  facsimile.typ, facsimile.pdf   the line-for-line facsimile (Phase 6 Rev. 6; `dj_build.py --facsimile`; git-ignored),
                   facsimile_over.tsv the lines it had to condense
  facsimile-P0008.pdf …  each ground-truth page set the same way from its GT text, to proofread it against the
                   scan (`dj_build.py --gt`, session 6; git-ignored; eval/README.md)
  fonts/           Ponomar Unicode, Old Standard TT (OFL; fetched by dj_build.py; git-ignored)
tools/
  dj_fetch.py      Phase 1: download scan + OCR layers, extract page images, write manifest (exists)
  dj_abbyy.py      Phase 3a: ABBYY XML → ocr/NNNN.json (text, geometry, formatting), idempotent (exists)
  dj_heads.py      Phase 3b (Rev. 5): `text` — per page, align witness D's text to A's segmentation, vote with B, A
                   and C (exists, run); `crops`/`read`/`collect`/`sheet`/`enter`/`check` — the headwords from
                   crops, by the API or by hand (exists, not yet run); idempotent and resumable throughout
  dj_seg.py        Phase 3b step 1c (Rev. 7): the printed indentation of C and D, line by line → segmentation.tsv,
                   which dj_abbyy.py applies — the authority on where an entry begins (exists, run)
  dj_witness.py    shared: witness word boxes and page mapping, reading order, normalisation, alignment,
                   `indent_levels` — a witness's indentation levels, deskewed (Rev. 7) (exists)
  dj_eval.py       Phase 2: CER of the OCR candidates against the ground truth, per zone; triangulation (exists)
  dj_inspect.py    helpers: dump/overlay a page, crop lines, find a word in all four witnesses side by side,
                   sanity checks of the ground truth and of the entry starts; `linecheck` — do the witnesses break
                   their lines alike (Rev. 6; result in eval/linecheck.tsv); `gtlines` — mark the printed lines in
                   the ground truth (`¦`, session 6); `counts` — pages short of lines against A (exists)
  dj_parse.py      Phase 4: ocr/*.json → entries.tsv + FLAGS.md (exists; headwords provisional until step 2 runs)
  dj_link.py       Phase 5: cross-reference entries.tsv with akathist/dictionary/dictionary.psv lemmas → links.tsv (exists)
  dj_build.py      Phase 6: entries.tsv → djachenko.typ (+ PDF via typst), in the original's layout; --facsimile
                   (Rev. 6) → facsimile.typ/.pdf, every line, column and page as in the book; --gt → the same for
                   each ground-truth page, facsimile-P<page>.pdf (exists)
```

`.gitignore` gets `djachenko/scan/` and `djachenko/pages/`. Everything else is committed, in small batches, so that a
session can end at any point without losing work.

## Phase 0 — Decisions (one short session; needs the user)

Decide and record in `PROGRESS.md`:

1. **Scope of the Typst output.** (a) the whole dictionary (~30,000 entries; at the current two-column A5 style this is
   in the order of 900–1,100 pages), or (b) a subset: the entries for the ~700 lemmas of the akathist dictionary plus
   whatever else is wanted, as an appendix or companion volume to `akathist/dictionary/dictionary.pdf`. The pipeline is the same
   up to Phase 5 either way; only Phase 6 differs. Default: build the full `entries.tsv`, render (b) first, (a) when
   proofreading has progressed.
2. **Headword encoding.** Store headwords in *civil pre-reform script* (keeping ѣ, і, ѳ, ѵ, final ъ, but no titla or
   superscript letters), plus a *normalised modern key* (ѣ→е, і→и, ѳ→ф, ѵ→и or в as pronounced, ъ# dropped) for lookup.
   Rationale: every OCR route can produce this reliably, PT Serif renders it, and lookup from the akathist dictionary
   works. The exact Church Slavonic form (titla etc.) can be added later as a separate column if wanted; rendering it
   needs a Slavonic font (Ponomar Unicode, OFL).
3. **Proofreading policy.** Nothing will be proofread completely by machine or by me. Priority order: (i) entries hit
   by the akathist lemma list; (ii) entries in any subset chosen for the PDF; (iii) the rest as time allows. The
   `status` column of `entries.tsv` records this; the PDF marks unchecked entries (e.g. a small ° after the headword).
4. **OCR route** is decided in Phase 2 by measurement, not now.

*Definition of done:* the four decisions are written in `PROGRESS.md`.

## Phase 1 — Acquire the scan and page images (one session, mostly unattended) — DONE

`tools/dj_fetch.py` does all of it, idempotently: `--meta` (files.xml, scandata, page_numbers.json, djvu.txt,
djvu.xml, abbyy.gz; MD5-verified), `--jp2` (the 2.1 GB zip, resumable), `--extract` (JP2s into `pages/jp2/`),
`--convert` (600 ppi JP2 → 300 ppi JPEG `pages/NNNN.jpg`, quality 88, parallel), `--manifest` (from scandata +
page_numbers.json; keeps hand corrections already in the file).

Then by hand, once: mark the sections in `manifest.tsv` — front matter (Roman-numbered pages), the first leaf of each
letter (from the guide words / the large initials; the OCR text of each first page will contain the letter heading),
and the supplement — and record the leaf→printed offset(s) in `SOURCE.md`.

*Definition of done:* `scan/` holds the verified files, `pages/` has 1,159 JPEGs, every manifest row has status `image`
and a section, `SOURCE.md` is filled in. Committed: `SOURCE.md`, `manifest.tsv`, `.gitignore`, `tools/dj_fetch.py`.
*Resume:* run `python3 tools/dj_fetch.py --all`; it only does what is missing. Then fill in sections if still empty.

## Phase 2 — Measure what the ABBYY layer gives and choose the route for the rest (one to two sessions) — DONE

Rev. 5: done 2026-09-19 (sessions 2–3); the numbers and the route are in `eval/RESULTS.md`. In short: definitions
from D (1.5 % CER) voted with B and A (~1 % expected, disagreements flagged); segmentation from A's geometry; headwords
by vision on crops; Greek from D (2 % strict CER, ~14,700 words in the book); the cut margins (left on 242 even
leaves, right on 313 odd leaves) supplied by D. The questions below are kept for the record.

Ground truth: 6 pages chosen to be representative — an ordinary page from А, one from the middle (П or С), one from a
short late letter (Ѣ or Ѵ), one dense in Greek/Hebrew etymology, one from the supplement, one with poor print quality.
Rev. 3: make the supplement page one with a cut-off left margin (e.g. leaf 1124 = p. 1087), since 242 pages are like
that, and include one page with a long article (e.g. leaf 465 = p. 428) — segmentation behaves differently there.
Transcribe them carefully by hand into `eval/gt/NNNN.txt` (one entry per paragraph, `headword = definition`, column
breaks marked). This is slow (~30–45 min per page) but is the only way to compare candidates honestly; the user may
prefer to check these transcriptions.

Questions to answer with numbers (`tools/dj_eval.py gt.txt candidate.txt` → CER/WER overall, headwords only,
definitions only, Greek only):

1. **Definition text from the ABBYY layer** — is its CER low enough to use as is (with a proofreading pass only for
   linked entries)? Expected yes; if not, Tesseract 5 (`rus`, `script/Cyrillic`) on the 300 ppi JPEGs is the fallback
   to test, and the vision route the last resort.
2. **Headword detection** — can headwords be located from geometry/formatting alone (ABBYY `<formatting>` font,
   paragraph start with hanging indent, position before "=")? Measure recall/precision against the ground truth.
3. **Headword transcription** — candidates: (a) a vision model reading a *column image* and returning only the list of
   headwords in civil pre-reform script (small output, ~1,150 pages × 2 columns); (b) a vision model reading *headword
   crops* built from the geometry of (2) — tiny images, easiest to verify, but ~30,000 calls unless batched into
   contact sheets of ~40 crops; (c) Tesseract with any Church Slavonic model that can be found, on the crops; (d)
   ABBYY's own garbled reading mapped back with a Slavonic-to-civil confusion table — probably hopeless, but cheap to
   measure. Score CER on headwords only.
4. **Greek** — how much Greek is there (count of parenthesised runs the ABBYY layer garbles), and is it worth a pass
   over all entries or only over the linked subset? Candidate: vision on line crops where ABBYY confidence is low.
5. Rev. 3: **Entry segmentation** of Phase 3a (`entries_hint` = hanging paragraphs) — precision/recall against the
   ground truth, separately for ordinary pages and for pages with a cut-off margin (paragraphs marked `guessed`).
6. Rev. 3: **Cut-off headwords** — on the 242 pages with a cut-off left margin the first letter(s) of many headwords
   are not in the image. Answered in session 2 (user's decision: triangulate with other copies): three more copies
   with intact margins are on disk (`COPIES.md`): B (1993 reprint, ~237 ppi bilevel), C (Indiana's reprint, Google,
   600 ppi bilevel) and D (Cornell's original, Google, 600 ppi bilevel, complete). Read the cut headwords in D (then
   C, B), with the alphabetical context as a check.
7. Rev. 4: **Triangulation** — the witnesses bring their own OCR: B (DjVu text layer; archive.org's ABBYY XML), C
   and D (Google's text layer in the PDFs). Measure their CER on the ground truth next to A's, and how often they
   disagree where one is wrong: where independent readings agree, the text can probably be trusted without
   proofreading; where they disagree, look at the images (A colour 600 ppi, D bilevel 600 ppi).

*Definition of done:* `eval/RESULTS.md` records the numbers and names the route for definitions, headwords and Greek;
`PROGRESS.md` says so.
*Resume:* ground-truth files and candidate outputs are on disk; continue with whichever candidates lack output.

## Phase 3 — Build the per-page OCR files (3a: one run; 3b: several sessions)

**3a. `tools/dj_abbyy.py`** converts the ABBYY XML into one `ocr/NNNN.json` per leaf: blocks → paragraphs → lines →
words with bounding boxes, character confidence, and formatting (font size, bold, italic). This is a single
deterministic run over all 1,159 leaves; no network, no tokens. It also records the guide words, page number and
column boundaries per page. — **DONE** (2026-09-19; 6 s for the whole book). The authoritative JSON schema is the
docstring of `tools/dj_abbyy.py` (it supersedes the sketch below: columns carry side a/b and band, paragraphs are
geometric — a new one at every flush line — and `entries_hint` carries ABBYY's reading and the headword's box).
How it works: the column rule (a separator on nearly every page) gives the gutter and removes the skew; lines across
it are split; header (page number, guide words, running title "Прибавленіе."), footer (signature line), letter
initials (big type or pictures on the rule, or a 250–900 px gap across both columns where ABBYY recorded nothing) and
specks (gutter, margin dust read as "п", ",", "„") are set aside; flush vs. indented is fitted per side relative to
the rule with a strong prior (right column: text starts 62 px right of the rule), checked against the text (entry
starts contain "=" in 82 % of cases, continuation lines in 2 %); on pages whose left margin is cut off, position and
text features are combined (naive Bayes) and the paragraphs marked `guessed`. **Rev. 7:** where
`segmentation.tsv` has a line, that decision is overruled by witnesses C and D (step 1c below); `dj_abbyy.py`
reads the file and records per page how often it did so (`seg`), and per paragraph whether the start is the
witnesses' and not A's (`seg: "CD"`) or one no witness could reach (`seg: "A"`). Result: 24,845 entry candidates
in main + supplement (22,575 with "=" in their first two lines; 232 starts added and 636 withdrawn against A's own
geometry; `guessed` down from 3,197 to 244, since a witness now decides most of the cut-margin pages; the page
footer looked for only on the pages that carry it, p ≡ 1 mod 16, after it had filed article lines as footer
on four pages — MISSING_HEADWORDS.md);
`manifest.tsv` has section and letters; `ocr/report.tsv` the per-page statistics and warnings. The book's
"~30,000 entries" is a round figure: the "=" count (24,483) and the candidates agree on ~25,000.

**3b. `tools/dj_heads.py --pages A-B`** (Rev. 5, after Phase 2) builds the page text from the witnesses on top of
A's segmentation, in three steps per page, each idempotent and each recorded in the page JSON:

1. *Text.* — **DONE** (session 3; `dj_heads.py`, shared code in `dj_witness.py`; eval/RESULTS.md addendum).
   Per column side: D's reading order from its word boxes, aligned to A's text, cut at A's paragraph starts snapped
   to D's line starts; per-character vote D/B/A with C as the check (the rules and their evidence: `VOTE.md`);
   per paragraph `text_d`, `text_merged`,
   `disputed` spans, `fixed`, `d_cut`, `d_line`; per page a `witness` block. Definitions 1.0 % CER on the GT
   (D alone 1.5 %), 85 % of the remaining errors inside the disputed spans. All 1,119 pages done (62 s; resumable;
   `dj_abbyy.py` carries the texts over on regeneration).
1c. *Where the entries begin* (Rev. 7, session 6; `tools/dj_seg.py`). An entry begins at a flush line and runs on
   at the hanging indent, so the segmentation is a matter of geometry — but of A's geometry it cannot be, because
   A's left margin is cut on 242 pages, its right on 313, and even on an intact page ABBYY drops the left half of
   a line under a stain and the flush line measures as indented (p. 20: `Аполинъ` vanished into `Апокрифы`, which
   is what sent this session looking). Measured over the book: witness C's narrowest outer margin is 27 pt and no
   line of it touches an image edge; D's is 0.1 pt and 148 sides have a line at the edge, and D's flag rate rises
   from 2.9 % to 10.5 % as its margin narrows — so C is the better geometric witness and the two are voted.
   Per column side: the voted text of step 1 is aligned to the witness, every printed line of A (`breaks`) carried
   over and snapped to a line start of the witness, and that line's indentation level read off
   `dj_witness.indent_levels` — which deskews the column by folding the left edges modulo the hanging indent,
   since the Google columns drift by up to 13 pt, more than the 11 pt indent itself. Which of a column's two
   levels is the flush one is the one thing the geometry cannot say (a column may lie wholly inside one long
   article, or hold nothing but one-line entries): A settles that, one yes/no per column decided by ~50 lines it
   reads right 99 % of the time. C and D then vote line by line. Coverage 96 % of the 124,497 printed lines, the
   two agreeing on 99.8 % of those; the result is `segmentation.tsv`, and `dj_abbyy.py` applies it.
   Committed, because the file is the witnesses' reading and not a diff: it does not depend on what A made of the
   page, so the two scripts can be re-run in either order, and a rebuild without the Google PDFs (git does not
   hold them) still gets the entry boundaries right. Run it after `dj_heads.py text` (it needs `text_merged` and
   `breaks`), then `dj_abbyy.py` and `dj_heads.py text` again for the pages whose paragraphs moved; one pass
   reaches the fixed point.

2. *Headwords.* — pipeline **built** (session 3), reading not yet run. For every `entries_hint` a crop of the start of
   the entry's first line, from A's 600 ppi image or from D's rendered page on the 242 left-cut pages (via `d_line`),
   at 400 ppi (`cache/crops/`). `dj_heads.py read` sends one request per page with the crops as separate images
   (~110 tokens each, ~3.5 M image tokens for the book) after a cached few-shot prefix of seven GT examples, and
   stores the JSON answer in `entries_hint[]`: `headword` (GT convention: letters as printed, no diacritics; null
   for a line that is not an entry start), `headword_source`, `check` (`confirmed` when D, C, B or A contain the
   same reading at norm level, else `disputed`, `no_entry`), `confirmed_by`. `read --batch` uses Message Batches
   (half price) and records the batch ids in `heads_batches.tsv` for `collect` in a later session; `sheet`/`enter`
   do the same by hand (tested on leaf 341: 25/25, 23 confirmed, the 2 disputed are the ones needing a second
   look). `dj_eval.py --heads` scores the readings on the GT pages. `headword_civil` is derived in Phase 4.
   Open decision (user): API (needs `pip install anthropic` and ANTHROPIC_API_KEY; cost = ~$17 of images + the
   model's output, which the effort level governs — measure on the six GT pages at effort low and medium first)
   or interactive sessions (~1,700 sheets of 15).
3. *Greek.* Greek runs come with D's text; where C disagrees on a Greek run, mark it `disputed`.
3a. *The crops themselves* (added session 4, `tools/dj_crops.py`): before the reading pass, every headword is
   located in all four witnesses and cropped once, into `djachenko/headwords.tsv` (the boxes, one row per entry
   and witness) and `djachenko/crops/<W>/NNNN.png` (one strip per page and witness, the page's headwords stacked;
   the index gives each headword's rows inside the strip). The index is committed; the crops are not — 134 MB
   that follow from the index and the scans, remade by `dj_crops.py crops` in about half an hour (the account's
   Git LFS budget is 80 % spent, see PROGRESS.md). With the crops in hand a headword can be compared across the
   four copies without touching the scans. Rev. 7 (session 6): B's, C's and D's boxes are cut as far along
   the line as the entry's head in entries.tsv is long (the user's proposal), C's and D's made full height,
   and B's flipped about the true page height — before, B's crops were cut up to 710 px too high and C's and
   D's ran into the definition (docstring of dj_crops.py). `index` therefore runs after dj_parse.py.
4. *The Old Church Slavonic citation type* (added session 4). Besides the civil text and the Church Slavonic
   headwords, the book has a third text class: quotations from Old Russian manuscripts set in a heavy uncial face
   (e.g. p. 223 "нноѹадыи вм. єдиноѹадыи", p. 1087). No OCR reads it: Google renders its letters as capitals
   ("ННОУЛДЫН") or as Greek look-alikes, ABBYY as noise, and A and B do not agree, so the vote cannot repair it.
   Entries that show it are flagged `caps` (184) and `script` (515) by `dj_parse.py` — an over-estimate of the
   spans and an under-estimate of the entries, since a citation may also come out as plausible lowercase noise.
   Route: read these spans in the same vision pass as the headwords (crops of the lines instead of the entry
   start), since it is the same problem — type that only a reader can decode. Until then the text of those spans
   is wrong and must not be trusted; a cosmetic lowercasing was considered and rejected, because it would hide an
   unread passage behind a plausible-looking word.

Manifest status becomes `ocr` when a page has all three. Batches sized to a session; after every batch:
`dj_parse.py --check`, a line in `PROGRESS.md`, commit.

Per-page JSON schema (engine-independent):

```
{ "idx": 150, "printed_page": 113, "guide_words": ["Вѣр—", "Вѣк—"],
  "columns": [ { "n": 1, "bbox": [x0,y0,x1,y1],
                 "paragraphs": [ { "bbox": [...], "hanging": true,
                                   "lines": [ { "bbox": [...], "text": "…", "words": [ {"text": "…", "bbox": [...], "conf": 0.93, "font": "cs|civil|italic|greek?"} ] } ] } ] } ],
  "entries_hint": [ { "col": 1, "para": 3, "headword": "Абіе", "headword_source": "vision|tesseract|abbyy", "conf": 0.9 } ],
  "warnings": ["…"] }
```

*Definition of done:* every manifest row has status ≥ `ocr` (3a done for all, 3b done for all).
*Resume:* run `dj_abbyy.py` (fast, idempotent), then `dj_heads.py text`, then `dj_seg.py`, then those two again
(Rev. 7 — the order is in step 1c and in the README's rebuild recipe); `PROGRESS.md` says which batch is next.

## Phase 4 — Structure into entries (one session to write, then re-run after every batch)

Rev. 5 (session 3): `tools/dj_parse.py` exists and runs (1.5 s) — see its docstring for the actual columns
(`id part page col headword headword_civil headword_key hw_source sep gram definition disputed status flags`) and
flags; `FLAGS.md` is its report. It builds on the Phase 3b texts (`text_merged`) and takes the headwords from step 2
where they exist, provisionally from D's text otherwise (`hw_provisional`). Still to do in this phase: the errata
table (`errata.tsv`, below) and the manifest status; re-run after every step-2 batch. The original design follows.

`tools/dj_parse.py` turns `ocr/*.json` into `entries.tsv`:

```
id  headword_civil  headword_key  gram  definition  page  column  status  flags
```

- Segmentation: primarily geometric — an entry starts at a paragraph whose first line begins at the column's left edge
  while continuation lines are indented (hanging indent), confirmed by the "=" after the headword (Дьяченко's
  convention); the two signals are cross-checked and disagreements flagged. Continuation lines are joined; hyphenation
  at line and column ends repaired; cross-references ("см.") kept as text.
- `gram` = the grammatical/etymological tag immediately after `=` when present (e.g. "(греч.)", "гл.").
- `headword_key` = normalised modern spelling (Phase 0.2).
- Validation report: headwords must be (nearly) alphabetical within a page and across pages — every violation is a
  segmentation or OCR error and is written to `flags`; pages whose entry count is far from the neighbours' are flagged;
  unbalanced parentheses flagged.
- `status` starts as `raw`.
- Rev. 3: the main part (pp. 1–863) and the supplement (pp. 865–1120) are two separate alphabetical sequences;
  validate the order within each. Supplement entries add to or correct main entries: add a column `part`
  (main/supplement) and, in Phase 5, link a supplement entry to the main entry with the same headword.
- Rev. 3: apply Дьяченко's own errata table (front matter pp. XXXIV–XXXVIII, leaves 32–36; columns: page, line
  counted from the top or bottom, column left/right, "напечатано", "слѣдуетъ читать"; a few hundred rows, much of it
  Greek) — transcribe it once into `djachenko/errata.tsv` and apply it to `entries.tsv`, flagging each corrected
  entry. **In progress** (session 4): leaf 32 transcribed, 43 rows, pp. 5–79; leaves 33–36 to go, ~190 rows.

*Definition of done:* `entries.tsv` covers all OCR'd pages; the validation report is in `PROGRESS.md`; flagged entries
listed in `djachenko/FLAGS.md` (regenerated each run).
*Resume:* the script is deterministic; just re-run it.

## Phase 5 — Cross-reference and targeted proofreading (several short sessions)

1. `tools/dj_link.py`: for every lemma of `akathist/dictionary/dictionary.psv`, find the matching Дьяченко entries by
   `headword_key` (with a small set of fallbacks: infinitive ↔ 1 sg. verb forms, ъ/ь variants, ѵ→и/в). Output
   `djachenko/links.tsv` (lemma → entry ids, match type) and a list of akathist lemmas with no match, to be resolved by
   hand. — Rev. 5: **exists** (session 3); with the provisional headwords it links 243 of 703 lemmas (exact 229,
   verb 11, soft 3); the rest waits for the step-2 headwords. Re-run after every step-2 batch.
2. Proofread the linked entries against the page image (open `pages/NNNN.png`, fix the text in `entries.tsv`, set
   `status=checked`). Estimate: ~500–600 entries, a few minutes each — spread over sessions; `PROGRESS.md` records the
   last checked id.
3. Optionally add a `dj` column to `akathist/dictionary/dictionary.psv` with the entry ids, so `dictionary.md/.typ` can show
   "Дьяченко s.v. …".

*Definition of done:* every akathist lemma is linked or explicitly marked "not in Дьяченко"; linked entries `checked`.

## Phase 6 — Typst rendition (one session for the script; re-run at will)

Rev. 5 (session 3, user's decision): the rendition follows the **original's layout**, not the akathist dictionary's
style. `tools/dj_build.py [--subset all|links] [--leaves A-B] [--marks] [--no-refs]` writes `djachenko/djachenko.typ`
and compiles it (whole book: 25,362 entries → ~1,000 A4 pages, 5 s, 20 MB): the original's text block (169 × 249
mm, measured on scan A) on A4, two columns with a rule, 12.6 pt line pitch, hanging indent 4.9 mm, page number over a
short double rule, guide words in Church Slavonic type, the running title with the signature number every sixteenth
page; letter initials in the column. Fonts (OFL, fetched into `djachenko/fonts/`, git-ignored): Ponomar Unicode for
the headwords (the Synodal CS typeface), Old Standard TT for the civil text and the Greek. Headwords not yet read
from the images (`hw_provisional`) are printed grey; italics are ABBYY's (carried over in Phase 3b step 1, incomplete);
a small grey ¶ with page and column of the 1900 edition ends every entry; `--marks` underlines the disputed spans.
Front matter: title page and an "About this edition" page with the status figures. Not yet: Дьяченко's own list of
abbreviations (front matter pp. XXIX–XXXIII), the "checked" mark (nothing is checked yet). — The earlier design
(akathist style, `--paper a5`) is superseded.

Front matter to include: title, bibliographic note, what "checked/unchecked" means, the encoding conventions of
Phase 0.2, and Дьяченко's own list of abbreviations (transcribed from the front matter as part of Phase 3;
Rev. 3: pp. XXIX–XXXIII = leaves 27–31, already in ocr/ as two-column text with hanging indents).

**Rev. 6 — the facsimile (decided and built 2026-09-20, session 5).** Besides the flowing rendition above, the
book is built so that every printed line, column and page is the same as in the 1900 edition: page 113 of the PDF
is page 113 of the book, line for line — `python3 tools/dj_build.py --facsimile` → `djachenko/facsimile.typ` +
`.pdf` (git-ignored). What the investigation established (numbers in PROGRESS.md, session 5):

- *One setting.* The four witnesses (A, B, C, D — COPIES.md) are one typesetting: over all 1,119 dictionary pages,
  99.8 % of B's, 99.7 % of C's and 99.5 % of A's line starts (margin-intact sides) fall on a line start of D, no
  page or column disagrees as a block, and the residue is OCR (`dj_inspect.py linecheck`, `eval/linecheck.tsv`).
  C's title page (1899) and D's (1900) are one setting apart from the year line. So the choice of witness is
  moot for the layout: A's geometry, already the segmentation reference, is the source; D fills A's cut margins.
- *The line structure is in the repository.* `ocr/*.json` hold every printed line of every page (124,548 in the
  dictionary proper) with box, baseline, indent level (flush/hanging), font size and ABBYY's text; the columns,
  bands and letter initials with their boxes; 26,947 paragraphs, 1,585 of them continuing over a column or page.
  Baseline pitch 102 px = 12.24 pt (the flowing build assumes 12.6).
- *What is missing:* (1) the mapping of the voted text onto the lines — `text_merged` and `entries.tsv` are
  line-less (lines joined, hyphens repaired); (2) the line-end hyphens of column b on the 313 right-cut pages
  (13 % of those lines end hyphenated in A against 26 % elsewhere, i.e. ~2,300 hyphens lost with the margin) —
  D has them, but D is on disk only (git-ignored); (3) the Church Slavonic type inside entries (cross-references)
  is not marked, which the flowing rendition lacks too.
- *The type.* The book's face is larger than the 10 pt Old Standard of the flowing build: printed x-height
  6.2 pt and cap height 8.9 pt correspond to Old Standard at 12.5–13.5 pt, line widths to ~12.7 pt, on a 12.24 pt
  pitch (a compact face with a large x-height). At 10 pt a line's natural width is 78 % of the printed line; the
  columns would have to be justified with a quarter of their width in white. Page size is free (user, session 5),
  so the page is scaled instead of the type. Share of full lines wider than the column, measured with Typst on
  1,214 justified lines of 16 pages (ABBYY's text, so the last per cent is garbled headword lines):

  | type size | scale 1.00 | 1.04 | 1.08 | 1.12 |
  |---|---|---|---|---|
  | 11 pt | 1.4 % | 1.0 % | 0.3 % | 0.2 % |
  | 12 pt | 16.5 % | 6.1 % | 2.2 % | 1.1 % |
  | 12.5 pt | 32.2 % | 17.0 % | 6.7 % | 2.5 % |

  Candidates: 12 pt at scale 1.08 (text block 183 × 269 mm, pitch 13.2 pt, a ~215 × 300 mm page); 11 pt at 1.04
  fits A4 with 15 mm margins. The rest is absorbed per line by negative tracking, found with `typst query` on
  measured widths.

How it is built (session 5): (1) `dj_heads.py text` VERSION 9 stores per paragraph `breaks` — the printed lines as
[offset, hyphen] in `text_merged`, one per line of A's paragraph: A's line starts carried through the alignment
and snapped to D's line starts (LINE_TOL 4), or D's k-th line start where A's cannot be carried over and D has as
many lines as A; the hyphen A's where A's line end is in the image, else D's (a D line joined without a space; so
the right-cut pages get theirs) — and `dj_abbyy.py` carries the key over. Also in 3a:
the page number's, guide words' and signature line's baselines (`header.base`, `header.guide_base`,
`footer_base`), and the printer's sheet signature "N*" at the foot of column b (p ≡ 3 mod 16), which ABBYY had
kept as a text line on 49 pages, is page furniture now. (2) `dj_parse.py` carries the lines into `entries.tsv` as
the `lines` column (offset in the definition, negative inside the head, "h" for a hyphenated end), remapped through
tidy/fix_quotes/errata like the italic and disputed spans; every entry's count equals the lines of its paragraphs.
(3) `dj_build.py --facsimile` sets the book page by page from `entries.tsv` and `ocr/*.json`: no Typst column
flow — each line is `place`d at its measured baseline and column position (deskewed on the column rule; the
columns' flush edges at book-wide constants from the rule, −2001 and +66 px, since the per-page fits vary with the
page's curl and fail on the left-cut pages; x from the flush edge and the hanging indent — ABBYY's "deeper" lines
are mostly lines it began late, so only a short one keeps its own position; the nominal first baseline is the
first line's, or the page number's + 240 px on a page that opens with a title), justified to the column width
(1927 px) with a forced break, the entry's last line ragged; **Rev. 7:** an entry is set indented and without a
head only when its start is A's unconfirmed guess (flag `guessed`) *and* it has neither headword nor separator —
before, every entry without both was, which hid 307 real lemmas inside the article above them (`Япрілій` on p. 21
among them; the segmentation of step 1c removed most of the continuation lines that the rule was meant for). A
real entry whose headword the OCR did not read is printed with a □; and since a missing separator is what
swallows the headword, `dj_parse.py` now cuts the head after as many words as ABBYY read of the headword region
whenever no separator is found at all (flag `hw_from_A`, 456 entries), which leaves 132 entries with no headword
instead of 874; page number over its double rule, guide
words (from the first and last entry of the page), "Прибавленіе." on the supplement's pages, the signature line and
the "N*", letter initials and titles fitted into their measured boxes (Ponomar for the letters); a line whose
natural width exceeds the column is condensed to fit and reported (`<over>` metadata → `facsimile_over.tsv`, the
count goes into the note). `--size` (default 12) and `--scale` (default 1.08; page 215 × 315 mm) as above.
Not yet: the book's front matter (its lines are in `ocr/`, but no voted text), the Church Slavonic type inside
entries, italics beyond ABBYY's.

*Definition of done:* `djachenko.pdf` builds cleanly from `entries.tsv`; README updated; committed. Rev. 6: the
facsimile build has as many dictionary pages as the book (1,119 + the blank p. 864) and every page the same lines
as the scan on a spot check; the condensed lines are listed by the build. — Done 2026-09-20 (PROGRESS.md has the
numbers).

## Effort and budget (revised after the Phase 1 findings; to be revised again after Phase 2)

| Phase | Sessions | Notes |
|---|---|---|
| 0 | done | |
| 1 | done | |
| 2 | done | 2 sessions; ground truth ~4 h |
| 3a | done | |
| 3b | 2 + reruns, or 4–8 | one session for the alignment/voting script and its checks, one for the crop pipeline; then either one unattended API pass over ~850 contact sheets (~2 M tokens) or 4–8 interactive sessions of sheet reading |
| 4 | 1 + reruns | |
| 5 | 3–6 short | proofreading ~550 linked entries |
| 6 | done | Rev. 6: the facsimile build took the one session estimated (session 5) |

Total for the full text with targeted proofreading: on the order of 10–18 sessions, about half the previous estimate,
because the definition text no longer has to be OCR'd or transcribed. A full proofreading of all 30,000 entries is
*not* part of this plan.

## Session protocol

At the start of a session: read `djachenko/PROGRESS.md` (its `NEXT:` line), then this plan's phase for that step.
At the end of a session, before anything else: update `PROGRESS.md`, commit. Never leave the manifest or
`entries.tsv` half-written — the scripts write to a temporary file and rename.
