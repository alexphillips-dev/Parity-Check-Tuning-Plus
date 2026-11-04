#!/usr/bin/env python3
"""Synthetic regressions for the GitHub reports and their connected state flows."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest

from build_package import ROOT, PLUGIN

BASE = ROOT / 'source/usr/local/emhttp/plugins' / PLUGIN


class Regressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pct-plus-regressions-')
        self.addCleanup(self.temp.cleanup)
        self.fixture = Path(self.temp.name)

    def php(self, code, payload=None):
        prelude = '$base=' + json.dumps(BASE.as_posix()) + ';$fixture=' + json.dumps(self.fixture.as_posix()) + ';'
        result = subprocess.run(['php', '-d', 'short_open_tag=1', '-r', prelude + code],
                                input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, '', result.stderr)
        return json.loads(result.stdout)

    def test_mover_pid_and_command_identity(self):
        code = '''require $base.'/parity.check.tuning.plus.background.php';
        $cases=json_decode(stream_get_contents(STDIN),true);$results=[];
        foreach($cases as $case){
            $pidFile=$fixture.'/mover.pid';$proc=$fixture.'/proc';
            @unlink($pidFile);
            if($case['pid']!==null) file_put_contents($pidFile,$case['pid']);
            if($case['command']!==null){
                @mkdir($proc.'/123',0777,true);
                file_put_contents($proc.'/123/cmdline',implode("\\0",$case['command'])."\\0");
            } else @unlink($proc.'/123/cmdline');
            $results[]=isMoverRunning($pidFile,$proc);
        } echo json_encode($results);'''
        cases = [
            (None, None, False), ('', None, False), ('0', None, False), ('-123', None, False),
            ('123;touch /tmp/x', None, False), ('9999999999999999999999999', None, False),
            ('123', None, False), ('123', [], False),
            ('123\n', ['/bin/bash','/usr/local/sbin/mover','start'], True),
            ('123', ['/usr/local/sbin/mover'], True),
            ('123', ['/bin/bash','-x','/plugins/tuning/age_mover','start'], True),
            ('123', ['/bin/sh','/plugins/tuning/share_mover'], True),
            ('123', ['/bin/bash','/usr/local/sbin/mover.old','start'], True),
            ('123', ['/bin/grep','mover'], False),
            ('123', ['/bin/bash','-c','echo mover'], False),
            ('123', ['/bin/bash','-lc','mover'], False),
            ('123', ['/usr/bin/python','-c','print("mover")'], False),
            ('123', ['/bin/bash','/tmp/not_mover','mover'], False),
        ]
        result = self.php(code, [{'pid':p,'command':c} for p,c,_ in cases])
        self.assertEqual(result, [expected for _,_,expected in cases])

    def scenario(self, steps, notify='0', mover='1', backup='1'):
        code = r'''
        require $base.'/parity.check.tuning.plus.i18n.php';
        require $base.'/parity.check.tuning.plus.background.php';
        set_error_handler(function($n,$s){throw new Exception($s);});
        define('PARITY_TUNING_PLUS_HOT_FILE',$fixture.'/hot');
        define('PARITY_TUNING_PLUS_RESTART_FILE',$fixture.'/restart');
        $calls=[];$notices=[];
        function parityTuningPlusDeleteFile($p){if(is_file($p))unlink($p);}
        function parityTuningPlusPartial(){return $GLOBALS['partial'];}
        function isIncrementActive($a){return $GLOBALS['window'];}
        function sendNotification($s){$GLOBALS['notices'][]=$s;}
        function sendNotificationWithCompletion($s){$GLOBALS['notices'][]=$s;}
        function parityTuningPlusPause($s,$notify){$GLOBALS['calls'][]=['pause',$notify];$GLOBALS['parityTuningPlusPaused']=true;}
        function parityTuningPlusResume($notify){$GLOBALS['calls'][]=['resume',$notify];$GLOBALS['parityTuningPlusPaused']=false;}
        $input=json_decode(stream_get_contents(STDIN),true);
        $parityTuningPlusCfg=$input['config'];$parityTuningPlusAction='check P';
        $parityTuningPlusActive=true;$parityTuningPlusPaused=false;
        $results=[];
        foreach($input['steps'] as $step){
            if(isset($step['paused']))$parityTuningPlusPaused=$step['paused'];
            $parityTuningPlusActive=$step['active']??true;
            $window=$step['window']??true;$partial=$step['partial']??false;
            if(!empty($step['hot']))file_put_contents(PARITY_TUNING_PLUS_HOT_FILE,'hot');
            else if(is_file(PARITY_TUNING_PLUS_HOT_FILE))unlink(PARITY_TUNING_PLUS_HOT_FILE);
            if(!empty($step['restart']))file_put_contents(PARITY_TUNING_PLUS_RESTART_FILE,'restart');
            else if(is_file(PARITY_TUNING_PLUS_RESTART_FILE))unlink(PARITY_TUNING_PLUS_RESTART_FILE);
            $results[]=pctHandleBackgroundTasks([
              ['config'=>'parityTuningPlusMover','label'=>'mover','marker'=>$fixture.'/mover','running'=>$step['mover']??false],
              ['config'=>'parityTuningPlusBackup','label'=>'backup','marker'=>$fixture.'/backup','running'=>$step['backup']??false],
            ]);
        }
        echo json_encode(['calls'=>$calls,'notices'=>$notices,'results'=>$results,'paused'=>$parityTuningPlusPaused]);
        '''
        return self.php(code, {'steps':steps,'config':{'parityTuningPlusBackground':notify,
                          'parityTuningPlusMover':mover,'parityTuningPlusBackup':backup}})

    def test_quiet_default_still_pauses_and_resumes(self):
        result = self.scenario([{'mover':True},{'mover':True},{}])
        self.assertEqual(result['calls'], [['pause',False],['resume',False]])
        self.assertEqual(result['notices'], [])

    def test_opt_in_notifies_each_transition_once(self):
        result = self.scenario([{'mover':True},{'mover':True},{}], notify='1')
        self.assertEqual(len(result['notices']), 2)
        self.assertEqual(result['calls'], [['pause',True],['resume',True]])

    def test_manual_pause_is_never_resumed(self):
        result = self.scenario([{'mover':True,'paused':True},{}])
        self.assertEqual(result['calls'], [])
        self.assertTrue(result['paused'])

    def test_overlapping_tasks_transfer_pause_ownership(self):
        result = self.scenario([{'mover':True},{'mover':True,'backup':True},{'backup':True},{}])
        self.assertEqual(result['calls'], [['pause',False],['resume',False]])
        self.assertEqual(result['results'], [True,True,True,False])

    def test_resume_waits_for_window_and_other_pause_reasons(self):
        for condition in ['hot','restart','partial']:
            with self.subTest(condition=condition):
                result = self.scenario([{'mover':True},{condition:True}])
                self.assertEqual(result['calls'], [['pause',False]])
        result = self.scenario([{'mover':True},{'window':False}])
        self.assertEqual(result['calls'], [['pause',False]])

    def test_disabled_task_and_inactive_array_do_not_pause(self):
        self.assertEqual(self.scenario([{'mover':True},{}], mover='0')['calls'], [])
        self.assertEqual(self.scenario([{'mover':True,'active':False},{}])['calls'], [])

    def test_current_hot_disks_transfer_resume_to_temperature_handler(self):
        code=r'''
        require $base.'/parity.check.tuning.plus.background.php';
        define('PARITY_TUNING_PLUS_HOT_FILE',$fixture.'/hot');
        $parityTuningPlusCfg=['parityTuningPlusHeat'=>'1','parityTuningPlusHeatHigh'=>'3'];
        $dynamixCfg=['display'=>['hot'=>45]];
        $disks=['parity'=>['temp'=>44],'disk1'=>['temp'=>30],'cache'=>['temp'=>99]];
        $blocked=pctBackgroundHeatBlock();
        echo json_encode([$blocked,file_get_contents(PARITY_TUNING_PLUS_HOT_FILE)]);
        '''
        self.assertEqual(self.php(code),[True,'parity'])

    def test_real_pause_resume_functions_keep_commands_and_notification_protocol(self):
        harness=(ROOT/'scripts/php_functions.php').as_posix()
        code='namespace PctTest;'+r'''
        $base=BASE;$fixture=FIXTURE;
        require HARNESS;
        define('PARITY_TUNING_PLUS_MOVER_FILE',$fixture.'/mover');
        define('PARITY_TUNING_PLUS_BACKUP_FILE',$fixture.'/backup');
        function pctT($s){return $s;}
        function exec($s,&$output=null,&$status=null){$GLOBALS['commands'][]=$s;$status=0;$GLOBALS['desiredPaused']=strpos($s,'nocheck')!==false;}
        function loadVars($delay){$GLOBALS['parityTuningPlusPaused']=$GLOBALS['desiredPaused'];}
        function parityTuningPlusProgressWrite($type){}
        function parityTuningPlusLoggerTesting($s){}
        function parityTuningPlusDeleteFile($p){}
        function sendArrayNotification($s,$type){$GLOBALS['notifications'][]=$type;}
        function suppressMonitorNotification(){$GLOBALS['suppressed']++;}
        $commands=[];$notifications=[];$suppressed=0;$parityTuningPlusErrors=0;
        $parityTuningPlusActive=true;$parityTuningPlusPaused=false;
        eval('namespace PctTest;'.\pctFixtureFunctions($base.'/parity.check.tuning.plus.php',['parityTuningPlusPause','parityTuningPlusResume']));
        parityTuningPlusPause('mover',false);parityTuningPlusResume(false);
        parityTuningPlusPause('mover',true);parityTuningPlusResume(true);
        echo json_encode([$commands,$notifications,$suppressed]);
        '''
        code=code.replace('BASE',json.dumps(BASE.as_posix())).replace('FIXTURE',json.dumps(self.fixture.as_posix())).replace('HARNESS',json.dumps(harness))
        # Namespace declarations must be the first statement, before the normal test prelude.
        result=subprocess.run(['php','-r',code],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        commands,notifications,suppressed=json.loads(result.stdout)
        self.assertEqual(len(commands),4)
        self.assertIn('"PAUSE"',commands[0])
        self.assertIn('"resume"',commands[1])
        self.assertEqual(notifications,['normal','normal'])
        self.assertEqual(suppressed,4)

    def test_partial_range_rejects_invalid_and_injected_values(self):
        code = '''require $base.'/parity.check.tuning.plus.assistant.php';$results=[];
        foreach(json_decode(stream_get_contents(STDIN),true) as $cfg){
          try{$results[]=pctPartialCheckRange($cfg,1000);}catch(InvalidArgumentException $e){$results[]=false;}
        }echo json_encode($results);'''
        cfg = {'parityProblemPlusType':'sector','parityProblemPlusStartSector':'9',
               'parityProblemPlusEndSector':'100','parityProblemPlusCorrect':'0'}
        invalid = [dict(cfg,parityProblemPlusStartSector=value) for value in ['-1','NaN','1.2','0; echo injected','9999999999999999']]
        invalid += [dict(cfg,parityProblemPlusEndSector=value) for value in ['9','0','1001']]
        invalid += [dict(cfg,parityProblemPlusCorrect='true'),dict(cfg,parityProblemPlusType='bad')]
        percent = dict(cfg,parityProblemPlusType='percent',parityProblemPlusStartPercent='10',parityProblemPlusEndPercent='20')
        invalid += [dict(percent,parityProblemPlusEndPercent=value) for value in ['101','nan','10','20abc']]
        result = self.php(code,[cfg,percent]+invalid)
        self.assertEqual(result[0], {'startSector':8,'endSector':100,'correct':False})
        self.assertEqual(result[1], {'startSector':96,'endSector':200,'correct':False})
        self.assertEqual(result[2:], [False]*len(invalid))

    def test_version_missing_empty_invalid_and_normal(self):
        code = '''require $base.'/parity.check.tuning.plus.i18n.php';$r=[];$p=$fixture.'/version';
        $r[]=pctVersion($p);foreach(['','<unknown>','<script>alert(1)</script>','2026.11.03.02\\n'] as $v){
        file_put_contents($p,str_replace('\\\\n',"\\n",$v));$r[]=pctVersion($p);}echo json_encode($r);'''
        self.assertEqual(self.php(code), ['unknown','unknown','unknown','unknown','2026.11.03.02'])


if __name__ == '__main__': unittest.main(verbosity=2)
