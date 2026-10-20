import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('groups', Path(__file__).resolve().parents[2] / 'skills/bulma-lstm/scripts/group-fixes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(i, **kwargs):
    return dict({'id': i, 'disposition': 'fix', 'claim_true': 'yes', 'fix_ok_here': 'yes',
                 'paths': ['src/a'], 'risk': 'normal', 'acceptance': 'claim gone',
                 'evidence': 'test:42', 'cause_id': 'contract', 'cause_evidence': 'provider:12'}, **kwargs)


class GroupTest(unittest.TestCase):
    def test_same_cause_preserves_all_comments_and_highest_risk(self):
        rows = [row(1), row(2, risk='elevated'), row(3, disposition='skip')]
        result = m.plan(rows)
        self.assertEqual(len(result['groups']), 1)
        self.assertEqual(result['fix_comments'], 2)
        self.assertEqual(result['groups'][0]['risk'], 'elevated')
        self.assertEqual(result['groups'][0]['comments'], rows[:2])

    def test_same_file_not_enough(self):
        result = m.plan([row(1, cause_evidence=''), row(2), row(3, cause_id='other')])
        self.assertEqual(len(result['groups']), 3)

    def test_bounded_groups_and_unclear(self):
        result = m.plan([row(i) for i in range(10)] + [row(11, disposition='unclear')])
        self.assertEqual([len(g['comments']) for g in result['groups']], [8, 2])
        self.assertEqual(result['unresolved'], ['11'])

    def test_duplicate_and_unverified_rejected(self):
        for rows in ([row(1), row(1)], [row(1, claim_true='unknown')], [row(1, acceptance='')]):
            with self.assertRaises(ValueError):
                m.plan(rows)


if __name__ == '__main__':
    unittest.main()
