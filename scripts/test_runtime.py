#!/usr/bin/env python3
"""Run renamed CLI and schedule generation against simulated Unraid files."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_package import ROOT, PLUGIN


@unittest.skipUnless(os.name == "posix" and shutil.which("php"), "Requires Linux/WSL PHP")
class Runtime(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pct-plus-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.version = ET.fromstring((ROOT/f'{PLUGIN}.plg').read_text()).attrib['version']
        self.plugin = self.root / "usr/local/emhttp/plugins" / PLUGIN
        shutil.copytree(ROOT / "source/usr/local/emhttp/plugins" / PLUGIN, self.plugin)
        # Only fixture copies are rewritten; production source is never executed here.
        for path in list(self.plugin.glob("*.php")) + list(self.plugin.glob('*.page')):
            text = path.read_text()
            for prefix in ("/usr/local/", "/boot/", "/var/local/", "/var/log/", "/etc/unraid-version"):
                text = text.replace(prefix, self.root.as_posix() + prefix)
            path.write_text(text)
        self.config = self.root / "boot/config/plugins" / PLUGIN
        self.config.mkdir(parents=True)
        self.cfg = self.config / f"{PLUGIN}.cfg"
        self.cfg.write_text('parityTuningPlusLogTarget="2"\n')
        self.write(self.plugin / f"{PLUGIN}.version", self.version+'\n')
        self.write(self.root / "etc/unraid-version", 'version="7.2.0"\n')
        self.write(self.root / "boot/config/plugins/dynamix/dynamix.cfg", '[display]\nunit="C"\nlocale="en_US"\n[parity]\ncumulative="0"\n')
        self.write(self.root / "var/local/emhttp/disks.ini", '[parity]\nstatus="DISK_OK"\n[parity2]\nstatus="DISK_NP_DSBL"\n')
        self.write(self.root / "var/local/emhttp/var.ini", 'NAME="FIXTURE"\nmdState="STOPPED"\nmdResyncPos="0"\nmdResyncSize="1000"\nmdResyncAction="check"\nmdResync="0"\nmdResyncCorr="0"\nsbSyncErrs="0"\nsbSynced="1793700000"\nsbSynced2="0"\nsbSyncExit="0"\n')
        helpers = '''<?php
function parse_plugin_cfg($plugin) {
    $root = getenv('PCT_PLUS_FIXTURE');
    return array_replace(
        parse_ini_file("$root/usr/local/emhttp/plugins/$plugin/default.cfg"),
        parse_ini_file("$root/boot/config/plugins/$plugin/$plugin.cfg"));
}
'''
        translations = '''<?php
function parse_plugin($catalog) {
    file_put_contents(getenv('PCT_PLUS_FIXTURE').'/catalog-calls', $catalog."\\n", FILE_APPEND);
}
'''
        self.write(self.root / "usr/local/emhttp/webGui/include/Helpers.php", helpers)
        self.write(self.root / "usr/local/emhttp/webGui/include/Translations.php", translations)
        self.write(self.root / "usr/local/emhttp/plugins/dynamix/include/Wrappers.php", "<?php\n")
        cron = self.root / "usr/local/sbin/update_cron"
        self.write(cron, '#!/bin/sh\necho called >> "$PCT_PLUS_FIXTURE/cron-calls"\n')
        cron.chmod(0o755)
        self.write(self.root / 'bin/logger', '#!/bin/sh\nexit 0\n')
        (self.root / 'bin/logger').chmod(0o755)
        self.cli = self.root / "parity.check.plus"
        if os.name == 'posix':
            self.cli.symlink_to(self.plugin / f"{PLUGIN}.php")
        else:
            shutil.copyfile(self.plugin / f"{PLUGIN}.php", self.cli)

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def simulate_kernel(self):
        """A fixture command that accepts requests and publishes corresponding native state."""
        command=self.root/'usr/local/sbin/mdcmd'
        self.write(command,'''#!/usr/bin/python3
import os,re,sys
from pathlib import Path
root=Path(os.environ['PCT_PLUS_FIXTURE'])
with (root/'mdcmd-calls').open('a') as file:file.write(' '.join(sys.argv[1:])+'\\n')
var=root/'var/local/emhttp/var.ini'
text=var.read_text()
state=dict(re.findall(r'^(\\w+)="([^"]*)"',text,re.M))
args=sys.argv[1:]
if args[0]=='check':
    if len(args)>1 and args[1]=='resume':
        state.update(mdResync='1',sbSynced=str(int(state['sbSynced'])+300),sbSynced2='0',sbSyncExit='0')
    else:
        state.update(mdResync='1',mdResyncPos=str(max(1,int(args[2])//2) if len(args)>2 else 1),mdResyncAction='check P',mdResyncCorr='1' if args[1]=='correct' else '0',sbSynced='1793700000',sbSynced2='0',sbSyncExit='0')
elif args[0]=='nocheck':
    state.update(mdResync='0',sbSynced2=str(int(state['sbSynced'])+600),sbSyncExit='-4')
    if len(args)<2 or args[1]!='PAUSE':state['mdResyncPos']='0'
var.write_text(''.join(key+'="'+value+'"\\n' for key,value in state.items()))
''')
        command.chmod(0o755)

    def command(self, action):
        env = dict(os.environ, PCT_PLUS_FIXTURE=str(self.root), PATH=str(self.root/'bin')+os.pathsep+os.environ['PATH'])
        result = subprocess.run(["php", "-d", "short_open_tag=1", str(self.cli), action],
                                text=True, capture_output=True, timeout=15, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "", result.stderr)
        return result.stdout

    def test_cli_name_catalog_and_log_brand(self):
        output = self.command("help")
        self.assertIn("parity.check.plus <action>", output)
        self.assertNotIn('Unrecognized option',output)
        self.assertIn(self.version, output)
        self.assertEqual((self.root / "catalog-calls").read_text(), "paritychecktuningplus\n")
        log = (self.config / f"{PLUGIN}.log").read_text()
        self.assertIn("Parity Check Tuning Plus:", log)

    def test_extended_cli_help_is_localized_for_every_language(self):
        import json
        metadata=json.loads((self.plugin/'locales/locales.json').read_text())
        cfg=self.root/'boot/config/plugins/dynamix/dynamix.cfg'
        template=cfg.read_text()
        with self.cfg.open('a') as file:file.write('parityTuningPlusLogging="2"\n')
        key='The following are also available for testing purposes only'
        for locale in metadata['locales']:
            cfg.write_text(template.replace('locale="en_US"',f'locale="{locale}"'))
            catalog=json.loads((self.plugin/'locales'/f'{locale}.json').read_text())
            output=self.command('help')
            self.assertIn(catalog[key],output,locale)
            self.assertIn('updatecron',output)

    def test_stopped_status_uses_renamed_cli(self):
        self.assertIn("Status: Array not yet started", self.command("status"))

    def test_active_and_idle_status_do_not_crash(self):
        var = self.root / 'var/local/emhttp/var.ini'
        text = var.read_text().replace('mdState="STOPPED"', 'mdState="STARTED"')
        var.write_text(text)
        self.assertIn('No array operation currently in progress', self.command('status'))
        var.write_text(text.replace('mdResyncPos="0"', 'mdResyncPos="100"').replace('mdResyncAction="check"', 'mdResyncAction="check P"'))
        self.assertIn('PAUSED', self.command('status'))

    def test_defaults_reset_settings_and_reload_cron(self):
        with self.cfg.open('a') as cfg:
            cfg.write('parityTuningPlusBackground="1"\nparityTuningPlusScheduled="0"\n')
        self.command('defaults')
        self.assertIn('parityTuningPlusBackground="0"', self.cfg.read_text())
        self.assertIn('"resume"', (self.config/f'{PLUGIN}.cron').read_text())

    def helper(self, expression):
        import json
        code='require '+json.dumps((self.plugin/f'{PLUGIN}.helpers.php').as_posix())+';echo json_encode('+expression+');'
        result=subprocess.run(['php','-d','short_open_tag=1','-r',code],text=True,capture_output=True,
                              env=dict(os.environ,PCT_PLUS_FIXTURE=str(self.root)))
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(result.stderr,'',result.stderr)
        return json.loads(result.stdout)

    def test_both_parity_slots_are_detected_correctly(self):
        disks=self.root/'var/local/emhttp/disks.ini'
        for first,second,missing in [('DISK_OK','DISK_OK',False),('DISK_NP_DSBL','DISK_NP_DSBL',True),('DISK_OK','DISK_NP_DSBL',False)]:
            disks.write_text(f'[parity]\nstatus="{first}"\n[parity2]\nstatus="{second}"\n')
            self.assertEqual(self.helper('$parityTuningPlusNoParity'),missing)

    def test_localized_action_does_not_change_stored_protocol(self):
        cfg=self.root/'boot/config/plugins/dynamix/dynamix.cfg'
        cfg.write_text(cfg.read_text().replace('locale="en_US"','locale="ja_JA"'))
        stored=self.helper("actionDescription('check P',0,'SCHEDULED',true,false)")
        displayed=self.helper("actionDescription('check P',0,'SCHEDULED',true,true)")
        self.assertEqual(stored,'Scheduled Non-Correcting Parity-Check')
        self.assertNotEqual(displayed,stored)

    def test_backend_percent_range_uses_authoritative_bounds(self):
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdState="STOPPED"','mdState="STARTED"'))
        with self.cfg.open('a') as cfg:
            cfg.write('parityProblemPlusType="percent"\nparityProblemPlusStartPercent="10"\nparityProblemPlusEndPercent="20"\n')
        self.simulate_kernel()
        self.command('partial')
        import json
        state=json.loads((self.config/f'{PLUGIN}.partial').read_text())
        self.assertEqual(state,{'startSector':200,'endSector':400,'correct':False,'kernelStart':1793700000,'size':1000})
        self.assertEqual((self.root/'mdcmd-calls').read_text(),'check nocorrect 200\n')
        self.assertEqual(self.helper('pctPartialEndSector()'),400)

    def test_backend_invalid_range_never_invokes_mdcmd(self):
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdState="STOPPED"','mdState="STARTED"'))
        with self.cfg.open('a') as cfg:cfg.write('parityProblemPlusStartSector="0; touch /tmp/bad"\n')
        self.command('partial')
        self.assertFalse((self.config/f'{PLUGIN}.partial').exists())
        self.assertFalse((self.root/'mdcmd-calls').exists())

    def test_explicit_cli_pause_releases_background_resume_ownership(self):
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdState="STOPPED"','mdState="STARTED"').replace('mdResyncPos="0"','mdResyncPos="100"'))
        marker=self.config/f'{PLUGIN}.mover'
        marker.write_text('{"paused":true,"notified":false}')
        self.command('pause')
        self.assertFalse(marker.exists())

    def test_completed_history_keeps_english_protocol_under_japanese_locale(self):
        import calendar
        import datetime
        cfg=self.root/'boot/config/plugins/dynamix/dynamix.cfg'
        cfg.write_text(cfg.read_text().replace('locale="en_US"','locale="ja_JA"'))
        helpers=self.root/'usr/local/emhttp/webGui/include/Helpers.php'
        with helpers.open('a') as file:file.write("\nfunction my_scale($value,&$unit,$precision){$unit='B';return (string)$value;}\n")
        begin=calendar.timegm(datetime.datetime(2026,11,3,10).timetuple())
        finish=begin+3600
        header='type|date|time|sbSynced|sbSynced2|sbSyncErrs|sbSyncExit|mdState|mdResync|mdResyncPos|mdResyncSize|mdResyncCorr|mdResyncAction|Description\n'
        rows=[]
        for kind,stamp,time,pos in [('SCHEDULED','2026 Nov 03 10:00:00',begin,1),('STARTED','2026 Nov 03 10:00:00',begin,1),('COMPLETED','2026 Nov 03 11:00:00',finish,1000)]:
            rows.append(f'{kind}|{stamp}|{time}|{begin}|{finish if kind=="COMPLETED" else 0}|0|0|STARTED|0|{pos}|1000|0|check P|Scheduled Non-Correcting Parity-Check|\n')
        (self.config/f'{PLUGIN}.progress').write_text(header+''.join(rows))
        history=self.root/'boot/config/parity-checks.log'
        history.write_text('2026 Nov 03 11:00:00|3600|1000000|0|0|check P|1000\n')
        self.command('analyze')
        fields=history.read_text().strip().split('|')
        self.assertEqual(len(fields),10)
        self.assertEqual(fields[-1],'Scheduled Non-Correcting Parity-Check')
        self.assertEqual(fields[5],'check P')

    def test_new_settings_control_cron_after_reload(self):
        self.command("config")
        cron = self.config / f"{PLUGIN}.cron"
        initial = cron.read_text()
        self.assertIn(f"{PLUGIN}/{PLUGIN}.php", initial)
        self.assertIn('15 0 * * * ', initial)
        self.assertIn('"resume"', initial)
        self.assertIn('"pause"', initial)
        self.assertIn('*/17 * * * * ', initial)
        with self.cfg.open("a") as cfg:
            cfg.write('parityTuningPlusScheduled="0"\nparityTuningPlusMonitorDefault="23"\n')
        self.command("updatecron")
        reloaded = cron.read_text()
        self.assertNotIn('"resume"', reloaded)
        self.assertNotIn('"pause"', reloaded)
        self.assertIn('*/23 * * * * ', reloaded)
        self.assertEqual((self.root / "cron-calls").read_text(), "called\ncalled\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
