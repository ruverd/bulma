import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[2] / 'skills/bulma-code-review/scripts/snapshot.py'
spec = importlib.util.spec_from_file_location('snapshot', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.context = self.root / 'CONTEXT.json'
        self.context.write_text('{"ac": ["works"], "rules": "hash"}')
        self.pr = {'head': {'sha': 'a' * 40}, 'base': {'sha': 'b' * 40, 'ref': 'main'},
                   'title': 'feature', 'body': 'AC'}
        self.snapshot = {'repo': 'o/r', 'pr': 1, **m.revision(self.pr)}
        (self.root / 'snapshot.json').write_text(json.dumps(self.snapshot))
        for name in m.ARTIFACTS:
            (self.root / name).write_text('[]')
        (self.root / 'analysis.json').write_text('{"pass": "deep", "critic": "ran"}')

    def test_cache_invalidation(self):
        m.seal(self.root, self.context)
        self.assertTrue(m.valid(self.root, self.context))
        for key in ('head', 'base', 'body'):
            changed = dict(self.snapshot, **{key: 'changed'})
            (self.root / 'snapshot.json').write_text(json.dumps(changed))
            self.assertFalse(m.valid(self.root, self.context))
        (self.root / 'snapshot.json').write_text(json.dumps(self.snapshot))
        with patch.object(m, 'policy_hash', return_value='new-policy'):
            self.assertFalse(m.valid(self.root, self.context))
        self.context.write_text('changed acceptance')
        self.assertFalse(m.valid(self.root, self.context))

    def test_incomplete_and_modified_analysis(self):
        (self.root / 'analysis.json').write_text('{"pass":"deep","critic":"failed"}')
        with self.assertRaises(ValueError):
            m.seal(self.root, self.context)
        (self.root / 'analysis.json').write_text('{"pass":"deep","critic":"ran"}')
        m.seal(self.root, self.context)
        (self.root / 'bound.json').write_text('{"lost": "findings"}')
        self.assertFalse(m.valid(self.root, self.context))

    def response(self, *args):
        if args[0:2] == ('api', 'graphql'):
            return b'[{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[]}}}}}]'
        if 'application/vnd.github.diff' in args:
            return b'diff'
        if '/files?' in args[1]:
            return b'[[{"filename":"new","previous_filename":"old"}]]'
        return b'[[]]'

    def test_collect_and_race(self):
        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=self.response):
            result = m.collect('o/r', 1, self.root)
        self.assertEqual(result, self.snapshot)
        self.assertEqual((self.root / 'PR_FILES.txt').read_text(), 'new\nold\n')
        changed = dict(self.pr, head={'sha': 'c' * 40})
        with patch.object(m, 'pr', side_effect=[self.pr, changed]), patch.object(m, 'gh', side_effect=self.response):
            with self.assertRaises(ValueError):
                m.collect('o/r', 1, self.root)
        self.assertFalse((self.root / 'snapshot.json').exists())

    def test_check_runs_forbidden_uses_statuses(self):
        def gh(*args):
            if len(args) > 1 and 'check-runs' in args[1]:
                exc = subprocess.CalledProcessError(1, args)
                exc.output = b''
                exc.stderr = b'gh: HTTP 403: Resource not accessible by integration\n'
                raise exc
            if len(args) > 1 and '/statuses?' in args[1]:
                return b'[[{"context":"build-and-test","state":"success","created_at":"t","description":"ok"}]]'
            return self.response(*args)

        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=gh):
            m.collect('o/r', 1, self.root)
        tooling = json.loads((self.root / 'ci-tooling.json').read_text())
        self.assertEqual(tooling['check_runs'], 'forbidden')
        self.assertEqual(tooling['fallback'], 'status')
        self.assertTrue(tooling['verified'])
        self.assertTrue((self.root / 'snapshot.json').exists())

    def test_check_runs_forbidden_uses_actions(self):
        def gh(*args):
            if len(args) > 1 and 'check-runs' in args[1]:
                exc = subprocess.CalledProcessError(1, args)
                exc.output = b''
                exc.stderr = b'gh: HTTP 403: Resource not accessible by integration\n'
                raise exc
            if len(args) > 1 and args[1].endswith('/status'):
                exc = subprocess.CalledProcessError(1, args)
                exc.output = b''
                exc.stderr = b'gh: HTTP 403: Resource not accessible by integration\n'
                raise exc
            if len(args) > 1 and 'actions/runs' in args[1]:
                run = {'id': 9, 'name': 'build-and-test', 'head_sha': 'a' * 40,
                       'status': 'completed', 'conclusion': 'success', 'html_url': 'https://example.test/run'}
                return json.dumps([{'workflow_runs': [run]}]).encode()
            return self.response(*args)

        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=gh):
            m.collect('o/r', 1, self.root)
        tooling = json.loads((self.root / 'ci-tooling.json').read_text())
        self.assertEqual(tooling['fallback'], 'actions')
        self.assertTrue(tooling['verified'])
        checks = json.loads((self.root / 'checks.json').read_text())
        self.assertEqual(checks[0]['check_runs'][0]['name'], 'build-and-test')

    def test_check_runs_forbidden_uses_pr_checks(self):
        def gh(*args):
            if len(args) > 1 and ('check-runs' in args[1] or args[1].endswith('/status') or 'actions/runs' in args[1]):
                exc = subprocess.CalledProcessError(1, args)
                exc.output = b''
                exc.stderr = b'gh: HTTP 403: Resource not accessible by integration\n'
                raise exc
            return self.response(*args)

        def gh_result(*args):
            if args[:2] == ('pr', 'checks'):
                body = b'[{"name":"build-and-test","state":"SUCCESS","bucket":"pass","link":"https://example.test/check"}]'
                return 0, body, b''
            return 1, b'', b'unexpected'

        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=gh), \
                patch.object(m, 'gh_result', side_effect=gh_result):
            m.collect('o/r', 1, self.root)
        tooling = json.loads((self.root / 'ci-tooling.json').read_text())
        self.assertEqual(tooling['fallback'], 'gh pr checks')
        self.assertTrue(tooling['verified'])
        checks = json.loads((self.root / 'checks.json').read_text())
        self.assertEqual(checks[0]['check_runs'][0]['conclusion'], 'success')

    def test_ci_unreadable_still_snapshots(self):
        def gh(*args):
            if len(args) > 1 and ('check-runs' in args[1] or '/statuses?' in args[1] or args[1].endswith('/status') or 'actions/runs' in args[1]):
                exc = subprocess.CalledProcessError(1, args)
                exc.output = b''
                exc.stderr = b'gh: HTTP 403: Resource not accessible by integration\n'
                raise exc
            return self.response(*args)

        def gh_result(*args):
            return 1, b'', b'gh: HTTP 403: Resource not accessible by integration\n'

        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=gh), \
                patch.object(m, 'gh_result', side_effect=gh_result):
            m.collect('o/r', 1, self.root)
        tooling = json.loads((self.root / 'ci-tooling.json').read_text())
        self.assertFalse(tooling['verified'])
        self.assertIn('HTTP 403 commits/{sha}/check-runs', tooling['errors'])
        self.assertTrue((self.root / 'snapshot.json').exists())
        self.assertEqual((self.root / 'PR_FILES.txt').read_text(), 'new\nold\n')

    def test_graphql_error_invalidates_old_snapshot(self):
        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', return_value=b'[{"errors":["denied"]}]'):
            with self.assertRaises(ValueError):
                m.collect('o/r', 1, self.root)
        self.assertFalse((self.root / 'snapshot.json').exists())


if __name__ == '__main__':
    unittest.main()
