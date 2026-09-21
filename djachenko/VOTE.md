# The vote: how the text of an entry is decided between the four witnesses

Phase 3b step 1 (`tools/dj_heads.py text`, function `merge`) produces `text_merged` for every paragraph of every
page: witness D's text, corrected character by character where the other witnesses give reason to. This file states
the rules, the evidence each one rests on and the ways each one is known to fail, so that a rule can be judged and
changed without re-deriving it. The short form is the docstring of `merge`; the numbers behind the route are in
`eval/RESULTS.md`. Whenever a rule changes, `VERSION` in `dj_heads.py` goes up and the whole book is re-voted (80 s).

## The witnesses and the unit of the vote

| | engine | reads well | reads badly |
|---|---|---|---|
| **D** Cornell copy, Google Books | Google | civil text (1.5 % CER), Greek with its accents (2 %), Latin-script words, both margins | Church Slavonic headwords (as Latin or Greek look-alikes), italic abbreviations (as Greek), the "=" after the headword (drops a third), final ъ/ь, п/и/т/г in italics (as n/u/m/r) |
| **C** Indiana copy, Google Books | Google | the same as D | the same as D — C confirms D's systematic errors |
| **B** the 1993 reprint | FineReader (Russian) | civil text (3.8 %), "=", ъ/ь, the abbreviations | Greek and every Latin-script word (transliterated into Cyrillic look-alikes), CS type (и/н, а/л) |
| **A** the РГБ scan | FineReader (pre-reform Russian) | as B, italics flagged | as B, and both margins cut on 551 pages |

The text is compared at the **norm level** (`dj_witness.norm_char`): Church Slavonic letters folded to civil
ones, Latin look-alikes (a c e o p x y A B C E H K M O P T X i I) to Cyrillic, diacritics and whitespace dropped,
all dashes and all quotation marks made alike. A, B and C are aligned to D's norm sequence (Levenshtein); at every
norm position of D the vote sees D's character and what each of the others has there. Alignment is per column
side, not per page. The result: the merged text, the `disputed` spans (every place where B differs from D, with
`fixed` = B's reading was taken) and the `italic` spans (ABBYY's flags on A, carried along).

## The base rule

**D stands, unless B and A agree against it and C does not confirm it.** Then B's reading replaces D's.

Why: A and B are the same engine and share its confusions, C and D likewise; two engines against two is a tie,
and Google measured better. On the ground truth (session 3) the FineReader pair, where it contradicted D *with* C
confirming D, was wrong 14:0 on period/comma, and wrong on Latin letters and on и/н and а/л in Church Slavonic
type; a first version without the C condition made the headwords and the Greek worse.

Where B and D agree (95 % of the characters) the text is wrong in 0.13 %; of the errors that remain after the vote,
85 % lie inside a `disputed` span, so proofreading the spans catches most of them.

## The exceptions

1. **The "=" after the headword** — B (with A) wins even where C confirms D. Google drops a third of them; on the
   GT the pair was right 19:0.
2. **Final ъ/ь** — the same; right 9:3 on the GT.
3. **Google's script confusion, single letters** (VERSION 7) — D reads Cyrillic letters as Greek look-alikes
   ("чтο", "πρимѣру", and whole words of the Old Church Slavonic citation type: "Γλι" for "гдь"), and C, being
   Google, confirms them. The pair may replace a Greek letter of D when D's own letter run is mostly Cyrillic, or
   when the run is unaccented (real Greek here carries accents and breathings) and A and B read every letter of it
   as the same Cyrillic letter. The unit is the letter run, not the whitespace token: "(συνοδία)-спутники" is two
   words. Effect: definitions 1.02 % → 0.98 % on the GT, 1,335 Greek characters gone from the definitions, mixed-
   script words 890 → 558.
4. **Latin-script words** (VERSION 10, session 5) — when D's letter run is entirely Latin and contains a letter
   that has no Cyrillic twin (b d f g h j k l m n q r s t u v w z …), i.e. a word of the etymologies (Latin,
   Sanskrit, Lithuanian, Polish, Gothic …) or a Roman numeral, the pair may turn it Cyrillic **only with a word the
   book is known to contain** — a word of D's own lexicon (below) — or when **C reads the same as B** (three
   witnesses against one). A dispute that leaves the word Latin (a dash B has and D lacks, a diacritic) is not
   touched by this rule.
   Evidence (a sample of every 8th page, 140 pages): 1,135 such words that A and B both read as Cyrillic; 102 of
   them were disputes the base rule decided against D, and in 95 of those C did *not* agree with B. Looking at
   them, the pair had agreed on the same transliteration garbage — 'зоііз' for solis, 'зкііѵа' for skilva,
   'сгих' for crux, 'ѵага' for vara, 'ХІѴ' for XIV (izhitsa for V) — because both are FineReader set to Russian:
   their agreement is no evidence on Latin script. The book-wide effect of the rule: 146 entries changed,
   66 Latin words keep their letters (suar, pola, dimba, cracire, arquebuse, "alta и ara" p. 13), 4 come back from
   Cyrillic; ground truth unchanged (−4 errors on p. 8, +1 in unreadable garbage on p. 246 and on p. 682).
