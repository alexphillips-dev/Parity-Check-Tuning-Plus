from pathlib import Path
import os
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from build_package import ROOT, PLUGIN
from validate_package import validate_members


class Package(unittest.TestCase):
    def test_failed_package_validation_preserves_the_existing_archive(self):
        import build_package
        with tempfile.TemporaryDirectory(prefix='pct-plus-atomic-') as directory:
            root=Path(directory)
            (root/'archives').mkdir()
            manifest=ROOT/f'{PLUGIN}.plg'
            (root/manifest.name).write_bytes(manifest.read_bytes())
            version=ET.fromstring(manifest.read_text()).attrib['version']
            archive=root/'archives'/f'{PLUGIN}-{version}.txz'
            archive.write_bytes(b'previous candidate')
            with patch.object(build_package,'ROOT',root),patch.object(build_package,'package_files',return_value={}),patch.object(build_package,'validate_members',side_effect=ValueError('negative control')):
                with self.assertRaises(ValueError):build_package.build()
            self.assertEqual(archive.read_bytes(),b'previous candidate')
            self.assertEqual((root/manifest.name).read_bytes(),manifest.read_bytes())
            self.assertEqual(list((root/'archives').iterdir()),[archive])

    def test_rejects_the_reported_root_metadata_and_other_unsafe_entries(self):
        for name,mode,uid,gid,kind in [
            ('.',0o777,99,100,tarfile.DIRTYPE),
            ('../outside',0o644,0,0,tarfile.REGTYPE),
            ('/usr/local/emhttp',0o755,0,0,tarfile.DIRTYPE),
            ('etc/passwd',0o644,0,0,tarfile.REGTYPE),
            ('usr',0o777,0,0,tarfile.DIRTYPE),
            ('usr',0o755,99,100,tarfile.DIRTYPE),
            ('usr/local/emhttp/plugins/'+PLUGIN+'/hook',0o4755,0,0,tarfile.REGTYPE),
            ('usr/local/emhttp/plugins/'+PLUGIN+'/hook',0o755,0,0,tarfile.SYMTYPE),
        ]:
            with self.subTest(name=name,mode=oct(mode),uid=uid,kind=kind):
                member=tarfile.TarInfo(name)
                member.mode,member.uid,member.gid,member.type=mode,uid,gid,kind
                with self.assertRaises(ValueError):validate_members([member])

    @unittest.skipUnless(os.name=='posix','Linux mode preservation check')
    def test_actual_package_preserves_extraction_root_permissions(self):
        xml=ET.fromstring((ROOT/f'{PLUGIN}.plg').read_text())
        package=ROOT/'archives'/f'{PLUGIN}-{xml.attrib["version"]}.txz'
        with tempfile.TemporaryDirectory(prefix='pct-plus-package-') as directory:
            root=Path(directory)
            root.chmod(0o750)
            before=root.stat()
            with tarfile.open(package) as archive:
                validate_members(archive.getmembers())
                archive.extractall(root,filter='fully_trusted')
            after=root.stat()
            self.assertEqual((before.st_mode,before.st_uid,before.st_gid),(after.st_mode,after.st_uid,after.st_gid))
            self.assertTrue((root/'usr/local/emhttp/plugins'/PLUGIN/f'{PLUGIN}.php').is_file())


if __name__=='__main__':unittest.main(verbosity=2)
