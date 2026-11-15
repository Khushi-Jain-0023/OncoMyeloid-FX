# OncoMyeloid-FX — Product Requirements Document

**Version:** 1.2 · **Status:** Descriptive research release 0.1.0 complete; independent prediction unvalidated · **Domain:** Lung cancer immunology / functional genomics

**Authorized scope amendment (2026-11-15):** Following the Phase 1 predictive NO-GO, the user explicitly approved Phase 2 as a descriptive transcriptomic study. QC, published-label annotation assessment, patient-level associations and composition/covariate sensitivity are authorized. Phase 2 does not require a predictive GO under this amendment. Phase 3–4 predictive development and validation claims remain gated; the original research thesis below is retained as a future objective.

## 1. Product thesis
**Phase 3 implementation note (2026-11-16):** The user requested Phase 3. Evidence curation and ranking deliverables are implemented as descriptive analyses using the existing indirect/context-related evidence tiers. Downloaded quantitative mouse immune-marker screens support separate exploratory rankings; they do not satisfy the original direct T-cell-function predictive endpoint. Original predictive success criteria and Phase 4 independence requirements are unchanged. Missing eligible evidence is explicitly unranked, not negative.

OncoMyeloid-FX is a research-first, reproducible framework to test whether independent functional perturbation evidence improves prioritisation of macrophage-associated immunoregulatory genes beyond transcriptomic-only methods. It is **not** a clinical decision tool and does **not** claim that transcriptomic associations establish causal immunosuppression.

## 2. Research question and success condition
**Phase 4 outcome (2026-11-16):** Current-data robustness and leakage evaluation are complete. Independent validation is inconclusive because eligible unseen quantitative T-cell-function outcomes are absent. This is not a validated or improved predictive result; future validation requires new data under the original success criteria.

**Question:** Can function-grounded evidence integration predict *held-out, experimentally measured* immune-function effects better than transcriptomic-only candidate rankings?

**Primary success:** A leakage-free, independently evaluated comparison against predefined baselines, with effect sizes and uncertainty. A rigorous negative finding or a documented no-go decision is acceptable; a website alone is not success.

**Blocking dependency:** The existence of sufficiently compatible public macrophage perturbation studies with relevant T-cell functional readouts is **not yet verified**.

## 3. Target users
Computational cancer immunologists, single-cell researchers, functional genomics groups and early-stage target-discovery researchers.

## 4. Scope
**In scope:** Public human lung cancer scRNA-seq; macrophage/T-cell programmes; patient-level association and composition sensitivity; provenance-tracked perturbation evidence; interpretable ranking; held-out benchmarking; reproducible reports; optional Streamlit results viewer.

**Out of scope:** Clinical treatment advice, proof of gene causality from observational data, new drug design, unvalidated immune-suppression predictions, unrestricted uploaded-data processing and a large AI foundation model.

## 5. Five implementable phases and end results

| Phase | Build | Concrete end result / acceptance gate |
|---|---|---|
| **1. Novelty + data feasibility** | Audit relevant methods, publications and repositories; inspect real downloadable files and assay metadata; define endpoint and evaluation splits. | `reports/feasibility.md`, `data/registry/datasets.csv`, `data/registry/perturbations.csv`, `reports/novelty_matrix.md`, and a documented **GO / CONDITIONAL GO / NO-GO** decision. **No model before GO.** |
| **2. Transcriptomic evidence baseline** | Load one verified lung cancer scRNA-seq cohort; QC, annotate macrophages/T cells; define non-circular signatures; compute patient-level associations and composition sensitivity. | Reproducible notebook/pipeline, processed data references, `results/transcriptomic_candidates.csv`, QC and association plots, `reports/transcriptomic_baseline.md`. Every result traceable to samples and settings. |
| **3. Functional evidence + candidate ranking** | Curate assay-level perturbation outcomes; harmonise genes, contexts and directions; implement transcriptomic-only and interpretable evidence-integration rankings. | `data/curated/functional_evidence.parquet`, `results/baseline_rankings.csv`, `results/integrated_rankings.csv`, evidence provenance and scoring specification. Missing evidence explicitly marked, not scored as negative. |
| **4. Independent benchmarking + robustness** | Hold out studies/experimental units; compare rankings on unseen functional endpoints; test patient/study/annotation/signature sensitivity and leakage. | `reports/benchmark.md`, metrics with confidence intervals, robustness figures, failure cases and **validated / inconclusive / not improved** decision. No superiority claim without evidence. |
| **5. Research release + optional interface** | Package pipeline, tests, reproducibility instructions, report exports and optionally a Streamlit read-only explorer of verified results. | Versioned repository, `README.md`, environment lock/requirements, tests, reproducibility walkthrough, final scientific report; optional working app. Interface must show limitations and evidence provenance. |