5. **Google's script confusion, whole abbreviations** (VERSION 10) — D reads the italic "греч." as "τρει.",
   "τρεν.", "ιρει."; "Пар." as "Παρ."; "Мак." as "Μακ.", "Апок." as "Αποκ.", "Григ." as "Γριι.", "отъ" as "οτι".
   An unaccented Greek run of D of three or more letters is replaced as a whole by the Cyrillic word B reads for it
   when that word is in the lexicon and A does not contradict — A reads nearly the same (one edit: 'грен') or
   nothing of the lexicon at all ('ч.ар', A's alignment slipping beside a garbled headword). When A and B read two
   *different* lexicon words ('Пар' / 'Дар'), the one the book uses more often wins (224 : 3). Effect: "греч."
   1,206 → 1,253 entries, "τρει."-type residue 46 → 10 (B failed there too).

**D's lexicon** (`build_lexicon`, `cache/d_lexicon.json`, git-ignored, rebuilt at every `text` run): the 36,247
Cyrillic words that D read at least twice anywhere in the book (`text_d` of `ocr/*.json`, letters only, lower
case). It is what "a word the book is known to contain" means in rules 4 and 5; FineReader's transliteration
garbage is never in it, Google's own systematic misreadings are under-represented in it ('пар' 224 although
"Пар." is far more frequent — D reads most of them as "Παρ.").

## Known failure modes

- **Latin word or Google's italic confusion?** D reads italic п и т г as n u m r, so "апр." comes out as "anp",
  "Сир." as "Cup", "тр." as "mp" — exactly the shape a real Latin word has. Rule 4 decides by the lexicon: 'апр',
  'сир', 'тр' are in it, so those are fixed; 'ага' (for ara) is not, so "ara" stays. A real Latin word whose
  FineReader transliteration happens to be a lexicon word would be turned Cyrillic ('саг' for car is not, 'зи'
  for su might be). The residue is a matter for proofreading; every such place is a `disputed` span.
- **Headwords in Church Slavonic type** are read by nobody; the vote's result there is garbage either way (p. 246
  "Kacakra" / "Kacakсa" for Касаюсѧ) and is replaced by the reading pass of step 2. The same for the Old Church
  Slavonic citation type (`caps` and `script` flags).
- **Deletions.** When B and A both have nothing aligned to a character of D and C does not confirm it, the base
  rule deletes it (the pair "agrees" on nothing). Usually right (a speck D read as a letter), sometimes not.
- **Look-alikes left in place.** The norm level hides a Latin look-alike inside a Cyrillic word ("Bce" with a
  Latin B, "Iep." with Latin I e p), so D's letters survive undisputed. A post-pass that folds look-alikes by the
  script of the rest of the word would fix these; not done yet.
- **Italic "отъ", "и" and the like read as Greek** (rule 5 fixes "οτι" → "отъ" where B reads отъ) — a genuine
  unaccented Greek ὅτι would be hit too, but D keeps the accents of real Greek, so an unaccented run is the
  italic Cyrillic in nearly every case.

## Measuring a change

1. `python3 tools/dj_heads.py text --pages 45,49,145 --force` on the pages in question, `dj_heads.py show LEAF N`
   for the A / D / merged text of a paragraph.
2. `python3 tools/dj_heads.py text --force` (80 s) and `python3 tools/dj_eval.py --refresh`: the GT scores in
   `eval/results.tsv`, candidate `merged`, compared with the committed file (the twelve pages have few Latin
   etymologies, so rules 4–5 barely show there).
3. `python3 tools/dj_parse.py`, then a diff of `entries.tsv` against the committed one, word by word, sampled: the
   book-wide effect is what matters.

## History

| VERSION | change |
|---|---|
| 4 | the vote as described (base rule, exceptions 1–2) — session 3 |
| 5 | italic spans from ABBYY's word flags carried through the alignment |
| 6 | the printer's sheet signature no longer read as text (`dj_witness.reading_order`) |
| 7 | exception 3, single Greek look-alikes |
| 8 | `norm_char` folds accented Latin letters like plain ones |
| 9 | `breaks`: the printed lines as offsets in `text_merged` (for the facsimile) |
| 10 | exceptions 4–5: Latin-script words and whole abbreviations, with D's lexicon — session 5 |
| 11 | witness B's word boxes in true page coordinates (`dj_witness.djvu_words` flipped them about the text layer's bounding box); B's text moves on 110 pages, nearly all gutter specks changing column — session 6 |
| 12 | the page footer looked for only on the pages that carry it (p ≡ 1 mod 16): the pattern also matched `(церк.-слав.)` in the text and cut off the foot of 8 pages — 98 witness lines restored, MISSING_HEADWORDS.md — session 6 |
