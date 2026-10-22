#!/usr/bin/env python3
"""Compare captured output without rerunning a baseline on the changed tree."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

BUS = Path(__file__).resolve().parents[2] / 'bulma-bus/scripts/runtime.py'
SPEC = importlib.util.spec_from_file_location('runtime', BUS)
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


def receipt(path):
    record = json.loads(Path(path).read_text())
    identity = record['identity']
    if (record.get('version') != 1 or record.get('exit_code') != 0
            or record.get('stable') is not True or identity.get('reusable') is not True
            or record.get('fingerprint') != runtime.digest(identity)):
        raise ValueError('comparison needs successful, stable receipts with a known environment')
    output = Path(record['log']).read_bytes()
    if not output or record.get('log_sha256') != hashlib.sha256(output).hexdigest():
        raise ValueError('receipt output is empty or its integrity check failed; recapture it')
    return record, output


def compare(repo, baseline, candidate, environment):
    if not environment or Path(baseline).resolve() == Path(candidate).resolve():
        raise ValueError('comparison needs a known environment and two separate captures')
    before, old = receipt(baseline)
    after, new = receipt(candidate)
    if before['fingerprint'] == after['fingerprint']:
        raise ValueError('baseline and candidate describe the same source snapshot')
    for key in ('repo', 'command', 'environment', 'submodules'):
        if before['identity'][key] != after['identity'][key]:
            raise ValueError(f'comparison {key} differs')
    if before['recorded_at'] >= after['recorded_at']:
        raise ValueError('baseline must have been captured before the candidate')
    current = runtime.identity(repo, after['identity']['command'], environment)
    if not runtime.reusable(after, current):
        raise ValueError('candidate evidence is stale for the current tree or environment')
    return {'version': 1, 'equivalent': old == new,
            'baseline': str(Path(baseline).resolve()), 'candidate': str(Path(candidate).resolve()),
            'environment': environment, 'candidate_fingerprint': after['fingerprint'],
            'baseline_fingerprint': before['fingerprint'],
            'scope': 'Exact combined command output on the recorded probe and fixtures only'}


def check_report(path, repo, environment):
    report = json.loads(Path(path).read_text())
    if not environment or report['environment'] != environment:
        raise ValueError('comparison needs the fresh current environment fingerprint')
    result = compare(repo, report['baseline'], report['candidate'], environment)
    if report != result or result['equivalent'] is not True:
        raise ValueError('equivalence report failed or no longer matches the current evidence')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--environment', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        out = runtime.outside_repo(args.out, args.repo)
        if out.exists():
            raise ValueError('comparison output already exists; keep the previous report and choose a new path')
        if out in (Path(args.baseline).resolve(), Path(args.candidate).resolve()):
            raise ValueError('comparison must not overwrite its inputs')
        result = compare(args.repo, args.baseline, args.candidate, args.environment)
        runtime.write_json(out, result)
        print(json.dumps({'report': str(out), **result}))
        return 0 if result['equivalent'] else 1
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
