# Phase 2 results — what the existing OCR layers give, and the route for the rest

Measured 2026-09-19 (session 3) with `tools/dj_eval.py` against the six ground-truth pages in `gt/` (~19,300
characters after whitespace removal, 132 entries). The numbers are reproducible: `python3 tools/dj_eval.py` re-extracts
nothing (candidate texts are cached in `cand/`), rescores in 2 s and rewrites `results.tsv`; `--refresh` re-extracts.

## Candidates

| name | what | how the page text is obtained |
|---|---|---|
| `abbyy_A` | archive.org's ABBYY FineReader layer of scan A (our 600 ppi colour scan, Russian State Library copy) | `ocr/NNNN.json` (Phase 3a), paragraphs in reading order |
| `djvu_B` | the hidden text layer of the 1993 reprint's DjVu (witness B, ~237 ppi bilevel, the uploader's FineReader) | `djvused print-txt`, reading order rebuilt from word boxes |
| `google_D` | Google Books' text layer of the Cornell copy PDF (witness D, 600 ppi bilevel, original 1900 printing) | `pdftotext -bbox`, reading order rebuilt from word boxes |
| `google_C` | Google Books' text layer of the Indiana copy PDFs (witness C, a photo-offset reprint) | idem |

B, C and D are independent OCR runs on independent copies; C and D share an engine (Google's), so their errors are
correlated. A and B are both FineReader, but on very different images.

## Scoring

Edit distance after global alignment of the whole page, whitespace ignored. Two levels:

- **strict**: text as printed (GT markup removed).
- **norm**: additionally dashes and quotes unified, Church Slavonic letters mapped to civil ones (ѡ→о, ꙋ/оу→у,
  ѧ/ꙗ→я, ѫ→у, ѕ→з, є→е, ї→і, …), Latin look-alikes mapped to Cyrillic, all diacritics removed (so Greek accents and
  the и/й distinction do not count). This is the level that matters for `headword_civil` and for lookup.

Zones of the GT: **hw** = the headword of each entry (the `{…}` span or the text before `=`/`—`/`(`), **grc** =
Greek letters, **def** = everything else. A zone's CER = edits charged to its characters ÷ its characters.
"Headwords exact" = headwords with zero edits (norm).

## 1. Overall numbers

| candidate | level | CER all | headwords CER | headwords exact | definitions CER | Greek CER |
|---|---|---:|---:|---:|---:|---:|
| A ABBYY (archive.org) | strict | 9.1% | 49.4% | 8/132 | 4.9% | 118.4% |
| A ABBYY (archive.org) | norm | 7.9% | 48.3% | 11/132 | 3.8% | 118.4% |
| B DjVu text (1993 reprint) | strict | 5.2% | 20.0% | 34/132 | 4.2% | 14.7% |
| B DjVu text (1993 reprint) | norm | 4.5% | 14.7% | 62/132 | 3.8% | 6.4% |
| D Google (Cornell) | strict | 3.1% | 17.0% | 46/132 | 2.3% | 2.3% |
| D Google (Cornell) | norm | 2.3% | 14.7% | 62/132 | 1.5% | 1.5% |
| C Google (Indiana) | strict | 3.3% | 18.0% | 49/132 | 2.4% | 1.9% |
| C Google (Indiana) | norm | 2.5% | 15.3% | 64/132 | 1.8% | 1.5% |

Per page (norm; CER all / headword CER):

| leaf | page | GT chars | A | B | D | C |
|---|---|---:|---:|---:|---:|---:|
| 45 | 8 | 3,264 | 8.9% / 71.6% | 6.7% / 32.1% | 3.2% / 23.9% | 4.3% / 30.6% |
| 517 | 480 | 3,194 | 8.8% / 45.6% | 3.3% / 3.0% | 1.8% / 9.4% | 1.8% / 9.1% |
| 465 | 428 | 3,371 | 1.7% / 0.0% | 1.5% / 0.0% | 0.7% / 0.0% | 0.6% / 0.0% |
| 660 | 623 | 2,985 | 9.6% / 50.2% | 3.7% / 6.2% | 2.9% / 12.4% | 3.6% / 14.5% |
| 893 | 856 | 3,066 | 13.2% / 64.7% | 6.8% / 50.3% | 4.0% / 38.6% | 4.0% / 36.6% |
| 1124 | 1087 | 3,394 | 6.1% / 31.3% | 5.1% / 7.3% | 1.3% / 5.5% | 1.3% / 4.0% |

Notes. Page 428 is one long article (one headword). Page 856 (Ѫ, Ѩ) is the hardest for everyone: no OCR has Ѫ in its
alphabet, and the small CS type there confuses и/н. Page 1087 (supplement, left margin cut off in A) scores A on what
is in its image only; the `‹…›` letters are in B/C/D's images and are scored for them. Page 8 has the largest share of
small-type CS quotations in the definitions.

## 2. Definition text (PLAN question 1) — and triangulation (question 7)

ABBYY on A reads the civil text at 3.8 % CER (norm; 4.9 % strict), Google on D at 1.5 % (2.3 %). D is better than A
on every page, and D's image is complete where A's is cut (see §6). Character-level comparison of the readings of the
same GT positions (norm, 17,895 definition characters):

| | definitions | headwords | Greek |
|---|---:|---:|---:|
| D and B agree on … of the characters | 95.1 % | 80.6 % | 92.5 % |
| … and are then wrong in | 0.13 % (22 chars) | 1.7 % | 0.0 % |
| D ≠ B: D right / B right / neither | 639 / 212 / 33 of 884 | 76 / 88 / 52 of 216 | 16 / 3 / 1 of 20 |
| majority of D, B, A | 0.81 % wrong | 12.0 % | 2.3 % |
| majority of D, C, B | 1.13 % | 12.2 % | 1.1 % |
| all four wrong | 0.15 % | 4.6 % | 0.4 % |

(These majorities are computed on the GT-anchored alignment, so they are a little optimistic for a real three-way
merge without ground truth.) The 18 definition characters on which D, C and B all agree against the GT are shared
systematic errors — mostly final ъ read as ь and ѵ read as и; the GT was checked on the images at each of them.

**Answer:** the definition text does not need re-OCR or transcription. Take it from D, vote with B and A (C as a
tie-breaker), which leaves an expected ~1 % character error, and flag the 5 % of characters where D and B disagree —
that is where nearly all remaining errors are (only 33 of 17,895 characters are wrong in *both*). ABBYY on A alone
(3.8 %) would also have been usable, but A's text is incomplete on 551 pages (§6), which settles it.

## 3. Headword detection / entry segmentation (questions 2 and 5)

Hanging paragraphs of `ocr/NNNN.json` (Phase 3a geometry) against the GT entry starts:

| leaf | GT entries | found (recall) | candidate starts | correct (precision) | of them guessed |
|---|---:|---:|---:|---:|---:|
| 45 | 20 | 20 (100.0%) | 21 | 20 (95.2%) | 0 |
| 517 | 27 | 27 (100.0%) | 27 | 27 (100.0%) | 0 |
| 465 | 1 | 1 (100.0%) | 1 | 1 (100.0%) | 0 |
| 660 | 29 | 29 (100.0%) | 29 | 29 (100.0%) | 0 |
| 893 | 26 | 25 (96.2%) | 25 | 25 (100.0%) | 0 |
| 1124 | 29 | 29 (100.0%) | 37 | 30 (81.1%) | 22 |
| all | 132 | 131 (99.2%) | 140 | 132 (94.3%) | 22 |

The one false start on p. 8 is a speck ("п,") in front of the page's first, continued line; the one miss on p. 856 is
{Ѫза}, the first entry after the Ѫ initial, whose headword ABBYY did not read at all. On the cut-margin page all seven
false starts are `guessed` continuation lines that begin with a capital or a digit ("Синод.", "Моск.", "4."). So: on
ordinary pages the geometry is essentially exact; on the ~260 pages with guessed paragraphs (§6) expect ~20 % false
starts among the guesses, i.e. several hundred in all, to be removed in Phase 4 by the "=" test, the alphabetical
order and the witnesses' text.

## 4. Headword transcription (question 3)

- (d) ABBYY's own reading mapped to civil letters: 48 % CER, 11/132 exact — hopeless, as expected.
- The witnesses: B, D and C each read 47–48 % of the headwords exactly (norm). A majority vote of all four gives 50 %;
  at least one of them is right for 67 %. The rule "accept B's reading when D or C agrees with it" accepts 36 % of the
  headwords (47/132) at 96 % accuracy, nothing on p. 8 and p. 856. The failures cluster: the large CS initials
  (А read as Я/Л/И, Ѫ as Ж/Х/Д, Ꙗ as А), и/н, в/к and б/в in the small type, ѣ as ъ/е, щ as ш, ѧ as а/л, ѳ as д.
- (b) Vision on headword crops, contact sheet — tested on a fresh page (leaf 341 = p. 304, Мет–Меѳ, 25 entries; not a
  GT page, because the GT headwords had been seen in this session): crops from `entries_hint[].bbox` at 600 ppi,
  25 per sheet, read by the model. Result: 25/25 correct (23 confirmed exactly by at least one witness, two — 
  {Мечтанноборецъ}, {Меѳимоны} — confirmed at 3× zoom where every witness had misread a letter; one word,
  {Метехати}, is uncertain in the image itself and was read the same by B and C). On the same page D/C/B read 13, 14
  and 17 of 25 exactly. The CS-specific letters (ѳ under pokrytie, ѧ, ї, є) and the и/н, в/к ambiguities of the
  small type are the residual risk; sense and alphabetical order resolve most.

**Answer:** read all headwords from crops (route b), in contact sheets of ~30, and use the witnesses as the check:
a crop reading that agrees with B, C or D is confirmed; a disagreement with all three marks the entry for a second
look. Cost: 25,362 entry candidates → ~850 sheets; at ~2,000 tokens a sheet that is ~2 M tokens in one pass, as
estimated in PLAN.md. On the 242 pages whose left margin is cut in A the crops must come from D (or B/C): the
headword's box has to be found in D's word coordinates (`pdftotext -bbox`) through the text alignment used here
(`dj_eval.py` already rebuilds D's reading order; the alignment A↔D works even with A's garbled headwords).

## 5. Greek (question 4)

In D's text layer the dictionary proper (pp. 1–1120) contains ~14,700 Greek words (~87,000 letters; ~11,500 runs on a
line) on 1,088 of the 1,120 pages — median 11 words a page, 90th percentile 26, maximum 68 (p. 682); 12,600 in the
main part, 2,100 in the supplement. ABBYY on A garbles all of it (118 % CER). D and C read it at 1.5 % CER (norm) and
2.3 % / 1.9 % strict, i.e. *with* accents and breathings; B at 6.4 % / 14.7 %.

