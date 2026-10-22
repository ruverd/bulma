import argparse
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from test_factory_eval import FIXES

spec = importlib.util.spec_from_file_location('improve', ROOT / 'evals/improve/run.py')
improve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(improve)


class ImprovementTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.lookback = self.directory / 'lookback.json'
        self.lookback.write_text(json.dumps({'clusters': [{'cluster': 'sibling-path parity', 'prs': 6}]}))
        self.candidate = self.directory / 'candidate.md'
        self.candidate.write_text('CANDIDATE: check sibling write paths.')
        self.args = argparse.Namespace(out=self.directory / 'proposal', lookback=self.lookback,
            candidate=self.candidate, cluster='sibling-path parity', hypothesis='Cover sibling writes.',
            model='pinned-test-model', development=['sibling-validation'], heldout=['tenant-access'],
            runs=1, timeout=10, budget_per_run=0.25, min_savings=0.1)

    def freeze(self):
        improve.prepare(self.args)
        return improve.load_plan(self.args.out)

    def emit(self, phase, baseline=True, candidate=True, cost=1):
        directory, plan = improve.load_plan(self.args.out)
        output = directory / phase
        output.mkdir()
        cases = [c for c in improve.read(directory / 'cases.json') if c['id'] in plan[phase]]
        before = (directory / 'baseline.txt').read_text()
        instructions = {'baseline': before, 'candidate': before + '\n\n' + (directory / 'candidate.txt').read_text()}
        improve.write(output / 'manifest.json', {'model': plan['model'], 'runs_per_case_arm': plan['runs'],
            'budget_per_run_usd': plan['budget_per_run'], 'timeout_seconds': plan['timeout'],
            'source_sha': plan['source_sha'], 'host': 'test-host',
            'runner_sha256': plan['runner_sha256'],
            'cases_sha256': improve.factory.digest(json.dumps(cases, sort_keys=True)),
            'instructions_sha256': {k: improve.factory.digest(v) for k, v in instructions.items()}})
        rows = [{'case': c['id'], 'run': 1, 'arm': arm, 'passed': passed, 'completed': True,
                 'cost_usd': cost, 'seconds': 2, 'permission_denials': []}
                for c in cases for arm, passed in [('baseline', baseline), ('candidate', candidate)]]
        (output / 'results.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        return output, rows

    def test_requires_recurrence_and_disjoint_cases_before_writing(self):
        self.args.heldout = self.args.development
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            improve.prepare(self.args)
        self.assertFalse(self.args.out.exists())
        self.args.heldout = ['tenant-access']
        self.lookback.write_text(json.dumps({'clusters': [{'cluster': self.args.cluster, 'prs': 4}]}))
        with self.assertRaisesRegex(ValueError, 'five distinct'):
            improve.prepare(self.args)
        self.assertFalse(self.args.out.exists())

    def test_frozen_inputs_and_plan_cannot_drift(self):
        directory, _ = self.freeze()
        (directory / 'candidate.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Frozen input changed'):
            improve.load_plan(directory)
        (directory / 'candidate.txt').write_text(self.candidate.read_text())
        (directory / 'plan.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Frozen plan changed'):
            improve.load_plan(directory)

    def test_dry_run_never_invokes_model_and_heldout_requires_development(self):
        directory, _ = self.freeze()
        args = argparse.Namespace(proposal=directory, phase='development', dry_run=True)
        with patch.object(improve.subprocess, 'run') as run:
            result = improve.probe(args)
        run.assert_not_called()
        self.assertEqual(result['model_calls'], 2)
        self.assertEqual(result['requested_budget_ceiling_usd'], 0.5)
        self.assertFalse((directory / 'development').exists())
        args.phase = 'heldout'
        with self.assertRaisesRegex(ValueError, 'development pilot_pass'):
            improve.probe(args)

    def test_regression_rejects_even_if_other_trials_improve(self):
        directory, plan = self.freeze()
        self.emit('development', baseline=True, candidate=False)
        self.emit('heldout', baseline=False, candidate=True)
        result = improve.report(argparse.Namespace(proposal=directory))
        self.assertEqual(result['status'], 'reject')
        self.assertEqual(len(result['phases']['development']['paired_regressions']), 1)
        self.assertEqual(result['probe_cost_usd'], 4)
        self.assertTrue((directory / 'review.md').exists())

    def test_no_change_and_unknown_cost_cannot_claim_savings(self):
        directory, plan = self.freeze()
        self.emit('development', cost=None)
        result = improve.assess(directory, plan, 'development')
        self.assertEqual(result['status'], 'inconclusive')
        self.assertIsNone(result['cost_per_correct_savings'])
        self.assertIsNone(result['inference_cost_usd'])
        result = improve.report(argparse.Namespace(proposal=directory))
        self.assertEqual(result['status'], 'inconclusive')
        self.assertIsNone(result['probe_cost_usd'])

    def test_partial_duplicate_or_mismatched_results_do_not_win(self):
        directory, plan = self.freeze()
        output, rows = self.emit('development')
        path = output / 'results.jsonl'
        path.write_text(json.dumps(rows[0]) + '\n')
        self.assertEqual(improve.assess(directory, plan, 'development')['status'], 'incomplete')
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows + [rows[0]]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            improve.assess(directory, plan, 'development')
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        manifest = improve.read(output / 'manifest.json')
        manifest['model'] = 'different-model'
        improve.write(output / 'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'frozen plan'):
            improve.assess(directory, plan, 'development')

    def test_changed_host_cannot_count_as_a_matched_heldout_trial(self):
        directory, plan = self.freeze()
        self.emit('development', baseline=False, candidate=True)
        output, _ = self.emit('heldout', baseline=False, candidate=True)
        manifest = improve.read(output / 'manifest.json')
        manifest['host'] = 'different-host-version'
        improve.write(output / 'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'Host version changed'):
            improve.assess(directory, plan, 'heldout')

    def test_cost_of_failed_trials_is_counted_and_nan_is_unknown(self):
        directory, plan = self.freeze()
        output, rows = self.emit('development', baseline=False, candidate=True)
        rows[0]['cost_usd'] = float('nan')
        (output / 'results.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        result = improve.assess(directory, plan, 'development')
        self.assertIsNone(result['inference_cost_usd'])
        self.assertEqual(result['metrics']['baseline']['correct'], 0)
        self.assertEqual(result['status'], 'pilot_pass')
        # Quality gain can justify a pilot pass; unknown spend never becomes zero.
        self.assertIsNone(result['cost_per_correct_savings'])

    def test_full_loop_uses_factory_grader_and_never_edits_installed_skill(self):
        directory, plan = self.freeze()
        original = (ROOT / 'skills/bulma-feature-delivery/LESSONS.md').read_bytes()
        real_run = subprocess.run
        real_output = subprocess.check_output

        def invoke(workspace, prompt, instructions, model, budget, timeout):
            if 'CANDIDATE:' in instructions:
                case = 'sibling-validation' if (workspace / 'save.mjs').exists() else 'tenant-access'
                for name, text in FIXES[case].items():
                    (workspace / name).write_text(text)
            return {'total_cost_usd': 0.05}, True, '{}', '', 1

        def execute(command, cwd):
            old = sys.argv
            try:
                sys.argv = command[1:]
                with patch.object(improve.factory, 'invoke', side_effect=invoke), \
                     patch.object(improve.factory.subprocess, 'check_output', side_effect=lambda cmd, **kw: 'test-host' if cmd[0] == 'claude' else real_output(cmd, **kw)), \
                     patch.object(improve.factory.subprocess, 'run', side_effect=real_run):
                    with contextlib.redirect_stdout(io.StringIO()):
                        improve.factory.main()
            finally:
                sys.argv = old
            return subprocess.CompletedProcess(command, 0)

        for phase in ('development', 'heldout'):
            with patch.object(improve.subprocess, 'run', side_effect=execute):
                result = improve.probe(argparse.Namespace(proposal=directory, phase=phase, dry_run=False))
            self.assertEqual(result['status'], 'pilot_pass')
        result = improve.report(argparse.Namespace(proposal=directory))
        self.assertEqual(result['status'], 'review_candidate')
        self.assertIn('real-task', result['promotion'])
        self.assertEqual((ROOT / 'skills/bulma-feature-delivery/LESSONS.md').read_bytes(), original)
        with self.assertRaisesRegex(ValueError, 'already attempted'):
            improve.probe(argparse.Namespace(proposal=directory, phase='development', dry_run=False))

    def test_refuses_artifacts_in_checkout_and_invalid_limits(self):
        self.args.out = ROOT / 'experiment-that-must-not-exist'
        with self.assertRaisesRegex(ValueError, 'outside git'):
            improve.prepare(self.args)
        self.args.out = self.directory / 'proposal'
        self.args.budget_per_run = float('nan')
        with self.assertRaisesRegex(ValueError, 'positive'):
            improve.prepare(self.args)


if __name__ == '__main__':
    unittest.main()
