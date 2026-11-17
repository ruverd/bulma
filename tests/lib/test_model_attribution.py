import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import json

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skills/bulma-host/scripts'))
import model_identity as m


class AttributionTest(unittest.TestCase):
    def records(self, model, source='runtime', **kw):
        return [{'role': 'Implementation', 'identity': dict(model=model, source=source, effort='high', **kw)}]

    def test_unknown_and_ambiguous_omit_entire_section_and_row(self):
        for value in (None, '', 'unknown', 'undefined', 'null', 'default', 'auto', 'session_model'):
            self.assertEqual(m.pr_section(self.records(value)), '')
            self.assertEqual(m.review_row(self.records(value)), '')
        self.assertEqual(m.pr_section(self.records('family-alias', ambiguous=True)), '')
        for source in ('requested', 'config', 'model_prose', None):
            self.assertEqual(m.review_row(self.records('fixture-v1', source)), '')

    def test_mixed_contributors_keep_only_known_no_effort(self):
        records = self.records('fixture-v1') + [
            {'role': 'Code review', 'identity': {}},
            {'role': 'Plan critic', 'identity': {'model': 'critic-v2', 'source': 'system'}}]
        for render in (m.pr_section, m.review_row):
            body = render(records)
            self.assertIn('Implementation', body)
            self.assertIn('fixture-v1', body)
            self.assertIn('critic-v2', body)
            self.assertNotIn('Code review', body)
            self.assertNotIn('effort', body.lower())
            self.assertNotIn('high', body)
            self.assertNotIn('unknown', body)

    def test_escaping_and_cli(self):
        records = self.records('fixture|v1\n<script>')
        self.assertNotIn('<script>', m.review_row(records))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'records.json'
            path.write_text(json.dumps(records))
            body = subprocess.check_output([sys.executable, str(ROOT / 'skills/bulma-host/scripts/model_identity.py'),
                                            '--kind', 'pr', '--records', str(path)], text=True)
            self.assertEqual(body.strip(), m.pr_section(records))

    def test_public_templates_do_not_require_effort_or_unknown(self):
        for name in ('skills/bulma-feature-delivery/templates/PR_BODY.md',
                     'skills/bulma-code-review/nodes/publish.md',
                     'skills/bulma-code-review/references/CHAT.md',
                     'skills/bulma-developer/nodes/fix.md',
                     'skills/bulma-lstm/nodes/patch.md'):
            text = (ROOT / name).read_text()
            self.assertNotIn('| Reasoning effort |', text)
            self.assertNotIn('- Reasoning effort:', text)
            self.assertNotIn('- Code review reasoning effort:', text)
            self.assertNotIn('actual model/effort pairs', text)
        self.assertIn('reviewer_effort', (ROOT / 'skills/bulma-code-review/templates/STATE.md').read_text())


if __name__ == '__main__':
    unittest.main()
