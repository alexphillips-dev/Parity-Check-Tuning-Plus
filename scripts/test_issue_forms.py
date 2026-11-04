"""Guard against silently broken report routing and unsafe required diagnostics."""
from pathlib import Path
import shutil
import tempfile
import unittest

import check_issue_forms as forms


class IssueForms(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pct-issue-forms-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(forms.ROOT/'.github',self.root/'.github')
        self.bug = self.root/'.github/ISSUE_TEMPLATE/01-bug-report.yml'

    def test_real_forms_and_label_references_are_valid(self):
        self.assertEqual(forms.validate(self.root),(5,27))

    def test_duplicate_yaml_keys_cannot_silently_change_routing(self):
        self.bug.write_text(self.bug.read_text()+'\nlabels: [question]\n')
        with self.assertRaisesRegex(ValueError,'Duplicate YAML mapping key'):
            forms.validate(self.root)

    def test_unknown_automatic_label_is_detected(self):
        labels = self.root/'.github/labels.json'
        labels.write_text(labels.read_text().replace('"needs-triage"','"unreviewed-renaming"'))
        with self.assertRaisesRegex(ValueError,'unknown automatic label'):
            forms.validate(self.root)

    def test_diagnostics_cannot_become_required(self):
        value = forms.load_yaml(self.bug)
        next(item for item in value['body'] if item.get('id')=='logs')['validations']['required']=True
        self.bug.write_text(forms.yaml.safe_dump(value,sort_keys=False))
        with self.assertRaisesRegex(ValueError,'diagnostics must remain optional'):
            forms.validate(self.root)
