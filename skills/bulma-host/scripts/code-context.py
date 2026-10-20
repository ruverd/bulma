#!/usr/bin/env python3
"""Query an existing fresh Trail Code map without initializing or rebuilding it."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def trail_context(repo, query, limit=6):
    repo = Path(repo).resolve()
    if not ((repo / 'graft').is_dir() or (repo / '.trail/cache').is_dir()):
        return {'status': 'fallback', 'reason': 'no existing Trail Code map'}
    executable = shutil.which('trail')
    if not executable:
        return {'status': 'fallback', 'reason': 'Trail Code unavailable'}
    try:
        check = subprocess.run([executable, 'build', '--check', '--json', str(repo)],
                               capture_output=True, text=True, timeout=30)
        if check.returncode:
            return {'status': 'fallback', 'reason': 'map stale or incompatible Trail executable'}
        response = subprocess.run([executable, 'ask', query, str(repo), '--source', '--json',
                                   '--no-refresh', '--limit', str(limit)],
                                  capture_output=True, text=True, timeout=30)
        if response.returncode:
            return {'status': 'fallback', 'reason': 'Trail query failed'}
        data = json.loads(response.stdout)
        return {'status': 'ok', 'provider': 'trail-code', 'context': data}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {'status': 'fallback', 'reason': 'Trail query unavailable'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--query', required=True)
    parser.add_argument('--limit', type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.limit <= 15:
        parser.error('limit must be between 1 and 15')
    result = trail_context(args.repo, args.query, args.limit)
    print(json.dumps(result))
    return 0 if result['status'] == 'ok' else 3


if __name__ == '__main__':
    raise SystemExit(main())
