"""Negative control for original/current behavioral comparison without a download."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import check_upstream_compatibility as compatibility


class UpstreamComparison(unittest.TestCase):
    def test_detects_changed_setting_binding_without_running_cli_entry_points(self):
        source = (compatibility.CURRENT/f'{compatibility.PLUGIN}.php').read_text()
        with tempfile.TemporaryDirectory(prefix='pct-compare-control-') as temp:
            root = Path(temp)
            old = root/'original'
            current = root/'current'
            old.mkdir()
            current.mkdir()
            # A top-level exception proves that the extractor executes functions only.
            original = '<?php throw new Exception("CLI entry point executed"); ?>\n'+source
            original = original.replace('parityTuningPlus','parityTuning').replace('PARITY_TUNING_PLUS_','PARITY_TUNING_')
            (old/f'{compatibility.ORIGINAL}.php').write_text(original)
            candidate = current/f'{compatibility.PLUGIN}.php'
            candidate.write_text(source)
            with patch.object(compatibility,'CURRENT',current), contextlib.redirect_stdout(io.StringIO()):
                compatibility.check_policies(old)
                needle = "$parityTuningPlusCfg['parityTuningPlusManual'] === '1'"
                self.assertEqual(source.count(needle),1)
                candidate.write_text(source.replace(needle,"$parityTuningPlusCfg['parityTuningPlusScheduled'] === '1'"))
                with self.assertRaises(AssertionError):
                    compatibility.check_policies(old)
