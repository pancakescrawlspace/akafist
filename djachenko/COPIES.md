# Copies and scans of Дьяченко's dictionary (1900) — what exists, what was checked

Record of every scan or copy located so far, including those that could not be downloaded or examined, so that later
sessions do not repeat the search. Checked 2026-09-19 (sessions 1 and 2). Keep this file up to date when a source is
checked again or a new one is found.

A **witness** is an independent physical copy of the 1900 printing. Scans of the same copy are one witness, however
many times they were re-uploaded. Witnesses are told apart by comparing the same page (p. 1087 was used) at the level
of damaged letters, specks and the crop.

**One typesetting (verified 2026-09-20, session 5).** The four witnesses are the same setting of type, line for
line: `python3 tools/dj_inspect.py linecheck` aligned every printed line start of A, B and C onto D's text over all
1,119 dictionary pages (`eval/linecheck.tsv`) — 99.8 % of B's, 99.7 % of C's and 99.5 % of A's line starts (on the
sides whose margin is intact) fall on a line start of D, no page or column disagrees as a block, and the residue is
OCR (Google splits a lone "=" or a tall headword into a "line" of its own, ABBYY adds speck lines, B's text layer
drops the last lines of some pages and lets guide words in). The title pages of C (dated 1899) and D (1900) are one
setting apart from the year line, both with the censor's permission of 21 Sept 1898: a re-dated title, not a new
edition. The one textual difference noted earlier, B's mid-dot in "175·об." on p. 1087, is a speck in copy B (A's
colour scan shows clean paper; C and D read "175 об."). Consequence for the facsimile rendition (PLAN.md Phase 6,
Rev. 6): the line structure of any witness is the line structure of the book; A's is in `ocr/*.json`.

## Summary

| witness | physical copy | best scan | margins | status |
|---|---|---|---|---|
| **A** | Russian State Library (РГБ), digitised by the Presidential Library (prlib.ru item 437968) | archive.org `20200215_20200215_0856`: colour, 600 ppi | left margin cut off on 242 left-hand pages | **downloaded**: working scan (`scan/`, `pages/`) |
| **B** | an unidentified copy, reproduced photographically in the Moscow 1993 reprint (the 2004 reprint used by Azbyka shows the same damaged letters) | archive.org `DyachenkoG.PolnyjCerkovnoslavyanskijSlovarM.19931159p`: bilevel DjVu, 300 dpi at reprint size ≈ 237 ppi at original size | intact; has the title page | **downloaded** (`scan/reprint1993/`, 2026-09-19) as second witness |
| **C** | Indiana University's copy — a modern photo-offset **reprint** ("Reprinted by JUH" on the title verso; title page dated 1899), 2 vols; which original it reproduces is unknown | Google Books PDFs (downloaded by the user): bilevel JBIG2, 600 ppi | intact | **downloaded** (`scan/google/google_indiana_v1.pdf`, `_v2.pdf`, 2026-09-19) |
| **D** | Cornell University Library's copy, an **original** (title page dated 1900), 1 vol. | Google Books PDF (downloaded by the user): bilevel JBIG2, 600 ppi | intact | **downloaded** (`scan/google/google_cornell.pdf`, 2026-09-19) — the best second witness |
| (HathiTrust) | the same Google digitisations: Indiana (= C, confirmed on a sample page), Cornell (= D), and the Chicago and Berkeley copies of the JUH reprint | page images | — | nothing to download; single pages only, automated downloading forbidden |

## Every source located

Page/image mapping: "p" = printed page of the dictionary proper (1–1120).

### Witness A (РГБ copy, Presidential Library scan)

1. **archive.org `20200215_20200215_0856`** — <https://archive.org/details/20200215_20200215_0856>. Uploaded
   2020-02-15; 1,159 leaves, JP2 4252×6520, 600 ppi, colour; ABBYY FineReader 11 XML (pre-reform Russian) by
   archive.org. Leaf = p + 37; leaf 0 cover, leaves 1–37 front matter (the title page and its verso, pp. I–II, are not
   in the scan). **Downloaded and in use**; details, checksums and defects in SOURCE.md.
