#!/usr/bin/env python3
"""Replay explicit task commands on fresh snapshots, retaining every attempted outcome."""
import argparse
from collections import Counter
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import random
import subprocess
from types import SimpleNamespace
import uuid

import improvement
import runtime


def command(value):
    if not isinstance(value, list) or not value or not all(isinstance(s, str) for s in value):
        raise ValueError('commands must be nonempty argv arrays')
    return value


def snapshot(source, sha, target):
    tree = runtime.git(source, 'ls-tree', '-r', sha).decode()
    if any(line.startswith('160000 ') for line in tree.splitlines()):
        raise ValueError('submodules need an explicit fixture before replay')
    target.mkdir()
    index = target.parent / 'snapshot.index'
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    try:
        subprocess.run(['git', '-C', str(source), 'read-tree', sha], env=env, check=True)
        subprocess.run(['git', '-C', str(source), 'checkout-index', '--all',
                        '--prefix=' + str(target) + '/'], env=env, check=True)
    finally:
        index.unlink(missing_ok=True)
    subprocess.run(['git', 'init', '-q', str(target)], check=True)
    runtime.git(target, 'add', '--force', '.')
    runtime.git(target, '-c', 'user.name=Replay', '-c', 'user.email=replay@example.invalid',
                '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
                'commit', '--allow-empty', '-qm', 'Starting snapshot')


def execute(argv, substitutions, repo, directory, environment, timeout):
    argv = command(argv)
    for key, value in substitutions.items():
        argv = [arg.replace('{' + key + '}', str(value)) for arg in argv]
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        runtime.run(SimpleNamespace(command=argv, repo=str(repo), directory=str(directory),
                                    environment=environment, trail=False, timeout=timeout))
    return json.loads(output.getvalue())


