# OncoMyeloid-FX — Living Implementation Plan

**Updated:** 2026-11-16
**Overall status:** All five phases of the current-data descriptive research release are complete (version 0.1.0). Independent functional validation remains INCONCLUSIVE; the original predictive objective is not established.
**Maintenance rule:** Exactly two top-level sections. Completed verified work belongs in Section 1; pending work and decisions in Section 2.

## 1. What has been done till now

- [x] Authored PRD/TRD and five-phase plan with biological replication and leakage safeguards.
- [x] Completed targeted novelty review of NicheNet, LIANA+, CellChat, scDrugPrio, CellOracle and functional drug screening. Novelty not demonstrated.
- [x] Downloaded and parsed GSE131907 cell annotations and sample workbook: 208506 unique cells, 58 samples, 44 explicit patients; 11 primary tumor patients with macrophages and T cells. Verified UMI endpoint access.
- [x] Documented functional evidence, publication-family dependence, context mismatch and source-data access limitations.
- [x] Created dataset registry and six qualitative gene-perturbation lead records. Missing IDs/numbers remain explicitly unresolved and ineligible for ranking.
- [x] Assessed independent benchmark feasibility and wrote a conditional protocol.
- [x] Recorded NO-GO decision, reasoning and reopening conditions.

Deliverables: reports/feasibility.md, reports/novelty_matrix.md, reports/file_verification.md, reports/functional_audit.md, reports/benchmark_design.md, reports/search_log.md, data/registry/datasets.csv, data/registry/perturbations.csv and registry README. Metadata audit scripts and downloaded source materials are in work/.

- [x] Completed Phase 2 on 11 primary-tumor patients: 45,149 source cells, 44,984 retained, 6,124 eligible genes.
- [x] Installed an isolated Python runtime, parsed and hashed the full matrix, reconciled metadata, assessed QC/doublets and inspected annotation-marker consistency.
- [x] Completed patient-level HC3 models, BH correction, composition/within-state analyses, nine sensitivities and leave-one-patient-out effects.
- [x] Produced report, candidate tables, four visually checked figures, executed notebook, dependency lock and provenance manifest.
- [x] Passed four statistical tests and real-output verification (11 patients, 6,124 genes, 55,116 sensitivity rows). Read back the QC-annotated count file successfully.

Phase 2 deliverables: reports/transcriptomic_baseline.md, reports/phase2_protocol.md, notebooks/02_transcriptomics.ipynb, results/, configs/phase2.json, phase2.py, tests/, requirements-lock.txt and README.md. Primary FDR <0.05: zero genes. Secondary associations do not establish functional validation. No website or predictive benchmark was implemented.

- [x] Curated 35,103 quantitative mouse marker-screen records and preserved six qualitative T-cell-function leads separately.
- [x] Applied conservative MGI/HGNC mapping; exported 6,124 baseline candidates and three endpoint-specific integrations with 5,155 ranked genes each, leaving 969 unknown in each stratum.
- [x] Implemented study-family isolation, missingness checks, source-control checks, weight sensitivity and reproducible provenance. Executed the Phase 3 notebook and inspected its figure.

Phase 3 deliverables: phase3.py, data/curated/functional_evidence.parquet, results/baseline_rankings.csv, results/integrated_rankings.csv, reports/scoring_spec.md, reports/phase3_evidence_ranking.md, notebooks/03_evidence_ranking.ipynb and results/phase3_verification.json. The original direct functional endpoint remains unavailable; these are descriptive marker-proxy results.

- [x] Completed Phase 4 with 300 paired patient-bootstrap samples, 11 patient-omission refits, 45 marker-specific ablation comparisons, failure cases and two inspected robustness figures.
- [x] Audited evidence families, source IDs, partitions, endpoint consistency and Phase 3 hashes. Independent quantitative T-cell-function test outcomes: zero.
- [x] Reported missing independent metrics explicitly; decision INCONCLUSIVE. Completed the benchmark/leakage reports, notebook, verification receipt and statistical/leakage tests (16 tests passed across phases).

