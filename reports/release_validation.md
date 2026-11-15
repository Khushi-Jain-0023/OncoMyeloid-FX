# Release validation — 0.1.0

2026-11-16. **Passed.** Machine-readable evidence is in results/phase5_verification.json.

## Build and installation

- Built both the Python source distribution and wheel with the pinned build tools.
- Installed the wheel into a newly created Python 3.11.9 virtual environment, separate from the analysis runtime's site-packages.
- Installed the analysis lock into that environment; the CLI doctor matched all 87 pinned packages.
- Tested the installed runner against a fresh extraction of the candidate research ZIP. Status, doctor and read-only SHA256 integrity verification passed.

## Clean-copy reproduction

- All **19 tests** passed before rerunning analysis and again afterward.
- Phase 3 curation, rankings, executed notebook and verifier completed successfully through the installed CLI.
- Phase 4 bootstrap/ablations, executed notebook and verifier completed successfully through the installed CLI.
- Compared 11 CSV outputs with the reference, using rtol 1e-10 and atol 1e-12 for floating values. All matched. Tables include baseline/integrated rankings, coverage, weight sensitivity, ablations, patient omissions, rank/effect resampling, bootstrap draws, failure cases and unavailable evaluation metrics.
- Compared the functional-evidence Parquet table with the reference. It matched.
- The scientific decision stayed inconclusive. Reproduction is not independent biological validation.

The receipt preserves executed command exit codes, log locations and the tested candidate archive hash. The final ZIP adds completed release documentation and its local Git revision; its own manifest and external SHA256 file identify that final artifact. No analysis algorithm changed after the successful clean-copy test.

## Practical limits

The raw single-cell Phase 2 pipeline was not rerun during this release check. Its earlier completed analysis, tests, source hashes and artifacts are preserved. The full raw UMI archive and H5AD caches are deliberately omitted from the compact release; download instructions and expected hashes are provided. Cross-platform execution has not been tested. GitHub and package-registry publication were not performed.

A temporary build-directory permission error was resolved by placing build temporary files inside the project workspace. This affects this sandbox's build process, not numerical results. The notebook builders use asynchronous kernel management to exit cleanly on this Windows runtime.
