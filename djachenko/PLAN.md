# Plan: a structured digital edition of Дьяченко's Полный церковнославянский словарь (1900)

Goal: a machine-readable, proofread-where-it-matters copy of Г. Дьяченко, *Полный церковнославянский словарь* (Москва 1900;
~30,000 entries, ~1,120 two-column pages + XXXVIII pages of front matter), and from it a Typst/PDF rendition in the
style of `dictionary/dictionary.typ`. The book is public domain (published 1900, author †1903).

This plan is written to be executed over several sessions. Every phase has a *Definition of done* and a *Resume*
paragraph; all state lives in files under `djachenko/` so that a new session can read `PROGRESS.md`, the manifest and
this plan and continue without any conversational memory.

## Findings that shape the plan (verified 2026-09-19)

- No transcribed text edition exists. Azbyka.ru (`/otechnik/Grigorij_Djachenko/polnyj-tserkovnoslavyanskij-slovar/`,
  38 per-letter pages) and dhonorare.ru (`/dict/dyachenko/`) serve **page images** only. Wikisource has an index
  (`Индекс:Полный церковнославянский словарь (Протоиерей Г.Дьяченко).djvu`) with **no OCR layer** and two transcribed
  pages. So the text must be produced by OCR (in the wide sense) from a scan.
- Scans available: the archive.org copy; the Wikimedia Commons PDF "Прот. Г. Дьяченко. Полный церковно-славянский
  словарь (1900).pdf"; Azbyka's per-page PNGs of the 2004 reprint; dhonorare's per-page JPGs. One of the single-file
  copies is preferable to 1,100+ requests to a website.
- Typography of the original: two columns; headwords in Church Slavonic type (titla, ѣ ѧ ѡ ѵ), followed by "=" and
  the definition in pre-reform Russian civil type; Greek, Hebrew, Latin in etymologies; biblical references in
  parentheses. The "=" after the headword and the hanging indent are the structural markers to exploit.
- Azbyka's robots.txt disallows automated fetching of `.epub`, `.txt`, `.djvu` files; HTML/PNG pages are not
  disallowed. Any fetching is done with a descriptive User-Agent, sequentially, with a delay.

## Layout of `djachenko/`

```
djachenko/
  PLAN.md          this file
  PROGRESS.md      running log: date, what was done, "NEXT:" line (the first thing a new session reads)
  SOURCE.md        which scan was used, URL, checksum, page count, page-index → printed-page mapping
  manifest.tsv     one row per scan page: idx, printed_page, section (front/letter/supplement), letter, status, notes
                   status ∈ {new, image, ocr, parsed, checked}
  scan/            the downloaded scan (git-ignored; large)
  pages/           one image per page, idx-numbered (git-ignored; regenerable from scan/)
  ocr/             raw OCR per page: NNNN.json (see Phase 3 for the schema) — committed
  entries.tsv      the structured dictionary (Phase 4 output) — committed
  eval/            ground-truth pages and evaluation results (Phase 2)
  djachenko.typ, djachenko.pdf   Typst rendition (Phase 6)
tools/
  dj_fetch.py      Phase 1: download scan, extract page images, write manifest skeleton
  dj_ocr.py        Phase 3: OCR a page range, idempotent (skips pages with status ≥ ocr)
  dj_eval.py       Phase 2: CER/WER of an OCR output against a ground-truth file
  dj_parse.py      Phase 4: ocr/*.json → entries.tsv, with validation report
  dj_link.py       Phase 5: cross-reference entries.tsv with dictionary/dictionary.psv lemmas
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

## Phase 1 — Acquire the scan and page images (one session, mostly unattended)

1. Compare one sample page (same printed page, e.g. p. 100) from the candidate scans for resolution and legibility;
   note results in `SOURCE.md`. Prefer the highest-resolution single-file copy (archive.org or Commons PDF).
2. `tools/dj_fetch.py --source <url>`: download to `scan/`, record URL, size, SHA-256, page count in `SOURCE.md`.
3. Extract page images losslessly at native resolution (`pdfimages -png` / `mutool draw` / `ddjvu`) to
   `pages/NNNN.png`. Deskew and crop only if the OCR evaluation shows it helps (do it in a separate step, keeping
   originals).
4. Build `manifest.tsv`: for every page its printed page number and section. The front matter (Roman numerals), each
   letter's first page and the supplement ("Прибавление") are found by hand from a handful of pages; the rest is
   arithmetic. Record the idx→printed mapping in `SOURCE.md`.

*Definition of done:* `scan/` present, `pages/` complete, `manifest.tsv` has one row per page with status `image`,
`SOURCE.md` filled in. Committed: `SOURCE.md`, `manifest.tsv`, `.gitignore`.
*Resume:* if `pages/` is incomplete, re-run step 3 (the script skips existing files).

## Phase 2 — Choose the OCR route by measurement (one to two sessions)

Ground truth: 6 pages chosen to be representative — an ordinary page from А, one from the middle (П or С), one from a
short late letter (Ѣ or Ѵ), one dense in Greek/Hebrew etymology, one from the supplement, one with poor print quality.
Transcribe them carefully by hand into `eval/gt/NNNN.txt` (headword lines start with `= `; column breaks marked). This
is slow (~30–45 min per page) but is the only way to compare candidates honestly; the user may prefer to check these
transcriptions.

Candidates, each producing `eval/<method>/NNNN.txt` for the same pages:

- **Tesseract 5** with `rus` (fails on ѣ/і/ѳ by design), `script/Cyrillic`, and any community model for
  pre-reform Russian or Church Slavonic that can be found; with and without column segmentation (`--psm 1/3/4`).
  Free, fast, weak on the Slavonic headwords — may still be the best choice for the *definition* text.
- **Kraken/eScriptorium** with a model trained on the ground-truth pages (needs more than 6 pages; realistic only if a
  pretrained historical-Cyrillic model exists to fine-tune).
- **Commercial OCR** (ABBYY FineReader lists Old/Church Slavonic among its languages; Google Document AI, Azure Vision):
  cost per page to be checked; decide only if the free routes fail.
- **Vision-model transcription (Claude reading the page image)**, one page per call, with a fixed output schema (see
  Phase 3) so that transcription and entry segmentation happen in one pass. Strengths: mixed scripts, pre-reform
  orthography, structure; costs tokens (order of magnitude: 1,150 pages × ~5k tokens ≈ 6M tokens for one pass) and
  must be measured for hallucination (invented words look plausible — compare against ground truth, not by eye).

`tools/dj_eval.py gt.txt candidate.txt` reports character and word error rate overall, for headwords only, and for
definition text only. Record all numbers in `eval/RESULTS.md`.

*Definition of done:* `eval/RESULTS.md` names the chosen route (possibly a hybrid: one engine for headwords, another for
definitions) with its measured error rates, and `PROGRESS.md` says so.
*Resume:* ground-truth files and candidate outputs are all on disk; continue with whichever candidates lack output.

## Phase 3 — Bulk OCR, in batches (several sessions; the long phase)

`tools/dj_ocr.py --pages 1-1160 [--batch 50]` runs the chosen route page by page, writes `ocr/NNNN.json`, sets the
manifest status to `ocr`, and skips pages already done — so it can be interrupted at any moment and re-run.

Per-page JSON schema (the same regardless of engine, so Phase 4 does not care which was used):

```
{ "idx": 123, "printed_page": 85, "engine": "...", "columns": [
    { "n": 1, "lines": ["…", "…"] },
    { "n": 2, "lines": ["…", "…"] } ],
  "entries_hint": [ {"headword": "…", "start_line": [1, 14]} ],   # optional, if the engine segments
  "warnings": ["…"] }
