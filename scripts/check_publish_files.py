#!/usr/bin/env python3
"""Check exact Git index bytes and package members for accidental private publication.

This dependency-free guard complements a secret scanner and manual staged review.
It reports paths/categories only, never matched values, and does not read untracked
workspace files. A file already tracked or force-added is checked despite ignores.
"""
from pathlib import Path, PurePosixPath
import argparse
import io
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = 'parity.check.tuning.plus'
ROOT_FILES = {
    '.gitattributes', '.gitignore', 'LICENSE', 'NOTICE', 'README.md',
    'package.json', 'package-lock.json', 'requirements-dev.txt',
    f'{PLUGIN}.plg', f'{PLUGIN}.svg', 'paritychecktuningplus.txt',
}
ISSUE_FILES = {
    '.github/labels.json',
    '.github/ISSUE_TEMPLATE/01-bug-report.yml',
    '.github/ISSUE_TEMPLATE/02-feature-request.yml',
    '.github/ISSUE_TEMPLATE/03-translation-problem.yml',
    '.github/ISSUE_TEMPLATE/04-documentation-correction.yml',
    '.github/ISSUE_TEMPLATE/05-question.yml',
    '.github/ISSUE_TEMPLATE/config.yml',
}
LOCAL_DIRS = {
    '.git', '.codex', '.claude', '.cursor', '.vscode', '.idea', '.ssh', '.aws', '.azure', '.kube', 'build',
    'node_modules', '__pycache__', '.pytest_cache', '.venv', 'venv', 'secrets',
    'private', 'host-data', 'diagnostics', 'support-bundles', 'logs', 'tmp', 'temp',
    'coverage', 'htmlcov', 'playwright-report', 'test-results', '.mypy_cache', '.ruff_cache',
}
LOCAL_NAME = re.compile(
    r'(?i)^(?:agents(?:\.local)?\.md|claude(?:\.local)?\.md|\.env(?:\..*)?'
    r'|\.npmrc|\.pypirc|\.?netrc|_netrc|id_rsa.*|id_ed25519.*'
    r'|credentials.*\.json|secrets(?:\..*)?|\.coverage(?:\..*)?'
    r'|\.ds_store|thumbs\.db|desktop\.ini)$'
)
LOCAL_SUFFIXES = {
    '.npp', '.tws', '.bak', '.log', '.tmp', '.orig', '.rej', '.pyc', '.pyo',
    '.pem', '.key', '.p12', '.pfx', '.p8', '.swp', '.swo', '.code-workspace',
    '.sublime-workspace', '.sublime-project',
}
CONTENT_RULES = {
    'private-key': re.compile(rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    'github-token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b'),
    'aws-access-key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'slack-token': re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
    'credential-in-url': re.compile(rb'https?://[^\s/<>"\x27:@]+:[^\s/<>"\x27@]+@'),
    'workstation-path': re.compile(rb'(?i)(?:[a-z]:[\\/]+(?:users|documents and settings)[\\/]+|/(?:Users|home)/)[^\s\x00<>"\x27]+'),
}


def local_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        return True
    return (any(part.lower() in LOCAL_DIRS for part in path.parts[:-1])
            or bool(LOCAL_NAME.fullmatch(path.name))
            and path.name not in {'.env.example', '.env.sample'}
            or path.suffix.lower() in LOCAL_SUFFIXES or path.name.endswith('~'))


def allowed_path(name):
    if local_path(name):
        return False
    if name in ROOT_FILES or name in ISSUE_FILES:
        return True
    path = PurePosixPath(name)
    if re.fullmatch(re.escape(PLUGIN) + r'-\d{4}\.\d{2}\.\d{2}\.\d+\.(?:txz|plg|md5|sha256)', path.name) and path.parent.as_posix() == 'archives':
        return True
    if name.startswith('docs/') and path.suffix == '.md':
        return True
    if name.startswith('scripts/') and path.suffix in {'.py', '.php'}:
        return True
    if name.startswith('tests/'):
        return path.suffix in {'.py', '.php', '.cjs', '.css', '.md', '.json'} or name == 'tests/fixtures/unraid/monitor'
    if name.startswith('translations/') and path.suffix == '.json':
        return True
    if name.startswith(f'source/usr/local/emhttp/plugins/{PLUGIN}/'):
        return path.suffix in {'.php', '.page', '.mdcmd', '.cfg', '.svg', '.json', '.md'} or '/event/' in name
    return bool(re.fullmatch(r'source/usr/local/emhttp/languages/[a-z]{2}_[A-Z]{2}/paritychecktuningplus\.txt', name))


def content_issues(data):
    return [category for category, pattern in CONTENT_RULES.items() if pattern.search(data)]


def inspect_file(name, data):
    issues = []
    if not allowed_path(name):
        issues.append((name, 'unexpected-or-local-file'))
    if name.endswith('.txz'):
        try:
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                for member in archive:
                    if not member.isfile():
                        continue
                    display = name + '!' + member.name
                    if local_path(member.name):
                        issues.append((display, 'local-file-in-package'))
                    if member.size > 16 * 1024 * 1024:
                        issues.append((display, 'oversized-package-member-needs-review'))
                        continue
                    content = archive.extractfile(member).read()
                    issues.extend((display, category) for category in content_issues(content))
        except (tarfile.TarError, EOFError, OSError):
            issues.append((name, 'unreadable-package'))
    else:
        issues.extend((name, category) for category in content_issues(data))
    return issues


def check_index(root=ROOT):
    root = Path(root)
    # ls-files --stage checks staged bytes even if the worktree was edited later.
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root).split(b'\0')
    issues = []
    checked = 0
    for entry in entries:
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, oid, stage = metadata.split()
        name = raw_name.decode('utf-8')
        checked += 1
        if mode not in {b'100644', b'100755'} or stage != b'0':
            issues.append((name, 'unsupported-index-entry'))
            continue
        data = subprocess.check_output(['git', 'cat-file', 'blob', oid.decode('ascii')], cwd=root)
        issues.extend(inspect_file(name, data))
    return checked, issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    count, issues = check_index(args.root)
    for name, category in issues:
        # Keep terminal control characters and matched private values out of logs.
        print(f'FAIL {category}: {ascii(name)}')
    if issues:
        raise SystemExit(1)
    print(f'PASS: {count} indexed files and package contents checked; no local-only paths or configured private-content patterns found.')


if __name__ == '__main__':
    main()
