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

NEXT: (1) finish the ground-truth extension — five pages left, in eval/README.md's table: 801 (Greek), 1104 (the
  OCS citation type), 146 (81 entries), and the two held-out random pages 283 and 696. Method that worked on 719:
  `dj_inspect.py lines LEAF COL FIRST LAST --scale 0.62` in 10–14 line chunks (col line counts from ocr/NNNN.json),
  read each chunk, compare every line with ABBYY's reading printed beside it, the Greek against witness D
  (`dj_witness.page_text('D', leaf)`), the headwords against `dj_heads.py sheet LEAF` at 600 ppi where a glyph is
  doubtful; write the file in the conventions of eval/README.md; then `dj_eval.py --refresh`, `--suspects` for all
  four independent pairings, the "stands alone" comparison, and `dj_inspect.py gtcheck`. Budget ~45 min a page.
  (2) Then Phase 3b step 2 — the headword reading itself, once the user has chosen: — the headword reading itself, once the user has chosen:
  (A) API: `pip install anthropic`, export ANTHROPIC_API_KEY, then `python3 tools/dj_heads.py read --pages
      45,465,517,660,893,1124 --effort low --force` and again with `--effort medium`; compare `dj_eval.py --heads`
      (exact headwords; expect ≳ 95 %) and the printed token usage; fix the prompt if the null/phrase rules are
      misread; then `read --batch` for the rest (records batch ids; `collect` later, resumable), then `check`.
  (B) By hand: `sheet LEAF` → read → `enter LEAF FILE`, ~15 entries a sheet, in batches with commits.
  Either way, then Phase 4 (dj_parse.py: entries.tsv from text_merged + headwords, headword_civil mapping,
  alphabetical validation, the "=" from A's eq hint where the merged text lost it). The five draft GT files still
  await the user's check (not blocking).
