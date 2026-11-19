# MedCura AI datathon story

Ten-slide speaking guide for a panel evaluating a proposed Saudi inventory pilot.

## 1. Inventory decisions for Saudi private medical complexes

A branch manager needs to know what can be issued today, what may expire and what needs approval before the next delivery.

- **Start in Riyadh.** A proposed single-branch pilot tracks gloves, masks and dressings.
- **Make decisions traceable.** Every reorder or transfer should explain its quantity, timing and evidence.

Use the prototype to show how an inventory record becomes a reviewable supply decision. State at the outset that the Saudi market counts come from dated statistics and branch transactions in the demo are synthetic. The operational value of this proposal remains a pilot question.

Figure F05. Evidence class SCENARIO. Source: Supplied Arabic presentation guide, slide 1; MedCura AI Visual Research and Codex Blueprint, pages 2 and 5.

## 2. What can the branch safely issue today?

A carton on a shelf may already be reserved. A lot can expire before the next inventory count. Staff need both quantities before promising supply.

- **Usable units.** Separate physical stock from reservations, quarantine and expired lots.
- **Evidence gap.** The supplied workbooks contain no dated branch issues, write-offs or counting shifts.

Use a concrete stocked-but-unavailable example. Stockout events, expiry losses and staff time are outcomes to measure. The guide describes the operating problem, but it does not quantify its prevalence across Saudi complexes.

Figure F07. Evidence class UNKNOWN. Source: Supplied Arabic presentation guide, slide 2; MedCura AI Visual Research and Codex Blueprint, pages 5 and 8.

## 3. The regional insurance figures are estimates

A workbook status cell cannot establish that a value was observed. Keep the source, definition and time window beside the number.

- **Workbook A.** A complete dated regional series is missing. The Q1 2026 figure covers the whole country.
- **Workbook B.** Regional estimates allocate a national pool using facility and population weights of 65% and 35%.

Separate an observation with incomplete primary verification from a derived number and a scenario. Workbook B labels some allocated values verified; the allocation still depends on assumptions. Avoid merging national estimates across different reporting windows.

Figure F04. Evidence class SCENARIO. Source: Supplied Arabic presentation guide, slide 3; workbooks A and B, 03 Insurance by Region!A2:E14 and 04 Insurance National.

## 4. Three regions account for 70.1% of private complexes

2,527 of 3,607 private medical complexes were in Riyadh, Makkah and Eastern Province in the 2024 workbook.

- **Riyadh.** 1,171 locations
- **Makkah.** 880 locations
- **Eastern Province.** 476 locations

The national count reconciles across all 13 administrative regions. Makkah refers to the region. The facility count gives a geographic footprint. There is no chain ownership or buyer identifier. The top seven total 3,238, or 89.8%. Population denominators refer to the 2022 census.

Figure F02. Evidence class DERIVED. Source: Supplied Arabic presentation guide, slide 4; Workbook A (Datathon Dataset - MedCuraAI - Completed.xlsx), 01 Facilities!A4:H18. Workbook A (Datathon Dataset - MedCuraAI - Completed.xlsx), 02 Population!A2:F14.

## 5. From one receipt to a reviewed transfer

A dated receipt enters stock in base units. A lot-level issue changes the balance. The next review compares usable stock with demand and expiry.

- **Ledger.** Record and validate each lot movement.
- **Policy.** Compare inventory position with lead-time demand and a safety buffer.
- **Review.** A named approver checks the lot, quantity and route before dispatch.

Demonstrate this sequence with the synthetic branch workspace. Explain why an order cannot increase physical stock before receipt, and why a transfer leaves the source once, then reaches its destination on receipt. Actual adoption and outcomes depend on future field data.

Figure F06. Evidence class SYNTHETIC_DEMO. Source: Supplied Arabic presentation guide, slide 5; MedCura AI Visual Research and Codex Blueprint, pages 6–8; prototype ledger and transfer controls.

## 6. A chain signs. Its branches use the service.

Facility locations provide a search area. Contracting and revenue require separate assumptions about the number of reachable chains, paid conversion and enabled branches.

