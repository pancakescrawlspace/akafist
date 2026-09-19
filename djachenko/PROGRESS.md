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

NEXT: Phase 3b step 1 — write tools/dj_heads.py: per page, rebuild D's reading order from `pdftotext -bbox` (reuse
dj_eval.reading_order), align to A's text (dj_eval.align), cut at A's paragraph starts, vote D/B/A per character,
store text_d / text_merged / disputed spans in ocr/NNNN.json; test on the six GT pages (the merged text should score
~1 % CER with dj_eval) and on a left-cut and a right-cut page. Then step 2, the crop/contact-sheet pipeline (crops
from A, from D on left-cut pages), after the user has chosen API vs. interactive reading.
