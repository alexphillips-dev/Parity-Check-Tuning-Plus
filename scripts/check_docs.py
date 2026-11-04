#!/usr/bin/env python3
"""Check README/wiki links and source-derived settings/language documentation."""
from pathlib import Path
import argparse
import json
import re
import xml.etree.ElementTree as ET
from build_package import CHANNELS, manifest_channel

ROOT=Path(__file__).resolve().parents[1]
PLUGIN='parity.check.tuning.plus'


def check(wiki_path=None, branch='dev', root=ROOT):
    root=Path(root)
    wiki=root/'docs/wiki'
    pages={p.stem:p for p in wiki.glob('*.md')}
    content={name:p for name,p in pages.items() if not name.startswith('_')}
    assert len(content)==22 and {'_Sidebar','_Footer'} <= pages.keys()
    manifest=(root/f'{PLUGIN}.plg').read_text()
    manifest_channel(manifest,branch)
    version=ET.fromstring(manifest).attrib['version']
    links=0
    for name,path in pages.items():
        text=path.read_text(encoding='utf-8')
        assert text.count('```')%2==0,f'Unbalanced code fence: {path}'
        if not name.startswith('_'):assert version in text,f'Stale version: {path}'
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('https://','http://','#')):continue
            assert target.split('#')[0] in pages,f'Broken wiki link: {name} -> {target}'
            links+=1
        if wiki_path:assert (wiki_path/path.name).read_bytes()==path.read_bytes(),f'Stale published wiki source: {path.name}'
    readme=(root/'README.md').read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)',readme):
        if target.startswith(('http://','https://','#')):continue
        assert (root/target.split('#')[0]).is_file(),f'Broken README link: {target}'
    for channel in CHANNELS:
        assert f'https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/{channel}/{PLUGIN}.plg' in readme
    assert version in readme and 'git push --no-verify origin dev' in readme
    defaults=dict(line.split('=',1) for line in (root/f'source/usr/local/emhttp/plugins/{PLUGIN}/default.cfg').read_text().splitlines())
    reference=(wiki/'Settings-Reference.md').read_text(encoding='utf-8')
    for key,value in defaults.items():
        value=value.strip('"') or '(empty)'
        assert f'| `{key}` | `{value}` |' in reference,f'Stale documented default: {key}'
    metadata=json.loads((root/f'source/usr/local/emhttp/plugins/{PLUGIN}/locales/locales.json').read_text(encoding='utf-8'))
    languages=(wiki/'Languages-and-Accessibility.md').read_text(encoding='utf-8')
    for code in [*metadata['locales'],*metadata['aliases']]:assert f'`{code}`' in languages,code
    sidebar=(wiki/'_Sidebar.md').read_text(encoding='utf-8')
    for name in content:assert f']({name})' in sidebar,f'Orphan page: {name}'
    print(f'PASS: README, {len(content)} wiki pages, {links} internal links, {len(defaults)} raw settings, and locale documentation.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wiki-path',type=Path)
    parser.add_argument('--branch',choices=CHANNELS,default='dev')
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    check(args.wiki_path,args.branch,args.root)
