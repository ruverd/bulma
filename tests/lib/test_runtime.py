import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[2] / 'skills/bulma-bus/scripts/runtime.py'
spec = importlib.util.spec_from_file_location('runtime', SCRIPT)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class EvidenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        for args in (('init',), ('config', 'user.email', 'test@example.com'),
                     ('config', 'user.name', 'Test')):
            self.git(*args)
        (self.repo / 'a').write_text('one')
        self.git('add', '.')
        self.git('commit', '-m', 'initial')
        self.command = [sys.executable, '-c', 'print("ok")']

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def capture(self, command=None, environment='toolchain-v1'):
        result = self.cli('run', '--repo', str(self.repo), '--directory', str(self.root / 'ev'),
                          '--environment', environment, '--', *(command or self.command))
        data = json.loads(result.stdout)
        record = json.loads(Path(data['evidence']).read_text())
        return result, record

    def test_success_and_invalidation(self):
        result, record = self.capture()
        self.assertEqual(result.returncode, 0)
        current = runtime.identity(self.repo, self.command, 'toolchain-v1')
        self.assertTrue(runtime.reusable(record, current))
        self.assertFalse(runtime.reusable(record, runtime.identity(self.repo, self.command, 'v2')))
        (self.repo / 'a').write_text('two')
        self.assertFalse(runtime.reusable(record, runtime.identity(self.repo, self.command, 'toolchain-v1')))

    def test_untracked_and_missing_log(self):
        _, record = self.capture()
        (self.repo / 'new').write_text('changes')
        self.assertFalse(runtime.reusable(record, runtime.identity(self.repo, self.command, 'toolchain-v1')))
        (self.repo / 'new').unlink()
        Path(record['log']).unlink()
        self.assertFalse(runtime.reusable(record, runtime.identity(self.repo, self.command, 'toolchain-v1')))

    def test_failure_unknown_environment_and_mutating_command(self):
        result, record = self.capture([sys.executable, '-c', 'raise SystemExit(7)'])
        self.assertEqual(result.returncode, 7)
        self.assertFalse(runtime.reusable(record, record['identity']))
        _, record = self.capture(environment='')
        self.assertFalse(runtime.reusable(record, record['identity']))
        _, record = self.capture([sys.executable, '-c', 'open("a", "w").write("changed")'])
        self.assertFalse(record['stable'])
        self.assertFalse(runtime.reusable(record, record['identity']))

    def test_command_binding(self):
        _, record = self.capture()
        current = runtime.identity(self.repo, ['false'], 'toolchain-v1')
        self.assertFalse(runtime.reusable(record, current))

    def test_changed_log_cannot_be_reused(self):
        _, record = self.capture()
        current = runtime.identity(self.repo, self.command, 'toolchain-v1')
        Path(record['log']).write_text('different output')
        self.assertFalse(runtime.reusable(record, current))

    def test_no_repository_state(self):
        result = self.cli('run', '--repo', str(self.repo), '--directory', str(self.repo / 'state'), '--', 'true')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.repo / 'state').exists())

    def test_measure_idempotent_and_usage_unknown(self):
        data = {'run': 'r', 'sample_id': '1', 'graph': 'fd', 'node': 'tester',
                'kind': 'active', 'duration_ms': 123}
        source = self.root / 'measurement.json'
        folder = self.root / 'metrics'
        source.write_text(json.dumps(data))
        for _ in range(2):
            result = self.cli('measure', '--repo', str(self.repo), '--directory', str(folder), '--input', str(source))
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli('report', '--directory', str(folder))
        row = json.loads(result.stdout)['fd/tester']
        self.assertEqual(row['samples'], 1)
        self.assertEqual(row['active_ms'], 123)
        self.assertIsNone(row['input_tokens'])
        data['input_tokens'] = 10
        source.write_text(json.dumps(data))
        self.assertEqual(self.cli('measure', '--repo', str(self.repo), '--directory', str(folder),
                                  '--input', str(source)).returncode, 2)


if __name__ == '__main__':
    unittest.main()
