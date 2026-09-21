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
  `djachenko/segmentation.tsv` (119,616 rows, 2.3 MB) holds the verdict for every such line and is **committed**:
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

- The headword crops remade (session 6, same day): `dj_crops.py index` + `crops --force` over all four witnesses
  (4,452 strips, 132 MB, 8 workers, ~100 min; the machine has 16 cores and the pool is CPU-bound at ~99 % a
  worker, so `--workers 14` would cut that by about 40 % — worth passing on the long runs). Every located
  headword is now in a strip: A 24,959, B 24,954, C 24,956, D 24,956 (was 99 %).
  Checking the result against `Аполинъ` — an entry that exists only because of the re-segmentation — found a
  defect in the crops themselves: **witness A's box came from ABBYY's own reading**, so it began at the first
  character ABBYY managed to read. On the 235 entries only C and D could see, that is a median 205 px right of
  the column edge (over 300 px on a third of them), against 0 px for every other entry, so A's crop showed the
  middle of the line instead of the lemma — on exactly the entries a reading will most need a second opinion
  about. A headword begins at the column's flush edge by definition, so `dj_crops.boxes_for` now extends
  A's box out to it (deskewed on the page rule, clamped at the image edge, which is where a cut left margin puts
  it). Re-indexed and A's 1,113 strips rebuilt; the crop of p. 20 now reads `Аполинъ — имя, встрѣтившееся`
  (faint under the patch, but legible) and `Апокрифы, т. е. книги` instead of ABBYY's `4 фтг книги`.
  `dj_seg.py --jobs` renamed `--workers`, as everywhere else in tools/.

- The head/definition split revised (session 6, same day; the user, reading the PDF: "some of the headword
  sections contain definition text: see even the very first lemma, `Я-первая`"). The logic dated from the first
  dj_parse.py (b27af76) and had never been revised.

  What it did: take the first separator (`=`, a dash, `(`, ` - `, or a hyphen before a known abbreviation) in the
  first 80 characters. What goes wrong: the print's dash after the headword reaches the voted text as a bare
  hyphen or not at all, and then a *later* separator wins and the head swallows a clause of the definition.
  The first entry of the book is the plainest case — A reads `Я=первая`, B `Я—первая`, C `Я = первая`, D
  `1-первая`, and D's hyphen won the vote, so the head came out `Я-первая`. Measured: 311 heads held an internal
  hyphen, 690 were four words or longer, 2,963 had been cut at a `(`.

  What it does now: **the head is the shorter of two bounds — up to the first separator, and as far as ABBYY
  measured the headword's own type run** (`entries_hint[].abbyy`, which dj_abbyy.py cuts at its own HW_END on
  A's line). It can never be the longer, because that run is the headword. Where the first separator lies past
  that bound the real one was lost by the OCR: the head is cut at the bound instead and a dash left at the cut
  taken as the separator (flag `sep_lost`, 1,307 entries). Two refinements, both found by a wrong answer:
  the count starts at the first word that has letters in it (the voted text sometimes opens with a speck read as
  `|`, which had made 156 heads empty), and the bound is not trusted when it comes out under 0.6 of the length
  of ABBYY's own reading — there the voted text has split a word ABBYY read whole (`Смꙋдрствовати` as
  `Сму дрствовати`), and the word count is not the headword's. Over the book that ratio sits at 1.0 with a long
  tail upwards; under 0.6 lie 233 entries, 0.9 %.
  A hyphen inside the head that ABBYY did *not* read also ends it: 200 of the 311 are of that kind (`Абстиненты-
  воздержники`, `Алой-ст. слав.`), while the other 111 are the book's own hyphenated headwords (`Баба-Яга`,
  `Воспріємника-ца`), whose hyphen is inside the run ABBYY measured, so it reads it.
  Last, a definition that began with a *second* separator (342 entries) has one of the two from the OCR — D adds
  a dash where the page has only `=` (p. 246 `Карачъ — = татарскій` for `Карачъ=татарскій`, confirmed against the
  ground truth) — so it is absorbed, keeping `=`, the book's mark for the gloss (flag `sep_double`).

  Measured on the twelve ground-truth pages, which transcribe the separators faithfully: our cut is aligned to
  the GT of the same entry (anchored on the definition, which is read at ~1 % CER — the provisional head is
  Church Slavonic type and too garbled to place its own last character) and we look at what the GT has there.
  **Real failures 18 of ~250 decidable entries (7.2 %) → 3 (1.2 %)**: the twelve that had skipped an earlier
  separator are all gone; of the three left, one is a page where the OCR glued the headword to the first word of
  the definition and one a phrase headword ABBYY read only the first word of. 1,412 heads changed over the book,
  all but 34 shorter; the 34 longer are numbered sub-senses that now carry their term (`1) Богородиченъ`) instead
  of the bare number. `hw_missing` 132 → 126, condensed lines in the facsimile 412 → 338. The printed-line
  invariant holds (124,497 line items = 124,497 printed lines).

