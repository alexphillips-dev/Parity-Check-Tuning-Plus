"""Clock-controlled tests of the actual schedule functions."""
import json
import subprocess
import unittest
from build_package import ROOT, PLUGIN


class Schedule(unittest.TestCase):
    def evaluate(self, cases):
        harness=json.dumps((ROOT/'scripts/php_functions.php').as_posix())
        source=json.dumps((ROOT/'source/usr/local/emhttp/plugins'/PLUGIN/f'{PLUGIN}.php').as_posix())
        code='namespace ScheduleFixture; require '+harness+';'
        code+='''
        function date($format){return \\date($format,$GLOBALS['timestamp']);}
        function time(){return $GLOBALS['timestamp'];}
        function isRunInIncrements($action){return true;}
        function parityTuningPlusLoggerTesting($message){}
        function file_exists($path){return $GLOBALS['marker'];}
        define('PARITY_TUNING_PLUS_INCREMENT_FILE','marker');
        define('PARITY_TUNING_PLUS_RESTART_FILE','restart');
        $parityTuningPlusAction='check P';$parityTuningPlusActive=true;
        '''
        code+='eval("namespace ScheduleFixture;".\\pctFixtureFunctions('+source+',["isActivePeriod"]));'
        code+='''$output=[];foreach(json_decode(stream_get_contents(STDIN),true) as $case){
          $timestamp=strtotime($case['time']);$marker=$case['marker']??false;
          $parityTuningPlusCfg=$case['cfg'];$output[]=(bool)isActivePeriod();
        }echo json_encode($output);'''
        result=subprocess.run(['php','-r',code],input=json.dumps(cases),text=True,capture_output=True)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout+result.stderr)
        return json.loads(result.stdout)

    def test_weekly_window_and_overnight_resume_boundary(self):
        cfg={'parityTuningPlusFrequency':'2','parityTuningPlusResumeDay':'0','parityTuningPlusResumeHour':'22','parityTuningPlusResumeMinute':'0','parityTuningPlusPauseDay':'1','parityTuningPlusPauseHour':'2','parityTuningPlusPauseMinute':'0'}
        cases=[{'time':time,'cfg':cfg} for time in ['2026-11-01 22:00','2026-11-01 23:00','2026-11-02 01:00','2026-11-02 02:00','2026-11-03 23:00']]
        self.assertEqual(self.evaluate(cases),[True,True,True,False,False])
