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
        text = ' '.join(str(arg) for arg in args)
        if args[:2] == ('run', 'list'):
            return (
                b'[{"databaseId":7,"name":"CI","status":"completed","conclusion":"success",'
                b'"workflowName":"CI"}]'
            )
        if args[:2] == ('run', 'view'):
            return b'{"jobs":[{"name":"build-and-test","status":"completed","conclusion":"success"}]}'
        if args[0:2] == ('api', 'graphql') and 'statusCheckRollup' in text:
            oid = 'a' * 40
            return (
                '{"data":{"repository":{"pullRequest":{"commits":{"nodes":[{"commit":'
                '{"oid":"%s","statusCheckRollup":{"state":"SUCCESS"}}}]}}}}}' % oid
            ).encode()
        if args[0:2] == ('api', 'graphql'):
            return b'[{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[]}}}}}]'
        if 'application/vnd.github.diff' in args:
            return b'diff'
        if len(args) > 1 and '/files?' in args[1]:
            return b'[[{"filename":"new","previous_filename":"old"}]]'
        return b'[[]]'

    def test_collect_and_race(self):
        calls = []

        def record(*args):
            calls.append(args)
            return self.response(*args)

        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=record):
            result = m.collect('o/r', 1, self.root)
        self.assertEqual(result, self.snapshot)
        self.assertEqual((self.root / 'PR_FILES.txt').read_text(), 'new\nold\n')
        actions = json.loads((self.root / 'actions.json').read_text())
        self.assertIsNone(actions['error'])
        self.assertEqual(actions['runs'][0]['jobs'][0]['name'], 'build-and-test')
        rollup = json.loads((self.root / 'rollup.json').read_text())
        self.assertEqual(rollup['state'], 'SUCCESS')
        self.assertFalse(any('check-runs' in str(arg) or 'check-suites' in str(arg) for call in calls for arg in call))
        self.assertTrue(any(call[:2] == ('run', 'list') for call in calls))
        changed = dict(self.pr, head={'sha': 'c' * 40})
        with patch.object(m, 'pr', side_effect=[self.pr, changed]), patch.object(m, 'gh', side_effect=self.response):
            with self.assertRaises(ValueError):
                m.collect('o/r', 1, self.root)
        self.assertFalse((self.root / 'snapshot.json').exists())

    def test_ci_read_failure_still_snapshots(self):
        def flaky(*args):
            text = ' '.join(str(arg) for arg in args)
            if (args[:2] == ('run', 'list') or '/statuses?' in text
                    or (args[:2] == ('api', 'graphql') and 'statusCheckRollup' in text)):
                raise subprocess.CalledProcessError(1, 'gh', stderr=b'HTTP 403 Forbidden')
            return self.response(*args)

        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=flaky):
            result = m.collect('o/r', 1, self.root)
        self.assertEqual(result['head'], 'a' * 40)
        actions = json.loads((self.root / 'actions.json').read_text())
        rollup = json.loads((self.root / 'rollup.json').read_text())
        self.assertEqual(actions['error'], '403')
        self.assertEqual(rollup['error'], '403')
        self.assertEqual(json.loads((self.root / 'statuses.json').read_text()), [[]])
        self.assertTrue((self.root / 'snapshot.json').exists())

    def test_failed_run_reads_log(self):
        def failed(*args):
            if args[:2] == ('run', 'list'):
                return (
                    b'[{"databaseId":9,"name":"CI","status":"completed","conclusion":"failure",'
                    b'"workflowName":"CI"}]'
                )
            if args[:2] == ('run', 'view') and '--log-failed' in args:
                return b'boom\n'
            if args[:2] == ('run', 'view'):
                return b'{"jobs":[{"name":"test","status":"completed","conclusion":"failure"}]}'
            return self.response(*args)

        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', side_effect=failed):
            m.collect('o/r', 1, self.root)
        actions = json.loads((self.root / 'actions.json').read_text())
        self.assertEqual(actions['runs'][0]['log_failed_tail'], 'boom')
        self.assertEqual(actions['runs'][0]['jobs'][0]['conclusion'], 'failure')

    def test_graphql_error_invalidates_old_snapshot(self):
        with patch.object(m, 'pr', return_value=self.pr), patch.object(m, 'gh', return_value=b'[{"errors":["denied"]}]'):
            with self.assertRaises(ValueError):
                m.collect('o/r', 1, self.root)
        self.assertFalse((self.root / 'snapshot.json').exists())


if __name__ == '__main__':
    unittest.main()
