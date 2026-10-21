import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[2] / 'skills/bulma-feature-delivery/scripts/floor-guard.py'

BASE_FILES = {
    'src/pay.ts': 'export function pay(n: number) {\n  return n * 2\n}\n',
    'src/pay.test.ts': ("import { pay } from './pay'\n"
                        "it('should double', () => {\n"
                        "  expect(pay(2)).toBe(4)\n"
                        "  expect(pay(0)).toBe(0)\n"
                        "})\n"),
    'tests/test_rate.py': 'def test_rate():\n    assert 1 == 1\n',
    'jest.config.js': 'module.exports = { coverageThreshold: { global: { lines: 90 } } }\n',
    '.github/workflows/ci.yml': 'jobs:\n  test:\n    steps:\n      - run: npm test\n',
    'README.md': 'docs\n',
}


class FloorGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        for args in (('init', '-q', '-b', 'main'), ('config', 'user.email', 't@example.com'),
                     ('config', 'user.name', 'T')):
            self.git(*args)
        for rel, text in BASE_FILES.items():
            self.write(rel, text)
        self.git('add', '.')
        self.git('commit', '-q', '-m', 'base')
        self.git('checkout', '-q', '-b', 'work')

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_guard(self, *extra):
        result = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.repo),
                                 '--base', 'main', '--json', *extra],
                                capture_output=True, text=True)
        report = json.loads(result.stdout) if result.stdout.strip() else None
        return result.returncode, report

    def rules(self, report):
        return sorted({item['rule'] for item in report['violations']})

    def test_clean_change_passes(self):
        self.write('src/pay.ts', 'export function pay(n: number) {\n  return n * 3\n}\n')
        self.write('README.md', 'mentions eslint-disable and it.skip( in prose\n')
        code, report = self.run_guard()
        self.assertEqual(code, 0)
        self.assertEqual(report['violations'], [])

    def test_suppression_in_unstaged_change(self):
        self.write('src/pay.ts', '// @ts-ignore\nexport function pay(n: number) {\n  return n * 2\n}\n')
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(report['violations'], [{'rule': 'suppression', 'path': 'src/pay.ts', 'line': 1}])

    def test_skip_and_only_in_tests(self):
        text = BASE_FILES['src/pay.test.ts'].replace("it('should", "it.skip('should")
        self.write('src/pay.test.ts', text + "it.only('should run alone', () => { expect(1).toBe(1) })\n")
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(self.rules(report), ['skipped-test'])
        self.assertEqual(len(report['violations']), 2)

    def test_removed_assertion_in_kept_test(self):
        self.write('src/pay.test.ts', BASE_FILES['src/pay.test.ts'].replace(
            '  expect(pay(0)).toBe(0)\n', ''))
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(self.rules(report), ['assertions-removed'])

    def test_rewritten_assertion_is_not_a_removal(self):
        self.write('src/pay.test.ts', BASE_FILES['src/pay.test.ts'].replace(
            'expect(pay(0)).toBe(0)', 'expect(pay(1)).toBe(2)'))
        code, report = self.run_guard()
        self.assertEqual(code, 0, report)

    def test_deleted_test_file(self):
        self.git('rm', '-q', 'tests/test_rate.py')
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(report['violations'], [{'rule': 'deleted-test', 'path': 'tests/test_rate.py', 'line': 0}])

    def test_renamed_test_is_not_deleted(self):
        self.git('mv', 'tests/test_rate.py', 'tests/test_rates.py')
        code, report = self.run_guard()
        self.assertEqual(code, 0, report)

    def test_empty_catch_single_and_multi_line(self):
        self.write('src/pay.ts', BASE_FILES['src/pay.ts'] + 'try { pay(1) } catch (e) {}\n')
        self.write('src/sync.py', 'try:\n    run()\nexcept Exception:\n    pass\n')
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(sorted((v['path'], v['line']) for v in report['violations']),
                         [('src/pay.ts', 4), ('src/sync.py', 3)])

    def test_stub_in_untracked_file(self):
        self.write('src/refund.py', 'def refund():\n    raise NotImplementedError\n')
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(report['violations'], [{'rule': 'stub', 'path': 'src/refund.py', 'line': 2}])

    def test_ci_step_silenced(self):
        self.write('.github/workflows/ci.yml',
                   'jobs:\n  test:\n    steps:\n      - run: npm test || true\n')
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(self.rules(report), ['ci-silenced'])

    def test_threshold_lowered_but_raise_is_silent(self):
        self.write('jest.config.js', BASE_FILES['jest.config.js'].replace('90', '70'))
        code, report = self.run_guard()
        self.assertEqual(code, 1)
        self.assertEqual(self.rules(report), ['threshold-lowered'])
        self.write('jest.config.js', BASE_FILES['jest.config.js'].replace('90', '95'))
        code, report = self.run_guard()
        self.assertEqual(code, 0, report)

    def test_inline_allow_is_reported_not_blocking(self):
        self.write('src/pay.ts', '// eslint-disable-next-line no-console -- floor-guard: allow vendor shim\n'
                   + BASE_FILES['src/pay.ts'])
        code, report = self.run_guard()
        self.assertEqual(code, 0)
        self.assertEqual(report['allowed'][0]['reason'], 'vendor shim')

    def test_file_allow_flag(self):
        self.git('rm', '-q', 'tests/test_rate.py')
        code, report = self.run_guard('--allow', 'deleted-test:tests/test_rate.py')
        self.assertEqual(code, 0)
        self.assertEqual(len(report['allowed']), 1)

    def test_report_never_carries_matched_text(self):
        self.write('src/pay.ts', 'const key = "sk_live_123" // @ts-ignore\n' + BASE_FILES['src/pay.ts'])
        _, report = self.run_guard()
        self.assertNotIn('sk_live', json.dumps(report))

    def test_cannot_run_is_exit_two(self):
        code, _ = self.run_guard('--base', 'no-such-ref')
        self.assertEqual(code, 2)
        outside = Path(self.tmp.name) / 'plain'
        outside.mkdir()
        result = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(outside)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
