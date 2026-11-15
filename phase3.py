"""Reproducible descriptive evidence curation and marker-stratified ranking."""
from pathlib import Path
import hashlib
import json
import importlib.metadata
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'data/sources/phase3'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def homology_map(table, hgnc):
    """Conservative homology-class lookup, never a case-folded symbol join."""
    valid_ids = set(hgnc.hgnc_id)
    rows = []
    for key, group in table.groupby('DB Class Key'):
        mouse = group[group['NCBI Taxon ID'].eq(10090)].drop_duplicates('Mouse MGI ID')
        human = group[group['NCBI Taxon ID'].eq(9606)].drop_duplicates('HGNC ID')
        for _, m in mouse.iterrows():
            valid = len(mouse) == len(human) == 1 and human.iloc[0]['HGNC ID'] in valid_ids
            rows.append({'mouse_symbol': m.Symbol, 'mouse_gene_id': m['Mouse MGI ID'],
                         'homology_class': str(key),
                         'gene_id': human.iloc[0]['HGNC ID'] if valid else None,
                         'mapping_status': 'one_to_one' if valid else 'ambiguous_class'})
    result = pd.DataFrame(rows)
    duplicates = result.mouse_symbol.duplicated(keep=False)
    result.loc[duplicates, 'gene_id'] = None
    result.loc[duplicates, 'mapping_status'] = 'multiple_classes'
    human_duplicates = result.gene_id.notna() & result.gene_id.duplicated(keep=False)
    result.loc[human_duplicates, 'gene_id'] = None
    result.loc[human_duplicates, 'mapping_status'] = 'human_id_multiple_classes'
    return result.drop_duplicates('mouse_symbol')


def candidate_ids(candidates, hgnc):
    out = candidates.copy()
    exact = hgnc.set_index('symbol').hgnc_id.to_dict()
    aliases = {}
    for row in hgnc.itertuples():
        for field in ['prev_symbol', 'alias_symbol']:
            value = getattr(row, field)
            if pd.notna(value):
                for symbol in str(value).split('|'):
                    aliases.setdefault(symbol, set()).add(row.hgnc_id)
    def resolve(symbol):
        if symbol in exact:
            return exact[symbol], 'approved_symbol'
        matches = aliases.get(symbol, set())
        return (next(iter(matches)), 'unique_previous_or_alias') if len(matches) == 1 else (None, 'unresolved')
    out[['gene_id', 'human_mapping_status']] = pd.DataFrame(
        [resolve(s) for s in out.gene_symbol], index=out.index)
    collision = out.gene_id.notna() & out.gene_id.duplicated(keep=False)
    out.loc[collision, 'gene_id'] = None
    out.loc[collision, 'human_mapping_status'] = 'candidate_id_collision'
    return out


