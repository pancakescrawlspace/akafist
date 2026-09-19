#!/usr/bin/env python3
"""Phase 5 of djachenko/PLAN.md, step 1: link the lemmas of the akathist dictionary to Дьяченко's entries.

    python3 tools/dj_link.py             # dictionary/dictionary.psv × djachenko/entries.tsv -> djachenko/links.tsv

For every lemma (modern-orthography civil form with accents, e.g. благоволи́ти, ага́рянский) the entries of
entries.tsv whose headword_key matches, in this order of match types (the first that yields anything wins):
    exact   the lemma's key equals an entry's key (or one alternative of a multi-word head: "Метохія, метухія",
            "Мехоноѳовый или мехоноѳовъ" are indexed under each alternative)
    verb    infinitive lemma ↔ Дьяченко's 1 sg. present (благоволити ↔ благоволю, благодарствовати ↔ благодарствую,
            беснуютися ↔ беснуюся), and the other way round
    soft    keys compared without ь and ъ anywhere (мечьникъ ~ мечник) and with й = и
    none    no entry — to be resolved by hand (Phase 5.1)
Keys: lowercase, accents removed, ѣ→е, і→и, ѳ→ф, ѵ→и (в after а/е), final ъ dropped — the headword_key of
entries.tsv (dj_parse.modern_key) applied to the lemma too. A lemma with alternatives ("в, во", "он, она, они",
"избавля́ти(ся)") or a gloss ("весь (село)") is tried under each alternative, gloss removed.

Output djachenko/links.tsv: lemma  pos  match  ids  headwords  parts — ids/headwords/parts are ;-separated, in the
order main before supplement, page order. The summary printed at the end counts the match types. NOTE: until
Phase 3b step 2 has read the headwords, most keys come from witness D's garbled reading of the Church Slavonic type
(hw_provisional in entries.tsv), so the match rate is a lower bound; re-run after every step-2 batch.
"""
import csv, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dj_parse import civil, modern_key  # noqa: E402
from dj_witness import DJ  # noqa: E402

LEMMAS = DJ.parent / 'dictionary' / 'dictionary.psv'
ENTRIES = DJ / 'entries.tsv'
LINKS = DJ / 'links.tsv'


def lemma_key(lemma):
    return modern_key(civil(lemma))


def lemma_alternatives(lemma):
    """'в, во' -> [в, во]; 'весь (село)' -> [весь]; 'избавля́ти(ся)' -> [избавлятися, избавляти]; 'он, она, они'."""
    base = re.sub(r'\s*\([^)]*\)\s*$', '', lemma)                 # a gloss in parentheses at the end
    alts = []
    for part in re.split(r',\s*', base):
        part = part.strip()
        if not part:
            continue
        if part.endswith('(ся)'):
            alts += [part[:-4] + 'ся', part[:-4]]
        else:
            alts.append(part)
    return alts or [lemma]


def soft(key):
    return key.replace('ь', '').replace('ъ', '').replace('й', 'и')


def head_alternatives(key):
    """'метохия, метухия' -> ['метохия, метухия', 'метохия', 'метухия']; 'x или y' likewise; 'x, -ся' kept as is."""
    alts = [key]
    for part in re.split(r',\s*|\s+или\s+|\s+и\s+', key):
        part = part.strip()
        if part and part != key and not part.startswith('-'):
            alts.append(part)
    return alts