```

Work in batches sized to a session (50–100 pages for the vision route, all pages at once for Tesseract). After every
batch: run `dj_parse.py --check` on the new pages (Phase 4 in validation mode), append a line to `PROGRESS.md`
("pages 301–400 OCR'd, 3 warnings"), commit.

*Definition of done:* every manifest row has status ≥ `ocr`.
*Resume:* `dj_ocr.py` with the full range; it does only what is missing. `PROGRESS.md` says which batch is next.

## Phase 4 — Structure into entries (one session to write, then re-run after every batch)

`tools/dj_parse.py` turns `ocr/*.json` into `entries.tsv`:

```
id  headword_civil  headword_key  gram  definition  page  column  status  flags
```

- Segmentation: an entry starts at a line beginning with a headword followed by `=` (Дьяченко's convention);
  continuation lines are joined; hyphenation at line and column ends is repaired; cross-references ("см.") kept as
  text.
- `gram` = the grammatical/etymological tag immediately after `=` when present (e.g. "(греч.)", "гл.").
- `headword_key` = normalised modern spelling (Phase 0.2).
- Validation report: headwords must be (nearly) alphabetical within a page and across pages — every violation is a
  segmentation or OCR error and is written to `flags`; pages whose entry count is far from the neighbours' are flagged;
  unbalanced parentheses flagged.
- `status` starts as `raw`.

*Definition of done:* `entries.tsv` covers all OCR'd pages; the validation report is in `PROGRESS.md`; flagged entries
listed in `djachenko/FLAGS.md` (regenerated each run).
*Resume:* the script is deterministic; just re-run it.

## Phase 5 — Cross-reference and targeted proofreading (several short sessions)

1. `tools/dj_link.py`: for every lemma of `dictionary/dictionary.psv`, find the matching Дьяченко entries by
   `headword_key` (with a small set of fallbacks: infinitive ↔ 1 sg. verb forms, ъ/ь variants, ѵ→и/в). Output
   `djachenko/links.tsv` (lemma → entry ids, match type) and a list of akathist lemmas with no match, to be resolved by
   hand.
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
Phase 0.2, and Дьяченко's own list of abbreviations (transcribed from the front matter as part of Phase 3).

*Definition of done:* `djachenko.pdf` builds cleanly from `entries.tsv`; README updated; committed.

## Effort and budget (rough, to be revised after Phase 2)

| Phase | Sessions | Notes |
|---|---|---|
| 0 | ½ | decisions |
| 1 | 1 | mostly download/extract time |
| 2 | 1–2 | ground truth is the slow part (~4 h of human-quality transcription for 6 pages) |
| 3 | 8–15 for the vision route (≈100 pages/session, ≈0.5M tokens each); 1 for Tesseract | the long phase |
| 4 | 1 + reruns | |
| 5 | 3–6 short | proofreading ~550 entries |
| 6 | 1 | |

Total for the full text with targeted proofreading: on the order of 15–25 sessions if the vision route is chosen,
about half that if Tesseract proves adequate for the definitions. A full proofreading of all 30,000 entries is *not*
part of this plan; it is a Wikisource-sized effort.

## Session protocol

At the start of a session: read `djachenko/PROGRESS.md` (its `NEXT:` line), then this plan's phase for that step.
At the end of a session, before anything else: update `PROGRESS.md`, commit. Never leave the manifest or
`entries.tsv` half-written — the scripts write to a temporary file and rename.
