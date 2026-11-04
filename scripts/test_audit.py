"""Repository audit regressions exercising isolated copies of actual runtime code."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

import test_runtime
from build_package import ROOT, PLUGIN


@unittest.skipUnless(os.name == 'posix' and shutil.which('php'), 'Requires Linux/WSL PHP')
class Audit(unittest.TestCase):
    def setUp(self):
        self.host = test_runtime.Runtime('test_cli_name_catalog_and_log_brand')
        self.host.setUp()
        self.addCleanup(self.host.doCleanups)
        self.root = self.host.root
        self.config = self.host.config
        self.main = self.host.plugin/f'{PLUGIN}.php'
        # All potentially destructive commands and marker paths remain in this fixture.
        for path in self.host.plugin.glob('*.php'):
            text = path.read_text()
            for prefix in ['/sbin/', '/mnt/', '/var/run/', '/tmp/appdata.backup/', '/tmp/ca.backup2/']:
                for quote in ['"', "'"]:
                    text = text.replace(quote+prefix, quote+self.root.as_posix()+prefix)
            text = text.replace('sleep (30);', 'usleep(1);').replace('loadVars(5)', 'loadVars(0)').replace('loadVars(10)', 'loadVars(0)').replace('loadVars(30)', 'loadVars(0)')
            path.write_text(text)
        self.host.write(self.root/'usr/local/emhttp/webGui/include/CustomMerge.php', '<?php\n')
        self.host.write(self.root/'sbin/shutdown', '#!/bin/sh\nprintf "%s\\n" "$*" >> "$PCT_PLUS_FIXTURE/shutdown-calls"\n')
        (self.root/'sbin/shutdown').chmod(0o755)
        self.host.write(self.root/'usr/local/sbin/mdcmd', '#!/bin/sh\nprintf "%s\\n" "$*" >> "$PCT_PLUS_FIXTURE/mdcmd-calls"\n')
        (self.root/'usr/local/sbin/mdcmd').chmod(0o755)
        (self.root/'bin/mdcmd').symlink_to(self.root/'usr/local/sbin/mdcmd')

    def configure(self, values):
        with self.host.cfg.open('a') as file:
            for key,value in values.items():
                value=value.replace('"','\\"')
                file.write(f'{key}="{value}"\n')

    def active(self, running=True):
        path=self.root/'var/local/emhttp/var.ini'
        text=path.read_text().replace('mdState="STOPPED"','mdState="STARTED"').replace('mdResyncPos="0"','mdResyncPos="100"').replace('mdResyncAction="check"','mdResyncAction="check P"')
        path.write_text(text.replace('mdResync="0"',f'mdResync="{1 if running else 0}"'))

    def disk(self, temperature):
        self.host.write(self.root/'var/local/emhttp/disks.ini',f'[parity]\nname="parity"\nstatus="DISK_OK"\ntemp="{temperature}"\nsize="1000"\nhotTemp="45"\nmaxTemp="55"\nid="fixture-disk"\n')

    def test_critical_heat_shutdown_is_independent_of_completion_shutdown(self):
        self.active()
        self.disk(60)
        self.configure({'parityTuningPlusHeatShutdown':'1','parityTuningPlusShutdown':'0'})
        self.host.command('monitor')
        self.assertEqual((self.root/'shutdown-calls').read_text(),'-h -P now\n')
        self.assertTrue((self.config/f'{PLUGIN}.critical').exists())

    def test_shutdown_temperature_monitoring_does_not_enable_pause_policy(self):
        self.active()
        self.disk(47)
        self.configure({'parityTuningPlusHeatShutdown':'1','parityTuningPlusHeat':'0'})
        self.host.command('monitor')
        self.assertFalse((self.root/'mdcmd-calls').exists())
        self.assertFalse((self.root/'shutdown-calls').exists())

    def test_critical_temperature_covers_idle_stopped_partial_and_pool_disks(self):
        for state in ['idle','stopped','partial','pool']:
            with self.subTest(state=state):
                self.active()
                self.disk(60)
                self.configure({'parityTuningPlusHeatShutdown':'1','parityTuningPlusShutdown':'0'})
                var=self.root/'var/local/emhttp/var.ini'
                if state=='idle':var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="0"'))
                if state=='stopped':var.write_text(var.read_text().replace('mdState="STARTED"','mdState="STOPPED"'))
                if state=='partial':(self.config/f'{PLUGIN}.partial').write_text('{"startSector":0,"endSector":2000,"correct":false}')
                else:(self.config/f'{PLUGIN}.partial').unlink(missing_ok=True)
                if state=='pool':
                    disks=self.root/'var/local/emhttp/disks.ini'
                    disks.write_text(disks.read_text().replace('[parity]','[cache]').replace('name="parity"','name="cache"'))
                (self.root/'shutdown-calls').unlink(missing_ok=True)
                self.host.command('monitor')
                self.assertTrue((self.root/'shutdown-calls').exists(),state)

    def test_temperature_pause_inherits_negative_per_disk_limit(self):
        self.active()
        self.disk(40)
        path=self.root/'var/local/emhttp/disks.ini'
        path.write_text(path.read_text().replace('hotTemp="45"','hotTemp="-1"'))
        self.configure({'parityTuningPlusHeat':'1'})
        self.host.command('monitor')
        self.assertFalse((self.root/'mdcmd-calls').exists())

    def test_marker_timestamp_records_creation_time(self):
        path=json.dumps(str(self.config/'audit-marker'))
        result=self.host.helper('(function(){createMarkerFile('+path+');return [file_get_contents('+path+'),date(PARITY_TUNING_PLUS_DATE_FORMAT)];})()')
        self.assertEqual(result[0],result[1])

    def test_shutdown_rechecks_saved_policy_before_power_command(self):
        self.active()
        self.disk(60)
        self.configure({'parityTuningPlusHeatShutdown':'1'})
        text=self.main.read_text().replace('usleep(1);', 'file_put_contents(PARITY_TUNING_PLUS_CFG_FILE, "parityTuningPlusHeatShutdown=0\\n");')
        self.main.write_text(text)
        self.host.command('monitor')
        self.assertFalse((self.root/'shutdown-calls').exists())

    def test_declared_unraid_feature_version_boundaries(self):
        for version,expected in [('6.10.2',[False,False]),('6.10.3',[True,False]),('6.11.0',[True,True]),('7.2.0',[True,True])]:
            with self.subTest(version=version):
                self.host.write(self.root/'etc/unraid-version',f'version="{version}"\n')
                self.assertEqual(self.host.helper('[$parityTuningPlusStartStop,$parityTuningPlusSizeInHistory]'),expected)

    def test_restart_detects_removed_disk_assignments(self):
        self.disk(30)
        current=(self.root/'var/local/emhttp/disks.ini').read_text()
        snapshot=self.config/f'{PLUGIN}.disks'
        code='(function(){define("PARITY_TUNING_PLUS_DISKS_FILE",'+json.dumps(str(snapshot))+');require '+json.dumps(str(ROOT/'scripts/php_functions.php'))+';eval(pctFixtureFunctions('+json.dumps(str(self.main))+',["disksChanged"]));return disksChanged();})()'
        extra='[disk1]\nname="disk1"\nstatus="DISK_OK"\nsize="1000"\nid="removed-disk"\n'
        for old,now,expected in [(current,current,0),(current+extra,current,1),(current,current+extra,1),(current,current.replace('fixture-disk','replacement'),1),(current,current+'[cache]\nname="cache"\n',0),(current,'',1)]:
            with self.subTest(expected=expected,now=now):
                snapshot.write_text(old)
                (self.root/'var/local/emhttp/disks.ini').write_text(now)
                self.assertEqual(self.host.helper(code),expected)

    def test_custom_increment_window_survives_idle_and_only_schedule_changes_clear_it(self):
        self.active()
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="0"'))
        self.configure({'parityTuningPlusFrequency':'1'})
        self.host.command('config')
        self.host.command('resume')
        marker=self.config/f'{PLUGIN}.increment'
        self.assertTrue(marker.exists())
        self.configure({'parityTuningPlusMonitorDefault':'23'})
        self.host.command('config')
        self.assertTrue(marker.exists())
        self.configure({'parityTuningPlusPauseCustom':'1 1 * * *'})
        self.host.command('config')
        self.assertFalse(marker.exists())

    def test_mdcmd_observer_reads_post_command_state_and_preserves_arguments(self):
        wrapper=self.root/'wrapper'
        kernel=self.root/'proc/mdcmd';kernel.parent.mkdir()
        wrapper.write_text((self.host.plugin/f'{PLUGIN}.mdcmd').read_text().replace('/proc/mdcmd',str(kernel)))
        self.host.write(self.root/'bin/ps','#!/bin/sh\ncase "$*" in *%c*) echo "   crond  ";; *) echo "   123  ";; esac\n')
        (self.root/'bin/ps').chmod(0o755)
        self.host.write(self.root/'bin/php','''#!/usr/bin/python3
import os,sys,json
from pathlib import Path
r=Path(os.environ['PCT_PLUS_FIXTURE'])
(r/'observer').write_text(json.dumps({'arguments':sys.argv[1:],'state':(r/'proc/mdcmd').read_text() if (r/'proc/mdcmd').exists() else ''}))
''')
        (self.root/'bin/php').chmod(0o755)
        env=dict(os.environ,PCT_PLUS_FIXTURE=str(self.root),PATH=str(self.root/'bin')+os.pathsep+os.environ['PATH'])
        args=['check','nocorrect','literal name','*']
        result=subprocess.run(['bash',str(wrapper),*args],env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        observed=json.loads((self.root/'observer').read_text())
        self.assertEqual(observed['state'],' '.join(args)+'\n')
        self.assertEqual(observed['arguments'][-4:],args)
        self.assertEqual(observed['arguments'][3],'crond')

    def prepare_restart(self, position='100'):
        self.disk(30)
        self.host.write(self.root/'boot/config/parity-checks.log','2026 Nov 03 10:00:00|3600|1000000|-4|0|check P|1000\n')
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdState="STOPPED"','mdState="STARTED"'))
        self.configure({'parityTuningPlusRestart':'1'})
        (self.config/f'{PLUGIN}.disks').write_text((self.root/'var/local/emhttp/disks.ini').read_text())
        (self.config/f'{PLUGIN}.tidy').write_text('tidy')
        (self.config/f'{PLUGIN}.restart').write_text(f'mdResync="0"\nmdResyncPos="{position}"\nmdResyncSize="1000"\nmdResyncAction="check P"\nmdResyncCorr="0"\ntriggerType="SCHEDULED"\n')
        header='type|date|time|sbSynced|sbSynced2|sbSyncErrs|sbSyncExit|mdState|mdResync|mdResyncPos|mdResyncSize|mdResyncCorr|mdResyncAction|Description\n'
        (self.config/f'{PLUGIN}.progress').write_text(header+'SCHEDULED|2026 Nov 03 10:00:00|1793700000|1793700000|0|0|0|STARTED|1|100|1000|0|check P|Scheduled Non-Correcting Parity-Check|\n')

    def test_invalid_saved_restart_position_is_rejected_without_native_command(self):
        self.prepare_restart('not-a-position')
        self.host.command('started')
        self.assertFalse((self.root/'mdcmd-calls').exists())
        self.assertFalse((self.config/f'{PLUGIN}.restart').exists())

    def test_disabling_restart_policy_prevents_pending_restart(self):
        self.prepare_restart()
        self.configure({'parityTuningPlusRestart':'0'})
        self.host.command('started')
        self.assertFalse((self.root/'mdcmd-calls').exists())

    def test_history_cancel_cleanup_handles_missing_and_retains_other_runs(self):
        path=self.root/'boot/config/parity-checks.log'
        code='(function(){define("UNRAID_PARITY_HISTORY_FILE",'+json.dumps(str(path))+');define("PARITY_TUNING_PLUS_HISTORY_FILE",'+json.dumps(str(self.config/'history'))+');require '+json.dumps(str(ROOT/'scripts/php_functions.php'))+';eval(pctFixtureFunctions('+json.dumps(str(self.main))+',["removeHistoryCancelEntry"]));removeHistoryCancelEntry(1793700000,null,"check P");return file_exists(UNRAID_PARITY_HISTORY_FILE)?file_get_contents(UNRAID_PARITY_HISTORY_FILE):null;})()'
        self.assertIsNone(self.host.helper(code))
        old='2026 Nov 01 10:00:00|3600|1|-4|0|check P|1000\n'
        path.write_text(old)
        self.assertEqual(self.host.helper(code),old)
        matching='2026 Nov 03 11:00:00|3600|1|-4|0|check P|1000\n'
        path.write_text(old+matching)
        self.assertEqual(self.host.helper(code),old)
        successful=matching.replace('|-4|','|0|')
        path.write_text(successful)
        self.assertEqual(self.host.helper(code),successful)

    def test_restart_wait_is_bounded_and_failed_start_is_not_reported_successful(self):
        self.prepare_restart()
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdResyncPos="0"','mdResyncPos="100"'))
        env=dict(os.environ,PCT_PLUS_FIXTURE=str(self.root),PATH=str(self.root/'bin')+os.pathsep+os.environ['PATH'])
        result=subprocess.run(['php','-d','short_open_tag=1',str(self.host.cli),'started'],env=env,text=True,capture_output=True,timeout=3)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.root/'mdcmd-calls').read_text(),'nocheck\n')

    def test_failed_restart_start_does_not_announce_restart(self):
        self.prepare_restart()
        self.host.command('started')
        log=(self.config/f'{PLUGIN}.log').read_text()
        self.assertNotIn('Send notification: Array operation restarted',log)

    def test_scheduled_native_callback_keeps_explicit_trigger(self):
        self.active()
        env=dict(os.environ,PCT_PLUS_FIXTURE=str(self.root),PATH=str(self.root/'bin')+os.pathsep+os.environ['PATH'])
        result=subprocess.run(['php','-d','short_open_tag=1',str(self.host.cli),'mdcmd','crond','check','nocorrect'],env=env,text=True,capture_output=True,timeout=5)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout+result.stderr)
        self.assertTrue((self.config/f'{PLUGIN}.scheduled').exists())
        self.assertFalse((self.config/f'{PLUGIN}.manual').exists())

    def test_successful_restart_restores_saved_trigger(self):
        self.prepare_restart()
        self.configure({'parityTuningPlusScheduled':'0'})
        state=self.config/f'{PLUGIN}.restart'
        state.write_text(state.read_text().replace('mdResync="0"','mdResync="1"'))
        self.host.write(self.root/'usr/local/sbin/mdcmd','''#!/usr/bin/python3
from pathlib import Path
import os,sys
r=Path(os.environ['PCT_PLUS_FIXTURE'])
with (r/'mdcmd-calls').open('a') as f:f.write(' '.join(sys.argv[1:])+'\\n')
if sys.argv[1]=='check':
 p=r/'var/local/emhttp/var.ini'
 p.write_text(p.read_text().replace('mdResyncPos="0"','mdResyncPos="100"').replace('mdResync="0"','mdResync="1"').replace('mdResyncAction="check"','mdResyncAction="check P"'))
''')
        (self.root/'usr/local/sbin/mdcmd').chmod(0o755)
        self.host.command('started')
        self.assertEqual((self.root/'mdcmd-calls').read_text(),'check nocorrect 200\n')
        self.assertIn('Scheduled Non-Correcting Parity-Check',(self.config/f'{PLUGIN}.log').read_text())

    def test_cli_check_honors_native_correction_setting(self):
        self.active()
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="0"'))
        cfg=self.root/'boot/config/plugins/dynamix/dynamix.cfg'
        base=cfg.read_text()
        for setting,expected in [('NOCORRECT','check nocorrect\n'),('','check correct\n')]:
            with self.subTest(setting=setting):
                cfg.write_text(base+f'write="{setting}"\n')
                (self.root/'mdcmd-calls').unlink(missing_ok=True)
                self.host.command('check')
                self.assertEqual((self.root/'mdcmd-calls').read_text(),expected)

    def test_failed_background_pause_does_not_claim_ownership_or_send_paused(self):
        self.active()
        self.disk(30)
        self.configure({'parityTuningPlusMover':'0','parityTuningPlusBackup':'1','parityTuningPlusBackground':'1'})
        self.host.write(self.root/'tmp/appdata.backup/running','running')
        self.host.command('monitor')
        state=json.loads((self.config/f'{PLUGIN}.backup').read_text())
        self.assertFalse(state['paused'])
        self.assertNotIn('Send notification: Paused:',(self.config/f'{PLUGIN}.log').read_text())

    def test_failed_background_resume_retains_ownership_and_retries(self):
        self.active(running=False)
        self.disk(30)
        self.configure({'parityTuningPlusMover':'0','parityTuningPlusBackup':'1','parityTuningPlusBackground':'1'})
        marker=self.config/f'{PLUGIN}.backup'
        marker.write_text('{"paused":true,"notified":true}')
        self.host.command('monitor')
        self.assertTrue(marker.exists())
        self.assertTrue(json.loads(marker.read_text())['paused'])
        self.host.command('monitor')
        self.assertEqual((self.root/'mdcmd-calls').read_text().count('check resume'),2)
        self.assertNotIn('Send notification: Resumed:',(self.config/f'{PLUGIN}.log').read_text())

    def test_failed_temperature_pause_does_not_claim_hot_pause(self):
        self.active()
        self.disk(50)
        self.configure({'parityTuningPlusHeat':'1'})
        self.host.command('monitor')
        self.assertFalse((self.config/f'{PLUGIN}.hot').exists())

    def test_failed_temperature_resume_keeps_hot_marker_for_retry(self):
        self.active(running=False)
        self.disk(30)
        self.configure({'parityTuningPlusHeat':'1'})
        marker=self.config/f'{PLUGIN}.hot';marker.write_text('parity')
        self.host.command('monitor')
        self.assertTrue(marker.exists())

    def test_syslog_popup_has_one_valid_language_attribute(self):
        helpers=self.root/'usr/local/emhttp/webGui/include/Helpers.php'
        with helpers.open('a') as file:file.write('\nfunction autov($path){echo $path;}\n')
        env=dict(os.environ,PCT_PLUS_FIXTURE=str(self.root))
        result=subprocess.run(['php','-d','short_open_tag=1',str(self.host.plugin/f'{PLUGIN}.entries.php')],env=env,text=True,capture_output=True)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout+result.stderr)
        self.assertEqual(result.stdout.count('lang='),1)

    def test_missing_host_state_is_safe_and_reload_updates_description(self):
        var=self.root/'var/local/emhttp/var.ini'
        original=var.read_text();var.unlink()
        self.assertIn('Array not yet started',self.host.command('status'))
        var.write_text(original)
        updated=original.replace('mdState="STOPPED"','mdState="STARTED"').replace('mdResyncPos="0"','mdResyncPos="100"').replace('mdResyncAction="check"','mdResyncAction="check P"')
        code='(function(){file_put_contents(PARITY_TUNING_PLUS_EMHTTP_VAR_FILE,'+json.dumps(updated)+');loadVars();global $parityTuningPlusDescription;return $parityTuningPlusDescription;})()'
        self.assertIn('Parity-Check',self.host.helper(code))

    def test_cli_check_requires_started_array_and_observed_start(self):
        self.host.command('nocorrect')
        self.assertFalse((self.root/'mdcmd-calls').exists())
        self.active()
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="0"'))
        output=self.host.command('nocorrect')
        self.assertNotIn(' started\n',output)

    def test_failed_cancel_does_not_claim_cancellation(self):
        self.active()
        output=self.host.command('cancel')
        self.assertNotIn(' Cancelled\n',output)
        progress=self.config/f'{PLUGIN}.progress'
        self.assertTrue(not progress.exists() or 'CANCELLED|' not in progress.read_text())

    def test_invalid_cron_configuration_preserves_last_valid_jobs(self):
        self.configure({'parityTuningPlusFrequency':'1'})
        self.host.command('config')
        cron=self.config/f'{PLUGIN}.cron';good=cron.read_bytes()
        for key,value in [('parityTuningPlusResumeCustom','* * * * *\n* * * * * echo injected'),('parityTuningPlusResumeCustom','60 * * * *'),('parityTuningPlusResumeCustom','*/0 * * * *'),('parityTuningPlusMonitorDefault','0')]:
            with self.subTest(value=value):
                self.configure({'parityTuningPlusResumeCustom':'5,15,25,35,45,55 * * * *','parityTuningPlusMonitorDefault':'17'})
                self.configure({key:value})
                self.host.command('updatecron')
                self.assertEqual(cron.read_bytes(),good)

    def render(self, page):
        helpers=self.root/'usr/local/emhttp/webGui/include/Helpers.php'
        with helpers.open('a' if not getattr(self,'render_helpers_added',False) else 'r') as file:
            if getattr(self,'render_helpers_added',False):return self.render_output(page)
            self.render_helpers_added=True
            file.write('''
function _var($a,$k,$d=''){return $a[$k]??$d;}
function my_explode($s,$v,$n){return array_pad(explode($s,trim($v)),$n,'');}
function my_scale($v,&$u,$p){$u='B';return (string)$v;}
function mk_option($s,$v,$l){return '<option>'.htmlspecialchars((string)$l).'</option>';}
function mk_option_check($s,$v,$l){return mk_option($s,$v,$l);}
''')
        helpers.write_text(helpers.read_text().replace("$root = getenv('PCT_PLUS_FIXTURE');", "$root = getenv('PCT_PLUS_FIXTURE');if($plugin==='dynamix')return ['display'=>['locale'=>'en_US']];"))
        return self.render_output(page)

    def render_output(self, page):
        text=(self.host.plugin/page).read_text()
        if '---\n' in text:text=text.split('---\n',1)[1]
        target=self.root/'render.php';target.write_text('<?php $path="Main";$docroot='+json.dumps(str(self.root/'usr/local/emhttp'))+';?>'+text)
        result=subprocess.run(['php','-d','short_open_tag=1',str(target)],text=True,capture_output=True,env=dict(os.environ,PCT_PLUS_FIXTURE=str(self.root)))
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout+result.stderr)
        return result.stdout

    def test_settings_and_assistant_escape_saved_attributes(self):
        self.configure({'parityTuningPlusResumeCustom':'x\" autofocus data-injected=\"yes', 'parityProblemPlusStartSector':'x\" autofocus data-injected=\"yes'})
        for page in ['Parity.check.tuning.plus.page','Parity.check.tuning.plus.problems.page']:
            with self.subTest(page=page):
                html=self.render(page)
                self.assertNotIn('autofocus data-injected="yes',html)
                self.assertIn('x&quot; autofocus data-injected=&quot;yes',html)

    def test_history_skips_malformed_arithmetic_and_escapes_text(self):
        self.host.write(self.root/'boot/config/parity-checks.log','2026 Nov 03 10:00:00|3600|<script>bad()</script>|<b>status</b>|<img src=x>|check P|1000\n2026 Nov 03 11:00:00|bad|1000000|0|0|check P|1000\n')
        html=self.render(f'{PLUGIN}.history.php')
        self.assertNotIn('<script>bad()',html)
        self.assertNotIn('<img src=x>',html)
        self.assertIn('&lt;script&gt;',html)

    def test_failed_partial_start_leaves_no_owner_or_started_notice(self):
        self.active()
        var=self.root/'var/local/emhttp/var.ini';var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="0"'))
        self.configure({'parityProblemPlusType':'percent','parityProblemPlusStartPercent':'10','parityProblemPlusEndPercent':'20'})
        self.host.command('partial')
        self.assertFalse((self.config/f'{PLUGIN}.partial').exists())
        self.assertNotIn('Send notification: Partial parity check',(self.config/f'{PLUGIN}.log').read_text())

    def test_stale_partial_marker_never_cancels_another_operation(self):
        self.active()
        marker=self.config/f'{PLUGIN}.partial'
        marker.write_text('{"startSector":0,"endSector":100,"correct":false,"kernelStart":1,"size":1000}')
        self.host.command('monitor')
        self.assertFalse((self.root/'mdcmd-calls').exists())
        self.assertFalse(marker.exists())

    def test_partial_success_uses_snapshot_and_failed_stop_retries(self):
        self.active()
        var=self.root/'var/local/emhttp/var.ini';var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="0"'))
        self.configure({'parityProblemPlusType':'percent','parityProblemPlusStartPercent':'10','parityProblemPlusEndPercent':'20'})
        self.host.simulate_kernel()
        self.host.command('partial')
        marker=self.config/f'{PLUGIN}.partial'
        self.assertEqual(json.loads(marker.read_text())['endSector'],400)
        self.configure({'parityProblemPlusEndSector':'1','parityProblemPlusEndPercent':'1'})
        var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="210"'))
        native=self.root/'usr/local/sbin/mdcmd';accepted=native.read_text()
        native.write_text('#!/bin/sh\nexit 1\n')
        self.host.command('monitor');self.assertTrue(marker.exists())
        native.write_text(accepted)
        self.host.command('monitor');self.assertFalse(marker.exists())
        log=(self.config/f'{PLUGIN}.log').read_text()
        self.assertIn('Sectors 200-400',log)
        self.assertIn('Completed partial check',log)

    def test_confirmed_pause_resume_full_start_and_cancel(self):
        self.active();self.disk(30);self.host.simulate_kernel()
        with (self.root/'usr/local/emhttp/webGui/include/Helpers.php').open('a') as file:file.write('\nfunction my_scale($v,&$u,$p){$u="B";return (string)$v;}\n')
        self.host.command('pause')
        self.assertIn('mdResync="0"',(self.root/'var/local/emhttp/var.ini').read_text())
        self.host.command('resume')
        self.assertIn('mdResync="1"',(self.root/'var/local/emhttp/var.ini').read_text())
        cancelled=self.host.command('cancel')
        self.assertIn('Parity-Check Cancelled',cancelled)
        self.assertIn('mdResyncPos="0"',(self.root/'var/local/emhttp/var.ini').read_text())
        output=self.host.command('nocorrect')
        self.assertIn('started',output)

    def test_malformed_heat_offsets_do_not_crash_monitor(self):
        self.active();self.disk(30)
        self.configure({'parityTuningPlusHeat':'1','parityTuningPlusHeatHigh':'bad','parityTuningPlusHeatLow':'NaN','parityTuningPlusHeatCritical':'-100'})
        self.host.command('monitor')
        self.assertFalse((self.root/'mdcmd-calls').exists())

    def test_kernel_integer_overflow_cannot_create_active_state(self):
        self.active()
        var=self.root/'var/local/emhttp/var.ini';var.write_text(var.read_text().replace('mdResyncPos="100"','mdResyncPos="9999999999999999999"'))
        self.assertEqual(self.host.helper('(bool)$parityTuningPlusStateValid'),False)

    def test_progress_writer_compares_transition_identity_not_prefix(self):
        self.active(running=False);self.disk(30)
        code='(function(){define("PARITY_TUNING_PLUS_PROGRESS_FILE",'+json.dumps(str(self.config/f'{PLUGIN}.progress'))+');define("PARITY_TUNING_PLUS_DISKS_FILE",'+json.dumps(str(self.config/f'{PLUGIN}.disks'))+');require '+json.dumps(str(ROOT/'scripts/php_functions.php'))+';eval(pctFixtureFunctions('+json.dumps(str(self.main))+',["parityTuningPlusProgressWrite"]));return [parityTuningPlusProgressWrite("PAUSE (HOT)"),parityTuningPlusProgressWrite("PAUSE"),parityTuningPlusProgressWrite("PAUSE (MANUAL)")];})()'
        self.assertEqual(self.host.helper(code),[1,0,0])


    def test_unclean_start_does_not_reclassify_rebuild_as_automatic_check(self):
        self.active();self.disk(30)
        var=self.root/'var/local/emhttp/var.ini';var.write_text(var.read_text().replace('check P','recon disk1'))
        self.host.command('started')
        self.assertFalse((self.config/f'{PLUGIN}.automatic').exists())


    def test_temperature_inheritance_and_disabled_limit_boundaries(self):
        module=json.dumps(str(self.host.plugin/f'{PLUGIN}.temperature.php'))
        code='(function(){require '+module+''';function get_nvme_info($device,$field){return [70,80];}
        $base=['hotTemp'=>'-1','maxTemp'=>'-1','rotational'=>'1'];
        return [pctDiskTemperatureLimit($base,[],'hotTemp'),
                pctDiskTemperatureLimit(array_replace($base,['hotTemp'=>'0']),[],'hotTemp'),
                pctDiskTemperatureLimit(array_replace($base,['rotational'=>'0']),['hotssd'=>60],'hotTemp'),
                pctDiskTemperatureLimit(array_replace($base,['transport'=>'nvme']),[],'maxTemp'),
                pctCriticalTemperatureDrives(['disk1'=>array_replace($base,['temp'=>53,'status'=>'DISK_OK'])],[],2),
                pctCriticalTemperatureDrives(['disk1'=>array_replace($base,['temp'=>53,'maxTemp'=>0])],[],2)];})()'''
        self.assertEqual(self.host.helper(code),[45,0,60,80,{'disk1':53},[]])

    def test_history_formats_five_through_ten_fields_are_renderable(self):
        rows=[]
        prefix='2026 Nov 03 10:00:00|3600|1000000|0|0'
        for suffix in ['', '|check P','|check P|1000','|7200|2|Scheduled Correcting Parity-Check','|check P|7200|2|Scheduled Correcting Parity-Check','|check P|1000|7200|2|Scheduled Correcting Parity-Check']:
            rows.append(prefix+suffix)
        self.host.write(self.root/'boot/config/parity-checks.log','\n'.join(rows)+'\n')
        html=self.render(f'{PLUGIN}.history.php')
        self.assertEqual(html.count('<td>&nbsp;OK</td>'),6)

    def native_callback(self, *arguments):
        result=subprocess.run(['php','-d','short_open_tag=1',str(self.main),'mdcmd','crond',*arguments],env=dict(os.environ,PCT_PLUS_FIXTURE=str(self.root)),text=True,capture_output=True)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout+result.stderr)

    def test_native_bare_check_callback_needs_no_optional_argument(self):
        self.active()
        self.native_callback('check')
        self.assertTrue((self.config/f'{PLUGIN}.scheduled').exists())

    def test_failed_native_cancel_and_pause_preserve_active_owner(self):
        self.active();self.disk(30)
        marker=self.config/f'{PLUGIN}.hot';marker.write_text('parity')
        self.native_callback('nocheck','PAUSE')
        progress=self.config/f'{PLUGIN}.progress'
        self.assertFalse(progress.exists())
        self.native_callback('nocheck')
        self.assertTrue(marker.exists())
        self.assertFalse(progress.exists())
        var=self.root/'var/local/emhttp/var.ini';var.write_text(var.read_text().replace('mdResync="1"','mdResync="0"'))
        self.native_callback('check','resume')
        self.assertFalse(progress.exists())

    def test_conflicting_trigger_diagnostic_uses_the_action_value(self):
        self.active()
        for suffix in ['scheduled','automatic']:
            (self.config/f'{PLUGIN}.{suffix}').write_text('fixture')
        self.assertEqual(self.host.helper('operationTriggerType()'), 'AUTOMATIC')
        self.assertIn('scheduled and automatic check P', (self.config/f'{PLUGIN}.log').read_text())

    def test_unknown_trigger_diagnostic_does_not_read_an_undefined_variable(self):
        code='(function(){require '+json.dumps(str(ROOT/'scripts/php_functions.php'))+';eval(pctFixtureFunctions('+json.dumps(str(self.main))+',["configuredAction"]));return configuredAction();})()'
        self.assertFalse(self.host.helper(code))
