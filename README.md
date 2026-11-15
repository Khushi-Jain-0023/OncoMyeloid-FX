# OncoMyeloid-FX

**Research release 0.1.0.** Descriptive macrophage/T-cell analysis in 11 primary lung-tumor patients, exploratory mouse-marker evidence integration, and patient-level robustness. Independent functional validation is **inconclusive**; this release makes no predictive or clinical claim.

Start with [the final report](reports/final_report.md) and [the reproducibility walkthrough](reports/reproducibility.md). Use the complete research ZIP, which includes the installable CLI wheel and bundled inputs for Phases 3–4. The wheel alone contains the runner, not the research data. The optional web interface is not included.

```text
python -m pip install -r requirements-phase3-lock.txt
python -m pip install dist/oncomyeloid_fx-0.1.0-py3-none-any.whl
python -m oncomyeloid_fx status
python -m oncomyeloid_fx doctor
python -m oncomyeloid_fx verify
python -m oncomyeloid_fx test
```

Run in an isolated Python 3.11 environment from the extracted research ZIP. `verify` is read-only; phase reruns change output timestamps/hashes and should use a separate working copy. No API key is required. GitHub publication remains deferred.

## Reproduce

Use Python 3.11 and install `requirements-lock.txt` into an isolated environment. Run commands from this repository root. On this Windows machine, the isolated interpreter is `work/python-runtime/python.exe`; it does not change system Python.

Download these public GEO supplementary files into work/:

| Local filename | Source |
|---|---|
| umi_matrix.txt.gz | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE131nnn/GSE131907/suppl/GSE131907_Lung_Cancer_raw_UMI_matrix.txt.gz |
| GSE131907_cell_annotation.txt.gz | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE131nnn/GSE131907/suppl/GSE131907_Lung_Cancer_cell_annotation.txt.gz |
| sample_metadata.xlsx | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE131nnn/GSE131907/suppl/GSE131907_Lung_Cancer_Feature_Summary.xlsx |
| hgnc_complete_set.txt | https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt |

The HGNC file supplies approved-symbol stable IDs; snapshot/hash are retained. Do not substitute a newer snapshot when reproducing IDs. The matrix is about 409 MB compressed; ingestion streams one gene at a time and saves sparse primary-lung counts. Allow several GB of RAM and disk for caches, Python and outputs.

```text
python phase2.py
python -m pytest tests -q
python summarize_phase2.py
python build_notebook.py
python verify_phase2.py
```

Configuration: configs/phase2.json. Protocol: reports/phase2_protocol.md. Main report: reports/transcriptomic_baseline.md. Notebook: notebooks/02_transcriptomics.ipynb. Results and figures: results/. Manifest includes input/config/code hashes, versions and timestamp. Derived count caches are in data/curated/ and are omitted from Git.

The pipeline reuses count and doublet caches. If changing inputs or preprocessing settings, move the old derived caches/results into a separate run directory before rerunning; never mix configurations. Original downloaded source files should remain immutable. Source workbook XML is read directly because its custom-property metadata is malformed for openpyxl; original contents are unchanged.

Tests check robust regression against statsmodels, BH correction, missing/constant inputs and composition-only/within-state-only synthetic changes. All inference uses patients, never cells as replicates. No clinical, causal or validated immune-function prediction is produced.

## Phase 3: evidence and exploratory ranking

The Phase 3 implementation curates 35,103 quantitative mouse immune-marker records (11,701 genes, three endpoints) and six qualitative T-cell-function leads. It exports transcriptomic baselines and separate MHCII, CD40 and PD-L1 proxy-integrated ranks for 5,155 human candidates; 969 have no eligible mapped evidence and remain unranked for integration. This is descriptive prioritization, not a validated T-cell-function model. The original direct functional objective remains data-limited.

Install `requirements-phase3-lock.txt` in Python 3.11 for the combined pipeline (adds PyArrow). Phase 2's original lock remains unchanged. Input download URLs are in `configs/phase3.json`; downloaded snapshots live in `data/sources/phase3/`. Preserve the existing HGNC snapshot at `work/hgnc_complete_set.txt`. Verify hashes against `results/phase3_manifest.json` before substituting or re-downloading any changing reference database. An archive recipient can reproduce Phase 3 from the bundled source snapshots, candidate table and HGNC snapshot without rerunning Phase 2.

```text
python phase3.py
python -m pytest tests -q
python build_phase3_notebook.py
python verify_phase3.py
```

Read `reports/scoring_spec.md` and `reports/phase3_evidence_ranking.md`. Outputs: `data/curated/functional_evidence.parquet`, `results/baseline_rankings.csv`, `results/integrated_rankings.csv`, orthology/coverage/weight-sensitivity audits, manifest, verification receipt and `notebooks/03_evidence_ranking.ipynb`. Tests cover unknown versus measured-zero evidence, ambiguous mappings, identifier collisions, endpoint isolation, excluded-family invariance, and source positive controls. No API key or login is required. Phase 4 subsequently completed the current-data assessment with an inconclusive independent-validation decision.

## Phase 4: robustness and inconclusive benchmark decision

Phase 4 completes the current-data evaluation with an **inconclusive** independent-validation decision. There are zero eligible independent quantitative T-cell-function outcomes. Missing performance metrics and confidence intervals remain missing in `results/evaluation_metrics.csv`; no accuracy or superiority claim is made.

The completed robustness analysis uses 300 paired patient-bootstrap draws, 11 leave-one-patient-out refits and 15 ablations per marker. Omitting one patient preserves only 9–17 of the original top 20 across marker endpoints. Rank ranges and selection frequencies are descriptive and condition on fixed mouse marker evidence; they are not functional-performance confidence intervals.

Use the existing `requirements-phase3-lock.txt` environment; no new dependencies are needed. Preserve Phase 3 hashes and outputs, the patient feature/expression matrices, and the saved sensitivity models. The pipeline checks source provenance before running.

```text
python phase4.py
python -m pytest tests -q
python build_phase4_notebook.py
python verify_phase4.py
```

Deliverables: `reports/benchmark.md`, `reports/leakage_audit.md`, `reports/phase4_protocol.md`, `results/evaluation_metrics.csv`, `results/phase4_*.csv`, two robustness figures, manifest/verification receipt and `notebooks/04_benchmark_robustness.ipynb`. The tests independently check vectorized HC3 against statsmodels, including duplicated patient draws, plus missingness, tied top-k selection, leakage rejection and real-output invariants. Future independent validation needs new compatible quantitative studies and a protocol frozen before outcome inspection.
