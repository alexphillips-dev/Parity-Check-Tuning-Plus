#!/usr/bin/env python3
"""Build the Plus package reproducibly and refresh local manifest checksums."""
from pathlib import Path
import argparse
import hashlib
import io
import re
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from validate_package import validate_members

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "parity.check.tuning.plus"
REPOSITORY = 'alexphillips-dev/Parity-Check-Tuning-Plus'
CHANNELS = ('dev', 'main')


def package_files(root=None):
    root = Path(ROOT if root is None else root)
    files = {p.relative_to(root / "source").as_posix(): p
             for p in sorted((root / "source").rglob("*")) if p.is_file()}
    files["usr/local/emhttp/languages/en_US/paritychecktuningplus.txt"] = root / "paritychecktuningplus.txt"
    for installed, source in (("COPYING", "LICENSE"), ("NOTICE", "NOTICE")):
        files[f"usr/local/emhttp/plugins/{PLUGIN}/{installed}"] = root / source
    return files


def manifest_channel(text, expected=None):
    """Reject unknown/mixed channels before any package files are written."""
    xml = ET.fromstring(text)
    declared = re.findall(r'<!ENTITY branch "([^"]+)">', text)
    if len(declared) != 1 or declared[0] not in CHANNELS:
        raise ValueError('Manifest must declare exactly one dev or main branch entity')
    channel = declared[0]
    if expected is not None and channel != expected:
        raise ValueError(f'Manifest channel mismatch: expected {expected}, found {channel}')
    version = xml.attrib.get('version', '')
    if not re.fullmatch(r'[0-9]{4}\.[0-9]{2}\.[0-9]{2}(?:\.[0-9]+)?', version):
        raise ValueError('Invalid plugin version')
    base = f'https://raw.githubusercontent.com/{REPOSITORY}/{channel}/'
    if xml.attrib.get('name') != PLUGIN or xml.attrib.get('pluginURL') != base+f'{PLUGIN}.plg':
        raise ValueError('Incorrect plugin identity or self-update channel URL')
    downloads = xml.findall('FILE/URL')
    package = xml.findall('FILE[@Name]')
    if (len(downloads) != 1 or len(package) != 1
            or package[0].find('URL') is not downloads[0]
            or downloads[0].text != base+f'archives/{PLUGIN}-{version}.txz'
            or package[0].attrib['Name'] != f'/boot/config/plugins/{PLUGIN}/{PLUGIN}-{version}.txz'):
        raise ValueError('Incorrect archive identity or download channel URL')
    return channel


def channel_manifest(text, channel):
    if channel not in CHANNELS:
        raise ValueError('Build channel must be dev or main')
    manifest_channel(text)
    text = re.sub(r'<!ENTITY branch "[^"]+">', f'<!ENTITY branch "{channel}">', text, count=1)
    text = re.sub(r'<!ENTITY pluginURL "[^"]+">',
                  '<!ENTITY pluginURL "https://raw.githubusercontent.com/&github;/&branch;/&plugin;.plg">', text, count=1)
    text = re.sub(r'<URL>[^<]+</URL>',
                  '<URL>https://raw.githubusercontent.com/&github;/&branch;/archives/&plugin;-&version;.txz</URL>', text, count=1)
    manifest_channel(text, channel)
    return text


def build(branch=None, dry_run=False, root=None):
    root = Path(ROOT if root is None else root)
    manifest = root / f"{PLUGIN}.plg"
    text = manifest.read_text(encoding="utf-8")
    current = manifest_channel(text)
    branch = current if branch is None else branch
    text = channel_manifest(text, branch)
    version = ET.fromstring(text).attrib['version']
    output = root / "archives" / f"{PLUGIN}-{version}.txz"
    files = package_files(root)
    directories = {parent.as_posix() for name in files
                   for parent in Path(name).parents if parent.as_posix() != "."}
    if dry_run:
        print(f'Would build {output.name}: channel {branch}; {len(files)} files; no files changed')
        return
    output.parent.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.'+PLUGIN+'-', suffix='.txz.tmp', dir=output.parent, delete=False) as file:
        staged = Path(file.name)
    try:
        write_archive(staged, files, directories)
        with tarfile.open(staged) as archive:
            validate_members(archive.getmembers())
        data = staged.read_bytes()
        staged.replace(output)
    finally:
        if staged.exists(): staged.unlink()
    for algorithm in ("md5", "sha256"):
        digest = hashlib.new(algorithm, data).hexdigest()
        text = re.sub(rf'<!ENTITY {algorithm} "[^"]*">', f'<!ENTITY {algorithm} "{digest}">', text)
        output.with_suffix(f".{algorithm}").write_text(f"{digest}  {output.name}\n", encoding="utf-8", newline="\n")
    ET.fromstring(text)
    manifest.write_text(text, encoding="utf-8", newline="\n")
    output.with_suffix(".plg").write_text(text, encoding="utf-8", newline="\n")
    print(f"Built {output.name}: channel {branch}; {len(files)} files; SHA256 {hashlib.sha256(data).hexdigest()}")


def write_archive(path, files, directories):
    with tarfile.open(path, "w:xz", format=tarfile.USTAR_FORMAT) as archive:
        for name in sorted(directories):
            info = tarfile.TarInfo(name + "/")
            info.type, info.mode = tarfile.DIRTYPE, 0o755
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = "root"
            archive.addfile(info)
        for name, path in sorted(files.items()):
            data = path.read_bytes()
            info = tarfile.TarInfo(name)
            executable = "/event/" in name or name.endswith((f"/{PLUGIN}.php", f"/{PLUGIN}.history.php", f"/{PLUGIN}.notify.php", ".mdcmd"))
            info.mode, info.size = (0o755 if executable else 0o644), len(data)
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = "root"
            archive.addfile(info, io.BytesIO(data))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', choices=CHANNELS, help='Set both update/download URLs to this channel; default preserves declared channel')
    parser.add_argument('--dry-run', action='store_true', help='Validate and preview without changing any files')
    parser.add_argument('--root', type=Path, default=ROOT, help='Build an isolated candidate checkout instead of this checkout')
    args = parser.parse_args()
    build(args.branch, args.dry_run, args.root)
