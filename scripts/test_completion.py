"""Completion/history and actual native-monitor notification regressions."""
import calendar
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import unittest

import test_runtime
from build_package import ROOT, PLUGIN


@unittest.skipUnless(os.name == 'posix' and shutil.which('php'), 'Requires Linux/WSL PHP')
class Completion(unittest.TestCase):
    def setUp(self):
        self.host = test_runtime.Runtime('test_cli_name_catalog_and_log_brand')
        self.host.setUp()
        self.addCleanup(self.host.doCleanups)
        self.root = self.host.root
        self.config = self.host.config
        self.begin = calendar.timegm(datetime.datetime(2026, 11, 3, 10).timetuple())
        self.finish = self.begin + 3600
        self.history = self.root/'boot/config/parity-checks.log'
        self.progress = self.config/f'{PLUGIN}.progress'
        self.receipt = self.config/f'{PLUGIN}.completion.json'
        self.calls = self.root/'notify-calls'
        self.notify = self.root/'usr/local/emhttp/webGui/scripts/notify'
        self.wrapper = self.host.plugin/f'{PLUGIN}.notify.php'
        self.wrapper.chmod(0o755)
        self.env = dict(os.environ, PCT_PLUS_FIXTURE=str(self.root), PATH=str(self.root/'bin')+os.pathsep+os.environ['PATH'])
        with (self.root/'usr/local/emhttp/webGui/include/Helpers.php').open('a') as file:
            file.write("\nfunction my_scale($value,&$unit,$precision){$unit='B';return (string)$value;}\n")
        with (self.root/'boot/config/plugins/dynamix/dynamix.cfg').open('a') as file:
            file.write('\n[notify]\nsystem="1"\n')
        self.host.write(self.notify.with_name(self.notify.name+f'.{PLUGIN}.orig'), '''#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
root=Path(os.environ['PCT_PLUS_FIXTURE'])
history=root/'boot/config/parity-checks.log'
with (root/'notify-calls').open('a') as out:
    out.write(json.dumps({'argv':sys.argv[1:],'history':history.read_text() if history.exists() else ''})+'\\n')
if 'Parity Check Tuning Plus' in sys.argv and (root/'hold-plus').exists():
    (root/'plus-entered').touch()
    until=time.monotonic()+8
    while not (root/'release-plus').exists() and time.monotonic()<until:time.sleep(.01)
if (root/'native-exit').exists():
    print('native stdout')
    print('native stderr',file=sys.stderr)
    sys.exit(int((root/'native-exit').read_text()))
''')
        self.notify.with_name(self.notify.name+f'.{PLUGIN}.orig').chmod(0o755)
        self.notify.symlink_to(self.wrapper)

    def stamp(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).strftime('%Y %b %d %H:%M:%S')

    def prepare(self, status=0, old_status=-4, errors=0, old_errors=0, paused=False):
        header='type|date|time|sbSynced|sbSynced2|sbSyncErrs|sbSyncExit|mdState|mdResync|mdResyncPos|mdResyncSize|mdResyncCorr|mdResyncAction|Description\n'
        records=[('SCHEDULED',self.begin,self.begin,0,0,1),('STARTED',self.begin,self.begin,0,0,1)]
        if paused:
            records += [('PAUSE',self.begin+900,self.begin,self.begin+900,-4,300),
                        ('RESUME',self.begin+1800,self.begin+1800,0,0,300)]
        kernel_start=self.begin+1800 if paused else self.begin
        records.append(('CANCELLED' if status == -4 else 'COMPLETED',self.finish,kernel_start,self.finish,status,0))
        rows=[f'{kind}|{self.stamp(t)}|{t}|{start}|{end}|{errors}|{exit_code}|STARTED|0|{pos}|1000|1|check P|Scheduled Correcting Parity-Check|\n'
              for kind,t,start,end,exit_code,pos in records]
        self.progress.write_text(header+''.join(rows))
        self.history.write_text(f'{self.stamp(self.finish)}|3600|1000000|{old_status}|{old_errors}|check P|1000\n')
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(f'NAME="FIXTURE"\nmdState="STARTED"\nmdResyncPos="0"\nmdResyncSize="1000"\nmdResyncAction="check P"\nmdResync="0"\nmdResyncCorr="1"\nsbSyncErrs="{errors}"\nsbSynced="{kernel_start}"\nsbSynced2="{self.finish}"\nsbSyncExit="{status}"\n')
        self.host.write(self.root/'var/local/emhttp/monitor.ini','[array]\nparity="Parity-Check"\n[smart]\nkeep="1"\n')

    def messages(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def option(self, message, key):
        args=message['argv']
        return args[args.index(key)+1]

    def analyze(self):
        return self.host.command('analyze')

    def native_monitor(self):
        # Run the verbatim native parity section with an already-loaded cancellation snapshot.
        native=(ROOT/'tests/fixtures/unraid/monitor').read_text()
        native=native.split('/* Process parity check, parity sync, and data-rebuild notifications */',1)[1].split('// check read-write status of Boot drive',1)[0]
        native=native.replace("'/var/tmp/resync.ini'",json.dumps(str(self.root/'var/tmp/resync.ini')))
        code='$item="array";$saved=["array"=>["parity"=>"Parity-Check"]];$var=["mdResyncPos"=>0,"sbSyncErrs"=>0];$server="FIXTURE";$notify='+json.dumps(str(self.notify))+';'
        code+='function last_parity_log(){return explode("|",trim(file_get_contents('+json.dumps(str(self.history))+')));}'
        code+='function last_parity_check(){return [3600,0,-4,0,"check P",1000];}'
        code+='function my_check($duration,$speed){return "$duration seconds";}'
        return ['php','-r',code+native]

    def run_native(self):
        result=subprocess.run(self.native_monitor(),capture_output=True,text=True,env=self.env,timeout=10)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout+result.stderr)

    def test_success_overrides_stale_cancel_and_persists_before_notification(self):
        self.prepare()
        self.analyze()
        message=self.messages()[0]
        self.assertIn('finished (0 errors)',self.option(message,'-s'))
        self.assertEqual(message['history'].split('|')[3],'0')
        self.assertEqual(self.history.read_text().split('|')[3],'0')
        self.assertTrue(self.receipt.exists())
        self.assertIn('keep="1"',(self.root/'var/local/emhttp/monitor.ini').read_text())
        self.assertIn('parity="Parity-Check"',(self.root/'var/local/emhttp/monitor.ini').read_text(), 'Native monitor retains ownership of its state')

    def test_native_snapshot_overlap_cannot_emit_false_cancel_after_success(self):
        self.prepare()
        (self.root/'var/tmp').mkdir(parents=True)
        (self.root/'var/tmp/resync.ini').write_text('check P,1000')
        # Hold delivery inside the real analyzer, after history/receipt commit, while it owns the lock.
        (self.root/'hold-plus').touch()
        analyzer=subprocess.Popen(['php','-d','short_open_tag=1',str(self.host.cli),'analyze'],env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        monitor=None
        try:
            until=time.monotonic()+5
            while not (self.root/'plus-entered').exists() and time.monotonic()<until:time.sleep(.01)
            self.assertTrue((self.root/'plus-entered').exists())
            monitor=subprocess.Popen(self.native_monitor(),env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            time.sleep(.15)
            self.assertIsNone(monitor.poll(),'Native finish waits for completion lock')
            (self.root/'release-plus').touch()
            for process in [analyzer,monitor]:
                out,err=process.communicate(timeout=10)
                self.assertEqual((process.returncode,err),(0,''),out+err)
            self.assertEqual(len(self.messages()),1)
            self.assertIn('finished (0 errors)',self.option(self.messages()[0],'-s'))
        finally:
            (self.root/'release-plus').touch()
            for process in [analyzer,monitor]:
                if process and process.poll() is None:process.kill();process.communicate()

    def test_actual_cancellation_remains_cancelled_with_alert(self):
        self.prepare(status=-4,old_status=0)
        self.analyze()
        self.assertEqual(self.history.read_text().split('|')[3],'-4')
        message=self.messages()[0]
        self.assertIn('canceled',self.option(message,'-s'))
        self.assertEqual(self.option(message,'-i'),'alert')
        self.run_native()
        self.assertEqual(len(self.messages()),1,'Real cancellation is reported once by Plus')

    def test_nonzero_error_code_is_not_changed_to_success(self):
        self.prepare(status=-7,old_status=0)
        self.analyze()
        self.assertEqual(self.history.read_text().split('|')[3],'-7')
        self.assertIn('exit code: -7',self.option(self.messages()[0],'-s'))
        self.assertEqual(self.option(self.messages()[0],'-i'),'alert')

    def test_native_error_count_is_merged_before_summary(self):
        self.prepare(old_errors=7)
        self.analyze()
        self.assertIn('finished (7 errors)',self.option(self.messages()[0],'-s'))
        self.assertEqual(self.option(self.messages()[0],'-i'),'alert')
        self.assertEqual(self.history.read_text().split('|')[4],'7')

    def test_no_history_creates_a_record_without_losing_unrelated_history(self):
        for existing in [None, self.stamp(self.begin-100)+'|100|1|-4|0|check P|1000\n', self.stamp(self.finish+100)+'|100|1|-4|0|recon P|1000\n']:
            with self.subTest(existing=existing):
                self.prepare()
                if existing is None:self.history.unlink()
                else:self.history.write_text(existing)
                self.analyze()
                text=self.history.read_text()
                if existing:self.assertTrue(text.startswith(existing))
                self.assertEqual(text.splitlines()[-1].split('|')[3],'0')

    def test_pause_resume_completion_has_final_time_status_and_total_duration(self):
        self.prepare(paused=True)
        self.history.write_text(f'{self.stamp(self.begin+900)}|900|1|-4|0|check P|1000\n'+self.history.read_text())
        self.analyze()
        record=self.history.read_text().splitlines()[-1].split('|')
        self.assertEqual(record[3],'0')
        self.assertEqual(record[1],'2700')
        self.assertEqual(record[-3:-1],['3600','2'])
        self.assertEqual(record[0],self.stamp(self.finish).replace(' 03 ','  3 '))

    def test_duplicate_transition_observations_do_not_double_count_runtime(self):
        self.prepare(paused=True)
        lines=self.progress.read_text().splitlines()
        rows=[]
        for line in lines:
            rows.append(line)
            if line.startswith('PAUSE|'):rows.extend([line.replace('PAUSE|','STOPPING|',1),line.replace('PAUSE|','PAUSE (RESTART)|',1)])
            if line.startswith('RESUME|'):rows.append(line.replace('RESUME|','RESUME (MANUAL)|',1))
        self.progress.write_text('\n'.join(rows)+'\n')
        self.analyze()
        record=self.history.read_text().splitlines()[-1].split('|')
        self.assertEqual(record[1],'2700')
        self.assertEqual(record[-3:-1],['3600','2'])

    def test_legacy_progress_annotations_and_history_version_matrix(self):
        # Preserve the original fourteen meaningful columns and temperature annotations.
        # The original writer appends a separator; readers also accept its absence.
        operations = [('check', 0), ('check P', 0), ('check P', 1),
                      ('recon P', 1), ('recon D1', 1), ('clear', 0)]
        for version in ['6.9.2', '6.10.3', '6.11.0', '7.2.0']:
            for action, correcting in operations:
                for trailing_separator in [True, False]:
                    with self.subTest(version=version, action=action,
                                      correcting=correcting, trailing_separator=trailing_separator):
                        case = Completion()
                        case.setUp()
                        try:
                            case.prepare(paused=True)
                            (case.root/'etc/unraid-version').write_text(f'version="{version}"\n')
                            rows = []
                            for row in case.progress.read_text().splitlines():
                                fields = row.rstrip('|').split('|')
                                if fields[0] == 'type':
                                    rows.append('|'.join(fields))
                                    continue
                                fields[11], fields[12] = str(correcting), action
                                row = '|'.join(fields) + ('|' if trailing_separator else '')
                                if fields[0] == 'PAUSE':
                                    rows.append(row.replace('PAUSE|', 'PAUSE (HOT)|', 1))
                                elif fields[0] == 'RESUME':
                                    rows.append(row.replace('RESUME|', 'RESUME (COOL)|', 1))
                                rows.append(row)
                            for row in rows[1:]:
                                self.assertEqual(len(row.split('|')), 15 if trailing_separator else 14)
                                self.assertEqual(row.endswith('|'), trailing_separator)
                            self.assertTrue(any(row.startswith('PAUSE (HOT)|') for row in rows))
                            self.assertTrue(any(row.startswith('RESUME (COOL)|') for row in rows))
                            case.progress.write_text('\n'.join(rows)+'\n')
                            state = case.root/'var/local/emhttp/var.ini'
                            state.write_text(state.read_text()
                                             .replace('mdResyncAction="check P"', f'mdResyncAction="{action}"')
                                             .replace('mdResyncCorr="1"', f'mdResyncCorr="{correcting}"'))
                            history = case.history.read_text().replace('|check P|', '|'+action+'|')
                            legacy_history = version in ['6.9.2', '6.10.3']
                            if legacy_history:
                                history = '|'.join(history.rstrip().split('|')[:6])+'\n'
                            case.history.write_text(history)
                            case.analyze()
                            records = case.history.read_text().splitlines()
                            self.assertEqual(len(records), 1)
                            record = records[0].split('|')
                            self.assertEqual(len(record), 9 if legacy_history else 10)
                            self.assertEqual(record[1], '2700')
                            self.assertEqual(record[3], '0')
                            self.assertEqual(record[5], action)
                            self.assertEqual(record[-3:-1], ['3600', '2'])
                            self.assertEqual(len(case.messages()), 1)
                        finally:
                            case.doCleanups()

    def test_first_correction_policy_survives_cleared_terminal_flag(self):
        self.prepare()
        lines=self.progress.read_text().splitlines();fields=lines[-1].split('|');fields[11]='0'
        self.progress.write_text('\n'.join(lines[:-1]+['|'.join(fields)])+'\n')
        self.analyze()
        self.assertIn('Scheduled Correcting Parity-Check',self.option(self.messages()[0],'-s'))

    def test_corrupt_progress_is_preserved_and_keeps_native_fallback(self):
        self.prepare()
        lines=self.progress.read_text().splitlines();lines.insert(2,'PAUSE|broken|not-a-number')
        original='\n'.join(lines)+'\n';self.progress.write_text(original)
        self.run_native()
        self.assertEqual(len(self.messages()),1,'Invalid progress cannot suppress native notification')
        self.calls.unlink()
        self.analyze()
        self.assertEqual(self.messages(),[])
        self.assertEqual(self.progress.read_text(),original)
        self.assertFalse(self.receipt.exists())

    def test_marker_lost_partial_progress_is_saved_without_a_full_check_summary(self):
        self.prepare()
        self.progress.write_text(self.progress.read_text().replace('SCHEDULED|','PARTIAL|',1))
        original = self.progress.read_text()
        native_history = self.history.read_bytes()
        self.analyze()
        self.assertEqual(self.history.read_bytes(), native_history)
        self.assertEqual(self.messages(), [])
        self.assertFalse(self.progress.exists())
        self.assertEqual((self.config/f'{PLUGIN}.progress.save').read_text(), original)
        self.assertFalse(self.receipt.exists())

    def test_duplicate_analyzers_send_one_summary(self):
        self.prepare()
        processes=[subprocess.Popen(['php','-d','short_open_tag=1',str(self.host.cli),'analyze'],env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        for process in processes:
            out,err=process.communicate(timeout=10)
            self.assertEqual((process.returncode,err),(0,''),out+err)
        self.assertEqual(len(self.messages()),1)

    def test_unowned_and_new_runs_and_invalid_receipts_keep_native_warning(self):
        for mode in ['unowned','new-run','future-receipt','kernel-error','corrupt-receipt']:
            with self.subTest(mode=mode):
                self.prepare()
                self.analyze()
                if mode=='unowned':self.receipt.unlink()
                elif mode=='future-receipt':
                    receipt=json.loads(self.receipt.read_text());receipt['created']+=301;self.receipt.write_text(json.dumps(receipt))
                elif mode=='corrupt-receipt':self.receipt.write_text('{bad json')
                else:
                    var=self.root/'var/local/emhttp/var.ini'
                    var.write_text(var.read_text().replace(f'sbSynced="{self.begin}"',f'sbSynced="{self.begin+1}"') if mode=='new-run' else var.read_text().replace('sbSyncExit="0"','sbSyncExit="-4"'))
                self.history.write_text(f'{self.stamp(self.finish)}|3600|1|-4|0|check P|1000\n')
                self.calls.unlink()
                self.run_native()
                self.assertEqual(self.option(self.messages()[0],'-d'),'Canceled')

    def test_matching_final_kernel_status_resolves_stale_terminal_progress(self):
        for final_status, stale_status in [(-4,0),(0,-4)]:
            with self.subTest(final_status=final_status):
                self.prepare(status=final_status)
                lines=self.progress.read_text().splitlines()
                fields=lines[-1].split('|');fields[6]=str(stale_status)
                self.progress.write_text('\n'.join(lines[:-1]+['|'.join(fields)])+'\n')
                self.analyze()
                self.assertEqual(self.history.read_text().split('|')[3],str(final_status))

    def test_delayed_monitor_still_matches_completed_operation_identity(self):
        self.prepare()
        self.analyze()
        receipt=json.loads(self.receipt.read_text());receipt['created']-=86400;self.receipt.write_text(json.dumps(receipt))
        self.run_native()
        self.assertEqual(len(self.messages()),1,'A delayed monitor cannot revive the same operation warning')

    def test_tracked_pause_suppresses_native_finish_without_receipt(self):
        self.prepare()
        lines=self.progress.read_text().splitlines()
        record=lines[-1].split('|');record[0]='PAUSE';record[6]='-4';record[9]='300'
        self.progress.write_text('\n'.join(lines[:-1]+['|'.join(record)])+'\n')
        var=self.root/'var/local/emhttp/var.ini'
        var.write_text(var.read_text().replace('mdResyncPos="0"','mdResyncPos="300"').replace('sbSyncExit="0"','sbSyncExit="-4"'))
        self.run_native()
        self.assertEqual(self.messages(),[])

    def test_higher_native_error_count_and_aborted_run_are_not_suppressed(self):
        self.prepare()
        self.analyze()
        self.calls.unlink()
        args=['-e','Unraid Parity-Check','-s','Notice [FIXTURE] - Parity-Check finished (5 errors)','-i','warning']
        result=subprocess.run([str(self.notify),*args],env=self.env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0)
        self.assertEqual(self.messages()[0]['argv'],args)
        self.receipt.unlink()
        self.prepare()
        self.progress.write_text(self.progress.read_text().replace('COMPLETED|','ABORTED|'))
        self.calls.unlink()
        self.run_native()
        self.assertEqual(self.option(self.messages()[0],'-d'),'Canceled')

    def test_other_notifications_commands_arguments_and_exit_code_pass_through(self):
        self.prepare()
        self.analyze()
        self.calls.unlink()
        literal='disk warning $(touch '+str(self.root/'must-not-exist')+') ; "quote" 日本語'
        for args in [['get'],['-e','Unraid Disk warning','-s',literal],['-e','Unraid Parity-Check','-s','Notice [FIXTURE] - Parity-Check started'],['-e','Unraid Disk-Clear','-s','Notice [FIXTURE] - Disk-Clear finished (0 errors)']]:
            result=subprocess.run([str(self.notify),*args],env=self.env,capture_output=True,text=True,timeout=10)
            self.assertEqual((result.returncode,result.stderr),(0,''))
            self.assertEqual(self.messages()[-1]['argv'],args)
        self.assertFalse((self.root/'must-not-exist').exists())
        (self.root/'native-exit').write_text('17')
        result=subprocess.run([str(self.notify),'get'],env=self.env,capture_output=True,text=True,timeout=10)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(17,'native stdout\n','native stderr\n'))

    def test_failed_history_write_does_not_claim_completion(self):
        self.prepare()
        self.history.unlink()
        self.history.mkdir()
        # Suppress only the expected filesystem warning in this fault-injection process.
        result=subprocess.run(['php','-d','short_open_tag=1','-d','display_errors=0','-d','log_errors=0',str(self.host.cli),'analyze'],env=self.env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0)
        self.assertFalse(self.receipt.exists())
        self.assertEqual(self.messages(),[])

    def test_failed_plus_delivery_keeps_native_fallback_available(self):
        self.prepare()
        (self.root/'native-exit').write_text('17')
        result=subprocess.run(['php','-d','short_open_tag=1',str(self.host.cli),'analyze'],env=self.env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0)
        self.assertFalse(self.receipt.exists())
        (self.root/'native-exit').unlink()
        self.run_native()
        self.assertEqual(len(self.messages()),2)
        self.assertEqual(self.option(self.messages()[-1],'-e'),'Unraid Parity-Check')
