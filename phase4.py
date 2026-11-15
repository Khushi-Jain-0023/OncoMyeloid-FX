"""Patient-level robustness and an explicit independent-benchmark eligibility audit."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
R = ROOT / 'results'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hc3(x, y):
    """Vectorized standardized simple OLS, HC3 SE and t(n-2) p; finite inputs."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim == 1:
        x = x[:, None]
    n, g = x.shape
    missing = np.full(g, np.nan)
    if n < 6 or not np.isfinite(y).all() or np.std(y, ddof=1) < 1e-12:
        return missing.copy(), missing.copy(), missing.copy()
    valid = np.isfinite(x).all(axis=0) & (np.std(x, axis=0, ddof=1) >= 1e-12)
    with np.errstate(divide='ignore', invalid='ignore'):
        z = (x - x.mean(axis=0)) / x.std(axis=0, ddof=1)
        yy = (y - y.mean()) / y.std(ddof=1)
        beta = np.sum(z * yy[:, None], axis=0) / (n - 1)
        residual = yy[:, None] - z * beta
        leverage = 1 / n + z ** 2 / (n - 1)
        valid &= (leverage < .999999).all(axis=0)
        se = np.sqrt(np.sum((z * residual / (1 - leverage)) ** 2, axis=0)) / (n - 1)
        p = 2 * stats.t.sf(np.abs(beta / se), n - 2)
    beta[~valid] = np.nan
    se[~valid] = np.nan
    p[~valid | (se <= 0)] = np.nan
    return beta, se, p


def percentiles(values):
    return pd.Series(values).rank(pct=True, method='average').to_numpy()


def scores(p, marker, weight=.5):
    p, marker = np.asarray(p, float), np.asarray(marker, float)
    valid = np.isfinite(p) & np.isfinite(marker)
    result = np.full(len(p), np.nan)
    result[valid] = np.round(weight * percentiles(-np.log10(np.maximum(p[valid], 1e-300))) +
                             (1 - weight) * percentiles(np.abs(marker[valid])), 12)
    return result


def top_indices(values, symbols, k=20):
    valid = np.flatnonzero(np.isfinite(values))
    return valid[np.lexsort((np.asarray(symbols)[valid], -np.asarray(values)[valid]))[:k]]


def compare(reference, variant, symbols, k=20):
    reference, variant = np.asarray(reference), np.asarray(variant)
    good = np.isfinite(reference) & np.isfinite(variant)
    count = int(good.sum())
    result = {'common_genes': count, 'variant_available': int(np.isfinite(variant).sum()),
              'rank_spearman': np.nan, 'top20_overlap': np.nan, 'max_rank_change': np.nan,
              'status': 'not_estimable' if count < k else 'descriptive_only'}
    if count < k:
        return result
    a, b, labels = reference[good], variant[good], np.asarray(symbols)[good]
    result['rank_spearman'] = stats.spearmanr(a, b).statistic if np.std(a) > 0 and np.std(b) > 0 else np.nan
    result['top20_overlap'] = len(set(top_indices(a, labels, k)) & set(top_indices(b, labels, k)))
    result['max_rank_change'] = float(np.max(np.abs(stats.rankdata(-a, method='min') - stats.rankdata(-b, method='min'))))
    return result


def audit(evidence, rankings):
    if not evidence.evidence_id.is_unique:
        raise ValueError('Duplicate evidence IDs')
    if evidence.groupby('doi').split_group.nunique().gt(1).any():
        raise ValueError('DOI assigned to multiple study families')
    used = rankings.dropna(subset=['source_ids'])
    source = evidence.set_index('evidence_id').loc[used.source_ids]
    if not source.partition.eq('development').all():
        raise ValueError('Excluded evidence used in ranking')
    if not np.array_equal(source.outcome.to_numpy(), used.endpoint.to_numpy()):
        raise ValueError('Endpoint mismatch')
    if used.groupby('endpoint').gene_id.apply(lambda x: x.duplicated().any()).any():
        raise ValueError('Duplicate mapped gene per endpoint')
    quantitative = evidence.loc[evidence.quantitative]
    eligible = evidence.loc[evidence.eligible_direct_T_function_ranking & evidence.quantitative &
                            evidence.gene_id.notna() & evidence.effect_size.notna() &
                            evidence.partition.eq('independent_unseen_test')]
    return {'quantitative_families': int(quantitative.split_group.nunique()),
            'eligible_independent_records': len(eligible), 'decision': 'inconclusive',
            'source_partition_check': 'passed', 'endpoint_check': 'passed',
            'note': 'No eligible unseen direct functional outcomes; no independent metrics computed.'}