def read_screen(path, mapping, config):
    raw = pd.read_excel(path, sheet_name='Sheet1', header=12)
    assert raw.columns[:5].tolist() == ['Gene', 'sgRNA', 'MHCII', 'CD40', 'PDL1']
    assert raw.Gene.notna().all() and raw.Gene.is_unique
    rows = []
    for endpoint, prefix in [('MHCII', 'mhc'), ('CD40', 'cd40'), ('PDL1', 'pdl1')]:
        d = pd.DataFrame({'mouse_symbol': raw.Gene, 'guide_n': raw.sgRNA,
                          'effect_size': raw[endpoint], 'source_row': np.arange(len(raw)) + 14})
        for name, suffix in [('high', ''), ('low', '.1')]:
            for stat in ['beta', 'z', 'p-value', 'fdr', 'wald-p-value', 'wald-fdr']:
                d[f'{name}_{stat.replace("-", "_")}'] = raw[f'{prefix}|{stat}{suffix}']
        assert np.allclose(d.effect_size, d.high_beta - d.low_beta, atol=1e-8)
        for col in [c for c in d if 'p_value' in c or 'fdr' in c]:
            assert d[col].between(0, 1).all(), col
        d['evidence_id'] = 'K09_SCREEN_' + endpoint + '_' + d.mouse_symbol
        d['outcome'] = endpoint
        d['effect_direction'] = np.where(d.effect_size > 0, 'KO_high_marker_enrichment',
                                         np.where(d.effect_size < 0, 'KO_low_marker_enrichment', 'zero_selection_contrast'))
        rows.append(d)
    evidence = pd.concat(rows, ignore_index=True).merge(mapping, on='mouse_symbol', how='left', validate='many_to_one')
    evidence['mapping_status'] = evidence.mapping_status.fillna('absent_from_snapshot')
    evidence['doi'] = config['screen_doi']
    evidence['split_group'] = config['screen_family']
    evidence['organism'] = 'Mus musculus'
    evidence['perturbed_cell_type'] = 'immortalized_bone_marrow_derived_macrophage'
    evidence['perturbation'] = 'CRISPR_knockout'
    evidence['experimental_context'] = 'IFNg_stimulated_mouse_macrophages_non_tumor'
    evidence['assay'] = 'pooled_CRISPR_FACS_surface_marker'
    evidence['effect_unit'] = 'MAGeCK_MLE_beta_high_minus_low'
    evidence['uncertainty'] = None
    evidence['biological_n'] = np.nan
    evidence['screen_replicate_n'] = 2
    evidence['replicate_unit'] = 'duplicate_screen_selections_not_donor_n'
    evidence['evidence_tier'] = 'indirect'
    evidence['endpoint_class'] = 'immune_marker_proxy'
    evidence['quantitative'] = True
    evidence['source_file'] = path.name
    evidence['source_location'] = 'Sheet1!row' + evidence.source_row.astype(str)
    evidence['compatibility_notes'] = 'mouse_non_tumor_marker_endpoint_not_T_cell_function'
    return evidence


def qualitative_records(path, mapping):
    q = pd.read_csv(path).rename(columns={'gene_symbol': 'mouse_symbol'})
    q = q.drop(columns='gene_id').merge(mapping, on='mouse_symbol', how='left', validate='many_to_one')
    q['mapping_status'] = q.mapping_status.fillna('absent_from_snapshot')
    q['quantitative'] = False
    q['endpoint_class'] = 'T_cell_function_qualitative'
    q['source_file'] = 'data/registry/perturbations.csv'
    return q


def development_evidence(evidence, config):
    dev, excluded = set(config['development_groups']), set(config['excluded_groups'])
    if dev & excluded:
        raise ValueError('Development/excluded families overlap')
    known = dev | excluded
    if not set(evidence.split_group).issubset(known):
        raise ValueError('Unassigned study family')
    return evidence.loc[evidence.split_group.isin(dev)].copy()


def baseline(candidates):
    d = candidates.copy()
    d['association_rank'] = d.p_value.rank(method='min')
    d['absolute_effect_rank'] = d.association_effect.abs().rank(ascending=False, method='min')
    d['composition_rank'] = d.composition_adjusted_p.rank(method='min')
    return d.sort_values(['association_rank', 'gene_symbol'])


