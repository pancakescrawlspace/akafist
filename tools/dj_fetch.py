#!/usr/bin/env python3
"""Phase 1 of djachenko/PLAN.md: fetch the archive.org scan of Дьяченко's dictionary, extract page images,
write djachenko/manifest.tsv.

    python3 tools/dj_fetch.py --meta       # metadata + OCR layers (~150 MB) into djachenko/scan/
    python3 tools/dj_fetch.py --jp2        # the JP2 zip (2.1 GB), resumable
    python3 tools/dj_fetch.py --extract    # unzip JP2s into djachenko/pages/jp2/
    python3 tools/dj_fetch.py --convert    # JP2 (600 ppi) -> djachenko/pages/NNNN.jpg (300 ppi), parallel, skips existing
    python3 tools/dj_fetch.py --manifest   # write/refresh djachenko/manifest.tsv from scandata + page_numbers.json
    python3 tools/dj_fetch.py --all

Every step is idempotent. Downloads use curl with resume and are verified against the MD5s in the item's _files.xml."""
import argparse, hashlib, json, re, subprocess, sys, zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DJ = ROOT / 'djachenko'
SCAN, PAGES, JP2 = DJ / 'scan', DJ / 'pages', DJ / 'pages' / 'jp2'
MANIFEST = DJ / 'manifest.tsv'

ITEM = '20200215_20200215_0856'
BASE = f'https://archive.org/download/{ITEM}/'
STEM = 'Дьяченко. Полный церковнославянский словарь'
UA = 'akafist-dictionary-research/1.0 (personal digitisation project; contact: r.pannekoek@bereslim.nl)'
META_FILES = [f'{ITEM}_files.xml', f'{STEM}_scandata.xml', f'{STEM}_page_numbers.json',
              f'{STEM}_djvu.txt', f'{STEM}_djvu.xml', f'{STEM}_abbyy.gz']
JP2_ZIP = f'{STEM}_jp2.zip'
WORK_WIDTH = 2126          # 600 ppi -> 300 ppi
JPEG_QUALITY = 88


def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def expected_md5s():
    fx = SCAN / f'{ITEM}_files.xml'
    if not fx.exists():
        return {}
    x = fx.read_text(encoding='utf-8')
    return {m.group(1): m.group(2) for m in re.finditer(r'<file name="([^"]+)"[^>]*>.*?<md5>(\w+)</md5>', x, re.S)}


def download(name):
    SCAN.mkdir(parents=True, exist_ok=True)
    dest = SCAN / name
    md5s = expected_md5s()
    if dest.exists() and name in md5s and md5_of(dest) == md5s[name]:
        print('ok      ', name)
        return
    url = BASE + quote(name)
    print('fetching', name)
    subprocess.run(['curl', '-sS', '-L', '-A', UA, '--retry', '5', '--retry-delay', '10', '-C', '-', '-o', str(dest), url],
                   check=True)
    md5s = expected_md5s()
    if name in md5s and not name.endswith('_files.xml'):     # files.xml cannot list its own checksum
        got = md5_of(dest)
        if got != md5s[name]:
            sys.exit(f'MD5 mismatch for {name}: {got} != {md5s[name]} — delete the file and retry')
        print('verified', name)


def extract():
    z = SCAN / JP2_ZIP
    JP2.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        members = [m for m in zf.namelist() if m.lower().endswith('.jp2')]
        done = 0
        for m in members:
            out = JP2 / Path(m).name
            if out.exists() and out.stat().st_size == zf.getinfo(m).file_size:
                continue
            with zf.open(m) as src, open(out, 'wb') as dst:
                dst.write(src.read())
            done += 1
    print(f'{len(members)} JP2 files, {done} newly extracted')


def leaf_of(name):
    return int(re.search(r'_(\d{4})\.jp2$', name).group(1))


def convert_one(src):
    from PIL import Image
    out = PAGES / f'{leaf_of(src.name):04d}.jpg'
    if out.exists():
        return False
    im = Image.open(src)
    im.draft(None, (WORK_WIDTH, WORK_WIDTH * 2))     # let OpenJPEG decode a reduced resolution level
    im = im.convert('L') if im.mode not in ('L', 'RGB') else im
    w, h = im.size
    if w > WORK_WIDTH:
        im = im.resize((WORK_WIDTH, round(h * WORK_WIDTH / w)), Image.LANCZOS)
    tmp = out.with_suffix('.tmp.jpg')
    im.save(tmp, 'JPEG', quality=JPEG_QUALITY, optimize=True)
    tmp.rename(out)
    return True


def convert():
    srcs = sorted(JP2.glob('*.jp2'), key=lambda p: leaf_of(p.name))
    with ProcessPoolExecutor() as ex:
        n = sum(ex.map(convert_one, srcs, chunksize=4))
    print(f'{len(srcs)} pages, {n} newly converted')


def manifest():
    pn = json.loads((SCAN / f'{STEM}_page_numbers.json').read_text(encoding='utf-8'))
    numbers = {p['leafNum']: (p.get('pageNumber') or '', p.get('confidence')) for p in pn['pages']}
    sd = (SCAN / f'{STEM}_scandata.xml').read_text(encoding='utf-8')
    leaves = [int(m) for m in re.findall(r'<page leafNum="(\d+)"', sd)]
    old = {}
    if MANIFEST.exists():
        for line in MANIFEST.read_text(encoding='utf-8').splitlines()[1:]:
            f = line.split('\t')
            old[int(f[0])] = f
    rows = []
    for leaf in leaves:
        printed, conf = numbers.get(leaf, ('', None))
        prev = old.get(leaf)
        section = prev[2] if prev else ('front' if leaf < 40 and not printed else '')
        letter = prev[3] if prev else ''
        status = prev[4] if prev else 'new'
        notes = prev[5] if prev and len(prev) > 5 else ''
        if (PAGES / f'{leaf:04d}.jpg').exists() and status == 'new':
            status = 'image'
        if prev and prev[1]:
            printed = prev[1]                     # hand corrections win over the automatic map
        elif conf is not None and conf < 90:
            notes = notes or f'page number confidence {conf}'
        rows.append([str(leaf), printed, section, letter, status, notes])
    tmp = MANIFEST.with_suffix('.tmp')
    tmp.write_text('idx\tprinted_page\tsection\tletter\tstatus\tnotes\n' +
                   ''.join('\t'.join(r) + '\n' for r in rows), encoding='utf-8')
    tmp.rename(MANIFEST)
    print(f'manifest: {len(rows)} leaves, {sum(1 for r in rows if r[4] != "new")} with images')


def main():
    ap = argparse.ArgumentParser()
    for opt in ('meta', 'jp2', 'extract', 'convert', 'manifest', 'all'):
        ap.add_argument('--' + opt, action='store_true')
    a = ap.parse_args()
    if a.all or a.meta:
        for name in META_FILES:
            download(name)
    if a.all or a.jp2:
        download(JP2_ZIP)
    if a.all or a.extract:
        extract()
    if a.all or a.convert:
        convert()
    if a.all or a.manifest:
        manifest()


if __name__ == '__main__':
    main()
