# Data placement

The checked-in analytic tables retain year, source references and evidence labels. Demo files are generated from the fixed synthetic inventory history. The pilot workbook is a blank template.

To reproduce from authorized originals, obtain the files and match their SHA-256 values in [source_manifest.json](source_manifest.json). Place the four supplied inputs under data/raw and the V3 contract at the root under its original name. The reproduction command will check their hashes and run extraction in a temporary worktree. Treat the full worksheet and PDF snapshots as local source artifacts. The Git release includes a selected cell index for the app's public facility and population tabs and its provenance pointers.