- The flush level on a column with numbered senses (session 6, same day; found while answering the user's
  question about `1) Богородиченъ` on p. 53, and fixed with the user's own observation that the indent is a
  constant of the book). The book sets a numbered sense as its own paragraph, one indent in, with its body a
  *second* indent in, so such a column has three levels, not two — 2,613 of the 4,480 column sides have three
  or more. `dj_seg.flush_level` chose which level is flush by agreement with A, and on those columns A is wrong
  in the same way (its own indent estimate is stretched by the deeper level, so it calls the ordinary hanging
  lines flush) and could not break the tie: `Богородичны = пѣснопѣнія въ честь Бо|жіей Матери` was cut in half
  mid-word and each of the seven numbered senses became an entry of its own, printed with its term in Church
  Slavonic type as though it were a lemma — which, as the user pointed out, it is not: the print has it in
  italic civil type.

  Two changes, both following from the indent being constant:
  1. The lowest level a column shows is its flush edge unless only a speck or two sit there (`n0 <= max(2, 5 %)`),
     since nothing in the body is set a whole indent to the LEFT of where the entries begin. A may then choose
     only between "the lowest level is flush" and "nothing in this column is".
  2. The verdict is accepted on **precision**, not on agreement: the lines the witness calls flush must be starts
     in A, but A may have starts the witness does not — that is the correction the file exists to make, and on a
     page of numbered senses it is most of the column. Low precision instead means the levels or the alignment
     are wrong, and the side is left to A. (The old F1 ≥ 0.5 test could not tell "A is wrong" from "the mapping
     is broken", and abstained on exactly the pages that needed correcting.)
  118 printed lines changed their verdict; **24,959 → 24,841 entries**; the pipeline reaches its fixed point
  again in one pass. p. 53 is now one `Богородичны` article with its senses inside it and `Божіей` joined across
  the line break. The ground-truth head measurement is unchanged by this (1.2 % failures), and the printed-line
  invariant holds.
  Not done: the facsimile still sets that second indent at the first one — A's `ind_of` collapses levels 1 and 2
  (its threshold is `indent + 110` px, and the second indent is 186 px), and `dj_build` renders `min(ind, 1)`.
  The witnesses now measure the levels properly, so `segmentation.tsv` could carry the level instead of just
  start/continue and the facsimile could set all of them — see the NEXT line.

- The headword crops remade again after the re-segmentation (4,452 strips, 131 MB, 14 workers ~33 min — the
  machine has 16 cores and the pool is CPU-bound, so 14 is worth passing; 8 took ~100 min). Every located
  headword is in a strip: A 24,841, B 24,836, C 24,838, D 24,838.

- DEFECT (found by the user inspecting djachenko/crops/; FIXED the same session, below): **the crops of B are cut
  from the wrong part of the page, and those of C and D take in too much.** A's are good (the user's judgement and ours). Diagnosed but
  NOT fixed — see the NEXT line.
  1. *B: the y-flip uses the wrong page height.* `dj_witness.djvu_words` reads the page rectangle from
     `djvused print-txt`, which is **the text layer's bounding box, not the page**: on B's p. 1 it is
     `(page 31 21 1608 1906)`, so the code takes H = 1906 + 21 = 1927 where `djvused … size` says the page is
     1647 × **2637**. Every word box is then flipped about the wrong axis and sits 710 px too high; the crop of
     the first lemma shows a line from the middle of the article. The error is `2637 − (y0+y1)` and so varies
     with how much of the page the text covers, which is why leaf 38 (the letter initial, a short first column)
     is the worst and most pages are only somewhat wrong. B's *text* is unaffected — reading order and the vote
     use relative positions — which is why nothing else has shown it.
     Ripple, measured on 200 pages: with the true height the extracted text is identical on 189; the 11 that
     differ all have a text bbox within ~60 px of the page height, where the footer zone (`y0 > 0.85 H`) moves
     across a line. So the fix needs dj_heads step 1 re-run and the vote re-checked, not only the crops.
  2. *C and D: the box within the line is too generous.* Their boxes come from `dj_crops.head_box`, which cuts
     at its own HW_END or, failing that, after four words — so the crop runs into the definition. Measured over
     the book at 600 ppi: median box width A 454 px, C 593, D 600 (~32 % wider), and boxes more than twice the
     median width are 6.9 % in A against 23.1 % in C and 23.2 % in D. A is right because its box is ABBYY's
     Church Slavonic type run, which is the headword itself.
     The user's proposal, and it is the right one now that the head/definition split is fixed: take the head we
     already have in `entries.tsv`, estimate its width from its character count against the line's own text and
     box, and cut there — we know the line, so we know the coordinates to within a few per cent.

