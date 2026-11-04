#!/usr/bin/env python3
"""Validate the renamed source, references, syntax, and exact package contents."""
from pathlib import Path
import argparse
import hashlib
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET

from build_package import ROOT, PLUGIN, CHANNELS, package_files, manifest_channel
from validate_package import validate_members
from check_runtime_references import check as check_runtime_references


def inherited_attribution_names(root=ROOT):
    """Read inherited identity spellings from the preserved copyright notice."""
    names = set()
    for line in (Path(root) / 'NOTICE').read_text(encoding='utf-8').splitlines():
        if not line.startswith('Copyright '):
            continue
        _, separator, holder = line.partition(',')
        if not separator:
            continue
        holder = holder.strip().rstrip('.')
        aliases = re.findall(r'\(([^)]+)\)', holder)
        holder = re.sub(r'\s*\([^)]*\)', '', holder).strip()
        names.update(name for name in [holder, *aliases] if name)
    assert names, 'NOTICE must identify inherited copyright holders'
    return tuple(sorted(names))


def check_attribution(text, names):
    """Permit inherited attribution in source only as a copyright comment."""
    for line in text.splitlines():
        if any(name.casefold() in line.casefold() for name in names):
            assert re.match(r'\s*(?:\*|#|/\*) Copyright ', line), 'Non-notice inherited attribution'


def check(branch='dev', root=ROOT):
    root = Path(root)
    plugin_dir = root / "source/usr/local/emhttp/plugins" / PLUGIN
    check_runtime_references(plugin_dir)
    previous = PLUGIN.removesuffix(".plus")
    old_display = "Parity Check Tuning Plus".removesuffix(" Plus")
    forbidden = [re.escape(previous) + r"(?!\.plus)",
                 re.escape(old_display) + r"(?! Plus)",
                 r"paritychecktuning(?!plus)", r"parityTuning(?!Plus)",
                 r"ParityTuning(?!Plus)", r"PARITY_TUNING_(?!PLUS_)",
                 r"parityProblem(?!Plus|sPlus)", r"parity_tune_",
                 r"paypal\.com|paypalobjects\.com|Dropbox|iCloud",
                 r"plus\.plus|PlusPlus"]
    expected = package_files(root)
    inherited_names = inherited_attribution_names(root)
    paths = [p for p in (root / "source").rglob("*") if p.is_file()]
    paths += [root / "README.md", root / "paritychecktuningplus.txt", root / f"{PLUGIN}.plg"]
    for path in paths:
        data = path.read_bytes()
        assert b"\r" not in data, f"Non-LF source: {path}"
        text = data.decode("utf-8")
        for pattern in forbidden:
            assert not re.search(pattern, text), f"Old identity {pattern!r} in {path}"
        check_attribution(text, inherited_names)
        # Use archive path strings so Windows cannot hide a Linux case mismatch.
        names = set(expected)
        prefix = f"/usr/local/emhttp/plugins/{PLUGIN}/"
        for match in re.finditer(re.escape(prefix) + r"([\w.-]+)", text):
            name = "usr/local/emhttp/plugins/" + PLUGIN + "/" + match[1]
            if match[1].endswith((".php", ".page", ".mdcmd", ".cfg", ".svg")):
                assert name in names, f"Unresolved installed reference {name} in {path}"
    manifest = root / f"{PLUGIN}.plg"
    xml = ET.fromstring(manifest.read_text(encoding="utf-8"))
    assert xml.attrib["name"] == PLUGIN and xml.attrib["author"] == "alexphillips-dev"
    manifest_channel(manifest.read_text(encoding='utf-8'), branch)
    assert xml.attrib["support"] == "https://forums.unraid.net/topic/201158-plugin-parity-check-tuning-plus/"
    version = xml.attrib["version"]
    archive_path = root / "archives" / f"{PLUGIN}-{version}.txz"
    payload = archive_path.read_bytes()
    with tarfile.open(archive_path) as archive:
        validate_members(archive.getmembers())
        for member in archive.getmembers():
            parts = Path(member.name).parts
            assert member.name not in ('.', './', '/'), 'Package must not change filesystem root metadata'
            assert not member.name.startswith('/') and '..' not in parts, f'Unsafe archive path: {member.name}'
            assert member.isfile() or member.isdir(), f'Unexpected archive entry type: {member.name}'
            assert member.uid == member.gid == 0, f'Non-root archive ownership: {member.name}'
            assert member.mode & 0o022 == 0, f'Group/world-writable archive entry: {member.name}'
            if member.isdir():
                assert member.mode == 0o755, f'Incorrect directory mode: {member.name}'
        members = {m.name: m for m in archive if m.isfile()}
        assert members.keys() == expected.keys(), "Archive/source file set differs"
        for name, source in expected.items():
            member = members[name]
            assert archive.extractfile(member).read() == source.read_bytes(), f"Stale package: {name}"
            assert member.uid == member.gid == 0, f"Non-root package ownership: {name}"
            executable = "/event/" in name or name.endswith((f"/{PLUGIN}.php", f"/{PLUGIN}.history.php", f"/{PLUGIN}.notify.php", ".mdcmd"))
            assert member.mode == (0o755 if executable else 0o644), f"Wrong mode: {name}"
    for algorithm in ("md5", "sha256"):
        digest = hashlib.new(algorithm, payload).hexdigest()
        assert re.search(rf'<!ENTITY {algorithm} "{digest}">', manifest.read_text()), f"Manifest {algorithm} differs"
        assert archive_path.with_suffix(f".{algorithm}").read_text().split()[0] == digest
    assert xml.find("FILE[@Name]/SHA256").text == hashlib.sha256(payload).hexdigest()
    assert archive_path.with_suffix(".plg").read_bytes() == manifest.read_bytes()
    assert all(p.name.startswith(PLUGIN + "-") for p in (root / "archives").iterdir()), "Inherited distribution remains"
    assert (root / f"{PLUGIN}.svg").read_bytes() == (plugin_dir / f"{PLUGIN}.svg").read_bytes()
    catalog = (root / "paritychecktuningplus.txt").read_text(encoding="utf-8")
    labels = set(re.findall(r"^:([^\n:]+_plug):$", catalog, re.M))
    page_labels = set()
    for page in plugin_dir.glob("*.page"):
        page_labels.update(re.findall(r"pctHelp\('([^']+)'\)", page.read_text()))
    assert labels <= page_labels, f"Translation help has missing targets: {labels - page_labels}"
    defaults = set(re.findall(r"^(\w+)=", (plugin_dir / "default.cfg").read_text(), re.M))
    for page in plugin_dir.glob("*.page"):
        fields = set(re.findall(r'name=[\x27\x22](parity(?:TuningPlus|ProblemPlus)\w+)[\x27\x22]', page.read_text()))
        assert fields <= defaults, f"Form fields missing defaults: {fields - defaults}"
    php = shutil.which("php")
    assert php, "PHP is required for syntax validation"
    count = 0
    for path in paths:
        if path.suffix in (".php", ".page"):
            result = subprocess.run([php, "-d", "short_open_tag=1", "-l", str(path)], capture_output=True, text=True)
            assert result.returncode == 0, result.stdout + result.stderr
            count += 1
    print(f"PASS: branding, case-sensitive references, translations, settings, XML, {count} PHP/page syntax checks, and {len(expected)} packaged files/checksums.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', choices=CHANNELS, default='dev')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    check(args.branch, args.root)
