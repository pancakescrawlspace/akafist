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
Result of the check (2026-09-19): leaves 0–6 unnumbered front matter, leaves 7–36 = pp. IX–XXXVIII, leaf 37
unnumbered, leaf 38 = p. 1 (unnumbered in print; set by hand), leaves 39–1157 = pp. 2–1120 without a single gap or
repeat, leaf 1158 unnumbered (end). So for the dictionary proper: **printed page = leaf − 37**. Letter boundaries and
the start of the supplement ("Прибавление") are filled into `manifest.tsv` in Phase 3a. 25 leaves have a page-number
confidence below 90 in the automatic map; their numbers fit the sequence, so they are accepted.

**Notes.**
- OCR quality (from a first look): the definition text is good and keeps pre-reform orthography (ѣ, і, ѳ, ъ);
  the Church Slavonic headwords and the Greek are garbled (low `charConfidence`, `suspicious="1"`,
  `wordFromDictionary="0"`), which is usable as a detector for them.
