"""Append data-dependent QC and robustness diagnostics to the generated report."""
from pathlib import Path
import json, hashlib, importlib.metadata
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent; R=ROOT/'results'
c=pd.read_csv(R/'transcriptomic_candidates.csv'); s=pd.read_csv(R/'sensitivity_models.csv'); f=pd.read_csv(R/'patient_features.csv'); q=pd.read_csv(R/'qc_summary.csv')
rows=[]
for name,g in s.groupby('analysis'):
    joined=c[['gene_symbol','association_effect']].merge(g,on='gene_symbol')
    valid=joined[['association_effect','effect']].dropna()
    rows.append({'analysis':name,'patient_n':int(g.patient_n.iloc[0]),'estimable_genes':int(g.effect.notna().sum()),'fdr_005':int(g.fdr.lt(.05).sum()),'effect_spearman':valid.corr(method='spearman').iloc[0,1] if len(valid)>2 else np.nan,'same_sign_fraction':float(np.mean(np.sign(valid.association_effect)==np.sign(valid.effect))) if len(valid) else np.nan})
d=pd.DataFrame(rows); d.to_csv(R/'sensitivity_summary.csv',index=False)
lines=['','## Run-specific QC and sensitivity findings',f'- Source QC retained {int(q.qc_pass.sum()):,}/{int(q.input_cells.sum()):,} cells; Scrublet flagged {int(q.doublets.sum()):,} cells across the included captures.',f'- Final macrophages per patient: {int(f.macrophages.min())}–{int(f.macrophages.max())}; T cells: {int(f.T_cells.min())}–{int(f.T_cells.max())}.',f'- Standardized within-state models use {int(c.within_state_patient_n.min())} patients with both states. Missing states are not assigned zero expression.',f'- Unique HGNC IDs mapped: {int(c.gene_id.notna().sum())}/{len(c)}; source symbols retained for all genes.','', '| Sensitivity | Patients | Estimable genes | FDR < .05 | Effect rank correlation with primary |','|---|---:|---:|---:|---:|']
for r in d.itertuples():lines.append(f'| {r.analysis} | {r.patient_n} | {r.estimable_genes} | {r.fdr_005} | {r.effect_spearman:.3f} |')
lines+=['','The sex-adjusted HC3 model is not estimable if the single female patient has leverage one; such results are missing, not negative findings. Cytotoxicity is a different endpoint, so low correlation there is not itself a failed robustness test. All sensitivity FDR families are separate and exploratory. Large shifts under QC/composition changes indicate fragility, not evidence favoring the most significant variant.','', '## Annotation and missing-state checks','Published broad T labels include unresolved and NK subtype labels; strict_T_annotation excludes them. CD8 sensitivity requires at least 20 retained cells per patient. Alveolar macrophages are absent for one source sample and sparse in others; within-state summaries may be noisy even when defined. Marker heatmaps are consistency checks on the source labels only.']
p=ROOT/'reports/transcriptomic_baseline.md'
text=p.read_text(encoding='utf-8').split('\n## Run-specific QC')[0].replace('eight sensitivity analyses','nine sensitivity analyses').replace('**1 genes**','**1 gene**')
hits=c.loc[c.composition_adjusted_fdr.lt(.05)]
lines+=['', '## Secondary composition-adjusted findings']
for hit in hits.itertuples():
    lines.append(f'{hit.gene_symbol}: composition-adjusted FDR {hit.composition_adjusted_fdr:.6g}, primary FDR {hit.fdr:.6g}. This model-dependent association is exploratory and is not independent validation or evidence of causality.')
p.write_text(text+'\n'+'\n'.join(lines),encoding='utf-8')
m=json.loads((R/'run_manifest.json').read_text())
m['packages']['scikit-learn']=importlib.metadata.version('scikit-learn')
for name in ['work/hgnc_complete_set.txt','reports/phase2_protocol.md','build_notebook.py','summarize_phase2.py','verify_phase2.py']:
    m['source_sha256'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
(R/'run_manifest.json').write_text(json.dumps(m,indent=2))
print(d.to_string(index=False))
