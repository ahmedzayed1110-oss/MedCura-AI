# Implementation record

Work began in the empty projectless workspace read-medcura-ai-one-shot-codex under Documents/Codex/2026-11-19. There was no pre-existing application or Git remote. All project files are under outputs/medcura-ai. The supplied pasted V3.0 text was read as the requested master contract and preserved under its requested Markdown filename. Both original XLSX files and both PDFs were inspected and copied unchanged under data/raw. The optional earlier Markdown engineering blueprint was absent.

1. Inspected nine worksheets in each workbook, extracted both PDFs, catalogued source hashes, and generated typed regional observations, conflicts and cell lineage. The spreadsheet audit retains blank values, formulas/caches, sheet metadata, URLs and periods. The research guide contains 10 slide topics across six PDF pages. The separate blueprint contains 17 pages.
2. Implemented local session authentication, per-tenant SQLite persistence, initialization, deterministic opening movements and a signed-delta stock ledger. Implemented role/scope, replay, rollback and approval checks before wiring UI actions.
3. Built calendar-aware forecasting, order checks, FEFO allocation, expiry and transfer checks, pilot protocols and a three-case economic model. Public and synthetic evidence are separate input paths.
4. Built the 12-section responsive English application and linked it to the API. Generated the scientific narrative, standalone PDF/PPTX, research tables, figure catalog, vector and raster assets, diagrams and source notes.
5. Ran integrity, concurrency, authorization, scenario, forecasting, study and presentation tests. Exercised browser-driven mutations on a temporary local database. The reproducibility record includes both the blocked loopback transport and successful pipe-based verification.

## Stack decisions

A Python standard-library HTTP service and SQLite replace the suggested multi-service stack. The offline app requires only Python and a browser. Transactional integrity, permissions and calculations are server-enforced. The browser uses plain JavaScript and local CSS. There is no separate TypeScript compilation or frontend bundling step. The project includes a development Compose configuration and a proposed GitHub Actions workflow. Neither has been executed in a remote CI environment.

## Asset production

Source regeneration is described in README.md. The XLSX template contains an editable observation sheet and field guide. The generator is scripts/template.mjs and uses the bundled artifact-tool package. The deck generator scripts/deck.mjs renders the slides with artifact-tool. For a fresh editable chart workbook, run `node scripts/deck.mjs candidate.pptx` and `python scripts/embed_chart.py candidate.pptx presentation/MedCura_AI_Datathon.pptx`. Source lines and table values are preserved in the native chart. The original deck package was also checked for its native chart, embedded workbook, 10 notes and source references.

The ten slide previews, five report page previews, figure contact sheet and real browser captures were used for visual review. Only final assets and selected browser screenshots are shipped. The runtime state and developer credentials are excluded.