- **Partner discovery.** Identify the buyer and how many branches that buyer controls.
- **Unit economics.** Price per paid branch and month. Model onboarding, recurring support, hosting and churn.

Test willingness to pay and implementation effort with potential buyers. Other vendors advertise inventory or forecasting capabilities. Position reviewable recommendations and light integration as hypotheses for buyer interviews. Healthcare-specific competitor prices remain unknown where the evidence gives no public rate.

Figure F03. Evidence class SCENARIO. Source: Supplied Arabic presentation guide, slide 6; Workbook A (Datathon Dataset - MedCuraAI - Completed.xlsx), 06 Competitors!A2:H13; MedCura AI Visual Research and Codex Blueprint, page 11.

## 7. One branch, comparable observation windows

Track the same non-pharmaceutical SKUs in a Riyadh branch before and after reviewed alerts begin.

- **Baseline.** Record eligible SKU-days, stockout starts and hours, write-offs and staff counting time.
- **Silent review.** Reconcile scans and compare simple forecasts without changing purchasing.
- **Intervention.** Turn on human-reviewed alerts. Log actions, missed scans, staffing and lead-time changes.

Pre-register the eligible SKU list, windows, main outcome, thresholds and censoring rules with the site. Add a comparison branch or staggered start where feasible. A single-site pre/post difference is an association and seasonality can affect it. Actual pilot outcomes are not measured.

Figure F08. Evidence class SCENARIO. Source: Supplied Arabic presentation guide, slide 7; MedCura AI Visual Research and Codex Blueprint, page 9.

## 8. A pilot in 2027 precedes regional expansion

Each step requires evidence from the preceding stage and permission from the next participating operator.

- **2027   Riyadh.** Seek one branch in a region with 1,171 private complexes. Review baseline quality and adherence.
- **2028   Makkah and Eastern.** Test replication across the three-region footprint of 2,527 locations.
- **2029   Four further regions.** Consider Asir, Madinah, Qassim and Jazan. Seven regions total 3,238 locations.

The geographic counts come from 2024. The years describe proposed commercial decisions. They do not establish new contracts, integrations or installations. Pause an expansion if support capacity, reconciliation or economics fail the agreed review.

Figure F09. Evidence class SCENARIO. Source: Supplied Arabic presentation guide, slide 8; Workbook A (Datathon Dataset - MedCuraAI - Completed.xlsx), 01 Facilities!A4:H18. MedCura AI Visual Research and Codex Blueprint, page 12.

## 9. The pilot must measure both benefit and failure

Pair each operating measure with a denominator and record events that can bias it.

- **Availability.** Stockout starts per 1,000 eligible SKU-days and unavailable hours per eligible observation window.
- **Waste and effort.** Write-off quantity and cost, tracked inventory value, and counting hours for the same scope.
- **Reliability.** Missing scans, reconciliation corrections and lead-time shifts can change the apparent result.

Agree a go, pivot or no-go rule before observing post-period results. Inspect adverse changes in availability or recording quality alongside any apparent benefit. Count episodes separately from affected SKU-days. Do not replace actual write-offs with estimated risk.

Figure F08. Evidence class SCENARIO. Source: Supplied Arabic presentation guide, slide 9; MedCura AI Visual Research and Codex Blueprint, page 9; T03 measurement protocol.

## 10. What a Riyadh pilot partner can test

Bring a branch owner, a stockkeeper and an authorized operational extract to the same pilot review.

- **The data request.** A SKU and unit dictionary, dated receipts and issues, lot attributes, lead times and physical counts.
- **The decision.** Agree how to measure availability, expiry, effort and adoption before the first alert goes live.

Close with a request for an authorized operational pilot, rather than a promise of savings. Source-linked statistics support the geographic case, the local prototype demonstrates a workflow, and a measured trial is the next evidence gate.

Figure F10. Evidence class SCENARIO. Source: Supplied Arabic presentation guide, slide 10; Workbook A (Datathon Dataset - MedCuraAI - Completed.xlsx), 01 Facilities!A4:H18. MedCura AI Visual Research and Codex Blueprint, pages 9 and 12.
