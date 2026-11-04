#!/usr/bin/env python3
"""Find unreachable owned PHP functions and unreferenced page JavaScript functions.

Native parser compatibility entry points are explicit external roots. Tokenization
does not execute Unraid code. This structural check complements behavioral tests;
it is not a proof about every possible dynamic host interaction or code branch.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT/'source/usr/local/emhttp/plugins/parity.check.tuning.plus'
HOST_PARSER_API = {'_', 'parse_lang_file', 'parse_help_file', 'parse_text', 'parse_file', 'parse_plugin'}


def php_references(plugin):
    output = subprocess.check_output(['php','-d','short_open_tag=1',str(ROOT/'scripts/runtime_references.php'),str(plugin)])
    graph = json.loads(output)
    reachable = set(graph['roots'])
    reachable.update(name for name, definition in graph['definitions'].items()
                     if definition['file'] == 'Legacy.php' and definition['name'] in HOST_PARSER_API)
    pending = list(reachable)
    while pending:
        for callee in graph['edges'].get(pending.pop(), []):
            if callee not in reachable:
                reachable.add(callee)
                pending.append(callee)
    return [definition for name, definition in graph['definitions'].items() if name not in reachable]


def without_js_comments(source):
    # Preserve strings and handler attributes while discarding actual comments.
    result = []; index = 0; quote = None
    source = re.sub(r'<!--.*?-->', lambda match: '\n' * match[0].count('\n'), source, flags=re.S)
    while index < len(source):
        char = source[index]
        if quote:
            result.append(char)
            if char == '\\' and index+1 < len(source):
                index += 1; result.append(source[index])
            elif char == quote: quote = None
        elif char in {'"', "'", '`'}:
            quote = char; result.append(char)
        elif source.startswith('//', index):
            index = source.find('\n', index)
            if index < 0: break
            result.append('\n')
        elif source.startswith('/*', index):
            end = source.find('*/', index+2)
            finish = len(source) if end < 0 else end+2
            result.append('\n' * source[index:finish].count('\n') or ' ')
            index = finish; continue
        else: result.append(char)
        index += 1
    return ''.join(result)


def javascript_references(plugin):
    unused = []
    for page in Path(plugin).glob('*.page'):
        source = without_js_comments(page.read_text(encoding='utf-8'))
        for match in re.finditer(r'\bfunction\s+(\w+)\s*\(', source):
            name = match[1]
            if len(re.findall(r'\b'+re.escape(name)+r'\b', source)) == 1:
                unused.append({'file':page.name,'name':name,'line':source[:match.start()].count('\n')+1})
    return unused


def check(plugin=PLUGIN):
    issues = php_references(plugin) + javascript_references(plugin)
    for issue in issues:
        print(f"Unreferenced runtime function: {issue['file']}:{issue['line']} {issue['name']}")
    if issues: raise SystemExit(1)
    print('PASS: owned PHP functions reachable from entry points/callbacks; page JavaScript functions referenced; native parser API retained.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin', type=Path, default=PLUGIN)
    check(parser.parse_args().plugin)