**Answer:** Greek comes from D, checked against C (they disagree on ~2 % of Greek characters); no vision pass, no
line crops, except for the entries flagged by that disagreement. Hebrew script is rare (a handful of words in D's
layer); Дьяченко mostly transliterates.

## 6. Scan A's cut margins (question 6) — new finding: the right margins too

Phase 3a found 242 left-hand pages (even leaves; 123 main, 119 supplement) with the left margin cut off, i.e. the
first letters of the flush lines missing. The GT work on p. 856 showed that **right-hand pages lose the right
margin**: in scan A the full lines of the right column end at the image edge. Counted from the line boxes
(`dj_abbyy.py` now warns `side b: right margin cut off in the scan (N lines end at the image edge)`, ≥ 3 lines within
4 px of the edge): **313 pages, all odd leaves — 196 main, 113 supplement, 4 front/back matter**; 296 of them with
≥ 3 lines within 2 px. What is lost is the last 1–4 characters of the justified lines of column b (typically 20–140 px
at 600 ppi, judged from the normal column width; on p. 856 a dash and a period at line ends, on other pages whole
syllables). No page is cut on both sides. In all, **551 of the 1,119 dictionary pages (49 %) are incomplete in A** on
one side; D (and B, C) have both margins on every page checked.

**Answer:** the missing letters come from D (line ends of column b on odd leaves; headword initials and line starts
of column a on even leaves), which the route of §2 provides for free: D is the primary text, A contributes its
geometry (segmentation, headword boxes) and a vote.

