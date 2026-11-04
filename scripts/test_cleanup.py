"""Behavior retained while retiring unused inherited scaffolding."""
import json
import os
import shutil
import unittest

import test_runtime
from build_package import PLUGIN


@unittest.skipUnless(os.name == 'posix' and shutil.which('php'), 'Requires Linux/WSL PHP')
class Cleanup(unittest.TestCase):
    def setUp(self):
        self.host = test_runtime.Runtime('test_cli_name_catalog_and_log_brand')
        self.host.setUp()
        self.addCleanup(self.host.doCleanups)

    def test_retired_settings_are_preserved_without_a_docker_dependency(self):
        with self.host.cfg.open('a') as cfg:
            cfg.write('parityTuningPlusDocker="1"\nparityTuningPlusContainers="fixture-container"\n')
        saved = self.host.cfg.read_bytes()
        self.assertFalse((self.host.root/'boot/config/docker.cfg').exists())
        self.host.command('config')
        self.assertEqual(self.host.cfg.read_bytes(), saved)
        self.assertIn('"monitor"', (self.host.config/f'{PLUGIN}.cron').read_text())

    def test_retired_cli_placeholder_does_not_replace_gui_history(self):
        output = self.host.command('history')
        self.assertIn('Unrecognized option', output)
        self.assertNotIn('history         ', self.host.command('help'))
        self.assertTrue((self.host.plugin/f'{PLUGIN}.history.php').is_file())

    def test_legacy_parser_contract_and_offline_catalog_still_work(self):
        (self.host.root/'usr/local/emhttp/webGui/include/Translations.php').unlink()
        self.host.write(self.host.root/'usr/local/emhttp/webGui/include/Markdown.php', '<?php function Markdown($text){return "rendered:".$text;}\n')
        source = self.host.root/'legacy-input.page'
        source.write_text('Title="Fixture"\n---\n_(Done)_\n')
        expression = '[pctT("Done"),parse_file('+json.dumps(source.as_posix())+',false),function_exists("parse_help_file")]'
        self.assertEqual(self.host.helper(expression), ['Done', 'Done\n', True])
        self.assertIn('parity.check.plus', self.host.command('help'))
