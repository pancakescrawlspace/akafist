# Church Slavonic letters and marks — to copy from

For typing headwords in the letters as printed: the review answers (`heads_review/NNN.txt`, HWOCR.md § 9) and the
ground truth (`eval/gt/`, conventions in `eval/README.md`). Copy a character from here, or see *Typing them* below.
If a character shows as a box, it is still the right character — the viewer's font lacks it (Ponomar Unicode, in
`djachenko/fonts/`, has them all).

The column *civil* is what the norm level makes of the letter — what stage 1 of our model learns, and what a
typed answer is compared by. A civil letter in an answer is therefore never *wrong*, only less informative: the
printed letter is kept in the answer file for stage 2 (letters as printed).

## Letters

**Church Slavonic letters** (not in the pre-reform civil alphabet):

| small | capital | name | codes (small / capital) | civil | how it looks, where it stands |
|:---:|:---:|---|---|:---:|---|
| ѡ | Ѡ | omega | U+0461 / U+0460 | о | w-shaped; often word-initial, and in prefixes (ѡ-) |
| ѿ | Ѿ | ot | U+047F / U+047E | от | omega with a т on top: the prefix от- |
| ѻ | Ѻ | round (wide) omega | U+047B / U+047A | о | a broad round о, usually word-initial |
| ꙩ | Ꙩ | monocular o | U+A669 / U+A668 | о | о with a dot inside (rare: "eye") |
| ꙋ | Ꙋ | monograph uk | U+A64B / U+A64A | у | 8-shaped у, inside a word |
| ѹ | Ѹ | uk (digraph) | U+0479 / U+0478 | у | о and у joined into one letter; type оу (two letters) if they stand apart |
| ѕ | Ѕ | dzelo | U+0455 / U+0405 | з | like a Latin s |
| ꙁ | Ꙁ | zemlya | U+A641 / U+A640 | з | the older letter з. But the ʒ-shaped and ζ-shaped з of the book's types are both written plain з (eval/README.md) |
| є | Є | est' (broad e) | U+0454 / U+0404 | е | a round С with a bar; usually word-initial |
| ѥ | Ѥ | iotified e | U+0465 / U+0464 | е | І joined to є (Old Church Slavonic forms) |
| ї | Ї | i with two dots | U+0457 / U+0407 | і | і with a diaeresis; before a vowel (Катавасїѧ) |
| ѧ | Ѧ | little yus | U+0467 / U+0466 | я | pointed, with a crossbar (Касфїѧ, Въпрѧженикъ); я after a consonant |
| ꙗ | Ꙗ | iotified a | U+A657 / U+A656 | я | І joined to а; я at the start of a word or after a vowel |
| ѩ | Ѩ | iotified little yus | U+0469 / U+0468 | я | І joined to ѧ (OCS forms; p. 856 Ѩзд—) |
| ѫ | Ѫ | big yus | U+046B / U+046A | у | nasal; OCS forms (p. 856 Ѫжь—) |
| ѭ | Ѭ | iotified big yus | U+046D / U+046C | ю | І joined to ѫ (OCS forms) |
| ѯ | Ѯ | ksi | U+046F / U+046E | кс | Greek ξ (Апоплеѯіа, Алеѯандръ) |
| ѱ | Ѱ | psi | U+0471 / U+0470 | пс | Greek ψ (Ѱалтирь) |

**Also in the pre-reform civil alphabet** (kept as they are at the norm level; listed in case the keyboard lacks one):

| small | capital | name | codes (small / capital) |
|:---:|:---:|---|---|
| ѣ | Ѣ | yat | U+0463 / U+0462 |
| і | І | decimal i | U+0456 / U+0406 |
| ѳ | Ѳ | fita (Greek θ) | U+0473 / U+0472 |
| ѵ | Ѵ | izhitsa (Greek υ) | U+0475 / U+0474 |

Look-alikes to avoid: Latin `i`, `s`, `o`, `y`, `v` for і, ѕ, о, у, ѵ; Cyrillic barred о `ө` (U+04E9) for fita ѳ;
palochka `Ӏ` (U+04C0) for І. They look the same on screen but are different characters.

## Marks — only if accents and titla are recorded

Whether the headwords get their accents and titla is left open (PLAN.md, Phase 0 decision 2). Typing them in an
answer does no harm — the civil label drops them, the answer file keeps them. A mark is typed *after* the letter it
stands over; a breathing before an accent (`А҆́`).

| mark | name | code | example |
|:---:|---|---|---|
| ◌҆ | psili (zvatel'tse), the breathing | U+0486 | А҆́зъ |
| ◌́ | oxia, acute accent | U+0301 | сло́во |
| ◌̀ | varia, grave accent (on a final vowel) | U+0300 | добрѣ̀ |
| ◌̑ | kamora, circumflex | U+0311 | marks certain plural forms |
| ◌҃ | titlo | U+0483 | бг҃ъ (Богъ), ст҃ъ (святъ) |
| ◌҇ | pokrytie (the arc over a letter-titlo) | U+0487 | — |
| ◌ⷭ҇ | slovo-titlo: superscript с + pokrytie | U+2DED U+0487 | гдⷭ҇ь (Господь) |
| ◌ⷣ҇ | dobro-titlo: superscript д + pokrytie | U+2DE3 U+0487 | — |
| ◌ⷢ҇ | glagol-titlo: superscript г + pokrytie | U+2DE2 U+0487 | — |
| ◌ⷪ҇ | on-titlo: superscript о + pokrytie | U+2DEA U+0487 | — |
| ◌ⷬ҇ | rtsy-titlo: superscript р + pokrytie | U+2DEC U+0487 | — |
| ◌ⷡ҇ | vedi-titlo: superscript в + pokrytie | U+2DE1 U+0487 | — |
| ◌ⷮ҇ | tverdo-titlo: superscript т + pokrytie | U+2DEE U+0487 | — |

(The GT convention today: a superscript letter is written in its place as an ordinary letter — гдсь — and the
marks are left out; eval/README.md.)

## Typing them on the Mac

- **Copy and paste** from this file.
- **Character Viewer:** Control-Command-Space, then search by name (`little yus`, `ksi`, `omega`, `monograph uk`).
- **Unicode Hex Input:** System Settings → Keyboard → Text Input → Edit… → + → *Unicode Hex Input*. With it
  selected, hold Option and type the four hex digits of the code, e.g. Option + `a64b` → ꙋ, Option + `0467` → ѧ.
- **Text Replacements:** System Settings → Keyboard → Text Replacements…, e.g. `;uk` → ꙋ, `;yus` → ѧ, `;ksi` → ѯ.
  They work in most Mac apps, but not in every code editor.
- **A Church Slavonic keyboard layout:** the Ponomar Project, which makes the Ponomar font, also offers keyboard
  layouts (sci.ponomar.net).
