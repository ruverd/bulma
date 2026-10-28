import argparse
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'skills/bulma/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('jev_reliability', SCRIPTS / 'bulma.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class ReliabilityTest(unittest.TestCase):
    def setUp(self):
        self.catalog = m.load_catalog()
        self.hook = self.catalog['fd.triage']
        self.state = json.loads((ROOT / 'tests/fixtures/bulma/state-fd-triage.json').read_text())
        self.response = json.loads((ROOT / 'tests/fixtures/bulma/replay-fd-triage.json').read_text())

    def row(self, **updates):
        row = dict.fromkeys(m.TSV_COLUMNS, '')
        row.update(hook='policy.ask', question='important', question_type='noul', answer='0.1',
                   confidence='0.1', graph_answer='no', outcome='confirmed', act_at='0.8',
                   model=m.DEFAULT_MODEL, policy_id='policy-a', source='live', acted='true')
        row.update(updates)
        return row

    def ask(self, response):
        request, thresholds, doc = m.prepare(self.hook, self.state, {}, 'balanced', m.DEFAULT_MODEL, {})
        with tempfile.TemporaryDirectory() as tmp, patch.dict(m.os.environ, {'BULMA_HOME': tmp}), \
                patch.object(m, 'post_json', return_value=response):
            return m.ask_one(self.hook, request, thresholds, doc, None, {}, {})

    def test_malformed_nouls_never_act(self):
        for raw in ({}, None, [], 'no', {'noul': None}, {'noul': True}, {'noul': '0.9'},
                    {'noul': -0.1}, {'noul': 10 ** 1000}, {'noul': 1.1}, {'noul': float('nan')}, {'noul': float('inf')}):
            with self.subTest(raw=raw):
                self.assertFalse(m.judge({'type': 'noul'}, raw, .8, 'balanced')['act'])
        for value, decisive in ((0, 'no'), (.1, 'no'), (.5, 'undecided'), (.9, 'yes'), (1, 'yes')):
            result = m.judge({'type': 'noul'}, {'noul': value}, .8, 'balanced')
            self.assertEqual(result['decisive'], decisive)
            self.assertEqual(result['act'], decisive != 'undecided')

    def test_noul_tie_never_authorizes_a_decision(self):
        self.assertFalse(m.judge({'type': 'noul'}, {'noul': .5}, .5, 'balanced')['act'])

    def test_missing_batch_state_prevents_every_network_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'batch.json'
            batch.write_text(json.dumps([
                {'hook': 'fd.triage', 'state': self.state},
                {'hook': 'policy.ask', 'state': {'fork': 'incomplete'}},
            ]))
            with patch.dict(m.os.environ, {'BULMA_HOME': tmp}), patch.object(m, 'post_json') as remote:
                with redirect_stderr(io.StringIO()):
                    code = m.main(['ask-many', '--batch', str(batch), '--bulma-root', tmp])
                self.assertEqual(code, 4)
                remote.assert_not_called()
                self.assertFalse(m.ledger_path(tmp).exists())

    def test_timeout_command_persists_only_requested_override(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(m.os.environ, {'BULMA_HOME': tmp}), redirect_stdout(io.StringIO()):
            m.main(['timeout', '4'])
            m.main(['timeout', '2', '--hook', 'entry.route'])
            self.assertEqual(m.load_config(), {'timeout_seconds': 4, 'timeout_by_hook': {'entry.route': 2}})
            for value in ('0', '-1', 'nan', 'inf'):
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(m.main(['timeout', value]), 4)
            self.assertEqual(m.load_config()['timeout_seconds'], 4)

    def test_choices_require_valid_enum_and_confidence(self):
        question = {'type': 'choice', 'criteria': {'one': 'First', 'two': 'Second'}}
        for raw in ({'choice': 'other', 'confidence': 1}, {'choice': 'one'},
                    {'choice': ['one'], 'confidence': 1}, {'choice': 'one', 'confidence': True},
                    {'choice': 'one', 'confidence': float('nan')}):
            self.assertFalse(m.judge(question, raw, .8, 'balanced')['act'])
        self.assertTrue(m.judge(question, {'choice': 'one', 'confidence': .9}, .8, 'balanced')['act'])

    def test_invalid_response_envelopes_fall_back(self):
        for response in (None, [], {}, {'answers': []}, {'answers': {'path': {}}}):
            with self.subTest(response=response):
                doc, rows, code = self.ask(response)
                self.assertEqual(code, 0)
                self.assertTrue(all(not answer['act'] for answer in doc['answers'].values()))
                self.assertTrue(all(row['note'] == 'invalid_answer' for row in rows))
        response = dict(self.response, answers=dict(self.response['answers'], path={'choice': 'invented', 'confidence': 1}))
        doc, rows, _ = self.ask(response)
        self.assertFalse(doc['answers']['path']['act'])
        self.assertTrue(doc['answers']['work_kind']['act'])
        self.assertEqual(next(row['note'] for row in rows if row['question'] == 'path'), 'invalid_answer')

    def test_invalid_cached_response_is_replaced(self):
        request, thresholds, doc = m.prepare(self.hook, self.state, {}, 'balanced', m.DEFAULT_MODEL, {})
        with tempfile.TemporaryDirectory() as tmp, patch.dict(m.os.environ, {'BULMA_HOME': tmp}), \
                patch.object(m.decision_cache, 'read', return_value={'answers': {'path': {}}}), \
                patch.object(m, 'post_json', return_value=self.response) as remote:
            result, _, _ = m.ask_one(self.hook, request, thresholds, doc, None, {}, {'repo': 'o/r', 'evidence': 'digest'})
            self.assertFalse(result['cache_hit'])
            remote.assert_called_once()

    def test_invalid_answers_are_not_cached(self):
        request, thresholds, doc = m.prepare(self.hook, self.state, {}, 'balanced', m.DEFAULT_MODEL, {})
        response = dict(self.response, answers=dict(self.response['answers'], path={}))
        with tempfile.TemporaryDirectory() as tmp, patch.dict(m.os.environ, {'BULMA_HOME': tmp}), \
                patch.object(m, 'post_json', return_value=response), patch.object(m.decision_cache, 'write') as write:
            m.ask_one(self.hook, request, thresholds, doc, None, {}, {'repo': 'o/r', 'evidence': 'digest'})
            write.assert_not_called()

    def test_missing_state_rejected_and_irrelevant_fields_removed(self):
        for state in ({}, dict(self.state, topology=None)):
            if state:
                # Null is explicit unknown; absence is a malformed recipe.
                m.prepare(self.hook, state, {}, 'balanced', m.DEFAULT_MODEL, {})
            else:
                with self.assertRaises(m.BulmaError) as caught:
                    m.prepare(self.hook, state, {}, 'balanced', m.DEFAULT_MODEL, {})
                self.assertEqual(caught.exception.code, 4)
        state = dict(self.state, unrelated='x' * 100000)
        request, _, doc = m.prepare(self.hook, state, {}, 'balanced', m.DEFAULT_MODEL, {})
        self.assertNotIn('unrelated', request['state'])
        self.assertFalse(doc['truncated'])
        hook = self.catalog['entry.route']
        state = {'args': 'review', 'world': {}, 'user_login': 'user', 'pr': {'number': 5}}
        request, _, _ = m.prepare(hook, state, {}, 'balanced', m.DEFAULT_MODEL, {})
        self.assertEqual(request['state']['pr']['number'], 5)

    def test_truncation_prevents_inference(self):
        state = dict(self.state, ticket_body='x' * 10000)
        request, thresholds, doc = m.prepare(self.hook, state, {}, 'balanced', m.DEFAULT_MODEL, {})
        with patch.object(m, 'post_json') as remote:
            result, rows, code = m.ask_one(self.hook, request, thresholds, doc, None, {}, {})
            remote.assert_not_called()
            self.assertEqual(code, 0)
            self.assertTrue(all(not answer['act'] for answer in result['answers'].values()))
            self.assertTrue(all(row['note'] == 'truncated' for row in rows))

    def test_noul_calibration_handles_both_tails_and_legacy_rows(self):
        for p, label in ((.1, 'no'), (.9, 'yes')):
            row = self.row(answer=str(p), confidence=str(p), graph_answer=label, question_type='')
            prediction, certainty = m.row_evaluation(row, self.catalog)
            self.assertEqual(prediction, label)
            self.assertAlmostEqual(certainty, .9)
            self.assertEqual(m.suggest_threshold([row] * 20, .8, self.catalog), '0.50')
        self.assertIsNone(m.row_evaluation(self.row(answer='0.5'), self.catalog))
        self.assertEqual(m.graph_label('false', 'noul'), 'no')

    def test_threshold_requires_outcomes_not_heuristic_agreement(self):
        self.assertEqual(m.suggest_threshold([self.row(outcome='')] * 30, .8, self.catalog), 'need >=20 outcomes')
        rows = [self.row(answer='.6', confidence='.6', outcome='reversed')] * 3
        rows += [self.row(answer='.1', confidence='.1')] * 20
        self.assertEqual(m.suggest_threshold(rows, .8, self.catalog), '0.65')
        self.assertEqual(m.suggest_threshold([self.row(outcome='reversed')] * 20, .8, self.catalog), 'no supported threshold')
        self.assertEqual(m.suggest_threshold([self.row(note='invalid_answer')] * 20, .8, self.catalog), 'need >=20 outcomes')
        self.assertEqual(m.suggest_threshold([self.row(note='cache_hit | checked')] * 20, .8, self.catalog), 'need >=20 outcomes')

    def test_report_separates_model_policy_and_provenance(self):
        rows = []
        for updates in ({}, {'model': 'other'}, {'policy_id': 'policy-b'}, {'source': 'replay'}):
            rows += [self.row(**updates, decision_id=str(len(rows) + i)) for i in range(10)]
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            path = m.ledger_path(tmp)
            path.parent.mkdir(parents=True)
            m.write_rows(path, rows)
            args = argparse.Namespace(bulma_root=tmp, repo_only=True, since=None, hook=None)
            with redirect_stdout(output):
                m.cmd_report(args)
        text = output.getvalue()
        self.assertEqual(text.count('model='), 4)
        self.assertEqual(text.count('need >=20 outcomes'), 3)
        output = io.StringIO()
        with patch.object(m, 'read_rows', return_value=rows), redirect_stdout(output):
            args.model = 'other'
            args.policy_id = 'policy-a'
            args.source = 'live'
            m.cmd_report(args)
        self.assertEqual(output.getvalue().count('model='), 1)
        self.assertIn('model=other', output.getvalue())
        self.assertIn('replay only', text)
        self.assertIn('100%', text)
        self.assertIn('unlabeled outcomes are unknown', text)

    def test_outcome_notes_keep_labels_usable(self):
        self.assertIsNotNone(m.row_evaluation(self.row(note='verified by test'), self.catalog))
        self.assertIsNone(m.row_evaluation(self.row(note='invalid_answer | verified'), self.catalog))

    def test_deadline_is_shared_between_retries(self):
        now = [0.0]
        timeouts = []
        def fail(request, timeout):
            timeouts.append(timeout)
            now[0] += .4
            raise urllib.error.URLError('offline')
        def sleep(seconds):
            now[0] += seconds
        with patch.object(m, 'api_key', return_value='test'), \
                patch.object(m.time, 'monotonic', side_effect=lambda: now[0]), \
                patch.object(m.time, 'sleep', side_effect=sleep), \
                patch.object(m.urllib.request, 'urlopen', side_effect=fail):
            with self.assertRaisesRegex(m.BulmaError, 'decision timeout'):
                m.post_json('/systemone', {}, timeout=3)
        self.assertEqual(len(timeouts), 2)
        self.assertAlmostEqual(timeouts[0], 3)
        self.assertAlmostEqual(timeouts[1], 1.6)
        self.assertLessEqual(now[0], 3)

    def test_retry_after_cannot_exceed_budget(self):
        error = urllib.error.HTTPError('url', 429, 'rate limit', {'retry-after': '100'}, None)
        with patch.object(m, 'api_key', return_value='test'), patch.object(m.time, 'sleep') as sleep, \
                patch.object(m.urllib.request, 'urlopen', side_effect=error) as remote:
            with self.assertRaisesRegex(m.BulmaError, 'decision timeout'):
                m.post_json('/systemone', {}, timeout=3)
            self.assertEqual(remote.call_count, 1)
            sleep.assert_not_called()

    def test_late_and_malformed_json_responses_are_rejected(self):
        for payload in (b'[]', b'not-json', b'\xff'):
            with patch.object(m, 'api_key', return_value='test'), patch.object(m.urllib.request, 'urlopen') as remote:
                remote.return_value.__enter__.return_value.read.return_value = payload
                with self.assertRaises(m.BulmaError):
                    m.post_json('/systemone', {}, timeout=3)
        with patch.object(m, 'api_key', return_value='test'), patch.object(m.urllib.request, 'urlopen') as remote, \
                patch.object(m.time, 'monotonic', side_effect=[0, 0, 4]):
            remote.return_value.__enter__.return_value.read.return_value = b'{}'
            with self.assertRaisesRegex(m.BulmaError, 'decision timeout'):
                m.post_json('/systemone', {}, timeout=3)

    def test_timeout_and_model_defaults_and_overrides(self):
        self.assertEqual(m.DEFAULT_MODEL, 'jev-1.14.0')
        self.assertEqual(m.decision_timeout('entry.route', {}), 3)
        self.assertEqual(m.decision_timeout('fd.triage', {}), 8)
        self.assertEqual(m.decision_timeout('entry.route', {'timeout_seconds': 4}), 4)
        self.assertEqual(m.decision_timeout('entry.route', {'timeout_seconds': 4, 'timeout_by_hook': {'entry.route': 2}}), 2)
        for value in (0, -1, True, '3', float('nan'), float('inf')):
            with self.assertRaises(m.BulmaError):
                m.decision_timeout('entry.route', {'timeout_seconds': value})
        for key in ('policy_id', 'question_type', 'source'):
            self.assertIn(key, m.TSV_COLUMNS)


if __name__ == '__main__':
    unittest.main()
