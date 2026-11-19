# Verification record

Host verification used Windows, bundled CPython 3.12.14, Node 24.22.3, Playwright 1.62.1 and installed Google Chrome. CLI commands below are shown relative to the project root with python and node standing for those binaries.

| Command or check | Observed result |
|---|---|
| python -m pip install --no-index --disable-pip-version-check -r scripts/requirements-evidence.txt | Exit 0. Pinned extraction dependencies were already installed |
| python scripts/ingest.py | Exit 0. Two nine-sheet workbooks, two PDFs, 13 regions, 59 conflicts and 231 lineage records. Version regional-v1-e9466e5c222f2afb |
| python scripts/benchmark.py | Exit 0. Five baseline rows and seven held-out forecast points written from the operational seed |
| python scripts/stress.py | Exit 0. Six synthetic interventions and fixed-policy comparison |
| python scripts/openapi.py | Exit 0. Local OpenAPI 3.1 document generated |
| python scripts/check.py --pipe | Exit 0. Standard-library indentation check, Python compilation and 47 passing tests, 0 failures, 0 skipped |
| node --check on app.js, study.js, deck.mjs, template.mjs and e2e.cjs | All five exited 0 |
| node tests/e2e.cjs --pipe | Exit 0. Nine browser workflows passed, 0 failed, 0 skipped |
| python run.py --data-dir <isolated directory> | Process initialized and bound its loopback listening socket. Real TCP client verification was blocked as described below |
| python scripts/embed_chart.py <candidate.pptx> <rebuilt.pptx> | Exit 0. Opened the embedded workbook and checked 1,171, 880 and 476 against the regional data |

### Test coverage

The 47 tests cover 10 market-integrity checks, nine inventory checks, six HTTP/session and authorization checks, three forecasting checks, one synthetic stress-bench check, 15 economics/pilot checks and three presentation checks. Stock tests use real SQLite files or in-memory databases. A concurrent double issue starts two writers. Exactly one succeeds, and the remaining balance reconciles. Tests also check allowed transitions, replayed receipts, rollback, quarantine release protection, SKU semantics, closed-day consistency, false zero handling, scenario accounting, enrolled imports, duplicate batches and cross-tenant access.

The browser tests sign in using generated temporary credentials and interact with the shipped interface. Each workflow uses production routing and SQLite. The checked workflows were:

1. Sign-in and cell-level lineage from the overview.
2. Keyboard scanner input, two-pack receipt, a three-unit issue and ledger reconciliation.
3. Forecast and reorder explanation.
4. Transfer draft, request, approval, dispatch and receipt.
5. Purchase approval followed by physical receipt.
6. Save a financial case and verify actual pilot outcomes remain unmeasured.
7. Reject an upload with an unapproved pilot column.
8. Filter a region and look up its workbook cell.
9. Navigate a 390-pixel mobile view, reopen stock and verify persisted changes.

The desktop viewport was 1440 × 1024. The mobile viewport was 390 × 844. The saved captures show the actual app. Some screens show transient feedback from an immediately preceding action. Browser results above use the local byte-stream adapter in tests/http_transport.py. It supplies complete request bytes to run.Handler; the actual HTTP parser, authentication, cookies, requests, responses, replay checks and database run normally. The adapter substitutes only for the network transport.

### Unverified execution environments

An early native TCP run passed 36 of 42 tests and raised six connection errors. A later native run passed 40 of 46 tests and again raised six connection errors after network permission was granted. Both exited 1. Windows denied the client connection to 127.0.0.1 with WinError 10013; Chrome reported ERR_NETWORK_ACCESS_DENIED. The default suite and default Playwright command retain genuine TCP testing for a normal workstation. The hermetic test run does not establish network reachability. Docker was absent. Remote CI, container startup, native PowerPoint interaction, real scanners and partner systems were not exercised.

The buildless UI is JavaScript. There is no TypeScript build in this architecture. Python compilation, standard-library tabnanny and JavaScript syntax checks ran. A separate install attempt for Ruff 0.11.8 and mypy 1.15.0 exited 1 because the environment offered no distribution for Ruff. No third-party lint or static type-check pass is claimed.

