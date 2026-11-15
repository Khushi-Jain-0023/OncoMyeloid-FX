# Phase 4 protocol — 2026-11-16

Frozen before Phase 4 computation. Phase 3 outputs are development results already inspected; nothing here converts them into an independent test set. User requested completion of Phase 4; acceptance is a documented inconclusive decision when independent evidence is insufficient.

## Independent evaluation gate

The intended endpoint is a quantitatively measured T-cell functional outcome following macrophage gene perturbation, with compatible context, defined biological units, verified stable mapping, and a study family not used in development or previously inspected for tuning. Audit the curated inventory and every integrated source ID. Related eLife 65109/65110 papers remain one family. Three markers and thousands of genes do not constitute independent studies. Marelli qualitative rows have no numeric outcomes and were already inspected; they are not a pristine holdout.

When no eligible independent endpoint exists, AUPRC, precision@20, rank correlation and their confidence intervals are **not estimable**, represented by missing values with reasons in evaluation_metrics.csv. No study bootstrap, random gene split, pseudo-negatives, marker-as-T-function evaluation, or superiority claim. The decision is **inconclusive**, not validated and not evidence of no improvement. Cross-cohort transfer is unavailable with only one transcriptomic cohort. Differential-expression and ligand-method predictive comparisons are unavailable without a specified valid contrast/compatible endpoint; do not substitute them silently.

## Descriptive robustness

Keep the 6,124-gene candidate universe fixed. Use the 5,155 mapped genes in each Phase 3 endpoint as the reference integration universe. Recompute the original standardized OLS/HC3 association p-values from paired patient expression and T-cell scores; compare to saved Phase 2 results before resampling. An independently tested vectorized closed form is used for unadjusted models. No cell-level resampling.

1. Leave each of 11 patients out and refit; recompute transcriptomic percentile features and the same 0.5/0.5 integration for each marker. Export rank correlation and top-20 overlap against the full cohort.
2. Draw 300 paired patient bootstrap samples of size 11 with replacement using seed 20261116. Preserve patient pairings and log sampled IDs/unique patient count. Refit associations, recompute ranks, and report per-gene 2.5/50/97.5 percentile rank ranges and top-20 selection frequency, plus effect quantiles. These are **exploratory resampling ranges**, not calibrated population CIs or functional-performance intervals. Report valid replicate counts; degenerate fits remain missing. Source cohort selection, annotation uncertainty, mouse assays and orthology are held fixed and are not covered by these ranges. The small cohort makes tail estimates uncertain.
3. Compare transcriptomic-only and marker-only scores on the same matched universe; compare composition-adjusted and within-state p-values and all nine saved Phase 2 sensitivities. Cytotoxicity is a different endpoint and CD8 is a restricted endpoint, not interchangeable replication. Sex adjustment is unestimable with this design and must stay missing.
4. Exclude indirect evidence and leave the sole development family out: integration becomes unavailable. Do not silently revert to a baseline and label it integrated.

Rank agreement is Spearman correlation of scores on their finite common gene set; top-20 overlap uses exactly 20 genes, breaking score ties lexically by original gene symbol. Also report common/available counts and maximum finite rank changes on the common universe. Recompute percentile denominators when a model has missing estimates; report that this conditions comparisons on measurable genes. Scores round to 12 decimals before rank assignment. No weights or signatures are selected based on these checks.

## Leakage audit and failure cases

Check DOI-family consistency, development/excluded partitions, source-ID membership, endpoint matching, unique per-endpoint human IDs, absence of excluded-family source IDs, and hashes against Phase 3 verification. Mutate excluded outcomes in tests and require identical ranks. Mark in-sample correlation with the marker feature as circular and refuse to interpret it as accuracy. Summarize genes with the largest leave-one-patient-out rank movements, unstable top-20 membership, missing evidence and annotation/composition dependence. The report must include limitations and the exact reopening requirements.
