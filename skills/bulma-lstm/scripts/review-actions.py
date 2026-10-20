#!/usr/bin/env python3
"""Plan dismissals and re-review requests from fresh, proved LSTM state."""
import argparse
import json
from pathlib import Path


def plan(state):
    result = {'dismiss': [], 'request': [], 'reason': 'no proved code change'}
    if (state.get('code_changed') is not True or state.get('proof_pass') is not True
            or not state.get('head') or state.get('proof_sha') != state['head']
            or state.get('pr_state') != 'OPEN'):
        return result
    reviews = state['reviews']
    if not isinstance(reviews, list):
        raise ValueError('reviews must be a fully paginated, flattened list')
    latest = {}
    for review in sorted(reviews, key=lambda r: (r.get('submitted_at') or '', r['id'])):
        if review['state'] in ('APPROVED', 'CHANGES_REQUESTED', 'DISMISSED'):
            latest[review['user']['login']] = review
    addressed = {str(i) for i in state.get('addressed_review_ids', [])}
    in_scope = set(state.get('original_reviewers', []))
    pending = set(state.get('requested_reviewers', []))
    for login in sorted(in_scope):
        review = latest.get(login)
        status = review['state'] if review else 'COMMENTED'
        if status == 'APPROVED':
            continue
        if status == 'CHANGES_REQUESTED' and str(review['id']) in addressed:
            result['dismiss'].append(review['id'])
        if state.get('review_decision') != 'APPROVED' and login not in pending:
            result['request'].append(login)
    result['reason'] = 'refresh live state before each mutation; dismissal is not approval'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(plan(json.loads(args.state.read_text())), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
