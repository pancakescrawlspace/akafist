# Progress log — Дьяченко digitisation

See PLAN.md for the phases. Newest entry last.

## 2026-09-19
- Investigated existing online editions: Azbyka and dhonorare.ru are page images; Wikisource index has no OCR layer
  and two transcribed pages. Conclusion: text must be produced from a scan (PLAN.md, "Findings").
- Wrote PLAN.md. No scan downloaded yet, no scripts written yet.

- Phase 0 decisions (user accepted the defaults of PLAN.md):
  1. Scope: build the full `entries.tsv`; render the akathist-lemma subset first, the full dictionary later.
  2. Headword encoding: civil pre-reform script (ѣ і ѳ ѵ ъ kept, no titla/superscripts) + normalised modern key.
  3. Proofreading: targeted — akathist lemmas first, then any PDF subset, then the rest as time allows; `status`
     column tracks it; unchecked entries marked in the PDF.
  4. OCR route: decided in Phase 2 by measurement.
  Phase 0 done.

- Phase 1 (same day, later): compared candidate scans; chose archive.org item 20200215_20200215_0856 (600 ppi) —
  see SOURCE.md. Found that it carries an ABBYY OCR layer with pre-reform orthography, character boxes/confidence and
  formatting (headwords and Greek garbled but detectable). PLAN.md revised (revision 2) accordingly: Phase 3 becomes
  "reuse ABBYY text; recover headwords + Greek", effort estimate halved.
- Wrote tools/dj_fetch.py; downloaded the metadata and OCR layers (verified); JP2 zip download started
  (`python3 tools/dj_fetch.py --jp2 --extract --convert --manifest`, log in djachenko/scan/fetch.log).

- JP2 zip downloaded and verified, 1,159 leaves extracted (pages/jp2/, 600 ppi) and converted to 300 ppi JPEGs
  (pages/NNNN.jpg, 3.9 GB). manifest.tsv built: all leaves status `image`; page map checked (printed page = leaf − 37
  for the dictionary proper, no gaps); sections front/main/back set. Phase 1 done except for the letter boundaries
  and the supplement start, which Phase 3a fills from the ABBYY layer.

