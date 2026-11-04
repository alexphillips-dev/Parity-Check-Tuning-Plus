#!/usr/bin/env python3
"""Extract all plugin messages; author bundled translations (runtime stays offline)."""
from pathlib import Path
import argparse
import ast
import concurrent.futures
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'source/usr/local/emhttp/plugins/parity.check.tuning.plus'
LOCALES = PLUGIN / 'locales'
PRINTF = re.compile(r'%(?:\d+\$)?[-+0 #]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[bcdeEfFgGosuxX%]')
PROTECTED = re.compile(r'%(?:\d+\$)?[-+0 #]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[bcdeEfFgGosuxX%]|<[^>]+>|https?://[^\s<>]+|Parity Check Tuning Plus(?: Assistant)?|Unraid|Docker|SMART|Ryzen/ThreadRipper|XMP|`[^`]*`', re.I)
PRINT_LOCK = threading.Lock()


def read(path): return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    temporary.replace(path)


def positional(text):
    index = 0
    def replace(match):
        nonlocal index
        token = match[0]
        if token == '%%' or re.match(r'%\d+\$', token): return token
        index += 1
        return '%' + str(index) + '$' + token[1:]
    return PRINTF.sub(replace, text)


def extract():
    messages = {}
    pattern = re.compile(r'\bpct[THJ]\(\s*([\x27\x22])((?:\\.|(?!\1)[^\\])*?)\1\s*(?=[,)])')
    for path in list(PLUGIN.glob('*.php')) + list(PLUGIN.glob('*.page')):
        source = path.read_text(encoding='utf-8')
        for match in pattern.finditer(source):
            text = ast.literal_eval(match[1] + match[2] + match[1])
            if '$' in text and match[1] == '"': raise ValueError(f'Dynamic translation key in {path}: {text}')
            messages[text] = positional(text)
        for match in re.finditer(r"throw new InvalidArgumentException\('([^']+)'\)", source):
            messages[match[1]] = match[1]
    # Dynamic weekday/date names and the two conditional background-setting labels.
    for text in ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday',
                 'Parity Sync / Data Rebuild','Disk Clear','Manual','Scheduled','Automatic','Partial','Read-Check','Correcting','Non-Correcting','Parity-Check',
                 'Send notifications for mover running','Send notifications for mover or backup running']:
        messages[text] = text
    messages.update(read(ROOT / 'translations/help.en_US.json'))
    return dict(sorted(messages.items()))


def signature(text): return sorted(PROTECTED.findall(text))


def untranslated(source, value):
    prose = re.sub(r'[^A-Za-z ]', '', PROTECTED.sub('', source))
    return source == value and len(prose.split()) >= 4 and len(prose.strip()) >= 20


def chunks(text):
    # Keep native Markdown block structure while translating prose, including long help.
    result = []
    for line in text.splitlines(keepends=True):
        prefix = re.match(r'^(?:> ?)?(?:\* |[0-9]+\. )?', line)[0]
        suffix = '\n' if line.endswith('\n') else ''
        body = line[len(prefix):].removesuffix('\n')
        if not re.search('[A-Za-z]', body):
            result.append((line, False))
        else:
            result.append((prefix, False))
            # A single source line can exceed the service's request limit.
            sentences = re.split(r'(?<=[.!?]) (?=[A-Z])', body) if len(body) > 1500 else [body]
            for i, sentence in enumerate(sentences):
                if i: result.append((' ', False))
                # Keep HTML outside translation requests; services can silently discard
                # even protected line-break tokens. Only the visible prose is translated.
                spans = []
                position = 0
                for match in PROTECTED.finditer(sentence):
                    spans.append((sentence[position:match.start()], True))
                    spans.append((match[0], False))
                    position = match.end()
                spans.append((sentence[position:], True))
                for fragment, translatable in spans:
                    if fragment:
                        translatable = translatable and bool(re.search('[A-Za-z]', fragment))
                        if translatable:
                            leading = re.match(r'^\s*', fragment)[0]
                            trailing = re.search(r'\s*$', fragment)[0]
                            result.extend([(leading, False), (fragment.strip(), True), (trailing, False)])
                        else:
                            result.append((fragment, False))
            result.append((suffix, False))
    return result


