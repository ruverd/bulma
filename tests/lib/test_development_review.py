import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('development_review', ROOT / 'skills/bulma-host/scripts/development-review.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

IDENTITY = {'model': 'fixture-v2', 'family': 'fixture-b', 'source': 'runtime'}
AUTHOR = {'model': 'author-v1', 'family': 'fixture-a', 'source': 'system'}
FINDING = {'id': 'missing-case', 'axis': 'quality', 'message': 'Missing boundary case', 'evidence': 'test.py:1'}
ADAPTER = '''import json, sys, time
from pathlib import Path
p = json.load(sys.stdin)
cfg = json.loads(Path(sys.argv[1]).read_text())
with open(sys.argv[2], 'a') as f: f.write(json.dumps(p) + '\\n')
if p['operation'] == 'discover':
    print(json.dumps({'candidates': cfg['candidates']}))
else:
    for event in cfg['events']:
        print(json.dumps(event), flush=True)
    if cfg.get('malformed'): print('not json', flush=True)
    if cfg.get('mutate'): (Path(p['repo']) / 'product').write_text('changed by adapter')
    if cfg.get('overflow'): print('x' * cfg['overflow'], flush=True)
    time.sleep(cfg.get('sleep', 0))
    sys.exit(cfg.get('exit', 0))
'''


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.test')
        self.git('config', 'user.name', 'Fixture')
        (self.repo / 'product').write_text('before\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        base = self.git('rev-parse', 'HEAD')
        (self.repo / 'product').write_text('after\n')
        self.git('commit', '-qam', 'change')
        self.head = self.git('rev-parse', 'HEAD')
        self.home = self.root / 'home'
        self.home.mkdir()
        self.request = dict(round_id='job-ticket-1-review-1', head=self.head, base=base,
                            task='Change product', spec='Return after', evidence=['unit: passed'],
                            context=['No product edits.'], implementation=[AUTHOR])
        self.adapter = self.root / 'adapter.py'
        self.adapter.write_text(ADAPTER)
        self.control = self.root / 'control.json'
        self.calls = self.root / 'calls.jsonl'
        self.config = self.root / 'config.json'
        self.data = {'candidates': [{'id': 'other', 'identity': IDENTITY}],
                     'events': [{'type': 'identity', 'identity': IDENTITY}, self.result()]}
        self.config.write_text(json.dumps({'version': 1,
            'adapter': [sys.executable, str(self.adapter), str(self.control), str(self.calls)],
            'candidates': ['other'], 'timeout_seconds': 1, 'discovery_timeout_seconds': 2,
            'read_only': True}))

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def result(self, **kw):
        return dict(type='result', head=self.head, spec_verdict='pass', quality_verdict='pass', **kw)

    def configure(self):
        (self.home / 'memory.md').write_text('## Preferences\n- development_review: ' + str(self.config) + '\n')

    def run_review(self):
        self.control.write_text(json.dumps(self.data))
        return m.execute(self.repo, self.home, self.request)

    def test_no_config_uses_existing_worker(self):
        result = self.run_review()
        self.assertEqual(result['mode'], 'default')
        self.assertEqual(result['action'], 'spawn_worker')
        self.assertFalse(self.calls.exists())

    def test_alternative_pinned_payload_and_idempotent_round(self):
        self.configure()
        result = self.run_review()
        self.assertEqual(result['mode'], 'alternative')
        self.assertTrue(result['diversity_verified'])
        self.assertEqual(result['action'], 'complete')
        self.assertEqual(result['executor']['model'], 'fixture-v2')
        calls = [json.loads(s) for s in self.calls.read_text().splitlines()]
        self.assertEqual([p['operation'] for p in calls], ['discover', 'review'])
        self.assertIn('+after', calls[1]['diff'])
        self.assertEqual(calls[1]['head'], self.head)
        self.assertIn('spec_verdict', calls[1]['contract'])
        self.assertEqual(calls[1]['context'], self.request['context'])
        self.assertEqual(self.run_review(), result)
        self.assertEqual(len(self.calls.read_text().splitlines()), 2)

    def test_same_or_unknown_identity_never_claims_diversity(self):
        self.configure()
        for identity in (AUTHOR, {}, {'model': 'auto', 'family': 'fixture-b', 'source': 'runtime'}):
            with self.subTest(identity=identity):
                self.request['round_id'] += 'x'
                self.data['candidates'][0]['identity'] = identity
                result = self.run_review()
                self.assertEqual(result['action'], 'spawn_worker')
                self.assertFalse(result['diversity_verified'])
        self.assertTrue(all(json.loads(s)['operation'] == 'discover' for s in self.calls.read_text().splitlines()))

    def test_unknown_implementer_prevents_diversity_selection(self):
        self.configure()
        self.request['implementation'] = [{}]
        self.assertEqual(self.run_review()['action'], 'spawn_worker')

    def test_quota_staleness_and_candidate_order(self):
        self.configure()
        now = m.timestamp()
        self.data['candidates'] = [dict(id='unauthorized', identity=IDENTITY),
            dict(id='other', identity=IDENTITY, quota={'available': False, 'checked_at': now})]
        self.assertEqual(self.run_review()['action'], 'spawn_worker')
        self.request['round_id'] += 'x'
        self.data['candidates'][1]['quota']['checked_at'] = '2000-01-01T00:00:00+00:00'
        self.assertEqual(self.run_review()['action'], 'complete')

    def test_operational_failure_only_one_attempt_then_fallback(self):
        self.configure()
        for reason in ('auth', 'quota', 'unavailable', 'timeout'):
            with self.subTest(reason=reason):
                self.request['round_id'] += 'x'
                self.data['events'] = [{'type': 'error', 'reason': reason}]
                result = self.run_review()
                self.assertEqual(result['mode'], 'fallback')
                self.assertEqual(result['reason'], reason)
                self.assertEqual(result['action'], 'spawn_worker')
                self.assertEqual(self.run_review(), result)
        self.assertEqual(sum(json.loads(s)['operation'] == 'review' for s in self.calls.read_text().splitlines()), 4)

    def test_timeout_preserves_findings_and_fallback_cannot_erase_them(self):
        self.configure()
        self.data['events'] = [{'type': 'finding', 'finding': FINDING}]
        self.data['sleep'] = 2
        result = self.run_review()
        self.assertEqual(result['reason'], 'timeout')
        self.assertEqual(result['findings'], [FINDING])
        result = m.finish(self.repo, self.home, self.request, self.result(identity=AUTHOR))
        self.assertEqual(result['quality_verdict'], 'fail')
        self.assertEqual(result['action'], 'complete')
        self.assertEqual(result['mode'], 'fallback')
        self.assertEqual(result['executor'], AUTHOR)

    def test_negative_verdict_never_retries_for_approval(self):
        self.configure()
        self.data['events'][-1]['spec_verdict'] = 'fail'
        self.data['exit'] = 1
        result = self.run_review()
        self.assertEqual(result['action'], 'complete')
        self.assertEqual(result['spec_verdict'], 'fail')
        self.assertEqual(result['mode'], 'alternative')

    def test_malformed_or_wrong_sha_never_pass(self):
        self.configure()
        for change in ('malformed', 'sha', 'identity', 'missing', 'duplicate'):
            with self.subTest(change=change):
                self.request['round_id'] += 'x'
                self.data = {'candidates': [{'id': 'other', 'identity': IDENTITY}],
                    'events': [{'type': 'identity', 'identity': IDENTITY}, self.result()]}
                if change == 'malformed': self.data['malformed'] = True
                if change == 'sha': self.data['events'][-1]['head'] = 'bad'
                if change == 'identity': self.data['events'][0]['identity'] = AUTHOR
                if change == 'missing': self.data['events'].pop()
                if change == 'duplicate': self.data['events'].append(self.result())
                self.assertEqual(self.run_review()['action'], 'spawn_worker')

    def test_bad_config_and_missing_adapter_fallback(self):
        self.configure()
        self.config.write_text('{}')
        self.assertEqual(self.run_review()['reason'], 'invalid_config')
        self.request['round_id'] += 'x'
        self.config.write_text(json.dumps({'version': 1, 'adapter': ['/missing/binary'],
            'candidates': ['other'], 'read_only': True}))
        self.assertEqual(self.run_review()['reason'], 'unavailable')

    def test_memory_precedence_and_explicit_off(self):
        self.configure()
        other = self.root / 'worktree'
        self.git('worktree', 'add', '-q', '-b', 'other', str(other))
        shared = m.paths(self.repo, self.home)[-1]
        shared.parent.mkdir(parents=True, exist_ok=True)
        shared.write_text('## Preferences\n- development_review: off\n')
        self.assertEqual(m.preference(other, self.home), 'off')
        local = m.paths(other, self.home)[-1]
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text('## Preferences\n- development_review: ' + str(self.config) + '\n')
        self.assertEqual(m.preference(other, self.home), str(self.config))

    def test_changed_snapshot_or_round_payload_rejected(self):
        self.configure()
        self.run_review()
        self.request['task'] = 'Changed task'
        with self.assertRaises(ValueError): self.run_review()
        (self.repo / 'product').write_text('dirty\n')
        with self.assertRaises(ValueError): self.run_review()

    def test_discovery_and_execution_may_have_different_metadata_sources(self):
        self.configure()
        self.data['events'][0]['identity'] = dict(IDENTITY, source='system')
        result = self.run_review()
        self.assertEqual(result['action'], 'complete')
        self.assertTrue(result['diversity_verified'])
        self.assertEqual(result['executor']['source'], 'system')

    def test_no_config_preserves_dirty_workflow(self):
        (self.repo / 'product').write_text('uncommitted')
        self.assertEqual(self.run_review()['mode'], 'default')

    def test_candidate_order_and_single_attempt_with_multiple_candidates(self):
        self.configure()
        cfg = json.loads(self.config.read_text())
        cfg['candidates'] = ['first', 'other']
        self.config.write_text(json.dumps(cfg))
        self.data['candidates'].append(dict(id='first', identity=IDENTITY))
        self.data['events'] = [{'type': 'error', 'reason': 'auth'}]
        self.data['exit'] = 1
        result = self.run_review()
        self.assertEqual(result['candidate']['id'], 'first')
        self.assertEqual(result['reason'], 'auth')
        calls = [json.loads(s) for s in self.calls.read_text().splitlines()]
        self.assertEqual([c.get('candidate') for c in calls if c['operation'] == 'review'], ['first'])
        self.request['round_id'] += 'x'
        self.data['candidates'][-1]['access'] = {'available': False, 'checked_at': m.timestamp()}
        self.assertEqual(self.run_review()['candidate']['id'], 'other')

    def test_unknown_or_future_quota_does_not_fabricate_unavailability(self):
        self.configure()
        for checked_at in (None, 'bad', '2999-01-01T00:00:00+00:00', '2026-11-17T00:00:00'):
            self.request['round_id'] += 'x'
            self.data['candidates'][0]['quota'] = {'available': False, 'checked_at': checked_at}
            self.assertEqual(self.run_review()['action'], 'complete')

    def test_interrupted_round_keeps_partial_findings_without_retry(self):
        self.configure()
        self.data['events'] = [{'type': 'finding', 'finding': FINDING}]
        result = self.run_review()
        receipt = Path(result['receipt'])
        result['action'] = 'running'
        receipt.write_text(json.dumps(result))
        count = len(self.calls.read_text().splitlines())
        result = self.run_review()
        self.assertEqual(result['reason'], 'interrupted')
        self.assertEqual(result['findings'], [FINDING])
        self.assertEqual(len(self.calls.read_text().splitlines()), count)
        (self.home / 'memory.md').write_text('## Preferences\n- development_review: off\n')
        self.assertEqual(self.run_review(), result)
        final = m.finish(self.repo, self.home, self.request, self.result(identity={}))
        self.assertEqual(final['quality_verdict'], 'fail')
        self.assertFalse(final['diversity_verified'])

    def test_invalid_fallback_cannot_complete(self):
        self.configure()
        self.data['events'] = [{'type': 'error', 'reason': 'quota'}]
        self.run_review()
        for result in (dict(self.result(), head='wrong'), dict(self.result(), spec_verdict='approved'),
                       self.result(findings=['bad'])):
            with self.assertRaises(ValueError):
                m.finish(self.repo, self.home, self.request, result)

    def test_findings_in_malformed_result_are_not_silently_dropped(self):
        self.configure()
        self.data['events'][-1]['findings'] = [FINDING]
        result = self.run_review()
        self.assertEqual(result['action'], 'spawn_worker')
        self.assertEqual(result['findings'], [FINDING])
        final = m.finish(self.repo, self.home, self.request, self.result())
        self.assertEqual(final['quality_verdict'], 'fail')

    def test_adapter_mutation_blocks_review(self):
        self.configure()
        self.data['mutate'] = True
        result = self.run_review()
        self.assertEqual(result['action'], 'blocked')
        self.assertEqual(result['reason'], 'snapshot_changed')

    def test_output_limit_and_discovery_commands_are_data(self):
        self.configure()
        self.data['candidates'][0]['adapter'] = ['/not/authorized']
        self.data['overflow'] = 64 * 1024
        original = m.LIMIT
        try:
            m.LIMIT = 16 * 1024
            result = self.run_review()
        finally:
            m.LIMIT = original
        self.assertEqual(result['action'], 'spawn_worker')
        self.assertEqual(result['reason'], 'output_limit')
        self.assertEqual(len(self.calls.read_text().splitlines()), 2)

    def test_config_in_git_is_rejected(self):
        self.configure()
        path = self.repo / 'local-config.json'
        path.write_text(self.config.read_text())
        self.git('add', '.')
        self.git('commit', '-qm', 'config')
        self.request['head'] = self.git('rev-parse', 'HEAD')
        (self.home / 'memory.md').write_text('## Preferences\n- development_review: ' + str(path) + '\n')
        result = self.run_review()
        self.assertEqual(result['reason'], 'invalid_config')
        self.assertFalse(self.calls.exists())

    def test_context_prompt_text_never_runs_as_shell(self):
        self.configure()
        marker = self.root / 'should-not-exist'
        self.request['task'] += ' $(touch ' + str(marker) + ') `exit 1`'
        result = self.run_review()
        self.assertEqual(result['action'], 'complete')
        self.assertFalse(marker.exists())

    def test_process_cleanup_failure_blocks_instead_of_spawning_another_worker(self):
        directory = self.root / 'cleanup'
        directory.mkdir()
        with patch.object(m.os, 'killpg', side_effect=PermissionError):
            _, reason = m.call([sys.executable, '-c', 'import time; time.sleep(5)'],
                               {}, directory, 'test', 0.05)
        self.assertEqual(reason, 'cleanup_failed')
        self.configure()
        discovery = json.dumps({'candidates': self.data['candidates']})
        with patch.object(m, 'call', side_effect=[(discovery, None), ('', reason)]):
            self.assertEqual(self.run_review()['action'], 'blocked')

    def test_cli_round_and_graph_limits(self):
        self.configure()
        self.control.write_text(json.dumps(self.data))
        path = self.root / 'request.json'
        path.write_text(json.dumps(self.request))
        output = subprocess.check_output([sys.executable, str(ROOT / 'skills/bulma-host/scripts/development-review.py'),
            '--repo', str(self.repo), '--home', str(self.home), '--request', str(path)], text=True)
        self.assertEqual(json.loads(output)['action'], 'complete')
        graph = (ROOT / 'skills/bulma-feature-delivery/GRAPH.md').read_text()
        self.assertIn('review_fix_loops: 2', graph)
        self.assertIn('plan_critic_loops: 1', graph)
        self.assertIn('| review | spec_verdict=pass and quality_verdict=pass | **tester** |', graph)


if __name__ == '__main__':
    unittest.main()
