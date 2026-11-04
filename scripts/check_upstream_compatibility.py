#!/usr/bin/env python3
"""Compare selected live functions with the pinned original distribution, offline.

Provide the pinned baseline checkout in an ignored directory and pass its path
with --upstream. Only named functions are extracted; neither CLI
entry point nor installer is executed. Native commands are fixture callbacks.
This establishes the listed contracts, not physical Unraid acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = 'parity.check.tuning.plus'
CURRENT = ROOT/'source/usr/local/emhttp/plugins'/PLUGIN
UPSTREAM_COMMIT = '5580d8f2a93223c81d805fbe556b00385b3201a7'
UPSTREAM_VERSION = '2026.04.24'
UPSTREAM_SHA256 = 'f6f6458db47d08c16f29726e958642b09e9cf839d37444ae8ca5f82bb06ae71f'
ORIGINAL = 'parity.check.tuning'


def literal(value):
    """A PHP single-quoted literal, with no variable interpolation."""
    return "'"+str(value).replace('\\','\\\\').replace("'","\\'")+"'"


def php(code, payload=None):
    prelude = 'require '+literal((ROOT/'scripts/php_functions.php').as_posix())+';'
    result = subprocess.run(['php', '-d', 'short_open_tag=1', '-r', prelude+code],
                            input=json.dumps(payload), capture_output=True, text=True,
                            timeout=30)
    if result.returncode or result.stderr:
        raise AssertionError(result.stdout+result.stderr)
    return json.loads(result.stdout)


def definitions(path, names, namespace, stubs=''):
    # Normalize identifiers only. Original executable decisions stay unchanged.
    code = 'pctFixtureFunctions('+literal(path.as_posix())+',json_decode('+literal(json.dumps(names))+',true))'
    if namespace == 'Original':
        mapping = {
            'parityTuning': 'parityTuningPlus',
            'PARITY_TUNING_': 'PARITY_TUNING_PLUS_',
            'parityProblem': 'parityProblemPlus',
            '"Parity Problem Assistant"': '"Parity Check Tuning Plus Assistant"',
            '"Parity Check Tuning"': '"Parity Check Tuning Plus"',
        }
        code = 'strtr('+code+',json_decode('+literal(json.dumps(mapping))+',true))'
    return 'eval('+literal('namespace '+namespace+';'+stubs)+' . '+code+');'


def check_baseline(upstream, scratch):
    commit = subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
    assert commit == UPSTREAM_COMMIT, 'Expected pinned original commit '+UPSTREAM_COMMIT
    manifest = ET.fromstring((upstream/f'{ORIGINAL}.plg').read_text())
    assert manifest.attrib['version'] == UPSTREAM_VERSION
    package = upstream/'archives'/f'{ORIGINAL}-{UPSTREAM_VERSION}.txz'
    assert hashlib.sha256(package.read_bytes()).hexdigest() == UPSTREAM_SHA256
    count = 0
    with tarfile.open(package) as archive:
        for member in archive:
            if not member.isfile():
                continue
            name = member.name.removeprefix('./')
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
            data = archive.extractfile(member).read()
            source = upstream/'source'/relative
            # Upstream Git uses capital P for this one file; its package uses lower p.
            if not source.is_file() and relative.name == 'parity.check.entries.php':
                source = source.with_name('Parity.check.entries.php')
            assert source.is_file(), 'Missing original source: '+name
            assert source.read_bytes().replace(b'\r\n',b'\n') == data.replace(b'\r\n',b'\n'), name
            output = scratch/relative
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(data)
            count += 1
    print(f'PASS: original {UPSTREAM_COMMIT}, manifest/archive checksum, {count} source/package files.')
    return scratch/'usr/local/emhttp/plugins'/ORIGINAL


def check_defaults(old):
    def read(path):
        return dict(line.split('=',1) for line in path.read_text().splitlines() if line)
    original = {key.replace('parityTuning','parityTuningPlus').replace('parityProblem','parityProblemPlus'): value
                for key,value in read(old/'default.cfg').items()}
    current = read(CURRENT/'default.cfg')
    for retired in ['Docker','Containers']:
        original.pop('parityTuningPlus'+retired)
    assert current.keys() == original.keys()
    differences = {key:(original[key],current[key]) for key in original if original[key] != current[key]}
    assert differences == {'parityTuningPlusBackground': ('"1"','"0"')}, differences
    print(f'PASS: {len(current)} retained settings; only documented quiet-notification default differs.')


def check_policies(old):
    stubs = '''function startsWith($a,$b){return strncmp($a,$b,strlen($b))===0;}
    function parityTuningPlusLoggerTesting($m){}
    function operationTriggerType(){return $GLOBALS['trigger'];}'''
    code = ''.join(definitions(path, ['configuredAction','isRunInIncrements'], ns, stubs)
                   for ns,path in [('Original',old/f'{ORIGINAL}.php'),('Current',CURRENT/f'{PLUGIN}.php')])
    code += r'''
    $parityTuningPlusDescription='fixture';$count=0;
    $keys=['Scheduled','Manual','Automatic','Recon','Clear'];
    foreach(range(0,31) as $mask){
      foreach($keys as $i=>$key)$parityTuningPlusCfg['parityTuningPlus'.$key]=($mask & 1<<$i)?'1':'0';
      foreach(['check','check P','recon D1','clear','unknown'] as $parityTuningPlusAction){
        foreach(['SCHEDULED','MANUAL','AUTOMATIC'] as $trigger){
          $a=[(bool)\Original\configuredAction(),\Original\isRunInIncrements($parityTuningPlusAction)];
          $b=[(bool)\Current\configuredAction(),\Current\isRunInIncrements($parityTuningPlusAction)];
          if($a!==$b)throw new Exception(json_encode([$mask,$parityTuningPlusAction,$trigger,$a,$b]));
          $count++;
        }
      }
    }echo json_encode($count);'''
    count = php(code)
    assert count == 480
    print(f'PASS: {count} original/current trigger and operation-policy combinations.')


def check_formatting(old):
    stubs = 'function _($s){return $s;} function pctT($s){return $s;}'
    names = ['this_plus','this_duration','tempInDisplayUnit','listDrives','opWithErrorCount']
    code = ''.join(definitions(path,names,ns,stubs) for ns,path in
                   [('Original',old/f'{ORIGINAL}.php'),('Current',CURRENT/f'{PLUGIN}.php')])
    code += r'''
    $count=0;
    foreach([0,1,59,60,61,3599,3600,86399,86400,172800,194352] as $value){
      if(\Original\this_duration($value)!==\Current\this_duration($value))throw new Exception('Duration '.$value);
      $count++;
    }
    foreach(['C','F'] as $parityTuningPlusTempUnit){
      foreach([-5,0,20,37,45,55,70,100] as $value){
        if(\Original\tempInDisplayUnit($value)!==\Current\tempInDisplayUnit($value))throw new Exception('Temperature');
        $count++;
      }
      foreach([[],['parity'=>45],['disk1'=>'*','disk2'=>37]] as $drives){
        if(\Original\listDrives($drives)!==\Current\listDrives($drives))throw new Exception('Drive list');
        $count++;
      }
    }
    foreach([0,1,123] as $parityTuningPlusErrors){
      if(\Original\opWithErrorCount('Paused')!==\Current\opWithErrorCount('Paused'))throw new Exception('Error text');
      $count++;
    }echo json_encode($count);'''
    count = php(code)
    assert count == 36
    print(f'PASS: {count} original/current duration, temperature, drive-list and error-text cases.')


def check_state(old, scratch):
    statefile = scratch/'var.ini'
    code = 'define("PARITY_TUNING_PLUS_EMHTTP_VAR_FILE",'+json.dumps(statefile.as_posix())+');'
    for name in ['SCHEDULED','AUTOMATIC','MANUAL','PARTIAL']:
        code += 'define("PARITY_TUNING_PLUS_'+name+'_FILE",'+json.dumps((scratch/name).as_posix())+');'
    stubs = 'function parityTuningPlusLoggerTesting($s){} function pctT($s){return $s;} function actionDescription(...$args){return "fixture";}'
    code += ''.join(definitions(path,['loadVars'],ns,stubs) for ns,path in
                    [('Original',old/f'{ORIGINAL}.helpers.php'),('Current',CURRENT/f'{PLUGIN}.helpers.php')])
    code += r'''
    $count=0;$guarded=0;
    foreach(['STARTED','STOPPED','STARTING','STOPPING'] as $state){
      foreach([0,1,123456] as $running){
        foreach([0,100] as $position){
          $raw=['NAME'=>'fixture','mdState'=>$state,'mdResyncPos'=>$position,'mdResyncSize'=>1000,
                'mdResyncAction'=>'check P','mdResync'=>$running,'mdResyncCorr'=>1,
                'sbSyncErrs'=>2,'sbSynced'=>100,'sbSynced2'=>0,'sbSyncExit'=>0];
          $text='';foreach($raw as $k=>$v)$text.=$k.'="'.$v.'"'."\n";
          file_put_contents(PARITY_TUNING_PLUS_EMHTTP_VAR_FILE,$text);
          $results=[];
          foreach(['Original','Current'] as $ns){
            call_user_func($ns.'\\loadVars');$result=[];
            foreach(['Server','Started','Pos','Size','Action','Active','Paused','Correcting','Errors'] as $key){
              $value=$GLOBALS['parityTuningPlus'.$key];$result[$key]=is_numeric($value)?(int)$value:$value;
            }$results[]=$result;
          }
          if($state!=='STARTED' && $position>0){
            // Intentional fail-closed change: stale positive positions on a stopped array are inactive.
            if($results[1]['Active']!==0 || $results[1]['Paused']!==0)throw new Exception('Stopped array treated active');
            unset($results[0]['Active'],$results[0]['Paused'],$results[1]['Active'],$results[1]['Paused']);$guarded++;
          }
          if($results[0]!==$results[1])throw new Exception(json_encode([$raw,$results]));$count++;
        }
      }
    }echo json_encode([$count,$guarded]);'''
    count,guarded = php(code)
    assert (count,guarded) == (24,9)
    print(f'PASS: {count} native-state combinations, including {guarded} intentional stopped-array safety differences.')


def check_cron(old, scratch):
    cron = scratch/'fixture.cron'
    code = 'define("PARITY_TUNING_PLUS_PLUGIN","fixture");define("PARITY_TUNING_PLUS_PHP_FILE","/fixture/plugin.php");'
    code += 'define("PARITY_TUNING_PLUS_CRON_FILE",'+json.dumps(cron.as_posix())+');'
    code += 'define("PARITY_TUNING_PLUS_INCREMENT_FILE",'+json.dumps((scratch/'increment').as_posix())+');'
    stubs = '''function _($s){return $s;} function pctT($s){return $s;}
    function parityTuningPlusLoggerTesting($s){} function parityTuningPlusLoggerDebug($s){}
    function parityTuningPlusPartial(){return $GLOBALS['partial'];}
    function parityTuningPlusDeleteFile($p){if(is_file($p))unlink($p);}
    function exec($s){if($s!=='/usr/local/sbin/update_cron')throw new \\Exception('Unexpected command');$GLOBALS['cronCalls']++;}'''
    code += definitions(old/f'{ORIGINAL}.php',['updateCronEntries'],'Original',stubs)
    code += definitions(CURRENT/f'{PLUGIN}.php',['updateCronEntries'],'Current',stubs)
    code += 'eval("namespace Current;".pctFixtureFunctions('+json.dumps((CURRENT/f'{PLUGIN}.helpers.php').as_posix())+',["pctCronExpression"]));'
    code += '$defaults=parse_ini_file('+json.dumps((CURRENT/'default.cfg').as_posix())+');'
    code += r'''
    $count=0;
    foreach(['0','1','2'] as $frequency){
      foreach([false,true] as $increments){
        foreach(['idle','active','heat','shutdown','partial'] as $mode){
          $parityTuningPlusCfg=$defaults;
          foreach(['Scheduled','Manual','Automatic','Recon','Clear'] as $key)$parityTuningPlusCfg['parityTuningPlus'.$key]='0';
          $parityTuningPlusCfg['parityTuningPlusScheduled']=$increments?'1':'0';
          $parityTuningPlusCfg['parityTuningPlusFrequency']=$frequency;
          $parityTuningPlusCfg['parityTuningPlusHeat']=$mode==='heat'?'1':'0';
          $parityTuningPlusCfg['parityTuningPlusHeatShutdown']=$mode==='shutdown'?'1':'0';
          $parityTuningPlusActive=$mode==='active';$partial=$mode==='partial';$results=[];
          foreach(['Original','Current'] as $ns){
            @unlink(PARITY_TUNING_PLUS_CRON_FILE);$cronCalls=0;
            call_user_func($ns.'\\updateCronEntries');
            if($cronCalls!==1)throw new Exception('Cron callback missing');
            $results[]=file_get_contents(PARITY_TUNING_PLUS_CRON_FILE);
          }
          if($results[0]!==$results[1])throw new Exception(json_encode([$frequency,$increments,$mode,$results]));$count++;
        }
      }
    }echo json_encode($count);'''
    count = php(code)
    assert count == 30
    print(f'PASS: {count} original/current daily, weekly, custom and monitor cron cases.')


def check_notifications(old):
    stubs = r'''function _($s){return $s;} function pctT($s){return $s;}
    function parityTuningPlusLogger($s){} function parityTuningPlusLoggerTesting($s){}
    function parityTuningPlusPartial(){return $GLOBALS['partial'];}
    function parityTuningPlusCompleted(){return ' 50%';}
    function exec($command,&$output=null,&$status=null){$GLOBALS['calls'][]=$command;$status=0;return '';}'''
    names = ['sendNotification','sendNotificationWithCompletion','sendArrayNotification','sendTempNotification','opWithErrorCount']
    code = ''.join(definitions(path,names,ns,stubs) for ns,path in
                   [('Original',old/f'{ORIGINAL}.php'),('Current',CURRENT/f'{PLUGIN}.php')])
    code += r'''
    $docroot='/fixture';$parityTuningPlusServer='FIXTURE';$parityTuningPlusDescription='Scheduled Correcting Parity-Check';$count=0;
    foreach(['','1'] as $system)foreach(['0','1'] as $notify)foreach(['0','1'] as $heatNotify)foreach([false,true] as $partial)foreach([0,3] as $errors){
      $dynamixCfg=['notify'=>['system'=>$system]];
      $parityTuningPlusCfg=['parityTuningPlusNotify'=>$notify,'parityTuningPlusHeatNotify'=>$heatNotify];
      $parityTuningPlusErrors=$errors;$results=[];
      foreach(['Original','Current'] as $ns){
        $calls=[];
        call_user_func($ns.'\\sendNotification','A "literal" $(test)','desc 日本語','warning','/Settings/Scheduler');
        call_user_func($ns.'\\sendNotificationWithCompletion','paused','overheated','alert');
        call_user_func($ns.'\\sendArrayNotification','resumed','normal');
        call_user_func($ns.'\\sendTempNotification','cool','drive','normal');
        $results[]=[$calls,call_user_func($ns.'\\opWithErrorCount','paused')];
      }
      if($results[0]!==$results[1])throw new Exception(json_encode([$system,$notify,$heatNotify,$partial,$errors,$results]));$count++;
    }echo json_encode($count);'''
    count = php(code)
    assert count == 32
    print(f'PASS: {count} original/current notification-policy cases, including quoted and Unicode arguments.')


def check(upstream):
    with tempfile.TemporaryDirectory(prefix='pct-upstream-') as temp:
        scratch = Path(temp)
        old = check_baseline(upstream.resolve(),scratch/'original')
        check_defaults(old)
        check_policies(old)
        check_formatting(old)
        check_state(old,scratch)
        check_cron(old,scratch)
        check_notifications(old)
    print('PASS: 602 executable comparisons; documented differences explicitly checked. No native host actions executed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream',type=Path,required=True)
    check(parser.parse_args().upstream)
