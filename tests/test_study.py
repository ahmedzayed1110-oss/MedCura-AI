"""Real SQL transactions and synthetic in-memory study fixtures only."""
import csv
import io
import sqlite3
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from apps.api import study


class Economics(unittest.TestCase):
    def test_funnel_and_timing(self):
        p = study.PRESETS["Base"]
        a,b,c = study.calculate(p)
        self.assertEqual((a["reachable"],a["qualified"],a["pilots"],a["new_contracts"]),(12,6,3,1))
        self.assertEqual((a["paying_branches"],a["mrr"],a["arr"],a["revenue"]),(2,1200,14400,8700))
        self.assertEqual(a["cogs"],4200)
        self.assertEqual(a["operating_result"],4500-3000-108000)
        self.assertEqual(c["arr"],c["paying_branches"]*600*12)
        self.assertEqual(b["break_even_branches"],26)

    def test_zero_conversions_and_negative_contribution(self):
        p = dict(study.PRESETS["Base"], conversion_pct=0, price=10)
        for row in study.calculate(p):
            self.assertEqual(row["arr"],0)
            self.assertIsNone(row["gross_margin_pct"])
            self.assertIsNone(row["break_even_branches"])

    def test_invalid_inputs(self):
        for key,val in [("reach_2029",1.5),("price","NaN"),("churn_pct",110),("hosting",True),("price","Infinity")]:
            with self.subTest(key=key,val=val), self.assertRaises(ValueError):
                study.calculate(dict(study.PRESETS["Base"],**{key:val}))

    def test_churn_precedes_new_billable_branches(self):
        a,b,_=study.calculate(dict(study.PRESETS["Favorable"],churn_pct=100))
        self.assertEqual(b["churned"],a["contracts"])
        self.assertEqual(b["contracts"],b["new_contracts"])
        self.assertEqual(b["branch_months"],b["paying_branches"]*6)

    def test_tenant_visibility_and_write_permissions(self):
        db=sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        study.init(db)
        body={"name":"Local base","assumptions":study.PRESETS["Base"]}
        with self.assertRaises(PermissionError):
            study.route(db,"POST","/api/scenarios",body,"training","Pat","viewer")
        saved=study.route(db,"POST","/api/scenarios",body,"training","Pat","owner")
        self.assertEqual(study.scenario_state(db,"training")["saved"][0]["id"],saved["id"])
        self.assertEqual(study.scenario_state(db,"sandbox")["saved"],[])
        with self.assertRaises(ValueError):
            study.route(db,"POST","/api/scenarios",dict(body,tenant="sandbox"),"training","Pat","owner")