## Route (Definition of done of Phase 2)

| what | source | check | expected quality |
|---|---|---:|---|
| entry segmentation | A's geometry (`ocr/*.json`, Phase 3a) | "=" test, alphabetical order, witnesses' text | recall 99 %, precision 100 % on ordinary pages, ~80 % among the guessed paragraphs of cut pages |
| definition text | D, voted with B and A | D≠B positions flagged (5 % of chars) | ~1 % CER; 0.2 % wrong in both D and B |
| headwords | vision on crops from A (from D on left-cut pages), contact sheets | agreement with B/C/D; alphabetical order | ~100 % on the test page; residual и/н, в/к in small type |
| Greek | D, checked against C | D≠C flagged | ~2 % strict CER |
| cut margins (551 pages) | D | — | complete text |

Consequences for the plan: Phase 3b is no longer "recover headwords in A" but "build the page text from D aligned to
A's segmentation, vote, and read the headwords from crops". The alignment machinery (D's reading order from word
boxes, Levenshtein alignment, headword-box transfer) exists in prototype form in `tools/dj_eval.py`. Decision still
open for the user: whether the crop reading runs through the API from `dj_heads.py` (~2 M tokens in one unattended
pass) or in interactive sessions (~850 sheets to look at).

## Ground truth after this session

