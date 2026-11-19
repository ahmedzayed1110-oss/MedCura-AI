# Prospective Riyadh inventory pilot

**Current outcome — Not measured.** The supplied files contain regional market records and strategy material. This protocol concerns one participating branch and a prespecified set of non-pharmaceutical consumables. The custodian must grant access to operational records before collection.

## Register the comparison

The example starts with gloves, masks and dressings at a single Riyadh branch. Replace the coded branch and SKU identifiers with approved local codes. Define equivalent base units and fixed count-session scope with the storekeeper. Enroll SKUs expected to remain eligible throughout both windows. Record planned opening hours, staffing, suppliers, delivery schedules, stockout episode rules and barcode exclusions.

1. In the Pilot workspace, register baseline and post windows, the intervention date and eligible SKUs. The prospective example uses 4–31 January 2027, introduces scanning on 1 February and measures 8 February–7 March. The six-day gap after the intervention date allows staff practice. Each 28-day window has 84 eligible SKU-days for three SKUs. All dates use Asia/Riyadh.
2. During baseline, retain the existing stock process. Record daily issues, receipts, final on-hand, episode starts and durations, counting effort, scan opportunities and corrections. Archive forecast estimates as issued, before observing their outcomes. A closed or incompletely observed day stays missing.
3. Introduce barcode capture, FEFO suggestions and approval-based alerts. Record training and changes to purchasing cadence. Continue the same measurements during post observation.
4. Reconcile quantities to stock movement records, align the source field definitions and record a coded extraction reference. A qualified custodian attests to the observations. The accountable branch lead reviews any expansion decision.

## Data collection and import

The canonical observation has one branch, one SKU and one local calendar date. Aggregate all eligible lots once. Use the coded lot field only where one lot represents the entire observation, otherwise leave it blank. Preserve lot detail in the authorized local source. Use weighted disposal cost for mixed-cost lots.

The comma-separated and Excel templates in `data/templates` have identical field names. Excel users enter rows on the Observations sheet, then save that sheet as UTF-8 CSV. The API accepts only CSV text with the exact ordered header, at most 180,000 UTF-8 bytes and 1,200 rows per file. Larger collections can use disjoint batches. Each accepted SKU-day is unique throughout the tenant's pilot. A duplicate or invalid row rejects the whole batch. Blanks remain unknown and legitimate recorded zeroes remain zeroes.

| Fields | Recording rule |
|---|---|
| branch, sku, lot, date | Use registered codes, optional lot code and YYYY-MM-DD. Do not enter staff or patient identifiers. |
| issued, received, on_hand | Whole base units. Final on-hand is a daily snapshot. |
| stockout_hours, stockout_starts | Capture observed outage hours (0–24) and new episodes during the day. An episode crossing midnight has one start. |
| expired_qty, unit_cost_sar, tracked_value_added_sar | Write-off units, weighted cost per expired unit and new inventory value entering the tracked scope. Include opening value on the first day of each window once. |
| counting_hours, count_sessions | Allocate staff time to a standardized SKU-level counting session. Preserve a fixed scope. |
| scan_eligible, scanned, entries, corrected | Whole event counts. Supply each numerator and denominator together. |
| count_lines, discrepant_lines, alerts, actions_followed | Whole event counts under a common review rule and time limit. |
| prior_forecast | Base units of demand forecast before the observation. Preserve the forecast timestamp in the local evidence file. |

In the local training app, validation provides a row count and digest. It never stores measured outcomes. A field installation needs a separate, access-controlled tenant deployment. The local custodian enrolls an already provisioned database using `python scripts/enroll_field.py --data-dir PATH --tenant FIELD_CODE --authorization-ref APPROVAL_CODE`. Both demo tenant IDs are permanently excluded. Register the field protocol before the first baseline day. After registration, only a field owner with an approval reference can import. The database retains the file SHA-256, source reference, authorization reference, actor, protocol and UTC import time. Uploaded CSV content is parsed into allowlisted fields. Free-text patient or staff columns are rejected.

## Analysis and progression

See T03 in `data/templates/T03_pilot_protocol.csv` for each numerator, denominator and unit. Completeness uses eligible SKU-days in the registered windows, including missing days. Outcomes use rows with their specific source fields. The interface reports both observed and eligible counts. Interval estimates remain unavailable because the single branch and repeated measurements within SKUs do not establish independent samples. Inspect rates by SKU at the custodian source where case mix changes.

| Example gate | Rationale and action |
|---|---|
| At least 28 complete days per SKU per window | Covers four weekly cycles. With exactly 28 scheduled days, every day must be complete for each SKU. Longer windows permit the separate completeness threshold to bind. |
| At least 95% of eligible SKU-days complete | Limits ambiguity from missing scans. Core fields include issues, receipts, on-hand, stockout starts and hours, and scan counts. Each outcome also requires adequate coverage of its own fields. |
| At least 85% post-period scan adoption | Proposed usability criterion. Confirm a practical threshold with operators. |
| At least 10% relative reduction in stockout starts per 1,000 observed SKU-days | Proposed operating target. A zero baseline incidence leaves the relative target undefined. Report the two rates and hold the decision. |
| Integration and security reviews complete | No-go pending either review. Check authorized sources, retention, reconciliation and access before proceeding. |
| No unresolved comparability flag | Flag seasonality, staffing or supplier changes, closures, rationing or changes in SKU scope. A flagged comparison goes to pivot review. |

During or after collection, a tenant owner records current safety, integration and comparability status in the governance review form. Append-only reviews preserve the actor and time. The newest review updates the decision while the registered scope and thresholds stay locked.

Failing evidence sufficiency places the decision on hold. Missing adoption or an undefined relative improvement also holds the decision. Adequate evidence with missed adoption, missed improvement or a confounder calls for investigation. Meeting all prespecified gates makes the proposal eligible for human review.

The single-branch result describes a temporal association. Changes in lead time, procurement, staff mix, scanning completeness, clinic closures or seasonal demand can explain movement. Censor unobserved periods explicitly. Preserve the same risk set in both windows and document any excluded days. For a stronger next study, choose a comparable branch with a concurrent baseline or stagger introduction across independent sites, register its analysis plan and use cluster-aware inference. No clinical, procurement or ROI effect has been established.
