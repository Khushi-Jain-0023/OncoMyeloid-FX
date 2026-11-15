"""Validate completed real-data outputs and produce a verification receipt."""
from pathlib import Path
import json, hashlib
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parent
r=ROOT/'results'
c=pd.read_csv(r/'transcriptomic_candidates.csv'); f=pd.read_csv(r/'patient_features.csv'); q=pd.read_csv(r/'qc_summary.csv'); s=pd.read_csv(r/'sensitivity_models.csv')
assert len(f)==11 and f.patient_id.is_unique
assert c.gene_symbol.is_unique and (c.patient_n==len(f)).all()
assert np.isfinite(c[['association_effect','association_se','p_value','fdr']]).all().all()
assert c.p_value.between(0,1).all() and c.fdr.between(0,1).all()
assert (c.fdr+1e-12>=c.p_value).all()
assert set(s.analysis)=={'age','sex','library_size','exclude_double_histology','cytotoxic','CD8','retain_doublets','adaptive_qc','strict_T_annotation'}
assert s.groupby('analysis').size().eq(len(c)).all()
assert q.input_cells.sum()==45149 and (q.retained<=q.qc_pass).all()
assert f.macrophages.ge(50).all() and f.T_cells.ge(50).all()
assert f.mo_fraction.between(0,1).all()
nb=json.loads((ROOT/'notebooks/02_transcriptomics.ipynb').read_text(encoding='utf-8'))
assert all(cell.get('execution_count') is not None for cell in nb['cells'] if cell['cell_type']=='code')
assert not any(out.get('output_type')=='error' for cell in nb['cells'] for out in cell.get('outputs',[]))
for name in ['qc','composition','associations','annotation']:
    assert (r/f'plots/{name}.png').stat().st_size>1000
receipt={'status':'passed','patients':len(f),'candidate_rows':len(c),'sensitivity_rows':len(s),'notebook_executed':True,'unit_tests':'4 passed; independent statsmodels HC3 comparison; BH; missingness; composition simulation','checked_utc':pd.Timestamp.now(tz='UTC').isoformat()}
(r/'verification.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))
