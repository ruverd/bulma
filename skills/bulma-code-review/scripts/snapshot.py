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
FAILED_RUN = {'failure', 'timed_out', 'cancelled', 'startup_failure', 'action_required', 'stale'}
ROLLUP = '''query($owner:String!, $name:String!, $number:Int!) {
 repository(owner:$owner, name:$name) { pullRequest(number:$number) {
 commits(last:1) { nodes { commit { oid statusCheckRollup { state } } } }
 } } }'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gh(*args):
    return subprocess.check_output(['gh', *args])


def denial(exc):
    err = exc.stderr or b''
    text = err.decode('utf-8', 'replace') if isinstance(err, bytes) else str(err)
    blob = f'{exc.returncode} {text}'
    if '403' in blob or 'forbidden' in blob.lower():
        return '403'
    return f'exit {exc.returncode}'


def try_json(*args):
    try:
        return json.loads(gh(*args)), None
    except subprocess.CalledProcessError as exc:
        return None, denial(exc)
    except ValueError:
        return None, 'unreadable'


def graphql_denied(payload):
    messages = []
    for item in payload.get('errors') or []:
        messages.append(item if isinstance(item, str) else str(item.get('message') or item))
    blob = ' '.join(messages)
    return '403' if '403' in blob or 'forbidden' in blob.lower() else 'unreadable'


def collect_actions(repo, head):
    payload, err = try_json(
        'run', 'list', '-R', repo, '--commit', head, '--limit', '100',
        '--json', 'databaseId,name,status,conclusion,workflowName')
    if err or not isinstance(payload, list):
        return {'head': head, 'runs': [], 'error': err or 'unreadable'}
    runs = []
    for run in payload:
        if not isinstance(run, dict) or not isinstance(run.get('databaseId'), int):
            return {'head': head, 'runs': [], 'error': 'unreadable'}
        item = {key: run.get(key) for key in ('databaseId', 'name', 'status', 'conclusion', 'workflowName')}
        rid = str(run['databaseId'])
        viewed, jerr = try_json('run', 'view', rid, '-R', repo, '--json', 'jobs')
        jobs = viewed.get('jobs') if isinstance(viewed, dict) else viewed
        if jerr or not isinstance(jobs, list):
            item['jobs'] = None
            item['jobs_error'] = jerr or 'unreadable'
        else:
            item['jobs'] = jobs
        if str(run.get('conclusion') or '').lower() in FAILED_RUN:
            try:
                log = gh('run', 'view', rid, '-R', repo, '--log-failed')
                item['log_failed_tail'] = '\n'.join(log.decode('utf-8', 'replace').splitlines()[-200:])
            except subprocess.CalledProcessError as exc:
                item['log_failed_error'] = denial(exc)
        runs.append(item)
    return {'head': head, 'runs': runs, 'error': None}


def collect_rollup(repo, number, head):
    owner, name = repo.split('/')
    payload, err = try_json(
        'api', 'graphql', '-f', f'owner={owner}', '-f', f'name={name}',
        '-F', f'number={number}', '-f', 'query=' + ROLLUP)
    if err or not isinstance(payload, dict):
        return {'head': head, 'state': None, 'error': err or 'unreadable'}
    if payload.get('errors'):
        return {'head': head, 'state': None, 'error': graphql_denied(payload)}
    try:
        commit = payload['data']['repository']['pullRequest']['commits']['nodes'][0]['commit']
    except (KeyError, IndexError, TypeError):
        return {'head': head, 'state': None, 'error': 'unreadable'}
    if commit.get('oid') != head:
        return {'head': head, 'state': None, 'error': 'head mismatch'}
    rollup = commit.get('statusCheckRollup') or {}
    return {'head': head, 'state': rollup.get('state'), 'error': None}


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
    statuses, _ = try_json('api', f'{prefix}/commits/{head}/statuses?per_page=100', '--paginate', '--slurp')
    # A token without commit-status read must not abort the snapshot; Actions and rollup carry CI.
    values['statuses.json'] = json.dumps(statuses if isinstance(statuses, list) and statuses else [[]]).encode()
    actions = collect_actions(repo, head)
    rollup = collect_rollup(repo, number, head)
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
    (directory / 'actions.json').write_text(json.dumps(actions))
    (directory / 'rollup.json').write_text(json.dumps(rollup))
    (directory / 'PR_FILES.txt').write_text('\n'.join(sorted(paths)) + '\n')
    (directory / 'pr.json').write_text(json.dumps(after))
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
