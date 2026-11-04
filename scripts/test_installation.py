#!/usr/bin/env python3
"""Exercise real manifest shell scripts against temporary Linux filesystem fixtures."""
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_package import ROOT, PLUGIN, channel_manifest


@unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "Requires Linux/WSL bash and symlinks")
class Installation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pct-plus-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.xml = ET.fromstring((ROOT / f"{PLUGIN}.plg").read_text())
        self.scripts = [node.text for node in self.xml.findall("FILE/INLINE")]
        archive = ROOT / "archives" / f"{PLUGIN}-{self.xml.attrib['version']}.txz"
        with tarfile.open(archive) as package:
            package.extractall(self.root, filter="data")
        self.plugin = self.root / "usr/local/emhttp/plugins" / PLUGIN
        self.config = self.root / "boot/config/plugins" / PLUGIN
        self.mdcmd = self.root / "usr/local/sbin/mdcmd"
        self.history = self.root / "usr/local/emhttp/plugins/dynamix/scripts/parity_history"
        self.notify = self.root / "usr/local/emhttp/webGui/scripts/notify"
        self.cli = self.root / "usr/local/bin/parity.check.plus"
        self.write(self.mdcmd, "#!/bin/sh\necho native-mdcmd\n", executable=True)
        self.write(self.history, "#!/bin/sh\necho native-history\n", executable=True)
        self.write(self.notify, "#!/bin/sh\necho native-notify\n", executable=True)
        self.cli.parent.mkdir(parents=True, exist_ok=True)
        # Stub only the application command; manifest hook and removal logic run unchanged.
        self.write(self.plugin / f"{PLUGIN}.php", "#!/bin/sh\nprintf '%s\\n' \"$*\" >> " + shlex.quote(str(self.root / "config-calls")) + "\n", executable=True)
        self.write(self.root / "usr/local/sbin/update_cron", "#!/bin/sh\nexit 0\n", executable=True)
        self.write(self.root / "bin/removepkg", "#!/bin/sh\nexit 0\n", executable=True)

    def write(self, path, text, executable=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        if executable:
            path.chmod(0o755)

    def backup(self, path):
        return path.with_name(path.name + f".{PLUGIN}.orig")

    def run_script(self, index, success=True):
        script = self.scripts[index]
        for prefix in ("/usr/local/", "/boot/"):
            script = script.replace(prefix, str(self.root) + prefix)
        environment = dict(os.environ, PATH=str(self.root / "bin") + os.pathsep + os.environ["PATH"])
        result = subprocess.run(["bash", "-eu"], input=script, text=True, capture_output=True, env=environment)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def install(self):
        self.run_script(0)
        self.run_script(1)

    def test_install_update_remove_preserves_native_hooks_and_settings(self):
        native = {p: p.read_bytes() for p in (self.mdcmd, self.history, self.notify)}
        self.install()
        self.assertTrue(self.cli.is_symlink())
        self.assertEqual(self.cli.resolve(), self.plugin / f"{PLUGIN}.php")
        self.assertEqual((self.root / "config-calls").read_text(), "config\n")
        cfg = self.config / f"{PLUGIN}.cfg"
        self.assertIn('parityTuningPlusBackground="0"',cfg.read_text())
        self.assertIn('parityTuningPlusMover="1"',cfg.read_text())
        cfg.write_text('parityTuningPlusScheduled="0"\nparityTuningPlusBackground="1"\n')
        self.install()
        self.assertEqual(cfg.read_text(), 'parityTuningPlusScheduled="0"\nparityTuningPlusBackground="1"\n')
        for hook, data in native.items():
            self.assertTrue(hook.is_symlink())
            self.assertEqual(self.backup(hook).read_bytes(), data)
        self.run_script(2)
        for hook, data in native.items():
            self.assertFalse(hook.is_symlink())
            self.assertEqual(hook.read_bytes(), data)
        self.assertFalse(self.cli.is_symlink())
        self.assertFalse(self.config.exists())
        self.assertFalse(self.plugin.exists())

    def test_legacy_history_is_restored(self):
        self.history.unlink()
        self.history = self.root / "usr/local/emhttp/plugins/dynamix/include/ParityHistory.php"
        self.write(self.history, "native legacy history\n")
        self.install()
        self.assertTrue(self.history.is_symlink())
        self.run_script(2)
        self.assertEqual(self.history.read_text(), "native legacy history\n")

    def test_explicit_channel_switch_preserves_settings_and_native_backups(self):
        native = {p:p.read_bytes() for p in (self.mdcmd,self.history,self.notify)}
        self.install()
        cfg = self.config/f'{PLUGIN}.cfg'
        cfg.write_text('parityTuningPlusScheduled="0"\nparityTuningPlusBackground="1"\n')
        saved = cfg.read_bytes()
        for channel in ['main','dev']:
            manifest = channel_manifest((ROOT/f'{PLUGIN}.plg').read_text(),channel)
            self.xml = ET.fromstring(manifest)
            self.scripts = [node.text for node in self.xml.findall('FILE/INLINE')]
            self.install()
            self.assertEqual(cfg.read_bytes(),saved)
            self.assertEqual((self.plugin/f'{PLUGIN}.version').read_text().strip(),self.xml.attrib['version'])
            for hook,data in native.items():
                self.assertTrue(hook.is_symlink())
                self.assertEqual(self.backup(hook).read_bytes(),data)
        self.run_script(2)
        for hook,data in native.items():
            self.assertFalse(hook.is_symlink())
            self.assertEqual(hook.read_bytes(),data)

    def test_update_removes_only_retired_integrations_and_preserves_settings(self):
        self.install()
        retired = [self.plugin/'Parity.check.tuning.plus.refresh.page']
        retired += [self.plugin/'event'/name for name in ['driver_loaded','disks_mounted','svcs_restarted','docker_started','libvirt_started','stopping_svcs','stopping_libvirt','stopping_docker','unmounting_disks']]
        for path in retired:
            self.write(path, 'obsolete fixture')
        cfg = self.config/f'{PLUGIN}.cfg'
        cfg.write_text(cfg.read_text()+'parityTuningPlusDocker="1"\nparityTuningPlusContainers="fixture-container"\n')
        saved = cfg.read_bytes()
        self.install()
        self.assertTrue(all(not path.exists() for path in retired))
        for name in ['starting','array_started','started','stopping_array','stopping','stopped']:
            self.assertTrue((self.plugin/'event'/name).is_file(), name)
        self.assertTrue((self.plugin/'Legacy.php').is_file())
        self.assertEqual(cfg.read_bytes(), saved)

    def test_previous_plugin_manifest_blocks_before_changes(self):
        self.write(self.root / "boot/config/plugins" / (PLUGIN.removesuffix(".plus") + ".plg"), "previous")
        result = self.run_script(0, success=False)
        self.assertIn("Uninstall", result.stdout)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.backup(self.mdcmd).exists())

    def test_previous_plugin_directory_blocks_before_changes(self):
        (self.plugin.parent / PLUGIN.removesuffix(".plus")).mkdir()
        self.run_script(0, success=False)
        self.assertFalse(self.config.exists())

    def test_foreign_hook_is_rejected(self):
        other = self.root / "foreign-hook"
        self.write(other, "other plugin")
        self.mdcmd.unlink()
        self.mdcmd.symlink_to(other)
        self.run_script(0, success=False)
        self.assertEqual(self.mdcmd.resolve(), other)
        self.assertFalse(self.config.exists())

    def test_foreign_notification_hook_blocks_before_any_changes(self):
        other = self.root/'foreign-notify'
        self.write(other, '#!/bin/sh\nexit 0\n', executable=True)
        self.notify.unlink()
        self.notify.symlink_to(other)
        self.run_script(0, success=False)
        self.assertEqual(self.notify.resolve(), other)
        self.assertFalse(self.backup(self.mdcmd).exists())

    def test_missing_notification_command_blocks_before_any_changes(self):
        self.notify.unlink()
        self.run_script(0, success=False)
        self.assertFalse(self.backup(self.mdcmd).exists())

    def test_upgrade_adds_notification_hook_to_previous_plus_install(self):
        self.install()
        self.notify.unlink()
        self.backup(self.notify).rename(self.notify)
        saved = self.backup(self.mdcmd).read_bytes()
        self.install()
        self.assertEqual(self.notify.resolve(), self.plugin/f'{PLUGIN}.notify.php')
        self.assertEqual(self.backup(self.notify).read_text(), '#!/bin/sh\necho native-notify\n')
        self.assertEqual(self.backup(self.mdcmd).read_bytes(), saved)

    def test_missing_notification_backup_blocks_update(self):
        self.install()
        self.backup(self.notify).unlink()
        self.run_script(0, success=False)
        self.assertTrue(self.mdcmd.is_symlink())
        self.assertTrue(self.notify.is_symlink())

    def test_missing_notification_backup_blocks_removal_before_restoring_hooks(self):
        self.install()
        self.backup(self.notify).unlink()
        self.run_script(2, success=False)
        self.assertTrue(self.mdcmd.is_symlink())
        self.assertTrue(self.history.is_symlink())
        self.assertTrue(self.notify.is_symlink())
        self.assertTrue(self.plugin.exists())

    def test_removal_preserves_another_owners_notification_hook(self):
        self.install()
        other=self.root/'foreign-notify'
        self.write(other,'#!/bin/sh\necho foreign-notify\n',executable=True)
        self.notify.unlink()
        self.notify.symlink_to(other)
        self.run_script(2)
        self.assertEqual(self.notify.resolve(),other)
        self.assertEqual(other.read_text(),'#!/bin/sh\necho foreign-notify\n')

    def test_removal_preserves_another_owners_hook(self):
        self.install()
        other = self.root / "foreign-hook"
        self.write(other, "other plugin")
        self.mdcmd.unlink()
        self.mdcmd.symlink_to(other)
        self.run_script(2)
        self.assertEqual(self.mdcmd.resolve(), other)
        self.assertEqual(other.read_text(), "other plugin")

    def test_missing_backup_stops_removal(self):
        self.install()
        self.backup(self.mdcmd).unlink()
        self.run_script(2, success=False)
        self.assertTrue(self.plugin.exists())
        self.assertTrue(self.cli.is_symlink())
        self.assertTrue(self.mdcmd.is_symlink())

    def test_shell_syntax(self):
        for script in self.scripts:
            result = subprocess.run(["bash", "-n"], input=script, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        for script in list((self.plugin / "event").iterdir()) + [self.plugin / f"{PLUGIN}.mdcmd"]:
            result = subprocess.run(["bash", "-n", str(script)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_only_plus_translation_caches_are_invalidated(self):
        language=self.root/'usr/local/emhttp/languages/de_DE'
        self.write(language/'paritychecktuningplus.dot','stale cache')
        self.write(language/'another-plugin.dot','other cache')
        self.install()
        self.assertFalse((language/'paritychecktuningplus.dot').exists())
        self.assertEqual((language/'another-plugin.dot').read_text(),'other cache')


if __name__ == "__main__":
    unittest.main(verbosity=2)
