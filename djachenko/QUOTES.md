# Floating quotation marks — the defect and the planned fix (drafted 2026-09-19, not yet implemented)

**Status: open.** Raised by the user on the first Typst rendition: opening and closing quotation marks float
among the words, separated by whitespace on both sides. To be fixed before proofreading starts (see the last
section) and before the next rendition is shown around.

## The defect, measured on the merged text of all 1,119 pages

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

The book itself is consistent: `„…“` (low-9 opening, high-6 closing). The straight `"` is an OCR rendering failure,
not the print. ABBYY on A shows the same defect to a lesser degree.

## Where to fix it — the options along the pipeline

1. `dj_witness.reading_order` (the witness texts): **no.** They are evidence; the Phase 2 measurements and the vote
   are built on them as read; a typographic rewrite there would silently change what `dj_eval.py` scores.
2. `dj_heads.py` step 1 (`text_merged`): **no.** It is a character-level merge with `disputed`/`italic` spans in its
   coordinates; typography does not belong in it and would have to be redone whenever the vote rule changes.
3. **`dj_parse.tidy()` — the right step.** Typographic clean-up already lives there (spaces before `.,;:)`, after
   `(`, double spaces) with an old→new index table that remaps the spans. `entries.tsv` is what every consumer
   reads (links, proofreading, Typst); `ocr/*.json` stays the faithful record.
4. `dj_build.py` only: **no** — it would leave `entries.tsv` dirty for everything else.

## The rule set (in `tidy`, per entry)

- Decide the direction first, then the spacing. `„` is always opening; `“` is always closing in this book. A
  straight `"` is resolved by a small state machine per entry: depth 0 → opening, depth ≥ 1 → closing, with the
  spacing context as tie-breaker (glued to the left of a letter → closing; glued to the right → opening). The
  depth resets at the end of the entry.
- Normalise the glyph to the book's convention: opening → `„`, closing → `“`.
- Attach: remove the space after an opening quote and before a closing one; put a space before an opening quote
  when a letter precedes it (`харатьи"„`); no space between a closing quote and following punctuation
  (`исраильтянъ“ .` → `исраильтянъ“.` — the existing rule already does this part).
- Leave `’`/`‘` alone (apostrophes in transliterations and Greek). Leave the `headword` field alone (quotes there
  are noise that Phase 3b step 2 removes). The `disputed` and `italic` spans follow automatically through the
  index table.
- Unbalanced quotes in an entry (the OCR dropped one: the 186 `"` glued on both sides, the 61 `„` on the wrong
  side) get a flag `quotes`, so that they surface in FLAGS.md instead of being guessed silently.

## `«` and `»` — TO BE DOUBLE-CHECKED

The draft above assumed the 28 `«` / 24 `»` are genuine (quoted Russian sources). **The user doubts this and wants
it verified against the scans before the rule is fixed**: take every entry containing `«` or `»` (28 places — use the
¶ page.column reference and `tools/dj_inspect.py find LEAF «word»` to crop scan A and witness D) and see whether
the print has `«…»`, `„…“`, or something else (an OCR misreading of `„`/`“`, of a `„` broken by the line end, or
of the small CS type is plausible). Decide then: keep `«»` as printed, or map them to `„“` like the straight `"`.
Do the same spot-check for the three `’` and the one `‘`.

## Verification after the change

- Re-count: quotes with a space on both sides should be 0; opening and closing counts should nearly balance per
  entry; list the `quotes`-flagged entries.
- Sample ~30 entries with quotes against the scan via the ¶ reference (`dj_inspect.py find`).
- Re-run the span-alignment check (compare a paragraph's `disputed`/`italic` texts in `ocr/*.json` with the spans
  in `entries.tsv`, as done for leaf 341 `Мечка` in session 3).
- The eval is untouched by construction (its norm level maps every quote to `"` and ignores whitespace); confirm
  by re-running `dj_eval.py`.
- Rebuild the PDF (`dj_build.py`, 4 min) and look at pages with quotations (p. 113 = leaf 150 has several).

## A related point that must be settled before proofreading (Phase 5)

`dj_parse.py` regenerates `entries.tsv` from `ocr/*.json` on every run, so the plan's "fix the text in
`entries.tsv`, set status=checked" would lose the corrections at the next regeneration. Needed: a corrections layer
that survives — suggested `djachenko/corrections.tsv` (entry id, field, corrected value, note), applied by
`dj_parse.py` **after** tidying, carrying the `checked` status too. The quote fix belongs before that layer;
corrections are final text.

Estimated effort for the quote fix: about an hour (rules + flag + counts + checks), plus the `«»` spot-check.
