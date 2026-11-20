import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills/bulma-feature-delivery'
TESTER = SKILL / 'scripts/tester-checks.py'
RUNTIME = ROOT / 'skills/bulma-bus/scripts/runtime.py'


class TesterChecksTest(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.project = self.root / 'project'
        self.project.mkdir()
        self.evidence = self.root / 'evidence'
        self.git('init', '-qb', 'main')
        self.git('config', 'user.email', 'tester@example.com')
        self.git('config', 'user.name', 'Tester')
        self.legacy = 'legacy_one = 1\nlegacy_two = 2\n'
        self.write('app/feature.py', self.legacy)
        self.write('app/lookup.py', 'def status(items, failed):\n    return ("ready", True)\n')
        self.write('README.md', 'base\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.git('checkout', '-qb', 'topic')

    def git(self, *argv):
        subprocess.run(['git', '-C', str(self.repo), *argv], check=True, capture_output=True)

    def write(self, path, content):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding='utf-8')
        return file

    def memory(self, text):
        (self.project / 'memory.md').write_text(text, encoding='utf-8')

    def run_tester(self, kind, *scope):
        result = subprocess.run([sys.executable, str(TESTER), '--repo', str(self.repo),
                                 '--base', 'main', '--project', str(self.project),
                                 '--directory', str(self.evidence), '--work-kind', kind, *scope],
                                capture_output=True, text=True)
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def capture(self, argv):
        result = subprocess.run([sys.executable, str(RUNTIME), 'run', '--repo', str(self.repo),
                                 '--directory', str(self.evidence), '--', *argv],
                                capture_output=True, text=True)
        self.assertTrue(result.stdout, result.stderr)
        return json.loads(result.stdout)['evidence']

    def prevention(self):
        test = self.root / 'lookup_regression.py'
        test.write_text(
            'import runpy\nimport unittest\n'
            'status = runpy.run_path("app/lookup.py")["status"]\n'
            'class LookupTest(unittest.TestCase):\n'
            '    def test_unresolved_read(self):\n'
            '        self.assertEqual(status(None, True), ("retry", False))\n'
            '    def test_successful_empty_read(self):\n'
            '        self.assertEqual(status([], False), ("ready", True))\n'
            'unittest.main()\n',
            encoding='utf-8')
        argv = [sys.executable, str(test)]
        original = (self.repo / 'app/lookup.py').read_text()
        red = self.capture(argv)
        fixed = original.replace('    return', '    if failed and items is None:\n'
                                 '        return ("retry", False)\n    return', 1)
        self.write('app/lookup.py', fixed)
        green = self.capture(argv)
        self.write('app/lookup.py', original)
        feedback = self.project / 'feedback/query-error/review-1.md'
        feedback.parent.mkdir(parents=True)
        feedback.write_text('# Unresolved read\n\n- Category: confirmed defect\n', encoding='utf-8')
        registration = {'feedback': 'query-error/review-1.md', 'paths': ['app/lookup.py'],
                        'argv': argv, 'red': red, 'green': green}
        self.memory('## Checks\n- prevention: ' + json.dumps(registration) + '\n')
        return feedback, registration, fixed

    def test_prevention_breaks_the_normal_tester_gate_then_passes(self):
        _, _, fixed = self.prevention()
        self.write('app/lookup.py', (self.repo / 'app/lookup.py').read_text() + '# intentional change\n')
        code, result = self.run_tester('bug')
        self.assertEqual((code, result['hard_gate']), (1, 'fail'))
        red = result['prevention'][0]
        self.assertEqual(red['exit_code'], 1)
        record = json.loads(Path(red['evidence']).read_text())
        log = Path(record['log']).read_text()
        self.assertIn('FAIL: test_unresolved_read', log)
        self.assertNotIn('FAIL: test_successful_empty_read', log)

        self.write('app/lookup.py', fixed)
        code, result = self.run_tester('bug', '--environment', 'fixture-local-v1')
        self.assertEqual((code, result['hard_gate']), (0, 'pass'))
        green = result['prevention'][0]
        self.assertEqual(green['exit_code'], 0)
        record = json.loads(Path(green['evidence']).read_text())
        self.assertIn('Ran 2 tests', Path(record['log']).read_text())

        code, reused = self.run_tester('bug', '--ran', green['evidence'],
                                       '--environment', 'fixture-local-v1')
        self.assertEqual(code, 0)
        self.assertEqual(reused['prevention'][0]['evidence'], green['evidence'])

    def test_irrelevant_unproven_and_unconfirmed_feedback_run_no_test(self):
        feedback, registration, _ = self.prevention()
        self.write('README.md', 'unrelated change\n')
        before = set(self.evidence.iterdir())
        code, result = self.run_tester('chore')
        self.assertEqual((code, result['prevention']), (0, []))
        self.assertEqual(set(self.evidence.iterdir()), before)

        self.write('app/lookup.py', '# current scope\n' + (self.repo / 'app/lookup.py').read_text())
        feedback.write_text('- Category: unknown\n', encoding='utf-8')
        code, result = self.run_tester('chore')
        self.assertEqual((code, result['prevention'][0]['status']), (0, 'unavailable'))
        feedback.write_text('- Category: confirmed defect\n', encoding='utf-8')
        Path(registration['red']).unlink()
        code, result = self.run_tester('chore')
        self.assertEqual((code, result['prevention'][0]['status']), (0, 'unavailable'))
        self.assertEqual(set(self.evidence.iterdir()), before)

    def coverage_config(self, trace, minimum=None, write_report=True):
        writer = self.root / 'coverage_fixture.py'
        program = ('from pathlib import Path\nimport sys\n'
                   'Path(sys.argv[1]).write_text(' + repr(trace) + ', encoding="utf-8")\n')
        writer.write_text(program if write_report else 'print("no coverage output")\n', encoding='utf-8')
        profile = {'argv': [sys.executable, str(writer), '{report}']}
        if minimum is not None:
            profile['minimum'] = minimum
        self.memory('## Preferences\n- feature_coverage: ' + json.dumps(profile) + '\n')

    def feature_diff(self):
        self.write('app/feature.py', self.legacy + 'a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n# comment\n')
        self.write('tests/test_feature.py', 'assert True\n')
        self.write('app/unrelated.py', 'unrelated = 1\n')
        return ('TN:\nSF:' + str(self.repo / 'app/feature.py') + '\n'
                'DA:1,0\nDA:2,0\nDA:3,1\nDA:4,1\nDA:5,1\nDA:6,1\nDA:7,0\nend_of_record\n'
                'SF:tests/test_feature.py\nDA:1,0\nend_of_record\n'
                'SF:app/unrelated.py\nDA:1,0\nend_of_record\n')

    def test_feature_default_threshold_is_inclusive_and_ignores_old_lines(self):
        trace = self.feature_diff()
        self.coverage_config(trace)
        code, result = self.run_tester('feature', '--feature-path', 'app/feature.py')
        coverage = result['feature_coverage']
        self.assertEqual((code, result['hard_gate'], coverage['status']), (0, 'pass', 'pass'))
        self.assertEqual((coverage['covered'], coverage['executable'], coverage['minimum']), (4, 5, 80))
        self.assertTrue(Path(coverage['evidence']).is_file())

        self.coverage_config(trace.replace('DA:6,1', 'DA:6,0'))
        code, result = self.run_tester('feature', '--feature-path', 'app/feature.py')
        self.assertEqual((code, result['hard_gate'], result['feature_coverage']['covered']), (1, 'fail', 3))

    def test_same_file_scope_excludes_unrelated_edits(self):
        trace = self.feature_diff()
        self.write('app/feature.py', (self.repo / 'app/feature.py').read_text().replace(
            'legacy_one = 1', 'legacy_one = 9'))
        self.coverage_config(trace)
        code, result = self.run_tester('feature', '--feature-path', 'app/feature.py',
                                       '--feature-lines', 'app/feature.py:3-7')
        coverage = result['feature_coverage']
        self.assertEqual((code, coverage['covered'], coverage['executable']), (0, 4, 5))

    def test_staged_rename_does_not_count_unchanged_lines(self):
        self.git('mv', 'app/feature.py', 'app/renamed.py')
        self.write('app/renamed.py', self.legacy + 'a = 1\n')
        self.coverage_config('SF:app/renamed.py\nDA:1,0\nDA:2,0\nDA:3,1\nend_of_record\n')
        code, result = self.run_tester('feature', '--feature-path', 'app/renamed.py')
        coverage = result['feature_coverage']
        self.assertEqual((code, coverage['covered'], coverage['executable']), (0, 1, 1))

    def test_no_code_feature_does_not_claim_coverage(self):
        self.write('README.md', 'docs-only feature\n')
        code, result = self.run_tester('feature', '--no-feature-code', 'diff only changes README')
        coverage = result['feature_coverage']
        self.assertEqual((code, coverage['status']), (0, 'not_applicable'))
        self.assertNotIn('covered', coverage)
        self.assertNotIn('evidence', coverage)

    def test_override_and_non_feature(self):
        trace = self.feature_diff()
        self.coverage_config(trace, 85)
        code, result = self.run_tester('feature', '--feature-path', 'app/feature.py')
        self.assertEqual((code, result['feature_coverage']['minimum']), (1, 85))
        self.coverage_config(trace.replace('DA:6,1', 'DA:6,0'), 60)
        code, result = self.run_tester('feature', '--feature-path', 'app/feature.py')
        self.assertEqual((code, result['feature_coverage']['minimum']), (0, 60))

        self.coverage_config(trace, 101)
        before = set(self.evidence.iterdir())
        for kind in ('bug', 'regression', 'chore'):
            with self.subTest(kind=kind):
                code, result = self.run_tester(kind)
                self.assertEqual((code, result['feature_coverage']['status']), (0, 'not_applicable'))
        self.assertEqual(set(self.evidence.iterdir()), before)
        code, result = self.run_tester('feature', '--feature-path', 'app/feature.py')
        self.assertEqual((code, result['feature_coverage']['status']), (1, 'unavailable'))

    def test_missing_malformed_or_empty_feature_report_cannot_pass(self):
        self.feature_diff()
        for trace, present, reason in (
                ('', False, 'report'),
                ('{"coverage":42}', True, 'LCOV'),
                ('SF:other.py\nDA:1,1\nend_of_record\n', True, 'app/feature.py'),
                ('SF:app/feature.py\nDA:1,1\nend_of_record\n', True, 'no executable')):
            with self.subTest(reason=reason):
                self.coverage_config(trace, write_report=present)
                code, result = self.run_tester('feature', '--feature-path', 'app/feature.py')
                coverage = result['feature_coverage']
                self.assertEqual((code, result['hard_gate'], coverage['status']), (1, 'fail', 'unavailable'))
                self.assertIn(reason, coverage['reason'])
                self.assertTrue(Path(coverage['evidence']).is_file())

    def test_tester_contract_and_existing_failure_route(self):
        sys.path.insert(0, str(ROOT / 'tests/lib'))
        from check_graphs import parse_edges, reachable

        node = (SKILL / 'nodes/tester.md').read_text()
        graph = (SKILL / 'GRAPH.md').read_text()
        self.assertIn('scripts/tester-checks.py', node)
        self.assertIn('hard_gate', node)
        self.assertIn('work_kind', node)
        self.assertIn('path: light_change', node)
        self.assertIn('| tester | fail + loops left | **implement** |', graph)
        self.assertFalse(reachable(parse_edges(graph), 'review', 'shipper', avoid=('tester',)))


if __name__ == '__main__':
    unittest.main()
