# OncoMyeloid-FX — Technical Requirements Document

**Version:** 1.2 · **Implementation:** Python research CLI + scripts/notebooks · **Status:** Release 0.1.0 complete; independent validation inconclusive

**Phase 2 amendment (2026-11-15):** User authorized a descriptive baseline despite the predictive NO-GO. Implement the cohort-specific protocol in reports/phase2_protocol.md and configs/phase2.json. Published annotations plus marker consistency assessment satisfy reference-supported labeling, not independent annotation validation. Descriptive outputs make no functional-prediction claim. Phases 3–4 remain gated.

## 1. Architecture
**Phase 3 implementation note (2026-11-16):** `phase3.py` implements provenance-linked evidence curation, verified homology, full-universe transcriptomic baselines and separate marker-proxy integrations. `reports/scoring_spec.md` freezes the heuristic. Unknown mappings/effects remain missing; related papers share a split family. No fitted function-prediction model or independent validation is claimed. Direct T-cell-function ranking remains unavailable.

```text
Public scRNA-seq -> verified registry -> QC/AnnData -> macrophage + T-cell annotations
                                          -> patient-level associations + composition sensitivity
Public perturbation studies -> evidence registry -> context harmonisation
                                      \             /
                                       candidate feature table
                                                |
                              transcriptomic baseline / integrated ranker
                                                |
                         study-held-out benchmark + sensitivity analysis
                                                |
                              reports, tables, tests -> optional Streamlit
```

## 2. Five phases: technical build and testable deliverables

### Phase 1 — Novelty and data feasibility (hard gate)
**Tasks:** (a) review NicheNet, LIANA+, CellChat, scDrugPrio and relevant experimental integration methods; (b) search public repositories and papers for macrophage perturbations with T-cell function readouts; (c) inspect actual file availability, biological units, metadata and outcome definitions; (d) identify an independent test design; (e) record novelty and data gaps.

**Deliver:** `reports/novelty_matrix.md`, `reports/feasibility.md`, `data/registry/datasets.csv`, `data/registry/perturbations.csv`.

**Acceptance:** Every proposed dataset has a verified source and explicit suitability decision; at least one defensible benchmark and train/test separation is documented for GO. Otherwise CONDITIONAL GO/NO-GO, with no claim of predictive feasibility.

### Phase 2 — Transcriptomic evidence baseline
**Tasks:** read verified AnnData/matrix; per-study QC and doublet assessment; reference-supported macrophage/T-cell annotation; fixed signature definitions; patient-level aggregation and association; sensitivity to composition, covariates and batches.

**Deliver:** `notebooks/02_transcriptomics.ipynb`, `results/transcriptomic_candidates.csv`, `reports/transcriptomic_baseline.md`, plots and run configuration.

**Acceptance:** Results reproducible; sample IDs retained; no pseudoreplication; multiple-testing control; state composition denominator and score scale defined; no circular reuse of markers as independent validation.

### Phase 3 — Functional evidence integration
**Tasks:** extract perturbation outcome rows; harmonise gene IDs, organism, perturbation direction, experimental cell type, assay and effect sign; attach DOI/accession; flag direct versus indirect evidence; implement prespecified baseline and interpretable integration model.

**Deliver:** `data/curated/functional_evidence.parquet`, `results/baseline_rankings.csv`, `results/integrated_rankings.csv`, `reports/scoring_spec.md`.

**Acceptance:** Every ranking input traceable; incompatible assays not naively pooled; missing evidence not coded as null effect; held-out outcomes inaccessible to ranking construction.

### Phase 4 — Benchmark and robustness
**Implemented outcome (2026-11-16):** phase4.py, benchmark/leakage reports, explicit missing independent metrics, 300 paired patient-bootstrap draws, 11 omission refits and 45 marker-specific ablation comparisons. Decision INCONCLUSIVE; the existing evidence cannot establish independent predictive performance. Notebook and verification scripts reproduce the descriptive assessment.

**Tasks:** split by independent study/experiment or appropriate biological unit; choose evaluation metric before scoring; compare baselines and integrated method; bootstrap by biological units; ablate evidence types; check sensitivity to signatures, annotations and study exclusions; audit leakage.

**Deliver:** `reports/benchmark.md`, `results/evaluation_metrics.csv`, `reports/leakage_audit.md`, plots and reproducible test configuration.

**Acceptance:** Independent evaluation demonstrably separated; effect estimates and uncertainty reported; failures and negative results documented; if too few studies, report descriptive validation only.

### Phase 5 — Release and optional app
**Implemented outcome (2026-11-16):** Installable CLI wheel/source distribution, complete research ZIP, final report, reproduction guide, per-file integrity manifest and a separately installed clean-copy test. Phases 3–4 reproduced 11 CSV tables and the evidence Parquet; 19 tests passed. Optional viewer and external publication are excluded from this release.

**Tasks:** package CLI/notebooks, pin dependencies, add tests and usage examples; generate research report and reproducibility instructions; optionally create read-only Streamlit pages for datasets, evidence, rankings and benchmarks.