- Explanatory words in the head are no longer set in Church Slavonic (session 6, end; the user: "sometimes a
  word in the headword section is not printed in headword style... 'Або, иногда альбо' means that the word Або
  is sometimes given as альбо. The word иногда is explanatory to the headword, not part of it"). Checked on the
  scan: in that line `Або,` and `альбо` are bold and `иногда` is not (and `польск.` is italic). ABBYY cannot
  help — it flags `b` on 3,585 of 676,646 words, 0.5 %, far too few to be the headword face — so a list of words
  it is, as the user proposed, and the twelve ground-truth pages supply it: they mark the Church Slavonic type
  with braces, and the words that fall between two marked groups there are `и` (5), `или` (3) and `вм.` (1),
  while none of the four ever appears inside a marked group.
  The user's caution about `и` is right and is measurable: `или`, `иногда` and `вм.` are never part of a lemma,
  but `и` can be — `Дворяне и дѣти боярскіе`, `Испытаніе водою и желѣзомъ`, `Полъ и Луда` are headwords in their
  own right. So `и` is taken as a connective only where it joins two spellings of one word (`Мождевельникъ и
  можжевельникъ`), measured by the similarity of its neighbours at the norm level: 148 of the 240 heads with an
  internal `и`, the other 92 keeping theirs.
  `dj_build.head_spans` gives the head's Church Slavonic spans and both renditions use it — the facsimile
  through its style regions, the flowing one through `head_markup`, whose `#e` now takes the head as markup
  rather than as a string. 332 of 24,719 heads have a word set in civil: 177 `или`, 149 `и`, 4 `вм.`,
  2 `иногда`. Both PDFs rebuilt; p. 1 checked by eye against the scan.
  This is an interim measure: once Phase 3b step 2 reads the headwords, the Church Slavonic span is the read
  headword itself and no list is needed.

- The crops of B, C and D fixed (session 6, NEXT item 1).
  1. *B's coordinates.* `dj_witness.djvu_words` now takes the page size from `djvused … size` (in the same call
     as `print-txt`) and flips the boxes about it; p. 1's first word moves from y 190 to 900 and the crop lands
     on `А=первая`. B's extracted text moves on 110 of 1,119 pages, because the gutter search is a fraction of
     the width and the width changed too: 596 of the 788 edits are gutter specks (`J`, `j`, `I`, `|`, `{`, `[`)
     changing column, the rest a few running-head fragments leaking in on some pages and out on others, and
     four line-order swaps. dj_heads VERSION 11, whole book re-voted (30 s at 14 workers): 23,677 → 23,670
     B+A fixes, 199,800 → 199,878 disputed places, paragraph cuts identical, dj_seg 0 lines differing;
     **14 of 24,841 entries changed text**, a coin toss (`разрѣшать н отъ` → `разрѣшать отъ` and `оть санскр.` →
     `отъ` better, `окрестъ` → `окресть` and `XIV — XV` → `XIV XV` worse). dj_eval --refresh: **no text column
     changed on any of the twelve ground-truth pages**, merged 2.279 % → 2.279 % at the norm level. So the vote
     does not see B's layout, as intended — B only overrides D where A agrees with it.
     The same refresh records the segmentation work of this session against the ground truth for the first time:
     recall 99.7 % → 100 %, precision 97.3 % → 99.7 %, guessed starts 54 → 2 (eval/results.tsv).
  2. *The box within the line* (the user's proposal): `head_box` now walks the line's words counting characters
     at the norm level until the entry's head in entries.tsv is reached, and cuts inside the word where the head
     ends there (`альбо—польск.`, `Я—первая`), with a sliver for the last letter. Before, it cut at the first word
     containing a separator, or after four words.
  3. *Full height.* C's and D's Google word boxes span the lowercase letters only — 54 px at 600 ppi against
     A's 94 — so every capital and accent lost its top (`Абецадло`, `Предзащитница`); they are extended 45 % up and
     15 % down, measured on pp. 1, 109 and 480 against the images. B's DjVu boxes are full height already.
  Result, median box at 600 ppi / share over twice the median width: A 454 px / 6.9 %, B 466 / 6.3 %,
  C 382 / 6.0 %, D 398 / 5.8 % (were B 577 / 13.6 %, C 593 / 23.1 %, D 600 / 23.2 %); heights A 94, B 104,
  C and D 86 (were 54). Checked by eye on pp. 1, 109 and 480 for all three witnesses. B, C and D's 3,339 strips
  rebuilt; A's were right and are untouched. `dj_crops.py index` now reads entries.tsv, so it runs after
  dj_parse.py.
  4. *B's vertical padding* (the user, looking at the rebuilt crops/B/0038: "all the headwords, but also still
     quite a bit of noise"). `PAD` (15 px) was meant at 600 ppi but applied in each witness's own pixels, and B's
     page is ~250 ppi, whose DjVu word boxes already span 95 % of its line pitch (41 px of 43): the padding took
     in two-thirds of the lines above and below. B's vertical pad is now 3 px (`PAD_Y`); the horizontal pad stays,
     since it is what keeps the last letter where the head's cut lands tight (tried at 6: `Ааронь род?`). B's
     strips rebuilt again.
  5. *The initial capital.* crops/B/0044 also showed `Адонисъдекъ`, `Адонъ`, `Аеръ` with the left half of the
     big initial А missing: B's OCR had left it out of the word box, which started at x 67 where the column's
     flush lines start at 35 — the same thing ABBYY does, and fixed the same way as for A this session: the box
     is pulled out to the column edge. Not to one figure per column, though: B's indent is only ~12 px (flush
     35–42, hanging 46–50), so the 10th percentile of the line starts lands on the hanging level, and the Google
     columns are skewed by up to 13 pt, so a column minimum would add much white at the other end. The edge is
     the start of the nearest flush line, level 0 of `dj_witness.indent_levels`, which is deskewed. B, C and D's
     strips rebuilt once more with all five changes together (14 workers, ~25 min): every located headword in a
     strip; the four witnesses take 105 MB (were 131), B's 11 MB (were 21 — the noise). Checked by eye on
     pp. 1 and 7 in B and D side by side: the same headwords row for row, initial capitals complete.
  Side-question from the user, answered by measurement: one PNG per headword instead of a strip per page costs
  the same in content (20 pages of A: 483 KB as strips, 496 KB as 354 files — PNG pays per ink, not per pixel,
  and a strip even has twice the pixels, padding every row to the widest), but 2.7× on disk, since a file of
  ~1.4 KB occupies a 4 KB APFS block: ~400 MB for the book against ~130. The "about a gigabyte" of the dj_crops
  docstring was greyscale JPEG, a format question, not a granularity one; the file-count concern was git's,
  and crops/ is git-ignored. Per-headword files would be fine if wanted (not done).
  Two further explanatory words for `dj_build.HEAD_CIVIL`, seen in crops/B/0044: `иначе` (3 heads; checked on
  the scan — p. 7 `Аермонъ, иначе Ермонъ`, the names Church Slavonic, `иначе` civil) and `также` (2).
  What the crops still show is upstream of them: where ABBYY's own reading of the headword ran on past the
  separator (`Лендиръ евр. источникъ обитанія`), the head in entries.tsv is that long and the crop follows it.

