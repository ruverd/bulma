#!/usr/bin/env python3
"""Opt-in paired coder pilot. Never called by CI; artifacts stay outside the repo."""
import argparse
import hashlib
import json
import math
import os
import signal
from pathlib import Path
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def prepare(case, workspace):
    for name, content in case['files'].items():
        target = workspace / name
        if not target.resolve().is_relative_to(workspace.resolve()):
            raise ValueError('Fixture path leaves workspace')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def grade(case, workspace):
    try:
        result = subprocess.run(
            ['node', '--input-type=module', '-e', "import assert from 'node:assert/strict';\n" + case['checks']],
            cwd=workspace, capture_output=True, text=True, timeout=10)
        return {'passed': result.returncode == 0, 'log': result.stdout + result.stderr}
    except subprocess.TimeoutExpired:
        return {'passed': False, 'log': 'Verifier timed out'}


def summarize(rows):
    summary = {}
    for arm in sorted({row['arm'] for row in rows}):
        group = [row for row in rows if row['arm'] == arm]
        correct = sum(row['passed'] and row['completed'] for row in group)
        known_cost = all(isinstance(row.get('cost_usd'), (int, float)) for row in group)
        cost = sum(row['cost_usd'] for row in group) if known_cost else None
        summary[arm] = {'runs': len(group), 'correct': correct, 'cost_usd': cost,
                        'cost_per_correct': cost / correct if cost is not None and correct else None}
    return summary


