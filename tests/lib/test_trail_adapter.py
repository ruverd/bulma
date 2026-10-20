import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

adapter = load('context_adapter', 'skills/bulma-host/scripts/code-context.py')
runtime = load('runtime_capture', 'skills/bulma-bus/scripts/runtime.py')


class TrailTest(unittest.TestCase):
    def test_homonymous_code_cli_is_not_log_capture(self):
        for help_text, expected in [('Commands:\n  ask [options]\n  build [options]', False),
                                    ('Commands:\n  run [flags] command\n  mcp', True)]:
            result = subprocess.CompletedProcess([], 0, stdout=help_text)
            with patch.object(runtime.shutil, 'which', return_value='/bin/trail'), patch.object(runtime.subprocess, 'run', return_value=result):
                self.assertEqual(runtime.log_capture_available(), expected)

    def test_no_map_never_runs_or_initializes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(adapter.subprocess, 'run') as run:
            self.assertEqual(adapter.trail_context(tmp, 'foo')['status'], 'fallback')
            run.assert_not_called()

    def test_stale_map_falls_back_without_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'graft').mkdir()
            with patch.object(adapter.shutil, 'which', return_value='trail'), patch.object(adapter.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)) as run:
                self.assertEqual(adapter.trail_context(tmp, 'foo')['status'], 'fallback')
                self.assertEqual(run.call_count, 1)
                self.assertIn('--check', run.call_args.args[0])

    def test_fresh_map_queries_source_without_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'graft').mkdir()
            replies = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0, stdout='{"hits":[]}')]
            with patch.object(adapter.shutil, 'which', return_value='trail'), patch.object(adapter.subprocess, 'run', side_effect=replies) as run:
                self.assertEqual(adapter.trail_context(tmp, 'foo')['status'], 'ok')
                self.assertIn('--no-refresh', run.call_args.args[0])
                self.assertIn('--source', run.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
