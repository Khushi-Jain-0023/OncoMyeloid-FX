# Functional audit — 2026-11-15

Qualitative findings only; numerical outcomes not extracted.

| Source | Functional assay | Suitability |
|---|---|---|
| [eLife 65110](https://doi.org/10.7554/eLife.65110), Fig 6 | Macrophage Gsk3b/Med16 loss reduces antigen-specific CD4 IFN-gamma response; Gsk3a alone did not inhibit the reported response | Infection-antigen context; retain as lead; distinguish single and combined interventions. |
| [eLife 65109](https://doi.org/10.7554/eLife.65109), Fig 7D/E | Ndufa1-deficient macrophages mixed with controls; CD4 IFN-gamma response | Source reports biological triplicates and two experiments; neither mixing ratios nor wells are independent studies. |
| [Marelli 2025](https://doi.org/10.1038/s41590-025-02191-x), Fig 3h | Olfr644 or Vmn2r29 perturbation removes impairment of CD8 proliferation | Cancer-relevant lead; numerical tables and human orthology unverified. |

Conservatively group both 2021 papers as `kiritsy_olive_2021` for split planning: shared authors, co-submission and macrophage resources are documented in 65109. Distinct DOIs do not establish independent evaluation.

Genome-wide marker screens are not genome-wide T-cell-function screens. Selected follow-up genes create selection bias; untested genes cannot be negative labels. Keep CD4 activation and CD8 proliferation separate. Do not substitute marker expression or tumor size for either endpoint.

[Zenodo 15309075](https://zenodo.org/records/15309075) has restricted files and describes prostate scRNA-seq/spatial data, not the functional assay table. Publisher functional source data must be checked separately. Some full-text endpoints returned browser challenges; indexed publisher evidence establishes leads but does not verify numerical file access.

## Completed feasibility assessment

Both linked Marelli Zenodo records (15309075 and 10908256) restrict files. Downloaded full-text XML confirms Figure 3h is CD8 division count with biological replicates; its source-data inventory lists CRISPR screen tables and blots, not an identified numerical Figure 3h table. Do not confuse a marker screen with functional follow-up. The publisher screening-table download failed DNS; file content is unverified.

[PMID 39181134](https://pubmed.ncbi.nlm.nih.gov/39181134/) describes a 1430-drug co-culture screen. The paper lists raw luminescence in Table S2 and T-cell-only follow-up in S4, despite a generic on-request data statement. It is a useful drug-level lead but not a macrophage-specific gene screen; compounds contact mixed cultures and can have multiple targets. Numerical supplement content was not downloaded in this audit.

[La Fleur et al.](https://doi.org/10.1158/0008-5472.CAN-20-1885) supplies human lung context for MARCO/IL37R antibody interventions. IL37 knockout in tumor cells must not be relabeled as macrophage perturbation. A broad numerical benchmark was not verified.

Decision: NO-GO for predictive development on the reviewed inventory. This closes Phase 1 with documented evidence limitations; it does not assert that suitable data cannot be obtained. Reopening criteria and conditional split design are in feasibility.md and benchmark_design.md.

## Phase 3 update — 2026-11-16

Downloaded and parsed the eLife 65109 Figure 1 source workbook: 11,701 mouse genes with three marker endpoints, producing 35,103 quantitative records. This establishes numeric immune-marker evidence, not numeric T-cell-function evidence. Original high/low selection statistics and sheet-row provenance are preserved in functional_evidence.parquet. MGI/Alliance homology and HGNC snapshots support conservative human mapping. The six earlier T-cell-function leads retain missing numeric effects. No figure values were guessed or digitized.

MHCII, CD40 and PD-L1 remain separate descriptive ranking strata. All quantitative rows belong to kiritsy_olive_2021, so there is still no independent functional benchmark. See scoring_spec.md and phase3_evidence_ranking.md for the implemented scope and limitations.
