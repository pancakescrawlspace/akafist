# The headwords a witness could not locate

`dj_crops.py index` locates every entry's headword in all four witnesses (`headwords.tsv`). Of 24,841 × 4 it
fails on **11** — which are **6 entries**, two of them missing from three witnesses and one from two. Examined one
by one (session 6, 2026-09-21), they fall into three kinds, and only one kind is about the witnesses at all.
(Resolved the same day for the four real headwords — see the last section; the list is now down to the two
non-headwords, which are rightly missing.)

| entry | page | what it is | missing from | cause |
|---|---|---|---|---|
| `0078-2-21` | 41 b | not a headword: the library stamp on copy A | B, C, D | A's layout took a stamp for a line |
| `0950-2-15` | 913 b | not a headword: the page footer | C, D | A's layout took the footer for a line |
| `0811-1-10` | 774 a | **Фата** | B, C, D | the footer cut in `reading_order` (below) |
| `0931-1-20` | 894 a | **Блевотина** | B | the same |
| `0931-2-17` | 894 b | **Блюстися** | B | the same |
| `1065-2-09` | 1028 b | **Кужель** | B | the same |

So the four real headwords are all lost the same way, and the list understates that defect: see the last section.

## How each witness reads them

Readings are each OCR's own, quoted as it gives them. "Dropped" means the words are in that witness's text
layer but the pipeline's `dj_witness.reading_order` throws the line away; "absent" means they are not in the
text layer at all.

### `0078-2-21`, p. 41 b — the stamp

| witness | reading |
|---|---|
| A (ABBYY) | line `I, (53`, headword read as `I` (confidence 13) |
| B, C, D | absent — they are other physical copies |

The purple oval ownership stamp of the library that holds copy A (*Публ. Библ. СССР им. В. И. Ленина*, with a
star), printed across the foot of column b. ABBYY read a fragment of its lettering as a one-line paragraph, and
Phase 3a's layout, seeing it flush at the column edge, made it an entry. In `entries.tsv` it is an empty entry
(flags `empty`, `hw_missing`, `unconfirmed`).

### `0950-2-15`, p. 913 b — the footer

| witness | reading |
|---|---|
| A (ABBYY) | line `Дьяченко. 68`, headword read as `Дьяченко` (confidence 61) |
| B | `Дьачеяко. 58` — kept, and so "located": B's crop shows the footer |
| C | `Прибавленіс. Церк.-славян. словарь свящ. Г. Дьяченко. 58` — dropped, rightly |
| D | `Прибавленіе. Церк.-славян. словарь свящ. Г. Дьяченко. 58` — dropped, rightly |

p. 913 is the first page of sheet 58, which carries the signature line. A's layout set most of it aside as page
furniture but kept its tail, in column b, as a text line, and it became an entry. In `entries.tsv` its head is
`встрѣчать` and its definition text belonging elsewhere (flags `sep_lost`, `unconfirmed`, …).

### `0811-1-10`, p. 774 a — Фата

| witness | reading |
|---|---|
| A (ABBYY) | `Фата =большой продолговатый шелковый`, headword `Фата` (confidence 84) |
| B | `Фата =большой продолговатый шелковый` — dropped |
| C | `Фата большой продолговатый шелковый` — dropped |
| D | `Фата большой продолговатый шелковый` — dropped |

The last line of column a; the article runs on at the head of column b (`платъ, которымъ женщины закрывали
голову…`). All three witnesses read it and all three drop it, so the voted text has nothing for it: in
`entries.tsv` the entry's head is `платъ` and its definition begins `которымъ женщины…` — "Фата = большой
продолговатый шелковый" is missing from the text. Beside it on the same row, column b's last line
`Февруарїй — (церк.-слав.)=февраль, второй` is dropped too, in all three: that entry now begins `мѣсяцъ въ году…`
under the garbled head `фенобарій`.

### `0931-1-20`, p. 894 a — Блевотина

| witness | reading |
|---|---|
| A (ABBYY) | `Блевотина — (И-іря^я) = рвота, плеваніе`, headword `Блевотина` (confidence 57) |
| B | `Блевотина — (έξέραμα) = рвота, плеваше` — dropped |
| C | `Блекотина –(ἐξέραμα)= рвота, плеваніе` |
| D | `Блекотина –(ἐξέραμα)= рвота, плеваніе` |

Only B loses it, and the voted text is D's, so `entries.tsv` is whole (head `Блекотина`, D's provisional misreading
of *Блевотина*; B and A read the headword right).

### `0931-2-17`, p. 894 b — Блюстися

| witness | reading |
|---|---|
| A (ABBYY) | `Блюстига — (тгроцеХгіѵ, (ЗХгтсеьѵ) = осте-`, headword `Блюстига` (confidence 55) |
| B | `Блюстисѧ — (προσελεΐν, βλέττειν) = осте-` — dropped |
| C | `Блюсτήρα – (προσελεῖν, βλέπειν) = осте-` |
| D | `Блюстиса – (προσελεῖν, βλέπειν) = осте-` |

