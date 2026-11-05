#!/usr/bin/env python3
"""Collect a pinned PR snapshot and retain completed analysis while CI runs."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess

THREADS = '''query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
 repository(owner:$owner, name:$name) { pullRequest(number:$number) {
 reviewThreads(first:100, after:$endCursor) {
 pageInfo { hasNextPage endCursor }
 nodes { id isResolved isOutdated comments(first:1) {
 nodes { databaseId url author { login } body } } }
 } } } }'''
ARTIFACTS = ('AC.md', 'bound.json', 'coverage.json', 'analysis.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gh(*args):
    code, out, err = gh_result(*args)
    if code != 0:
        raise subprocess.CalledProcessError(code, ['gh', *args], out, err)
    return out


def gh_result(*args):
    proc = subprocess.run(['gh', *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout, proc.stderr


def forbidden(out, err):
    blob = (out or b'') + b'\n' + (err or b'')
    text = blob.decode('utf-8', 'replace')
    return 'HTTP 403' in text or '"status":"403"' in text or '"status": "403"' in text


def try_api(route, paginate=True, attempts=2):
    args = ['api', route]
    if paginate:
        args.extend(['--paginate', '--slurp'])
    last = None
    for _ in range(attempts):
        try:
            return gh(*args), None
        except subprocess.CalledProcessError as exc:
            last = exc
            if forbidden(exc.output, exc.stderr):
                break
    return None, last


def ci_error(name, exc):
    if forbidden(exc.output, exc.stderr):
        return 'HTTP 403 ' + name
    return name + ' unreadable'


def empty_checks():
    return b'[{"check_runs":[]}]'


def encode_keyed(items, key):
    return json.dumps([{key: items}]).encode()


def statuses_from(raw):
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    pages = data if isinstance(data, list) else [data]
    out = []
    for page in pages:
        if isinstance(page, dict) and isinstance(page.get('statuses'), list) and 'sha' in page:
            out.extend(item for item in page['statuses'] if isinstance(item, dict))
        elif isinstance(page, dict) and page.get('context'):
            out.append(page)
        elif isinstance(page, list):
            out.extend(item for item in page if isinstance(item, dict) and item.get('context'))
    return out


def actions_checks(raw, head):
    try:
        data = json.loads(raw or b'[]')
    except ValueError:
        return []
    pages = data if isinstance(data, list) else [data]
    checks = []
    for page in pages:
        runs = page.get('workflow_runs') if isinstance(page, dict) else None
        if not isinstance(runs, list):
            continue
        for run in runs:
            if not isinstance(run, dict):
                continue
            if run.get('head_sha') not in (None, head):
                continue
            checks.append({
                'id': run.get('id'),
                'name': run.get('name') or 'workflow',
                'head_sha': run.get('head_sha') or head,
                'status': run.get('status'),
                'conclusion': run.get('conclusion'),
                'html_url': run.get('html_url'),
            })
    return checks


PR_CHECK_BUCKET = {
    'pass': ('completed', 'success'),
    'fail': ('completed', 'failure'),
    'pending': ('in_progress', None),
    'skipping': ('completed', 'skipped'),
    'cancel': ('completed', 'cancelled'),
}


def pr_check_state(item):
    bucket = PR_CHECK_BUCKET.get(item.get('bucket') or '')
    if bucket:
        return bucket
    state = (item.get('state') or '').upper()
    if state == 'SUCCESS':
        return 'completed', 'success'
    if state in ('SKIPPED', 'NEUTRAL'):
        return 'completed', state.lower()
    if state in ('FAILURE', 'ERROR', 'TIMED_OUT', 'CANCELLED', 'ACTION_REQUIRED', 'STALE', 'STARTUP_FAILURE'):
        return 'completed', 'failure' if state == 'FAILURE' else state.lower()
    if state in ('PENDING', 'QUEUED', 'IN_PROGRESS', 'WAITING', 'REQUESTED'):
        return 'in_progress', None
    return 'completed', None


def pr_checks_to_runs(raw, head):
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return None
    checks = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            return None
        if 'name' not in item and 'state' not in item and 'bucket' not in item:
            return None
        status, conclusion = pr_check_state(item)
        checks.append({
            'id': index,
            'name': item.get('name') or 'check',
            'head_sha': head,
            'status': status,
            'conclusion': conclusion,
            'html_url': item.get('link'),
            'output': {'title': item.get('description') or ''},
        })
    return checks


def read_pr_checks(repo, number, head):
    code, out, err = gh_result(
        'pr', 'checks', str(number), '--repo', repo,
        '--json', 'name,state,bucket,link,workflow,description')
    if forbidden(out, err):
        return None, 'HTTP 403 gh pr checks'
    if out and out.strip():
        parsed = pr_checks_to_runs(out, head)
        if parsed is not None:
            return parsed, None
    text = (err or b'').decode('utf-8', 'replace').lower()
    if 'no checks reported' in text or (code in (0, 1, 8) and (out or b'').strip() in (b'', b'[]')):
        return [], None
    return None, 'gh pr checks unreadable'


def resolve_ci(repo, number, head):
    prefix = f'repos/{repo}/commits/{head}'
    errors = []
    checks_raw, checks_err = try_api(f'{prefix}/check-runs?per_page=100')
    statuses_raw, statuses_err = try_api(f'{prefix}/statuses?per_page=100')
    if statuses_err is not None:
        errors.append(ci_error('commits/{sha}/statuses', statuses_err))
        statuses_raw = None
    if checks_err is None:
        return checks_raw, statuses_raw or b'[[]]', {
            'check_runs': 'ok', 'fallback': None, 'verified': True, 'errors': errors,
        }
    errors.append(ci_error('commits/{sha}/check-runs', checks_err))
    kind = 'forbidden' if forbidden(checks_err.output, checks_err.stderr) else 'error'
    found = None
    if statuses_from(statuses_raw):
        found = (empty_checks(), statuses_raw, 'status')
    if found is None:
        combined, combined_err = try_api(f'{prefix}/status', paginate=False)
        if combined_err is not None:
            errors.append(ci_error('commits/{sha}/status', combined_err))
        else:
            try:
                payload = json.loads(combined or b'{}')
            except ValueError:
                payload = {}
            items = []
            if isinstance(payload, dict):
                items = [item for item in payload.get('statuses') or [] if isinstance(item, dict) and item.get('context')]
            if items:
                found = (empty_checks(), json.dumps([items]).encode(), 'status')
    if found is None:
        actions, actions_err = try_api(f'repos/{repo}/actions/runs?head_sha={head}&per_page=100')
        if actions_err is not None:
            errors.append(ci_error('actions/runs', actions_err))
        else:
            runs = actions_checks(actions, head)
            if runs:
                found = (encode_keyed(runs, 'check_runs'), statuses_raw, 'actions')
    pr_read = False
    if found is None:
        parsed, pr_err = read_pr_checks(repo, number, head)
        if pr_err:
            errors.append(pr_err)
        else:
            pr_read = True
            if parsed:
                found = (encode_keyed(parsed, 'check_runs'), statuses_raw, 'gh pr checks')
    if found:
        checks, statuses, fallback = found
        verified = True
    else:
        checks, statuses, fallback = empty_checks(), statuses_raw, 'gh pr checks' if pr_read else None
        verified = pr_read
    return checks, statuses or b'[[]]', {
        'check_runs': kind, 'fallback': fallback, 'verified': verified, 'errors': errors,
    }


def pr(repo, number):
    return json.loads(gh('api', f'repos/{repo}/pulls/{number}'))


def revision(data):
    return {'head': data['head']['sha'], 'base': data['base']['sha'],
            'base_ref': data['base']['ref'], 'title': data['title'], 'body': data.get('body')}


def collect(repo, number, directory):
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / 'snapshot.json'
    marker.unlink(missing_ok=True)
    before = pr(repo, number)
    head = before['head']['sha']
    prefix = f'repos/{repo}'
    routes = {
        'reviews.json': f'{prefix}/pulls/{number}/reviews?per_page=100',
        'comments.json': f'{prefix}/issues/{number}/comments?per_page=100',
        'inline.json': f'{prefix}/pulls/{number}/comments?per_page=100',
        'timeline.json': f'{prefix}/issues/{number}/timeline?per_page=100',
        'files.json': f'{prefix}/pulls/{number}/files?per_page=100',
    }
    commands = {name: ('api', route, '--paginate', '--slurp') for name, route in routes.items()}
    owner, name = repo.split('/')
    commands['threads.json'] = ('api', 'graphql', '--paginate', '--slurp', '-f', f'owner={owner}',
                               '-f', f'name={name}', '-F', f'number={number}', '-f', 'query=' + THREADS)
    commands['PR_PATCH.diff'] = ('api', f'{prefix}/pulls/{number}', '-H', 'Accept: application/vnd.github.diff')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        values = dict(zip(commands, pool.map(lambda argv: gh(*argv), commands.values())))
    checks_raw, statuses_raw, tooling = resolve_ci(repo, number, head)
    values['checks.json'] = checks_raw
    values['statuses.json'] = statuses_raw
    for name, content in values.items():
        if name.endswith('.json'):
            value = json.loads(content)
            if not isinstance(value, list) or not value:
                raise ValueError('incomplete response: ' + name)
            if name == 'threads.json':
                for page in value:
                    if page.get('errors') or not ((page.get('data') or {}).get('repository') or {}).get('pullRequest'):
                        raise ValueError('unknown review threads')
    after = pr(repo, number)
    if revision(before) != revision(after):
        raise ValueError('PR changed during snapshot; retry collection')
    file_pages = json.loads(values['files.json'])
    if sum(len(page) for page in file_pages) != after.get('changed_files', sum(len(page) for page in file_pages)):
        raise ValueError('incomplete full PR file list')
    paths = set()
    for page in file_pages:
        for item in page:
            paths.add(item['filename'])
            if item.get('previous_filename'):
                paths.add(item['previous_filename'])
    # Commit a complete batch only. The marker is written last.
    for name, content in values.items():
        (directory / name).write_bytes(content)
    (directory / 'PR_FILES.txt').write_text('\n'.join(sorted(paths)) + '\n')
    (directory / 'pr.json').write_text(json.dumps(after))
    (directory / 'ci-tooling.json').write_text(json.dumps(tooling))
    snapshot = {'repo': repo, 'pr': number, **revision(after)}
    marker.write_text(json.dumps(snapshot))
    return snapshot


def policy_hash():
    root = Path(__file__).resolve().parents[2]
    paths = []
    for name in ('bulma-code-review', 'bulma-host', 'bulma-bus'):
        paths.extend(p for p in (root / name).rglob('*') if p.suffix in ('.md', '.py'))
    return sha(b''.join(str(p.relative_to(root)).encode() + b'\0' + p.read_bytes() for p in sorted(paths)))


def key(directory, context):
    snapshot = json.loads((directory / 'snapshot.json').read_text())
    return {'snapshot': snapshot, 'context': sha(context.read_bytes()), 'policy': policy_hash()}


def seal(directory, context):
    analysis = json.loads((directory / 'analysis.json').read_text())
    if analysis.get('pass') not in ('deep', 'light') or analysis.get('critic') not in ('ran', 'skip'):
        raise ValueError('only completed review and critic analysis can be retained')
    coverage = json.loads((directory / 'coverage.json').read_text())
    if not isinstance(coverage, list):
        raise ValueError('coverage must contain per-file evidence')
    hashes = {name: sha((directory / name).read_bytes()) for name in ARTIFACTS}
    result = {'key': key(directory, context), 'artifacts': hashes}
    (directory / 'analysis-cache.json').write_text(json.dumps(result))
    return {'retained': True}


def valid(directory, context):
    try:
        cache = json.loads((directory / 'analysis-cache.json').read_text())
        return (cache['key'] == key(directory, context)
                and set(cache['artifacts']) == set(ARTIFACTS)
                and all(sha((directory / n).read_bytes()) == h for n, h in cache['artifacts'].items()))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('collect', 'seal', 'check'))
    parser.add_argument('--dir', type=Path, required=True)
    parser.add_argument('--repo')
    parser.add_argument('--pr', type=int)
    parser.add_argument('--context', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'collect':
            if not args.repo or not args.pr:
                raise ValueError('collect requires --repo and --pr')
            result = collect(args.repo, args.pr, args.dir)
        elif args.context is None:
            raise ValueError('seal/check requires freshly built --context')
        elif args.action == 'seal':
            result = seal(args.dir, args.context)
        else:
            ok = valid(args.dir, args.context)
            print(json.dumps({'reusable_analysis': ok, 'approval_authorized': False}))
            return 0 if ok else 1
        if args.action == 'collect':
            result = {name: result[name] for name in ('repo', 'pr', 'head', 'base')}
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
