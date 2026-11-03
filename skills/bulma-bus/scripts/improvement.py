#!/usr/bin/env python3
"""Record explicit process assessments and compare delivery outcomes offline."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import runtime


def required(row, *keys):
    for key in keys:
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError(key + ' must be a nonempty string')


def references(paths):
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        raise ValueError('evidence must be a list of file paths')
    return [{'path': str(Path(p).resolve()),
             'sha256': hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in paths]


def intact(refs):
    try:
        return bool(refs) and all(
            hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in refs)
    except OSError:
        return False


def record(repo, directory, row):
    row = dict(row)
    required(row, 'run', 'task', 'variant', 'workflow', 'configuration', 'kind')
    if not re.fullmatch(r'[0-9a-f]{64}', row['workflow']):
        raise ValueError('workflow must be a SHA-256 content fingerprint')
    trial = row.setdefault('trial', 1)
    if type(trial) is not int or trial < 1:
        raise ValueError('trial must be a positive integer')
    kind = row['kind']
    if kind == 'assessment':
        required(row, 'criterion')
        if row.get('status') not in ('pass', 'fail', 'unknown'):
            raise ValueError('assessment status must be pass, fail or unknown')
        if row.get('method') not in ('human', 'deterministic', 'model'):
            raise ValueError('assessment method must be human, deterministic or model')
        if row['status'] == 'fail':
            required(row, 'cause', 'prevention', 'counterexample')
        key = [kind, row['run'], row['criterion']]
    elif kind == 'outcome':
        if row.get('status') not in ('accepted', 'rejected', 'blocked', 'cancelled', 'unknown'):
            raise ValueError('invalid delivery outcome')
        required(row, 'sha', 'starting_sha', 'environment')
        if row.get('scope') not in ('delivery', 'replay'):
            raise ValueError('outcome scope must be delivery or replay')
        artifact_repo = row.get('artifact_repo', repo)
        if row['sha'] != runtime.git(artifact_repo, 'rev-parse', 'HEAD').decode().strip():
            raise ValueError('outcome SHA must match the current head')
        if (row['status'] == 'accepted' and row['scope'] == 'delivery'
                and runtime.git(artifact_repo, 'status', '--porcelain')):
            raise ValueError('accepted delivery requires a clean artifact checkout')
        try:
            row['artifact_identity'] = runtime.identity(artifact_repo, [], row['environment'])
        except (OSError, subprocess.CalledProcessError) as exc:
            if row['status'] == 'accepted':
                raise
            row['artifact_identity'] = None
            row['artifact_error'] = str(exc)
        for field in ('cost_usd', 'human_ms'):
            value = row.get(field)
            if value is not None:
                if (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                    raise ValueError(field + ' must be nonnegative and finite, or null')
                required(row, 'cost_source' if field == 'cost_usd' else 'human_time_source')
        if row.get('cost_usd') is not None and row.get('cost_kind') != 'api_billed':
            raise ValueError('cost_usd requires cost_kind=api_billed; estimates stay separate')
        if row.get('first_pass') is not None:
            if type(row['first_pass']) is not bool or (row['first_pass'] and row['status'] != 'accepted'):
                raise ValueError('first_pass must be a boolean; true requires accepted')
        metrics = row.get('metrics', [])
        row['metrics'] = references(metrics)
        samples = set()
        for ref in row['metrics']:
            sample = json.loads(Path(ref['path']).read_text())
            required(sample, 'run', 'sample_id', 'graph', 'node')
            if sample.get('run') != row['run'] or sample.get('kind') not in ('active', 'wait'):
                raise ValueError('metrics must belong to this run')
            if sample['sample_id'] in samples:
                raise ValueError('duplicate metric sample')
            samples.add(sample['sample_id'])
            if type(sample.get('duration_ms')) is not int or sample['duration_ms'] < 0:
                raise ValueError('invalid runtime duration')
        key = [kind, row['run']]
    else:
        raise ValueError('kind must be assessment or outcome')
    row['evidence'] = references(row.get('evidence', []))
    if row.get('status') in ('accepted', 'fail') and not row['evidence']:
        raise ValueError('accepted outcomes and failed assessments require evidence')
    row['repo'] = str(Path(runtime.git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve())
    row['schema'] = 1
    folder = runtime.outside_repo(directory, repo)
    path = folder / (runtime.digest(key) + '.json')
    if path.exists():
        old = json.loads(path.read_text())
        for field in ('repo', 'task', 'trial', 'variant', 'workflow', 'configuration',
                      'starting_sha', 'environment', 'scope', 'task_fingerprint'):
            if old.get(field) != row.get(field):
                raise ValueError('run identity changed: ' + field)
    runtime.write_json(path, row)
    return row


def load(directory, repo):
    folder = runtime.outside_repo(directory, repo)
    root = str(Path(runtime.git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve())
    rows = []
    for path in sorted(folder.glob('*.json')):
        row = json.loads(path.read_text())
        if row.get('schema') != 1 or row.get('repo') != root:
            raise ValueError('foreign or unsupported improvement record: ' + str(path))
        rows.append(row)
    return rows


def delivery_totals(rows):
    outcomes = Counter(r['status'] for r in rows)
    costs = [r['cost_usd'] for r in rows if r.get('cost_usd') is not None]
    human = [r['human_ms'] for r in rows if r.get('human_ms') is not None]
    first_pass = [r['first_pass'] for r in rows if r.get('first_pass') is not None]
    accepted = outcomes['accepted']
    totals = {'runs': len(rows), 'tasks': len({r['task'] for r in rows}),
              'outcomes': dict(outcomes), 'accepted_runs': accepted,
              'first_pass_samples': len(first_pass),
              'first_pass_accepted_runs': sum(first_pass) if first_pass else None,
              'cost_samples': len(costs), 'known_cost_usd': sum(costs) if costs else None,
              'cost_per_accepted_run_usd': sum(costs) / accepted
              if accepted and len(costs) == len(rows) else None,
              'human_samples': len(human), 'known_human_ms': sum(human) if human else None,
              'human_ms_per_accepted_run': sum(human) / accepted
              if accepted and len(human) == len(rows) else None,
              'active_ms': 0, 'wait_ms': 0, 'metric_samples': 0, 'runs_with_metrics': 0}
    for row in rows:
        refs = row.get('metrics', [])
        if refs and intact(refs):
            totals['runs_with_metrics'] += 1
            for ref in refs:
                sample = json.loads(Path(ref['path']).read_text())
                totals[sample['kind'] + '_ms'] += sample['duration_ms']
                totals['metric_samples'] += 1
    return totals


def report(rows):
    groups = defaultdict(list)
    assessments = defaultdict(list)
    invalid = 0
    for row in rows:
        if row.get('evidence') and not intact(row['evidence']):
            invalid += 1
            if row['kind'] == 'assessment':
                continue
            row = dict(row, status='unknown', cost_usd=None, human_ms=None, first_pass=None)
        key = (row['variant'], row['workflow'], row['configuration'])
        if row['kind'] == 'outcome':
            groups[(*key, row['scope'])].append(row)
        else:
            assessments[(*key, row['criterion'])].append(row)
    process = []
    for (variant, workflow, configuration, criterion), items in sorted(assessments.items()):
        counts = Counter(r['status'] for r in items)
        verified = Counter(r['status'] for r in items if r['method'] != 'model')
        causes = defaultdict(list)
        for row in items:
            if row['status'] == 'fail' and row['method'] in ('human', 'deterministic'):
                causes[row['cause']].append(row)
        candidates = []
        for cause, failures in sorted(causes.items()):
            tasks = sorted({r['task'] for r in failures})
            if len(tasks) >= 2:
                candidates.append({'cause': cause, 'tasks': tasks, 'runs': [r['run'] for r in failures],
                                   'preventions': sorted({r['prevention'] for r in failures}),
                                   'counterexamples': sorted({r['counterexample'] for r in failures})})
        process.append({'variant': variant, 'workflow': workflow, 'configuration': configuration,
                        'criterion': criterion, 'observations': len(items), 'classifications': dict(counts),
                        'verified_classifications': dict(verified),
                        'failure_rate': verified['fail'] / (verified['pass'] + verified['fail'])
                        if verified['pass'] + verified['fail'] else None, 'candidates': candidates})
    return {'invalid_evidence_records': invalid, 'deliveries': [
        dict(variant=v, workflow=w, configuration=c, scope=s, **delivery_totals(items))
        for (v, w, c, s), items in sorted(groups.items())], 'process': process}


def compare(rows, baseline, candidate):
    if baseline == candidate:
        raise ValueError('choose two different variants')
    selected = {}
    for name in (baseline, candidate):
        items = [r for r in rows if r['kind'] == 'outcome' and r['variant'] == name]
        if len({(r['workflow'], r['configuration']) for r in items}) != 1:
            raise ValueError('variant must have exactly one workflow/configuration: ' + name)
        pairs = {}
        for row in items:
            if not re.fullmatch(r'[0-9a-f]{64}', row.get('task_fingerprint', '')):
                raise ValueError('comparison requires a task_fingerprint: ' + row['run'])
            key = (row['task'], row['trial'])
            if key in pairs:
                raise ValueError('duplicate task/trial for variant ' + name)
            if row.get('evidence') and not intact(row['evidence']):
                raise ValueError('comparison evidence changed: ' + row['run'])
            pairs[key] = row
        selected[name] = pairs
    keys = sorted(selected[baseline].keys() & selected[candidate].keys())
    for key in keys:
        a, b = selected[baseline][key], selected[candidate][key]
        if any(a.get(field) != b.get(field) for field in
               ('starting_sha', 'environment', 'scope', 'task_fingerprint', 'runner_fingerprint')):
            raise ValueError('unmatched task conditions: ' + str(key))
    return {'paired_trials': len(keys), 'independent_tasks': len({k[0] for k in keys}),
            'unmatched': {name: len(pairs.keys() - set(keys)) for name, pairs in selected.items()},
            'baseline_accepted_candidate_not': sum(
                selected[baseline][k]['status'] == 'accepted' and
                selected[candidate][k]['status'] != 'accepted' for k in keys),
            'variants': {name: delivery_totals([pairs[k] for k in keys])
                         for name, pairs in selected.items()}, 'promotion': 'not_evaluated'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('record', 'report', 'compare'):
        p = sub.add_parser(action)
        p.add_argument('--repo', required=True)
        p.add_argument('--directory', required=True)
        if action == 'record':
            p.add_argument('--input', required=True)
        if action == 'compare':
            p.add_argument('--baseline', required=True)
            p.add_argument('--candidate', required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == 'record':
            result = record(args.repo, args.directory, json.loads(Path(args.input).read_text()))
        else:
            rows = load(args.directory, args.repo)
            result = report(rows) if args.action == 'report' else compare(rows, args.baseline, args.candidate)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