def invoke(workspace, prompt, instructions, model, budget, timeout):
    command = ['claude', '-p', '--output-format', 'json', '--model', model,
               '--max-budget-usd', str(budget), '--tools', 'Read,Write,Edit,Bash',
               '--allowedTools', 'Read', 'Write', 'Edit', 'Bash(node *)',
               '--permission-mode', 'acceptEdits', '--disable-slash-commands',
               '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
               '--setting-sources', '', '--settings', '{"autoMemoryEnabled":false,"disableAllHooks":true}',
               '--no-session-persistence', '--system-prompt', instructions, '--', prompt]
    start = time.monotonic()
    proc = subprocess.Popen(command, cwd=workspace, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)
    try:
        raw, error = proc.communicate(timeout=timeout)
        try:
            result = json.loads(raw)
        except ValueError:
            result = {}
        completed = proc.returncode == 0 and result.get('subtype') == 'success' and not result.get('is_error')
        return result, completed, raw, error, time.monotonic() - start
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        raw, _ = proc.communicate()
        return {}, False, raw, 'Host timed out; usage unknown', time.monotonic() - start


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--model', required=True, help='Exact model id, not an alias')
    parser.add_argument('--runs', type=int, default=1)
    parser.add_argument('--arm', action='append', choices=['baseline', 'compact', 'ponytail'])
    parser.add_argument('--ponytail-file', type=Path, help='Optional pinned full Ponytail prompt, outside the repo')
    parser.add_argument('--case', action='append', default=[])
    parser.add_argument('--budget-per-run', type=float, default=0.25)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if args.runs < 1 or args.timeout < 1 or not math.isfinite(args.budget_per_run) or args.budget_per_run <= 0:
        parser.error('Runs, timeout and budget must be positive')
    if args.out.resolve().is_relative_to(ROOT):
        parser.error('Runtime artifacts must be outside the repository')
    cases = json.loads((HERE / 'cases.json').read_text())
    unknown = set(args.case) - {case['id'] for case in cases}
    if unknown:
        parser.error(f'Unknown cases: {sorted(unknown)}')
    cases = [case for case in cases if not args.case or case['id'] in args.case]
    lessons = (ROOT / 'skills/bulma-feature-delivery/LESSONS.md').read_text()
    baseline = ('You are implementing one bounded ticket in an isolated evaluation workspace. '
                'Use only files in this workspace. No network, git, packages or external repositories. '
                'Read the supplied files, write a regression test before fixing nontrivial logic, and run node tests. '
                'Implement the complete ticket with a minimal diff following local contracts. '
                'Report actual verification and remaining limitations. Do not claim tests ran unless they ran.\n\n' + lessons)
    variants = {'baseline': baseline, 'compact': baseline + '\n\n' + (HERE / 'compact-reuse.md').read_text()}
    if args.ponytail_file:
        variants['ponytail'] = baseline + '\n\n' + args.ponytail_file.read_text()
    if args.arm:
        if 'ponytail' in args.arm and not args.ponytail_file:
            parser.error('--arm ponytail requires --ponytail-file')
        variants = {arm: variants[arm] for arm in dict.fromkeys(args.arm)}
    args.out.mkdir(parents=True, exist_ok=False)
    meta = {'model': args.model, 'host': subprocess.check_output(['claude', '--version'], text=True).strip(),
            'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'cases_sha256': digest(json.dumps(cases, sort_keys=True)),
            'runner_sha256': digest(Path(__file__).read_text()),
            'instructions_sha256': {key: digest(value) for key, value in variants.items()},
            'runs_per_case_arm': args.runs, 'budget_per_run_usd': args.budget_per_run,
            'requested_budget_ceiling_usd': len(cases) * len(variants) * args.runs * args.budget_per_run,
            'scope': 'Reduced coder fixtures, not full factory or historical repository replay'}
    (args.out / 'manifest.json').write_text(json.dumps(meta, indent=2) + '\n')
    (args.out / 'cases.json').write_text(json.dumps(cases, indent=2) + '\n')
    (args.out / 'runner.py').write_text(Path(__file__).read_text())
    for arm, content in variants.items():
        (args.out / f'{arm}-instructions.txt').write_text(content)
    rows = []
    for repetition in range(args.runs):
        for index, case in enumerate(cases):
            # Alternate arm order; no shared workspace, memory, answer or conversation.
            order = list(variants)
            offset = (index + repetition) % len(order)
            arms = order[offset:] + order[:offset]
            for arm in arms:
                cell = args.out / f'{case["id"]}-{repetition + 1}-{arm}'
                cell.mkdir()
                with tempfile.TemporaryDirectory(prefix='bulma-coder-eval-') as temporary:
                    workspace = Path(temporary)
                    prepare(case, workspace)
                    prompt = case['prompt'] + '\nFiles: ' + ', '.join(case['files'])
                    result, completed, raw, error, elapsed = invoke(workspace, prompt, variants[arm], args.model, args.budget_per_run, args.timeout)
                    verification = grade(case, workspace)
                    # Preserve delivered source/tests without retaining generated directories.
                    delivered = {str(p.relative_to(workspace)): p.read_text() for p in workspace.rglob('*')
                                 if p.is_file() and p.suffix in ('.mjs', '.json', '.lock') and not p.is_symlink()}
                (cell / 'response.json').write_text(raw)
                (cell / 'stderr.txt').write_text(error)
                (cell / 'verifier.log').write_text(verification['log'])
                (cell / 'delivered.json').write_text(json.dumps(delivered, indent=2) + '\n')
                row = {'case': case['id'], 'run': repetition + 1, 'arm': arm, 'completed': completed,
                       'passed': verification['passed'], 'cost_usd': result.get('total_cost_usd'),
                       'usage': result.get('usage'), 'model_usage': result.get('modelUsage'),
                       'turns': result.get('num_turns'), 'seconds': elapsed,
                       'permission_denials': result.get('permission_denials')}
                rows.append(row)
                with (args.out / 'results.jsonl').open('a') as output:
                    output.write(json.dumps(row) + '\n')
                (args.out / 'summary.json').write_text(json.dumps(summarize(rows), indent=2) + '\n')
                print(json.dumps(row), flush=True)
    print(json.dumps(summarize(rows), indent=2))


if __name__ == '__main__':
    main()
