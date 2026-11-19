# Requirements traceability

T06_requirements.csv maps each module and acceptance gate to its implementing source, artifact, and automated check. Test locations are relative to the project root. Read TEST_RESULTS.md for execution details and scope.

| Gate | Coverage |
|---|---|
| A · Data | Independent OOXML reads, 13 region IDs, national totals, year and unit semantics, missingness, price treatment, assertions on malformed inputs |
| B · Inventory | FEFO, reservation ownership, returns, expiry, pack conversion, count reconciliation, immutable deltas, concurrency and conservation |
| C · Forecast | Chronological model selection, disjoint holdout, nonnegative quantities, zero-denominator behavior, missing scan and cold-start fallback |
| D · Decisions | Reorder boundary, lead time, MOQ/pack/capacity, stale approval, transit/confirmed order arithmetic, sender/recipient and shelf-life gates |
| E · Web/API | Authenticated HTTP parser and session handling, scoped reads/writes, mutations, sanitized export, browser navigation and responsive view |
| F · Reproducibility | Repeated data ingestion, deterministic stress runs, bytecode compilation, JS syntax, portable CLI and pinned QA dependency. Native TCP, external linters and Docker limits are recorded |
| G · Demonstration | Browser-driven receive, issue, decision review, transfer approval/dispatch/receipt, purchase receipt, saved scenario and gated pilot |

The pilot progression gate uses agreed site conditions, observed item-day coverage and sign-offs. A local test passing cannot satisfy a real clinic’s governance or benefit threshold.

