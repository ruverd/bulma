import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[2] / 'skills/bulma-code-review/scripts/batch-plan.py'
spec = importlib.util.spec_from_file_location('batch_plan', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def section(path):
    return (f'diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n'
            '@@ -1,1 +1,2 @@\n x\n+y\n')


class BatchTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, paths, diff_source='api', churn=2):
        files = [{'filename': p, 'additions': churn, 'deletions': 0} for p in paths]
        (self.root / 'files.json').write_text(json.dumps([files]))
        (self.root / 'PR_PATCH.diff').write_text(''.join(section(p) for p in paths))
        (self.root / 'snapshot.json').write_text(json.dumps(
            {'head': 'h' * 40, 'base': 'b' * 40, 'diff_source': diff_source}))

    def test_small_and_large_prs_do_not_batch(self):
        self.write([f'src/f{i}.ts' for i in range(30)])
        self.assertFalse(m.plan(self.root, 15, 1500)['batched'])
        self.assertFalse((self.root / 'batches.json').exists())

    def test_api_refusal_batches_even_when_few_files(self):
        self.write(['src/a.ts'], diff_source='local')
        self.assertTrue(m.plan(self.root, 15, 1500)['batched'])

    def test_churn_threshold_batches(self):
        self.write([f'src/f{i}.ts' for i in range(10)], churn=600)
        result = m.plan(self.root, 15, 1500)
        self.assertTrue(result['batched'])
        manifest = json.loads((self.root / 'batches.json').read_text())
        self.assertTrue(all(b['churn'] <= 1500 for b in manifest['batches']))

    def test_very_large_pr_plans_hotspots_first(self):
        self.plan_large()

    def plan_large(self):
        paths = [f'src/ui/c{i}.tsx' for i in range(40)]
        paths += [f'src/auth/guard{i}.ts' for i in range(12)]
        paths += ['package-lock.json', 'src/ui/__snapshots__/c.snap']
        self.write(paths)
        result = m.plan(self.root, 15, 1500)
        self.assertTrue(result['batched'])
        manifest = json.loads((self.root / 'batches.json').read_text())
        batches = manifest['batches']
        self.assertTrue(all(len(b['files']) <= 15 for b in batches[:-1]))
        self.assertTrue(batches[0]['files'][0].startswith('src/auth/'))
        self.assertTrue(batches[-1]['mechanical'])
        planned = [p for b in batches for p in b['files']]
        self.assertEqual(sorted(planned), sorted(paths))
        first = self.root / batches[0]['dir']
        self.assertIn('diff --git a/src/auth/', (first / 'PATCH.diff').read_text())
        self.assertEqual(sum(p.startswith('src/auth/') for p in batches[0]['files']), 12)
        self.assertEqual((first / 'FILES.txt').read_text().split(), batches[0]['files'])
        self.assertEqual((first / 'PATCH.diff').read_text().count('diff --git'), len(batches[0]['files']))
        return manifest

    def test_merge_one_artifact_and_detects_gaps(self):
        manifest = self.plan_large()
        batches = manifest['batches']
        for index, batch in enumerate(batches):
            folder = self.root / batch['dir']
            rows = [{'path': p, 'checked': 'logic'} for p in batch['files']]
            if index == 1:
                rows = rows[:-1]
            (folder / 'coverage.json').write_text(json.dumps(rows))
            found = [{'path': batch['files'][0], 'line': 2, 'severity': 'nit', 'class': 'naming'}]
            if index == 0:
                found.append({'path': batch['files'][0], 'line': 2, 'severity': 'blocker', 'class': 'naming'})
            (folder / 'findings.json').write_text(json.dumps(found))
        summary, complete = m.merge(self.root)
        self.assertFalse(complete)
        self.assertEqual(summary['uncovered'], [batches[1]['files'][-1]])
        merged = json.loads((self.root / 'findings.json').read_text())
        self.assertEqual(merged[0]['severity'], 'blocker')
        self.assertEqual(len(merged), len(batches))
        folder = self.root / batches[1]['dir']
        (folder / 'coverage.json').write_text(json.dumps([{'path': p} for p in batches[1]['files']]))
        summary, complete = m.merge(self.root)
        self.assertTrue(complete)
        self.assertEqual(summary['covered_files'], summary['changed_files'])
        (self.root / batches[2]['dir'] / 'findings.json').unlink()
        summary, complete = m.merge(self.root)
        self.assertFalse(complete)
        self.assertEqual(summary['missing_batches'], [batches[2]['id']])

    def test_merge_refuses_stale_manifest(self):
        self.plan_large()
        (self.root / 'snapshot.json').write_text(json.dumps({'head': 'n' * 40, 'base': 'b' * 40}))
        summary, complete = m.merge(self.root)
        self.assertFalse(complete)
        self.assertIn('error', summary)


if __name__ == '__main__':
    unittest.main()
