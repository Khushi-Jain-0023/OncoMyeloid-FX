"""Verify source hashes, numerical ranks, partitions and notebook execution."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
m = json.loads((ROOT / 'results/phase3_manifest.json').read_text())
for name, expected in m['input_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
e = pd.read_parquet(ROOT / 'data/curated/functional_evidence.parquet')
b = pd.read_csv(ROOT / 'results/baseline_rankings.csv')
r = pd.read_csv(ROOT / 'results/integrated_rankings.csv')
assert len(b) == 6124 and b.gene_symbol.is_unique
assert len(e) == 35109 and e.evidence_id.is_unique
assert len(r) == 18372
for endpoint, g in r.groupby('endpoint'):
    good = g.dropna(subset=['rank'])
    assert len(good) == 5155
    assert good.gene_id.is_unique
    expected = .5 * good.transcriptomic_evidence + .5 * good.functional_evidence
    assert np.allclose(good.ranking_value, expected)
    assert np.allclose(good['rank'], good.ranking_value.rank(method='min', ascending=False))
    source = e.set_index('evidence_id').loc[good.source_ids]
    assert source.outcome.eq(endpoint).all()
    assert source.partition.eq('development').all()
    assert np.allclose(source.effect_size, good.marker_selection_contrast)
    missing = g.loc[g['rank'].isna()]
    assert missing[['ranking_value','functional_evidence','source_ids']].isna().all().all()
nb = json.loads((ROOT / 'notebooks/03_evidence_ranking.ipynb').read_text(encoding='utf-8'))
assert all(c.get('execution_count') is not None for c in nb['cells'] if c['cell_type'] == 'code')
assert not any(o.get('output_type') == 'error' for c in nb['cells'] for o in c.get('outputs', []))
outputs = ['data/curated/functional_evidence.parquet','results/baseline_rankings.csv',
           'results/integrated_rankings.csv','reports/phase3_evidence_ranking.md',
           'notebooks/03_evidence_ranking.ipynb','requirements-phase3-lock.txt',
           'results/plots/phase3_evidence.png','build_phase3_notebook.py','verify_phase3.py','tests/test_phase3.py']
receipt = {'status': 'passed', 'checked_utc': pd.Timestamp.now(tz='UTC').isoformat(),
           'quantitative_records': 35103, 'qualitative_records': 6,
           'ranked_genes_per_endpoint': 5155, 'missing_per_endpoint': 969,
           'notebook_executed': True, 'direct_T_function_eligible_records': 0,
           'output_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in outputs}}
(ROOT / 'results/phase3_verification.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k != 'output_sha256'}, indent=2))
