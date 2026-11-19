import unittest
from datetime import date,timedelta
from apps.api.science import forecast,reorder,score

DAY="2026-11-19"
def history(n=63):
    end=date.fromisoformat(DAY)
    return [dict(date=(end-timedelta(days=n-i)).isoformat(),qty=i%7) for i in range(n)]


class DecisionScience(unittest.TestCase):
    def test_missing_close_and_short_series(self):
        for data in [history(10),history()[:-1],history()[:-8]+history()[-7:]]:
            fc=forecast(data,DAY)
            self.assertIsNone(fc["chosen"])
            self.assertIsNone(fc["shortage_probability"])
        d=history();d[-1]["qty"]=0
        self.assertIsNotNone(forecast(d,DAY)["chosen"])

    def test_holdout_changes_never_leak(self):
        data=history();orig=forecast(data,DAY)
        self.assertEqual(orig,forecast(data,DAY))
        self.assertLess(orig["selection_end"],orig["holdout_start"])
        data[-1]["qty"]=600
        after=forecast(data,DAY)
        self.assertEqual(after["chosen"],orig["chosen"])
        self.assertEqual(after["validation_mae"],orig["validation_mae"])
        self.assertEqual([r["prediction"] for r in after["points"]],[r["prediction"] for r in orig["points"]])
        self.assertTrue(all(v>=0 for v in after["future"]))
        self.assertIn("naive",[r["model"] for r in after["scores"]])
        self.assertIsNone(score([(0,0),(0,0)])["wape"])

    def test_threshold_rounding_capacity_and_lead_delay(self):
        fc=dict(chosen="naive",future=[5]*30,points=[dict(actual=6,prediction=5)]*7)
        policy=lambda pos,days,cap:reorder(fc,pos,days,7,.90,10,15,cap)
        self.assertEqual(policy(19,3,200)["quantity"],0)
        self.assertEqual(policy(18,3,200)["quantity"],40)
        self.assertEqual(policy(18,6,200)["point"],36)
        self.assertEqual(policy(18,3,29)["quantity"],0)
        self.assertEqual(policy(18,3,40)["quantity"],20)

