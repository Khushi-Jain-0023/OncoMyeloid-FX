# Phase 3 scoring specification

Frozen before producing rankings, 2026-11-16. Scope: descriptive evidence integration, not training or validation of a T-cell-function predictor. The user requested Phase 3 implementation; the Phase 1 predictive NO-GO remains in force.

## Evidence and endpoints

The downloaded [eLife 65109 Figure 1 source workbook](https://cdn.elifesciences.org/articles/65109/elife-65109-fig1-data1-v2.xlsx) reports 11,701 mouse genes from macrophage knockout screens. MHCII, CD40 and PD-L1 surface-expression endpoints remain three separate strata. These are perturbed immune-marker outcomes, **not measured T-cell activation, proliferation or suppression**. Mouse immortalized macrophages under IFN-gamma stimulation are indirect evidence for human lung tumors. No direct human functional ranking is available from these data.

Retain the six earlier T-cell-function leads with qualitative directions and missing numeric effects. Do not digitize plots or invent uncertainty, biological replicate counts or zero effects. Source workbook screen selections are duplicated; guides and selections are not independent patients. Store two screen replicates separately from biological_n, which remains unknown at donor level.

## Harmonization and provenance

Read Sheet1 row 13 as column headers; data start at Excel row 14. Each record carries DOI, publication family, source filename, sheet and row. Preserve source high/low beta, permutation p/FDR and Wald p/FDR. Verify the summative effect equals beta_high minus beta_low. This selection contrast describes KO enrichment toward high expression when positive, low expression when negative; it is not an expression fold change. No combined p-value or CI is inferred from component tests. No favorable therapeutic direction is assigned.

Use [MGI/Alliance homology classes](https://www.informatics.jax.org/homology.shtml), accepting only classes with exactly one mouse and one human gene, unique mouse mapping, and a valid HGNC ID. Preserve mouse MGI ID separately from human HGNC ID. Ambiguous or absent mappings stay unresolved. Resolve human transcriptomic source symbols by exact approved HGNC symbol, then unique previous/alias symbol only; ambiguous mappings and collisions remain unranked for integration. Do not uppercase mouse symbols to infer orthology. All source snapshots are hashed.

## Baselines

The candidate universe is the unchanged 6,124 Phase 2 genes. Export distinct ranks for primary association p ascending, absolute standardized effect descending, and composition-adjusted p ascending, along with effect signs and FDR. These prioritize strength of observational evidence, not suppression direction. Ties receive minimum rank, with lexical ordering for display only. Unresolved stable IDs do not prevent baseline ranking.

## Exploratory marker integration

Within each marker stratum, restrict to candidates with unique one-to-one mapping and measured development-screen evidence. Compute average-tie percentile ranks in that **same complete-case universe**:

- T = percentile rank of minus log10(primary association p).
- F = percentile rank of absolute marker selection contrast.
- ranking_value = 0.5 T + 0.5 F, ranked descending.

Scores are rounded to 12 decimal places before assigning ranks, including weight sensitivities. This numerical tie tolerance prevents floating-point serialization from breaking mathematically equal rank sums; it was added during export verification, without optimizing biological results.

The equal weight is an explicit heuristic, not fitted or validated confidence. Preserve raw effects, source tests, transcriptomic FDR, evidence IDs, cohort size, endpoint, context tier and LOO sign consistency. Do not label LOO sign consistency as a rank confidence interval. Rank sensitivity at transcriptomic weights 0.25 and 0.75 is reported without choosing the best-looking result. All measured effects, including weak/zero estimates, remain eligible; no hit-selection filter. Missing functional evidence receives missing score/rank, not a zero contribution. Baseline ranks remain available for these genes. Integrated ranks cannot be compared across endpoints or to full-universe baseline ranks without noting different denominators.

## Leakage and limits

Only kiritsy_olive_2021 is a development family. Related eLife 65109/65110 papers share this family and cannot be independent train/test studies. Marelli records are excluded from construction; prior inspection means they are not a pristine held-out validation set. Filter by family before mapping/aggregation/ranking. Tests change excluded outcomes and verify unchanged rankings. No outcome-based weight fitting or validation metrics are produced. A future benchmark needs new compatible independent evidence, grouped biological units and a separately frozen endpoint.

The original direct T-cell-function objective remains unavailable. Phase 3 delivers curation, explicit exclusions, baseline rankings and exploratory marker-stratified integration; it does not reopen predictive GO.
