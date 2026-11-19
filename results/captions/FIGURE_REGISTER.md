# Matplotlib figure register

Rebuild each figure with `python scripts/reproduce_all.py --out reproduction`.

## F01 · Private medical complexes by region

Facility locations ranked across 13 administrative regions.

**Status and units** OBSERVED_PUBLIC. 2024 · locations. **Source** data/processed/T01_regions.csv; 01 Facilities F5:F17. [SVG](../figures/F01.svg) · [PNG](../figures/F01.png) · [PDF](../figures/F01.pdf)

## F02 · Concentration of private complexes

Top three account for 70.1%; top seven account for 89.8%.

**Status and units** DERIVED. 2024 · locations and percent. **Source** T01; cumulative sum / national total. [SVG](../figures/F02.svg) · [PNG](../figures/F02.png) · [PDF](../figures/F02.pdf)

## F03 · Private complexes per 100,000 residents

Mixed-year footprint ratio; operational pressure and patient traffic remain unknown.

**Status and units** DERIVED. 2024 facilities / 2022 residents. **Source** T01; 100000 × complexes / population. [SVG](../figures/F03.svg) · [PNG](../figures/F03.png) · [PDF](../figures/F03.pdf)

## F04 · How evidence enters the prototype

Public observations, computed indicators, synthetic histories and scenarios retain distinct evidence labels.

**Status and units** DERIVED. 2022–2029 · conceptual. **Source** docs/EVIDENCE_BOUNDARIES.md; T03. [SVG](../figures/F04.svg) · [PNG](../figures/F04.png) · [PDF](../figures/F04.pdf)

## F05 · Inventory lifecycle and ledger controls

A simulated receipt or issue records an authenticated inventory movement.

**Status and units** SYNTHETIC DATA. Prototype · conceptual. **Source** apps/api/inventory.py; tests/test_inventory.py. [SVG](../figures/F05.svg) · [PNG](../figures/F05.png) · [PDF](../figures/F05.pdf)

## F06 · One-day forecast errors by baseline

Five baselines evaluated over seven forward one-day origins. Clinic accuracy remains unmeasured.

**Status and units** SYNTHETIC DATA. November 2026 · MAE in gloves. **Source** experiments/runs/backtest.json; T04. [SVG](../figures/F06.svg) · [PNG](../figures/F06.png) · [PDF](../figures/F06.pdf)

## F07 · Weekly naive forecast and synthetic observations

The model was selected by November 11, before the November 12–18 holdout.

**Status and units** SYNTHETIC DATA. September–November 2026 · gloves. **Source** experiments/runs/backtest.json. [SVG](../figures/F07.svg) · [PNG](../figures/F07.png) · [PDF](../figures/F07.pdf)

## F08 · How a reorder recommendation is built

Inventory position, lead-time demand and pack constraints inform a human-reviewed recommendation.

**Status and units** SYNTHETIC DATA. Prototype · conceptual. **Source** apps/api/science.py and inventory.py; T05. [SVG](../figures/F08.svg) · [PNG](../figures/F08.png) · [PDF](../figures/F08.pdf)

## F09 · Transfer approval and stock in transit

Dispatch records an issue at origin. Destination stock increases upon receipt.

**Status and units** SYNTHETIC DATA. Prototype · conceptual. **Source** apps/api/inventory.py; T05. [SVG](../figures/F09.svg) · [PNG](../figures/F09.png) · [PDF](../figures/F09.pdf)

## F10 · Geographic expansion gates

Later regions depend on evidence readiness and operational feasibility.

**Status and units** SCENARIO. 2027–2029 · proposed gates. **Source** apps/api/study.py; T06. [SVG](../figures/F10.svg) · [PNG](../figures/F10.png) · [PDF](../figures/F10.pdf)

## F11 · Modeled break-even branch requirement

Compare equivalent active branches under editable price, branch cost and overhead assumptions.

**Status and units** SCENARIO. 2027–2029 · active branches. **Source** T08; apps/api/study.py. [SVG](../figures/F11.svg) · [PNG](../figures/F11.png) · [PDF](../figures/F11.pdf)

## F12 · Riyadh pilot measurement design

A baseline, silent review and intervention track prespecified stock and effort measures.

**Status and units** FIELD OUTCOMES NOT YET MEASURED. Proposed · conceptual. **Source** docs/PILOT_PROTOCOL.md; T07. [SVG](../figures/F12.svg) · [PNG](../figures/F12.png) · [PDF](../figures/F12.pdf)

