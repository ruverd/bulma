import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
LIB = Path(__file__).resolve().parent
SCRIPT = LIB / 'check_routing.py'

SKILLS = {
    'alpha-review': 'Review a pull request and post a verdict. Use when reviewing PRs.',
    'beta-debug': 'Debug a crash or a failing job. Use when something is broken.',
    'gamma-docs': 'Write a README or a tutorial. Use when writing documentation.',
}


class RoutingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name, description in SKILLS.items():
            self.skill(name, description)
        (self.root / 'evals' / 'routing').mkdir(parents=True)

    def skill(self, name, description):
        path = self.root / 'skills' / name / 'SKILL.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'---\nname: {name}\ncategory: lib\ndescription: {description}\n---\n')

    def case(self, skill, positive, negative):
        data = {'skill': skill, 'positive': [{'prompt': p} for p in positive],
                'negative': [dict(prompt=p, **({'owner': o} if o else {})) for p, o in negative]}
        (self.root / 'evals' / 'routing' / f'{skill}.json').write_text(json.dumps(data))

    def run_check(self):
        env = dict(os.environ, PYTHONPATH=str(LIB))
        return subprocess.run([sys.executable, str(SCRIPT), str(self.root)],
                              capture_output=True, text=True, env=env)

    def test_good_cases_pass(self):
        self.case('alpha-review', ['review my pull request'], [('the job is broken', 'beta-debug')])
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_vocabulary_fails(self):
        self.case('gamma-docs', ['add a changelog entry'], [('review my PR', 'alpha-review')])
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('gamma-docs ranks #None', result.stdout)

    def test_overbroad_skill_fails_negative(self):
        self.case('alpha-review', ['review my pull request'], [('review the README', 'gamma-docs')])
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('must not take', result.stdout)

    def test_near_duplicate_descriptions_fail(self):
        self.skill('delta-review', SKILLS['alpha-review'])
        self.case('alpha-review', ['review my pull request'], [('the job is broken', None)])
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('descriptions collide: alpha-review ~ delta-review', result.stdout)

    def test_case_name_must_match_skill(self):
        (self.root / 'evals' / 'routing' / 'alpha-review.json').write_text(
            json.dumps({'skill': 'beta-debug', 'positive': [], 'negative': []}))
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('does not match the file name', result.stdout)


if __name__ == '__main__':
    unittest.main()
