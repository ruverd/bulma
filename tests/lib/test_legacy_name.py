import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('check_legacy_name.py')


class LegacyNameTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.write('install.sh', '# legacy layout migration (begin)\nLEGACY="previous"\n# legacy layout migration (end)\n')
        self.write('plugin.json', json.dumps({'author': {'name': 'Previous Developer'}}))

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        subprocess.run(['git', '-C', str(self.root), 'add', '--', name], check=True)

    def check(self):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.root)], capture_output=True, text=True)

    def test_matching_learning_author_is_identity(self):
        self.write('.julius/learnings/2026-10-28-fix-previous.md', '---\nauthor: Previous\n---\nNo obsolete branding.\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_body_and_title_still_reject_obsolete_branding(self):
        for text in ('---\nauthor: Previous\ntitle: previous product\n---\n',
                     '---\nauthor: Previous\n---\nUse previous now.\n'):
            with self.subTest(text=text):
                self.write('.julius/learnings/2026-10-28-fix-previous.md', text)
                result = self.check()
                self.assertEqual(result.returncode, 1)
                self.assertIn('legacy name ->', result.stdout)

    def test_learning_slug_still_rejects_obsolete_branding(self):
        self.write('.julius/learnings/2026-10-28-previous-fix-previous.md', '---\nauthor: Previous\n---\n')
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('path contains', result.stdout)

    def test_mismatched_author_and_nonlearning_paths_are_not_exempt(self):
        self.write('.julius/learnings/2026-10-28-fix-previous.md', '---\nauthor: Someone\n---\n')
        self.write('docs/2026-10-28-fix-previous.md', '---\nauthor: Previous\n---\n')
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count('path contains'), 2)
        self.assertIn('author: Previous', result.stdout)


if __name__ == '__main__':
    unittest.main()