**Dependencies:** Phase 1 gates Phase 2–4. Phase 3 requires eligible functional data. Phase 4 requires independent evaluation units. Phase 5 must not disguise inconclusive findings.

## 6. Functional requirements
- **FR-01:** Register datasets with accession, DOI, organism, tissue, cell types, patient IDs, assay, files, permissions and suitability.
- **FR-02:** Validate sample metadata and QC single-cell data without universal hard-coded thresholds.
- **FR-03:** Characterise macrophage states using multi-gene or reference-supported annotations; avoid assigning function from a marker alone.
- **FR-04:** Quantify predefined T-cell programmes; distinguish signature scores from measured functional impairment.
- **FR-05:** Analyse macrophage–T-cell associations at patient/sample level, with appropriate covariates and multiple-testing correction.
- **FR-06:** Assess macrophage-state composition versus within-state expression using comparable state definitions and score scales.
- **FR-07:** Curate perturbation records with gene, perturbed cell, organism, assay, outcome, effect, uncertainty, sample size and citation.
- **FR-08:** Grade evidence by biological context compatibility; do not treat T-cell-only perturbations as direct macrophage evidence.
- **FR-09:** Generate transparent transcriptomic-only and integrated candidate rankings.
- **FR-10:** Evaluate on evidence excluded from model development and feature construction.
- **FR-11:** Report ranking stability, cohort transfer, negative results and missing-data sensitivity.
- **FR-12:** Export tables, plots, methods and provenance; optional interactive results browsing.

## 7. Quality and scientific requirements
- **Reproducible:** versioned configuration, code, seeds where relevant, dataset checksums or stable accessions.
- **Leakage-resistant:** study-level or biological-unit splits; no evaluation outcome reused as a feature for that evaluation.
- **Interpretable:** candidate rank decomposed into documented evidence contributions; do not invent confidence probabilities.
- **Privacy-conscious:** use permitted public data; do not expose identifiable or controlled-access patient records.
- **Robust:** explicitly handle batch effects, sample imbalance, missing states, incompatible assays and multiple testing.

## 8. Evaluation
**Primary endpoint:** Recovery/ranking of held-out perturbations with a prespecified, biologically relevant functional readout. Depending on label structure: AUPRC, precision@k or rank correlation, with confidence intervals; use ROC-AUC only when suitable. Compare against differential expression, transcriptomic association, and compatible existing prioritisation approaches. Report study-level generalisation and uncertainty. If data cannot support an independent endpoint, do not claim validated predictive performance.

## 9. Risks and stop rules
1. **No suitable functional datasets:** stop function-grounded prediction; document a no-go or re-scope as a descriptive study.
2. **Existing method fully covers proposed contribution:** refine research question and benchmark rather than relabel integration as novelty.
3. **Too few independent experiments:** do not train an overparameterised ML model or report inflated accuracy.
4. **Cross-species / assay mismatch:** stratify, downgrade evidence or exclude.
5. **Confounded observational associations:** report associations only, never causal claims.

## 10. Release definition
The minimum research product is a verified dataset/evidence registry, reproducible analysis, baseline and integrated rankings, leakage-free evaluation where feasible, and a limitations-rich report. The web interface is optional and last.
