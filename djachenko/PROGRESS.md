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

NEXT: Phase 3a — write tools/dj_abbyy.py (ABBYY XML → ocr/NNNN.json per leaf, schema in PLAN.md Phase 3), run it over
all leaves, and use its output to fill `letter`/supplement in manifest.tsv. Then Phase 2 (ground truth + measurements).
