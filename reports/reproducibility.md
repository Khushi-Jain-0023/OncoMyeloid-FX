# Reproducibility walkthrough — release 0.1.0

## Prerequisites

Use 64-bit Python 3.11, an isolated environment, several GB of free disk/RAM, and the complete research ZIP. The tested platform is Windows/Python 3.11.9. Other platforms have not been certified; the dependency lock reflects the tested environment. The CLI wheel and source distribution contain the runner, not the scientific data. The ZIP contains the runner sources, wheel, scripts, reports, notebooks and data required to repeat Phases 3–4.

## Install and inspect

Extract the ZIP into a new directory. In a terminal at its root:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-phase3-lock.txt
.venv\Scripts\python -m pip install dist/oncomyeloid_fx-0.1.0-py3-none-any.whl
.venv\Scripts\python -m oncomyeloid_fx status
.venv\Scripts\python -m oncomyeloid_fx doctor
.venv\Scripts\python -m oncomyeloid_fx verify
.venv\Scripts\python -m oncomyeloid_fx test
```

On macOS/Linux substitute `.venv/bin/python`; platform dependency availability is not verified. Alternatively use uv to create a Python 3.11 environment and `uv pip install --python <interpreter> ...`. No API key or account login is needed. Installing dependencies requires internet access; analysis of bundled inputs does not.

The installed `oncomyeloid-fx` executable also supports these commands. Use `--project <path>` before the command to target a different extracted snapshot. `verify` is read-only and checks every packaged file against SHA256 hashes in RELEASE_MANIFEST.json. This checks integrity, not scientific validity or a cryptographically signed publisher identity. `doctor` checks Python and all pinned analysis package versions.

## Recompute from bundled patient-level data

Keep one extracted copy untouched as the reference release. Make a second working copy, then run:

```text
python -m oncomyeloid_fx --project <working-copy> run --phase 3
python -m oncomyeloid_fx --project <working-copy> run --phase 4
python -m oncomyeloid_fx --project <working-copy> test
```

The commands use the interpreter in which the runner is installed. They execute the phase script, its notebook builder and verifier, stopping at the first failure. Phase 3 must precede Phase 4 if it is recomputed: Phase 4 checks the current Phase 3 hashes. Outputs and timestamps change in a working copy, so the original release-integrity check will correctly report changed files. Numerical equivalence, statistical tests and each phase's verification receipt are the rerun checks; do not silently regenerate the reference release manifest to hide differences.

Phase 4 uses the bundled patient expression/feature matrices and Phase 2 sensitivity results; it does not silently recalculate QC or the full single-cell matrix. Phases 3–4 clean-copy reproduction is documented in release_validation.md.

## Recompute from raw single-cell inputs

For full Phase 2 recomputation, download the three GEO files listed in README.md into work/; preserve the supplied HGNC snapshot. The 409 MB raw count archive and large H5AD caches are not bundled. Their expected source hashes are recorded in results/run_manifest.json. Place any changed-input experiment in a separate working copy, without old derived count/doublet caches, to avoid cache reuse across configurations.

```text
python -m oncomyeloid_fx --project <working-copy> run --phase 2
python -m oncomyeloid_fx --project <working-copy> run --phase 3
python -m oncomyeloid_fx --project <working-copy> run --phase 4
```

Phase 2 ingestion streams the complete archive and validates the original cohort. It can take considerably longer than Phases 3–4 and requires the full input files. Its original completed run, tests and artifacts are retained; a new raw-data rerun is not claimed as part of the Phase 5 clean-copy check. The machine-specific embedded runtime under the original project's work/ is not bundled or required for recipients using standard Python 3.11.

## Build the runner and release

```text
python -m pip install -r requirements-build.txt
python -m build --no-isolation
python build_release.py --output <release.zip>
```

The build produces a wheel and source distribution for version 0.1.0. The ZIP builder selects explicit research paths, excludes environments/caches/raw count matrices, and embeds per-file hashes and the local Git revision when available. Git checkout preserves exact bytes through .gitattributes. Source data remain subject to their original provider terms; see NOTICE.md. No package registry or GitHub publication occurs automatically.
