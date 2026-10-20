#!/usr/bin/env python3
"""Group verified comments by an explicit, evidenced root cause."""
import argparse
import hashlib
import json
from pathlib import Path

RISK = {'low': 0, 'normal': 1, 'elevated': 2}


def plan(rows):
    if not isinstance(rows, list):
        raise ValueError('dispositions must be a list')
    seen = set()
    groups = []
    for row in rows:
        ident = str(row['id'])
        if ident in seen:
            raise ValueError('duplicate comment id: ' + ident)
        seen.add(ident)
        if row['disposition'] not in ('fix', 'skip', 'unclear'):
            raise ValueError('unknown disposition')
        if row['disposition'] != 'fix':
            continue
        if row.get('claim_true') != 'yes' or row.get('fix_ok_here') not in ('yes', 'na'):
            raise ValueError('unverified fix: ' + ident)
        paths = row.get('paths')
        if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p for p in paths):
            raise ValueError('fix needs bound paths: ' + ident)
        if not row.get('acceptance') or not row.get('evidence') or row.get('risk') not in RISK:
            raise ValueError('fix needs acceptance, evidence and risk: ' + ident)
        cause = row.get('cause_id') if row.get('cause_evidence') else None
        group = next((g for g in groups if cause and g['cause_id'] == cause
                      and len(g['comments']) < 8 and len(set(g['paths']) | set(paths)) <= 6), None)
        if group is None:
            group = {'cause_id': cause, 'comments': [], 'paths': [], 'risk': 'low'}
            groups.append(group)
        group['comments'].append(row)
        group['paths'] = sorted(set(group['paths']) | set(paths))
        group['risk'] = max((group['risk'], row['risk']), key=RISK.get)
    for group in groups:
        ids = sorted(str(row['id']) for row in group['comments'])
        group['id'] = 'fix-' + hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:12]
    return {'groups': groups, 'fix_comments': sum(len(g['comments']) for g in groups),
            'unresolved': [str(r['id']) for r in rows if r['disposition'] == 'unclear']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dispositions', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(plan(json.loads(args.dispositions.read_text())), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
