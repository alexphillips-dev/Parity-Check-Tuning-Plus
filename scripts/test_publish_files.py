"""Publication boundary regressions, including forced adds and exact index bytes."""
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from check_publish_files import ROOT, allowed_path, check_index, content_issues, identity_issues, inspect_file


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

    def test_private_email_is_rejected_without_exposing_the_address(self):
        address = ('private-person'+'@'+'mail.invalid').encode()
        self.assertEqual(content_issues(address), ['nonpublic-email'])
        for address in [b'public-alias@users.noreply.github.com', b'123+public-alias@users.noreply.github.com', b'person@example.com']:
            self.assertEqual(content_issues(address), [])

    def test_fixture_email_exception_requires_exact_path_and_bytes(self):
        name = 'tests/fixtures/unraid/Markdown.php'
        data = (ROOT/name).read_bytes()
        self.assertIn('nonpublic-email', content_issues(data))
        self.assertEqual(inspect_file(name, data), [])
        self.assertIn((name, 'nonpublic-email'), inspect_file(name, data+b'\n'))
        other = 'tests/fixtures/unraid/other.php'
        self.assertIn((other, 'nonpublic-email'), inspect_file(other, data))

    def test_personal_profile_name_is_rejected_without_exposing_it(self):
        profile = 'Fixture'+' Private'
        with patch('check_publish_files.Path.home', return_value=Path('/profiles')/profile):
            self.assertEqual(content_issues(profile.upper().encode()), ['private-profile-name'])
            self.assertEqual(content_issues(b'Public project documentation'), [])

    def test_resolved_git_identities_reject_environment_leaks(self):
        with tempfile.TemporaryDirectory(prefix='pct-identity-') as directory:
            subprocess.run(['git', 'init', '-q', directory], check=True)
            public = {'GIT_AUTHOR_NAME':'public-alias', 'GIT_COMMITTER_NAME':'public-alias',
                      'GIT_AUTHOR_EMAIL':'public-alias@users.noreply.github.com',
                      'GIT_COMMITTER_EMAIL':'public-alias@users.noreply.github.com'}
            with patch.dict(os.environ, public):
                self.assertEqual(identity_issues(directory), [])
                with patch.dict(os.environ, {'GIT_AUTHOR_EMAIL':'private'+'@'+'mail.invalid'}):
                    self.assertEqual(identity_issues(directory), [('git-author', 'nonpublic-identity-email')])
                with patch.dict(os.environ, {'GIT_COMMITTER_NAME':'Fixture'+' Private'}):
                    self.assertEqual(identity_issues(directory), [('git-committer', 'nonpublic-identity-name')])

    def test_package_email_is_checked_even_when_its_filename_is_allowed(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:xz') as archive:
            entry = tarfile.TarInfo('usr/local/emhttp/plugins/parity.check.tuning.plus/config.php')
            data = ('<?php /* '+'private'+'@'+'mail.invalid'+' */').encode()
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
        issues = inspect_file('archives/parity.check.tuning.plus-2026.11.04.05.txz', buffer.getvalue())
        self.assertEqual([category for _, category in issues], ['nonpublic-email'])


if __name__ == '__main__':
    unittest.main()