2. **Президентская библиотека, <https://www.prlib.ru/item/437968>** — "Москва: Тип. Вильде, 1900. XL, 1120 с.; 26 см",
   "Источник: РГБ". The origin of 1, 3 and 4 (3 names it as its source_url; 1 and 4 are image-identical). Not
   downloaded from prlib.ru itself.
3. **archive.org `polnyjtserkovnoslavjanskijslovarsovne27`** —
   <https://archive.org/details/polnyjtserkovnoslavjanskijslovarsovne27>. Upload of the prlib.ru scan (collection
   russian-online-libraries); 1,162 images; raw images zip 1.37 GB, JP2 zip 675 MB; Tesseract OCR (rus, no ѣ/і).
   Leaf = p + 39. p. 1087: same crop and bleed-through as 1. Not downloaded. (Its raw zip was not opened; it might be
   uncropped — unlikely, since the page-service images match 1 exactly.)
4. **archive.org `dyachenkos-dictionary-church-slavonic`** —
   <https://archive.org/details/dyachenkos-dictionary-church-slavonic>. "High-fidelity digital edition", 300 ppi,
   JP2 zip 1.1 GB, PDF 1.9 GB, Tesseract OCR (bul). Leaf = p + 37 (same leaf numbers as 1); p. 1087 identical to 1,
   margin cut. Not downloaded.

### Witness B (the copy behind the 1993 reprint)

5. **archive.org `DyachenkoG.PolnyjCerkovnoslavyanskijSlovarM.19931159p`** —
   <https://archive.org/details/DyachenkoG.PolnyjCerkovnoslavyanskijSlovarM.19931159p>. "M., 1993, 1159p", described
   as "DJV c OCR + подробное оглавление". Original: DjVu 63.9 MB, 1,158 pages, bilevel JB2 at 300 dpi, ~1647×2637 px;
   the reprint is reduced (text block of p. 113: 13.4 cm against 17.0 cm in A, i.e. 79 %, so ≈ 237 ppi at original
   size); hidden text layer (OCR by the uploader, ABBYY FineReader 11 per the item metadata); the title page (DjVu
   page 1121) is cropped below the imprint, so its year cannot be read. archive.org
   derivatives: text PDF, JP2 zip (214 MB), `_abbyy.gz` (77 MB, archive.org's own ABBYY XML), `_djvu.xml`, `_djvu.txt`. The hidden text
   layer is incomplete on some pages: it drops the last lines of a column (p. 894: seven lines that the image has) and
   includes the guide words of the head (session 5). Order: DjVu page = p for pp. 1–1120
   (archive.org leaf = p − 1), then page 1121 title page, 1122 table of contents, 1123 first page of the preface
   (p. III), 1124 p. IV … 1158 p. XXXVIII. Margins intact on p. 1087 (all headwords complete).
   **Downloaded** 2026-09-19 with `python3 tools/dj_fetch.py --reprint` into `djachenko/scan/reprint1993/` (DjVu,
   `_abbyy.gz`, `_djvu.txt`, `_scandata.xml`, `_files.xml`; MD5-verified). Render a page with
   `ddjvu -format=tiff -page=N <djvu> out.tif` (djvulibre from MacPorts is installed).
6. **archive.org `B-001-027-578-ALL`** — <https://archive.org/details/B-001-027-578-ALL> (collection
   nicolai-woodenko-library). A repackaging of 5: its zip contains 5's DjVu and PDF; image PDF of 999×1600 JPEG pages
   (182 ppi), with its own archive.org OCR (`_abbyy.gz`, hOCR). Leaf = p − 1, front matter at the end. Not
   downloaded (inferior copy of 5).
7. **Wikimedia Commons, `File:Полный церковнославянский словарь (Протоиерей Г.Дьяченко).djvu`** —
   <https://commons.wikimedia.org/wiki/File:Полный_церковнославянский_словарь_(Протоиерей_Г.Дьяченко).djvu>.
   1,158 pages, 1635×2316, 42 MB. The file behind the Wikisource index "Индекс:Полный церковнославянский словарь
   (Протоиерей Г.Дьяченко).djvu" (no OCR layer; two pages transcribed — session 1). Speck-for-speck the same images
   as 5 (p. 1087). File page = p + 38. Not downloaded.
