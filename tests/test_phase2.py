import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from phase2 import regress, bh

def test_hc3_matches_independent_statsmodels():
    rng=np.random.default_rng(42); x=rng.normal(size=(11,4)); y=rng.normal(size=11); cov=rng.normal(size=(11,1))
    b,se,p=regress(x,y,cov)
    yy=(y-y.mean())/y.std(ddof=1)
    for j in range(4):
        z=(x[:,j]-x[:,j].mean())/x[:,j].std(ddof=1)
        model=sm.OLS(yy,np.column_stack([np.ones(11),z,(cov-cov.mean())/cov.std()])).fit(cov_type='HC3',use_t=True)
        np.testing.assert_allclose([b[j],se[j],p[j]],[model.params[1],model.bse[1],model.pvalues[1]],rtol=1e-9)

def test_bh_and_missingness():
    p=np.array([.01,.3,.04,np.nan,.001]); q=bh(p)
    np.testing.assert_allclose(q[np.isfinite(p)],multipletests(p[np.isfinite(p)],method='fdr_bh')[1])
    assert np.isnan(q[3])

def test_constant_and_small_samples_not_invented():
    b,se,p=regress(np.ones((11,2)),np.arange(11))
    assert np.isnan(b).all() and np.isnan(p).all()
    b,se,p=regress(np.arange(5),np.arange(5))
    assert np.isnan(b).all()

def test_composition_and_within_state_separation():
    p=np.array([[.1,.9],[.5,.5],[.9,.1]])
    mu=np.tile(np.array([[[1.],[4.]]]),(3,1,1))
    total=(p[:,:,None]*mu).sum(axis=1)
    within=(p.mean(axis=0)[None,:,None]*mu).sum(axis=1)
    comp=p@mu.mean(axis=0)
    np.testing.assert_allclose(total,comp)
    assert np.std(within)==0
    fixed=np.tile([.5,.5],(3,1)); changing=mu+np.arange(3)[:,None,None]
    total=(fixed[:,:,None]*changing).sum(axis=1)
    within=(fixed.mean(axis=0)[None,:,None]*changing).sum(axis=1)
    np.testing.assert_allclose(total,within)