Phase 4 deliverables: phase4.py, configs/phase4.json, reports/phase4_protocol.md, reports/benchmark.md, reports/leakage_audit.md, results/evaluation_metrics.csv, results/phase4_*, and notebooks/04_benchmark_robustness.ipynb. No independent validation or superiority was established.

- [x] Completed Phase 5: installable CLI wheel/source distribution, final scientific report, reproducibility walkthrough, source attribution, release builder and SHA256 integrity checks.
- [x] Installed into a separate Python 3.11.9 virtual environment; all 87 analysis pins matched. Fresh extracted-copy Phases 3–4 and notebooks completed; 19 tests passed before and after reruns.
- [x] Verified numerical equivalence of 11 CSV outputs and the evidence Parquet against the reference. Preserved the tested archive hash and command receipts.
- [x] Prepared local versioned research release 0.1.0. GitHub publication remains deferred; optional website is outside this release.

Phase 5 deliverables: pyproject.toml, src/oncomyeloid_fx/, dist/ wheel and source archive, reports/final_report.md, reports/reproducibility.md, reports/release_validation.md, results/phase5_verification.json, build_release.py, smoke_release.py and complete research ZIP with integrity manifest.

## 2. What is left / updates to the plan

### Phase 2 — COMPLETE
The user authorized descriptive analysis; PRD/TRD record the scope amendment. No required Phase 2 work remains. Functional data acquisition is a separate reopening task; no author outreach was sent.

### Phase 3 — DESCRIPTIVE DELIVERABLES COMPLETE; DIRECT ENDPOINT UNAVAILABLE
- Quantitative mouse immune-marker evidence is curated separately from qualitative T-cell-function leads. These related endpoints do not meet the original direct functional objective.
- Source data, baseline ranks, marker-stratified integrated ranks, scoring specification, executed notebook and audit tests are delivered.
- Reopening the predictive objective still requires compatible numeric T-cell-function outcomes and independent study families; no marker-to-function substitution is permitted.

### Phase 4 — COMPLETE WITH INCONCLUSIVE DECISION
- Current-data evaluation, patient-resampling uncertainty, ablations, leakage audit and failure cases are complete.
- Independent performance is not estimable; the original validation objective requires new compatible, previously unseen quantitative functional evidence. This is a scientific reopening dependency, not an unreported successful benchmark.

### Phase 5 — COMPLETE
The required research release, installation/reproduction checks and final report are complete. The optional web interface and external publication are not part of version 0.1.0. No required release work remains.

### Blockers and decisions
- B1: Quantitative compatible gene-level functional inventory is insufficient for prediction.
- B2: Methodological novelty is not established.
- B3: No defensible independent predictive benchmark verified.
- D1: NO-GO remains for predictive development; the authorized descriptive Phase 2 is complete.
- D2: System Python alias remains unused; isolated Python 3.11.9 and pinned dependencies run the analysis successfully.

### Change log
| Date | Change | Status |
|---|---|---|
| 2026-11-15 | Established requirements and five gated phases | Complete |
| 2026-11-15 | Verified annotation/patient metadata; documented evidence and novelty audit | Complete |
| 2026-11-15 | Closed Phase 1 with NO-GO and explicit reopening criteria | Complete |
| 2026-11-15 | Authorized descriptive scope; completed and verified Phase 2 | Complete |
| 2026-11-16 | Curated quantitative marker screens; completed descriptive Phase 3 rankings, provenance and checks | Complete with explicit direct-endpoint limitation |
| 2026-11-16 | Completed Phase 4 robustness and leakage audit; independent functional validation inconclusive | Complete with explicit evidence limitation |
| 2026-11-16 | Released local version 0.1.0 with installable CLI, final report and clean-copy numerical reproduction | Complete |
