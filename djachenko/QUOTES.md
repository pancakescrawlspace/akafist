# Floating quotation marks — the defect and the fix

**Status: fixed** (session 4, 2026-09-19) in `dj_parse.fix_quotes()`; the `«»` check asked for by the user is done
(below). Drafted at the end of session 3, when the user saw quotation marks floating among the words of the first
Typst rendition.

## The defect, measured on the merged text of all 1,119 pages (before the fix)

About 8,100 quotation marks: `„` 3,965, straight `"` 2,881, `“` 1,109, `«` 28, `»` 24, a handful of `’ ‘ ”`.
Google's text layer (witness D, the primary text) emits each quote as a separate word; `dj_witness.reading_order`
joins words with spaces; hence:

| character | spacing | count | example |
|---|---|---:|---|
| `„` | space before, glued after | 2,070 | `по употребленію въ „Ідеѣграмматикіи` (right) |
| `„` | space on both sides | 1,763 | `правильнаго „ бене-эль" .` (floating) |
| `"` | glued before, space after | 1,716 | `мусикійской" Дилецкаго` (a closing quote, wrong glyph) |
| `"` | space on both sides | 877 | floating |
| `“` | space on both sides | 520 | `„ Аглъ Бжій “ также` (floating) |
| `“` | glued before, space after | 503 | right |
| `"` | glued on both sides | 186 | `дам" = подобіе` (OCR dropped one quote or a space) |
| `„` | glued on the wrong side | 61 | `харатьи"„` |

The straight `"` is an OCR rendering failure, not the print.

**A second cause, in the PDF only** (found by the user at Ядамъ, p. 5b = page 7 of the PDF): `dj_build.py` set
`lang: "ru"`, and Typst's smart quotes turn every straight `"` into `«` or `»` by their spacing, so `„дам" =`
was printed as `„дам» =`, and floating ones in the wrong direction (`по подобію « (евр.`). Fixed by
`#set smartquote(enabled: false)` in the generated preamble: the text's own glyphs are now printed as they are.

## What the book prints — the `«»` check (session 4)

The user doubted that the `«`/`»` in the text were genuine. All 52, and the 5 `’ ‘ ”`, were checked on crops of
scan A and witness D (`dj_inspect.py find`):

- **Genuine `«…»`, about 30.** The book mostly uses `„…“` but prints `«…»` in some long articles and quotations:
  pp. 577–578 (Свойственно… `«удаляется берегъ»`, `«несообразность»`, `«невѣсомую жидкость»` …), 579
  (`«свѣденіе»`), 626–627 (`«И вражду положу… пяту»`, `«…Дѣвою»`), 668 (`«Имамъ… покоя»`), 675 (`«стружіе»`),
  733 (`«вса́дники трїста́ты»`), 757, 797, 829, 846. **Mixed pairs are printed too**: `«…“` (pp. 621
  `«Смертію умрете“`, 668 `«Отъ многой страдьбы… изнемогъ“`, 675 `«стружія“`, 703, 773 `«медоркіе“`) and `„…»`
  (pp. 732 `„Къ Тебѣ утреннюю»`, 757 `„умыкаху жены собѣ»`). So `«` and `»` are kept as printed, and the pairing
  rule treats `„ «` as opening and `“ »` as closing, in any combination.
- **Misread `„`/`“`, 4:** `»Матер.` p. 564, `»Ахматовичемъ` p. 636, `» Опытъ` p. 952 (all `„` in print — a `»` in an
  opening position with nothing open is now written `„`); `окаянна »` p. 654 (a small closing mark in italic type).
- **Misread letters or specks, about 19:** `Соб»ство`, `благода»ственная`, `«же` (ꙋже), `жизнів»` (жизнію), `шнур»`,
  `един»`, `«розваніе`, `че«.`, `нап ».`, `«кга`, `«аставленіе`, `«увазію`, `«гре`, `«зькъ`, `«дрость`, `«долитъ`,
  `«за=`, `«χρυσοπορφύρος)`. Not fixed by rule; most unbalance their entry and surface under the `quotes` flag.
- **`’ ‘ ”`, 5, all noise:** a speck (p. 8), CS accent marks before a headword (p. 13), a stray mark (p. 492), and
  **two printer's signature marks** `32 ’` (p. 499) and `64 ’` (p. 1011) — page furniture that leaked into the
  text; that was a separate defect, fixed the same session in `dj_witness.reading_order` (see PROGRESS.md).
  Apostrophes `'` (91) are left alone.

