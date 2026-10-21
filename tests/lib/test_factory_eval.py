import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('factory_eval', ROOT / 'evals/factory/run.py')
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)

FIXES = {
    'postgres-unavailable': {'suite.mjs': "export async function runSuite(ok,check){if(!ok)throw Error('database missing');await check();return {executed:1,passed:true}}"},
    'advisory-status': {'verdict.mjs': "export function verdict(s,sha){return s?.sha===sha ? (/^AI QA (PASS|FAIL|BLOCKED)\\b/.exec(s.description??'')?.[1]??'UNKNOWN'):'UNKNOWN'}"},
    'reuse-money': {'receipt.mjs': "import {money} from './money.mjs';export function receipt(amount){return 'Total: '+money.format(amount)}"},
    'sibling-validation': {'save.mjs': "export function save(n,p){if(!Number.isInteger(n)||n<=0)throw Error('invalid');return p(n)}export const autosave=save;"},
    'tenant-access': {'documents.mjs': "export function readDocument(id,s,docs){const d=docs.find(d=>d.id===id);if(!s?.tenantId||!d||d.tenantId!==s.tenantId)throw Error('denied');return d}"},
    'concurrent-delivery': {'handler.mjs': "export function createHandler(send){const jobs=new Map();return id=>{if(!jobs.has(id))jobs.set(id,Promise.resolve().then(()=>send(id)).catch(e=>{jobs.delete(id);throw e}));return jobs.get(id)}}"},
    'pagination-bound': {'pages.mjs': "export async function collect(fetch,max=100){if(!Number.isInteger(max)||max<1)throw Error('invalid');const out=[];for(let i=0;i<max;i++){const page=await fetch(i);if(!page.length)return out;out.push(...page)}throw Error('limit')}"},
    'duplicate-override': {'package.json': json.dumps({'name': 'fixture', 'private': True, 'devDependencies': {'follow-redirects': '^1.16.1'}, 'overrides': {'other': '2.0.0'}})},
}


class FactoryEvalTest(unittest.TestCase):
    def test_every_case_rejects_bug_and_accepts_complete_fix(self):
        cases = json.loads((ROOT / 'evals/factory/cases.json').read_text())
        self.assertEqual({case['id'] for case in cases}, set(FIXES))
        for case in cases:
            with self.subTest(case=case['id']), tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                factory.prepare(case, workspace)
                self.assertFalse(factory.grade(case, workspace)['passed'], case['id'])
                for name, code in FIXES[case['id']].items():
                    (workspace / name).write_text(code)
                result = factory.grade(case, workspace)
                self.assertTrue(result['passed'], result['log'])

    def test_failed_runs_cost_money_and_unknown_cost_stays_unknown(self):
        rows = [{'arm': 'baseline', 'passed': True, 'completed': True, 'cost_usd': 1},
                {'arm': 'baseline', 'passed': False, 'completed': True, 'cost_usd': 2},
                {'arm': 'baseline', 'passed': True, 'completed': False, 'cost_usd': 3}]
        summary = factory.summarize(rows)['baseline']
        self.assertEqual(summary['correct'], 1)
        self.assertEqual(summary['cost_per_correct'], 6)
        rows.append({'arm': 'baseline', 'passed': False, 'completed': False, 'cost_usd': None})
        self.assertIsNone(factory.summarize(rows)['baseline']['cost_usd'])

    def test_host_budget_stop_is_not_completed(self):
        process = MagicMock(returncode=0)
        process.communicate.return_value = (json.dumps({'subtype': 'error_max_budget_usd', 'total_cost_usd': 0.25}), '')
        with patch.object(factory.subprocess, 'Popen', return_value=process):
            result, completed, *_ = factory.invoke(Path('/tmp'), 'task', 'rules', 'model', 0.25, 10)
        self.assertFalse(completed)
        self.assertEqual(result['total_cost_usd'], 0.25)

    def test_timeout_stops_process_group_and_keeps_usage_unknown(self):
        process = MagicMock(pid=123)
        process.communicate.side_effect = [factory.subprocess.TimeoutExpired('claude', 10), ('partial', '')]
        with patch.object(factory.subprocess, 'Popen', return_value=process), patch.object(factory.os, 'killpg') as kill:
            result, completed, raw, error, _ = factory.invoke(Path('/tmp'), 'task', 'rules', 'model', 0.25, 10)
        kill.assert_called_once_with(123, factory.signal.SIGKILL)
        self.assertEqual(result, {})
        self.assertFalse(completed)
        self.assertEqual(raw, 'partial')
        self.assertIn('usage unknown', error)

    def test_fixture_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                factory.prepare({'files': {'../escape': 'bad'}}, Path(directory))


if __name__ == '__main__':
    unittest.main()
