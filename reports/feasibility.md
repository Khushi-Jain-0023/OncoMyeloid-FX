# Phase 1 feasibility decision

2026-11-15. Phase 1 audit complete. **NO-GO for predictive development with the currently verified evidence.**

This decision applies to the reviewed inventory, not all potentially existing data. The targeted public-source search did not establish a compatible independent gene-level functional benchmark. A documented no-go is an accepted Phase 1 outcome under PRD/TRD.

## Findings
- GSE131907 annotations and feature workbook were downloaded and parsed: 208506 cells, 58 samples, 44 explicit patient IDs. Eleven primary lung-tumor samples represent 11 patients with both macrophages and T cells. The UMI endpoint returned HTTP 200; matrix contents remain unvalidated.
- The two 2021 macrophage studies provide CD4 functional follow-up but share experimental lineage. Their genome-wide screens measure surface markers; selected functional follow-up is not an unbiased genome-wide benchmark.
- Marelli 2025 provides a separate family with sparse mouse CD8 proliferation follow-up. Both linked Zenodo records restrict files. Supplement inventory was inspected; publisher screening-table download failed DNS resolution. This is an access limitation, not proof that data are absent.
- Human lung MARCO/IL37R experiments are relevant leads, but no broad independent gene benchmark was verified. Tumor-cell IL37 knockout is not macrophage-specific perturbation.
- A 1430-compound macrophage/T-cell screen lists public raw supplementary tables. Its generic on-request statement does not negate those supplements. Mixed-culture drug exposure, multiple targets and surrogate luminescence prevent treating compounds as macrophage gene knockouts.

## Gate
Transcriptomic metadata feasibility passes. Relevant functional experiments exist. Compatible independent evaluation, an unbiased tested gene universe and methodological novelty are not established. Therefore predictive GO fails.

## Next decision
Do not train or claim validated function prediction. A descriptive patient-level analysis with curated evidence is a plausible fallback, requiring an explicit scope decision and revised requirements. Phase 2–4 remain gated.

Reopen when accessible assay-level data establish independent publication families, compatible endpoints, tested genes and controls, biological replicate identifiers, gene mapping and a prespecified evaluation. Two families are necessary for a train/test distinction but not automatically sufficient for reliable inference.

See file_verification.md, functional_audit.md, novelty_matrix.md, benchmark_design.md, search_log.md and registries. No ranking or predictive performance has been produced.
