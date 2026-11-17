#!/usr/bin/env python3
"""Run one locally configured development reviewer; host performs any fallback.

No shell, provider dependency, paid discovery, or automatic configuration writes.
See ../references/DEVELOPMENT_REVIEW.md for the adapter and coordinator contract.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_identity import identity

LIMIT = 4 * 1024 * 1024
OPERATIONAL = {'auth', 'quota', 'unavailable', 'timeout', 'access', 'invalid_output'}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                   stderr=subprocess.PIPE, timeout=15).rstrip('\n')


def paths(repo, home):
    root = Path(git(repo, 'rev-parse', '--show-toplevel')).resolve()
    main = Path(git(repo, 'worktree', 'list', '--porcelain').splitlines()[0][9:]).resolve()
    result = [Path(home) / 'memory.md']
    for path in (main, root):
        memory = Path(home) / str(path).lstrip('/').replace('/', '-') / 'memory.md'
        if memory not in result:
            result.append(memory)
    return result


def preference(repo, home):
    value = None
    for path in paths(repo, home):
        if not path.exists():
            continue
        section = ''
        for line in path.read_text().splitlines():
            if line.startswith('## '):
                section = line[3:].strip()
            match = re.fullmatch(r'\s*(?:-\s*)?development_review:\s*(.*?)\s*', line)
            if section == 'Preferences' and match:
                value = match[1]
    return value


def local_path(value, repo, home):
    value = value.replace('$BULMA_HOME', str(home)).replace('$HOME', str(Path.home()))
    path = Path(value).expanduser()
    if not path.is_absolute() or path.resolve().is_relative_to(Path(repo).resolve()):
        raise ValueError('configuration and receipts must be absolute paths outside the worktree')
    path = path.resolve()
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    inside = subprocess.run(['git', '-C', str(parent), 'rev-parse', '--is-inside-work-tree'],
                            capture_output=True, text=True, timeout=15)
    if inside.returncode == 0 and inside.stdout.strip() == 'true':
        raise ValueError('configuration and receipts must stay outside Git')
    return path


def config(value, repo, home):
    data = json.loads(local_path(value, repo, home).read_text())
    if not isinstance(data, dict) or data.get('version') != 1 or data.get('read_only') is not True:
        raise ValueError('version=1 and read_only=true required')
    argv = data.get('adapter')
    if (not isinstance(argv, list) or not argv or len(argv) > 32
            or any(not isinstance(arg, str) or not arg or '\x00' in arg for arg in argv)
            or not Path(argv[0]).is_absolute()):
        raise ValueError('adapter must be a fixed argv with an absolute executable')
    candidates = data.get('candidates')
    if (not isinstance(candidates, list) or not 1 <= len(candidates) <= 20
            or any(not isinstance(c, str) or not re.fullmatch(r'[\w.-]{1,100}', c) for c in candidates)
            or len(set(candidates)) != len(candidates)):
        raise ValueError('ordered, unique candidate IDs required')
    for key, default, maximum in (('timeout_seconds', 600, 600),
                                  ('discovery_timeout_seconds', 15, 30),
                                  ('freshness_seconds', 300, 300)):
        number = data.get(key, default)
        if isinstance(number, bool) or not isinstance(number, (float, int)) or not math.isfinite(number) or not 0 < number <= maximum:
            raise ValueError(f'invalid {key}')
        data[key] = number
    return data


def call(argv, payload, directory, name, timeout):
    """Bound both process lifetime and output; preserve partial JSONL on failure."""
    inp, out, err = [directory / (name + suffix) for suffix in ('.input.json', '.jsonl', '.stderr')]
    inp.write_text(json.dumps(payload))
    reason = None
    with inp.open('rb') as stdin, out.open('wb') as stdout, err.open('wb') as stderr:
        try:
            proc = subprocess.Popen(argv, stdin=stdin, stdout=stdout, stderr=stderr,
                                    cwd=directory, start_new_session=True)
        except OSError:
            return '', 'unavailable'
        deadline = time.monotonic() + timeout
        try:
            while proc.poll() is None:
                if out.stat().st_size > LIMIT or err.stat().st_size > LIMIT:
                    reason = 'output_limit'
                    break
                if time.monotonic() >= deadline:
                    reason = 'timeout'
                    break
                time.sleep(0.02)
        finally:
            # Also stop descendants after their launcher exits.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                # A reaped process may no longer own this group on macOS.
                if proc.poll() is None:
                    reason = 'cleanup_failed'
                    try:
                        proc.kill()
                    except OSError:
                        pass
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                reason = 'cleanup_failed'
        if reason != 'cleanup_failed' and (out.stat().st_size > LIMIT or err.stat().st_size > LIMIT):
            reason = 'output_limit'
        reason = reason or ('unavailable' if proc.returncode else None)
    with out.open('rb') as stream:
        text = stream.read(LIMIT).decode('utf-8', errors='replace')
    return text, reason


def fresh(record, seconds):
    try:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(record['checked_at'])).total_seconds()
        return 0 <= age <= seconds
    except (KeyError, ValueError, TypeError):
        return False


def select(data, cfg, authors):
    families = [identity(author).get('family') for author in authors]
    if not families or not all(families):
        return None
    candidates = data.get('candidates')
    if not isinstance(candidates, list) or len(candidates) > 100:
        raise ValueError('invalid discovery candidates')
    for key in cfg['candidates']:
        matches = [c for c in candidates if isinstance(c, dict) and c.get('id') == key]
        if len(matches) != 1:
            continue
        candidate = matches[0]
        actual = identity(candidate.get('identity'))
        if not actual.get('family') or actual['family'] in families:
            continue
        blocked = False
        for name in ('access', 'quota'):
            status = candidate.get(name)
            if isinstance(status, dict) and fresh(status, cfg['freshness_seconds']) and status.get('available') is False:
                blocked = True
        if not blocked:
            return candidate
    return None


def finding(value):
    return (isinstance(value, dict) and value.get('axis') in ('spec', 'quality')
            and all(isinstance(value.get(k), str) and value[k].strip() for k in ('id', 'message', 'evidence')))


def verdict(value, head):
    return (isinstance(value, dict) and value.get('type') == 'result' and value.get('head') == head
            and all(value.get(k) in ('pass', 'fail') for k in ('spec_verdict', 'quality_verdict')))


def parse(text, head):
    findings, results, identities, reason = [], [], [], None
    for line in text.splitlines():
        try:
            event = json.loads(line)
            kind = event.get('type')
            if kind == 'finding' and finding(event.get('finding')):
                if event['finding'] not in findings:
                    findings.append(event['finding'])
            elif kind == 'identity':
                identities.append(identity(event.get('identity')))
            elif kind == 'result' and verdict(event, head):
                results.append(event)
                if set(event) != {'type', 'head', 'spec_verdict', 'quality_verdict'}:
                    reason = 'invalid_output'
                    # Preserve recognizable findings even from a malformed envelope.
                    items = event.get('findings', [])
                    if isinstance(items, list):
                        findings.extend(f for f in items if finding(f) and f not in findings)
            elif kind == 'error' and event.get('reason') in OPERATIONAL:
                reason = reason or event['reason']
            else:
                reason = 'invalid_output'
        except (ValueError, AttributeError, TypeError):
            reason = 'invalid_output'
    executor = identities[0] if len(identities) == 1 else {}
    result = results[0] if len(results) == 1 else None
    if len(results) != 1:
        reason = reason or 'invalid_output'
    # Negative verdicts are evidence even if the process subsequently fails.
    failures = {k for r in results for k in ('spec_verdict', 'quality_verdict') if r[k] == 'fail'}
    return findings, executor, result, failures, reason


def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(path)
    return data


def snapshot(repo, request):
    if not re.fullmatch(r'[\w.-]{1,160}', request.get('round_id', '')):
        raise ValueError('round_id must identify job, ticket and review round')
    if git(repo, 'rev-parse', 'HEAD') != request.get('head') or git(repo, 'status', '--porcelain'):
        raise ValueError('review requires the pinned HEAD and a clean worktree')
    for key in ('head', 'base'):
        if not re.fullmatch(r'[0-9a-f]{40,64}', request.get(key, '')):
            raise ValueError(f'{key} must be a full commit SHA')
    for key in ('task', 'spec'):
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise ValueError(f'{key} text required')
    for key in ('context', 'evidence', 'implementation'):
        if not isinstance(request.get(key), list) or not request[key]:
            raise ValueError(f'{key} required (use explicit unknown identity or unverified evidence)')
    payload = {key: request[key] for key in ('round_id', 'head', 'base', 'task', 'spec', 'context', 'evidence')}
    payload.update(operation='review', version=1, repo=str(Path(repo).resolve()), read_only=True,
                   diff=git(repo, 'diff', '--no-ext-diff', '--no-textconv', request['base'], request['head'], '--'),
                   contract=(Path(__file__).resolve().parents[2] / 'bulma-feature-delivery/nodes/reviewer.md').read_text())
    if len(json.dumps(payload).encode()) > LIMIT:
        raise ValueError('review payload exceeds 4 MiB; narrow the ticket')
    digest = hashlib.sha256(json.dumps([payload, request['implementation']], sort_keys=True).encode()).hexdigest()
    return payload, digest


def complete(record, result):
    for key in ('spec_verdict', 'quality_verdict'):
        record[key] = result[key]
    for item in record['findings']:
        record[item['axis'] + '_verdict'] = 'fail'
    for key in record.get('failed_axes', []):
        record[key] = 'fail'
    record['action'] = 'complete'
    return record


def operate(repo, home, request, fallback=None):
    pref = preference(repo, home)
    if not re.fullmatch(r'[\w.-]{1,160}', request.get('round_id', '')):
        raise ValueError('round_id must identify job, ticket and review round')
    directory = local_path(str(paths(repo, home)[-1].parent / 'development-review' / request['round_id']), repo, home)
    # Configuration changes cannot discard an already reserved round or its findings.
    if pref in (None, 'off') and not (directory / 'receipt.json').exists():
        return dict(mode='default', action='spawn_worker', reason='not_configured', diversity_verified=False, findings=[])
    payload, digest = snapshot(repo, request)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = directory / 'receipt.json'
        record = json.loads(path.read_text()) if path.exists() else None
        if record and record['fingerprint'] != digest:
            raise ValueError('round payload changed; use the next graph review round')
        if fallback is not None:
            if not record or record['action'] != 'spawn_worker' or not verdict(fallback, request['head']):
                raise ValueError('fallback requires a pending receipt and a valid pinned verdict')
            items = fallback.get('findings', [])
            if not isinstance(items, list) or not all(finding(f) for f in items):
                raise ValueError('invalid fallback findings')
            record['findings'].extend(f for f in items if f not in record['findings'])
            record['executor'] = identity(fallback.get('identity'))
            record['finished_at'] = timestamp()
            return save(path, complete(record, fallback))
        if record and record['action'] != 'running':
            return record
        if record:
            log = directory / 'review.jsonl'
            with log.open('rb') if log.exists() else open(os.devnull, 'rb') as stream:
                partial = stream.read(LIMIT).decode('utf-8', errors='replace')
            findings, executor, _, failed, _ = parse(partial, request['head'])
            record.update(findings=findings, alternative_executor=executor, failed_axes=sorted(failed),
                          reason='interrupted', action='spawn_worker', mode='fallback')
            return save(path, record)
        record = dict(version=1, head=request['head'], round_id=request['round_id'], fingerprint=digest,
                      mode='fallback', action='running', reason=None, diversity_verified=False,
                      executor={}, findings=[], failed_axes=[], started_at=timestamp(), receipt=str(path))
        save(path, record)  # Durable reservation before any external call; resume never spends twice.
        try:
            cfg = config(pref, repo, home)
        except (ValueError, TypeError, OSError) as exc:
            record.update(reason='invalid_config', diagnostic=str(exc), action='spawn_worker')
            return save(path, record)
        text, reason = call(cfg['adapter'], dict(version=1, operation='discover', candidates=cfg['candidates']),
                            directory, 'discovery', cfg['discovery_timeout_seconds'])
        record['discovered_at'] = timestamp()
        candidate = None
        if not reason:
            try:
                candidate = select(json.loads(text), cfg, request['implementation'])
            except (ValueError, TypeError, AttributeError):
                reason = 'invalid_discovery'
        if not candidate:
            record.update(reason=reason or 'no_eligible_candidate',
                          action='blocked' if reason == 'cleanup_failed' else 'spawn_worker')
            return save(path, record)
        record['candidate'] = candidate
        save(path, record)
        payload['candidate'] = candidate['id']  # Never execute commands from discovery output.
        text, process_reason = call(cfg['adapter'], payload, directory, 'review', cfg['timeout_seconds'])
        findings, executor, result, failed, reason = parse(text, request['head'])
        if process_reason and reason == 'invalid_output':
            reason = process_reason
        record.update(findings=findings, alternative_executor=executor, failed_axes=sorted(failed))
        expected = identity(candidate.get('identity'))
        diverse = bool(executor.get('family') and all(
            executor.get(key) == expected.get(key) for key in ('model', 'family')))
        record['diversity_verified'] = diverse
        # Product edits or a moved HEAD invalidate completion, including otherwise clean output.
        try:
            snapshot(repo, request)
        except (ValueError, subprocess.SubprocessError):
            record.update(reason='snapshot_changed', action='blocked', diversity_verified=False)
            return save(path, record)
        if process_reason == 'cleanup_failed':
            record.update(reason=process_reason, action='blocked', diversity_verified=False)
            return save(path, record)
        if failed:
            record.update(mode='alternative', executor=executor, reason=reason or process_reason or
                          (None if diverse else 'identity_unverified'), finished_at=timestamp())
            return save(path, complete(record, result or dict(spec_verdict='fail', quality_verdict='fail')))
        if result and not reason and not process_reason and diverse:
            record.update(mode='alternative', executor=executor, finished_at=timestamp())
            return save(path, complete(record, result))
        record.update(mode='fallback', action='spawn_worker', diversity_verified=False,
                      reason=reason or process_reason or 'identity_unverified')
        return save(path, record)


def execute(repo, home, request):
    return operate(repo, home, request)


def finish(repo, home, request, fallback):
    return operate(repo, home, request, fallback)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--home', type=Path, default=Path(os.environ.get('BULMA_HOME', Path.home() / '.bulma')))
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--finish', type=Path, help='Finalize the one host fallback worker result')
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text())
        fallback = json.loads(args.finish.read_text()) if args.finish else None
        result = operate(args.repo, args.home.resolve(), request, fallback)
        print(json.dumps(result, indent=2))
        return 2 if result['action'] == 'blocked' else 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, f'development-review: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
