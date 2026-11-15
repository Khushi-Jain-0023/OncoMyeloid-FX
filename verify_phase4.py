"""Verify real Phase 4 results, source hashes and executed notebook."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
R = ROOT / 'results'
m = json.loads((R/'phase4_manifest.json').read_text())
for name, expected in m['input_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, name
assert m['decision']['decision']=='inconclusive'
assert m['decision']['eligible_independent_records']==0
assert m['patients']==11 and m['genes']==6124 and m['bootstrap_draws']==300
metrics = pd.read_csv(R/'evaluation_metrics.csv')
assert len(metrics)==12 and metrics.status.eq('not_estimable').all()
assert metrics[['estimate','ci_lower','ci_upper']].isna().all().all()
a = pd.read_csv(R/'phase4_ablation_metrics.csv')
assert len(a)==45 and a.groupby('endpoint').comparison.nunique().eq(15).all()
unavailable = a.comparison.isin(['sex','exclude_indirect','leave_development_family_out'])
assert a.loc[unavailable,'common_genes'].eq(0).all()
assert a.loc[unavailable,['rank_spearman','top20_overlap']].isna().all().all()
loo = pd.read_csv(R/'phase4_leave_patient_out.csv')
assert len(loo)==33 and loo.groupby('endpoint').omitted_patient.nunique().eq(11).all()
assert loo.rank_spearman.between(-1,1).all() and loo.top20_overlap.between(0,20).all()
r = pd.read_csv(R/'phase4_rank_resampling.csv')
assert len(r)==15465 and r.groupby('endpoint').gene_symbol.nunique().eq(5155).all()
assert r.valid_draws.between(0,300).all() and r.groupby('endpoint').top20_count.sum().eq(6000).all()
assert r.rank_q025.le(r.rank_median).all() and r.rank_median.le(r.rank_q975).all()
assert r.rank_q025.ge(1).all() and r.rank_q975.le(5155).all()
assert np.allclose(r.top20_frequency_all_draws,r.top20_count/300)
nb=json.loads((ROOT/'notebooks/04_benchmark_robustness.ipynb').read_text(encoding='utf-8'))
assert all(c.get('execution_count') is not None for c in nb['cells'] if c['cell_type']=='code')
assert not any(o.get('output_type')=='error' for c in nb['cells'] for o in c.get('outputs',[]))
files = list(R.glob('phase4_*.csv'))+[R/'evaluation_metrics.csv',ROOT/'reports/benchmark.md',
    ROOT/'reports/leakage_audit.md',ROOT/'notebooks/04_benchmark_robustness.ipynb',
    ROOT/'build_phase4_notebook.py',ROOT/'verify_phase4.py',ROOT/'tests/test_phase4.py',
    R/'plots/phase4_ablations.png',R/'plots/phase4_rank_ranges.png']
receipt={'status':'passed','decision':'inconclusive','checked_utc':pd.Timestamp.now(tz='UTC').isoformat(),
    'bootstrap_draws':300,'ablation_comparisons':45,'leave_patient_out_comparisons':33,
    'rank_uncertainty_rows':15465,'notebook_executed':True,
    'output_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(R/'phase4_verification.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k!='output_sha256'},indent=2))
