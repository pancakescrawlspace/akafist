# Akathist to the Theotokos before the Kazan icon — groundwork for a Dutch translation

Source: https://azbyka.ru/molitvoslov/akafist-presvjatoj-bogorodice-pred-ikonoj-kazanskaja.html
(Church Slavonic in civil script with stress marks, with a Russian rendering), retrieved 2026-09-19.

## Contents

| Path | What it is |
|---|---|
| `source/akafist-kazanskaja-cs.txt` | The Church Slavonic text, one paragraph per line, headings `## Конда́к 1.` etc. (kontakia 1–13, ikoi 1–12, the repeated ikos 1 / kontakion 1, two prayers). |
| `source/akafist-kazanskaja-ru.txt` | The Russian rendering from the same page, aligned paragraph for paragraph. |
| `dictionary/dictionary.psv` | **Master dictionary** (edit this one). 703 entries, one per line, fields separated by ` \| `: lemma · part of speech · attested forms · Russian · English · Dutch · notes. |
| `dictionary/dictionary.md` | The same, generated as readable Markdown, alphabetical, with occurrence counts per form. |
| `dictionary/forms-index.tsv` | Every word-form of the text (1070) → its lemma, so a form met while translating can be looked up directly. |
| `dictionary/dictionary.typ`, `dictionary/dictionary.pdf` | The same in a conventional printed-dictionary layout (Typst source and the compiled PDF): two columns on A5, run-in entries with hanging indent, guide words in the running head, letters bookmarked in the PDF outline. |
| `tools/build.py` | Regenerates all derived files from the master and checks that every form in the source text is covered by exactly one entry: `python3 tools/build.py` (options: `--paper a4` gives three columns; `--columns`, `--size`; `--no-pdf` skips the Typst compilation). |

## How the dictionary was made

1. The Church Slavonic text was tokenised (2298 tokens, 1070 distinct forms after removing stress marks).
2. Every form was assigned to a lemma by hand; the build script verifies that nothing is missing, nothing is claimed twice
   (except the two deliberate homonyms `мир` peace/world and `о` preposition/interjection), and that no listed form is absent from the text.
3. Every lemma got a Russian, English and Dutch gloss and, where relevant, notes on the Greek term behind it, its biblical
   locus (LXX psalm numbering), the liturgical text it quotes or echoes, false friends with modern Russian, and the usual
   Dutch Orthodox rendering.

Coverage is complete: all nouns, adjectives, verbs, adverbs, participles and numerals are in, and — since they cost little
and sometimes matter (`ра́ди`, `ра́зве`, `я́ко`, `да`, `е́же`, the relative `-же` pronouns) — so are the pronouns,
prepositions, conjunctions and particles, with short glosses.