**Deliver:** installable repository, `README.md`, `tests/`, `reports/final_report.md`, optional `app/streamlit_app.py`.

**Acceptance:** A new researcher can reproduce a documented analysis from permissible inputs; no unsupported causal/clinical statements; app displays provenance and caveats.

## 3. Proposed stack
- Python 3.11 (verify package compatibility), Scanpy, AnnData, NumPy, pandas, SciPy, statsmodels, scikit-learn, Matplotlib/Plotly.
- Parquet/CSV for tabular records, H5AD for single-cell matrices, YAML for configuration, pytest for tests, Git for versioning.
- Google Colab for initial development; use a workstation/server if datasets exceed available memory.
- Streamlit **only after** research evaluation.

## 4. Canonical schemas
### `datasets.csv`
`dataset_id,accession,repository,doi,organism,cancer_subtype,tissue,assay,patient_count,sample_count,patient_ids_available,cell_annotations_available,processed_files_url,access_status,eligibility_reason,verified_on`

### `perturbations.csv` / `functional_evidence.parquet`
`evidence_id,doi,accession,gene_id,gene_symbol,perturbation,perturbed_cell_type,organism,experimental_context,assay,outcome,effect_direction,effect_size,effect_unit,uncertainty,biological_n,evidence_tier,compatibility_notes,source_location,split_group`

### `transcriptomic_candidates.csv`
`gene_id,gene_symbol,cohort_id,patient_n,macrophage_programme,t_cell_programme,association_effect,association_se,p_value,fdr,composition_adjusted_effect,model_id`

### `integrated_rankings.csv`
`gene_id,gene_symbol,rank,ranking_value,transcriptomic_evidence,functional_evidence,context_compatibility,rank_stability,source_ids,model_version`

**Rules:** Stable gene identifiers; missing is distinct from zero; no unverified numeric fields; raw records immutable, derived tables versioned.

## 5. Statistical and biological safeguards
- Unit of inference: patient or independent biological sample, not individual cells.
- Macrophage state mean: \(S_i=\sum_k p_{ik}\mu_{ik}\). State proportions \(p\) and within-state means \(\mu\) require comparable definitions; decomposition is descriptive, not causal.
- Use study-aware batch handling; do not erase true condition effects via aggressive integration.
- Separate transcriptional T-cell dysfunction proxies from measured T-cell suppression.
- Evidence tiers: **direct** macrophage perturbation with T-cell functional outcome; **context-relevant** macrophage perturbation with related immune endpoint; **indirect** different cell/species/context; **observational** expression/signalling inference.
- Do not interpret ligand–receptor co-expression as confirmed communication.

## 6. Ranking design
1. Prespecify candidate universe and transcriptomic-only baselines.
2. Build features solely from training/development studies.
3. Start with transparent rank aggregation or regularised statistical models; use complex ML only if independent sample size justifies it.
4. Compare against a relevant established method **only when its required inputs and assumptions are met**.
5. Avoid arbitrarily weighted scores presented as validated confidence or biological truth.
6. Explicitly model missing functional evidence and context mismatch.

## 7. Evaluation design
- **Splitting:** Prefer leave-one-study-out or held-out independent experimental studies; group replicates to avoid contamination.
- **Endpoints:** prespecified direction/magnitude of relevant functional change; avoid combining incomparable assays without a justified model.
- **Metrics:** AUPRC and precision@k for imbalanced binary endpoints; rank correlation for continuous/ranked outcomes; uncertainty via study/biological-unit resampling.
- **Controls:** differential expression, transcriptomic association and simple evidence-integration baselines.
- **Leakage tests:** no target label, derived proxy, overlapping publication or replicate shared across training and held-out evaluation.
- **Ablations:** remove functional evidence; remove composition adjustment; exclude indirect evidence; vary signature/annotation; leave out cohorts.
- **Failure mode:** if independent functional data are insufficient, state that performance cannot be validated.

## 8. Repository layout
```text
oncomyeloid_fx/
  PRD.md  TRD.md  plan.md  README.md
  configs/default.yaml
  data/registry/  data/curated/  data/examples/
  src/oncomyeloid_fx/
    datasets/  transcriptomics/  statistics/
    functional/  ranking/  evaluation/  reporting/
  notebooks/
    01_feasibility.ipynb
    02_transcriptomics.ipynb
    03_evidence.ipynb
    04_ranking.ipynb
    05_benchmark.ipynb
  results/  reports/  tests/
  app/streamlit_app.py   # optional; Phase 5
```

## 9. Automated tests and reproducibility
- Schema validation and accession/provenance checks.
- Synthetic-data tests for composition-only and within-state-only changes.
- Missing-value and assay-compatibility tests.
- Split isolation and leakage detection tests.
- Deterministic fixture for ranking and report generation.
- Lock/pin software dependencies; record random seeds, parameters, input identifiers and run timestamps.

## 10. Decision gates and exclusions
**Phase 1 NO-GO:** No compatible perturbation outcome data or no defensible independent evaluation → do not train a function-prediction model. **Phase 4 inconclusive:** Do not claim superiority or novel biological target validation. **Phase 5:** Website is optional, never a substitute for evidence.
