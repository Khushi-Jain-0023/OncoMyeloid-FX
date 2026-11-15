# File verification — 2026-11-15

Downloaded and parsed https://ftp.ncbi.nlm.nih.gov/geo/series/GSE131nnn/GSE131907/suppl/GSE131907_Lung_Cancer_cell_annotation.txt.gz

Local copy: `work/GSE131907_cell_annotation.txt.gz`. SHA256: `9D017652A31A489C1F62CACC436936D48A5B07BB554FC0DBE602DA7474532205`.

Verified 208506 rows, 208506 unique cell IDs and 58 sample IDs. Seven columns: Index, Barcode, Sample, Sample_Origin, Cell_type, Cell_type.refined, Cell_subtype. No explicit patient-ID column; do not infer patient identity from sample suffixes without supporting metadata.

Eleven LUNG_T samples contain 45149 cells. Each has annotated macrophages (142–1153 per sample) and T lymphocytes (310–3585). Labels are published annotations, not independent validation of biological function. Reproduce with `pwsh -File work/audit_annotations.ps1`.

UMI archive HEAD returned HTTP 200 and Content-Length 408736818 bytes at https://ftp.ncbi.nlm.nih.gov/geo/series/GSE131nnn/GSE131907/suppl/GSE131907_Lung_Cancer_raw_UMI_matrix.txt.gz . Matrix contents are not yet downloaded or validated.

## Completed patient mapping

Downloaded `GSE131907_Lung_Cancer_Feature_Summary.xlsx` from the same GEO supplementary directory as the annotation. Local copy: work/sample_metadata.xlsx; SHA256 27BEC6D22D2658E5CCCAB2BDD463E7B4E4BA342F795BDEB07FDB3F68084FF8E4. Parsed explicit Patient id, Samples, Tissue origins, Histology and cell-count fields: 58 samples, 44 patients, 208506 cells. Eleven LUNG_T samples have 11 distinct patients. Two are annotated ADC(Double), requiring a sensitivity exclusion in later analysis. Ten LUNG_T patients have matching normal-lung samples; these pairs must remain grouped by patient.

Reproduce mapping with `pwsh -File work/read_metadata.ps1`. Patient mapping is now verified, superseding the earlier annotation-only limitation above.

Environment at Phase 1: default python was an inaccessible WindowsApps alias and the launcher had no installed interpreter. This limitation is superseded by the isolated Phase 2 runtime below.

## Phase 2 completion verification

The full 408,736,818-byte UMI archive was downloaded and completely parsed with gzip integrity checking. SHA256: b44a9c6635d0b59ec66b5eb6b40b40e7292c3a75aaf8afc4f933eb0550a26372. This supersedes the earlier endpoint-only check. The sparse primary cohort contains 45,149 cells and 29,634 genes. The QC-annotated H5AD retains all source rows with QC flags; downstream analyses use 44,984 retained cells.

Isolated Python 3.11.9 runs from work/python-runtime/python.exe, with dependency versions frozen in requirements-lock.txt. The executed notebook, four statistical tests, output verification receipt and read-back of the QC H5AD establish the completed Phase 2 artifacts. See results/verification.json and results/run_manifest.json. All four figures were visually inspected.