def run(manifest_path, output):
    manifest_path = Path(manifest_path).resolve()
    doc = json.loads(manifest_path.read_text())
    doc['runner_fingerprint'] = runtime.digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in (Path(__file__), Path(runtime.__file__),
                                                         Path(improvement.__file__))})
    source = Path(doc['repo']).resolve()
    output = runtime.outside_repo(output, source)
    if output.exists():
        raise ValueError('use a fresh output directory; completed trials are never overwritten')
    improvement.required(doc, 'environment')
    repetitions = doc.get('repetitions', 3)
    timeout = doc.get('timeout_seconds', 180)
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError('repetitions must be a positive integer')
    if type(timeout) not in (int, float) or not 0 < timeout < float('inf'):
        raise ValueError('timeout_seconds must be positive and finite')
    tasks, variants = doc['tasks'], doc['variants']
    if not tasks or not variants:
        raise ValueError('tasks and variants cannot be empty')
    if len({t['id'] for t in tasks}) != len(tasks) or len({v['name'] for v in variants}) != len(variants):
        raise ValueError('task and variant names must be unique')
    for task in tasks:
        improvement.required(task, 'id', 'ref', 'prompt')
        command(task['verify'])
        task['starting_sha'] = runtime.git(source, 'rev-parse', '--verify', '--end-of-options',
                                          task['ref'] + '^{commit}').decode().strip()
        task['task_fingerprint'] = runtime.digest({key: task[key] for key in
                                                  ('id', 'prompt', 'verify', 'starting_sha')})
    policies = {}
    for variant in variants:
        improvement.required(variant, 'name')
        command(variant['command'])
        if not isinstance(variant.get('configuration'), dict):
            raise ValueError('each variant needs an explicit configuration object')
        files = variant.get('policy_files', {})
        if not isinstance(files, dict) or not files:
            raise ValueError('each variant needs named policy_files')
        frozen = {}
        for name, path in files.items():
            if not name or Path(name).is_absolute() or '..' in Path(name).parts or name == '.':
                raise ValueError('policy names must stay inside the policy directory')
            frozen[name] = (manifest_path.parent / path).read_bytes()
        policies[variant['name']] = frozen
        variant['workflow'] = runtime.digest({
            'files': {name: hashlib.sha256(data).hexdigest() for name, data in frozen.items()},
            'command': variant['command'], 'configuration': variant['configuration']})
    plan = [{'task': t['id'], 'variant': v['name'], 'trial': trial, 'status': 'not_started'}
            for t in tasks for v in variants for trial in range(1, repetitions + 1)]
    random.Random(doc.get('seed', 0)).shuffle(plan)
    output.mkdir(parents=True)
    runtime.write_json(output / 'manifest.json', doc)
    runtime.write_json(output / 'plan.json', plan)
    for entry in plan:
        task = next(t for t in tasks if t['id'] == entry['task'])
        variant = next(v for v in variants if v['name'] == entry['variant'])
        run_id = uuid.uuid4().hex
        folder = output / run_id
        folder.mkdir()
        repo = folder / 'repo'
        entry.update(run=run_id, status='running')
        runtime.write_json(output / 'plan.json', plan)
        row = dict(entry, kind='outcome', scope='replay', workflow=variant['workflow'],
                   configuration=runtime.digest(variant['configuration']),
                   starting_sha=task['starting_sha'], task_fingerprint=task['task_fingerprint'],
                   environment=doc['environment'], runner_fingerprint=doc['runner_fingerprint'])
        try:
            snapshot(source, task['starting_sha'], repo)
            policy = folder / 'policy'
            for name, data in policies[variant['name']].items():
                path = policy / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            (folder / 'prompt.txt').write_text(task['prompt'])
            runtime.write_json(folder / 'configuration.json', variant['configuration'])
            substitutions = {'repo': repo, 'prompt': folder / 'prompt.txt', 'policy': policy,
                             'config': folder / 'configuration.json'}
            worker = execute(variant['command'], substitutions, repo, folder / 'evidence',
                             doc['environment'], timeout)
            results = [worker]
            status = 'blocked'
            policy_intact = all((policy / name).is_file() and (policy / name).read_bytes() == data
                                for name, data in policies[variant['name']].items())
            if worker['exit_code'] == 0 and policy_intact:
                verifier = execute(task['verify'], substitutions, repo, folder / 'evidence',
                                   doc['environment'], timeout)
                results.append(verifier)
                status = 'accepted' if verifier['exit_code'] == 0 else 'rejected'
                if verifier['exit_code'] in (75, 124, 130):
                    status = 'blocked'
            metric_refs, evidence = [], []
            for index, result in enumerate(results):
                record = json.loads(Path(result['evidence']).read_text())
                evidence.extend([result['evidence'], record['log']])
                metric = folder / ('metric-' + str(index) + '.json')
                runtime.write_json(metric, {'run': run_id, 'sample_id': str(index), 'graph': 'replay',
                                           'node': 'worker' if index == 0 else 'verify', 'kind': 'active',
                                           'duration_ms': result['duration_ms']})
                metric_refs.append(str(metric))
            row.update(status=status, artifact_repo=str(repo),
                       sha=runtime.git(repo, 'rev-parse', 'HEAD').decode().strip(),
                       evidence=evidence, metrics=metric_refs, policy_intact=policy_intact)
            improvement.record(source, output / 'outcomes', row)
            entry.update(run=run_id, status=status, exit_codes=[r['exit_code'] for r in results])
        except (OSError, ValueError, subprocess.CalledProcessError, KeyboardInterrupt) as exc:
            entry.update(run=run_id, status='blocked', error=str(exc) or 'interrupted')
            error = folder / 'error.json'
            runtime.write_json(error, {'error': str(exc) or 'interrupted'})
            row.update(status='blocked', sha=runtime.git(source, 'rev-parse', 'HEAD').decode().strip(),
                       evidence=[str(error)])
            row.pop('artifact_repo', None)
            improvement.record(source, output / 'outcomes', row)
            runtime.write_json(output / 'plan.json', plan)
            return 130 if isinstance(exc, KeyboardInterrupt) else 2
        runtime.write_json(output / 'plan.json', plan)
        if any(r['exit_code'] in (75, 124, 130) for r in results):
            return next(r['exit_code'] for r in results if r['exit_code'] in (75, 124, 130))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        code = run(args.manifest, args.output)
        plan = json.loads((Path(args.output) / 'plan.json').read_text())
        print(json.dumps({'output': str(Path(args.output).resolve()), 'exit_code': code,
                          'trials': dict(Counter(r['status'] for r in plan))}))
        return code
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
