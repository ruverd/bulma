import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from check_graphs import parse_edges, reachable
spec = importlib.util.spec_from_file_location('shape', ROOT / 'skills/bulma-feature-delivery/scripts/plan-shape.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FlowTest(unittest.TestCase):
    def test_depth(self):
        self.assertEqual(m.choose('normal', 2, 1)['plan_mode'], 'compact')
        self.assertEqual(m.choose('normal', 2, 1)['quality_mode'], 'focused')
        for args in ({'risk': 'elevated'}, {'cross_contract': True}, {'uncertain': True}, {'units': 2}):
            values = dict(risk='normal', files=2, units=1)
            values.update(args)
            self.assertEqual(m.choose(**values)['plan_mode'], 'detailed')
        self.assertEqual(m.choose('normal', 2, 1, structural=True)['quality_mode'], 'deep')

    def test_quality_cannot_ship_without_review_test_and_evidence(self):
        graph = (ROOT / 'skills/bulma-feature-delivery/GRAPH.md').read_text()
        edges = parse_edges(graph)
        for gate in ('review', 'tester', 'evidence'):
            self.assertFalse(reachable(edges, 'quality', 'shipper', avoid=(gate,)), gate)
        self.assertTrue(reachable(edges, 'quality', 'shipper'))
        self.assertIn('implement', edges['ci_watch'])
        self.assertNotIn('shipper', edges['quality'])


if __name__ == '__main__':
    unittest.main()