8. **Wikimedia Commons, `File:Прот. Г. Дьяченко. Полный церковно-славянский словарь (1900).pdf`** —
   <https://commons.wikimedia.org/wiki/File:Прот._Г._Дьяченко._Полный_церковно-славянский_словарь_(1900).pdf>.
   1,158 pages at 816×1156, 50 MB; uploaded 2019-06-01; source given as
   `http://церковно-славянская-библия.рф/pdf/polniy_cerkovno-slavyanskiy_slovar_dyachenko.1900.pdf` (not checked).
   Same images as 5 at low resolution. File page = p + 38. Not downloaded.
9. **Azbyka.ru** — <https://azbyka.ru/otechnik/Grigorij_Djachenko/polnyj-tserkovnoslavyanskij-slovar/>. The preface
   and the front matter are HTML text in modern spelling; the dictionary itself is PNG page images,
   `https://azbyka.ru/otechnik/assets/build/html/30755/image{p}.png` (image number = printed page; 1132×1755 at
   p. 1087), per session 1 from the 2004 reprint. The damaged letters on p. 1087 are identical to 5, so it is witness
   B again, scanned separately. robots.txt allows .png (disallows .djvu, .txt, .epub). Not downloaded (only p. 1087).
   Its preface text is a ready transcription of the front matter, useful when the preface is needed.
   Checked again 2026-09-20 (session 5): the user saved the page of letter А by hand (30 PNGs, pp. 1–30,
   1132×1755 px palette images ≈ 160 ppi at page size, no text layer). Same setting as everything else; at that
   resolution nothing tells it from B or D on p. 20, and the p. 1087 comparison of session 1 (damaged letters
   identical to the 1993 reprint) stands: witness B's copy. Lower resolution than B's DjVu (≈ 237 ppi) and a
   quarter of A's and D's — no new witness and no better image; the rest of the letters were not downloaded.
10. **dhonorare.ru, <https://dhonorare.ru/dict/dyachenko/>** — page images 816×1156 (session 1). Lineage not
    checked; the page size equals 8, so probably witness B. Not downloaded.

### Witnesses C and D (Google-digitised copies from Indiana and Cornell)

C1. **Google Books PDFs of the Indiana University copy** (the user downloaded them from Google Books in the
    Netherlands, 2026-09-19; the Google IDs were not recorded — ask the user for the URLs). Moved from the repo root to
    `djachenko/scan/google/` (git-ignored):
    - `google_indiana_v1.pdf` (originally `Полный_церковно_славя.pdf`): 618 PDF pages, 40,922,077 bytes, MD5
      e17677545cf7a53600bd01910006c1d3; PDF metadata "Полный церковно-славянский словарь", "Григорий Михайлович
      Дьяченко". Title page stamped "Indiana University Libraries Bloomington", shelfmark "PG 603 .D536 v.1"; title
      page dated **1899**; verso: censor's permission "Москва, сентября 21 дня 1898 г." and **"Reprinted by JUH"** —
      a photo-offset reprint. Front matter, then pp. 1–567; PDF page = p + 46 (p. 567 = page 613, the last printed
      page; its Google text layer holds only the first lines; pages 614–618 blank).
    - `google_indiana_v2.pdf` (originally `Polnyĭ_t͡serkovno_slavi͡anskīĭ_slov.pdf`): 570 PDF pages, 38,800,838
      bytes, MD5 8a46a010c787843250821969994f4906; "v. 2", same title page repeated; opens with p. 567 again (the
      letter С starts there), pp. 567–1120; PDF page = p − 558 (p. 567 = page 9, p. 1087 = page 529).
      `dj_witness.c_page` takes pp. 1–566 from v1 and p. 567 on from v2 — until session 5 the boundary stood at
      p. 572, so pp. 568–572 pointed at v1's blank pages and C was silently absent there (fixed 2026-09-20, the six
      pages re-voted and re-indexed).
    Text pages: bilevel JBIG2 images at 600 ppi (~3700×5650 px) plus a hidden Google OCR text layer. Margins intact.
