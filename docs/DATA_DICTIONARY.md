# Market and evidence dictionary

| Field or table | Meaning and grain |
|---|---|
| regions.json | One record per administrative region. Rows descend by private-complex count. Alphabetical English name breaks ties. |
| complexes, phcs, private_hospitals, government_hospitals, hospitals | 2024 locations in each named class. PHCs here are government primary health centers. |
| clinics | Single-doctor private clinics reported by A. The broader standalone-clinic total remains unknown. |
| population | Persons in the 2022 Census. Workbook cites MOH 2023 yearbook table 1-4. |
| insured | Comparable, dated observed regional beneficiaries. Null for all 13 regions. The undated Riyadh figure remains in the lineage record's reported_value. |
| share_pct | 100 × region's complexes / national complexes. |
| cumulative_pct | 100 × running sorted sum of complex counts / national complexes. |
| density | 100,000 × 2024 private complexes / 2022 population. A separate intensity in workbook sheet 07 includes a broader numerator of hospitals, PHCs and complexes. |
| rank | One-based position in sorted display. Regions tied on count have equal footprint. |
| metrics.json | National aggregates, grouped regional counts, shares and insurance context. |
| lineage.json and lineage.csv | Field-level evidence records keyed by region ID and field, or by national indicator. Derived ratios carry numerator, denominator and factor. |
| cells_A.json and cells_B.json | Populated raw cells with workbook ID, worksheet, address, value, formula, cached result and detected URLs. |
| T01_regions.csv | Regional values with field-specific references, evidence labels and units. |
| conflicts.json and T02_conflicts.csv | Material discrepancies and review decisions, one entry per pair of source values. |
| competitors.json | Each named listing per workbook. Original commercial wording is kept in reported_price. Comparable healthcare-specific price_sar remains null. |
| pages_guide.json and pages_blueprint.json | Extracted page text, table cells, dimensions and one-based page number. |

Each evidence record carries value, evidence_level, reference_year, source_ref, unit, notes, calculation_id and citation_url. Null calculation IDs identify a transcription or unknown observation. Reference periods can be a year, a quarter, a multi-year window or null. The timestamp of extraction differs from both the observation period and publication date.

The ETL rejects missing required counts, duplicate or unrecognized region IDs, workbook disagreement on shared facility or population fields, and failed subtotal reconciliations. Zero is meaningful for Al-Baha's private hospitals in 2024. Blank values never establish zero facilities. Makkah covers the administrative region. No individual facility or chain is identifiable in these rows.

