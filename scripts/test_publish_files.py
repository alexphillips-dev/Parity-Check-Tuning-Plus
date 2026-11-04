"""Publication boundary regressions, including forced adds and exact index bytes."""
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

from check_publish_files import allowed_path, check_index, content_issues, inspect_file


class Publication(unittest.TestCase):
    def test_only_product_and_reproducible_development_inputs_are_allowed(self):
        for name in ['README.md', 'scripts/check_publish_files.py', 'tests/ui.cjs',
                     'requirements-dev.txt', '.github/labels.json',
                     '.github/ISSUE_TEMPLATE/01-bug-report.yml', '.github/ISSUE_TEMPLATE/config.yml',
                     'docs/wiki/Home.md', 'source/usr/local/emhttp/plugins/parity.check.tuning.plus/default.cfg',
                     'archives/parity.check.tuning.plus-2026.11.03.07.txz']:
            self.assertTrue(allowed_path(name), name)
        for name in ['AGENTS.md', 'docs/agents.md', 'source/AGENTS.local.md', '.env',
                     '.vscode/settings.json', 'build/report.json', 'diagnostics/host.json',
                     'source/usr/local/emhttp/plugins/parity.check.tuning.plus/host.log',
                     'credentials.json', 'id_ed25519', 'unreviewed.json']:
            self.assertFalse(allowed_path(name), name)

    def test_issue_files_do_not_allow_arbitrary_github_configuration(self):
        for name in ['.github/workflows/unreviewed.yml', '.github/credentials.json',
                     '.github/ISSUE_TEMPLATE/host-data.yml', '.github/ISSUE_TEMPLATE/AGENTS.md',
                     '.github/ISSUE_TEMPLATE/config.yaml', '.github/private/labels.json']:
            self.assertFalse(allowed_path(name), name)

    def test_forced_tracked_instructions_are_rejected_despite_gitignore(self):
        with tempfile.TemporaryDirectory(prefix='pct-publish-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root/'.gitignore').write_text('AGENTS.md\n')
            (root/'AGENTS.md').write_text('Local agent instructions\n')
            subprocess.run(['git', 'add', '.gitignore'], cwd=root, check=True)
            self.assertEqual(check_index(root)[1], [])
            subprocess.run(['git', 'add', '-f', 'AGENTS.md'], cwd=root, check=True)
            self.assertIn(('AGENTS.md', 'unexpected-or-local-file'), check_index(root)[1])

    def test_guard_reads_staged_content_even_when_worktree_is_cleaned(self):
        with tempfile.TemporaryDirectory(prefix='pct-publish-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            token = 'gh' + 'p_' + 'A' * 36
            (root/'README.md').write_text(token)
            subprocess.run(['git', 'add', 'README.md'], cwd=root, check=True)
            (root/'README.md').write_text('Public documentation\n')
            self.assertIn(('README.md', 'github-token'), check_index(root)[1])

    def test_private_content_detection_does_not_return_matched_values(self):
        key = ('-----' + 'BEGIN PRIVATE KEY-----').encode()
        path = ('C:' + '/' + 'Users/' + 'fixture-profile/private.txt').encode()
        self.assertEqual(content_issues(key), ['private-key'])
        self.assertEqual(content_issues(path), ['workstation-path'])
        escaped_path = ('C:' + '\\' * 2 + 'Users' + '\\' * 2 + 'fixture-profile/private.txt').encode()
        self.assertEqual(content_issues(escaped_path), ['workstation-path'])
        self.assertEqual(content_issues(b'/boot/config/plugins/example/default.cfg'), [])

    def test_package_members_cannot_bypass_the_publication_boundary(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:xz') as archive:
            for name, data in [('usr/local/emhttp/plugins/parity.check.tuning.plus/AGENTS.md', b'Local instructions'),
                               ('usr/local/emhttp/plugins/parity.check.tuning.plus/config.php', ('gh'+'p_'+'B'*36).encode())]:
                entry = tarfile.TarInfo(name)
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))
        issues = inspect_file('archives/parity.check.tuning.plus-2026.11.03.07.txz', buffer.getvalue())
        self.assertEqual({category for _, category in issues}, {'local-file-in-package', 'github-token'})


if __name__ == '__main__':
    unittest.main()
