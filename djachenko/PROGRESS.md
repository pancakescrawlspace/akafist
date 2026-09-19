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

NEXT: Phase 1 — compare candidate scans on a sample page, download the chosen one to djachenko/scan/, extract page
images, build manifest.tsv, fill in SOURCE.md.
