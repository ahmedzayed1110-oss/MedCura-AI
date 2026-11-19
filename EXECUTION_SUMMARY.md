# MedCura AI execution summary

**Delivered locally** — source, offline data, persistent application, 10-slide presentation, five-page research report, 11 SVG/PNG figure pairs, Mermaid sources, six requested tables, blank pilot templates, protocols, screenshots and tests. Run `python run.py --open` from this directory. No account, API key or network connection is required for the application data.

**Evidence** — reconciliation of the supplied 2024 facility table gives 3,607 private medical complex locations across 13 administrative regions. Riyadh, Makkah and Eastern Province account for 2,527 (70.1%). The largest seven account for 3,238 (89.8%). Private hospitals are counted separately (166). The population column is from the 2022 census (32,175,224). See data/processed/T01_regions.csv for field-level cell pointers and units. Workbook B’s regional insurance allocation is quarantined as a scenario. Actual operational outcomes remain unmeasured.

**Verification** — 47 Python tests and nine Playwright workflows passed with the production HTTP handler and real SQLite using local byte-stream transport. Stock mutations, conservation, role isolation, independent market arithmetic, financial scenarios, pilot boundaries and presentation artifacts were checked. Windows denied loopback client connections. Docker and third-party static typing were unavailable. Those acceptance items remain unverified.

**Commands executed** — `python scripts/ingest.py`, `python scripts/benchmark.py`, `python scripts/stress.py`, `python scripts/openapi.py`, `python scripts/check.py --pipe`, `node tests/e2e.cjs --pipe`, JavaScript syntax checks, native startup and attempted TCP tests. See docs/TEST_RESULTS.md for exact outcomes and docs/IMPLEMENTATION_REPORT.md for implementation boundaries.

**Next field gate** — one authorized Riyadh partner branch, coded non-pharmaceutical SKUs and lot data, reconciled daily receipts/issues and on-hand, supplier lead times, stockout episodes, expiry write-offs, cost and staff effort. Agree eligible SKU-days, comparison periods, data access, custody and decision thresholds before collecting results.