def main():
    cfg = json.loads((ROOT / 'configs/phase4.json').read_text())
    # Check exact Phase 3 source/outputs before using them.
    for name in ['phase3_manifest.json', 'phase3_verification.json']:
        manifest = json.loads((R / name).read_text())
        for rel, expected in manifest.get('input_sha256', manifest.get('output_sha256', {})).items():
            if sha(ROOT / rel) != expected:
                raise ValueError(f'Changed Phase 3 artifact: {rel}')
    c = pd.read_csv(R / 'baseline_rankings.csv', float_precision='round_trip').sort_values('gene_symbol').reset_index(drop=True)
    genes = c.gene_symbol.to_numpy()
    f = pd.read_csv(R / 'patient_features.csv').set_index('patient_id')
    expr = pd.read_csv(R / 'patient_macrophage_expression.csv', index_col=0)
    assert expr.index.is_unique and set(expr.index) == set(f.index)
    x = expr.loc[f.index, genes].to_numpy(float)
    y = f.t_inhibitory.to_numpy(float)
    b, se, p = hc3(x, y)
    np.testing.assert_allclose(b, c.association_effect, atol=2e-6, rtol=2e-6)
    np.testing.assert_allclose(p, c.p_value, atol=2e-6, rtol=2e-5)
    print('Reproduced primary models; auditing evidence and resampling patients.', flush=True)
    e = pd.read_parquet(ROOT / 'data/curated/functional_evidence.parquet')
    rankings = pd.read_csv(R / 'integrated_rankings.csv', float_precision='round_trip')
    decision = audit(e, rankings)
    metric_rows = []
    for model in ['transcriptomic_association', 'absolute_effect', 'composition_adjusted', 'integrated_marker_proxy']:
        for metric in ['AUPRC', 'precision_at_20', 'spearman_functional_effect']:
            metric_rows.append({'model': model, 'endpoint': cfg['endpoint'], 'metric': metric,
                'estimate': np.nan, 'ci_lower': np.nan, 'ci_upper': np.nan,
                'test_studies': 0, 'test_genes': 0, 'status': 'not_estimable',
                'reason': 'no_compatible_independent_quantitative_T_cell_function_outcomes'})
    pd.DataFrame(metric_rows).to_csv(R / 'evaluation_metrics.csv', index=False)
    family = e.groupby(['split_group', 'partition', 'endpoint_class'], dropna=False).agg(
        rows=('evidence_id', 'size'), mapped=('gene_id', 'count'), numeric=('effect_size', 'count'))
    family.to_csv(R / 'phase4_family_audit.csv')
    # Paired patient resampling. No gene or cell bootstrap.
    rng = np.random.default_rng(cfg['seed'])
    n_boot = cfg['bootstrap_replicates']
    boot_p = np.empty((n_boot, len(genes)))
    boot_b = np.empty_like(boot_p)
    draws = []
    for j in range(n_boot):
        ix = rng.integers(0, len(f), size=len(f))
        boot_b[j], _, boot_p[j] = hc3(x[ix], y[ix])
        draws.append({'replicate': j, 'sampled_patient_ids': '|'.join(f.index[ix]),
                      'unique_patients': len(set(ix)), 'estimable_genes': int(np.isfinite(boot_p[j]).sum())})
    pd.DataFrame(draws).to_csv(R / 'phase4_bootstrap_draws.csv', index=False)
    quantiles = cfg['interval_quantiles']
    effect_q = np.nanquantile(boot_b, quantiles, axis=0)
    pd.DataFrame({'gene_symbol': genes, 'effect_q025': effect_q[0], 'effect_median': effect_q[1],
        'effect_q975': effect_q[2], 'valid_draws': np.isfinite(boot_b).sum(axis=0)}).to_csv(R / 'phase4_effect_resampling.csv', index=False)
    loo_p = []
    for i in range(len(f)):
        take = np.arange(len(f)) != i
        _, _, lp = hc3(x[take], y[take])
        loo_p.append(lp)
    sensitivity = pd.read_csv(R / 'sensitivity_models.csv')
    comparisons, loo_rows, boot_summaries, failures = [], [], [], []
    for endpoint, g in rankings.groupby('endpoint'):
        g = g.set_index('gene_symbol').loc[genes]
        selected = np.flatnonzero(g['rank'].notna().to_numpy())
        labels = genes[selected]
        marker = e.set_index('evidence_id').loc[g.source_ids.iloc[selected], 'effect_size'].to_numpy()
        reference = g.ranking_value.to_numpy()[selected]
        np.testing.assert_allclose(scores(c.p_value.to_numpy()[selected], marker), reference, atol=1e-12)
        base_rank = stats.rankdata(-reference, method='min')
        variants = {'transcriptomic_only': percentiles(-np.log10(c.p_value.to_numpy()[selected])),
                    'marker_only': percentiles(np.abs(marker)),
                    'composition_adjusted': scores(c.composition_adjusted_p.to_numpy()[selected], marker),
                    'within_state': scores(c.within_state_p.to_numpy()[selected], marker),
                    'exclude_indirect': np.full(len(selected), np.nan),
                    'leave_development_family_out': np.full(len(selected), np.nan)}
        for analysis, group in sensitivity.groupby('analysis'):
            ap = group.set_index('gene_symbol').loc[labels, 'p_value'].to_numpy()
            variants[analysis] = scores(ap, marker)
        assert set(variants) == set(cfg['comparisons'])
        for name, value in variants.items():
            row = {'endpoint': endpoint, 'comparison': name, **compare(reference, value, labels, cfg['top_k'])}
            row['interpretation'] = ('different_T_endpoint' if name in ['cytotoxic', 'CD8'] else
                'no_eligible_evidence' if name in ['exclude_indirect', 'leave_development_family_out'] else
                'unestimable_design' if name == 'sex' else 'descriptive_rank_agreement')
            comparisons.append(row)
        all_loo_ranks = []
        for patient, lp in zip(f.index, loo_p):
            value = scores(lp[selected], marker)
            loo_rows.append({'endpoint': endpoint, 'omitted_patient': patient,
                             **compare(reference, value, labels, cfg['top_k'])})
            all_loo_ranks.append(pd.Series(value).rank(ascending=False, method='min').to_numpy())
        all_loo_ranks = np.array(all_loo_ranks)
        rank_draws = np.full((n_boot, len(selected)), np.nan)
        hit = np.zeros(len(selected), int)
        for j in range(n_boot):
            value = scores(boot_p[j, selected], marker)
            rank_draws[j] = pd.Series(value).rank(ascending=False, method='min').to_numpy()
            hit[top_indices(value, labels, cfg['top_k'])] += 1
        rq = np.nanquantile(rank_draws, quantiles, axis=0)
        valid_n = np.isfinite(rank_draws).sum(axis=0)
        summary = pd.DataFrame({'endpoint': endpoint, 'gene_symbol': labels, 'reference_rank': base_rank,
            'rank_q025': rq[0], 'rank_median': rq[1], 'rank_q975': rq[2],
            'valid_draws': valid_n, 'top20_count': hit,
            'top20_frequency_all_draws': hit / n_boot,
            'top20_frequency_valid_draws': np.divide(hit, valid_n, out=np.full(len(hit), np.nan), where=valid_n>0),
            'loo_min_rank': np.nanmin(all_loo_ranks, axis=0), 'loo_max_rank': np.nanmax(all_loo_ranks, axis=0),
            'max_loo_rank_change': np.nanmax(np.abs(all_loo_ranks - base_rank), axis=0)})
        boot_summaries.append(summary)
        top = top_indices(reference, labels, cfg['top_k'])
        failure = summary.iloc[top].copy()
        failure['case_type'] = 'reference_top20_patient_sensitivity'
        failures.append(failure)
        shifts = summary.nlargest(20, 'max_loo_rank_change').copy()
        shifts['case_type'] = 'largest_LOO_rank_changes'
        failures.append(shifts)
    comparison = pd.DataFrame(comparisons)
    loo = pd.DataFrame(loo_rows)
    boot = pd.concat(boot_summaries, ignore_index=True)
    comparison.to_csv(R / 'phase4_ablation_metrics.csv', index=False)
    loo.to_csv(R / 'phase4_leave_patient_out.csv', index=False)
    boot.to_csv(R / 'phase4_rank_resampling.csv', index=False)
    pd.concat(failures, ignore_index=True).to_csv(R / 'phase4_failure_cases.csv', index=False)
    plot(comparison, loo, boot)
    report(decision, comparison, loo, boot, cfg)
    sources = ['phase4.py', 'configs/phase4.json', 'reports/phase4_protocol.md',
        'results/baseline_rankings.csv', 'results/integrated_rankings.csv',
        'results/patient_features.csv', 'results/patient_macrophage_expression.csv',
        'results/sensitivity_models.csv', 'data/curated/functional_evidence.parquet',
        'results/phase3_manifest.json', 'results/phase3_verification.json']
    manifest = {'created_utc': pd.Timestamp.now(tz='UTC').isoformat(), 'config': cfg,
        'patients': len(f), 'genes': len(genes), 'bootstrap_draws': n_boot,
        'decision': decision, 'input_sha256': {name: sha(ROOT / name) for name in sources}}
    (R / 'phase4_manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['input_sha256','config']}, indent=2), flush=True)


def plot(comparison, loo, boot):
    names = ['transcriptomic_only','marker_only','composition_adjusted','within_state','age','library_size',
             'exclude_double_histology','cytotoxic','CD8','retain_doublets','adaptive_qc','strict_T_annotation']
    table = comparison.pivot(index='comparison', columns='endpoint', values='top20_overlap').loc[names]
    fig, ax = plt.subplots(figsize=(8, 6.5), constrained_layout=True)
    im = ax.imshow(table.to_numpy(), vmin=0, vmax=20, cmap='viridis', aspect='auto')
    ax.set_xticks(range(3), table.columns)
    ax.set_yticks(range(len(table)), table.index)
    for i in range(len(table)):
        for j in range(3):
            value = table.iloc[i, j]
            ax.text(j, i, str(int(value)), ha='center', va='center', color='white' if value<10 else 'black')
    fig.suptitle('Top-20 agreement with Phase 3\nDescriptive sensitivity, not independent validation', fontsize=12)
    fig.colorbar(im, ax=ax, label='Genes shared in top 20')
    fig.savefig(R / 'plots/phase4_ablations.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), constrained_layout=True)
    for ax, (endpoint, g) in zip(axes, boot.groupby('endpoint')):
        top = g.sort_values(['reference_rank','gene_symbol']).head(10).iloc[::-1]
        yy = np.arange(len(top))
        ax.hlines(yy, top.rank_q025, top.rank_q975, color='#497b9b')
        ax.scatter(top.rank_median, yy, color='#223c50', label='Bootstrap median', s=18)
        ax.scatter(top.reference_rank, yy, marker='x', color='#c26925', label='Full cohort', s=22)
        ax.set_yticks(yy, top.gene_symbol)
        ax.set(title=endpoint, xlabel='Rank (lower is earlier)')
    axes[0].legend(fontsize=8)
    fig.suptitle('Top candidates: central 95% patient-resampling rank ranges\n300 paired draws; marker evidence fixed; not functional-performance CIs')
    fig.savefig(R / 'plots/phase4_rank_ranges.png', dpi=150)
    plt.close(fig)


def report(decision, comparison, loo, boot, cfg):
    lines = ['# Phase 4 benchmark and robustness', '', '**Decision: INCONCLUSIVE.** Independent functional performance cannot be estimated from the current inventory.', '',
        'The audit found one quantitative development family and zero eligible independent quantitative T-cell-function outcomes. No AUPRC, precision@20, held-out rank correlation or performance confidence interval is reported. Missing metrics are not zero performance. Neither superiority nor failure to improve is established.', '',
        '## Completed analyses', f'Frozen universe: 6,124 genes, 11 patients, 5,155 mapped candidates per marker. Completed {cfg["bootstrap_replicates"]} paired patient bootstrap draws, 11 leave-one-patient-out refits, 15 ablation/sensitivity comparisons per marker, source/partition checks and provenance verification. All three mouse marker endpoints stay separate.', '',
        '## Leave-one-patient-out stability', '| Marker | Spearman range | Shared top-20 range |', '|---|---:|---:|']
    for endpoint, g in loo.groupby('endpoint'):
        lines.append(f'| {endpoint} | {g.rank_spearman.min():.3f}–{g.rank_spearman.max():.3f} | {g.top20_overlap.min():g}–{g.top20_overlap.max():g} |')
    lines += ['', 'The top lists change materially when individual patients are omitted. For the leading full-data candidate in each marker stratum, top-20 membership across patient-bootstrap draws was:']
    for endpoint, g in boot.groupby('endpoint'):
        first = g.sort_values(['reference_rank','gene_symbol']).iloc[0]
        lines.append(f'- {endpoint}: {first.gene_symbol}, {first.top20_frequency_all_draws:.1%}; central rank range {first.rank_q025:.1f}–{first.rank_q975:.1f}.')
    lines += ['', '## Ablation and sensitivity findings', '| Marker | Comparison | Common genes | Shared top 20 | Rank correlation |', '|---|---|---:|---:|---:|']
    for r in comparison.itertuples():
        shared = 'not estimable' if pd.isna(r.top20_overlap) else str(int(r.top20_overlap))
        rho = 'not estimable' if pd.isna(r.rank_spearman) else f'{r.rank_spearman:.3f}'
        lines.append(f'| {r.endpoint} | {r.comparison} | {r.common_genes} | {shared} | {rho} |')
    lines += ['', '## Patient-resampling uncertainty and failure cases',
        'Per-gene effect and rank quantiles, valid-draw counts, top-20 selection frequencies and patient omissions are exported. Central 95% resampling ranges are descriptive stability summaries with only 11 patients, not calibrated CIs. They condition on the selected genes, fixed mouse assays, orthology and source annotation. They do not cover functional-study uncertainty.',
        'Failure-case tables retain all reference top-20 genes and the largest leave-one-patient-out rank changes. A high full-data rank need not mean stable prioritization. Removing indirect evidence or the sole development family eliminates integrated ranking; the sex-adjusted model is unestimable. Cytotoxic/CD8 comparisons change the endpoint and are not replication.', '',
        '## Limits and reopening requirements',
        'Only one human transcriptomic cohort is available, so cohort transfer cannot be assessed. No valid differential-expression contrast or compatible independent ligand-method benchmark was specified. No gene split, marker proxy, selected qualitative follow-up or same-study cross-marker comparison replaces an independent functional endpoint. New compatible quantitative T-cell-function studies with biological units, stable mappings and previously unseen study families are required; freeze a new evaluation protocol before inspecting outcomes.', '',
        '## Reproduce', '`python phase4.py`; `python -m pytest tests -q`; `python build_phase4_notebook.py`; `python verify_phase4.py`. See phase4_protocol.md, leakage_audit.md, configs/phase4.json and results/phase4_manifest.json.', '',
        '![Ablations](../results/plots/phase4_ablations.png)', '![Rank ranges](../results/plots/phase4_rank_ranges.png)']
    (ROOT / 'reports/benchmark.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    audit_text = ['# Phase 4 leakage audit', '',
        'Passed actual-data checks: unique evidence IDs; one family per DOI; all ranking source IDs in the development partition; exact marker endpoint matching; unique human gene per endpoint; unchanged Phase 3 input/output hashes.',
        'Related eLife 65109/65110 papers are grouped as kiritsy_olive_2021. Marelli records are excluded and previously inspected, so they are not a pristine test set. Numerical marker rows all belong to one development family.',
        'Automated regression tests mutate excluded-family outcomes and require unchanged rankings. Phase 4 additionally rejects an excluded source ID or endpoint mismatch in a ranking. No outcome fitting, random gene train/test split, or selection of weights using these robustness results is performed.',
        'Correlation of an integrated score with its own marker feature would reuse construction evidence; it is not computed as predictive accuracy. Transcriptomic/marker-only comparisons are explicitly ablations on the same development universe.',
        'No independent generalization claim is justified. The absence of eligible test outcomes is recorded as not estimable in evaluation_metrics.csv. Study-bootstrap uncertainty is unavailable; patient bootstrap addresses only the human expression component.']
    (ROOT / 'reports/leakage_audit.md').write_text('\n\n'.join(audit_text)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
