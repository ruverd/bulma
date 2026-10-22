import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills/bulma-feature-delivery'
SCRIPT = SKILL / 'scripts/playbook.py'
EQUIVALENCE = SKILL / 'scripts/equivalence.py'
RUNTIME = ROOT / 'skills/bulma-bus/scripts/runtime.py'
spec = importlib.util.spec_from_file_location('playbooks', SCRIPT)
playbooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(playbooks)


class PlaybookTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.repo = self.folder / 'project'
        self.repo.mkdir()
        for args in [('init',), ('config', 'user.email', 'test@example.com'),
                     ('config', 'user.name', 'Test')]:
            self.git(*args)
        (self.repo / 'value.py').write_text('def render(): return "total: 10"\n')
        self.git('add', '.')
        self.git('commit', '-m', 'initial')
        self.proof = self.folder / 'proof.txt'
        self.proof.write_text('observed contract and command output\n')
        self.state = self.folder / 'STATE.md'
        self.command = [sys.executable, '-B', '-c', 'from value import render; print(render())']

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL)

    def cli(self, script, *args):
        return subprocess.run([sys.executable, '-B', str(script), *map(str, args)],
                              capture_output=True, text=True)

    def write_state(self, name, changes=None):
        contract = playbooks.select('chore', name)
        rows = []
        for step in contract['steps']:
            row = {'status': 'pass', 'evidence': str(self.proof), 'reason': ''}
            if not step['required']:
                row = {'status': 'skip', 'evidence': '', 'reason': 'existing contract settles the choice'}
            row.update((changes or {}).get(step['id'], {}))
            rows.append('| ' + ' | '.join([step['id'], row['status'], row['evidence'], row['reason']]) + ' |')
        metadata = {key: contract[key] for key in ('work_kind', 'playbook', 'playbook_version', 'playbook_digest')}
        text = '---\n' + ''.join(f'{k}: {v}\n' for k, v in metadata.items())
        text += '---\n\n## Playbook\n\n| Step | Status | Evidence | Reason |\n|---|---|---|---|\n'
        self.state.write_text(text + '\n'.join(rows) + '\n\n## Next\n')

    def check(self, environment='v1'):
        return self.cli(SCRIPT, 'check', '--state', self.state, '--repo', self.repo, '--environment', environment)

    def capture(self, environment='v1', command=None):
        result = self.cli(RUNTIME, 'run', '--repo', self.repo, '--directory', self.folder / 'captures',
                          '--environment', environment, '--', *(command or self.command))
        return Path(json.loads(result.stdout)['evidence'])

    def compare(self, before, after, environment='v1', name='comparison.json'):
        return self.cli(EQUIVALENCE, '--repo', self.repo, '--baseline', before,
                        '--candidate', after, '--environment', environment, '--out', self.folder / name)

    def test_selects_readonly_and_maintenance_without_feature_ceremony(self):
        for kind, expected in [('spike', 'investigation'), ('bug', 'bug-fix'),
                               ('regression', 'bug-fix'), ('chore', 'maintenance')]:
            result = self.cli(SCRIPT, 'select', '--kind', kind)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['playbook'], expected)
        self.assertEqual(playbooks.select('chore', 'refactoring')['playbook'], 'refactoring')
        with self.assertRaises(ValueError):
            playbooks.select('spike', 'feature')
        for name in playbooks.catalog()['playbooks']:
            self.assertTrue((SKILL / playbooks.select('chore', name)['contract']).is_file())

    def test_optional_skip_stays_visible_and_required_proof_cannot_skip(self):
        self.write_state('feature')
        self.assertEqual(self.check().returncode, 0)
        for change in [{'status': 'skip', 'reason': 'in a hurry'}, {'status': 'pending'},
                       {'status': 'fail'}, {'evidence': ''}, {'evidence': '/missing/proof'}]:
            self.write_state('feature', {'acceptance': change})
            self.assertEqual(self.check().returncode, 2, change)
        self.write_state('feature', {'alternatives': {'reason': ''}})
        self.assertEqual(self.check().returncode, 2)

    def test_drift_missing_duplicate_and_extra_rows_cannot_complete(self):
        self.write_state('maintenance')
        text = self.state.read_text()
        broken = [text.replace('playbook_digest:', 'old_digest:'),
                  text.replace('playbook_version: 1', 'playbook_version: 2'),
                  text.replace('| scope | pass', '| wrong | pass'),
                  text.replace('## Next', '| extra | pass | /missing | |\n\n## Next'),
                  text.replace('## Next', f'| scope | pass | {self.proof} | |\n\n## Next'),
                  text + '\n## Playbook\n']
        for content in broken:
            self.state.write_text(content)
            self.assertEqual(self.check().returncode, 2)

    def test_repository_proof_is_rejected(self):
        proof = self.repo / 'proof'
        proof.write_text('not runtime state')
        self.write_state('maintenance', {'scope': {'evidence': str(proof)}})
        self.assertEqual(self.check().returncode, 2)

    def test_refactor_proves_real_outputs_and_rechecks_current_tree(self):
        before = self.capture()
        (self.repo / 'value.py').write_text('def render(): return "total: " + str(10)\n')
        after = self.capture()
        result = self.compare(before, after)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write_state('refactoring', {'baseline': {'evidence': str(before)},
                         'equivalence': {'evidence': str(self.folder / 'comparison.json')}})
        self.assertEqual(self.check().returncode, 0)
        self.assertEqual(self.check(environment='v2').returncode, 2)
        self.write_state('refactoring', {'equivalence': {'evidence': str(self.folder / 'comparison.json')}})
        self.assertEqual(self.check().returncode, 2)
        self.write_state('refactoring', {'baseline': {'evidence': str(before)},
                         'equivalence': {'evidence': str(self.folder / 'comparison.json')}})
        (self.repo / 'value.py').write_text('def render(): return "total: 11"\n')
        self.assertEqual(self.check().returncode, 2)
        different = self.capture()
        result = self.compare(before, different, name='different.json')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.write_state('refactoring', {'equivalence': {'evidence': str(self.folder / 'different.json')}})
        self.assertEqual(self.check().returncode, 2)

    def test_refuses_changed_environment_command_missing_or_tampered_output(self):
        before = self.capture()
        after = self.capture()
        self.assertEqual(self.compare(before, after, environment='v2').returncode, 2)
        other = self.capture(command=[sys.executable, '-c', 'print("total: 10")'])
        self.assertEqual(self.compare(before, other).returncode, 2)
        self.assertEqual(self.compare(before, before).returncode, 2)
        self.assertEqual(self.compare(after, before).returncode, 2)
        record = json.loads(before.read_text())
        Path(record['log']).write_text('forged\n')
        self.assertEqual(self.compare(before, after).returncode, 2)
        Path(record['log']).unlink()
        self.assertEqual(self.compare(before, after).returncode, 2)

    def test_refuses_failed_empty_mutating_and_unknown_environment_runs(self):
        after = self.capture()
        commands = [[sys.executable, '-c', 'print("total: 10"); raise SystemExit(7)'],
                    [sys.executable, '-c', ''],
                    [sys.executable, '-c', 'open("value.py", "w").write("bad"); print("total: 10")']]
        for command in commands:
            before = self.capture(command=command)
            self.assertEqual(self.compare(before, after).returncode, 2)
        unknown = self.capture(environment='', command=[sys.executable, '-c', 'print("ok")'])
        self.assertEqual(self.compare(unknown, after).returncode, 2)

    def test_output_stays_outside_repo_and_previous_reports_survive(self):
        before, after = self.capture(), self.capture()
        self.assertEqual(self.compare(before, after).returncode, 2)
        (self.repo / 'value.py').write_text('def render(): return "total: " + str(10)\n')
        after = self.capture()
        result = self.compare(before, after, name='project/report.json')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.repo / 'report.json').exists())
        self.assertEqual(self.compare(before, after).returncode, 0)
        saved = (self.folder / 'comparison.json').read_bytes()
        self.assertEqual(self.compare(before, after).returncode, 2)
        self.assertEqual((self.folder / 'comparison.json').read_bytes(), saved)


if __name__ == '__main__':
    unittest.main()
