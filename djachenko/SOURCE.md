# Source of the scan and OCR layers

**Work.** Прот. Григорий Дьяченко, *Полный церковно-славянскій словарь (со внесеніемъ въ него важнѣйшихъ
древне-русскихъ словъ и выраженій)*, Москва: Типографія Вильде, 1900. XXXVIII + 1120 pages, two columns.
Public domain (author †1903).

**Scan.** Internet Archive item [`20200215_20200215_0856`](https://archive.org/details/20200215_20200215_0856),
1,159 leaves at 4252×6520 px, 600 ppi (the same scan is also uploaded as item `dyachenkos-dictionary-church-slavonic`).
Files used, downloaded by `tools/dj_fetch.py` into `djachenko/scan/` and verified against the MD5s in
`20200215_20200215_0856_files.xml`:

| file | size | MD5 | content |
|---|---|---|---|
| `…_jp2.zip` | 2,100,577,489 | 64d0f750b15b863960c313c3de1bc6b8 | one JPEG 2000 image per leaf, 600 ppi |
| `…_abbyy.gz` | 78,813,970 | 74bc40242ff6f24c877e0af341942c29 | ABBYY FineReader Engine 11 XML: characters with boxes, confidence, dictionary flags; formatting (font size, italic, bold, smallcaps, `lang` Russian / RussianOldSpelling); paragraphs with indents; blocks |
| `…_djvu.xml` | 62,445,818 | 409780ea4d8b54dcba3ccba87fd90d4a | the same OCR as DjVu XML, word level |
| `…_djvu.txt` | 8,543,658 | ad6b3277eeb16c65837708d9903f9a0d | the same OCR as plain text |
| `…_page_numbers.json` | 195,417 | e5d00ed011fe38efbf8d21c0e52e4c42 | leaf → printed page number (archive.org's automatic map, overall confidence 98) |
| `…_scandata.xml` | 388,282 | be20464662dde51e5b4234c9f1714d46 | leaf sizes, page types |

(`…` = `Дьяченко. Полный церковнославянский словарь`.) The hOCR file (127 MB) was not downloaded; it duplicates
the ABBYY layer.

**Working images.** `djachenko/pages/NNNN.jpg` = leaf NNNN downscaled to 2126 px wide (300 ppi), JPEG quality 88;
`djachenko/pages/jp2/` keeps the 600 ppi originals. Single leaves can also be fetched from archive.org at 300 ppi:
`https://archive.org/download/20200215_20200215_0856/page/n<leaf>.jpg`.

**Leaf → printed page.** Leaf numbers are 0-based as in the JP2 file names (`…_0150.jp2` = leaf 150). Verified by
eye: leaf 150 = printed page 113 (guide words Вѣр— / Вѣк—). The automatic map in `page_numbers.json` is copied into
`manifest.tsv`; corrections made by hand in the manifest take precedence when the manifest is regenerated.
Result of the check (2026-09-19): leaf 0 cover, leaf 1 = p. III (first page of the preface, unnumbered), leaves 2–6 =
pp. IV–VIII (numbers read from the images; the automatic map missed them), leaves 7–36 = pp. IX–XXXVIII, leaf 37 the
unnumbered table of contents, leaf 38 = p. 1 (unnumbered in print; set by hand), leaves 39–1157 = pp. 2–1120 without
a single gap or repeat, leaf 1158 back cover. The preface text runs on from leaf 1 ("…высказаться какъ о той") to
leaf 2 ("цѣли, которой мы желали…"), so nothing of it is missing; pp. I–II (title page and its verso) are not in this
scan — the 1993 reprint (witness B in COPIES.md) has the title page. So for the dictionary proper: **printed page =
leaf − 37**.
25 leaves have a page-number confidence below 90 in the automatic map; their numbers fit the sequence, so they are
accepted. Phase 3a confirmed the map independently: the page number read from the running head of every dictionary
page agrees with the manifest, up to single-digit OCR confusions (3/8, 5/8, 0/9) on 81 pages.

**Structure (from the table of contents, leaf 37; checked against the letter initials found in Phase 3a).** Front
matter: preface pp. I–XXVIII; Приложенія: А. how to use the dictionary XXVIII–XXIX, Б. table of abbreviations (authors,
works, common nouns) XXIX–XXXIII (leaves 27–31), В. errata (Замѣченныя опечатки) XXXIV–XXXVIII (leaves 32–36, a table:
page, line from top/bottom, column, "напечатано", "слѣдуетъ читать"). Main part pp. 1–863 (leaves 38–900), А to Ѵ; p.
864 (leaf 901) blank; **Прибавленіе** (words omitted, additions and corrections) pp. 865–1120 (leaves 902–1157), a
second alphabetical sequence А to Я — the TOC gives, for each letter, its pages in both parts; the table is in
`tools/dj_abbyy.py` (`MAIN_LETTERS`, `SUPP_LETTERS`) and the letters on each page are in `manifest.tsv`. The TOC
misprints Ѩ as 826—857 for 856—857. The letter initials found on the pages match the TOC on every letter start except p.
808 (Ч, set beside the column), p. 858 (Ѯ, at the head of the page) — both not read by ABBYY — and p. 1120 (an extra gap
before the closing "Конецъ … Бгу слава").

**Other copies.** Every other scan or copy located — including the ones that could not be downloaded — is recorded in
`COPIES.md`. This scan is witness A (the Russian State Library copy, digitised by the Presidential Library). Further
witnesses on disk, all with intact margins: B (the copy behind the 1993 reprint, `scan/reprint1993/`), C (Indiana
University's photo-offset reprint, Google, 2 vols) and D (Cornell University's original copy, Google, 600 ppi
bilevel) in `scan/google/`.

**Scan defects found in Phase 3a.**
- **Left margin cut off** on 242 dictionary pages, all of them even leaves (left-hand pages): 123 in the main part and
  119 of the 128 left-hand pages of the supplement. The lines of the left column start at the image edge, and the first
  letter or two of the headwords (on the worst pages also of the continuation lines) are missing from the image. Listed
  in `ocr/report.tsv` ("margin cut off"). Witnesses B, C and D (see COPIES.md) have these margins intact.
- **Right margin cut off** (found in Phase 2, 2026-09-19) on 313 pages, all odd leaves (right-hand pages): 196 in
  the main part, 113 in the supplement, 4 in the front/back matter. The full lines of the right column end at the
  image edge, so their last 1–4 characters are missing (typically 20–140 px at 600 ppi). No page is cut on both
  sides; 551 of the 1,119 dictionary pages are incomplete on one side. Listed in `ocr/report.tsv` ("right margin cut
  off"); witness D supplies the line ends (eval/RESULTS.md §6).
- **Paper patch** over the lower left column of p. 1120 (leaf 1157): the starts of about ten entries (Авій …) are
  covered.
- Pictures instead of text: 18 headwords with tall superscripts (e.g. Кощѵна p. 266, Пѣвцы, Служба, Фѵлло,
  Хорѵгвь) were stored by ABBYY as picture blocks, so they have no OCR text; Phase 3a keeps them in the text flow as a
  placeholder (U+FFFC).

**Notes.**
- OCR quality (from a first look): the definition text is good and keeps pre-reform orthography (ѣ, і, ѳ, ъ);
  the Church Slavonic headwords and the Greek are garbled (low `charConfidence`, `suspicious="1"`,
  `wordFromDictionary="0"`), which is usable as a detector for them.
