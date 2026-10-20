import importlib.util
from pathlib import Path
import sys
import unittest

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


if __name__ == '__main__':
    unittest.main()
