"""Negative controls for owned-code reachability, callbacks, and host contracts."""
from pathlib import Path
import tempfile
import unittest

from check_runtime_references import javascript_references, php_references


class References(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pct-references-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def test_unreachable_function_cycle_is_detected_and_live_callback_is_kept(self):
        (self.root/'main.php').write_text('''<?php
function unusedOne(){unusedTwo();}
function unusedTwo(){unusedOne();}
function callback($v){return $v;}
array_map('callback',[]);
''')
        self.assertEqual({entry['name'] for entry in php_references(self.root)}, {'unusedOne','unusedTwo'})
        with (self.root/'main.php').open('a') as file:file.write('unusedOne();')
        self.assertEqual(php_references(self.root), [])

    def test_native_parser_api_is_an_explicit_host_contract(self):
        (self.root/'Legacy.php').write_text('<?php function parse_file($file){return $file;} function staleHelper(){}')
        self.assertEqual([entry['name'] for entry in php_references(self.root)], ['staleHelper'])

    def test_html_callbacks_are_live_and_comments_do_not_keep_dead_js(self):
        (self.root/'settings.page').write_text('''---
<script>function active(){} function stale(){} // stale();
/* stale(); */
</script><input onclick="active()"><a href="https://example.invalid/">Docs</a>
''')
        self.assertEqual([entry['name'] for entry in javascript_references(self.root)], ['stale'])
