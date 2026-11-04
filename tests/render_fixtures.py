#!/usr/bin/env python3
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from test_runtime import Runtime

output=ROOT/'build/ui-cases'
output.mkdir(parents=True,exist_ok=True)
fixture=Runtime('test_cli_name_catalog_and_log_brand')
fixture.setUp()
try:
    host=fixture.root/'usr/local/emhttp'
    for source in (ROOT/'tests/fixtures/unraid').glob('*.php'):
        shutil.copyfile(source,host/'webGui/include'/source.name)
    for code in ['en_US']:
        fixture.write(host/f'languages/{code}/helptext.txt','')
    shutil.copytree(ROOT/'source/usr/local/emhttp/languages',host/'languages',dirs_exist_ok=True)
    (host/'webGui/javascript').mkdir(parents=True)
    helpers=host/'webGui/include/Helpers.php'
    text=helpers.read_text().replace("$root = getenv('PCT_PLUS_FIXTURE');", "$root = getenv('PCT_PLUS_FIXTURE');\n    if ($plugin === 'dynamix') return ['display'=>['locale'=>$_SESSION['locale']??'', 'unit'=>'C']];")
    text += r'''
function mk_option($selected,$value,$label){return '<option value="'.htmlspecialchars((string)$value,ENT_QUOTES).'"'.((string)$selected===(string)$value?' selected':'').'>'.htmlspecialchars((string)$label,ENT_QUOTES).'</option>';}
// The weekday selectors call this native host helper directly.
function mk_option_check($selected,$value,$label){return mk_option($selected,$value,$label);}
function autov($path){echo htmlspecialchars($path,ENT_QUOTES);}
function _var($values,$key,$default=''){return $values[$key]??$default;}
function my_explode($separator,$text,$limit){return array_pad(explode($separator,trim($text)),$limit,'');}
function my_scale($value,&$unit,$precision){$unit='B';return (string)round($value,max(0,$precision));}
'''
    helpers.write_text(text)
    var=fixture.root/'var/local/emhttp/var.ini'
    var.write_text(var.read_text().replace('mdState="STOPPED"','mdState="STARTED"'))
    # Make optional setting groups available to the layout matrix without a live daemon.
    fixture.write(fixture.root/'boot/config/plugins/appdata.backup.plg','fixture')
    fixture.write(fixture.root/'var/log/syslog','Nov 3 kernel: md: recovery thread: P incorrect, sector=432 <script>bad()</script>\n')
    fixture.write(fixture.root/'boot/config/parity-checks.log','2026 Nov 03 10:00:00|3600|1000000|0|0|check P|1000|7200|2|Scheduled Non-Correcting Parity-Check\n')
    metadata=json.loads((fixture.plugin/'locales/locales.json').read_text(encoding='utf-8'))
    cases=[]
    routes=[('settings','Parity.check.tuning.plus.page','/Settings/Scheduler'),
            ('plugins','Parity.check.tuning.plus.page','/Plugins/Parity.check.tuning.plus'),
            ('assistant','Parity.check.tuning.plus.problems.page','/Tools/Parity.check.tuning.plus.problems'),
            ('popup','parity.check.tuning.plus.entries.php','/plugins/parity.check.tuning.plus/parity.check.tuning.plus.entries.php'),
            ('history','parity.check.tuning.plus.history.php','/Main')]
    for code in [*metadata['locales'],*metadata['aliases']]:
        canonical=metadata['aliases'].get(code,code)
        catalog=json.loads((fixture.plugin/'locales'/f'{canonical}.json').read_text(encoding='utf-8'))
        for kind,page,uri in routes:
            result=subprocess.run(['php','-d','short_open_tag=1',str(ROOT/'tests/render_page.php'),code,page,uri],
                                  env=dict(os.environ,PCT_PLUS_FIXTURE=str(fixture.root)),capture_output=True,text=True,encoding='utf-8')
            if result.returncode or result.stderr:raise RuntimeError(f'{code}/{kind}: {result.stdout}\n{result.stderr}')
            name=f'{code}-{kind}.html'
            (output/name).write_text(result.stdout,encoding='utf-8',newline='\n')
            cases.append({'locale':code,'canonical':canonical,'kind':kind,'file':name,
                          'rtl':metadata['locales'][canonical]['rtl'],
                          'expected':{key:catalog[key] for key in ['Check','Done','Do you really want Debug logging mode?','Increment frequency','Method used to specify start and stop points','sector','percent','Action','Scheduled','Non-Correcting']}})
    (output/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(f'Rendered {len(cases)} pages using official Unraid parsers, including native locale aliases.')
finally:
    fixture.doCleanups()
