"""Channel isolation, immutable package identity, and failure-before-write checks."""
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

import build_package as packaging


class Channels(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pct-channels-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root/f'{packaging.PLUGIN}.plg'
        self.manifest.write_bytes((packaging.ROOT/self.manifest.name).read_bytes())
        for name in ['LICENSE','NOTICE','paritychecktuningplus.txt']:
            shutil.copyfile(packaging.ROOT/name,self.root/name)
        source = self.root/'source/usr/local/emhttp/plugins'/packaging.PLUGIN
        source.mkdir(parents=True)
        (source/'default.cfg').write_text('fixture="unchanged"\n')

    def snapshot(self):
        return {p.relative_to(self.root).as_posix():p.read_bytes() if p.is_file() else None
                for p in self.root.rglob('*')}

    def test_channel_build_matrix_preserves_package_scripts_version_and_history(self):
        archive_dir = self.root/'archives'
        archive_dir.mkdir()
        historical = archive_dir/f'{packaging.PLUGIN}-2020.01.01.01.plg'
        historical.write_bytes(b'historical snapshot must not change')
        original = ET.fromstring(self.manifest.read_text())
        results = []
        for channel in ['dev','main','dev']:
            packaging.build(channel,root=self.root)
            value = self.manifest.read_text()
            self.assertEqual(packaging.manifest_channel(value,channel),channel)
            xml = ET.fromstring(value)
            version = xml.attrib['version']
            archive = archive_dir/f'{packaging.PLUGIN}-{version}.txz'
            self.assertEqual(xml.attrib['version'],original.attrib['version'])
            self.assertEqual([node.text for node in xml.findall('FILE/INLINE')],
                             [node.text for node in original.findall('FILE/INLINE')])
            self.assertEqual(xml.find('FILE[@Name]').attrib,original.find('FILE[@Name]').attrib)
            base = f'https://raw.githubusercontent.com/{packaging.REPOSITORY}/{channel}/'
            self.assertEqual(xml.attrib['pluginURL'],base+f'{packaging.PLUGIN}.plg')
            self.assertEqual(xml.find('FILE/URL').text,base+f'archives/{archive.name}')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(xml.find('FILE/SHA256').text,digest)
            self.assertEqual(archive.with_suffix('.sha256').read_text().split()[0],digest)
            self.assertEqual(archive.with_suffix('.plg').read_bytes(),self.manifest.read_bytes())
            results.append(archive.read_bytes())
        self.assertEqual(results[0],results[1])
        self.assertEqual(results[0],results[2])
        self.assertEqual(historical.read_bytes(),b'historical snapshot must not change')

    def test_preview_of_either_channel_changes_no_files_or_directories(self):
        before = self.snapshot()
        for channel in ['dev','main']:
            packaging.build(channel,dry_run=True,root=self.root)
            self.assertEqual(self.snapshot(),before)

    def test_mixed_or_foreign_channel_urls_fail_before_artifact_changes(self):
        packaging.build('dev',root=self.root)
        valid = self.manifest.read_text()
        mutations = [
            valid.replace('/&branch;/archives/','/main/archives/'),
            valid.replace('/&branch;/&plugin;.plg','/main/&plugin;.plg'),
            valid.replace('alexphillips-dev/Parity-Check-Tuning-Plus','untrusted/other-project'),
            valid.replace('<!ENTITY branch "dev">','<!ENTITY branch "preview">'),
            valid.replace('</PLUGIN>',''),
        ]
        for candidate in mutations:
            with self.subTest(candidate=mutations.index(candidate)):
                self.manifest.write_text(candidate)
                before = self.snapshot()
                with self.assertRaises((ValueError,ET.ParseError)):
                    packaging.build('main',root=self.root)
                self.assertEqual(self.snapshot(),before)

    def test_wrong_expected_channel_and_invalid_build_channel_are_rejected(self):
        value = self.manifest.read_text()
        main = packaging.channel_manifest(value,'main')
        with self.assertRaisesRegex(ValueError,'channel mismatch'):
            packaging.manifest_channel(main,'dev')
        before = self.snapshot()
        with self.assertRaises(ValueError):
            packaging.build('preview',root=self.root)
        self.assertEqual(self.snapshot(),before)
