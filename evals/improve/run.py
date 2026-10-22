#!/usr/bin/env python3
"""Freeze an evidence-led prompt proposal, probe it, and prepare a review report."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNNER = ROOT / 'evals/factory/run.py'
spec = importlib.util.spec_from_file_location('factory', RUNNER)
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outside_checkout(path):
    path = path.resolve()
    if any((parent / '.git').exists() for parent in (path, *path.parents)):
        raise ValueError('Experiment artifacts must stay outside git checkouts')
    return path


def prepare(args):
    out = outside_checkout(args.out)
    if out.exists():
        raise ValueError('Proposal directory already exists; use a new proposal')
    if args.runs < 1 or args.timeout < 1 or not math.isfinite(args.budget_per_run) or args.budget_per_run <= 0:
        raise ValueError('Runs, timeout and budget must be positive')
    if not math.isfinite(args.min_savings) or not 0 < args.min_savings < 1:
        raise ValueError('min-savings must be between zero and one')
    report = read(args.lookback)
    evidence = next((c for c in report['clusters'] if c['cluster'] == args.cluster), None)
    if not evidence or evidence['prs'] < 5:
        raise ValueError('A global proposal requires recurrence on at least five distinct PRs')
    development, heldout = set(args.development), set(args.heldout)
    if not development or not heldout or development & heldout:
        raise ValueError('Development and held-out cases must be nonempty and disjoint')
    cases = read(ROOT / 'evals/factory/cases.json')
    ids = {case['id'] for case in cases}
    if (development | heldout) - ids:
        raise ValueError('Unknown case IDs')
    candidate = args.candidate.read_text()
    if not candidate.strip() or not args.hypothesis.strip():
        raise ValueError('Candidate and testable hypothesis must be nonempty')
    out.mkdir(parents=True)
    (out / 'candidate.txt').write_text(candidate)
    (out / 'baseline.txt').write_text(factory.baseline_instructions())
    write(out / 'lookback.json', report)
    write(out / 'cases.json', [c for c in cases if c['id'] in development | heldout])
    plan = {'schema_version': 1, 'cluster': args.cluster, 'hypothesis': args.hypothesis,
            'target': 'skills/bulma-feature-delivery/LESSONS.md',
            'evidence_prs': evidence['prs'], 'evidence_status': 'recurrence signal; source claims require review',
            'model': args.model, 'runs': args.runs, 'budget_per_run': args.budget_per_run,
            'timeout': args.timeout, 'min_savings': args.min_savings,
            'development': sorted(development), 'heldout': sorted(heldout),
            'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'runner_sha256': sha(RUNNER),
            'files': {name: sha(out / name) for name in ('candidate.txt', 'baseline.txt', 'cases.json', 'lookback.json')},
            'scope': 'Reduced coder fixtures; no automatic promotion or full-workflow claim'}
    write(out / 'plan.json', plan)
    (out / 'plan.sha256').write_text(sha(out / 'plan.json') + '\n')
    return {'proposal': str(out), 'status': 'prepared', 'evidence_prs': evidence['prs'],
            'requested_budget_ceiling_usd': len(development | heldout) * 2 * args.runs * args.budget_per_run}


def load_plan(directory):
    directory = outside_checkout(directory)
    if sha(directory / 'plan.json') != (directory / 'plan.sha256').read_text().strip():
        raise ValueError('Frozen plan changed; create a new proposal')
    plan = read(directory / 'plan.json')
    if sha(RUNNER) != plan['runner_sha256']:
        raise ValueError('Runner changed since proposal was frozen')
    for name, expected in plan['files'].items():
        if sha(directory / name) != expected:
            raise ValueError(f'Frozen input changed: {name}')
    return directory, plan


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def assess(directory, plan, phase):
    output = directory / phase
    expected = {(case, run, arm) for case in plan[phase] for run in range(1, plan['runs'] + 1)
                for arm in ('baseline', 'candidate')}
    if not (output / 'results.jsonl').exists():
        return {'status': 'pending' if not output.exists() else 'incomplete'}
    manifest = read(output / 'manifest.json')
    cases = [c for c in read(directory / 'cases.json') if c['id'] in plan[phase]]
    instructions = {'baseline': (directory / 'baseline.txt').read_text(),
                    'candidate': (directory / 'baseline.txt').read_text() + '\n\n' + (directory / 'candidate.txt').read_text()}
    required = {'model': plan['model'], 'runs_per_case_arm': plan['runs'],
                'budget_per_run_usd': plan['budget_per_run'], 'timeout_seconds': plan['timeout'],
                'source_sha': plan['source_sha'],
                'runner_sha256': plan['runner_sha256'], 'cases_sha256': factory.digest(json.dumps(cases, sort_keys=True)),
                'instructions_sha256': {k: factory.digest(v) for k, v in instructions.items()}}
    if any(manifest.get(k) != value for k, value in required.items()):
        raise ValueError(f'{phase} execution does not match the frozen plan')
    if phase == 'heldout':
        development = read(directory / 'development/manifest.json')
        if manifest.get('host') != development.get('host'):
            raise ValueError('Host version changed between development and held-out probes')
    rows = [json.loads(line) for line in (output / 'results.jsonl').read_text().splitlines() if line.strip()]
    keys = [(r['case'], r['run'], r['arm']) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) - expected:
        raise ValueError(f'{phase} has duplicate or unexpected trial rows')
    if set(keys) != expected:
        return {'status': 'incomplete', 'observed': len(keys), 'expected': len(expected)}
    if any(type(r.get(k)) is not bool for r in rows for k in ('passed', 'completed')):
        raise ValueError('Results require explicit boolean passed/completed values')
    success = lambda row: row['passed'] and row['completed'] and not row.get('permission_denials')
    index = dict(zip(keys, rows))
    regressions, improvements = [], []
    for case in plan[phase]:
        for run in range(1, plan['runs'] + 1):
            before, after = (success(index[(case, run, arm)]) for arm in ('baseline', 'candidate'))
            if before and not after:
                regressions.append({'case': case, 'run': run})
            if after and not before:
                improvements.append({'case': case, 'run': run})
    metrics = {}
    for arm in ('baseline', 'candidate'):
        group = [r for r in rows if r['arm'] == arm]
        correct = sum(success(r) for r in group)
        cost = sum(r['cost_usd'] for r in group) if all(number(r.get('cost_usd')) for r in group) else None
        seconds = sum(r['seconds'] for r in group) if all(number(r.get('seconds')) for r in group) else None
        metrics[arm] = {'runs': len(group), 'correct': correct, 'cost_usd': cost, 'seconds': seconds,
                        'cost_per_correct': cost / correct if cost is not None and correct else None}
    before, after = (metrics[a]['cost_per_correct'] for a in ('baseline', 'candidate'))
    savings = (before - after) / before if before is not None and before > 0 and after is not None else None
    if regressions:
        status = 'reject'
    elif improvements or savings is not None and savings >= plan['min_savings']:
        status = 'pilot_pass'
    else:
        status = 'inconclusive'
    return {'status': status, 'metrics': metrics, 'paired_regressions': regressions,
            'paired_improvements': improvements, 'cost_per_correct_savings': savings,
            'inference_cost_usd': sum(m['cost_usd'] for m in metrics.values()) if all(m['cost_usd'] is not None for m in metrics.values()) else None}


def probe(args):
    directory, plan = load_plan(args.proposal)
    if args.phase == 'heldout' and assess(directory, plan, 'development')['status'] != 'pilot_pass':
        raise ValueError('Held-out probe requires a completed development pilot_pass')
    output = directory / args.phase
    if output.exists():
        raise ValueError('Phase already attempted; preserve evidence and create a new proposal for retries')
    command = [sys.executable, str(RUNNER), '--out', str(output), '--model', plan['model'],
               '--runs', str(plan['runs']), '--budget-per-run', str(plan['budget_per_run']),
               '--timeout', str(plan['timeout']), '--arm', 'baseline', '--arm', 'candidate',
               '--baseline-file', str(directory / 'baseline.txt'), '--candidate-file', str(directory / 'candidate.txt'),
               '--cases-file', str(directory / 'cases.json')]
    for case in plan[args.phase]:
        command += ['--case', case]
    if args.dry_run:
        return {'command': command, 'model_calls': len(plan[args.phase]) * plan['runs'] * 2,
                'requested_budget_ceiling_usd': len(plan[args.phase]) * plan['runs'] * 2 * plan['budget_per_run']}
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        return {'status': 'execution_failed', 'exit_code': result.returncode, 'evidence': str(output)}
    return assess(directory, plan, args.phase)


def report(args):
    directory, plan = load_plan(args.proposal)
    phases = {phase: assess(directory, plan, phase) for phase in ('development', 'heldout')}
    statuses = [p['status'] for p in phases.values()]
    if 'reject' in statuses:
        status = 'reject'
    elif statuses == ['pilot_pass', 'pilot_pass']:
        status = 'review_candidate'
    else:
        status = 'inconclusive'
    costs = [p.get('inference_cost_usd') for p in phases.values()]
    result = {'status': status, 'cluster': plan['cluster'], 'hypothesis': plan['hypothesis'],
              'phases': phases, 'probe_cost_usd': sum(costs) if all(number(c) for c in costs) else None,
              'promotion': 'manual review only; real-task validation still required',
              'unmeasured_costs': 'proposal authoring, preparation, human review and other optimizer sessions',
              'limitations': 'Small synthetic pilot; no statistical equivalence, full-workflow or rare-defect guarantee'}
    write(directory / 'report.json', result)
    (directory / 'review.md').write_text(
        '# Improvement proposal\n\n' + plan['hypothesis'] + '\n\n'
        + f"Cluster: {plan['cluster']}. Recurrence signal: {plan['evidence_prs']} PRs.\n\n"
        + f"Result: {status}. Development: {statuses[0]}. Held-out: {statuses[1]}.\n\n"
        + 'Review report.json and raw execution evidence. Confirm source observations, inspect delivered code, '
        + 'and validate on real tasks before proposing a production change. The instruction amendment is candidate.txt. '
        + 'No skill was edited or PR opened by this command.\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare', help='Freeze one reviewed hypothesis and disjoint fixture split')
    for name in ('lookback', 'candidate', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('cluster', 'hypothesis', 'model'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--development', nargs='+', required=True)
    p.add_argument('--heldout', nargs='+', required=True)
    p.add_argument('--runs', type=int, default=3)
    p.add_argument('--budget-per-run', type=float, default=0.25)
    p.add_argument('--timeout', type=int, default=180)
    p.add_argument('--min-savings', type=float, default=0.1)
    p.set_defaults(action=prepare)
    p = commands.add_parser('probe', help='Run frozen baseline/candidate comparison; incurs model cost')
    p.add_argument('--proposal', type=Path, required=True)
    p.add_argument('--phase', choices=('development', 'heldout'), required=True)
    p.add_argument('--dry-run', action='store_true')
    p.set_defaults(action=probe)
    p = commands.add_parser('report', help='Write a review packet; never promotes or edits live skills')
    p.add_argument('--proposal', type=Path, required=True)
    p.set_defaults(action=report)
    args = parser.parse_args()
    try:
        result = args.action(args)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 4


if __name__ == '__main__':
    sys.exit(main())
