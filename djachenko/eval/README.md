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
| `gt/1124.txt` | 1124 | 1087 | supplement; the left margin is cut off in scan A — the missing letters are read in witness B |

Page images: `djachenko/pages/NNNN.jpg` (300 ppi; 600 ppi originals in `pages/jp2/`). For leaf 1124 also witness B
(`scan/reprint1993/`, DjVu page 1087; see COPIES.md).

**Status of each file:** the first line says `status: draft` until the user has checked it against the image, then
`status: checked (date)`.

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
- **Church Slavonic type** (headwords, and CS words quoted in the definitions) is enclosed in `{ }` and written with
  the letters as printed — Cyrillic including ѡ ѿ ѻ ꙋ ѹ ѕ ꙁ є ѥ ї ѧ ꙗ ѩ ѫ ѭ ѯ ѱ ѳ ѵ ѣ — **without** accents,
  breathings, titla and pokrytie; a superscript letter is written in its place in the word. The two shapes of z
  (ʒ-shaped in the large headword type, ζ-shaped in the small type) are both written з; ꙋ (8-shaped uk), оу and у
  are kept apart as printed. The civil pre-reform form
  used for `headword_civil` (Phase 0.2) is derived from this by a fixed mapping: ѡ ѻ ꙩ → о, ѿ → от, ꙋ ѹ оу → у,
  ѕ ꙁ → з, є ѥ → е, ї → і, ѧ ꙗ ѩ → я, ѫ → у, ѭ → ю, ѯ → кс, ѱ → пс; ѳ ѵ ѣ і ъ ь stay.
- **Greek** in polytonic Unicode with accents and breathings as printed; Latin, Hebrew etc. as printed.
- `‹…›` encloses letters that are not in scan A (margin cut off) and were read in witness B.
- `[?]` after a word: reading uncertain. `□`: an illegible character. A letter that is printed but damaged (broken
  type) is transcribed as the letter it is, with a `# notes:` comment.
- Roman numerals are written with Latin letters (XVI), as printed. An entry split across a column break: the first
  part keeps its final hyphen (`со сбо-`), the continuation starts with `+ ` (`+ рами …`).
- How it was made: each column was read line by line in 600 ppi crops of scan A, and every line was compared with
  ABBYY's reading of it; where the two differed, the image decided. Doubtful glyphs were compared with witness D
  (Cornell copy) where needed.