def integrate(candidates, evidence, config):
    """Excluded families are removed before any aggregation or feature construction."""
    dev = development_evidence(evidence, config)
    outputs = []
    for endpoint in config['endpoints']:
        source = dev.loc[dev.quantitative & dev.endpoint_class.eq('immune_marker_proxy') &
                         dev.outcome.eq(endpoint) & dev.gene_id.notna()].copy()
        if source.gene_id.duplicated().any():
            raise ValueError('Multiple source rows per human gene/endpoint require a new protocol')
        source = source[['gene_id', 'evidence_id', 'effect_size', 'split_group']].rename(
            columns={'effect_size': 'marker_selection_contrast', 'evidence_id': 'source_ids'})
        d = candidates.merge(source, on='gene_id', how='left', validate='many_to_one')
        eligible = d.marker_selection_contrast.notna() & d.gene_id.notna()
        d['endpoint'] = endpoint
        d['context_compatibility'] = 'indirect_mouse_non_tumor_marker'
        d['ranking_scope'] = config['scope']
        d['model_version'] = config['model_version']
        d['functional_evidence_status'] = np.where(eligible, 'measured_marker_proxy', 'missing_eligible_evidence')
        d['transcriptomic_evidence'] = np.nan
        d['functional_evidence'] = np.nan
        d.loc[eligible, 'transcriptomic_evidence'] = (-np.log10(d.loc[eligible, 'p_value'].clip(lower=1e-300))).rank(pct=True)
        d.loc[eligible, 'functional_evidence'] = d.loc[eligible, 'marker_selection_contrast'].abs().rank(pct=True)
        weight = config['transcriptomic_weight']
        d['ranking_value'] = (weight * d.transcriptomic_evidence + (1 - weight) * d.functional_evidence).round(12)
        d['rank'] = d.ranking_value.rank(ascending=False, method='min')
        d['rank_denominator'] = int(eligible.sum())
        d['rank_stability'] = 'not_estimated;see_weight_sensitivity_and_loo_sign_fraction'
        for w in config['weight_sensitivities']:
            value = (w * d.transcriptomic_evidence + (1 - w) * d.functional_evidence).round(12)
            d[f'rank_weight_{w:g}'] = value.rank(ascending=False, method='min')
        outputs.append(d.sort_values(['rank', 'gene_symbol'], na_position='last'))
    return pd.concat(outputs, ignore_index=True)


