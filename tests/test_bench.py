import unittest
from scripts.stress import bench

class StressBench(unittest.TestCase):
    def test_repeatable_interventions(self):
        r=bench()
        self.assertEqual(r,bench())
        self.assertGreater(r["lead_delay"]["after_point"],r["lead_delay"]["before_point"])
        self.assertGreater(r["demand_spike"]["after"]["mae"],r["demand_spike"]["before"]["mae"])
        self.assertEqual(r["return_quarantine"],{"physical":7,"available":0})
        self.assertTrue(r["missing_scan"]["fallback"])
        self.assertTrue(r["short_shelf_life_rejected"])
        self.assertGreater(r["redistribution"]["net_minor"],0)
        self.assertEqual(len(r["policy_comparison"]),2)

