# Table register

Run `python scripts/reproduce_all.py --out reproduction` for all eight UTF-8 CSVs. Blank cells denote missing or inapplicable values.

| CSV | Schema and interpretation |
|---|---|
| [T01](../tables/T01.csv) | Region and rank, integer facility and population counts, mixed-year density, shares, reference years and per-field lineage |
| [T02](../tables/T02.csv) | Conflict ID, source references, reported values, evidence status and resolution. Regional insurance allocation is scenario evidence |
| [T03](../tables/T03.csv) | Stable claim IDs, source file and pointer, calculation, period, value/unit, type, caveats and destinations |
| [T04](../tables/T04.csv) | Model, MAE, WAPE, sMAPE, bias, shortage units, seven-origin split and development selection |
| [T05](../tables/T05.csv) | Synthetic decision cases, quantities, units and assumptions |
| [T06](../tables/T06.csv) | Proposed year, stage, criterion and threshold status |
| [T07](../tables/T07.csv) | Measure, numerator, scope/denominator, unit, collection notes and outcome status |
| [T08](../tables/T08.csv) | Case, period, parameter/metric, unit, numeric value and scenario classification. Monetary units are labeled SAR or their applicable SAR rate |

