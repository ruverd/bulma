import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'skills/bulma-bus/scripts'
sys.path.insert(0, str(SCRIPTS))
import improvement as m
import replay


class ImprovementTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        (self.repo / 'app').write_text('old')
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'start')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        self.evidence = self.root / 'proof.txt'
        self.evidence.write_text('observed behavior')
        self.directory = self.root / 'observations'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True,
                                       stderr=subprocess.DEVNULL)

    def outcome(self, run='r1', **overrides):
        return dict(dict(kind='outcome', run=run, task='task1', trial=1, variant='base',
                         workflow='a' * 64, configuration='config1', status='accepted',
                         scope='delivery', sha=self.sha, starting_sha=self.sha,
                         task_fingerprint='b' * 64,
                         environment='fixture-v1', evidence=[str(self.evidence)]), **overrides)

    def save(self, row):
        return m.record(self.repo, self.directory, row)

    def rows(self):
        return m.load(self.directory, self.repo)

    def test_identity_and_evidence_are_bound(self):
        self.save(self.outcome())
        self.save(self.outcome())
        self.assertEqual(len(self.rows()), 1)
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            self.save(self.outcome(task='another-task'))
        with self.assertRaisesRegex(ValueError, 'current head'):
            self.save(self.outcome('wrong-sha', sha='b' * 40))
        with self.assertRaisesRegex(ValueError, 'require evidence'):
            self.save(self.outcome('no-proof', evidence=[]))
        self.evidence.write_text('edited')
        result = m.report(self.rows())
        self.assertEqual(result['invalid_evidence_records'], 1)
        self.assertEqual(result['deliveries'][0]['outcomes'], {'unknown': 1})
        self.assertIsNone(result['deliveries'][0]['cost_per_accepted_run_usd'])

    def test_failure_cost_is_included_and_unknown_is_not_free(self):
        cost = dict(cost_kind='api_billed', cost_source='host-event-1')
        self.save(self.outcome(cost_usd=2, first_pass=True, **cost))
        self.save(self.outcome('r2', task='task2', status='rejected', cost_usd=3, **cost))
        totals = m.report(self.rows())['deliveries'][0]
        self.assertEqual(totals['cost_per_accepted_run_usd'], 5)
        self.assertEqual(totals['first_pass_samples'], 1)
        self.assertIsNone(totals['known_human_ms'])
        self.save(self.outcome('r3', task='task3', status='blocked'))
        totals = m.report(self.rows())['deliveries'][0]
        self.assertEqual(totals['runs'], 3)
        self.assertEqual(totals['known_cost_usd'], 5)
        self.assertIsNone(totals['cost_per_accepted_run_usd'])
        self.assertEqual(totals['cost_samples'], 2)
        for value in (True, -1, float('inf'), float('nan')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.save(self.outcome('invalid', cost_usd=value, **cost))
        with self.assertRaisesRegex(ValueError, 'estimates'):
            self.save(self.outcome('estimated', cost_usd=1, cost_source='estimate'))

    def test_metrics_reuse_existing_run_and_preserve_partial_coverage(self):
        metric = self.root / 'measurement.json'
        metric.write_text(json.dumps(dict(run='r1', sample_id='tester-1', graph='fd',
                                         node='tester', kind='active', duration_ms=234)))
        self.save(self.outcome(metrics=[str(metric)]))
        totals = m.report(self.rows())['deliveries'][0]
        self.assertEqual(totals['active_ms'], 234)
        self.assertEqual(totals['metric_samples'], 1)
        with self.assertRaisesRegex(ValueError, 'belong to this run'):
            self.save(self.outcome('other', metrics=[str(metric)]))
        with self.assertRaisesRegex(ValueError, 'duplicate metric'):
            self.save(self.outcome(metrics=[str(metric), str(metric)]))
        metric.unlink()
        totals = m.report(self.rows())['deliveries'][0]
        self.assertEqual(totals['runs_with_metrics'], 0)

    def test_distinct_tasks_and_verified_failure_opportunities(self):
        base = dict(kind='assessment', task='task1', variant='base', workflow='a' * 64,
                    configuration='config1', criterion='test-command', status='fail',
                    cause='repeated-discovery', prevention='Use the project test command',
                    counterexample='Expected TDD RED must remain allowed', method='human',
                    evidence=[str(self.evidence)])
        for run in ('r1', 'r2'):
            self.save(dict(base, run=run))
        self.assertEqual(m.report(self.rows())['process'][0]['candidates'], [])
        self.save(dict(base, run='r3', task='task2'))
        self.save(dict(base, run='r4', task='task3', method='model'))
        self.save(dict(base, run='r5', status='pass'))
        self.save(dict(base, run='r6', status='unknown'))
        self.save(dict(base, run='r6', status='unknown'))
        group = m.report(self.rows())['process'][0]
        self.assertEqual(group['observations'], 6)
        self.assertEqual(group['failure_rate'], .75)
        self.assertEqual(group['candidates'][0]['tasks'], ['task1', 'task2'])
        self.assertEqual(group['classifications']['unknown'], 1)

    def test_compare_keeps_failures_and_unmatched_trials(self):
        self.save(self.outcome())
        self.save(self.outcome('candidate1', variant='candidate', status='blocked'))
        self.save(self.outcome('candidate2', variant='candidate', task='extra'))
        result = m.compare(self.rows(), 'base', 'candidate')
        self.assertEqual(result['paired_trials'], 1)
        self.assertEqual(result['baseline_accepted_candidate_not'], 1)
        self.assertEqual(result['unmatched'], dict(base=0, candidate=1))
        self.assertIsNone(result['variants']['candidate']['cost_per_accepted_run_usd'])
        self.assertEqual(result['promotion'], 'not_evaluated')
        rows = self.rows()
        next(r for r in rows if r['run'] == 'candidate1')['environment'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'conditions'):
            m.compare(rows, 'base', 'candidate')
        self.evidence.unlink()
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            m.compare(self.rows(), 'base', 'candidate')

    def test_no_checkout_state_and_lookback_needs_no_review_observations(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            m.record(self.repo, self.repo / 'state', self.outcome())
        self.save(self.outcome())
        result = subprocess.run([sys.executable, str(ROOT / 'skills/bulma/scripts/lookback.py'),
                                 '--process', str(self.directory), '--repo', str(self.repo)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['deliveries'][0]['accepted_runs'], 1)

    def test_dirty_delivery_cannot_claim_head_acceptance(self):
        before = m.runtime.identity(self.repo, [], 'fixture-v1')
        (self.repo / 'app').write_text('uncommitted fix')
        with self.assertRaisesRegex(ValueError, 'clean artifact'):
            self.save(self.outcome())
        row = self.save(self.outcome(scope='replay'))
        self.assertNotEqual(row['artifact_identity']['diff'], before['diff'])

    def test_cli_records_and_compares(self):
        for row in (self.outcome(), self.outcome('c1', variant='candidate')):
            path = self.root / 'input.json'
            path.write_text(json.dumps(row))
            result = subprocess.run([sys.executable, str(SCRIPTS / 'improvement.py'), 'record',
                                     '--repo', str(self.repo), '--directory', str(self.directory),
                                     '--input', str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, str(SCRIPTS / 'improvement.py'), 'compare',
                                 '--repo', str(self.repo), '--directory', str(self.directory),
                                 '--baseline', 'base', '--candidate', 'candidate'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['paired_trials'], 1)

    def manifest(self, worker=None, repetitions=2):
        policy = self.root / 'coder.md'
        policy.write_text('Fix behavior; preserve scope.')
        doc = dict(repo=str(self.repo), environment='fixture-v1', repetitions=repetitions,
                   timeout_seconds=5, seed=42, tasks=[dict(id='task1', ref=self.sha, prompt='Fix app',
                   verify=[sys.executable, '-c', 'from pathlib import Path; assert Path("app").read_text()=="fixed"'])],
                   variants=[dict(name='base', command=[sys.executable, '-c', 'pass'],
                   configuration=dict(model='test'), policy_files={'coder.md': str(policy)}),
                   dict(name='candidate', command=worker or [sys.executable, '-c',
                   'from pathlib import Path; Path("app").write_text("fixed")'],
                   configuration=dict(model='test'), policy_files={'coder.md': str(policy)})])
        path = self.root / 'suite.json'
        path.write_text(json.dumps(doc))
        return path

    def test_replay_isolated_snapshots_and_matched_outcomes(self):
        (self.repo / 'future').write_text('answer from the future')
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'future answer')
        future = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'app').write_text('uncommitted work')
        before_index = self.git('diff', '--cached')
        worker = [sys.executable, '-c',
                  'import subprocess; from pathlib import Path; '
                  'assert subprocess.check_output(["git","rev-list","--all","--count"]).strip()==b"1"; '
                  'assert not subprocess.check_output(["git","remote"]); '
                  'assert subprocess.run(["git","cat-file","-e",' + repr(future) + ']).returncode!=0; '
                  'assert not Path("future").exists(); assert Path("app").read_text()=="old"; '
                  'Path("app").write_text("fixed")']
        output = self.root / 'replay with spaces'
        self.assertEqual(replay.run(self.manifest(worker), output), 0)
        rows = m.load(output / 'outcomes', self.repo)
        comparison = m.compare(rows, 'base', 'candidate')
        self.assertEqual(comparison['paired_trials'], 2)
        self.assertEqual(comparison['independent_tasks'], 1)
        self.assertEqual(comparison['variants']['base']['outcomes'], {'rejected': 2})
        self.assertEqual(comparison['variants']['candidate']['accepted_runs'], 2)
        self.assertEqual(comparison['variants']['candidate']['metric_samples'], 4)
        self.assertIsNone(comparison['variants']['candidate']['known_cost_usd'])
        self.assertEqual((self.repo / 'app').read_text(), 'uncommitted work')
        self.assertEqual(self.git('diff', '--cached'), before_index)
        with self.assertRaisesRegex(ValueError, 'fresh output'):
            replay.run(self.root / 'suite.json', output)

    def test_quota_stops_queue_and_does_not_create_cheap_successes(self):
        path = self.manifest(repetitions=3)
        doc = json.loads(path.read_text())
        for variant in doc['variants']:
            variant['command'] = [sys.executable, '-c', 'raise SystemExit(75)']
        path.write_text(json.dumps(doc))
        output = self.root / 'quota'
        self.assertEqual(replay.run(path, output), 75)
        plan = json.loads((output / 'plan.json').read_text())
        self.assertEqual(sum(r['status'] == 'blocked' for r in plan), 1)
        self.assertEqual(sum(r['status'] == 'not_started' for r in plan), 5)
        rows = m.load(output / 'outcomes', self.repo)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(m.report(rows)['deliveries'][0]['known_cost_usd'])

    def test_replay_cli_prints_outcomes(self):
        output = self.root / 'cli-replay'
        result = subprocess.run([sys.executable, str(SCRIPTS / 'replay.py'),
                                 '--manifest', str(self.manifest(repetitions=1)),
                                 '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['trials'], {'accepted': 1, 'rejected': 1})

    def test_timeout_stops_and_records_evidence(self):
        path = self.manifest()
        doc = json.loads(path.read_text())
        doc['timeout_seconds'] = .1
        for variant in doc['variants']:
            variant['command'] = [sys.executable, '-c', 'import time; time.sleep(10)']
        path.write_text(json.dumps(doc))
        output = self.root / 'timeout'
        self.assertEqual(replay.run(path, output), 124)
        rows = m.load(output / 'outcomes', self.repo)
        self.assertEqual(len(rows), 1)
        self.assertTrue(m.intact(rows[0]['evidence']))

    def test_changed_policy_blocks_acceptance_and_verifier_quota_stops(self):
        worker = [sys.executable, '-c',
                  'from pathlib import Path; Path("{policy}/coder.md").write_text("changed")']
        path = self.manifest(worker, repetitions=1)
        doc = json.loads(path.read_text())
        doc['variants'] = [doc['variants'][1]]
        path.write_text(json.dumps(doc))
        output = self.root / 'changed-policy'
        self.assertEqual(replay.run(path, output), 0)
        row = m.load(output / 'outcomes', self.repo)[0]
        self.assertEqual(row['status'], 'blocked')
        self.assertFalse(row['policy_intact'])
        path = self.manifest(repetitions=2)
        doc = json.loads(path.read_text())
        doc['tasks'][0]['verify'] = [sys.executable, '-c', 'raise SystemExit(75)']
        path.write_text(json.dumps(doc))
        output = self.root / 'verifier-quota'
        self.assertEqual(replay.run(path, output), 75)
        self.assertEqual(m.load(output / 'outcomes', self.repo)[0]['status'], 'blocked')

    def test_snapshot_failure_remains_a_blocked_attempt(self):
        (self.repo / '.gitmodules').write_text('[submodule "nested"]\npath = nested\nurl = ../fixture\n')
        self.git('add', '.gitmodules')
        self.git('update-index', '--add', '--cacheinfo', '160000,' + self.sha + ',nested')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'submodule fixture')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        output = self.root / 'setup-failure'
        self.assertEqual(replay.run(self.manifest(), output), 2)
        rows = m.load(output / 'outcomes', self.repo)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'blocked')

    def test_snapshot_keeps_tracked_ignored_inputs(self):
        (self.repo / '.gitignore').write_text('app\n')
        self.git('add', '.gitignore')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'ignore already tracked input')
        target = self.root / 'export'
        replay.snapshot(self.repo, self.git('rev-parse', 'HEAD').strip(), target)
        tracked = subprocess.check_output(['git', '-C', str(target), 'ls-files'], text=True)
        self.assertIn('app', tracked.splitlines())

    def test_interrupt_before_worker_preserves_attempt(self):
        output = self.root / 'snapshot-interrupt'
        with patch.object(replay, 'snapshot', side_effect=KeyboardInterrupt):
            self.assertEqual(replay.run(self.manifest(), output), 130)
        rows = m.load(output / 'outcomes', self.repo)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'blocked')
        plan = json.loads((output / 'plan.json').read_text())
        self.assertEqual(sum(r['status'] == 'not_started' for r in plan), 3)

    def test_interrupted_command_is_killed_and_recorded(self):
        ready = self.root / 'ready'
        proc = subprocess.Popen([sys.executable, str(SCRIPTS / 'runtime.py'), 'run',
                                 '--repo', str(self.repo), '--directory', str(self.root / 'interrupt'),
                                 '--', sys.executable, '-c',
                                 'from pathlib import Path; import os,time; Path(' + repr(str(ready)) +
                                 ').write_text(str(os.getpid())); time.sleep(30)'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: proc.kill() if proc.poll() is None else None)
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(ready.exists())
        proc.send_signal(signal.SIGINT)
        stdout, stderr = proc.communicate(timeout=5)
        self.assertEqual(proc.returncode, 130, stderr)
        record = json.loads(Path(json.loads(stdout)['evidence']).read_text())
        self.assertEqual(record['exit_code'], 130)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(ready.read_text()), 0)


if __name__ == '__main__':
    unittest.main()
