# Reproducibility report

The previous ZIP contains 128 files. Each matched its extracted counterpart byte-for-byte. The preservation directory contains the complete extracted tree and original ZIP. Its checksum inventory covers both. The new repository keeps original app directories and generated deliverables in their original locations.

Two raw-input runs executed extraction in isolated temporary directories. Both matched the existing canonical regional tables, conflicts, lineage and benchmark files. All 59 hashed outputs in the run manifests matched across the two runs. The recorded manifests retain timestamps alongside the separately hashed deterministic outputs.

Market audit yielded 3,607 complex locations across 13 regions in 2024. Riyadh, Makkah and Eastern Province contribute 2,527 or 70.1%. The top seven contribute 3,238 or 89.8%. The 2022 population was 32,175,224. Madinah and Jazan hospital counts and the modeled insurance allocation remain in T02 with the source and decisions. There are 231 lineage records and 59 conflict decisions.

Five baselines reproduce from seeded branch movements. MAEs in gloves/day were 0.8571, 0.1429, 1.0000, 0.7143 and 1.0638. The weekly naive model was selected by validation MAE before November 12. The local run covers seven one-day holdout origins, November 12–18, 2026. Its small synthetic sample supports a descriptive comparison. Stress and revenue outputs also matched prior artifacts. No field effect estimate is available.

Run the build with `python scripts/reproduce_all.py --out reproduction`. In this environment an alternate Python with the extraction dependencies was supplied through `--ingest-python`; both interpreters were CPython 3.12. See [run manifest](../../experiments/run_manifest.json), [experiment summary](../../experiments/README-run.md), [coverage matrix](ARTIFACT_COVERAGE.csv), and [before/after comparison](BEFORE_AFTER.csv).

The original report and deck remain in presentation/. The appendix edition retains the original five pages and appends six Matplotlib pages. The research deck retains ten original slide layouts and adds provenance references to speaker notes. Run `python scripts/publication_supplement.py` with pypdf to build the revised copies after refreshing results/figures.