class Pilot(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        study.init(self.db)
        self.tenant="field"
        self.p=dict(study.PROTOCOL,branch="RUH",skus=["MASK"],baseline_start="2024-01-01",baseline_end="2024-01-07",
                    intervention="2024-01-08",post_start="2024-01-09",post_end="2024-01-15",minimum_days=7,
                    integration_reviewed=True,security_reviewed=True)
        self.observations=[]
        for offset in [*range(7),*range(8,15)]:
            obs=dict.fromkeys(study.FIELDS,"")
            obs.update(branch="RUH",sku="MASK",date=(date(2024,1,1)+timedelta(days=offset)).isoformat(),issued=5,received=3,
                       on_hand=10,stockout_hours=1 if offset<7 else 0,stockout_starts=1 if offset<7 else 0,
                       scan_eligible=10,scanned=9,expired_qty=2,unit_cost_sar=3,tracked_value_added_sar=100)
            self.observations.append(obs)

    def call(self,path,body,role="owner",method="POST"):
        return study.route(self.db,method,"/api/pilot/"+path,body,self.tenant,"local-custodian",role)

    def enroll(self):
        study.enroll(self.db,self.tenant,"BOARD-001")
        with patch.object(study,"local_today",return_value=date(2023,12,1)):
            self.call("protocol",self.p)

    def payload(self,rows=None,mode="import"):
        stream=io.StringIO(newline="")
        w=csv.DictWriter(stream,fieldnames=study.FIELDS)
        w.writeheader()
        w.writerows(self.observations if rows is None else rows)
        return dict(filename="anonymous.csv",csv=stream.getvalue(),attest_actual=True,reference="CUST-001",mode=mode)

    def test_empty_status_is_not_measured(self):
        r=self.call("report",{},method="GET")
        self.assertEqual(r["decision"],"Not measured")
        self.assertIsNone(r["baseline"]["metrics"]["expired_units"])
        self.assertEqual(r["evidence_level"],"UNKNOWN")

    def test_demo_is_never_field_eligible(self):
        for self.tenant in ("training","sandbox"):
            with self.subTest(tenant=self.tenant):
                with self.assertRaises(ValueError):
                    study.enroll(self.db,self.tenant,"BOARD-001")
                self.call("protocol",self.p)
                self.assertEqual(self.call("measurements",self.payload(mode="validate"))["rows"],14)
                with self.assertRaises(PermissionError):
                    self.call("measurements",self.payload())
                self.assertEqual(self.call("report",{},method="GET")["imports"],[])

    def test_preregistered_disjoint_windows(self):
        with self.assertRaises(ValueError):
            self.call("protocol",self.p)
        with self.assertRaises(ValueError):
            study.validate_protocol(dict(self.p,post_start="2024-01-07"))
        with self.assertRaises(ValueError):
            study.validate_protocol(dict(self.p,skus=["MASK","MASK"]))
        with self.assertRaises(ValueError):
            study.validate_protocol(dict(self.p,minimum_days=14))

    def test_authority_and_attestation_required(self):
        with self.assertRaises(PermissionError):
            self.call("measurements",self.payload())
        self.enroll()
        for role in ("manager","auditor","viewer"):
            with self.subTest(role=role), self.assertRaises(PermissionError):
                self.call("measurements",self.payload(),role)
        with self.assertRaises(ValueError):
            self.call("measurements",dict(self.payload(),attest_actual=False))
        with self.assertRaises(ValueError):
            self.call("measurements",dict(self.payload(),reference=""))

    def test_denominators_gate_and_import_audit(self):
        self.enroll()
        accepted=self.call("measurements",self.payload())
        r=self.call("report",{},method="GET")
        self.assertEqual(r["imports"][0]["sha256"],accepted["sha256"])
        self.assertEqual(r["decision"],"Eligible for human go review")
        self.assertEqual(r["stockout_incidence_improvement_pct"],100)
        pre=r["baseline"]["metrics"]
        self.assertEqual(pre["stockout_starts_per_1000_sku_days"],1000)
        self.assertEqual(pre["expiry_pct_of_tracked_value"],6)
        self.assertEqual(pre["expiry_writeoff_sar"],42)
        self.assertIsNone(pre["correction_pct"])
        self.assertEqual(study.report(self.db,"other")["evidence_level"],"UNKNOWN")
        with self.assertRaises(ValueError):
            self.call("protocol",self.p)

    def test_missing_scope_and_comparison_are_withheld(self):
        self.enroll()
        self.call("measurements",self.payload(self.observations[:4]))
        r=self.call("report",{},method="GET")
        self.assertFalse(r["baseline"]["sufficient"])
        self.assertIsNone(r["stockout_incidence_improvement_pct"])
        self.assertIsNone(r["baseline"]["metrics"]["barcode_adoption_pct"])

    def test_duplicate_import_and_overlap_are_atomic(self):
        self.enroll()
        self.call("measurements",self.payload(self.observations[:1]))
        for rows in [self.observations[:1],self.observations[:2],[self.observations[1]]*2]:
            with self.assertRaises(ValueError):
                self.call("measurements",self.payload(rows))
        self.assertEqual(self.db.execute("SELECT count(*) FROM study_days").fetchone()[0],1)
        self.assertEqual(self.db.execute("SELECT count(*) FROM study_imports").fetchone()[0],1)

    def test_incorrect_header_dates_counts_type_and_limits(self):
        self.enroll()
        good=self.payload()
        for bad in [dict(good,csv=good["csv"].replace("branch,","patient_name,",1)),dict(good,filename="file.xls"),
                    dict(good,csv="x"*180001),dict(good,csv=good["csv"]+"\x00"),dict(good,evidence_level="PILOT_MEASURED"),
                    self.payload([dict(self.observations[0],scanned=12)]), self.payload([dict(self.observations[0],stockout_hours=30)]),
                    self.payload([dict(self.observations[0],date="2024-01-08")]), self.payload([dict(self.observations[0],issued="-1")]),
                    self.payload([dict(self.observations[0],lot="=HYPERLINK()")]), self.payload([dict(self.observations[0],date="2100-01-01")])]:
            with self.assertRaises(ValueError):
                self.call("measurements",bad)

    def test_confounding_flags_force_review(self):
        self.p["confounders"]=["Supplier delay"]
        self.enroll()
        self.call("measurements",self.payload())
        self.assertTrue(study.report(self.db,self.tenant)["decision"].startswith("Pivot"))

    def test_followup_review_keeps_original_design(self):
        self.enroll()
        self.call("measurements",self.payload())
        body={"security_reviewed":True,"integration_reviewed":True,"confounders":["Staffing change"]}
        with self.assertRaises(PermissionError):
            self.call("review",body,"manager")
        report=self.call("review",body)
        self.assertTrue(report["decision"].startswith("Pivot"))
        self.assertEqual(report["protocol"]["confounders"],[])
        self.assertEqual(report["reviews"][0]["actor"],"local-custodian")
        self.assertTrue(self.call("review",dict(body,security_reviewed=False))["decision"].startswith("No-go"))
