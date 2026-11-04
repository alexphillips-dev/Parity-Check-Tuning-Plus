from pathlib import Path
import json
import hashlib
import shutil
import subprocess
import tempfile
import unittest

from build_package import ROOT, PLUGIN
from build_i18n import extract, read, signature, untranslated

BASE=ROOT/'source/usr/local/emhttp/plugins'/PLUGIN


class Languages(unittest.TestCase):
    def test_official_parser_fixture_blob_integrity(self):
        fixture=ROOT/'tests/fixtures/unraid'
        for name,metadata in read(fixture/'sources.json').items():
            data=(fixture/name).read_bytes()
            blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            self.assertEqual(blob,metadata['blob'],name)

    def php(self,code):
        result=subprocess.run(['php','-r',code],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(result.stderr,'',result.stderr)
        return json.loads(result.stdout)

    def test_every_catalog_covers_the_actual_source_and_preserves_templates(self):
        english=extract()
        metadata=read(BASE/'locales/locales.json')
        self.assertEqual(len(metadata['locales']),42)
        for code in metadata['locales']:
            catalog=read(BASE/'locales'/f'{code}.json')
            self.assertEqual(catalog.keys(),english.keys(),code)
            for key,value in catalog.items():
                self.assertTrue(value.strip(),(code,key))
                self.assertEqual(signature(english[key]),signature(value),(code,key))
                if code!='en_US':self.assertFalse(untranslated(english[key],value),(code,key))
        self.assertIn('specify the end point',english['_parityProblemsPlus_end_plug'])
        self.assertNotIn('specify the start point',english['_parityProblemsPlus_end_plug'])

    def test_locale_switching_aliases_and_english_reset_in_one_request(self):
        code='require '+json.dumps((BASE/f'{PLUGIN}.i18n.php').as_posix())+';'
        code+="""$out=[];foreach(['de_DE','ja_JA','ko_KO','da_DA','ar_AR','','../../bad'] as $locale){
        $_SESSION['locale']=$locale;$out[]=[pctLocaleDefinition()['locale'],pctT('Done')];}echo json_encode($out);"""
        output=self.php(code)
        self.assertEqual([item[0] for item in output],['de_DE','ja_JP','ko_KR','da_DK','ar_AR','en_US','en_US'])
        self.assertEqual(output[-1][1],'Done')
        self.assertNotEqual(output[0][1],'Done')

    def test_translated_printf_templates_execute_in_every_language(self):
        code='require '+json.dumps((BASE/f'{PLUGIN}.i18n.php').as_posix())+';'
        code+='''$meta=json_decode(file_get_contents('''+json.dumps((BASE/'locales/locales.json').as_posix())+'''),true);
        $count=0;foreach($meta['locales'] as $locale=>$definition){
          $_SESSION['locale']=$locale;
          $catalog=json_decode(file_get_contents('''+json.dumps((BASE/'locales').as_posix())+'''.'/'.$locale.'.json'),true);
          foreach($catalog as $key=>$value){
            if($key[0]==='_')continue;
            if(preg_match_all('/%(\\d+)\\$/',$value,$matches)){
              $result=vsprintf($value,array_fill(0,max($matches[1]),8));
              if($result===false)throw new Exception($locale.': '.$key);
              $count++;
            }
          }
        }echo json_encode($count);'''
        self.assertGreater(self.php(code),500)

    def test_translated_html_and_javascript_are_escaped(self):
        with tempfile.TemporaryDirectory(prefix='pct-plus-i18n-') as directory:
            root=Path(directory)
            shutil.copyfile(BASE/f'{PLUGIN}.i18n.php',root/f'{PLUGIN}.i18n.php')
            (root/'locales').mkdir()
            shutil.copyfile(BASE/'locales/locales.json',root/'locales/locales.json')
            danger='</script><script>bad()</script> "quote" \'apostrophe\'\n\u2028'
            (root/'locales/en_US.json').write_text(json.dumps({'danger':danger}),encoding='utf-8')
            code='require '+json.dumps((root/f'{PLUGIN}.i18n.php').as_posix())+';echo json_encode([pctH("danger"),pctJ("danger")]);'
            html,script=self.php(code)
            self.assertNotIn('<script>',html)
            self.assertNotIn('</script>',script)
            self.assertEqual(json.loads(script),danger)


if __name__=='__main__':unittest.main(verbosity=2)
