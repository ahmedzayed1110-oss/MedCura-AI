# Source conflicts and decisions

The [comparison table](../data/processed/T02_conflicts.csv) records both values, cell addresses, reference periods and decisions in 59 entries. A missing observation is null in JSON and empty in CSV.

| Issue | Source observations | Decision |
|---|---|---|
| Regional insurance | A cites 9.7M for Riyadh without a dashboard date and has unavailable values elsewhere. B allocates 13M using 65% private-facility share and 35% population share. | Keep the dated observed series empty. Retain the undated source observation and label all B regional estimates SCENARIO. |
| National insurance | A `04 Insurance National!B5` reports 14.5M in Q1 2026. B `03 Insurance by Region!B15` reports 13M in 2024. | Retain both periods. Only the 2026 figure has primary corroboration here. The 23 health insurers reported in 2025 are companies. |
| Clinic definition | A `01 Facilities!G18` gives 56 single-doctor clinics. B marks broader standalone clinics unavailable. | Keep the narrow class separate. Broad standalone total stays unknown. |
| Growth | Sheet 02 column D in A reports change from 2021 to 2022. The same column in B reports 2010–2022 compound annual growth. | Preserve fractional rates with period and formula. Historical inputs required to independently reproduce the rates are absent. |
| Workforce | A reports 38,905 physicians and 22,100 beds for Riyadh at `05 Workforce!B2:C2`. B assigns 31,679 and 19,348 using weights. | Prefer A's attributed MOH branch aggregation. Mark all of B's regional estimates as scenarios. |
| Competitor pricing | A cites one generic WMS benchmark. B includes pricing per practitioner, user, clinic, installation and enterprise quote. | Retain raw price text and source. Leave comparable healthcare inventory prices null. |
| Density and throughput | B `07 Regional Analysis!I3` interprets facility density as throughput pressure and urgent replenishment need. | Use density to describe geography. Consumption and patient activity require separate evidence. |
| Timeline | B's Makkah commentary proposes 2027. The guide proposes a Riyadh-first pilot and conditional expansion in 2028. | Use the adopted stage-gated strategy. |
| Hospital subtotals | Guide p.3 reports 9 private hospitals in Madinah and 4 in Jazan. Both workbooks `01 Facilities!D8,D13` report 10 and 3. | Use the agreeing workbook values, retain both PDF observations and flag the guide for correction. |

Agreement between the two workbooks establishes transcription consistency. Both cite overlapping sources. Health-policy alignment in the narrative remains a strategic interpretation and carries no institutional endorsement claim.

