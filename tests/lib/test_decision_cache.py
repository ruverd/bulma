import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[2] / 'skills/bulma/scripts/decision_cache.py'
spec = importlib.util.spec_from_file_location('decision_cache', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CacheTest(unittest.TestCase):
    def key(self, **changes):
        args = dict(hook={'id': 'lstm.verify'}, request={'state': 'bound code'},
                    thresholds={'true': .9}, doc={'power': 'balanced', 'model': 'test'},
                    graph_answers={}, context={'repo': 'o/r', 'sha': 'a', 'evidence': 'digest'}, policy='v1')
        args.update(changes)
        return m.cache_key(**args)

    def test_requires_identity_and_excludes_live_gates(self):
        self.assertIsNotNone(self.key())
        self.assertIsNone(self.key(context={'repo': 'o/r'}))
        for hook in ('qa.gate', 'policy.ask', 'entry.next_step', 'entry.route'):
            self.assertIsNone(self.key(hook={'id': hook}))
        self.assertIsNone(self.key(doc={'power': 'balanced', 'model': 'test', 'truncated': True}))
        with patch.dict(os.environ, {'BULMA_JEV_CACHE': '0'}):
            self.assertIsNone(self.key())

    def test_all_decision_inputs_invalidate(self):
        for changes in ({'policy': 'v2'}, {'request': {'state': 'other'}},
                        {'thresholds': {'true': .8}}, {'graph_answers': {'true': 'no'}},
                        {'context': {'repo': 'o/r', 'sha': 'b', 'evidence': 'digest'}},
                        {'doc': {'power': 'bold', 'model': 'test'}},
                        {'doc': {'power': 'balanced', 'model': 'other'}}):
            self.assertNotEqual(self.key(), self.key(**changes))

    def test_expiry_corruption_and_write_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = self.key()
            with patch.object(m.time, 'time', return_value=1000):
                m.write(tmp, key, {'answers': {'true': 'yes'}})
                self.assertIsNotNone(m.read(tmp, key))
            with patch.object(m.time, 'time', return_value=1301):
                self.assertIsNone(m.read(tmp, key))
            (Path(tmp) / (key + '.json')).write_text('broken')
            self.assertIsNone(m.read(tmp, key))
            blocked = Path(tmp) / 'file'
            blocked.write_text('not a directory')
            m.write(blocked, key, {})


class CallerTest(unittest.TestCase):
    def test_ask_one_reuses_without_network_or_duplicate_usage(self):
        sys.path.insert(0, str(SCRIPT.parent))
        core_spec = importlib.util.spec_from_file_location('core_cache_test', SCRIPT.parent / 'bulma.py')
        core = importlib.util.module_from_spec(core_spec)
        core_spec.loader.exec_module(core)
        fixtures = SCRIPT.parents[3] / 'tests/fixtures/bulma'
        response = json.loads((fixtures / 'replay-fd-triage.json').read_text())
        hook = core.load_catalog()['fd.triage']
        state = json.loads((fixtures / 'state-fd-triage.json').read_text())
        context = {'repo': 'o/r', 'sha': 'head', 'evidence': 'sources-digest'}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'BULMA_HOME': tmp, 'BULMA_JEV_CACHE': '1'}):
            with patch.object(core, 'post_json', return_value=response) as remote:
                request, thresholds, doc = core.prepare(hook, state, {}, 'balanced', core.DEFAULT_MODEL, {})
                first, rows, code = core.ask_one(hook, request, thresholds, doc, None, {}, context)
                self.assertEqual(code, 0)
                request, thresholds, doc = core.prepare(hook, state, {}, 'balanced', core.DEFAULT_MODEL, {})
                second, cached_rows, code = core.ask_one(hook, request, thresholds, doc, None, {}, context)
                self.assertEqual(remote.call_count, 1)
                self.assertEqual(first['answers'], second['answers'])
                self.assertNotEqual(first['decision_id'], second['decision_id'])
                self.assertEqual(second['usage']['input_tokens'], 0)
                self.assertTrue(all(r['note'] == 'cache_hit' for r in cached_rows))
                request, thresholds, doc = core.prepare(hook, state, {}, 'balanced', core.DEFAULT_MODEL, {})
                core.ask_one(hook, request, thresholds, doc, None, {}, dict(context, sha='new'))
                self.assertEqual(remote.call_count, 2)


if __name__ == '__main__':
    unittest.main()
