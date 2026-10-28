#!/usr/bin/env python3
"""Capture bounded command evidence and host-reported performance measurements."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import time
import uuid


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def identity(repo, command, environment):
    repo = Path(git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    untracked = []
    for name in git(repo, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0'):
        if name:
            path = repo / os.fsdecode(name)
            content = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            untracked.append([os.fsdecode(name), hashlib.sha256(content).hexdigest()])
    data = {
        'repo': str(repo), 'head': git(repo, 'rev-parse', 'HEAD').decode().strip(),
        'diff': hashlib.sha256(git(repo, 'diff', '--binary', 'HEAD', '--')).hexdigest(),
        'untracked': untracked, 'command': command, 'environment': environment,
    }
    # Dirty/uninitialized submodules cannot supply reusable evidence.
    submodules = git(repo, 'submodule', 'status', '--recursive').decode()
    data['submodules'] = submodules
    data['reusable'] = bool(environment) and not any(
        line.startswith(('-', '+', 'U')) for line in submodules.splitlines())
    return data


def outside_repo(path, repo):
    path = Path(path).resolve()
    root = Path(git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    if path == root or root in path.parents:
        raise ValueError('runtime evidence must live outside the repository')
    return path


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    tmp.replace(path)


def log_capture_available():
    executable = shutil.which('trail')
    if not executable:
        return False
    try:
        help_result = subprocess.run([executable, '--help'], capture_output=True, text=True, timeout=5)
        return help_result.returncode == 0 and bool(re.search(
            r'^\s+run(?:\s|$)', help_result.stdout, re.MULTILINE))
    except (OSError, subprocess.TimeoutExpired):
        return False


def run(args):
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise ValueError('run requires a command after --')
    folder = outside_repo(args.directory, args.repo) / uuid.uuid4().hex
    folder.mkdir(parents=True)
    before = identity(args.repo, command, args.environment)
    capture = 'trail' if args.trail and log_capture_available() else 'file'
    argv = ['trail', 'run', '--', *command] if capture == 'trail' else command
    started = time.monotonic()
    with (folder / 'output.log').open('wb') as log:
        try:
            process = subprocess.Popen(argv, cwd=args.repo, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                result = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                result = 124
        except OSError as exc:
            log.write(str(exc).encode())
            result = 127
    after = identity(args.repo, command, args.environment)
    record = {'version': 1, 'identity': before, 'fingerprint': digest(before),
              'stable': before == after, 'exit_code': result, 'capture': capture,
              'duration_ms': round((time.monotonic() - started) * 1000),
              'log': str(folder / 'output.log'),
              'log_sha256': hashlib.sha256((folder / 'output.log').read_bytes()).hexdigest(),
              'recorded_at': time.time()}
    write_json(folder / 'result.json', record)
    print(json.dumps({'evidence': str(folder / 'result.json'), 'exit_code': result,
                      'duration_ms': record['duration_ms'], 'capture': capture}))
    return result if 0 <= result <= 255 else 1


def reusable(record, current):
    return (record.get('version') == 1 and record.get('exit_code') == 0
            and record.get('stable') is True and current.get('reusable') is True
            and record.get('identity') == current
            and record.get('fingerprint') == digest(current)
            and Path(record.get('log', '')).is_file()
            and record.get('log_sha256') == hashlib.sha256(Path(record['log']).read_bytes()).hexdigest())


def check(args):
    record = json.loads(Path(args.evidence).read_text())
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise ValueError('check requires the exact command after --')
    current = identity(args.repo, command, args.environment)
    valid = reusable(record, current)
    print(json.dumps({'reusable': valid, 'fingerprint': digest(current)}))
    return 0 if valid else 1


def measure(args):
    data = json.loads(Path(args.input).read_text())
    required = ('run', 'graph', 'node', 'sample_id', 'duration_ms', 'kind')
    if not isinstance(data, dict) or any(key not in data for key in required):
        raise ValueError('measurement needs ' + ', '.join(required))
    if data['kind'] not in ('active', 'wait'):
        raise ValueError('kind must be active or wait')
    for key in ('duration_ms', 'input_tokens', 'output_tokens', 'cached_tokens', 'workers', 'retries'):
        value = data.get(key)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(key + ' must be a nonnegative integer or null')
    if data.get('rework') is not None and type(data['rework']) is not bool:
        raise ValueError('rework must be a boolean or null')
    if any(data.get(key) is not None for key in ('input_tokens', 'output_tokens', 'cached_tokens')):
        if not data.get('usage_source'):
            raise ValueError('token usage requires a host usage_source')
    folder = outside_repo(args.directory, args.repo)
    # Stable sample IDs replace retries of the same observation, never double-count.
    write_json(folder / (digest([data['run'], data['sample_id']]) + '.json'), data)
    return 0


def report(args):
    rows = [json.loads(p.read_text()) for p in Path(args.directory).glob('*.json')]
    groups = {}
    for row in rows:
        if args.run is not None and row['run'] != args.run:
            continue
        key = row['graph'] + '/' + row['node']
        item = groups.setdefault(key, {'samples': 0, 'active_ms': 0, 'wait_ms': 0,
                                       'input_tokens': None, 'output_tokens': None,
                                       'cached_tokens': None, 'usage_samples': 0,
                                       'retries': None, 'retry_samples': 0,
                                       'rework_samples': None, 'rework_observed_samples': 0,
                                       'rework_active_ms': None, 'rework_wait_ms': None})
        item['samples'] += 1
        item[row['kind'] + '_ms'] += row['duration_ms']
        if row.get('retries') is not None:
            item['retry_samples'] += 1
            item['retries'] = (item['retries'] or 0) + row['retries']
        if row.get('rework') is not None:
            item['rework_observed_samples'] += 1
            item['rework_samples'] = (item['rework_samples'] or 0) + int(row['rework'])
            for kind in ('active', 'wait'):
                field = 'rework_' + kind + '_ms'
                item[field] = (item[field] or 0) + (
                    row['duration_ms'] if row['rework'] and row['kind'] == kind else 0)
        if row.get('input_tokens') is not None:
            item['usage_samples'] += 1
        for name in ('input_tokens', 'output_tokens', 'cached_tokens'):
            if row.get(name) is not None:
                item[name] = (item[name] or 0) + row[name]
    print(json.dumps(groups, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('run', 'check'):
        p = sub.add_parser(name)
        p.add_argument('--repo', required=True)
        p.add_argument('--environment', default='')
        if name == 'run':
            p.add_argument('--directory', required=True)
            p.add_argument('--trail', action='store_true')
            p.add_argument('--timeout', type=float, default=180)
        else:
            p.add_argument('--evidence', required=True)
        p.add_argument('command', nargs=argparse.REMAINDER)
    p = sub.add_parser('measure')
    p.add_argument('--repo', required=True)
    p.add_argument('--directory', required=True)
    p.add_argument('--input', required=True)
    p = sub.add_parser('report')
    p.add_argument('--directory', required=True)
    p.add_argument('--run', help='limit phase totals to one delivery/run ID')
    args = parser.parse_args()
    try:
        return globals()[args.action](args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