- Phase 3a (second session, same day): wrote tools/dj_abbyy.py and ran it over all 1,159 leaves (6 s; deterministic,
  checked; headwords filled in later survive a re-run). Output: djachenko/ocr/NNNN.json (57 MB, schema in the script's
  docstring — it supersedes the sketch in PLAN.md) and ocr/report.tsv (per-page statistics and warnings).
  - Layout: column rule → gutter and deskew; header/footer/letter initials/specks set aside; lines grouped into
    geometric paragraphs (a new one at every flush line), in reading order across bands (a letter initial in mid-page
    splits the page into two bands). Checked by eye against the page images on leaves 102, 150, 155, 201, 303, 465,
    902, 1124 and 1157.
  - Result: 25,362 entry candidates in main + supplement, 22,542 of them with "=" in their first two lines ("=" signs
    in all: 24,483; the book's "~30,000 entries" is a round figure). Consistency indicators: ~44 likely false starts
    and ~10 likely missed starts in the unambiguous (geometric) part.
  - Found and handled: left margin cut off on 242 left-hand pages (123 main, 119 of 128 in the supplement) — first
    letters of headwords missing from the image; there entry starts come from position + text features (naive Bayes)
    and 3,197 paragraphs are marked `guessed`. 18 headwords exist only as ABBYY picture blocks (placeholder U+FFFC in
    the text). Paper patch over the lower left column of p. 1120. Details in SOURCE.md ("Scan defects").
  - manifest.tsv: section (front/main/blank/supplement/back) and letters per page, from the book's table of contents
    (leaf 37; pp. 865–1120 are a supplement "Прибавленіе" with its own А–Я sequence; p. 864 blank); the detected letter
    initials agree with the TOC except on 3 explained pages. Front matter corrected by hand: leaves 2–6 = pp. IV–VIII
    (leaf 1 first recorded as p. I with pp. II–III missing — wrong, corrected below to p. III). The OCR'd running-head
    page numbers confirm the page map.
  - PLAN.md revision 3: Phase 2 ground truth should include a cut-margin page (leaf 1124) and a long-article page
    (leaf 465); new Phase 2 questions 5 (segmentation accuracy) and 6 (cut-off headwords: context or another copy);
    Phase 4 gets the two alphabetical sequences (main/supplement) and Дьяченко's errata table (leaves 32–36).
  Phase 3a done.

- User decisions for Phase 2 (same day): (1) the user will check the ground-truth transcriptions (djachenko/eval/gt/);
  (2) look for other copies/scans of the book to triangulate the original text, in particular where this scan has
  the left margin cut off; (3) keep a precise record of every scan located, downloadable or not → djachenko/COPIES.md
  (also referenced from CLAUDE.md).
- Copy survey (session 2): 16 sources recorded in COPIES.md. They reduce to three physical copies ("witnesses"):
  A = the Russian State Library copy scanned by the Presidential Library (our scan; also archive.org
  polnyjtserkovnoslavjanskijslovarsovne27 and dyachenkos-dictionary-church-slavonic — identical images, same cut
  margins); B = the copy reproduced in the Moscow 1993 reprint (archive.org DyachenkoG…19931159p, B-001-027-578-ALL,
  both Wikimedia Commons files, Azbyka's PNGs — all with the same damaged letters; margins intact, title page
  present); C = Indiana University's copy (Google Books lgbgAAAAMAAJ, snippet view; HathiTrust blocked for automated
  access — the user is checking by hand). Tver diocese PDF and predanie.ru could not be fetched (404/400).
  Downloaded witness B: `python3 tools/dj_fetch.py --reprint` → djachenko/scan/reprint1993/ (DjVu 1,158 pp.,
  bilevel 300 dpi ≈ 237 ppi at original size, own OCR text layer; archive.org ABBYY XML; MD5-verified).
  Correction: leaf 1 is p. III, not p. I — the preface runs on from leaf 1 to leaf 2 (the "…а за симъ" line compared
  earlier was a footnote; confirmed by B and by Azbyka's transcription of the preface). Nothing of the preface is
  missing; pp. I–II (title page and verso) are not in scan A. Manifest and SOURCE.md fixed. PLAN.md revision 4.
- HathiTrust (user, by hand): the book is viewable but only single pages can be downloaded; agreed: hard pages on
  request (COPIES.md item 12). The user then downloaded three Google Books PDFs (full downloads work from the
  Netherlands); moved to djachenko/scan/google/ and identified: C = Indiana University's copy, a photo-offset reprint
  ("Reprinted by JUH", title page 1899), 2 vols; D = Cornell University's original copy (title page 1900), complete.
  Both bilevel 600 ppi with Google's OCR text layer, margins intact. D is now the best second witness.

- Phase 2 started (session 2): ground-truth conventions in djachenko/eval/README.md; transcribed (status draft, for
  the user to check): eval/gt/0045.txt (p. 8), 0517.txt (p. 480), 0660.txt (p. 623). Method: 600 ppi crops of scan A,
  line by line against ABBYY's reading; doubtful glyphs checked in witness D. Observation to measure: Google's text
  layer of witness D (Cornell PDF) reads the CS headwords far better than ABBYY does on A (e.g. p. 623: Смудреникъ,
  Смученикъ, Смышленіе, Смѣжаю и сомжаю, Смѣйна — all right; ABBYY: garbage) — a strong candidate for the headwords.

- Ground truth complete (session 2): all six pages in djachenko/eval/gt/ (0045 p. 8, 0517 p. 480, 0660 p. 623,
  1124 p. 1087, 0893 p. 856, 0465 p. 428; ~22,900 characters, 141 entries/paragraphs). The user checked 0045
  thoroughly (no error) and 0517 cursorily (no error); the rest are `status: draft`. The user asked that two
  conventions be explicit decisions, now in eval/README.md: spacing around "=" follows the (inconsistent) print and
  is ignored by the evaluation; CS accents/titla are not transcribed (Phase 0 decision 2).
  Findings while transcribing: (1) p. 856 (leaf 893) also has the RIGHT margin of col b cut off in scan A (line ends
  read in D) — Phase 3a only detects cut left margins; check how many pages have this. (2) p. 1087: in scan A even
  the indented lines of col a lose their first letter. (3) Misprints of the book itself, confirmed in D:
  "мꙋгленый" without С (p. 623), broken digit in "(Іер. 12, 4)" (p. 428). (4) In the small CS type и/н, в/к, б/в
  are hard to tell apart; Google's reading of D often gets the headwords right where ABBYY on A fails.

- Phase 2 measurements (session 3; the scoring itself was written and first run at the end of session 2 but not
  logged): tools/dj_eval.py scores four candidates against eval/gt/ — ABBYY on A, B's DjVu text, Google's text of D
  and of C (reading order rebuilt from word boxes; CER strict/norm, per zone hw/def/grc; segmentation of ocr/*.json;
  `--vote`, `--suspects`, `--show`); tools/dj_inspect.py (dump/overlay/lines/find across all four witnesses/gtcheck/
  segcheck). Results in eval/RESULTS.md, numbers in eval/results.tsv, candidate texts cached in eval/cand/.
  Headline numbers (norm): definitions — D 1.5 % CER, C 1.8 %, A 3.8 %, B 3.8 %; where D and B agree (95 % of
  characters) only 0.13 % is wrong; majority D/B/A 0.8 %. Headwords — every OCR ~48 % exact, majority 50 %; vision
  on a contact sheet of 600 ppi crops: 25/25 on a fresh page (leaf 341). Greek — ~14,700 words in the book, D reads
  them at 2 % strict CER; ABBYY garbles all. Segmentation — recall 99 %, precision 100 % on ordinary pages, 81 %
  among the guessed paragraphs of a cut page.
  New finding: scan A also lacks the RIGHT margin on 313 odd leaves (196 main, 113 supplement; last 1–4 characters
  of column b's lines); dj_abbyy.py now warns about it (re-run; only warnings changed), SOURCE.md updated. 551 of
  1,119 dictionary pages are incomplete in A on one side; D has both margins.
  Ground truth: `--suspects` (D and B agreeing against the GT) found 11 slips in the drafts, all confirmed on the
  images and corrected (0045: 6, 0465: 2, 0893: 2, 1124: 1 — see the files' headers; 0045 had been checked by the
  user before these). The 35 remaining disagreements are OCR errors. gtcheck's parentheses test fixed (it stripped
  the ")" of references).
  Route decided (PLAN.md revision 5, Phase 3b rewritten): text from D aligned to A's segmentation and voted with B
  and A, disagreements flagged; headwords by vision on crops with the witnesses as check; Greek from D. Phase 2 done.
  Open for the user: run the ~850 headword contact sheets through the API (~2 M tokens, unattended) or read them in
  interactive sessions; and the draft GT files (0465, 0517, 0660, 0893, 1124) still await the user's check.

- Phase 3b step 1 (session 3, continued): user decisions — go ahead with step 1; the user will check the five
  draft GT files later (not blocking); the headword reading route (API pass vs. interactive) is being reconsidered
  after a clearer statement of both options (API key billed separately, ~$10–25 with Opus 5, half with the Batches
  API; vs. 10–20 sessions of in-session reading) — no decision yet. Also: whatever runs must survive interruptions
  (per-page/per-sheet persistence, resumable).
  Written: tools/dj_witness.py (shared: witness word boxes and page mapping — D's PDF page = p + 48 and B's DjVu
  page = p verified over the whole book —, reading order with line/word spans, per-side texts, normalisation,
  alignment; dj_eval.py refactored onto it with identical results) and tools/dj_heads.py (step 1). Run over all
  1,119 pages (62 s): per paragraph text_d / text_merged / disputed / fixed / d_cut / d_line, per page a witness
  block (version 4). GT scores: definitions 1.0 % CER norm (D alone 1.5 %), Greek 1.5 %, headwords unchanged; 85 %
  of the remaining definition errors inside the disputed spans; 26,937/26,947 cuts on a D line start.
  Lessons recorded in RESULTS.md's addendum: A and B are both FineReader and must not outvote D on CS type or
  Greek unless C fails to confirm D (exceptions "=" and final ъ/ь); align per column side, not per page (band
  detection differs between witnesses); Google's precise boxes allow overlap-based line clustering (CS headwords
  are taller), B's coarse boxes do not. dj_abbyy.py writes the witness block and carries the paragraph texts over
  by box (verified byte-identical after a full re-run).

- Phase 3b step 2 pipeline (session 3, continued): dj_heads.py restructured into subcommands (text, show, crops,
  sheet, enter, read, collect, check, report). Crops: start of the entry's first line from the column's left edge
  (A's JP2; D's page rendered at 600 ppi on left-cut pages — a word box of D can miss the first letter, hence the
  column edge), 400 ppi JPEG, cache/crops/ (git-ignored). Manual path tested on leaf 341 (enter → check: 23 of 25
  confirmed by a witness, the 2 disputed are the two I had to zoom on earlier). API path written per the SDK
  reference (claude-opus-5, few-shot prefix with cache_control, JSON answer, direct or Message Batches with the
  batch ids recorded in heads_batches.tsv) but UNTESTED: no SDK installed, no key. dj_eval.py --heads scores the
  step-2 headwords on the GT pages (tested with a planted error). dj_abbyy.py carries headword/check fields over.
  Request size measured: ~110 image tokens per crop, ~3.5 M image tokens for the book (~$17 at Opus 5 input
  price); the model's output (thinking + answers, $25/M) may cost as much again — governed by the effort level.
  The user retracted the earlier "API pass" answer and asked for a clear statement of both options (given in the
  session); decision pending.

- Phase 4 first version (session 3, continued; user: "go ahead" with what needs no decision): tools/dj_parse.py
  → djachenko/entries.tsv (25,362 entries: 20,079 main, 5,283 supplement; 10 MB) and FLAGS.md. Entries from the
  hanging paragraphs, text = text_merged joined across columns and pages, split at the first separator; headword
  from step 2 where read (25 so far), else provisional from D (25,337 flagged hw_provisional; 874 hw_missing where
  Google skipped the CS headword); eq_from_A recovers the head where D dropped the "=" (863). Flags: order (LIS
  on the book's letter order, per part; meaningless until the headwords are read), parens (725, real: sense
  numbers excluded), no_sep (726: mostly continuations that Phase 3a took for entry starts on cut-margin pages —
  step 2's null answers will merge them), guessed, no_eq, odd_len, empty (19). Checked by eye on leaf 341 (all 25
  entries right, page-break continuation right, disputed spans still aligned after tidying). A page-level entry-
  count check was tried and dropped (a page of 81 short Въз- entries and a one-article page are both normal).
  Not done: Дьяченко's errata table (leaves 32–36 → errata.tsv; needs its own transcription session, Greek-heavy)
  and the manifest status column.

- Phase 5 step 1 (session 3, continued; user: "go ahead with dj_link.py"): tools/dj_link.py links the 703 akathist
  lemmas (modern civil forms with accents, verbs as infinitives; alternatives "в, во", "он, она, они",
  "избавля́ти(ся)" and glosses "(село)" handled) to entries.tsv by headword_key with fallbacks infinitive ↔ 1 sg.
  present and ь/ъ/й-insensitive comparison → djachenko/links.tsv (lemma, pos, match, ids, headwords, parts).
  With the provisional headwords: 243 linked (exact 229, verb 11, soft 3), 460 none — a lower bound until step 2
  (e.g. а́нгел, ами́нь, благи́й are unmatched only because D reads the CS initial А as Я). Matches sampled: right.
  entries.tsv must be read with csv.QUOTE_NONE (definitions contain quotation marks) — noted in dj_parse.py.

- Phase 6 first version (session 3, continued; user: match the ORIGINAL's layout, not the akathist dictionary's):
  tools/dj_build.py → djachenko/djachenko.typ + .pdf (git-ignored, regenerated in 4 min). Page measured on scan A
  (text block 169 × 249 mm, columns 82.5 mm, gutter 5.3 mm, pitch 12.6 pt, indent 4.9 mm) on A4; two columns with
  a rule, page number over a double rule, guide words (first three letters + dash) in CS type, running title +
  signature number every 16th page, letter initials (all 68 sections placed from the manifest's letters). Fonts
  fetched (OFL) into djachenko/fonts/: Ponomar Unicode (headwords), Old Standard TT (civil text, Greek). Marks of
  the edition: grey headwords where still provisional, small grey ¶ page.column refs, --marks underlines disputed
  spans; title page + "About this edition" page with the status figures. Whole book: 1,001 pages (original 1,120
  → ~10 % denser). Also: step 1 now carries ABBYY's italic flags through the alignment (VERSION 5; `italic` spans
  per paragraph and an `italic` column in entries.tsv), so sources and quotations are set in italics (partially:
  ABBYY misses some). dj_parse: eq_from_A off-by-one fixed; enum/list/heading markup escaped in the builder.
  Not yet in the rendition: Дьяченко's abbreviations list (front matter), the "checked" mark, the original's
  spanning letter initials (Typst places them in the column), the errata.

- ⚠ OPEN DEFECT (session 3, end; fixed in session 4, below): quotation marks float in the text (the OCR emits them as separate words: „ x " with
  spaces on both sides; straight " where the book prints “). Approach drafted in djachenko/QUOTES.md — fix it in
  dj_parse.tidy() (not in the witness texts, not in text_merged), with a per-entry opening/closing state machine,
  normalisation to the book's „…“, a `quotes` flag for unbalanced cases. The user doubts that the 28 «/24 » are
  genuine: check them against the scans before fixing the rule. Also in QUOTES.md: before proofreading starts, a
  corrections layer (corrections.tsv applied after tidying) is needed, because dj_parse regenerates entries.tsv.

- Quotation marks fixed (session 4; QUOTES.md rewritten as the record). `«»` check first, as the user asked: of the
  52 `«`/`»`, about 30 are genuine (the book prints `«…»` in some articles, pp. 577–846, and mixed pairs `«…“`,
  `„…»`), 4 are misread `„`/`“`, about 19 misread letters (`Соб»ство`, `«же` for ꙋже …); the 5 `’ ‘ ”` are noise.
  dj_parse.fix_quotes() (in split_entry; definition and head text as separate passes): direction by glyph, else
  by spacing, next printed character and depth; glyphs `„…“` (« » kept as printed); spacing attached; new flag
  `quotes` (275 entries: unbalanced — OCR losses, misread letters — listed in FLAGS.md). Checked: only quotes and spaces changed,
  all 145,780 italic/disputed spans still cover the same text, links.tsv unchanged, Ядамъ (p. 5b) and a random
  sample right against scan A.
  The user found a second cause at Ядамъ (PDF p. 7): Typst's smart quotes (lang "ru") turned straight `"` into
  `«`/`»`; dj_build.py now sets `smartquote(enabled: false)`. PDF rebuilt.
- ⚠ OPEN DEFECT (found during the check; FIXED the same session, below): the printer's asterisked sheet signatures (`3*`, `5 *`, `32 ’`, `64 ’` …,
  on pages ≡ 3 mod 16: number = (p − 3)/16 + 1) are not recognised as page furniture and end up in the text of
  column b's last lines — 38 entries found by a simple pattern, some mid-sentence (`дыханіемъ 5 * своимъ`), more
  in garbled form (`১*`, `1 6*`). Fix at the page level (drop the word(s) in the footer zone of D's page, or strip
  the expected number + `*` from the last lines of those pages in dj_parse), with the spans remapped.
- ⚠ OPEN DEFECT (Phase 4, found during the quote check; FIXED the same session, below):
  where D dropped the "=", the separator found is often a later "(" and D's head text holds the gloss and a
  quotation: `Инока- др. рус. инокиня. „Матери своей инокы Марѳы“` + `(Новг. л. 4).` As long as the headword is
  provisional this text is only misplaced (printed grey as the head); but with a step-2 headword split_entry keeps
  only the text after the separator, so the gloss would be LOST. 751 provisional heads have 4+ words (429 of them
  cut at "("). Fix: with a step-2 headword, look for the separator right after the headword's extent in the text
  (or prefer "=", "—" over "(" and the eq hint of A) and move any head text beyond the headword into the definition.

- Both open defects fixed (session 4, continued; user: "fix both open defects").
  1. Page furniture (`dj_witness.reading_order`): a foot line of one or two short words is dropped only when it
     lies below EVERY other line of the page — each candidate is now compared with the other lines, not with the
     bottom of all lines (which was the candidate itself, so the rule never fired) nor with the last body line
     (which would eat a short last line of a column, e.g. p. 36 "нахаль-|ство ."). Plus, on the pages that carry a
     signature (printed page ≡ 1 or 3 mod 16), a signature clustered INTO the lowest line is taken off its end when
     it is set in smaller type and reads as a number with an optional mark; digits of other scripts count as their
     value (the user's point: the book has no Bengali digits — p. 115 read `১*`).
     Measured against the committed version over all 1,119 pages × witnesses B, C, D: 232 witness pages changed,
     185 on p ≡ 3, 40 on p ≡ 1 (mod 16), 7 elsewhere — 5 specks (`і`, `V`, `\`, two strays), 1 hyphen artefact,
     and nothing else; every "lost" word with letters was a hyphen-join corruption being undone (`бла10* гость`
     → `благость`, `Сокра-` + `10`). dj_heads VERSION 6 → step 1 re-run over all pages (78 s, 0 errors, same
     alignment statistics); 78 definitions in entries.tsv changed, all signature removals; signature-like
     leftovers now 0 (were 38+); `quotes` 275 → 273. dj_eval --refresh: all 24 previously measured rows
     byte-identical (no GT page carries a signature), results.tsv now holds all candidates.
  2. Head text (`dj_parse.split_entry`): with a step-2 headword the separator is now looked for right after the
     headword's own words (window: from the start of its last word to 3 characters past it); if none is there the
     text is cut after those words, flag `hw_cut`, and everything else stays in the definition. Before, the first
     separator anywhere in the first 80 characters won, so a gloss or quotation that D had run into the head was
     dropped from the entry. Already true of one of the 25 read entries: `Механическїй` had lost "машиннымъ
     искуствомъ устроенный." and has it back. Provisional entries are untouched (no step-2 headword, same path as
     before); checked by simulating step-2 headwords on `Гадара`, `Инока`, `Стѣна плача`.
  PDF rebuilt; links.tsv unchanged.

- Repository restructured (session 4, end; user's request): the akathist project moved into `akathist/`
  (`akathist/source/`, `akathist/dictionary/`); `djachenko/` and `tools/` unchanged. The only path that mattered
  here: `dj_link.py` now reads `akathist/dictionary/dictionary.psv` (links.tsv unchanged after the move). README.md
  rewritten as two independent projects, with a Mermaid diagram of the Дьяченко toolchain and its sources; PLAN.md
  and CLAUDE.md paths updated.

- Script confusion fixed in the vote; the citation type flagged (session 4, continued; user, browsing the PDF at
  Нноходьцъ p. 223: Greek letters among Russian ones, and part-capitalised words).
  Diagnosis: both are the book's THIRD text class — Old Church Slavonic quotations set in a heavy uncial face,
  which no OCR reads. ABBYY's formatting does not mark it (same flags and font size as the civil text, checked on
  leaf 260), so there is no typographic signal to key on.
  1. FIXED — `Γλι` (D and C) vs `гдь` (A and B): Google reads Cyrillic letters as Greek look-alikes, and C, being
     Google, confirms D, so the vote's "two engines against two" rule kept the Greek. `dj_heads.merge` has a third
     exception now (see eval/RESULTS.md): A+B may fix a Greek character when D's own letter run is mostly Cyrillic,
     or when the run is unaccented and A and B read every letter of it as the same Cyrillic letter. The unit is the
     letter run, not the whitespace token — the first version rewrote genuine Greek in "(συνοδία)-спутники".
     VERSION 7, step 1 re-run over the book: GT definitions 1.02 % → 0.98 % CER, all 1.80 % → 1.75 %, Greek
     unchanged at 1.50 %; 528 entries changed, 1,335 Greek characters gone, mixed-script words 890 → 558,
     `order` 8031 → 7983. Sampled 16 changes: all right (τρεν→греч, Ακαθ→Акаѳ, Ηο→Но, βολα→вола …).
  2. NOT FIXED, flagged — the capitals (`ННОУЛДЫН ВМ. ЄдиноҮЛДЫН`). No safe rule: mostly-capital words are also
     Roman numerals and genuine abbreviations (Б. М., СВ.), and the letters are wrong anyway, so lowercasing would
     hide an unread passage behind a plausible word. New flags in dj_parse: `caps` (184 entries) and `script`
     (515), both listed in FLAGS.md. The route is in PLAN.md Phase 3b step 4: read these spans in the same vision
     pass as the headwords. The user's point stands — this is what a real reading pass is for.
  (The user read `Γλι` as "Где"; the scan shows `гдⷭь` with a titlo, i.e. Господь — the quotation is Ps 67:7,
  "Господь вселяет единомысленныя въ домъ", so A's and B's `гдь` is the right reading.)

- Ground truth: checked, then extended (session 4, end; user: "First check the drafts, then do the six new pages").
  Checking pass, all six files: the three witness pairings never used before (C+A, C+B, D+A) on top of D+B — 73
  places in all, 38 of them new; every position where a file stands alone against all four witnesses (75); and
  every headword of every page against a 400 ppi contact sheet (`dj_heads.py sheet LEAF`). The decidable places
  were read at 600 ppi. **No error found**; two scares were my own misreadings of the sheets, settled at higher
  zoom (p. 623 "Смрѣча" is ч; p. 1087 really prints "Синод." once and "Сѵнод." four times). The remaining
  disagreements are OCR errors or the documented и/н, а/ѧ ambiguity of the small CS type. Recorded in each file's
  header and in eval/README.md; it does not replace the user's own reading, which stays open for five files.
  Found while checking: `norm_char` folded look-alikes before stripping diacritics, so an accented Latin letter
  (á in the Sanskrit etymologies) stayed Latin while a plain one became Cyrillic — every candidate that read it
  plain was charged an error. Fixed (diacritics first); VERSION 8, step 1 re-run. GT scores: merged definitions
  0.98 % → 0.90 % CER, overall 1.75 % → 1.70 %.
  Why extend at all (measured, in case the plan is revisited): the definition CER of 0.98 % had a 95 % CI of
  0.4–1.5 % (per-page 0.33–1.66 %, sd 0.67); the Greek rate rested on **4 errors in 266 characters**; 132
  headwords give ±3.7 pp for scoring the vision pass; and the OCS citation type appeared on no page at all.
  Doubling similar pages would only shrink the CI by √2, so the six new pages are chosen for coverage
  (eval/README.md has the table and the held-out rule).
  **gt/0719.txt (p. 682) done** — the Greek-densest page. Transcribed from 600 ppi crops in 10–14 line chunks, each
  line against ABBYY, the Greek against D; then the same checking signals as above. One correction to my own draft
  came out of the "stands alone" signal: "есть собственно {ꙗ}" (the letter discussed, printed in CS type as the
  І+А ligature) where I had first read "к" — all four witnesses are wrong there too. The headword type does
  distinguish ѧ from а at 600 ppi (triangle with splayed legs vs round bowl), confirmed by the alphabetical run
  Стѧгъ → Стѧкльство. Now 7 GT pages, 142 headwords; merged norm 1.6 % all, 0.9 % definitions, 1.3 % Greek.

- gt/0801.txt (p. 764) done, the second Greek-dense page: 8 GT pages, 168 headwords; merged norm 1.9 % all,
  0.9 % definitions, 1.1 % Greek. Two corrections to my draft came from the witness check ({Оустраннопрїимствовати},
  {Оусъньнь}); one place where the witnesses agree against the file was kept — the book prints "зависгливо" with г
  and both OCRs normalise it away.
- The `caps` flag over-counted: garbled Roman numerals (ХП for XII, ХШ for XIII, ХѴП for XVII) looked like
  capitalised words. dj_parse now maps the Cyrillic look-alikes and the ligature readings before the numeral test;
  caps 184 → 159 entries, on 150 pages. That also killed the reason for choosing leaf 1104 as the citation-type
  page — its flags were all numerals — so the GT list now uses **leaf 260 (p. 223)**, where the type was seen and
  verified in this session ("ННОУЛДЫН ВМ. ЄдиноҮЛДЫН"). A page carrying it cannot be found by the flags alone;
  look for the uncial face on the image.

- Ground-truth extension finished (session 4, end): all six pages done — 719 (p. 682) and 801 (p. 764) for the
  Greek, 260 (p. 223) for the Old Church Slavonic citation type, 146 (p. 109) with its 81 entries, and the two
  held-out random pages 283 (p. 246) and 696 (p. 659). **12 pages, 325 headwords**; merged norm 2.3 % all, 1.2 %
  definitions, 1.5 % Greek, 139/325 headwords exact. Numbers and the caveat about the hard pages: eval/RESULTS.md
  (addendum), the table of pages and the held-out rule: eval/README.md.
  Each page was checked as the old ones were (witness pairings, the stands-alone comparison, headword crops); the
  check found one error in my own draft on nearly every page — {ꙗ} read as к (p. 682), прїимствовати and Оусъньнь
  (p. 764), Иновольнаа (p. 223), карина (p. 246), γραΐδιον (p. 659) — which is the rate to expect from a first
  transcription, and the reason the signals are worth running.
  Segmentation on the new pages: p. 109 (81 entries) 100 % recall and precision, p. 246 likewise, p. 659 (cut
  margin) 100 % / 94.7 %.

- Headword crops consolidated (session 4, continued; user: crops of all the headwords from all four scans, saved
  in the repo, with a file of their locations). tools/dj_crops.py:
  - `index` → **djachenko/headwords.tsv** (101,448 rows = 25,362 entries × 4 witnesses, 7 MB): the headword box
    in each witness's own pixels, the page inside that witness's source (leaf / DjVu page / PDF page / volume),
    the strip it was cropped into and the rows it occupies there. Located: A 25,362, B 25,357, C 25,293, D 25,359
    — essentially everything. A's box is ABBYY's Church Slavonic type run; D's comes from the entry's first line
    recorded by step 1; B's and C's by aligning their column text to A's, as the vote does. The line is cut at the
    separator ("Метехати = …", "Метненїе—…"), so the box is the headword, not the whole line.
  - `crops` → **djachenko/crops/<W>/NNNN.png**, 4,452 strips, 134 MB (A 35, B 21, C 38, D 40): one image per page
    and witness with that page's headwords stacked, at full 600 ppi, 1-bit PNG. One file per headword would have
    been 101,448 files and ~1 GB; a strip per page keeps git workable and a single headword is still one crop
    away — `Image.open(strip).crop((0, y0s, width, y1s))`, no scans needed.
  Two things worth remembering: Pillow's `convert('1')` dithers, and dithered paper grain is noise that PNG cannot
  compress (169 KB a page against 35 KB for a plain threshold at 165) — that one change decided whether this fits
  in the repository at all. And the temporary 600 ppi page renders of B, C and D must be deleted as they are used,
  or a full run leaves tens of gigabytes in cache/.
  **The crops are NOT committed** (decided with the user after measuring the account's Git LFS budget): the
  billing usage report (`gh api /users/<user>/settings/billing/usage`, needs a token with the `user` scope — the
  old shared-storage endpoint is gone, HTTP 410) shows **801 MB of the 1,000 MB free LFS storage already in
  use**: orthodoxy 613, orthodoxy-private 74, heiligenjaar 54, kerkmuziek 33, kummer 27; bandwidth 0 of 1,000 MB
  this month. Adding these 134 MB would leave no headroom, and LFS storage counts every version ever pushed and
  is not freed by deleting the files later, so one regeneration at other settings would go over. The repository
  keeps the coordinates (headwords.tsv, 7 MB of text) and the script; `dj_crops.py crops` remakes the images.
  `djachenko/crops/` is git-ignored.
  (An LFS migration was made first and then undone. If it is ever wanted: `git lfs migrate import` needs
  `--exclude-ref=refs/remotes/origin/master`, or it rewrites every commit including those already pushed, and the
  push then needs --force. `git lfs checkout` is needed afterwards, or the working tree keeps pointer stubs.)
  Checked: slicing five entries out of the strips with nothing but headwords.tsv gives the same headword from all
  four copies side by side (Метати, Метехати, Метненїе). B's crops carry a sliver of the next line, because B's
  line boxes are coarse; C's sometimes keep the "=".

- Errata transcription started (session 4, end; user: hold the headword scan, do the errata meanwhile).
  **djachenko/errata.tsv**, leaf 32 (p. XXXIV) done: 43 rows, dictionary pages 5–79. Columns: leaf, row, page,
  line, where (сверху/снизу), col (лѣвый/правый), printed, read, note. The table's repeat marks ("—", "„") are
  resolved to explicit values; three cells in Church Slavonic type are marked [?] and need a second look
  ({Боукари}, {вѣлило}, {Великооувенъ}); row 17 is an instruction, not a substitution ("одно о лишнее").
  Method (the table is a five-column layout that ABBYY reads as a jumble, and the Greek it garbles entirely):
  scratch scripts crop the page at 600 ppi — full-width bands of ~10 table rows to read the locators and pair the
  two halves, then the Напечатано | Слѣдуетъ читать block alone at ~1600 px for six rows, and single rows at
  ~2000 px where a diacritic decides the correction. Many corrections ARE a single accent or breathing
  (ἀγνός → ἁγνός, χώριον → χωρίον, ὄροψος → ὄροφος), so the high zoom is not optional.
  Useful to know for the rest: in this face ѧ is the triangular shape and ѫ the ж-like one (p. 7
  съмѣреномѧдрье → съмѣреномѫдрье).
  Leaf 33 (p. XXXV) done as well: 53 rows, dictionary pages 80–161; 96 rows in the file so far, and their page
  numbers run monotonically, which is a useful check because the table is ordered by page. Seven cells are [?]:
  mostly Church Slavonic words where only an accent moves, and three Greek breathings.
  tools/dj_errata_bands.py now has the three modes the work needs: `--bands N` (full width, for the locators and
  for pairing the halves), `--rows N N N` (those rows alone at 2000 px, for the marks) and `--right N`.
  Leaf 34 (p. XXXVI) too: 50 rows, pp. 170–273; 146 rows in the file, still monotonic by page, 14 cells [?].
  Two of its rows are guide words at the head of a page ({Жат—} → {Жаж—}), not text in an entry, and one locator
  is a single brace over three printed rows ("194 … 195 … и др."), which the applier will have to allow for.
  Leaf 35 (p. XXXVII) too: 51 rows, pp. 284–677; 197 rows, monotonic. Two of its rows correct a page NUMBER in
  the print (356: "страница 256 → 356"), not text. Row 47 is a nice cross-check: p. 623 {мꙋгленый} → {Смꙋгленый}
  is exactly the misprint the ground truth of that page records as printed.
  **Leaf 36 (p. XXXVIII) done — the errata table is fully transcribed: 234 rows, pp. 5–1119, monotonic by page**
  (32: 43, 33: 53, 34: 50, 35: 51, 36: 37); 126 in the left column, 103 in the right, 5 with no column. 18 cells
  carry [?] and want a re-read at maximum zoom — nearly all Church Slavonic words where only an accent moves, and
  a few Greek breathings. 13 rows are not substitutions in an entry: guide words at the head of a page
  ({Сал—} → {Сак—}), page numbers in the running head (2050 → 1050, "страница 256 → 356") and two instructions
  ("одно о лишнее", "4 раза встрѣчается υψος вмѣсто ὕψος"); the applier must skip or special-case them.
  Left to do: then the applier — each row
  names page, column and line counted from the top or the bottom, and A's geometry has exactly that, so the target
  line can be located, the entry found and "напечатано" replaced by "слѣдуетъ читать" with a flag. Matching on the
  printed string as well as on the line number guards against off-by-one counting. The corrections layer
  (corrections.tsv, QUOTES.md) should come first or alongside: dj_parse regenerates entries.tsv on every run.

- Errata applied (session 4, end; user: "try it"). tools/dj_errata.py + a step in dj_parse.build_entries /
  split_entry, so the corrections are made while entries.tsv is built and survive every regeneration.
  How a row finds its place: the page's columns of the named side give the printed lines, so "19 сверху" or
  "4 снизу" picks a line and with it a paragraph and an entry; then the STRING decides — `напечатано` is looked
  for exactly, then folded to the norm level of dj_witness, then folded to letters and digits alone (the OCR
  drops and adds full stops: "Панд . Акт" for "Панд. Акт."), first in that paragraph, then anywhere on the page
  if exactly one place holds it. A substitution changes the length, so the disputed and italic spans are moved
  with it (dj_errata.apply_to takes the span lists, as tidy and fix_quotes do).
  Numbers: of 234 rows, 202 are substitutions we can apply (18 are [?] readings, 12 are not entry text, 2 have no
  usable locator); 200 locate, and the printed string is found for 166 → **165 entries flagged `errata`**, 34
  rows flagged `errata_missed` and listed in FLAGS.md with their strings.
  The 34 misses are not a bug and cannot be fixed by better matching: Дьяченко corrects what the BOOK prints,
  while our text is the OCR's reading of it, and where the OCR already misread the word there is nothing to
  replace — they are mostly Church Slavonic words ({Ѩꙁы́къ}, {Трѣлостоѧ́тельница}), Greek the OCR renders
  differently (σομπλήρωμα, λιθοστρωτόν) and a few references. They need the page image, so they are listed for
  the proofreading pass.
  Checked: p. 623 {мꙋгленый} → {Смꙋгленый} (the errata corrects a HEADWORD, and it is the misprint our ground
  truth of that page records), p. 889 "Панд . Акт" → "Панд. Ант."; no span of any entry is out of range after
  the substitutions; links.tsv unchanged.

## 2026-09-20 (session 5)

- Feasibility of a line-for-line facsimile (user's question, not in PLAN.md before: can the Typst rendition have
  every line, column and page as in the book? Two preconditions — one edition among the witnesses, or a witness we
  can pick without trouble; and the metadata in the repo). Answered, recorded as **PLAN.md revision 6** (Phase 6).
  1. One typesetting: `dj_inspect.py linecheck` (new) aligns every printed line start of A, B and C onto D's text
     and counts those that fall on a D line start. Whole book, 1,119 pages, 3 min → eval/linecheck.tsv:
     B 99.78 % / C 99.72 % / A 98.78 % of their line starts (A 99.5 % on the sides whose margin is intact; the
     left-cut sides lose the first letters and with them my 2-character tolerance); D's line starts hit 99.4 %,
     99.5 %, 98.4 %; no page or column disagrees as a block. Residue looked at: Google splits a lone "=" or a tall
     headword into its own "line", ABBYY adds speck lines, B's DjVu text layer drops the last lines of some pages
     (p. 894: the image has them — checked) and lets guide words in. Title pages: C 1899, D 1900, same setting
     but for the year line, both with the censor's permission of 21 Sept 1898. B's "175·об." on p. 1087 (COPIES.md)
     is a speck in copy B. So the witness choice is moot; A's geometry stays the source. COPIES.md updated.
  2. Metadata: ocr/*.json hold every line (124,548 in main + supplement) with bbox, baseline, ind, fs, text; the
     columns, bands, initials; 26,947 paragraphs, 1,585 continuing over a column/page; pitch 102 px = 12.24 pt.
     Missing: the mapping of text_merged/entries.tsv onto the lines (derivable in step 1 as the italics are), and
     the line-end hyphens of column b on the 313 right-cut pages (13 % hyphenated there against 26 % elsewhere,
     ~2,300 lost with the margin; D has them but is on disk only). Design and effort in PLAN.md Phase 6 Rev. 6.
  3. The type: a one-page prototype (p. 113, lines `place`d at their measured baselines, justified to the column)
     works mechanically, but at 10 pt Old Standard a line is 78 % as wide as printed. Printed x-height 6.2 pt,
     cap height 8.9 pt ≈ Old Standard 12.5–13.5 pt; widths ≈ 12.7 pt; on a 12.24 pt pitch. The user allows a
     larger page: measured with `typst query` on 1,214 justified lines of 16 pages, 12 pt at page scale 1.08 or
     11 pt at 1.04 leave ≤ 2 % of lines overlong (mostly ABBYY-garbled headword lines) — table in PLAN.md.
- **Bug found and fixed: `dj_witness.c_page`** put C's volume boundary at p. 572; v1 ends with p. 567 (page 613,
  its text layer truncated to 8 lines) and v2 opens with p. 567 on page 9, so pp. 568–572 pointed at v1's blank
  pages and C was silently absent there (the linecheck showed it: C "missing" on leaves 605–609). Now pp. 1–566
  from v1, p. 567 on from v2 (also in dj_inspect.py's own copy of the mapping). Re-done for leaves 604–609:
  step 1 (`dj_heads.py text --pages 604-609 --force`; 45 entries changed, C now confirming D there as on every
  other page — gains like Сддовїе → Садовїе, (φυтόѵ) → (φυτόν), and D's usual quirks under the usual rule),
  dj_parse (entries.tsv, FLAGS.md), dj_link (242 linked, one fewer: сад → the provisional headword now reads
  Сада; back with step 2), `dj_crops.py index` (only the 115 C rows of those leaves changed; C located
  25,359/25,362 now) and the six C strips (`crops --pages … --witness C`, two of them with --force — `crops`
  skips a strip that exists; git-ignored anyway).
  Lesson: `dj_crops.py index --pages` writes ONLY those pages' rows (it would truncate headwords.tsv); re-index
  the whole book (37 s).

- **The facsimile built** (session 5, continued; user: "go ahead with the facsimile"). PLAN.md Phase 6 Rev. 6
  now describes what exists. `python3 tools/dj_build.py --facsimile` → djachenko/facsimile.typ + .pdf
  (git-ignored; 16 s for the book): **1,120 dictionary pages** (1,119 + the blank p. 864) after two front pages,
  124,435 lines placed, page 215 × 315 mm at 12 pt / scale 1.08; **509 lines condensed** (0.4 %): 347 by < 6 %,
  128 by 6–20 % (Greek-heavy lines, D's word-order slips), 35 by more — alignment/OCR defects (`odd_len`
  entries, the 9 `aligned` cuts), listed in facsimile_over.tsv (git-ignored). Spot-checked against the scan:
  pp. 1, 31, 113, 115, 166, 536, 865, 994, 1087 — the same lines, initials, number, guide words, signatures.
  The three steps as built:
  1. dj_heads.py VERSION 9: per paragraph `breaks` = [offset in text_merged, hyphen] per printed line, one per
     line of A's paragraph (A's line starts through the alignment, snapped to D's line starts within 4
     characters; the hyphen is A's where A's line end is in the image, else D's — a D line joined without a
     space). Whole book re-run (80 s): 124,497 lines, every paragraph's count equal to A's, 34,793 hyphenated
     ends (A alone showed 32,807 — the right-cut pages' hyphens came from D). Text unchanged.
     dj_abbyy.py: `header.base`, `header.guide_base`, `footer_base` (the furniture's baselines; needed a full
     regeneration — key order of the carried-over paragraph fields changed too, semantically identical, checked
     on 9 pages) and the printer's sheet signature "N*" set aside as footer (SIG_LIKE; it had been the last text
     line of column b on 49 of the 70 p ≡ 3 (mod 16) pages, plus a bare number on 2 p ≡ 1 pages; 51 lines
     fewer, 3 definitions changed — "дождева 68," → "дождева,").
  2. dj_parse.py: `lines` column (offset in the definition, negative in the head, "h" = hyphenated end), the
     line spans remapped by tidy/fix_quotes/errata like the other spans; 124,497 items, every entry's count equal
     to the A lines of its paragraphs.
  3. dj_build.py --facsimile: no column flow — every line `place`d at its measured baseline and x (deskewed on
     the rule; column width 1927 px; the nominal first baseline = the first line's, or the page number's + 240 px
     on the pages that open with a title), justified to the column with a forced break (the entry's last line
     ragged), condensed in Typst (`measure` + `scale(reflow)`) when wider than the column and reported through
     `<over>` metadata; number over its double rule 240 px above, guide words 125 px above (from the page's first
     and last entry), "Прибавленіе." on supplement pages, signature line / "N*" below the last line, initials and
     titles fitted into their scan boxes (Ponomar for the letters, the letter from the TOC tables), a paragraph
     ABBYY stored as a picture (no lines in A) flowed at the pitch. p. 1 gets no number (the print has none;
     ABBYY's "number" there is bleed-through) — the rule: a number where the OCR read digits or nothing stands
     above the first line.
  Measurements behind the defaults: printed x-height 6.2 pt, cap height 8.9 pt, widths ≈ Old Standard 12.7 pt on
  a 12.24 pt pitch; at 12 pt / 1.08 the natural line is 93 % of the column (table in PLAN.md). Fonts unchanged.
  Not in the facsimile: the book's front matter (lines in ocr/, no voted text), CS type inside entries, italics
  beyond ABBYY's; and the text defects the flowing rendition has too.
  Lesson: Typst's `measure` inside `context` ignores a `set text` in the same block — wrap the content in
  `text(...)` instead; a `box(width: 0pt, align(center, …))` wraps multi-word content at width 0 (use
  `move(dx: -w/2)` with an explicit width).

- Facsimile, three defects the user found on pp. 20 and 53 (session 5, end): (1) Апокрифы's lines set deep in
  the column and unevenly — ABBYY had read only the right part of those lines (boxes starting mid-column, `ind`
  2), and the build placed such lines at their box; now every continuation line sits at the hanging indent, a
  line keeps its own deeper position only when it is short (≤ 20 characters: a verse, a formula). Also, since
  A's line starts were wrong there, the breaks fell mid-line: step 1 now takes D's k-th line start where A's
  cannot be carried over and D has as many lines as A (measured: 99.6 % of A's line starts snap onto D's; of the
  0.4 % that do not, four in five sit in such paragraphs). Whole book re-run; Апокрифы's eight lines are now the
  printed ones (Аполинъ merged into it stays an A segmentation slip, flagged odd_len). (2) Богородичны's lines
  ran into the rule: p. 53 is a left-cut page, where the fitted flush edge of column a was 80 px too far right;
  the columns' edges now come from the rule with book-wide constants (FLUSH_A −2001, FLUSH_B 66 px). (3) The □
  marks: the placeholder for an entry without a headword (874); 731 of these have no separator either — they
  are continuation lines the segmentation took for entry starts, mostly on the cut-margin pages — and are now
  set indented without a head; the 143 real entries whose headword the OCR did not read keep the □ (the note
  says so). Condensed lines 509 → 415.

- The vote, exceptions 4 and 5 (session 5, end; user's finds on pp. 12–13: "τρει." for the italic "греч.", and
  "alta и ага" for "alta и ara"). Both were rules, not corrections. VERSION 10 of dj_heads.merge:
  (4) a Latin-script word of D (a letter without a Cyrillic twin) may be turned Cyrillic by the FineReader pair
  only with a word of D's own lexicon (36,247 Cyrillic words D read twice or more, cache/d_lexicon.json) or when
  C reads the same as B — measured on every 8th page: of 102 such disputes the base rule decided against D, 95
  had C disagreeing with B, and the pair had agreed on the same transliteration garbage ('зоііз' for solis,
  'сгих' for crux, 'ХІѴ' for XIV): the vote was corrupting most Latin-script words of the etymologies;
  (5) an unaccented Greek run of D (3+ letters) is replaced as a whole by B's Cyrillic lexicon word when A does
  not contradict (one edit, or no lexicon word), two different lexicon words decided by frequency ('Пар' 224 :
  'Дар' 3). Three slips of my own on the way: a per-position replacement left "гречч."; a guard demanding a
  Cyrillic replacement blocked disputes about a dash after a Latin word ("jurny — похотливый" lost its dash);
  B's error was preferred over A's correct "Пар." until the frequency rule went first. Whole book re-voted
  (3 ×); GT: definitions 1.18 % → 1.17 % (−4 errors on p. 8, +1 each in unreadable garbage on pp. 246, 682);
  book-wide 146 entries changed, "греч." 1,206 → 1,253 entries, "τρει."-type residue 46 → 10 (B wrong too),
  66 Latin words keep their letters; links.tsv: но lost one entry (its provisional head changed), о́браз gained
  one — 246 linked as before. entries.tsv, facsimile and flowing PDF rebuilt.
  **djachenko/VOTE.md** written (the user asked whether the rules deserve a file of their own): every rule with
  its evidence, the lexicon, the known failure modes (Latin word vs Google's italic n/u/m/r; look-alikes hidden
  by the norm level, "Bce"; deletions), how to measure a change, the VERSION history.

- Exploratory (session 5, end; user's question): a hand-made OCR for the Church Slavonic headwords from the
  crops, glyph templates from a CS font. Looked at p. 480's headwords in A and D beside Ponomar Unicode at the
  print's size: the same Synodal design, letter for letter (ѧ, ꙋ, ї, ж, т), the print a heavier cut — usable
  after emboldening, better still with templates averaged from the ~350 labelled headwords (12 GT pages + 25
  read). Kinds of headword: ABBYY's `?` flag on the first word separates the CS-type ones (~40 % of a sample of
  first words) from the civil bold ones of the supplement, which the OCRs already read; Greek/Hebrew heads are a
  handful. Estimate given to the user (no decision): (a) analysis-by-synthesis — candidates from D's reading and
  the known confusion pairs (и/н, а/ѧ, в/к, ъ/ь, о/ѡ, у/ꙋ, е/є, і/ї), each rendered and scored against the crops of
  all four witnesses with a width-tolerant match, plus the alphabetical-order prior: 1–2 sessions, 85–95 % words
  expected, no segmentation; (b) a segmenting template OCR with self-trained templates and a Viterbi decode over
  D's reading and the sort order: 3–5 sessions, ~90–95 % words, diacritics/superscripts/touching letters the
  risks. Either is worth having as a second, free witness beside the vision pass (25/25 on a page, ~$17–35 for
  the book), which stays the cheaper sole reader.

## 2026-09-21

- Session 6 (bug-hunt from the PDF; the user was reading facsimile.pdf and flagged two pages). **Two defects, both
  present since the first entries.tsv** (checked out all twelve commits that touched the file — not a regression
  of the recent facsimile/vote work):
  1. *p. 20 `Аполинъ` inside `Апокрифы`.* A faded patch over the left of column a; ABBYY read only the right half
     of six lines there, so the flush line `Аполинъ` measured as indented (x0 1161 instead of ~280) and
     `dj_abbyy.py` began no paragraph. The same page swallowed `Аξіосъ` into `Анѳѵпатъ`.
  2. *p. 21 `Япрілій` inside `Япракосъ`.* The segmentation was right — it was its own paragraph — but D read
     `Апрілій—` as `Япрілій-` and `др.` is not in dj_parse's ABBR list, so no separator matched, headword and
     separator both came out empty, and `dj_build.entry_lines` had `cont = not headword and not sep`, which sets
     such an entry indented and without a head. A real lemma printed as a continuation line of the article above.

- **A new witness check: `tools/dj_seg.py` (PLAN.md Rev. 7, Phase 3b step 1c).** Measured first: witness C's
  narrowest outer margin over the book is 27.5 pt and *no* line of it touches an image edge; D's minimum is 0.1 pt,
  148 sides have a line at the edge, and D's disagreement rate with A rises from 2.9 % to 10.5 % as its margin
  narrows (the user asked whether D has cut margins — it does, C does not). So C is the better geometric witness
  and the two are voted. Per column side: step 1's voted text aligned to the witness, A's printed lines (`breaks`)
  carried over and snapped to the witness's line starts, the indentation level read off the new
  `dj_witness.indent_levels`. Three things had to be got right, each found by a wrong answer first:
  - *Deskew.* The Google columns drift by up to 13 pt down a page — more than the 11.1 pt hanging indent — so no
    absolute edge works (leaf 145: flush lines at 37 and 40.6, hanging ones at 41.5 at the top of the same
    column). The skew is found by folding the left edges modulo the indent and maximising the concentration: both
    levels then fall on one peak, whatever their proportion. Without it the check reported 5,107 missed starts.
  - *Which level is the flush one.* Geometry cannot say: a column may lie wholly inside one long article (no
    flush line at all) or hold nothing but one-line entries (almost nothing else). Anchoring on the justified
    right edge failed (ragged columns), and on the column pitch too (it is itself bimodal, contaminated by the
    same ambiguity). A settles it instead — one yes/no per column decided by ~50 lines that A reads right 99 % of
    the time — and the witnesses decide the individual line.
  - *One line of A per line of the witness.* Where ABBYY's reading is destroyed, two of A's lines reach for the
    same witness line; the verdict then depended on the segmentation it was meant to correct and the pipeline
    oscillated (p. 167 `Євшанъ`). Requiring the match to be injective settled it. A line with fewer than four
    letters is a speck, not a line, and gets no verdict (those had produced empty entries).
  Result: 124,497 printed lines, 96 % carried over to both witnesses, **C and D agreeing on 99.8 %** of those —
  the same order as the 99.7 % of `linecheck`, and independent evidence for the one-typesetting finding.
  `djachenko/segmentation.tsv` (119,461 rows, 2.3 MB) holds the verdict for every such line and is **committed**:
  it is the witnesses' reading, not a diff against A, so the scripts may be re-run in either order and a rebuild
  without the Google PDFs still gets the entry boundaries right. `dj_abbyy.py` reads it when it groups lines into
  paragraphs (keyed by the line's baseline, which no re-run changes), counts how often it overruled A (page key
  `seg`), and marks each paragraph `seg: "CD"` (the witnesses' start, not A's) or `seg: "A"` (no witness reached
  the line). Against A's own geometry: **232 entry starts added, 636 withdrawn.**

- Also fixed, all three found while doing the above:
  - `dj_abbyy.carry_over` kept the Phase 3b text of a page whose paragraph *count* was unchanged even when the
    boxes had moved, so a page with one split and one merge kept `breaks` for lines it no longer had. It now
    requires the box to be the same one (IoU > 0.9) and that every new paragraph got a text; this was what stopped
    the pipeline reaching a fixed point.
  - `dj_parse.split_entry`: when no separator is found at all, the head is now cut after as many words as ABBYY
    read of the headword region (flag `hw_from_A`), as it already did when A had seen an "=" (`eq_from_A`). A
    missing separator is exactly what leaves the headword inside its own definition.
  - `dj_build.entry_lines`: `cont` now also requires the flag `guessed` — only an entry whose start no witness
    could confirm is set as a continuation line.
  New flags in entries.tsv: `seg` (235, the entries the witnesses added), `unconfirmed` (653, no witness reached
  the start), `hw_from_A` (456). Gone: `no_sep` (was 726).

- Rebuilt end to end (dj_abbyy → dj_heads text → dj_seg → dj_abbyy → dj_heads text → dj_parse → dj_link →
  dj_crops index → both renditions), and the loop verified to reach a fixed point (two iterations with nothing
  left to correct). **24,959 entries** (was 25,362). FLAGS.md: `guessed` 3,197 → 244, `hw_missing` 874 → 132,
  `parens` 723 → 422, `quotes` 272 → 262, `order` 7,977 → 8,086 (more entries now have a headword to sort).
  `headwords.tsv` rebuilt (99,836 rows, all 24,959 located in A). links.tsv: 252 lemmas matched, was 247.
  Both PDFs rebuilt; pp. 22 and 23 checked by eye — `Аполинъ` and `Япрілій` now stand as their own lemmas.

- Written up: PLAN.md Rev. 7 (Phase 3a, 3b step 1c, 3b resume, Phase 6), README.md (the Mermaid diagram, the
  tools and files tables, the rebuild recipe), this file.

NEXT: (1) **the headword crops are stale.** `crops/<W>/NNNN.png` were cut from the old `headwords.tsv`, whose
  entry ids the re-segmentation changed; the index is rebuilt but the images are not (they are git-ignored).
  Run `python3 tools/dj_crops.py crops` (~30 min) before Phase 3b step 2, or `dj_heads.py crops` will read the
  wrong strips.

  (2) the corrections layer (corrections.tsv, QUOTES.md) — the errata now survives a regeneration because it
  is applied during the build, but OUR proofreading fixes still do not; and the 34 errata_missed rows want it too,
  since they have to be made by hand against the image.

  (3) the 653 entries flagged `unconfirmed` are the whole residue of the segmentation: neither C nor D could be
  carried over to their first line, so only A's geometry says an entry begins there. They are where a spurious
  lemma can still hide (p. 21 `два евангелія…`, printed with `дка` as its provisional headword). A pass over them
  — or a third geometric witness (B's DjVu boxes are coarse but its margins are intact) — would close it.

  (4) the five older draft GT files still await the user's own reading (0465, 0517, 0660, 0893, 1124), and the
  six new ones are drafts too; not blocking. Method that worked on 719:
  `dj_inspect.py lines LEAF COL FIRST LAST --scale 0.62` in 10–14 line chunks (col line counts from ocr/NNNN.json),
  read each chunk, compare every line with ABBYY's reading printed beside it, the Greek against witness D
  (`dj_witness.page_text('D', leaf)`), the headwords against `dj_heads.py sheet LEAF` at 600 ppi where a glyph is
  doubtful; write the file in the conventions of eval/README.md; then `dj_eval.py --refresh`, `--suspects` for all
  four independent pairings, the "stands alone" comparison, and `dj_inspect.py gtcheck`. Budget ~45 min a page.

  (5) Phase 3b step 2 — the headword reading itself, once the user has chosen:
  (A) API: `pip install anthropic`, export ANTHROPIC_API_KEY, then `python3 tools/dj_heads.py read --pages
      45,465,517,660,893,1124 --effort low --force` and again with `--effort medium`; compare `dj_eval.py --heads`
      (exact headwords; expect ≳ 95 %) and the printed token usage; fix the prompt if the null/phrase rules are
      misread; then `read --batch` for the rest (records batch ids; `collect` later, resumable), then `check`.
  (B) By hand: `sheet LEAF` → read → `enter LEAF FILE`, ~15 entries a sheet, in batches with commits.

  Note: djachenko.pdf and facsimile.pdf are git-ignored; both rebuilt 2026-09-21 from the current entries.tsv
  (flowing: 4 min; facsimile: 1,120 pages, 15 s). Rebuild after any change to entries.tsv.
  The pipeline order is now dj_abbyy → dj_heads text → **dj_seg** → dj_abbyy → dj_heads text → dj_parse (README
  has it with timings): dj_seg.py needs step 1's text, and dj_abbyy.py needs dj_seg.py's file.