def main():
    config = json.loads((ROOT / 'configs/phase3.json').read_text())
    hgnc = pd.read_csv(ROOT / 'work/hgnc_complete_set.txt', sep='\t', low_memory=False)
    mapping = homology_map(pd.read_csv(SOURCES / 'HOM_MouseHumanSequence.rpt', sep='\t'), hgnc)
    candidates = candidate_ids(pd.read_csv(ROOT / 'results/transcriptomic_candidates.csv'), hgnc)
    screen = read_screen(SOURCES / 'elife-65109-fig1-data1-v2.xlsx', mapping, config)
    qualitative = qualitative_records(ROOT / 'data/registry/perturbations.csv', mapping)
    evidence = pd.concat([screen, qualitative], ignore_index=True)
    symbols = hgnc.set_index('hgnc_id').symbol
    evidence['gene_symbol'] = evidence.gene_id.map(symbols)
    evidence['partition'] = np.where(evidence.split_group.isin(config['development_groups']), 'development', 'excluded_not_pristine_test')
    evidence['eligible_marker_ranking'] = evidence.quantitative & evidence.gene_id.notna() & evidence.partition.eq('development')
    evidence['eligible_direct_T_function_ranking'] = False
    evidence.to_parquet(ROOT / 'data/curated/functional_evidence.parquet', index=False)
    qualitative.to_csv(ROOT / 'results/phase3_qualitative_evidence.csv', index=False)
    mapping.to_csv(ROOT / 'results/phase3_orthology_audit.csv', index=False)
    b = baseline(candidates)
    b.to_csv(ROOT / 'results/baseline_rankings.csv', index=False)
    integrated = integrate(b, evidence, config)
    integrated.to_csv(ROOT / 'results/integrated_rankings.csv', index=False)
    coverage = integrated.groupby('endpoint').agg(candidates=('gene_symbol', 'size'),
        ranked=('rank', 'count'), missing=('rank', lambda s: s.isna().sum()))
    coverage.to_csv(ROOT / 'results/phase3_coverage.csv')
    sensitivity = []
    for endpoint, g in integrated.groupby('endpoint'):
        for w in config['weight_sensitivities']:
            col = f'rank_weight_{w:g}'
            sensitivity.append({'endpoint': endpoint, 'transcriptomic_weight': w,
                'rank_spearman': g[['rank', col]].corr(method='spearman').iloc[0, 1],
                'top20_overlap': len(set(g.nsmallest(20, 'rank').gene_symbol) & set(g.nsmallest(20, col).gene_symbol))})
    pd.DataFrame(sensitivity).to_csv(ROOT / 'results/phase3_weight_sensitivity.csv', index=False)
    manifest = {'created_utc': pd.Timestamp.now(tz='UTC').isoformat(), 'config': config,
        'screen_genes': screen.mouse_symbol.nunique(), 'quantitative_records': len(screen),
        'qualitative_records': len(qualitative), 'families': sorted(evidence.split_group.unique()),
        'direct_T_function_eligible_records': 0, 'coverage': coverage.reset_index().to_dict('records'),
        'predictive_gate': 'NO_GO', 'phase3_status': 'descriptive_deliverables_complete_direct_functional_objective_unavailable',
        'packages': {p: importlib.metadata.version(p) for p in ['pandas', 'numpy', 'openpyxl', 'pyarrow']}}
    inputs = [ROOT / 'configs/phase3.json', ROOT / 'reports/scoring_spec.md', Path(__file__),
              ROOT / 'results/transcriptomic_candidates.csv', ROOT / 'data/registry/perturbations.csv',
              ROOT / 'work/hgnc_complete_set.txt', *sorted(SOURCES.glob('*'))]
    manifest['input_sha256'] = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in inputs if p.is_file()}
    (ROOT / 'results/phase3_manifest.json').write_text(json.dumps(manifest, indent=2))
    report = ['# Phase 3: functional evidence and descriptive ranking', '',
        'Descriptive implementation complete. The original human T-cell-function prediction objective remains unavailable; predictive NO-GO is unchanged.', '',
        f'Curated {len(screen):,} quantitative marker records for {screen.mouse_symbol.nunique():,} mouse genes, plus {len(qualitative)} qualitative T-cell-function leads.',
        'All three marker screens belong to one development publication family. Related publications are not independent validation.', '',
        '## Coverage', '| Endpoint | Candidate genes | Ranked with proxy evidence | Missing eligible evidence |', '|---|---:|---:|---:|']
    for endpoint, r in coverage.iterrows():
        report.append(f'| {endpoint} | {r.candidates} | {r.ranked} | {r.missing} |')
    report += ['', '## Interpretation',
        'Integrated scores combine observational association strength with absolute mouse marker-screen selection contrasts, separately by endpoint. They do not predict suppression direction, clinical benefit, causality or T-cell-function effect size. No primary Phase 2 association passed 5% FDR.',
        'The source workbook provides component test statistics, not uncertainty for the high-minus-low contrast; no combined significance is invented. Missing numeric T-cell effects stay missing. Missing/ambiguous orthology excludes integration but preserves the transcriptomic baseline.', '',
        '## Leading exploratory results']
    for endpoint, g in integrated.groupby('endpoint'):
        report += ['', f'### {endpoint}', '| Source human symbol | Rank | Score | Mouse marker contrast | Primary transcriptomic FDR |', '|---|---:|---:|---:|---:|']
        for r in g.dropna(subset=['rank']).head(10).itertuples():
            report.append(f'| {r.gene_symbol} | {r.rank:g} | {r.ranking_value:.3f} | {r.marker_selection_contrast:.3f} | {r.fdr:.3f} |')
    report += ['', '## Provenance and reproducibility',
        'See scoring_spec.md, configs/phase3.json, results/phase3_manifest.json and each evidence record’s source sheet/row. Run python phase3.py, then python -m pytest tests -q. The source workbook and MGI snapshot reside in data/sources/phase3/. No external service credentials are required.',
        '[Source paper and data](https://elifesciences.org/articles/65109/figures); [MGI homology](https://www.informatics.jax.org/homology.shtml).', '',
        '## What remains scientifically unavailable',
        'Numerical compatible T-cell-function outcomes, independent biological units across study families, and a pristine held-out test set are still needed for the original predictive objective. The six qualitative leads and their endpoint mismatch remain documented. Marker screen rows must never be relabeled as a T-cell-function benchmark.']
    (ROOT / 'reports/phase3_evidence_ranking.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k not in ['input_sha256', 'config', 'packages']}, indent=2))


if __name__ == '__main__':
    main()
