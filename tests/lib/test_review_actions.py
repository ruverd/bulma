import importlib.util
import json
import subprocess
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('actions', Path(__file__).resolve().parents[2] / 'skills/bulma-lstm/scripts/review-actions.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def review(ident, state, login='alice'):
    return {'id': ident, 'state': state, 'user': {'login': login}, 'submitted_at': str(ident)}


class ActionsTest(unittest.TestCase):
    def state(self, **changes):
        return dict({'pr_state': 'OPEN', 'head': 'abc', 'proof_sha': 'abc', 'proof_pass': True,
                     'code_changed': True, 'review_decision': 'CHANGES_REQUESTED',
                     'original_reviewers': ['alice'], 'requested_reviewers': [],
                     'addressed_review_ids': [1], 'reviews': [review(1, 'CHANGES_REQUESTED')]}, **changes)

    def test_proved_fix_dismisses_and_requests(self):
        result = m.plan(self.state())
        self.assertEqual(result['dismiss'], [1])
        self.assertEqual(result['request'], ['alice'])

    def test_no_change_no_proof_or_stale_head(self):
        for change in ({'code_changed': False}, {'proof_pass': False}, {'proof_sha': 'old'}, {'pr_state': 'CLOSED'}):
            result = m.plan(self.state(**change))
            self.assertEqual(result['dismiss'], [])
            self.assertEqual(result['request'], [])

    def test_approved_reviewer_not_notified_or_dismissed(self):
        result = m.plan(self.state(reviews=[review(1, 'APPROVED'), review(2, 'COMMENTED')]))
        self.assertEqual(result['dismiss'], [])
        self.assertEqual(result['request'], [])
        self.assertEqual(m.plan(self.state(review_decision='APPROVED'))['request'], [])

    def test_unaddressed_block_kept_and_pending_request_not_repeated(self):
        result = m.plan(self.state(addressed_review_ids=[], requested_reviewers=['alice']))
        self.assertEqual(result['dismiss'], [])
        self.assertEqual(result['request'], [])

    def test_after_dismissal_request_still_possible(self):
        result = m.plan(self.state(reviews=[review(1, 'DISMISSED')]))
        self.assertEqual(result['dismiss'], [])
        self.assertEqual(result['request'], ['alice'])

    def test_dismissal_uses_exact_proved_id_independent_of_rerequest_scope(self):
        reviews = [review(1, 'CHANGES_REQUESTED'), review(2, 'COMMENTED'),
                   review(3, 'CHANGES_REQUESTED', 'bob')]
        result = m.plan(self.state(reviews=reviews, original_reviewers=['bob']))
        self.assertEqual(result['dismiss'], [1])
        self.assertEqual(result['request'], ['bob'])

    def test_superseded_review_is_not_dismissed(self):
        for state in ('APPROVED', 'CHANGES_REQUESTED', 'DISMISSED'):
            with self.subTest(state=state):
                result = m.plan(self.state(reviews=[review(1, 'CHANGES_REQUESTED'), review(2, state)]))
                self.assertEqual(result['dismiss'], [])

    def dismiss(self, state=None, *, live_head='abc', live_reviews=None, put=None, readback=None):
        snapshot = self.state() if state is None else state
        live_pr = {'state': 'OPEN', 'headRefOid': live_head}
        pages = [[], snapshot['reviews'] if live_reviews is None else live_reviews]
        dismissed = {'id': 1, 'state': 'DISMISSED'}
        if put is None:
            put = dismissed
        with patch.object(m.subprocess, 'run') as run:
            def gh(command, **kwargs):
                if command[1:3] == ['pr', 'view']:
                    data = live_pr
                elif '--slurp' in command:
                    data = pages
                elif '-X' in command:
                    self.assertEqual(command[2:5], ['-X', 'PUT', 'repos/acme/app/pulls/7/reviews/1/dismissals'])
                    self.assertIn('event=DISMISS', command)
                    self.assertIn('message=proof abc', command)
                    if isinstance(put, str):
                        return subprocess.CompletedProcess(command, 1, '', put)
                    data = put
                else:
                    self.assertEqual(command[2], 'repos/acme/app/pulls/7/reviews/1')
                    data = dismissed if readback is None else readback
                return subprocess.CompletedProcess(command, 0, json.dumps(data), '')

            run.side_effect = gh
            try:
                return m.dismiss(snapshot, 'acme/app', 7, 1, 'proof abc')
            finally:
                self.calls = [call.args[0] for call in run.call_args_list]

    def test_dismiss_confirms_exact_state_with_readback(self):
        result = self.dismiss()
        self.assertEqual(result, {'id': 1, 'state': 'DISMISSED'})
        self.assertEqual(self.calls[-1][2], 'repos/acme/app/pulls/7/reviews/1')

    def test_dismiss_never_mutates_with_stale_proof_skip_only_or_new_review(self):
        for kwargs in ({'live_head': 'new'}, {'state': self.state(code_changed=False)},
                       {'live_reviews': [review(1, 'CHANGES_REQUESTED'), review(2, 'CHANGES_REQUESTED')]}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    self.dismiss(**kwargs)
                self.assertFalse(any('PUT' in cmd for cmd in self.calls))

    def test_already_dismissed_is_reconciled_without_put(self):
        result = self.dismiss(live_reviews=[review(1, 'DISMISSED')])
        self.assertEqual(result, {'id': 1, 'state': 'DISMISSED'})
        self.assertFalse(any('PUT' in cmd for cmd in self.calls))

    def test_success_response_with_unconfirmed_readback_is_pending(self):
        with self.assertRaisesRegex(ValueError, 'review 1: readback did not confirm'):
            self.dismiss(readback={'id': 1, 'state': 'CHANGES_REQUESTED'})

    def test_denial_and_unconfirmed_success_surface_as_failures(self):
        for response in ('HTTP 403: Review dismissal is restricted',
                         {'id': 1, 'state': 'CHANGES_REQUESTED'},
                         {'id': 2, 'state': 'DISMISSED'}):
            with self.subTest(response=response), self.assertRaisesRegex(ValueError, 'review 1.*(403|DISMISSED)'):
                self.dismiss(put=response)


if __name__ == '__main__':
    unittest.main()