The PDF is compiled with [Typst](https://typst.app) (0.15 was used). The Typst source uses PT Serif (bundled with macOS)
for Cyrillic and Latin because it anchors the combining stress mark (U+0301) correctly on Cyrillic vowels, and falls back to
Typst's bundled Libertinus Serif for Greek. If PT Serif is not installed Typst warns and uses Libertinus throughout, which
leaves the stress marks visibly displaced to the right of their vowels; any serif font with Cyrillic mark anchoring
(Times New Roman also works) can be put first in the `font:` list of `tools/build.py`.

## Conventions

- Headwords are in civil script with the stress as printed in the source. Verbs are given under the infinitive
  (`вопи́ти`), participles under their verb, nouns in nom. sg., adjectives in the long masculine form (`благи́й`),
  fixed epithets of the Theotokos capitalised as in the source (`Пречи́стый`, `Засту́пница`).
- Glosses separated by `;` are alternatives, most literal / most usual first. Russian glosses give the modern
  Russian equivalent(s) of the *lemma*, which is not always the word the page's Russian rendering uses in context.
- Dutch glosses lean on Dutch Orthodox liturgical usage where a fixed term exists (`Moeder Gods`, `Alheilige`,
  `Alreine`, `Verheug u`, `ontferming`, `in de eeuwen der eeuwen`, `eerbiedwaardiger dan de Cherubijnen`) and on the Dutch Bible
  tradition for Gospel quotations (Luke 1:28, 30, 38, 42, 48).

## Church Slavonic words that are not what they look like in Russian

The notes flag these individually; the ones a translator most needs to have in mind:

| CS | means | not |
|---|---|---|
| воня́ | fragrance, sweet smell (2 Cor 2:16) | stench |
| живо́т | life | belly |
| лесть | deceit, delusion, error (Mt 27:64) | flattery |
| напра́сный | sudden (of death) | vain, futile |
| находи́ти (находящих зол) | to come upon, befall | to find |
| призре́ние | gracious care, looking-after | contempt |
| изве́стный | sure, certain, reliable | famous |
| живо́тный | of life, life-giving | animal |
| честны́й | honoured, precious, venerable | honest |
| стра́стный | of the passions (πάθη) | passionate (romantic) |
| те́плый | fervent, ardent | lukewarm |
| горе́ (adv.) | on high, above | woe |
| любе́зно | lovingly | politely |
| забра́ло | rampart, bulwark | visor |
| пала́та | palace | ward, chamber |
| весь (noun) | village | — (homonym of *весь* "all") |
| лик / лице́ | choir, company / face | — (two different nouns) |
| у́м / ра́зум / смысл | νοῦς / γνῶσις-σύνεσις / φρόνημα | — (three words, keep them apart) |

## Passages that quote or echo other texts

Worth deciding once, then keeping identical wherever they recur:

- **Refrain** (×15): `Ра́дуйся, Засту́пнице усе́рдная ро́да христиа́нскаго` — from the Kazan troparion (tone 4).
  The first six lines of Ikos 4 paraphrase the rest of that troparion (`Ма́ти Бо́га Вы́шняго … в держа́вный Тво́й покро́в прибега́ющим`).
- **Luke 1** in Ikos 9: `Благода́тная`, `Госпо́дь с Тобо́ю` (1:28), `Благослове́нная в жена́х` (1:42), `обре́тшая благода́ть у Бо́га` (1:30),
  `осене́нная си́лою Всевы́шняго` (1:35), `ве́рная Рабо́ Госпо́дня` (1:38), `блажа́т вси́ ро́ди` (1:48); in Prayer 1 `сокруше́нным се́рдцем` (Ps 50:19 LXX).
- **Great Akathist** (Ἀκάθιστος): Ikos 1 (`А́нгел предста́тель по́слан бы́сть рещи́…`), Ikos 2 (`Разуме́ние … и́щущи`; `неве́рных сумни́тельное слы́шание / ве́рных изве́стная похвало́`),
  Kontakion 3 (`Си́ла Вы́шняго`), Kontakion 5 (`Боготе́чная звезда́`), Ikos 6 (`Возсия́вши просвеще́ние и́стинное и отгна́вши … ле́сть`), Kontakion 8 (`Стра́нно … неве́рующим слу́шати`),
  Ikos 8 (`Невмести́маго вмести́лище`), Kontakion 9 (`Вся́каго естества́ а́нгельскаго превы́шшая`), Ikos 9 (`Вити́я многовеща́нныя, я́ко ры́бы безгла́сныя`),
  Kontakion 10 (`Спасти́ хотя́щи`), Ikos 10 (`Стена́ еси́`), Ikos 11 (`светоприе́мную свещу́ … невеще́ственный о́гнь … наставля́ющи`), Kontakion 12 (`Благода́ть да́ти восхоте́вши`),
  Ikos 12 (`Пою́ще … хва́лим Тя́`), Kontakion 13 (`О Всепе́тая Ма́ти, ро́ждшая все́х святы́х Святе́йшее Сло́во, приими́ ны́не ма́лое сие́ моле́ние`), and the refrain `Неве́сто Неневе́стная` (Ikos 11).
- **Theophany canon, 9th-ode irmos** (`Недоуме́ет вся́к язы́к благохвали́ти по достоя́нию, изумева́ет же у́м … пе́ти Тя́ … оба́че, Блага́я су́щи…`) in Ikos 9.
- **Hymn to the Theotokos** `Честне́йшую Херуви́м и Сла́внейшую без сравне́ния Серафи́м` in Kontakion 9.
- **Kontakion "Предста́тельство христиа́н непосты́дное, хода́тайство ко Творцу́ непрело́жное"** behind `христиа́н непосты́дное упова́ние` (Ikos 12) and `хода́тайству Твоему́` (Prayer 2).
- **Vespers/Compline prayer** `Не и́мамы ины́я по́мощи, не и́мамы ины́я наде́жды, ра́зве Тебе́` in both prayers.
- **Icon titles**: `все́х скорбя́щих Ра́досте` (Ikos 3), `Живоно́сный Исто́чник` (Ikos 12), `Одиги́трия / Путеводи́тельница` (Ikos 7, Ikos 5), `Держа́вный покро́в`.
- **St Basil / Nicaea II**: `че́сть бо ико́ны на первообра́зное восхо́дит` (Kontakion 8).
- **Doxologies**: `Пречестно́е и Великоле́пое И́мя Отца́ и Сы́на и Свята́го Ду́ха`, `ны́не и при́сно и во ве́ки веко́в`, `Тебе́ сла́ва подоба́ет`.
