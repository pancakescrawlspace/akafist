# Copies and scans of Дьяченко's dictionary (1900) — what exists, what was checked

Record of every scan or copy located so far, including those that could not be downloaded or examined, so that later
sessions do not repeat the search. Checked 2026-09-19 (sessions 1 and 2). Keep this file up to date when a source is
checked again or a new one is found.

A **witness** is an independent physical copy of the 1900 printing. Scans of the same copy are one witness, however
many times they were re-uploaded. Witnesses are told apart by comparing the same page (p. 1087 was used) at the level
of damaged letters, specks and the crop.

## Summary

| witness | physical copy | best scan | margins | status |
|---|---|---|---|---|
| **A** | Russian State Library (РГБ), digitised by the Presidential Library (prlib.ru item 437968) | archive.org `20200215_20200215_0856`: colour, 600 ppi | left margin cut off on 242 left-hand pages | **downloaded**: working scan (`scan/`, `pages/`) |
| **B** | an unidentified copy, reproduced photographically in the Moscow 1993 reprint (the 2004 reprint used by Azbyka shows the same damaged letters) | archive.org `DyachenkoG.PolnyjCerkovnoslavyanskijSlovarM.19931159p`: bilevel DjVu, 300 dpi at reprint size ≈ 237 ppi at original size | intact; has the title page | **downloaded** (`scan/reprint1993/`, 2026-09-19) as second witness |
| **C** | Indiana University's copy, digitised by Google | Google Books `lgbgAAAAMAAJ` (vol. 2), probably also HathiTrust | unknown | **not accessible from here**; the user is checking HathiTrust by hand |

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
   size); hidden text layer (OCR by the uploader, ABBYY FineReader 11 per the item metadata). archive.org
   derivatives: text PDF, JP2 zip (214 MB), `_abbyy.gz` (77 MB, archive.org's own ABBYY XML), `_djvu.xml`, `_djvu.txt`. Order: DjVu page = p for pp. 1–1120
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
10. **dhonorare.ru, <https://dhonorare.ru/dict/dyachenko/>** — page images 816×1156 (session 1). Lineage not
    checked; the page size equals 8, so probably witness B. Not downloaded.

### Witness C (Indiana University copy) — not examined

11. **Google Books `lgbgAAAAMAAJ`** — <https://books.google.com/books?id=lgbgAAAAMAAJ>: "Polnyĭ t͡serkovno-slavi͡anskīĭ
    slovarʹ … Volume 2", Grigorīĭ Dʹi͡achenko, Tip. Vilʹde, 1899; original from Indiana University; snippet view from
    the Netherlands. The Google Books API refused queries (daily quota) on 2026-09-19. Volume 1 not located yet.
12. **HathiTrust** — the Google-digitised Indiana copy is probably catalogued there, but catalog.hathitrust.org
    answers automated requests with 403 (Cloudflare). For an 1899 book published outside the US, full view is usually
    US-only. The user is checking by hand (2026-09-19), e.g.
    <https://catalog.hathitrust.org/Search/Home?lookfor=Polnyi%20tserkovno-slavianskii%20slovar%20Diachenko&type=all>.

### Located but not examined (lineage unknown)

13. **Тверская епархия** — <https://tvereparhia.ru/biblioteka-2/d/1981-dyachenko-g/23007-dyachenko-g-polnyj-tserkovno-slavyanskij-slovar-1900>:
    a PDF of 89.7 MB according to the search snippet; the page returned HTTP 404 when fetched (2026-09-19).
14. **Предание.ру** — <https://predanie.ru/dyachenko-grigoriy-mihaylovich/book/217771-polnyy-cerkovnoslavyanskiy-slovar>:
    returned HTTP 400 when fetched (2026-09-19).
15. **церковно-славянская-библия.рф** — the PDF named as the source of 8; not fetched.
16. **Славянская школа здравой мысли forum** — <http://www.anaslav.ru/forum/viewtopic.php?t=170>: a thread about the
    dictionary with download links (search result); not fetched.

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
- Witness C would be a third reading where A and B disagree; only if it becomes accessible.