Comparing the witnesses (`dj_eval.py --suspects`: places where D and B agree against the GT) found and the images
confirmed 11 slips in the draft transcriptions, all corrected and noted in the files' headers: 0045 (6, incl. Азкъ →
Азвъ, three faint punctuation marks), 0465 (2), 0893 (2: ѫтро → ѩтро, ἔγχέλυες), 1124 (1: Подъвои → Подъбои). The 37
remaining disagreements were checked on the images and are OCR errors (и/н, final ъ/ь, ѵ read as и — `Сѵнод.` is
printed with ѵ in four places on p. 1087, `Синод.` in one). The `status:` lines of the files are unchanged (0045
checked by the user before the corrections; the rest draft).

## Addendum (session 3, later): the merged text of Phase 3b step 1

`tools/dj_heads.py` implements the route of §2 (per column side: D cut at A's paragraph starts, snapped to D's line
starts; per-character vote). Scored as candidates `merged` and `text_d` (`dj_eval.py --only merged,text_d --refresh`):

| candidate | level | CER all | headwords CER | headwords exact | definitions CER | Greek CER |
|---|---|---:|---:|---:|---:|---:|
| text_d (D cut at A's paragraphs) | norm | 2.3% | 14.7% | 62/132 | 1.5% | 1.5% |
| merged (vote D / B / A, C as check) | strict | 2.6% | 16.6% | 47/132 | 1.8% | 2.3% |
| merged | norm | 1.8% | 14.4% | 62/132 | **1.0%** | 1.5% |

- The cut loses nothing (`text_d` ≡ `google_D`); the segmentation scored on the merged text is the same as on A's
  (recall 99.2 %, precision 94.3 %). Over the book: 26,937 of 26,947 paragraph starts fell on a D line start
  within 15 characters; 9 were placed at a word boundary, 1 forced; 19 paragraphs have a D text much shorter or
  longer than A's (`witness.odd`), mostly headwords Google did not OCR at all.
- The vote rule was tuned on the GT and is stated in `dj_heads.merge`: B and A (both FineReader) may overrule D
  only when C (Google, like D) does not confirm D — where C confirmed D, the FineReader pair was right only for the
  "=" sign (19:0) and final ъ/ь (9:3), and wrong otherwise (period/comma 0:14, Latin letters, и/н, а/л in CS type).
  A first version without the C condition made the headwords and the Greek worse (B and A share the CS-type
  confusions and read Cyrillic look-alikes for Greek).
- Third exception (session 4): **Google's script confusion**. D reads Cyrillic letters as Greek look-alikes —
  single letters ("чтο", "πρимѣру", "θиміамъ") and whole words of the Old Church Slavonic citation type ("Γλι" for
  "гдь", p. 223) — and C, being Google too, confirms them, so the rule above kept the Greek. The FineReader pair
  may now fix a Greek character when D's own letter run is mostly Cyrillic, or when the run is unaccented (real
  Greek here carries accents and breathings) and A and B read every letter of it as the same Cyrillic letter.
  Effect on the GT (norm): definitions **1.02 % → 0.98 %** CER, all **1.80 % → 1.75 %**, Greek unchanged at 1.50 %.
  Book-wide: 1,335 Greek characters gone from the definitions, 528 entries changed, mixed-script words 890 → 558.
  The unit must be the letter run, not the whitespace token: "(συνοδία)-спутники" would otherwise count as
  Cyrillic and the Greek word would be rewritten.