Same page, same cause, B only. B, which drops it, is the one that reads the headword right (`Блюстисѧ`).

### `1065-2-09`, p. 1028 b — Кужель

| witness | reading |
|---|---|
| A (ABBYY) | `Кужель=льняное полотно; кужвлы`, headword `Кужель` (confidence 45) |
| B | `Кужель=льняное полотно; кужельный—` — dropped |
| C | `Кужель льняное полотно; кужельный—` |
| D | `Кужель льняное полотно; кужельный -` |

B only; `entries.tsv` is whole.

## The defect behind the four: the footer cut

`dj_witness.reading_order` recognises the page footer — *Церк.-славян. словарь свящ. Г. Дьяченко.*, printed at
the foot of the first page of every sheet — by the pattern `FOOT_RE` (`Ц[еѳe]рк\W{0,3}сла|…`, case-insensitive),
and cuts off everything from the first line in the bottom 15 % of the page that matches it. The abbreviation
`(церк.-слав.)` in ordinary text matches it too. When such a line falls in the bottom 15 % of a page, that line and
every line below it, in both columns, are thrown away: on p. 774 the matching line is column b's last,
`Февруарїй — (церк.-слав.)`, which takes `Фата` in column a with it; on p. 894 it is `церк.-слав. соблазна…`, on
p. 1028 `Кудити (церк.-слав. и …)`, each several lines up, so B loses fourteen lines on each of those pages.

Measured over the book, on the pages that carry no footer (p ≢ 1 mod 16, where any match is ordinary text):

| page | B | C | D |
|---|---:|---:|---:|
| 387 | 5 lines | 6 | 5 |
| 774 | 2 | 2 | 2 |
| 839 | 16 | — | — |
| 840 | 5 | 5 | 5 |
| 894 | 14 | — | — |
| 1028 | 14 | — | — |
| 1030 | 4 | 3 | 4 |
| 1093 | 2 | 2 | 2 |

**On pp. 387, 774, 840, 1030 and 1093 all three lose the same lines, so the vote cannot restore them: some 18
printed lines (~640 characters) are missing from `entries.tsv`**, and the text after each gap slides into the
entry before it. Besides `Фата` and `Февруарїй`: on p. 387 `Оріонъ … утренняя (Іов. 38, 31)`, `Орлейщикъ =
служка, который при свя-`, `Орьлъ — (церк. слав.) — орелъ; санскр. ara` and `Орьтъма = плащъ, одежда, покрышка
шатра` (the entry `Оріонъ` now reads *…утро, востокъ, звѣзда щеннослуженіи подстилаетъ…*); on p. 840 three lines
of the article on the letter Ь (`…переходъ его въ е: день (изъ дьнь)…`) and the last two of column b; on p. 1030 `Куръ — (церк.-слав.) = пѣтухъ; санскр. kur пѣть` and
two lines of column b; on p. 1093 one line in each column.

That is why the 11 undercount it: most entries on these pages were still "located" in B, C and D — the alignment
put them on some other line nearby — so their crops show the wrong line without being flagged. Only where a
headword's line was gone and nothing plausible was near did the index record a failure.

## Resolution (session 6, the same day)

Fixed in the build layer, where it arose — no hand corrections:

- `dj_witness.reading_order` looks for the footer only on the pages that carry it, printed page ≡ 1 (mod 16), and
  cuts at the lowest line that matches, since the footer lies below all text. Checked first that this holds: in
  B, C and D the footer's own words (*словарь свящ. Г. Дьяченко*) occur at the foot of 70 pages, every one ≡ 1,
  one per sheet. Against the old code the witnesses' text changes on exactly the 8 pages above: 98 lines
  restored, none lost anywhere. dj_heads VERSION 12.
- `dj_abbyy.py` had the same pattern in A's own layout: on four of those pages (387, 840, 1030, 1093) it had
  filed article lines as the page footer — p. 387's footer held `Орлейщикъ`, `Орьлъ` and `Орьтъма`. The same rule
  there returns 8 lines to A's body; no real footer changed.

Result: 24,841 → 24,845 entries — `Орлейщикъ`, `Орьлъ`, `Орьтъма` and `Куръ` are entries of their own again,
`Фата` and `Февруарій` have their first lines back, and no text slides into a neighbour. The ground-truth scores
are unchanged (none of the eight pages is a GT page). **The unlocated list is down to the two non-headwords**: the
stamp on p. 41 (missing from B, C, D) and the footer's tail on p. 913 (missing from C, D) — five witness-instances,
all correctly so. That these two became entries at all is a defect of A's layout, still open (PROGRESS.md, NEXT).

A check that would have found the footer cut is now in the build: `dj_inspect.py counts` compares every page's
lines and characters in B, C and D with A's and flags a column side where a witness is at least one line short
*and* under 98.5 % of A's characters. Before the fix it flagged all eight pages; after it, none of them.