- Strips with separator bars (session 6). The user's aim: "if there's noise on the page, I can't clearly see to
  which headword it is connected." Tried in turn: one file per headword (`--files`; built for 62,747 headwords,
  then stopped — the user: "too many small files", and on disk a ~1.4 KB file fills a 4 KB block, 2.7× the space
  for the same bytes), frames round each headword in the strip, frames in red. Measured on 25 pages per witness,
  the frames themselves cost 1.7 % and the red another 15–19 % (a 3-colour palette needs 2 bits a pixel; strips
  for the book 82 MB black, 95 MB red). Settled on the user's design: **one strip per page, a black bar the full
  width of the strip between two headwords**, 4 px (twice the frames' 2 px), with 6 px of white either side so
  it never touches a letter; 1-bit PNG again. Strips are the default of `dj_crops.py crops` once more; `--files`
  and `--both` (both from one decoding of each page — the page image is cached per worker) stay as options.
  The per-headword files were deleted (generated and git-ignored); all 4,452 strips rebuilt.
  The bars' purpose (the user): "that we can easily extract the individual headwords purely from the images, no
  other metadata needed". Two things follow, both done: (a) **every entry of the page has its slot in every
  witness**, in entry order — an entry a witness could not locate (11 in the book: B 5, C 3, D 3) gets an empty
  12 px slot instead of being left out, which would have shifted every later headword of that strip by one, so
  the k-th piece of a page's four strips is always the same entry; (b) `dj_crops.py split` cuts every strip apart
  from its pixels alone — a bar is a run of rows black across the whole width, which no headword row is — and
  checks the result against headwords.tsv (as many pieces as the page has entries, each inside its slot, a piece
  empty exactly where the witness has no box); `--out DIR` writes the pieces as files.
  Result over the whole book: **4,452 strips split from their pixels alone, 0 disagreeing with the index**; every
  entry has its slot in all four witnesses. The strips take 106 MB (120 MB on disk): A 35, B 11, C 29, D 31.

- **djachenko/MISSING_HEADWORDS.md** (the user asked for it): the 11 headwords `dj_crops.py index` could not
  locate are 6 entries, of three kinds — the library stamp of copy A on p. 41 (*Публ. Библ. СССР им. В. И.
  Ленина*) and the page footer on p. 913, both made into entries by A's layout; and four real headwords (`Фата`,
  `Блевотина`, `Блюстися`, `Кужель`) that the witnesses read but `dj_witness.reading_order` throws away. Every
  witness's reading of each is in the file.
  ⚠ OPEN DEFECT found that way: **the footer cut**. `FOOT_RE` (`Ц[еѳe]рк\W{0,3}сла|…`, case-insensitive) is meant
  for the footer *Церк.-славян. словарь…* but also matches the abbreviation `(церк.-слав.)`, and a match in the
  bottom 15 % of a page cuts off that line and all below it in both columns. On pages that carry no footer it
  fires on 8 pages; on 5 of them (387, 774, 840, 1030, 1093) B, C and D all lose the same lines, so ~18 printed
  lines (~640 characters) are missing from entries.tsv and the text after each gap slides into the entry
  before it. Most entries there were still "located" in the witnesses — on the wrong line — so the unlocated list
  understates it.

