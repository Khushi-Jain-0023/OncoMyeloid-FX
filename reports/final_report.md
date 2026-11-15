# OncoMyeloid-FX — final research report

Release 0.1.0 · 2026-11-16 · Descriptive research release

## Conclusion

The project produced a reproducible study of macrophage/T-cell expression associations and exploratory integration with mouse macrophage immune-marker screens. It did **not** establish a validated functional predictor, improved target prioritization, gene causality, or clinical utility. The independent-validation decision is **inconclusive**, because no eligible unseen quantitative T-cell-function outcomes were available in the curated inventory.

This is a completed current-data research release, including negative results, missing evidence, uncertainty and reopening requirements. Completion of the software does not remove the scientific evidence limitations.

## Question and feasibility

The original question was whether independent functional perturbation evidence improves gene prioritization beyond transcriptomic evidence. Phase 1 audited relevant methods and public evidence. Novelty and an independent benchmark were not established, leading to NO-GO for predictive development. The user then authorized a descriptive transcriptomic study. Subsequent phases retained this boundary and separated mouse immune-marker effects from T-cell functional outcomes.

## Human transcriptomic analysis

The [GSE131907 study](https://doi.org/10.1038/s41467-020-16164-1) supplied 11 primary lung-tumor patients. The parsed cohort contained 45,149 deposited cells; 44,984 were retained after QC and the doublet screen. Published annotations were checked for marker consistency on the same data, which is not independent annotation validation.

Macrophage expression and predefined T-cell inhibitory-expression scores were summarized at patient level. Cells were not treated as independent biological replicates. Standardized OLS with HC3 uncertainty and BH correction tested 6,124 eligible macrophage genes. **Zero primary associations passed 5% FDR.** The composition-adjusted analysis produced one significant secondary association, C3AR1, whose primary FDR was approximately 1; this model dependence is not validation. Nine sensitivities addressed covariates, cell selection, annotations and alternative T-cell endpoints. Sex-adjusted HC3 estimates were unestimable in the single-female design and remained missing.

The expression score is an analyst-defined proxy, not measured T-cell suppression. Single-cohort design, 11 patients, mixed T-cell states, sparse/absent macrophage states and capture/patient confounding limit interpretation. Protocol, signatures, source hashes and complete outputs are retained.

## Perturbation evidence and rankings

The [eLife 65109 source data](https://elifesciences.org/articles/65109/figures) provide 11,701 tested mouse genes across MHCII, CD40 and PD-L1 surface-expression screens: 35,103 quantitative records. These are indirect immune-marker endpoints from non-tumor mouse macrophages, not quantitative T-cell-function outcomes. Six earlier functional leads remain qualitative, with numeric effects absent. Related 65109/65110 papers share a development family rather than constituting independent validation.

[MGI/Alliance homology](https://www.informatics.jax.org/homology.shtml) and HGNC snapshots support conservative stable-ID mapping. Ambiguous mappings were excluded. Each marker-specific integration covers 5,155 human candidates; 969 of the 6,124 transcriptomic candidates have no eligible mapped integration evidence. Unknown evidence is not scored as a negative result.

The transparent heuristic averages within-universe percentiles of transcriptomic association evidence and absolute marker-selection contrast. Equal weighting is not fitted or calibrated confidence. Marker endpoints remain separate; a high rank has no therapeutic direction. Baseline ranks, both feature contributions, source IDs, original statistics and scoring rules are exported.

## Robustness and independent evaluation

Phase 4 completed 300 paired patient-bootstrap draws, 11 patient-omission refits and 45 marker-specific ablation comparisons. Removing one patient retained only 9–17 of the original top 20 candidates. The leading full-data candidates remained in the bootstrap top 20 in approximately 40% (CD40), 64% (MHCII) and 72% (PD-L1) of draws. Rank ranges were broad; high full-data ranks are not uniformly stable.

The bootstrap holds mouse assays, annotation, orthology and candidate selection fixed. Its central 95% ranges describe patient-resampling variability and are not calibrated population confidence intervals or functional-performance intervals. Removing indirect evidence or the only development family leaves no integrated ranking. Changing T-cell endpoints is sensitivity analysis, not independent replication.

The audit verified source membership, endpoint matching, family grouping, partition isolation and prior hashes. Mutation tests reject use of excluded outcomes. No random gene split, pseudo-negative labeling or in-sample correlation was used as predictive accuracy. AUPRC, precision@20, held-out effect correlation and performance confidence intervals remain explicitly missing, with reasons. Neither superiority nor failure to improve was demonstrated.

## Release and reproduction

The release includes an installable, dependency-free command runner plus the accompanying scientific scripts, pinned analysis dependencies, executed notebooks, source snapshots, derived tables, plots and provenance manifests. The wheel alone does not contain the research dataset; use the complete research ZIP. The optional web interface is not part of version 0.1.0.

Read reports/reproducibility.md for a clean environment setup, integrity verification, phase reruns and the distinction between immutable release files and mutable working copies. Tests cover statistical correctness against statsmodels, missingness, composition simulation, mapping, leakage, resampling and release integrity. reports/release_validation.md records the installation and clean-copy verification results. No API keys are needed for the bundled-data workflows. GitHub publication is deferred; this is a local release.

## What would justify reopening prediction

New studies must provide compatible quantitative T-cell functional outcomes after macrophage gene perturbation, controls, stable gene mapping and identifiable independent biological units. Test families must be independent of development and previously inspected evidence. A new protocol must freeze endpoints, splits, metrics, missingness handling and biological-unit uncertainty before test outcomes are inspected. Additional human cohorts are needed to evaluate transfer. The existing marker screens cannot stand in for these requirements.
