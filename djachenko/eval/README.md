# Ground truth for Phase 2

Six pages transcribed by hand from the page images, to measure OCR candidates against (`tools/dj_eval.py`). They
were chosen to cover the kinds of page the book has (PLAN.md Phase 2):

| file | leaf | page | why |
|---|---|---|---|
| `gt/0045.txt` | 45 | 8 | an ordinary page of А |
| `gt/0517.txt` | 517 | 480 | a typical dense page from the middle (П) |
| `gt/0465.txt` | 465 | 428 | a long article with verse quotations (П) |
| `gt/0660.txt` | 660 | 623 | the lowest OCR confidence in the main part: poor print (С) |
| `gt/0893.txt` | 893 | 856 | the rare letters Ѫ and Ѩ with an initial in mid-page; the most etymologies (Greek, Hebrew) |
| `gt/1124.txt` | 1124 | 1087 | supplement; the left margin is cut off in scan A — the missing letters are read in another copy |
| `gt/0719.txt` | 719 | 682 | **added session 4**: the densest Greek page of the book (395 Greek characters) |

**Extension (session 4, in progress).** The first six pages were chosen to cover the kinds of page; measuring them
showed where the sample is too thin (PROGRESS.md): Greek rests on 266 characters over the six, the Old Church
Slavonic citation type is absent, and no page is dense in short entries. Six pages are being added for those gaps,
one done so far:

| leaf | page | why | state |
|---|---|---|---|
| 719 | 682 | Greek-densest page (395 Greek characters) | **done** |
| 801 | 764 | second Greek-dense page (314) | **done** |
| 260 | 223 | the Old Church Slavonic citation type, unmeasured so far (the page the user noticed it on) | **done** |
| 146 | 109 | 81 entries, the densest page of the book: segmentation and headwords | to do |
| 283 | 246 | drawn at random (seed 2026) — **held out**: never to be used for tuning a rule | to do |
| 696 | 659 | drawn at random — **held out** | to do |

The four targeted pages are stress pages, not a random sample: the headline error rate should stay on the six
representative pages, and these should be read per page. The two random pages exist so that a change tuned on the
others can be tested on something it has never seen.

Page images: `djachenko/pages/NNNN.jpg` (300 ppi; 600 ppi originals in `pages/jp2/`). For leaf 1124 also witness B
(`scan/reprint1993/`, DjVu page 1087) and D (`scan/google/google_cornell.pdf`, PDF page 1135); see COPIES.md.

**Status of each file:** the second line says `status: draft` until the user has checked it against the image,
then `status: checked (date)`. A machine-assisted check of all six files was made in session 4 (2026-09-20) and is
recorded in each file's header: every place where two independent OCRs agree against the file (73, of which 38 were
new), every place where the file stands alone against all four witnesses, and every headword against a contact
sheet of the headword crops; the decidable ones read on the images at 600 ppi. No error was found — the earlier
11 slips were the ones this signal could catch, and they were corrected in session 3. It is not a substitute for
the user's own reading, which stands open for 0465, 0660, 0893, 1124 and (beyond a cursory look) 0517. User's checks so far: 0045 checked thoroughly, no error found (2026-09-19); 0517
checked cursorily, no error found (2026-09-19). After those checks, comparing the OCR witnesses against the GT
(`tools/dj_eval.py --suspects [--only X,Y]`: places where two independent OCRs agree against the transcription) found 11 slips
in five files, each confirmed on the images and corrected; they are listed in the files' header comments (0045: 6,
0465: 2, 0893: 2, 1124: 1). The remaining 35 disagreements are OCR errors (checked). Results: `RESULTS.md`;
candidate texts per witness and page in `cand/` (cached; `--refresh` re-extracts them from the scans).

- In the small CS type и and н look nearly the same (ABBYY reads н for both), л is Λ-shaped and а is ɑ-shaped; where
  the glyphs do not decide, the word is read by sense and the choice noted in the file (e.g. Ѫзилиште on p. 856).

## Conventions

- UTF-8, Unicode NFC. One printed **entry per text line**: the whole paragraph joined, with line-end hyphenation
  removed ("на-|переди" → "напереди"); a hyphen that belongs to the word (a compound broken at its hyphen,
  "древне-|русскихъ") stays.
- `# …` lines are comments. The first lines give leaf, page, guide words and status.
- `@ col N a|b` starts column N of the page in reading order, as in `ocr/NNNN.json` (`a` left, `b` right; a page
  with a letter initial in mid-page has four columns). `@ heading X` stands where a letter initial is printed.
- A line starting with `+ ` continues an entry from the previous column or page (it is not an entry start).
- Text as printed, pre-reform spelling included (ѣ, і, ѳ, ѵ, ъ), misprints included — nothing is corrected.
  Italics and bold are not marked. Spaces as printed, but the evaluation ignores differences in spacing.
  **Deliberate:** the spacing around "=" follows the print, which is itself inconsistent ("слово=", "слово =",
  "= слово" all occur); the evaluation ignores it, and Phase 4 may normalise it in `entries.tsv`.
- **Church Slavonic type** (headwords, and CS words quoted in the definitions) is enclosed in `{ }` and written with
  the letters as printed — Cyrillic including ѡ ѿ ѻ ꙋ ѹ ѕ ꙁ є ѥ ї ѧ ꙗ ѩ ѫ ѭ ѯ ѱ ѳ ѵ ѣ — **without** accents,
  breathings, titla and pokrytie; a superscript letter is written in its place in the word. **Deliberate** (user's
  Phase 0 decision 2: headwords in civil pre-reform script, no titla or superscripts): the CS diacritics are not
  transcribed, so the OCR candidates are not scored on them; a column with the full CS form (accents, titla) can be
  added later if wanted. Greek, by contrast, keeps all its accents and breathings. The two shapes of z
  (ʒ-shaped in the large headword type, ζ-shaped in the small type) are both written з; ꙋ (8-shaped uk), оу and у
  are kept apart as printed. The civil pre-reform form
  used for `headword_civil` (Phase 0.2) is derived from this by a fixed mapping: ѡ ѻ ꙩ → о, ѿ → от, ꙋ ѹ оу → у,
  ѕ ꙁ → з, є ѥ → е, ї → і, ѧ ꙗ ѩ → я, ѫ → у, ѭ → ю, ѯ → кс, ѱ → пс; ѳ ѵ ѣ і ъ ь stay.
- **Greek** in polytonic Unicode with accents and breathings as printed; Latin, Hebrew etc. as printed.
- `‹…›` encloses letters that are not in scan A (margin cut off) and were read in another copy (witness D, else B
  or C; see COPIES.md).
- `[?]` after a word: reading uncertain. `□`: an illegible character. A letter that is printed but damaged (broken
  type) is transcribed as the letter it is, with a `# notes:` comment.
- Verse quotations (set indented) are joined like prose, one space between verse lines; a turned-over verse end is
  joined to its line.
- A defect of scan A (cut margin) is supplemented from another copy; a defect of the printed book itself (a letter
  missing, broken type) is transcribed as printed and noted — checked in witness D, e.g. "мꙋгленый" (p. 623) lacks
  its С in both copies.
- Roman numerals are written with Latin letters (XVI), as printed. An entry split across a column break: the first
  part keeps its final hyphen (`со сбо-`), the continuation starts with `+ ` (`+ рами …`).
- How it was made: each column was read line by line in 600 ppi crops of scan A, and every line was compared with
  ABBYY's reading of it; where the two differed, the image decided. Doubtful glyphs were compared with witness D
  (Cornell copy) where needed.
