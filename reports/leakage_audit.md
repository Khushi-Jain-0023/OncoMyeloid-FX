# Phase 4 leakage audit



Passed actual-data checks: unique evidence IDs; one family per DOI; all ranking source IDs in the development partition; exact marker endpoint matching; unique human gene per endpoint; unchanged Phase 3 input/output hashes.

Related eLife 65109/65110 papers are grouped as kiritsy_olive_2021. Marelli records are excluded and previously inspected, so they are not a pristine test set. Numerical marker rows all belong to one development family.

Automated regression tests mutate excluded-family outcomes and require unchanged rankings. Phase 4 additionally rejects an excluded source ID or endpoint mismatch in a ranking. No outcome fitting, random gene train/test split, or selection of weights using these robustness results is performed.

Correlation of an integrated score with its own marker feature would reuse construction evidence; it is not computed as predictive accuracy. Transcriptomic/marker-only comparisons are explicitly ablations on the same development universe.

No independent generalization claim is justified. The absence of eligible test outcomes is recorded as not estimable in evaluation_metrics.csv. Study-bootstrap uncertainty is unavailable; patient bootstrap addresses only the human expression component.
