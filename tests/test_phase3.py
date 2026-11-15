import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from phase3 import homology_map, candidate_ids, integrate, development_evidence

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    candidates = pd.DataFrame({'gene_id': ['HGNC:1', 'HGNC:2', 'HGNC:3', None],
                               'gene_symbol': ['A', 'B', 'C', 'D'],
                               'p_value': [.001, .1, .5, .001]})
    evidence = pd.DataFrame({'gene_id': ['HGNC:1', 'HGNC:2', 'HGNC:3'],
        'evidence_id': ['a', 'b', 'held'], 'split_group': ['dev', 'dev', 'held'],
        'quantitative': [True] * 3, 'endpoint_class': ['immune_marker_proxy'] * 3,
        'outcome': ['MHCII'] * 3, 'effect_size': [0., 2., 99.]})
    config = {'development_groups': ['dev'], 'excluded_groups': ['held'],
        'endpoints': ['MHCII'], 'scope': 'test', 'model_version': 'test',
        'transcriptomic_weight': .5, 'weight_sensitivities': [.25, .75]}
    return candidates, evidence, config


def test_missing_is_not_zero_and_hand_calculated_rank():
    c, e, cfg = fixture()
    result = integrate(c, e, cfg).set_index('gene_symbol')
    # A: T=1,F=.5; B:T=.5,F=1. Both have score .75 and rank 1.
    assert result.loc['A', 'ranking_value'] == .75
    assert result.loc['B', 'ranking_value'] == .75
    assert result.loc[['A', 'B'], 'rank'].eq(1).all()
    assert result.loc[['C', 'D'], 'ranking_value'].isna().all()
    assert result.loc['A', 'marker_selection_contrast'] == 0
    assert result.rank_denominator.eq(2).all()


def test_export_preserves_tied_ranks():
    from io import StringIO
    c, e, cfg = fixture()
    result = integrate(c, e, cfg)
    restored = pd.read_csv(StringIO(result.to_csv(index=False)))
    pd.testing.assert_series_equal(restored['rank'], restored.ranking_value.rank(method='min', ascending=False), check_names=False)


def test_excluded_outcome_changes_do_not_change_rankings():
    c, e, cfg = fixture()
    before = integrate(c, e, cfg)
    e.loc[e.split_group.eq('held'), ['gene_id', 'effect_size']] = ['HGNC:1', -100000]
    pd.testing.assert_frame_equal(before, integrate(c, e, cfg))
    cfg['development_groups'].append('held')
    with pytest.raises(ValueError, match='overlap'):
        development_evidence(e, cfg)


def test_unassigned_study_and_duplicate_gene_fail_closed():
    c, e, cfg = fixture()
    e.loc[0, 'split_group'] = 'unassigned'
    with pytest.raises(ValueError, match='Unassigned'):
        integrate(c, e, cfg)
    e.loc[0, 'split_group'] = 'dev'
    with pytest.raises(ValueError, match='Multiple source'):
        integrate(c, pd.concat([e, e.iloc[[0]]]), cfg)


def test_endpoint_isolation():
    c, e, cfg = fixture()
    before = integrate(c, e, cfg)
    other = e.iloc[[0]].copy()
    other['outcome'] = 'PDL1'
    other['effect_size'] = 10000
    pd.testing.assert_frame_equal(before, integrate(c, pd.concat([e, other]), cfg))


def test_ambiguous_orthology_and_aliases_do_not_map():
    h = pd.DataFrame({'hgnc_id': ['HGNC:1', 'HGNC:2'], 'symbol': ['A', 'B'],
                      'prev_symbol': ['OLD', None], 'alias_symbol': ['SHARED', 'SHARED']})
    m = pd.DataFrame({'DB Class Key': [1, 1, 2, 2, 2],
        'NCBI Taxon ID': [10090, 9606, 10090, 9606, 9606],
        'Symbol': ['a', 'A', 'b', 'A', 'B'],
        'Mouse MGI ID': ['MGI:1', None, 'MGI:2', None, None],
        'HGNC ID': [None, 'HGNC:1', None, 'HGNC:1', 'HGNC:2']})
    mapped = homology_map(m, h).set_index('mouse_symbol')
    assert mapped.loc['a', 'gene_id'] == 'HGNC:1'
    assert pd.isna(mapped.loc['b', 'gene_id'])
    c = candidate_ids(pd.DataFrame({'gene_symbol': ['OLD', 'SHARED']}), h)
    assert c.gene_id.iloc[0] == 'HGNC:1' and pd.isna(c.gene_id.iloc[1])
    collision = candidate_ids(pd.DataFrame({'gene_symbol': ['A', 'OLD']}), h)
    assert collision.gene_id.isna().all()


def test_real_data_source_and_missingness():
    # Checks external data semantics against source controls, not just output shape.
    e = pd.read_parquet(ROOT / 'data/curated/functional_evidence.parquet')
    assert e.evidence_id.is_unique and len(e) == 35109
    assert e.loc[~e.quantitative, 'effect_size'].isna().all()
    assert not e.eligible_direct_T_function_ranking.any()
    for mouse, marker in [('H2-Ab1', 'MHCII'), ('Cd40', 'CD40'), ('Cd274', 'PDL1')]:
        row = e.loc[e.mouse_symbol.eq(mouse) & e.outcome.eq(marker)].iloc[0]
        assert row.effect_size < -2  # Known marker KO enriches marker-low cells.
        assert np.isclose(row.effect_size, row.high_beta - row.low_beta)
    r = pd.read_csv(ROOT / 'results/integrated_rankings.csv')
    assert len(r) == 3 * 6124
    missing = r.functional_evidence_status.eq('missing_eligible_evidence')
    assert r.loc[missing, ['rank', 'ranking_value', 'functional_evidence']].isna().all().all()
    assert r.loc[~missing, 'source_ids'].notna().all()
    assert r.loc[~missing, 'ranking_value'].between(0, 1).all()
    assert set(r.split_group.dropna()) == {'kiritsy_olive_2021'}
    assert r.groupby('endpoint').gene_symbol.nunique().eq(6124).all()