def translate_batch(batch, target, attempt=0):
    protected = []
    def protect(text):
        def replace(match):
            protected.append(match[0])
            return f'__{len(protected)-1}__'
        return PROTECTED.sub(replace, text)
    markers = [f'987654321{i:04d}' for i in range(1, len(batch))]
    payload = '\n'.join((markers[i-1] + '\n' if i else '') + protect(text) for i, text in enumerate(batch))
    alternate = attempt % 2 == 1
    query = urllib.parse.urlencode({'client':'gtx' if alternate else 'dict-chrome-ex','sl':'en','tl':target,'q':payload,'dt':'t'})
    endpoint = 'single' if alternate else 't'
    request = urllib.request.Request('https://translate.googleapis.com/translate_a/' + endpoint + '?' + query,
                                     headers={'User-Agent':'ParityCheckTuningPlus-CatalogBuilder/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=35) as response: data = json.load(response)
        text = data[0] if isinstance(data[0], str) else ''.join(segment[0] or '' for segment in data[0])
        parts = re.split(r'\s*(?:' + '|'.join(markers) + r')\s*', text) if markers else [text]
        def restore(text):
            return re.sub(r'__\s*(\d+)\s*__', lambda m: protected[int(m[1])], text.strip())
        parts = [restore(text) for text in parts]
        if len(parts) == len(batch) and any(untranslated(source,value) for source,value in zip(batch,parts)):
            raise RuntimeError('Translation service returned unchanged prose')
        if len(parts) != len(batch) or any((not value and source.strip().lower() not in {'the','a','an'}) or signature(source) != signature(value)
             or re.search(r'__\s*\d+\s*__|987654321\d+', value) for source, value in zip(batch, parts)):
            if len(batch) > 1:
                middle = len(batch)//2
                return translate_batch(batch[:middle], target) + translate_batch(batch[middle:], target)
            raise ValueError('Translation changed protected text: ' + repr((batch[0][:100], parts)))
        return parts
    except Exception as error:
        if isinstance(error, ValueError): raise
        with PRINT_LOCK: print(f'{target}: retry {attempt+1}: {error}', flush=True)
        if attempt >= 4: raise
        time.sleep(min(20, 2 ** attempt))
        return translate_batch(batch, target, attempt + 1)


def author(code, definition, english):
    path = LOCALES / (code + '.json')
    prior = read(path) if path.exists() else {}
    prior.update(read(ROOT/'translations/overrides.json').get(code,{}))
    cache_path = ROOT / 'build/i18n-cache' / (code + '.json')
    cache = read(cache_path) if cache_path.exists() else {}
    cache = {key:value for key,value in cache.items() if signature(key) == signature(value) and not untranslated(key,value)}
    missing = {key:value for key,value in english.items()
               if not prior.get(key) or signature(value) != signature(prior[key]) or untranslated(value,prior[key])}
    units = sorted({part for value in missing.values() for part, translate in chunks(value) if translate and part not in cache})
    batch, size = [], 0
    batches = []
    for unit in units:
        if batch and size + len(unit) > 2400:
            batches.append(batch); batch, size = [], 0
        batch.append(unit); size += len(unit) + 30
    if batch: batches.append(batch)
    for i, batch in enumerate(batches):
        translated = translate_batch(batch, definition['translate'])
        cache.update(zip(batch, translated))
        write(cache_path, cache)
        with PRINT_LOCK: print(f'{code}: batch {i+1}/{len(batches)}', flush=True)
        time.sleep(0.2)
    for key, value in missing.items():
        translated = ''.join(cache[part] if translate else part for part,translate in chunks(value))
        if signature(value) != signature(translated): raise ValueError(f'{code}: damaged message {key}')
        prior[key] = translated
    write(path, {key:prior[key] for key in english})
    with PRINT_LOCK: print(f'{code}: {len(english)}/{len(english)} messages', flush=True)


def native_catalog(catalog):
    lines = ['; Parity Check Tuning Plus - generated offline catalog. Do not edit by hand.', '']
    seen = set()
    for key, value in catalog.items():
        if key.startswith('_') and key.endswith('_plug'):
            lines.extend([':'+key[1:]+':', value, ':end', ''])
            continue
        native_key = re.sub(r'&amp;|[?{}|&~!\[\]()/\\:*^.\"\x27]|<.+?/?>', '', key)
        native_key = re.sub(r'  +', ' ', native_key)
        if native_key.lower() in ['null','yes','no','true','false','on','off','none']: native_key += '.'
        if native_key in seen: continue
        seen.add(native_key)
        lines.append(native_key + '=' + value)
    return '\n'.join(lines) + '\n'


def exports(metadata, check=False):
    for code in [*metadata['locales'], *metadata['aliases']]:
        canonical = metadata['aliases'].get(code,code)
        text = native_catalog(read(LOCALES/(canonical+'.json')))
        path = PLUGIN.parents[1]/'languages'/code/'paritychecktuningplus.txt'
        if check: assert path.read_text(encoding='utf-8') == text, f'{code}: stale native catalog'
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(text,encoding='utf-8',newline='\n')
        if code == 'en_US':
            root = ROOT/'paritychecktuningplus.txt'
            if check: assert root.read_text(encoding='utf-8') == text
            else: root.write_text(text,encoding='utf-8',newline='\n')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--translate', action='store_true', help='Contact translation service to author missing catalog entries')
    parser.add_argument('--check', action='store_true', help='Verify all catalogs offline without changing files')
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    english = extract()
    metadata = read(LOCALES / 'locales.json')
    if args.check:
        assert read(LOCALES/'en_US.json') == english, 'English catalog is stale'
        for code in metadata['locales']:
            catalog = read(LOCALES/(code+'.json'))
            assert catalog.keys() == english.keys(), f'{code}: incomplete keys'
            for key,value in catalog.items():
                assert value.strip() and signature(english[key]) == signature(value), f'{code}: damaged message {key}'
                if code != 'en_US': assert not untranslated(english[key],value), f'{code}: untranslated prose {key}'
                assert '<?' not in value and re.search(r'<(?:script|iframe)\b',value,re.I) is None, f'{code}: unsafe catalog markup'
        exports(metadata,check=True)
        print(f'PASS: {len(metadata["locales"])} languages; {len(english)} messages each, placeholders and markup intact.')
    else:
        write(LOCALES/'en_US.json', english)
        if args.translate:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                jobs=[executor.submit(author, code, definition, english) for code,definition in metadata['locales'].items() if code!='en_US']
                for job in concurrent.futures.as_completed(jobs): job.result()
            exports(metadata)
        print(f'English catalog: {len(english)} messages.')


if __name__ == '__main__': main()