D1. **Google Books PDF of the Cornell University Library copy** — `djachenko/scan/google/google_cornell.pdf`
    (originally `Polnyĭ_t︠s︡erkovno_slavi︠a︡nsk.pdf`): 1,174 PDF pages, 95,330,806 bytes, MD5
    b2241130c8a442e23376f1ed756b0a4c; PDF metadata "Polnyĭ t︠s︡erkovno-slavi︠a︡nskīĭ slovarʹ", "Grigorīĭ
    Mihaĭlovich Dʹi︠a︡chenko". Cornell bookplate and date-due slip, shelfmark "PG 613 D53"; title page (PDF page 9)
    dated **1900**; an original copy. Complete in one PDF: title page, preface from p. III, all pages to 1120;
    PDF page = p + 48 (p. 1087 = PDF page 1135). Bilevel JBIG2 600 ppi, hidden Google OCR text layer. Margins intact.
    On p. 1087 the text agrees with A and B (the "mid-dot" once noted in B's "175·об." is a speck in copy B — see
    "One typesetting" above).
11. **Google Books `lgbgAAAAMAAJ`** — <https://books.google.com/books?id=lgbgAAAAMAAJ>: "Polnyĭ t͡serkovno-slavi͡anskīĭ
    slovarʹ … Volume 2", Grigorīĭ Dʹi͡achenko, Tip. Vilʹde, 1899; original from Indiana University — probably the
    record of C1 vol. 2 (the web fetch here saw only snippet view; the user could download the PDF). The Google Books
    API refused queries (daily quota) on 2026-09-19.
12. **HathiTrust** — catalog.hathitrust.org answers automated requests with 403 (Cloudflare), so it cannot be used
    from here. The user checked by hand (2026-09-19): the book is there and can be viewed, but only **single pages**
    can be downloaded, not whole volumes. A sample page saved by the user (2026-09-20,
    `inu-30000011356106-46-…pdf`, 600 ppi bilevel, "Original from Indiana University, digitized by Google") is
    witness C's digitisation, which is complete on disk from Google Books; HathiTrust's other volumes are the same
    Google digitisations as 11 and C2–C3 below. Nothing to download there, and its terms forbid automated
    page-by-page downloading anyway. Search used:
    <https://catalog.hathitrust.org/Search/Home?lookfor=Polnyi%20tserkovno-slavianskii%20slovar%20Diachenko&type=all>.
