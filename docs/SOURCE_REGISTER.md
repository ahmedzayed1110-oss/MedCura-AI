# Source register

| ID | Supplied input | Coverage and use |
|---|---|---|
| A | Datathon Dataset - MedCuraAI - Completed.xlsx | Nine visible worksheets. Source-linked 2024 facilities and workforce, 2022 census population, insurance context and vendor scan. |
| B | اكسل ٢ جيميناي.xlsx | Nine visible worksheets. Confirms facility and census counts. Includes allocated regional values, assumed prices and commercial interpretations. |
| guide | دليل_محتوى_العرض_التقديمي_-_MedCura_AI.pdf | Six pages covering ten slides, the pilot, 2027–2029 strategy and judge questions. Page 3 contains the market table. |
| blueprint | MedCura_AI_Visual_Research_and_Codex_Blueprint.pdf | Seventeen pages on evidence classification, decision logic and the operating model. Pages 16–17 contain an earlier prompt retained as reference material. |
| contract | MedCura_AI_ONE_SHOT_CODEX_MASTER_PROMPT.md | Byte-preserved copy of the pasted V3 execution directive. Engineering specification. |

The [source manifest](../data/source_manifest.json) records SHA-256 hashes, sizes, UTC extraction time, metadata, decoded formulas, caches, URLs and worksheet statistics. Original input copies are in data/raw. The optional prior Markdown blueprint was absent. Dataset version `regional-v1-e9466e5c222f2afb` identifies this pair of source workbook hashes.

Both files have nine visible sheets. A contains 696 populated cells and 92 formulas. B contains 721 populated cells and 102 formulas. Neither file has merged cells. PDF exports include text and detected tables on every page. The Arabic rendering uses ligatures and mixed visual reading order. Consult the original PDF page when working with its prose.

The featured regional counts originate in A and B, `01 Facilities!F5:F17`, and the national subtotal is in F18. Both files report 2022 population in `02 Population!B2:B14`. The [field lookup](../data/processed/lineage.json) includes exact locations, units and calculations. The [regional export](../data/processed/T01_regions.csv) includes field-specific evidence labels.

### External checks on 19 November 2026

| Primary reference | Verified scope |
|---|---|
| MOH yearbook index | Lists the 2024 Excel yearbook with file date 20 Oct 2025 and the 2023 PDF with file date 25 Feb 2025. The browser could not parse the binary workbook, and the 2023 PDF request timed out. Regional facility rows retain workbook-level corroboration. [MOH index](https://www.moh.gov.sa/en/ministry/statistics/book/pages/default.aspx) |
| GASTAT Healthcare Establishments and Workforce Statistics 2024 | Confirms 516 hospitals nationally, 115 in Riyadh and 99 in Makkah, 5,779 combined PHCs and complexes, and 129,772 physicians nationally. [GASTAT publication](https://www.stats.gov.sa/documents/20117/2435273/Healthcare%2BEstablishments%2Band%2BWorkforce%2BStatistics%2BPublication%2B2024%2BEN%2B%281%29.pdf/a9775b6f-5333-c2d7-4f32-dcb5d8c549b0) |
| GASTAT Livability in Saudi Cities 2025 | Page 7 independently confirms the 2022 national population of 32,175,224. Its city-specific facility statistics have a different geographic scope. [GASTAT publication](https://www.stats.gov.sa/documents/20117/2435245/GASTAT_LISC%2Breport_2025_EN.pdf/80b46893-12e0-2b26-2a54-70a1553169c1) |
| Insurance Authority | The Q1 2026 report announcement dated 8 September 2026 corroborates 14.5 million health beneficiaries nationally. [Insurance Authority](https://www.ia.gov.sa/en/media-center/news/128) |
| CHI and Saudi Census portals | CHI timed out and the Census portal was unavailable to the retrieval tool. A complete dated official regional beneficiary series still requires a primary source. [CHI](https://www.chi.gov.sa/en/pages/Home.aspx) and [Saudi Census](https://portal.saudicensus.sa/portal) |
| Medlog | Advertises seasonal medicine-demand forecasting and supply tracking. Independent customer deployment and price remain unverified. [Medlog](https://medlog-sa.com/) |
| iMED and Stokvera | URLs responded without readable page text. Descriptions remain attributed to the workbooks. [iMED](https://imed.sa/erp) and [Stokvera](https://stokvera.tech/terms) |

### Regeneration

From the project directory run `python -m pip install -r scripts/requirements-evidence.txt` and `python scripts/ingest.py`. The shipped snapshots support offline app startup. ETL requires no network after installing the extraction dependencies. Run `python -m unittest discover -s tests -p test_market.py -v` for direct OOXML verification.