## Where it is fixed

In `dj_parse.split_entry`, after the existing tidying and after the separator is found: first on the definition,
then on D's head text as a separate pass with its own pairing (its quotes are often noise — CS accent marks read as
`"` — and must not upset the definition's pairing; but where D dropped the `=`, the head text runs on to the next
`(` and carries real quotations, which the PDF prints in grey). The flag is the definition's. Not in the witness
texts or `text_merged` (evidence for the Phase 2 measurements and the vote; `disputed`/`italic` spans live in their
coordinates) and not in `dj_build.py` alone (entries.tsv is what every consumer reads). `ocr/*.json` stays the
faithful record.

## The rules (`quote_roles`, `fix_quotes`)

- **Direction.** `„ «` open, `“ » ”` close, as printed. A straight `"` by its spacing: glued to a word or
  punctuation on the left and followed by a space, punctuation, `=`, `(` or another quote → closing; followed by
  punctuation or `=` → closing; followed by a letter and not preceded by one → opening. A floating `"` (spaces on
  both sides, or between two letters) is decided by the next printed character (`( . , ; : ) = —` → closing: a
  source reference follows), then by a preceding `:` (→ opening), then by the depth (closing if a quotation is
  open). A `»` in an opening position with nothing open → opening.
- **Glyphs.** Opening `"` and misread `»` → `„`; closing `"` and `”` → `“`; `«` `»` `„` `“` kept.
- **Spacing.** No space after an opening or before a closing mark; a space is added before an opening mark that
  follows a word, punctuation or a closing mark (`харатьи"„` → `харатьи“ „`), and after a closing mark followed by
  a word, `(` or an opening mark (`„зрѣти"смотрѣть` → `„зрѣти“ смотрѣть`). Punctuation after a closing mark stays
  glued (the old tidy rule already removes the space before `.,;:)`).
- **Kept as is:** `(")` (the text names the sign itself: the ико/kamora, pp. 878, 996), and `„ « »` between two
  letters (noise inside a word, e.g. `муси„кію`) — the latter flagged.
- **Flag `quotes`**: a closing mark with nothing open, a quotation left open at the end of the entry, or a mark
  kept as noise. The `disputed` and `italic` spans follow through the index table.

## Verification (session 4)

- Only quotation marks and spaces changed (definition and head text): the definitions compared with the previous
  entries.tsv with quotes and whitespace removed are identical for all 25,362 entries; sep, part, page, col unchanged; `gram` changed in 10
  entries (quotes inside the parenthesised tag, now tidied); 55 provisional heads changed in their quotes only
  (6 of their keys, all long garbage heads, keep a final ъ now followed by `“`). links.tsv unchanged.
- All 145,780 `italic`/`disputed` spans cover the same text as before (compared with quotes and spaces removed).
- After (definitions): `„` 3,989, `“` 3,847, `«` 27, `»` 20, straight `"` 3 (`(")` twice, `8 "/ л.` once);
  floating quotes: 5, all a stray `„` at the very end of an entry (flagged). **275 entries flagged `quotes`** (198 with more opening marks,
  68 with more closing): OCR losses of one mark of a pair, the misread letters above, stray marks — for
  proofreading; listed in FLAGS.md.
- Ядамъ (p. 5b) checked mark by mark against scan A: all 9 quotations right (`„сотворимъ … по подобію“ (евр.`,
  `„Адамъ“`, `„дам“ =`, `„дама“=`, `„адама“ само`, `„Адам“, и`, `„Тлѣніе … осужденія“ (3 кан.`). A random sample of
  24 marks from unflagged entries: 15 could be checked on the scan (2 of them at another quotation of the same
  word), all right (direction, glyph, attachment); the other 9 were on a later page of a long entry, in a cut
  margin, or the crop found another word.
- `dj_eval.py` does not read entries.tsv — untouched by construction. PDF rebuilt; the Ядамъ page checked by eye.

## Still to settle before proofreading (Phase 5)

`dj_parse.py` regenerates `entries.tsv` from `ocr/*.json` on every run, so the plan's "fix the text in
`entries.tsv`, set status=checked" would lose the corrections at the next regeneration. Needed: a corrections layer
that survives — suggested `djachenko/corrections.tsv` (entry id, field, corrected value, note), applied by
`dj_parse.py` **after** tidying and the quote fix, carrying the `checked` status too. Corrections are final text.
