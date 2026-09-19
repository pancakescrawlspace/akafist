# Plan: a structured digital edition of Дьяченко's Полный церковнославянский словарь (1900)

Goal: a machine-readable, proofread-where-it-matters copy of Г. Дьяченко, *Полный церковнославянский словарь* (Москва 1900;
~30,000 entries, ~1,120 two-column pages + XXXVIII pages of front matter), and from it a Typst/PDF rendition in the
style of `dictionary/dictionary.typ`. The book is public domain (published 1900, author †1903).

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
  djachenko.typ, djachenko.pdf   Typst rendition (Phase 6)
tools/
  dj_fetch.py      Phase 1: download scan + OCR layers, extract page images, write manifest (exists)
  dj_abbyy.py      Phase 3a: ABBYY XML → ocr/NNNN.json (text, geometry, formatting), idempotent (exists)
  dj_heads.py      Phase 3b (Rev. 5): `text` — per page, align witness D's text to A's segmentation, vote with B, A
                   and C (exists, run); `crops`/`read`/`collect`/`sheet`/`enter`/`check` — the headwords from
                   crops, by the API or by hand (exists, not yet run); idempotent and resumable throughout
  dj_witness.py    shared: witness word boxes and page mapping, reading order, normalisation, alignment (exists)
  dj_eval.py       Phase 2: CER of the OCR candidates against the ground truth, per zone; triangulation (exists)
  dj_inspect.py    helpers: dump/overlay a page, crop lines, find a word in all four witnesses side by side,
                   sanity checks of the ground truth and of the entry starts (exists)
  dj_parse.py      Phase 4: ocr/*.json → entries.tsv + FLAGS.md (exists; headwords provisional until step 2 runs)
  dj_link.py       Phase 5: cross-reference entries.tsv with dictionary/dictionary.psv lemmas → links.tsv (exists)
  dj_build.py      Phase 6: entries.tsv → djachenko.typ (+ PDF via typst)
```

`.gitignore` gets `djachenko/scan/` and `djachenko/pages/`. Everything else is committed, in small batches, so that a
session can end at any point without losing work.

## Phase 0 — Decisions (one short session; needs the user)

Decide and record in `PROGRESS.md`:

1. **Scope of the Typst output.** (a) the whole dictionary (~30,000 entries; at the current two-column A5 style this is
   in the order of 900–1,100 pages), or (b) a subset: the entries for the ~700 lemmas of the akathist dictionary plus
   whatever else is wanted, as an appendix or companion volume to `dictionary/dictionary.pdf`. The pipeline is the same
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
text features are combined (naive Bayes) and the paragraphs marked `guessed`. Result: 25,362 entry candidates in
main + supplement (22,542 with "=" in their first two lines; 3,197 guessed, on 261 pages); `manifest.tsv` has section
and letters; `ocr/report.tsv` the per-page statistics and warnings. The book's "~30,000 entries" is a round figure:
the "=" count (24,483) and the candidates agree on ~25,000.

**3b. `tools/dj_heads.py --pages A-B`** (Rev. 5, after Phase 2) builds the page text from the witnesses on top of
A's segmentation, in three steps per page, each idempotent and each recorded in the page JSON:

1. *Text.* — **DONE** (session 3; `dj_heads.py`, shared code in `dj_witness.py`; eval/RESULTS.md addendum).
   Per column side: D's reading order from its word boxes, aligned to A's text, cut at A's paragraph starts snapped
   to D's line starts; per-character vote D/B/A with C as the check; per paragraph `text_d`, `text_merged`,
   `disputed` spans, `fixed`, `d_cut`, `d_line`; per page a `witness` block. Definitions 1.0 % CER on the GT
   (D alone 1.5 %), 85 % of the remaining errors inside the disputed spans. All 1,119 pages done (62 s; resumable;
   `dj_abbyy.py` carries the texts over on regeneration).
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
*Resume:* run `dj_abbyy.py` (fast, idempotent) then `dj_heads.py` with the full range; `PROGRESS.md` says which
batch is next.

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
  entry.

*Definition of done:* `entries.tsv` covers all OCR'd pages; the validation report is in `PROGRESS.md`; flagged entries
listed in `djachenko/FLAGS.md` (regenerated each run).
*Resume:* the script is deterministic; just re-run it.

## Phase 5 — Cross-reference and targeted proofreading (several short sessions)

1. `tools/dj_link.py`: for every lemma of `dictionary/dictionary.psv`, find the matching Дьяченко entries by
   `headword_key` (with a small set of fallbacks: infinitive ↔ 1 sg. verb forms, ъ/ь variants, ѵ→и/в). Output
   `djachenko/links.tsv` (lemma → entry ids, match type) and a list of akathist lemmas with no match, to be resolved by
   hand. — Rev. 5: **exists** (session 3); with the provisional headwords it links 243 of 703 lemmas (exact 229,
   verb 11, soft 3); the rest waits for the step-2 headwords. Re-run after every step-2 batch.
2. Proofread the linked entries against the page image (open `pages/NNNN.png`, fix the text in `entries.tsv`, set
   `status=checked`). Estimate: ~500–600 entries, a few minutes each — spread over sessions; `PROGRESS.md` records the
   last checked id.
3. Optionally add a `dj` column to `dictionary/dictionary.psv` with the entry ids, so `dictionary.md/.typ` can show
   "Дьяченко s.v. …".

*Definition of done:* every akathist lemma is linked or explicitly marked "not in Дьяченко"; linked entries `checked`.

## Phase 6 — Typst rendition (one session for the script; re-run at will)

`tools/dj_build.py [--subset links|all] [--paper a5|a4]` writes `djachenko/djachenko.typ` in the style of
`dictionary/dictionary.typ` (same preamble: PT Serif + Libertinus, Greek rule, guide words, hanging-indent entries, big
letter initials, front matter) and compiles it. Entry style: **headword** (civil pre-reform) `=` definition; grammatical
tag in italics; unchecked entries marked with a small sign; page reference to the 1900 edition in grey at the end of
the entry ("¶ 85b" = page 85, column b) so that anything can be verified against the scan.

Front matter to include: title, bibliographic note, what "checked/unchecked" means, the encoding conventions of
Phase 0.2, and Дьяченко's own list of abbreviations (transcribed from the front matter as part of Phase 3;
Rev. 3: pp. XXIX–XXXIII = leaves 27–31, already in ocr/ as two-column text with hanging indents).

*Definition of done:* `djachenko.pdf` builds cleanly from `entries.tsv`; README updated; committed.

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
| 6 | 1 | |

Total for the full text with targeted proofreading: on the order of 10–18 sessions, about half the previous estimate,
because the definition text no longer has to be OCR'd or transcribed. A full proofreading of all 30,000 entries is
*not* part of this plan.

## Session protocol

At the start of a session: read `djachenko/PROGRESS.md` (its `NEXT:` line), then this plan's phase for that step.
At the end of a session, before anything else: update `PROGRESS.md`, commit. Never leave the manifest or
`entries.tsv` half-written — the scripts write to a temporary file and rename.