def verb_variants(key, pos):
    """Keys of the 1 sg. present for an infinitive lemma, and of the infinitive for a 1 sg. entry key (the second
    is used when indexing the entries, so the lookup is symmetric)."""
    out = set()
    refl = ''
    if key.endswith(('ся', 'сѧ')):
        key, refl = key[:-2], 'ся'
    if key.endswith('ти'):
        stem = key[:-2]                                   # благоволи, благодарствова, бесновати -> беснова
        if stem.endswith('ова') or stem.endswith('ева'):
            out.add(stem[:-3] + 'ую')                     # -овати -> -ую
        if stem.endswith(('и', 'е', 'а', 'я')):
            out.add(stem[:-1] + 'ю')                      # благоволи -> благоволю, благодари -> благодарю
            out.add(stem[:-1] + 'у')
            out.add(stem + 'ю')                           # -аю, -ею: благодаря -> благодаряю? (rare) кланяти -> кланяю
        if stem.endswith('ну'):
            out.add(stem)                                 # -нути -> -ну
        out.add(stem + 'ю')
    elif pos is None and key.endswith(('ю', 'у')):        # an entry key: 1 sg. -> possible infinitives
        stem = key[:-1]
        if stem.endswith('у') and key.endswith('ую'):
            out.add(stem[:-1] + 'овати')
        for th in ('и', 'а', 'е', 'я'):
            out.add(stem + th + 'ти')
    return {v + refl for v in out}


def load_entries():
    rows = list(csv.DictReader(open(ENTRIES, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    exact, verb, softi = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in rows:
        key = r['headword_key']
        if not key:
            continue
        for alt in head_alternatives(key):
            exact[alt].append(r)
            softi[soft(alt)].append(r)
            for v in verb_variants(alt, None):
                verb[v].append(r)
    return rows, exact, verb, softi


def link(lemma, pos, exact, verb, softi):
    keys = [lemma_key(a) for a in lemma_alternatives(lemma)]
    for kind in ('exact', 'verb', 'soft'):
        hits = []
        for key in keys:
            if kind == 'exact':
                hits += exact.get(key, [])
            elif kind == 'verb':
                for v in verb_variants(key, pos):
                    hits += exact.get(v, [])
                hits += verb.get(key, [])
            else:
                hits += softi.get(soft(key), [])
        if hits:
            return kind, hits
    return 'none', []


def main():
    rows, exact, verb, softi = load_entries()
    order = {r['id']: i for i, r in enumerate(rows)}
    out, counts, pos_counts = [], Counter(), Counter()
    for line in LEMMAS.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        fields = [f.strip() for f in line.split(' | ')]
        if len(fields) < 2:
            continue
        lemma, pos = fields[0], fields[1]
        kind, hits = link(lemma, pos, exact, verb, softi)
        seen, uniq = set(), []
        for r in sorted(hits, key=lambda r: order[r['id']]):
            if r['id'] not in seen:
                seen.add(r['id'])
                uniq.append(r)
        counts[kind] += 1
        pos_counts[(pos.split('/')[0], kind)] += 1
        out.append(dict(lemma=lemma, pos=pos, match=kind, ids=';'.join(r['id'] for r in uniq),
                        headwords=';'.join(r['headword'] for r in uniq), parts=';'.join(r['part'] for r in uniq)))
    tmp = LINKS.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        cols = ['lemma', 'pos', 'match', 'ids', 'headwords', 'parts']
        f.write('\t'.join(cols) + '\n')
        for o in out:
            f.write('\t'.join(o[c] for c in cols) + '\n')
    tmp.rename(LINKS)
    n = len(out)
    print(f'{n} lemmas: ' + ', '.join(f'{k} {counts[k]} ({counts[k] / n:.0%})' for k in ('exact', 'verb', 'soft', 'none')))
    prov = sum(1 for r in rows if 'hw_provisional' in r['flags'])
    print(f'(entries.tsv: {len(rows)} entries, {prov} with a provisional headword)')
    by_pos = defaultdict(Counter)
    for (p, k), v in pos_counts.items():
        by_pos[p][k] += v
    for p, c in sorted(by_pos.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(c.values())
        print(f'  {p:8} {tot:4}: matched {tot - c["none"]:4} ({(tot - c["none"]) / tot:.0%})')
    unmatched = [o['lemma'] for o in out if o['match'] == 'none']
    print(f'unmatched ({len(unmatched)}): ' + ' '.join(unmatched))
    print(f'written: {LINKS.relative_to(DJ.parent)}')


if __name__ == '__main__':
    main()