C2. **Google Books `8y1IAQAAMAAJ`** — University of Chicago's copy, "1899, JUH", vol. 1 (616 pages), full view,
    digitised 2015: another copy of the same JUH photo-offset reprint as C (found 2026-09-20 through the Google
    Books Atom feed, `google.com/books/feeds/volumes?q=…`, which answers when the JSON API's quota does not). A
    second scan of the reprint's plates, not a new witness; not downloaded.
C3. **Google Books `AWFOAQAAMAAJ` (А–Р, 616 pages) and `euDar5UjPEsC` (С–Я, 568 pages)** — University of California,
    Berkeley, "1899, JUH", full view, digitised 2016: the JUH reprint once more. Not downloaded. (`_QXgAAAAMAAJ` is
    Indiana's vol. 1 again, = C1; `CqczAQAAMAAJ` is Cornell's record, = D1; `4k0UAQAAIAAJ`, `kt9FswEACAAJ`,
    `fEhbzwEACAAJ`, `P_LCtgAACAAJ` are catalogue records without pages; `aaAkDwAAQBAJ` is the 2013 Рипол Классик
    reprint, preview only.)
    So every Google/HathiTrust digitisation is either Cornell's original (D) or a copy of the JUH reprint.

### Located but not examined (lineage unknown)

13. **Тверская епархия** — <https://tvereparhia.ru/biblioteka-2/d/1981-dyachenko-g/23007-dyachenko-g-polnyj-tserkovno-slavyanskij-slovar-1900>:
    a PDF of 89.7 MB according to the search snippet; the page returned HTTP 404 when fetched (2026-09-19). Checked
    again 2026-09-20: the site was rebuilt and its library is gone; the Wayback Machine has the author's listing of
    2017 (a "1900" and a "1993" item) but no capture of either item page or PDF. Dead.
14. **Предание.ру** — <https://predanie.ru/dyachenko-grigoriy-mihaylovich/polnyy-cerkovno-slavyanskiy-slovar/>
    (the old `/book/217771-…` URL gives 400). Reached 2026-09-20; two files under
    `/uploads/ftp/dyachenko-grigoriy-m/polnyy-cerkovno-slavyanskiy-slovar/`, both downloaded and checked:
    `slovar-dyachenko.djvu` (40,546,912 bytes, MD5 63758ffa987523629b356de24cb4d971, 1,159 pages, 1132×1755 px,
    no text layer; DjVu page = printed page) is pixel for pixel the Azbyka scan of 9 (p. 20 compared) — witness B's
    copy at ≈ 160 ppi; `slovar-dyachenko.pdf` (94,112,338 bytes, MD5 a44ce6120d43e0ce073db91b554a8206, 1,158
    pages, CCITT 1646×2637 px at 300 dpi, "ABBYY FineReader 8.0", 2006, no text layer; PDF page = p + 38, front
    matter first) is the scan behind 5, 6, 7 and 8 — p. 20 correlates 0.994 with the archive.org DjVu at zero
    shift, 2.75 % of pixels differing from the JB2 re-encoding. Both witness B; nothing new. Not kept.
15. **церковно-славянская-библия.рф** — the PDF named as the source of 8; HTTP 403 for a non-browser and for a
    browser user agent alike (2026-09-20); the same 2006 scan as 14's PDF in all likelihood.
16. **Славянская школа здравой мысли forum** — <http://www.anaslav.ru/forum/viewtopic.php?t=170>: a thread about the
    dictionary with download links (search result); not fetched (connection times out, 2026-09-20 too).
17. **НЭБ (rusneb.ru), record `000199_000009_003687812`** — <https://rusneb.ru/catalog/000199_000009_003687812/>:
    an РГБ item ("тип. Вильде, 1899"). The site answers foreign addresses with 403 and a "switch off your VPN"
    page (2026-09-20), so it could not be examined. It is either the Presidential Library's scan of the РГБ copy
    (= A) or a separate РГБ digitisation — the one open lead for a second *original*; needs a Russian address or
    the user's browser. РНБ's catalogue (primo.nlr.ru) could not be searched automatically either.

### Not scans

- Printed reprints on sale, "Репринтное издание 1900 года" (ЗАО «БММ»): <https://www.blagovest-moskva.ru/item23450.html>,
  <https://www.pravknigi.com/goods/polnyy-cerkovno-slavyanskiy-slovar-protoierey-g-dyachenko-reprintnoe-izdanie-1900-goda-10593.html>.
  Which copy they reproduce is not known.
- An antiquarian listing of an original copy: <https://www.rusbibliophile.ru/Book/Dyachenko_G__Polnyj_cerkovnosl>.
- No transcribed text of the dictionary proper was found anywhere (Azbyka transcribes only the front matter; the
  Wikisource index has two pages — session 1).

## Use in this project

- Witness A remains the working scan (best resolution; colour; ABBYY layer with pre-reform orthography).
- Witness B supplies what A lacks — the 242 left-hand pages with the margin cut off (headword starts), the title
  page — and a second, independent reading for triangulation: its own images, the DjVu's hidden OCR text and
  archive.org's ABBYY XML (`scan/reprint1993/*_abbyy.gz`, same format as A's, so `tools/dj_abbyy.py` can in
  principle read it). Being bilevel and reduced, B is weaker for small print (Greek accents, italics) but good for
  headwords.
- Witness D (Cornell, original, 600 ppi bilevel, complete) is the best second witness for headwords and for pages
  cut in A; C (Indiana, a reprint) and B are further readings where A and D disagree or are unclear. HathiTrust single
  pages (12) only if something is still missing.
