"""Protect inherited notices without permitting project-identity reintroduction."""
from pathlib import Path
import tempfile
import unittest

from check_branding import check_attribution, inherited_attribution_names


class Attribution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pct-attribution-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'NOTICE').write_text(
            'Copyright 2000-2020, Prior Maintainer (legacy-account).\n',
            encoding='utf-8')

    def test_reads_names_and_account_aliases_from_the_preserved_notice(self):
        self.assertEqual(set(inherited_attribution_names(self.root)),
                         {'Prior Maintainer', 'legacy-account'})

    def test_preserved_copyright_comments_are_allowed(self):
        names = inherited_attribution_names(self.root)
        for prefix in ['/* ', ' * ', '# ']:
            with self.subTest(prefix=prefix):
                check_attribution(prefix+'Copyright 2000-2020, Prior Maintainer (legacy-account).', names)
        check_attribution('Maintained by the current project.\nhttps://example.test/current-project', names)

    def test_reintroduced_non_notice_names_and_support_links_are_rejected(self):
        names = inherited_attribution_names(self.root)
        for text in ['Maintained by Prior Maintainer',
                     'https://example.test/legacy-account/project',
                     'Support: LEGACY-ACCOUNT',
                     'Copyright 2000-2020, Prior Maintainer (legacy-account).']:
            with self.subTest(text=text):
                with self.assertRaisesRegex(AssertionError, 'Non-notice inherited attribution'):
                    check_attribution(text, names)

    def test_missing_holder_information_does_not_silently_disable_the_check(self):
        (self.root/'NOTICE').write_text('Maintained by the current project.\n', encoding='utf-8')
        with self.assertRaisesRegex(AssertionError, 'NOTICE must identify'):
            inherited_attribution_names(self.root)


if __name__ == '__main__':
    unittest.main()