- Of the remaining definition errors, 85 % lie inside a `disputed` span (9.3 % of the characters are flagged, with
  one character of slack); headwords 98 %, Greek 100 %. Proofreading the flagged spans therefore catches most of
  what is left; the unflagged remainder (~5 characters a page) are errors D and B share.
- Book-wide: 201,347 disputed places, 22,945 fixes; "=" within the first 80 characters of a hanging paragraph:
  A 88.9 %, merged 83.5 % (Phase 4 uses A's `eq` hint as well).

- Session 5: two more exceptions (Latin-script words, whole abbreviations read as Greek) and D's lexicon; the
  complete statement of the vote with its evidence has moved to `djachenko/VOTE.md`.

## Addendum (session 4): the ground truth extended from 6 to 12 pages

The six pages of Phase 2 were chosen to cover the kinds of page; measuring them showed where the sample was too
thin: the Greek rate rested on 4 errors in 266 characters, 132 headwords gave ±3.7 pp for scoring the coming
vision pass, no page carried the Old Church Slavonic citation type, and none was dense in short entries. Six pages
were added for those gaps (`eval/README.md` has the table): 719 and 801 (the two densest Greek pages), 260 (the
citation type), 146 (81 entries, the densest page), and 283 and 696 drawn at random and **held out** — never to be
used for tuning a rule.

Now 12 pages, 325 headwords. Scores over the whole set (norm level):

| candidate | CER all | headwords CER | headwords exact | definitions | Greek |
|---|---:|---:|---:|---:|---:|
| abbyy_A | 10.5 % | 51.6 % | 29/325 | 3.3 % | 120 % |
| djvu_B | 4.6 % | 13.3 % | 154/325 | 3.7 % | 9.2 % |
| google_D | 2.8 % | 17.0 % | 137/325 | 1.7 % | 1.5 % |
| google_C | 3.1 % | 17.5 % | 129/325 | 1.9 % | 1.4 % |
| **merged** | **2.2 %** | **16.0 %** | **139/325** | **1.1 %** | **1.5 %** |

(Re-measured 2026-09-21, session 6, after the last printed line of p. 109's col b — left out of its transcription —
was added to the ground truth: every candidate had been charged ~20 characters for it. Before: merged 2.3 % all,
1.2 % definitions.)

The definition rate is higher than the 0.9 % of the first six pages because four of the new pages were chosen to
be hard; the headline figure for the book should stay on the six representative pages, and the new ones should be
read per page. Segmentation on the new pages: p. 109 with its 81 entries came out at 100 % recall and 100 %
precision, p. 246 likewise; p. 659 (margin cut) 100 % recall, 94.7 % precision.

What the hard pages measure: on p. 223 and p. 109 nearly every disagreement between the witnesses and the ground
truth is a confusion of the citation face (И/Н, в/к, и/н, л/ль), where the transcription itself can only read by
sense — the places where it cannot are marked `[?]`. That is the class the vision pass will have to read.
