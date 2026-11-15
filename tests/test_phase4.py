from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from phase4 import hc3, scores, compare, top_indices, audit

ROOT = Path(__file__).resolve().parents[1]


def test_vectorized_hc3_matches_statsmodels_with_paired_duplicates():
    rng = np.random.default_rng(2026)
    x, y = rng.normal(size=(11, 7)), rng.normal(size=11)
    for ix in [np.arange(11), np.array([0,0,1,2,2,3,5,7,8,9,10])]:
        b, se, p = hc3(x[ix], y[ix])
        yy = (y[ix] - y[ix].mean()) / y[ix].std(ddof=1)
        for j in range(x.shape[1]):
            z = x[ix, j]
            z = (z-z.mean()) / z.std(ddof=1)
            fit = sm.OLS(yy, sm.add_constant(z)).fit(cov_type='HC3', use_t=True)
            np.testing.assert_allclose([b[j], se[j], p[j]], [fit.params[1], fit.bse[1], fit.pvalues[1]], rtol=1e-10)


def test_degenerate_draws_and_unknown_evidence_stay_missing():
    b, se, p = hc3(np.ones((11,3)), np.arange(11))
    assert np.isnan(b).all() and np.isnan(se).all() and np.isnan(p).all()
    assert np.isnan(hc3(np.arange(11), np.ones(11))[0]).all()
    got = scores([.01, .2, np.nan], [0, np.nan, 1])
    assert got[0] == 1 and np.isnan(got[1:]).all()
    result = compare(np.arange(20), np.full(20,np.nan), [str(i) for i in range(20)])
    assert result['status'] == 'not_estimable' and np.isnan(result['top20_overlap'])


def test_topk_ties_are_lexical_and_agreement_hand_computed():
    labels = np.array(['C','A','B','D'])
    assert labels[top_indices(np.array([1,1,1,0]),labels,2)].tolist() == ['A','B']
    result = compare(np.array([4,3,2,1]), np.array([1,2,3,4]), labels,2)
    assert result['top20_overlap'] == 0
    assert np.isclose(result['rank_spearman'],-1)
    assert result['max_rank_change'] == 3


def fixture():
    evidence = pd.DataFrame({'evidence_id':['a','b'], 'doi':['doi1','doi2'],
        'split_group':['dev','held'], 'partition':['development','excluded_not_pristine_test'],
        'outcome':['MHCII','MHCII'], 'quantitative':[True,True],
        'eligible_direct_T_function_ranking':[False,False], 'gene_id':['HGNC:1','HGNC:2'],
        'effect_size':[1.,2.]})
    ranks = pd.DataFrame({'source_ids':['a'], 'endpoint':['MHCII'], 'gene_id':['HGNC:1']})
    return evidence,ranks


def test_leakage_audit_rejects_excluded_outcomes_and_wrong_endpoint():
    e,r = fixture()
    assert audit(e,r)['eligible_independent_records'] == 0
    r.loc[0,'source_ids'] = 'b'
    with pytest.raises(ValueError,match='Excluded'):
        audit(e,r)
    r.loc[0,'source_ids'] = 'a'
    r.loc[0,'endpoint'] = 'PDL1'
    with pytest.raises(ValueError,match='Endpoint'):
        audit(e,r)


def test_real_patient_draws_and_no_fabricated_metrics():
    draws = pd.read_csv(ROOT/'results/phase4_bootstrap_draws.csv')
    patients = set(pd.read_csv(ROOT/'results/patient_features.csv').patient_id)
    assert len(draws)==300
    rng = np.random.default_rng(20261116)
    ordered = pd.read_csv(ROOT/'results/patient_features.csv').patient_id.to_numpy()
    for row in draws.itertuples():
        observed = row.sampled_patient_ids.split('|')
        assert len(observed)==11 and set(observed)<=patients
        assert len(set(observed))==row.unique_patients
        assert observed==ordered[rng.integers(0,11,size=11)].tolist()
    metrics = pd.read_csv(ROOT/'results/evaluation_metrics.csv')
    assert len(metrics)==12
    assert metrics[['estimate','ci_lower','ci_upper']].isna().all().all()
    assert metrics.status.eq('not_estimable').all() and metrics.test_studies.eq(0).all()
    r = pd.read_csv(ROOT/'results/phase4_rank_resampling.csv')
    assert len(r)==3*5155
    assert r.rank_q025.le(r.rank_median).all() and r.rank_median.le(r.rank_q975).all()
    assert r.top20_frequency_all_draws.between(0,1).all()
    assert r.groupby('endpoint').top20_count.sum().eq(300*20).all()
