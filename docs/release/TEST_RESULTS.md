# Research release checks

Fresh verification ran on Windows with CPython 3.12, Node 24 and the installed Chrome browser. The [evidence folder](evidence) records command output with no credentials.

| Check | Status | Command and result |
|---|---|---|
| Baseline inventory | PASS | ZIP integrity and byte comparison, 128 original files, zero drift |
| Raw regeneration | PASS | `python -X utf8 scripts/reproduce_all.py --out <fresh-directory> --ingest-python <extractor-python>`, twice. All 59 hashed outputs identical |
| Compile and full Python suite | PASS | `python -X utf8 scripts/check.py --pipe`, 48 passed, zero skipped with originals available |
| Native API | PASS | `python -X utf8 -m unittest tests.test_api -v`, six passed via real localhost TCP |
| Browser suite, pipes | PASS | `node tests/e2e.cjs --pipe`, nine passed |
| Browser suite, real localhost | PASS | `node tests/e2e.cjs`, nine passed, TCP HTTP |
| JavaScript syntax and dependency health | PASS | `node --check` for both app scripts and browser tests, `python -m pip check` |
| Scientific figure/table QA | PASS | 12 valid SVG, 12 PNG at 300 dpi, 12 PDF, eight UTF-8 CSV. Contact sheet reviewed |
| Release document structure | PASS | 10 unchanged original slide layouts in research edition, four revised notes and 11 pages in appendix report |
| Ruff, mypy and package vulnerability scan | NOT RUN | Tools unavailable on this host. Application and source archive checks ran with standard-library tooling |
| Docker and hosted CI | NOT RUN | Docker unavailable. CI configuration is included for GitHub execution |
| Private remote | BLOCKED | GitHub CLI returned HTTP 401. See [private publication procedure](PRIVATE_PUBLICATION.md) |

The original delivery reported native loopback as blocked. The new release verified it independently by launching the prototype through Playwright and exercising the real HTTP API.


## Clean Git archive

**PASS**. All file hashes matched the artifact manifest. Python ran 48 tests, with 46 passes and two expected raw-source skips. All nine browser workflows passed through pipes. The complete publication pipeline regenerated from checked-in canonical tables, with restricted originals absent.

A direct local clone attempt was blocked by the Windows Git shell with an access-denied error. The clean Git archive served as the equivalent content check. The first archive revealed Git newline normalization drift. The release now stages files without newline conversion and verifies byte hashes. The raw generated SVG files and preserved source retain their original formatting.