- **The footer cut fixed** (the user: go ahead, "if this can properly be done in the build layer, and not in the
  corrections layer" — it can, and nothing here is a hand correction). First checked the premise from the
  witnesses: the footer's own words occur at the foot of 70 pages in B, C and D, every one ≡ 1 mod 16, one per
  sheet. `dj_witness.reading_order` now takes a `footer` flag (printed page ≡ 1) and cuts only there, at the
  LOWEST matching line; against the committed code the witnesses' text changes on exactly the 8 pages, 98 lines
  restored and none lost anywhere (VERSION 12, VOTE.md). Then found that A's own layout had the same pattern:
  `dj_abbyy.py` had filed article lines as the page footer on pp. 387, 840, 1030, 1093 (p. 387's footer held
  `Орлейщикъ`, `Орьлъ`, `Орьтъма`); the same rule returns 8 lines to A's body, no real footer changed.
  Loop to the fixed point, then: 24,841 → **24,845 entries** (`Орлейщикъ`, `Орьлъ`, `Орьтъма`, `Куръ` entries again;
  `Фата` and `Февруарій` whole); 124,497 → 124,505 printed lines, the line invariant holding; disputed places
  199,878 → 198,730; ground-truth scores unchanged. The unlocated headwords are down from 11 to the 5 witness-
  instances of the two non-headwords (the stamp, the footer tail). Crops of the 8 pages rebuilt; all 4,452
  strips split cleanly. MISSING_HEADWORDS.md has the resolution.
- **`dj_inspect.py counts`** (the user's idea: store line counts per page to spot pages with too little in them) →
  `eval/pagecounts.tsv`, lines and characters of every page and column side in B, C and D against A (whose lines
  are ABBYY's own layout, not the reading order the others share). Measured before settling the rule: line counts
  alone are too noisy for a loss of one or two lines — OCR splits or merges a line either way, witnesses differ
  from A by ±1–2 on ordinary pages — and so are characters (±3 %); flagging a side where a witness is **at least
  one line short *and* under 98.5 % of A's characters** caught all 8 footer-cut pages. After the fix none of the 8
  is flagged; **53 pages remain flagged**, of unknown cause (their first and last lines match A, so not this bug)
  — the review list.

- **The ground truth gets its printed lines, and a facsimile page each** (the user asked, to make reviewing
  easier). `dj_inspect.py gtlines` puts a `¦` into the GT files before every printed line that begins inside an
  entry line: scan A's line starts are known in the voted text (`text_merged` + `breaks`), and that text agrees
  with the GT on ~99 % of its characters, so each start is carried over by alignment — to the start of the word for
  a break between words, inside the word where the print hyphenated it. A file is written only when every column
  then has as many printed lines as scan A. 11 of the 12 pages came out right at once; **p. 109 did not, and the
  cause was the GT: the last printed line of col b, `12 въ сп. XVI в. (Вост.).`, had not been transcribed** (read
  on scan A and added; the note that the entry runs on to p. 110 was a consequence and is corrected — p. 110
  begins with Вывертка). p. 109's scores improve by ~20 errors for every candidate; every other page scores exactly
  as before (`dj_eval.py` and `gtcheck` drop the `¦`). Also closed on the way: an unbalanced `‹` on p. 246
  (`и у‹ инѣхъ` → `и ‹у› инѣхъ`, the у half cut off by the scan's edge; text unchanged), which gtcheck had reported
  since session 4.
  `dj_build.py --gt [LEAF …]` then sets each GT page as a facsimile page, `djachenko/facsimile-P<printed page>.pdf`
  (facsimile-P0008.pdf … facsimile-P1087.pdf; git-ignored): the GT's entries and `¦` lines placed on scan A's
  lines in order, column by column; its `{…}` as the Church Slavonic type (headword size in the head, text size
  after it); `‹…›` letters grey, `[?]` a small grey ?; guide words as transcribed, or grey from the first and last
  headword where they were not; a note at the foot with the file and its status. Checked side by side with the
  scans on pp. 8, 428, 856 (four columns, an initial in mid-page) and 1087 (cut margin): line for line. The main
  facsimile's output is unchanged by the refactoring (44 pages compared), except that on supplement pages the
  rules under the page number now sit close under it, as printed, instead of running into the running title
  *Прибавленіе.* Known and left: verse lines are justified at the first indent where the book sets them ragged
  and deeper (as in the main facsimile).

- **The flowing PDF: 3.7 min → 5 s** (NEXT item 7; the user asked to look into it). Measured by stage: writing
  djachenko.typ 0.7 s; `typst compile` 118 s; and a `typst query <e>` that `compile_pdf` ran afterwards and never
  used — a second full layout, 103 s. Compiled without the running head's two queries the book takes 3.3 s, so the
  compile's time was all the guide words: every page filtered all 24,845 `<e>` markers by page in a Typst closure
  (`query(<e>).filter(m => m.location().page() == here().page())`), ~25 million closure calls per layout pass.
  Now the footer carries a marker, `<pgend>`, and since a page's header comes before its body in document order
  and its footer after, the page's entries are `selector(<e>).after(here()).before(<its pgend>)`, resolved by
  Typst's selectors instead of a closure. The unused query is gone. `dj_build.py` end to end: 5.2 s. The PDF's
  text is identical to the old build's on all 1,000 pages, guide words included (pdftotext); `--subset links`
  (32 pages) builds too.

- **What the GT pages are for** (the user asked): not a benchmark of `dj_build.py` but of the text the pipeline
  produces; also the instrument that chose the route (Phase 2), the regression test, the error estimate the edition
  can state, the specification of right output, and the source of the vision model's examples. Blind to rare
  defects (the footer cut left the scores unchanged) — the book-wide checks complement it. Answered in the chat;
  nothing written.
- **Phase 3b step 2 gets a third option, (C) our own OCR model** (the user's proposal; PLAN.md). The user will not
  commit to the paid API pass (A) before the free options are exhausted, and wants to learn the machine-learning
  side. Assessment: feasible; the bottleneck is labels, not images; best seen as (A)'s independent partner.
  - Kraken installed by the user in `~/.venvs/kraken` (7.1.1, PyTorch 2.14, the Mac's GPU via MPS). SciPy there
    upgraded to 1.17.1 past Kraken's pin: the 1.15.3 build fails to load on macOS 27. A smoke test (one epoch on
    300 lines) runs: 4.0 M parameters, ~1.5 batches of 16 a second, i.e. ~12 min an epoch for the full set.
  - **`tools/dj_hwocr.py`** (new) prepares the training data in `djachenko/cache/hwocr/` (git-ignored, ~1 GB):
    line images of scan A (400 ppi) with their text, three kinds — gt (the GT's lines, paired with A's through the
    `¦` markers: 1,094 train, and the two held-out pages 283/696 as the **test set**, 215 lines, 52 headwords),
    agree (entry first lines whose head D and B read alike, 5,274, and 2,431 continuation lines they read alike
    throughout; 359 of every 20th leaf are the validation set) and synth (8,000 first lines set by Typst in five
    Church Slavonic faces, accented, a quarter with a bold civil head as the user pointed out the book has, then
    real definition text; roughened like a scan; checked against the real lines for letter size). Labels at the
    norm level for stage 1; strict and accented labels kept for later stages (the user: the Phase 0 decision
    against accents and titla is not final). The automatic labels measured on the GT pages: head right in 83 %
    (35/42), line characters in 98.85 %. `sheet` draws contact sheets; `data --only synth` rebuilds one kind.
  - **djachenko/HWOCR.md** (the user asked for an expository note): CTC, the network Kraken trains, training,
    the three sets, what dj_hwocr.py prepares and why, how to run and read a training run, a glossary.
- **The GT audit that building the data became.** Pairing every GT line with A's and comparing their lengths found
  **20 misplaced `¦` markers** — `gtlines` had snapped a marker back over a hyphen or dash (`съмрьтьни-¦полумертвы`
  → `¦съмрьтьни-…`, `Римскій—¦старый` → `¦Римскій—…`) and to the start of words the print had broken whose hyphen
  the vote had lost (`Богоро¦дицы`, `кры¦латый`, `священни¦ковъ`, each checked against A's line end) — and **a
  second line missing from p. 109**, the last of col a (`(др. слав. „{искони}“).`, read on scan A), hidden because
  a misplaced marker had made the counts agree. `gtlines` now snaps over letters only (not in Church Slavonic type
  or a line's first word, where the alignment is loose), keeps a break deep inside a civil word, and lists every
  line whose length disagrees with A's; all twelve pages rewritten and checked, the GT facsimile PDFs rebuilt.
  Scores: merged 15.9 → 15.8 % on headwords, definitions 1.1 % (RESULTS.md).
  ⚠ Found on the way, a pipeline defect: **the voted text of `Смокноути` (p. 623, leaf 660) is scrambled** —
  `…разбиша сѣни о ша нема и“ (Пер. лѣт., 58). и ту уби`: D's words out of order and `немъ и смокоша и съ сѣній`
  lost, so entries.tsv has it wrong. Its GT markers are set by hand (noted in the file). How many paragraphs are
  like it is unknown — NEXT.
- **The first training run** (the user, `ketos train` as in HWOCR.md § 8), and `dj_hwocr.py eval`: the model's
  readings of the two test pages scored against the GT and beside the vote's, split by type and by whether scan A
  shows the line start. Before the run, Kraken's alphabet warning showed look-alikes and debris in ~1 % of the
  labels (fita as barred o, braces, ■, |): folded or left out, data rebuilt, run restarted. Interim, after epoch 2
  (val 98.2 %): **31/40 headwords exact on the sides A shows whole, the vote 28/40**; 2/12 against 8/12 on the
  cut column of p. 659 (A's image lacks the first letters; the vote has D). Where model and vote agree: 26/27
  right. Workers measured: the GPU is the bottleneck, not the data loading.
- **The review round** (the user asked whether hand-checked originals were needed; the answer: not for the training
  set as a whole — training averages label noise away, what the model lacks is correct examples of the hard cases —
  but yes where the model and the vote disagree: *active learning*). `dj_hwocr.py book` has the model read the first
  line of every entry and sets each head beside the vote's; `review` samples the disagreements (no GT page, no
  cut column) into sheets of 15, both readings under each line, to be answered in `djachenko/heads_review/NNN.txt`
  (a / b / the word / -); `data` adds the answers as a fourth kind of sample, `checked`. Trial on leaves 100–109
  (epoch-5 checkpoint): model and vote agree on 34 % of the intact heads; where they differ the model is mostly
  right (the vote reads ѣ as е or ъ), its own weak spot В/К in the headword type. Sheets labelled in Old Standard
  (its ѣ unmistakable) with Greek from Arial Unicode. The trial sheets were removed; the real round waits for the
  final model. Also answered: what a contact sheet is (HWOCR.md § 9).
- **Epoch 10 of the first run** (val 98.82 %), evaluated while training goes on: **37/40 test headwords exact on the
  intact sides against the vote's 29; 41/52 in all against 37**; where they agree (30) all right. Two GT slips on
  p. 246 found by it — `Касфїѧ`, `Катавасїѧ` (ѧ, not а; checked on scan A) — corrected. `eval` now reads the test
  lines from the GT files, so a GT correction counts without a data rebuild. `dj_hwocr.py alphabet` → alphabet.tsv
  (169 characters + blank = the 170 outputs of the model summary).
- **The review round, drawn.** `book` with the epoch-10 model (on the CPU, 8 Kraken processes side by side, while
  training went on): 24,845 first lines; model and vote read the head alike in 49 % of the 22,142 intact lines.
  Fixed on the way: heads cut at a dash (norm text has only `-`; `-` with a space on one side, or unspaced as a
  prefix match), and the label of an answered line built from the confirmed reader's whole line (a free-end
  alignment for a typed head). **500 disagreements drawn → `djachenko/heads_review/001–034.txt`** (committed,
  unanswered), images `cache/hwocr/review/NNN.png`. The user reads them next; then `data`, retrain, `eval`.

NEXT: (1) **Phase 3a: page furniture must not become a paragraph of A.** Two entries are not headwords at all:
  the library stamp on p. 41 (`0078-2-21`) and the tail of the footer on p. 913 (`0950-2-15`). Then the 53 pages
  `dj_inspect.py counts` flags (eval/pagecounts.tsv): look at a sample, find what the shortfall is.

  (2) the corrections layer (corrections.tsv, QUOTES.md) — the errata now survives a regeneration because it
  is applied during the build, but OUR proofreading fixes still do not; and the 34 errata_missed rows want it too,
  since they have to be made by hand against the image.

  (3) **the second indent.** The book sets the body of a numbered sense two indents in, and the facsimile sets
  it at one: A's `ind_of` collapses the two levels and `dj_build` renders `min(ind, 1)` anyway. `dj_seg.py`
  already measures the true level of every line in C and D (`dj_witness.indent_levels`), so `segmentation.tsv`
  could carry it — one more column — and both `dj_abbyy.py` (which would store it as the line's `ind`) and the
  facsimile could use it. It would also give `dj_parse.py` a way to tell a numbered sense from a lemma.

  (4) the 653 entries flagged `unconfirmed` are the whole residue of the segmentation: neither C nor D could be
  carried over to their first line, so only A's geometry says an entry begins there. They are where a spurious
  lemma can still hide (p. 21 `два евангелія…`, printed with `дка` as its provisional headword). A pass over them
  — or a third geometric witness (B's DjVu boxes are coarse but its margins are intact) — would close it.

  (5) the five older draft GT files still await the user's own reading (0465, 0517, 0660, 0893, 1124), and the
  six new ones are drafts too; not blocking. The user reads them in `facsimile-P<page>.pdf` beside the scan
  (`dj_build.py --gt`); a corrected GT file keeps its `¦` markers, and a new one gets them with
  `dj_inspect.py gtlines LEAF` (which also catches a line left out, as on p. 109). Method that worked on 719:
  `dj_inspect.py lines LEAF COL FIRST LAST --scale 0.62` in 10–14 line chunks (col line counts from ocr/NNNN.json),
  read each chunk, compare every line with ABBYY's reading printed beside it, the Greek against witness D
  (`dj_witness.page_text('D', leaf)`), the headwords against `dj_heads.py sheet LEAF` at 600 ppi where a glyph is
  doubtful; write the file in the conventions of eval/README.md; then `dj_eval.py --refresh`, `--suspects` for all
  four independent pairings, the "stands alone" comparison, and `dj_inspect.py gtcheck`. Budget ~45 min a page.

  (6) Phase 3b step 2 — the headword reading itself. **Now: option (C), our own model** (PLAN.md, HWOCR.md). The
  data is built (`dj_hwocr.py data`); next the stage-1 training run — a few hours, unattended:
  `~/.venvs/kraken/bin/ketos -d mps --workers 4 train -f path -t djachenko/cache/hwocr/train.txt -e
  djachenko/cache/hwocr/val.txt -o djachenko/cache/hwocr/model -B 16 --augment -q early` (running, session 6) —
  then `python3 tools/dj_hwocr.py eval` on the final model. **The review round is drawn** (sheets 001–034 in
  `djachenko/heads_review/`); the user is answering them and checking the two test pages (0283, 0696 — the
  verdict rests on them). With those in hand, the plan (sketched to the user, session 6):
  1. `dj_hwocr.py data` (adds the answers), train on from the best model (`ketos train -i <best> …`, fewer epochs
     than from scratch), `eval` on the checked test pages.
  2. From the answers, a random sample of the disagreements: how often the model is right, the vote, neither —
     with the 49 % agreement (right 30/30 on the test pages) an estimate of the book's headword accuracy; the `-`
     answers are a list of segmentation faults. If the model wins: it becomes a witness — agreement = confirmed,
     disagreement = the better reader's reading, flagged — replacing entries.tsv's provisional headwords (links,
     both PDFs).
  3. Further rounds (`book` on the new model, `review`) while each still pays.
  4. The ~2,700 first lines on cut columns: witness D's images (train on them and read from them).
  5. Stage 2, letters as printed (strict labels: GT, synthetic, the user's typed answers in printed letters);
     accents perhaps later.
  6. The corrections layer (item 2) takes the answers into the edition as checked headwords.
  **Decision (the user, session 6):** the end result is the headword in the letters as printed, not civil letters;
  the civil readings are the intermediate. Whether titla and accents are recorded too is **left open** (the user:
  omitting them is a possibility kept open, not decided) — nothing may be built that rules them out.
  `djachenko/CS_LETTERS.md` (the user asked): the Church Slavonic letters and marks to copy, their codes and civil
  equivalents, and how to type them on the Mac. Found making it: dj_witness.norm_char folds ѻ and ꙩ to о but not
  their capitals Ѻ, Ꙩ — folded in dj_hwocr.py; the shared function (and so the vote) still has the gap.
- **The first run ended** (2026-09-22): early stopping after epoch 22; best epoch 12, val 98.92 %,
  `cache/hwocr/model/best_0.9892.safetensors`. Test pages: 37/40 intact headwords (vote 29), 41/52 in all (vote
  37), agreement 30/30 right — as epoch 10. `data` now looks each review answer up in the readings its sheet was
  drawn from (readings_<model>.tsv, matched by the `a:` text), so reading the book with a later model cannot
  change what an answer confirmed. The user is answering the sheets (001 under way) and checking the test pages. Stage 2 (PLAN.md option C, HWOCR.md § 10): extend the
  model's alphabet, train on the strict labels, *constrained reading* of every confirmed headword (the civil form
  fixes the word; the model chooses the letters). Meanwhile the user types corrections in printed letters.
  What stays open after that: the unreviewed disagreements — more rounds, or (A) aimed only at them:
  (A) API: `pip install anthropic`, export ANTHROPIC_API_KEY, then `python3 tools/dj_heads.py read --pages
      45,465,517,660,893,1124 --effort low --force` and again with `--effort medium`; compare `dj_eval.py --heads`
      (exact headwords; expect ≳ 95 %) and the printed token usage; fix the prompt if the null/phrase rules are
      misread; then `read --batch` for the rest (records batch ids; `collect` later, resumable), then `check`.
  (B) By hand: `sheet LEAF` → read → `enter LEAF FILE`, ~15 entries a sheet, in batches with commits.

  The crops are current (all four witnesses, 2026-09-21). Checked while fixing the index: step 2 does **not**
  need the same correction — `dj_heads.crop_boxes` cuts its own crops from A's image and already starts them at
  `min(the line's box, the column's bbox)`, i.e. at the column edge (x = 250 on leaf 57, for `Апокрифы` and
  `Аполинъ` alike). The two crops differ on purpose: dj_heads crops the *start of the line* for reading, the
  index crops the *headword box* for comparing one lemma across the four copies, and it was only the latter that
  took ABBYY's word for where the headword began.

  (7) **scrambled voted text** (found session 6): the paragraph of `Смокноути` on p. 623 has D's words out of order
  and half a line lost. Find how many paragraphs are like it — e.g. compare each paragraph's `text_merged` with
  A's own line texts (ABBYY, reliable on civil text) by alignment, and flag the ones whose order disagrees — and
  where the cause lies (D's reading order, `dj_witness.reading_order`, or the vote's cut).

  Note: djachenko.pdf and facsimile.pdf are git-ignored; both rebuilt 2026-09-21 from the current entries.tsv
  (flowing: 5 s; facsimile: 1,120 pages, 15 s). Rebuild after any change to entries.tsv.
  The pipeline order is now dj_abbyy → dj_heads text → **dj_seg** → dj_abbyy → dj_heads text → dj_parse (README
  has it with timings): dj_seg.py needs step 1's text, and dj_abbyy.py needs dj_seg.py's file.
