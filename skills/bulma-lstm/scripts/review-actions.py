#!/usr/bin/env python3
"""Plan LSTM review actions and confirm a single proved dismissal."""
import argparse
import json
import subprocess
from pathlib import Path


def blocked_reason(state):
    if state['pr_state'] != 'OPEN':
        return 'PR is not open'
    if state['code_changed'] is not True:
        return 'no feedback-driven code change'
    if state['proof_pass'] is not True:
        return 'final proof did not pass'
    if not state['head'] or state['proof_sha'] != state['head']:
        return 'final proof does not match the live PR head'
    return None


def plan(state):
    result = {'dismiss': [], 'request': [], 'reason': blocked_reason(state)}
    if result['reason']:
        return result
    reviews = state['reviews']
    if not isinstance(reviews, list):
        raise ValueError('reviews must be a fully paginated, flattened REST list')
    latest = {}
    for review in sorted(reviews, key=lambda r: (r.get('submitted_at') or '', r['id'])):
        login = (review['user'] or {}).get('login')
        if login and review['state'] in ('APPROVED', 'CHANGES_REQUESTED', 'DISMISSED'):
            latest[login] = review
    addressed = {str(i) for i in state['addressed_review_ids']}
    result['dismiss'] = [
        latest[login]['id'] for login in sorted(latest)
        if latest[login]['state'] == 'CHANGES_REQUESTED' and str(latest[login]['id']) in addressed
    ]

    pending = set(state.get('requested_reviewers', []))
    for login in sorted(set(state.get('original_reviewers', []))):
        review = latest.get(login)
        if review and review['state'] == 'APPROVED':
            continue
        if state.get('review_decision') != 'APPROVED' and login not in pending:
            result['request'].append(login)
    result['reason'] = 'planned from final proof and review snapshot'
    return result


def gh_json(*args):
    response = subprocess.run(['gh', *args], capture_output=True, text=True)
    if response.returncode:
        raise ValueError(response.stderr.strip() or f'gh exited with status {response.returncode}')
    return json.loads(response.stdout)


def dismiss(state, repo, pr, review_id, message):
    try:
        reason = blocked_reason(state)
        if reason:
            raise ValueError(reason)
        if review_id not in plan(state)['dismiss']:
            raise ValueError('review was not in the proved dismissal plan')
        if not message.strip():
            raise ValueError('a dismissal reason with proof is required')

        reviews_endpoint = f'repos/{repo}/pulls/{pr}/reviews'
        pages = gh_json('api', reviews_endpoint, '--paginate', '--slurp')
        reviews = [review for page in pages for review in page]
        live_pr = gh_json('pr', 'view', str(pr), '--repo', repo, '--json', 'state,headRefOid')
        live = dict(state, pr_state=live_pr['state'], head=live_pr['headRefOid'], reviews=reviews)
        reason = blocked_reason(live)
        if reason:
            raise ValueError(reason)

        endpoint = f'{reviews_endpoint}/{review_id}'
        if not any(review['id'] == review_id and review['state'] == 'DISMISSED' for review in reviews):
            if review_id not in plan(live)['dismiss']:
                raise ValueError('review is no longer the active change request for its reviewer')
            response = gh_json('api', '-X', 'PUT', f'{endpoint}/dismissals',
                               '-f', 'event=DISMISS', '-f', f'message={message}')
            if response.get('id') != review_id or response.get('state') != 'DISMISSED':
                raise ValueError('PUT did not return the exact review in state DISMISSED')

        confirmed = gh_json('api', endpoint)
        if confirmed.get('id') != review_id or confirmed.get('state') != 'DISMISSED':
            raise ValueError('readback did not confirm the exact review in state DISMISSED')
        return {'id': confirmed['id'], 'state': confirmed['state']}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f'review {review_id}: {exc}') from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path)
    parser.add_argument('--dismiss', type=int, metavar='REVIEW_ID')
    parser.add_argument('--repo')
    parser.add_argument('--pr', type=int)
    parser.add_argument('--message')
    args = parser.parse_args()
    if args.dismiss is not None and not (args.repo and args.pr and args.message):
        parser.error('--dismiss requires --repo, --pr and --message')
    try:
        state = json.loads(args.state.read_text())
        result = (plan(state) if args.dismiss is None
                  else dismiss(state, args.repo, args.pr, args.dismiss, args.message))
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
