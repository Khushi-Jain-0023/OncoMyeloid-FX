# Phase 3: functional evidence and descriptive ranking

Descriptive implementation complete. The original human T-cell-function prediction objective remains unavailable; predictive NO-GO is unchanged.

Curated 35,103 quantitative marker records for 11,701 mouse genes, plus 6 qualitative T-cell-function leads.
All three marker screens belong to one development publication family. Related publications are not independent validation.

## Coverage
| Endpoint | Candidate genes | Ranked with proxy evidence | Missing eligible evidence |
|---|---:|---:|---:|
| CD40 | 6124 | 5155 | 969 |
| MHCII | 6124 | 5155 | 969 |
| PDL1 | 6124 | 5155 | 969 |

## Interpretation
Integrated scores combine observational association strength with absolute mouse marker-screen selection contrasts, separately by endpoint. They do not predict suppression direction, clinical benefit, causality or T-cell-function effect size. No primary Phase 2 association passed 5% FDR.
The source workbook provides component test statistics, not uncertainty for the high-minus-low contrast; no combined significance is invented. Missing numeric T-cell effects stay missing. Missing/ambiguous orthology excludes integration but preserves the transcriptomic baseline.

## Leading exploratory results

### CD40
| Source human symbol | Rank | Score | Mouse marker contrast | Primary transcriptomic FDR |
|---|---:|---:|---:|---:|
| SPTY2D1 | 1 | 0.990 | 1.481 | 0.989 |
| UROD | 2 | 0.987 | 1.585 | 0.989 |
| EGR2 | 3 | 0.987 | -1.293 | 0.989 |
| MESDC2 | 4 | 0.981 | 1.211 | 0.989 |
| THAP4 | 5 | 0.981 | -1.169 | 0.989 |
| TBC1D4 | 6 | 0.978 | 1.066 | 0.425 |
| ECSIT | 7 | 0.972 | -1.138 | 0.989 |
| KIFC3 | 8 | 0.971 | 0.964 | 0.261 |
| GART | 9 | 0.968 | 2.099 | 1.000 |
| QRICH1 | 10 | 0.964 | 1.975 | 1.000 |

### MHCII
| Source human symbol | Rank | Score | Mouse marker contrast | Primary transcriptomic FDR |
|---|---:|---:|---:|---:|
| EIF3F | 1 | 0.996 | -1.921 | 0.425 |
| USP5 | 2 | 0.994 | 1.857 | 0.864 |
| DHX36 | 3 | 0.984 | -1.602 | 0.989 |
| GLTSCR2 | 4 | 0.982 | -1.249 | 0.069 |
| GSK3B | 5 | 0.980 | -1.275 | 0.873 |
| GCH1 | 6 | 0.979 | 1.480 | 0.989 |
| DHPS | 7 | 0.977 | -2.079 | 1.000 |
| RFWD2 | 8 | 0.973 | -1.654 | 1.000 |
| PAF1 | 9 | 0.973 | 1.290 | 0.989 |
| SF3A2 | 10 | 0.972 | 1.458 | 1.000 |

### PDL1
| Source human symbol | Rank | Score | Mouse marker contrast | Primary transcriptomic FDR |
|---|---:|---:|---:|---:|
| MAT2A | 1 | 0.989 | 1.554 | 0.688 |
| TRMT1 | 2 | 0.983 | 1.782 | 0.989 |
| LAMTOR4 | 3 | 0.982 | 1.864 | 0.989 |
| NPRL3 | 4 | 0.979 | -1.318 | 0.989 |
| EIF3F | 5 | 0.978 | -1.177 | 0.425 |
| EEPD1 | 6 | 0.976 | 1.220 | 0.989 |
| RNF168 | 7 | 0.973 | 1.333 | 0.989 |
| RIPK2 | 8 | 0.972 | 1.156 | 0.989 |
| SRFBP1 | 9 | 0.971 | -1.510 | 1.000 |
| LMBRD1 | 10 | 0.970 | 1.124 | 0.989 |

## Provenance and reproducibility
See scoring_spec.md, configs/phase3.json, results/phase3_manifest.json and each evidence record’s source sheet/row. Run python phase3.py, then python -m pytest tests -q. The source workbook and MGI snapshot reside in data/sources/phase3/. No external service credentials are required.
[Source paper and data](https://elifesciences.org/articles/65109/figures); [MGI homology](https://www.informatics.jax.org/homology.shtml).

## What remains scientifically unavailable
Numerical compatible T-cell-function outcomes, independent biological units across study families, and a pristine held-out test set are still needed for the original predictive objective. The six qualitative leads and their endpoint mismatch remain documented. Marker screen rows must never be relabeled as a T-cell-function benchmark.
