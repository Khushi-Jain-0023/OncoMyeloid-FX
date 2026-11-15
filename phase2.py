"""Reproducible descriptive analysis; run from repository root with Python 3.11."""
from pathlib import Path
import argparse, gzip, hashlib, json, sys, platform, importlib.metadata, time
import zipfile, xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from scipy import sparse, stats
import anndata as ad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT/'configs/phase2.json').read_text())
OUT = ROOT/'results'
for folder in [OUT, OUT/'plots', ROOT/'data/curated', ROOT/'notebooks']:
    folder.mkdir(parents=True, exist_ok=True)

def log(message):
    print(time.strftime('%H:%M:%S'), message, flush=True)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024), b''): h.update(block)
    return h.hexdigest()

def metadata():
    # Source workbook has malformed custom properties; parse its actual worksheet unchanged.
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(ROOT/'work/sample_metadata.xlsx') as z:
        ss=ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings=[''.join(e.itertext()) for e in ss]
        sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        parsed=[]
        for row in sheet.findall('.//s:sheetData/s:row',ns):
            number=int(row.attrib['r'])
            if not 3<=number<=61:continue
            vals={}
            for cell in row:
                v=cell.find('s:v',ns); text='' if v is None else v.text
                vals[''.join(c for c in cell.attrib['r'] if c.isalpha())]=strings[int(text)] if cell.attrib.get('t')=='s' else text
            parsed.append(vals)
        m=pd.DataFrame(parsed[1:]).rename(columns=parsed[0])
    m.columns=m.columns.str.strip()
    m=m.rename(columns={'Samples':'Sample','Patient id':'patient_id','Tissue origins':'tissue','Histology':'histology','Age':'age','Sex':'sex','No. of single-cells':'source_cells'})
    m['age']=pd.to_numeric(m.age); m['source_cells']=pd.to_numeric(m.source_cells)
    m=m[['Sample','patient_id','tissue','histology','sex','age','source_cells']]
    assert m.Sample.is_unique and m.patient_id.nunique()==44
    m.to_csv(OUT/'sample_metadata.csv',index=False)
    return m.set_index('Sample')

def ingest():
    target=ROOT/'data/curated/primary_counts.h5ad'
    if target.exists():
        log('Using parsed count cache'); return ad.read_h5ad(target)
    ann=pd.read_csv(ROOT/'work/GSE131907_cell_annotation.txt.gz',sep='\t',index_col=0,keep_default_na=False)
    m=metadata()
    genes=[]; values=[]; indices=[]; ptr=[0]
    with gzip.open(ROOT/'work/umi_matrix.txt.gz','rt') as f:
        cells=f.readline().rstrip('\n').split('\t')[1:]
        assert len(cells)==len(set(cells))==208506
        assert set(cells)==set(ann.index)
        sel=np.array([i for i,c in enumerate(cells) if ann.loc[c,'Sample'].startswith(CFG['sample_prefix'])])
        obs=ann.loc[np.array(cells)[sel]].copy()
        for j,line in enumerate(f):
            gene,text=line.rstrip('\n').split('\t',1)
            a=np.fromstring(text,sep='\t',dtype=np.int32)
            if a.size!=len(cells) or (a<0).any(): raise ValueError(f'Malformed counts: {gene}')
            a=a[sel]; nz=np.flatnonzero(a)
            genes.append(gene); indices.append(nz.astype(np.int32)); values.append(a[nz]); ptr.append(ptr[-1]+len(nz))
            if j%3000==0: log(f'Parsed {j} genes')
    assert len(genes)==len(set(genes))
    x=sparse.csr_matrix((np.concatenate(values),np.concatenate(indices),np.array(ptr)),shape=(len(genes),len(sel))).T.tocsr()
    obs=obs.join(m,on='Sample',rsuffix='_metadata')
    obs['sex_male']=(obs.sex=='Male').astype(int)
    assert obs.patient_id.notna().all() and obs.patient_id.nunique()==11
    a=ad.AnnData(x,obs=obs,var=pd.DataFrame(index=pd.Index(genes,name='gene_symbol')))
    temp=target.with_suffix('.tmp.h5ad'); a.write_h5ad(temp,compression='gzip'); temp.replace(target); log(f'Counts saved: {a.shape}; nnz={a.X.nnz}')
    return a

def qc(a):
    a.obs['total_umi']=np.asarray(a.X.sum(axis=1)).ravel()
    a.obs['detected_genes']=np.asarray((a.X>0).sum(axis=1)).ravel()
    a.obs['mito_fraction']=np.asarray(a.X[:,a.var_names.str.startswith('MT-')].sum(axis=1)).ravel()/a.obs.total_umi.clip(lower=1)
    q=CFG['qc']; o=a.obs
    o['qc_pass']=o.detected_genes.between(q['min_genes'],q['max_genes']) & o.total_umi.between(q['min_umi'],q['max_umi']) & (o.mito_fraction<=q['max_mito_fraction'])
    o['adaptive_pass']=o.qc_pass.copy()
    thresholds=[]
    for sample,g in o.groupby('Sample',observed=True):
        lg=np.log1p(g.detected_genes); mt=g.mito_fraction
        low=np.median(lg)-3*np.median(np.abs(lg-np.median(lg)))
        high=np.median(mt)+3*np.median(np.abs(mt-np.median(mt)))
        o.loc[g.index,'adaptive_pass'] &= (lg>=low)&(mt<=high)
        thresholds.append({'sample':sample,'log1p_genes_lower':low,'mito_upper':high})
    pd.DataFrame(thresholds).to_csv(OUT/'adaptive_qc_thresholds.csv',index=False)
    doublet=OUT/'doublet_calls.csv'
    if doublet.exists():
        d=pd.read_csv(doublet,index_col=0); assert set(d.index)==set(o.index)
        o['doublet_score']=d.loc[o.index,'doublet_score']; o['predicted_doublet']=d.loc[o.index,'predicted_doublet'].astype(bool)
    else:
        import scanpy as sc
        o['doublet_score']=np.nan; o['predicted_doublet']=False
        for sample in sorted(o.Sample.unique()):
            log(f'Scrublet {sample}')
            take=(o.Sample==sample)&o.qc_pass
            b=a[take].copy()
            sc.pp.scrublet(b,expected_doublet_rate=CFG['doublet_expected_rate'],n_prin_comps=30,use_approx_neighbors=False,random_state=CFG['seed'],verbose=False)
            o.loc[b.obs_names,'doublet_score']=b.obs.doublet_score
            o.loc[b.obs_names,'predicted_doublet']=b.obs.predicted_doublet
        o[['doublet_score','predicted_doublet']].to_csv(doublet)
    o['retained']=o.qc_pass & ~o.predicted_doublet
    o.to_csv(OUT/'cell_qc_annotations.csv.gz',compression='gzip')
    summary=o.groupby('Sample',observed=True).agg(input_cells=('Sample','size'),qc_pass=('qc_pass','sum'),doublets=('predicted_doublet','sum'),retained=('retained','sum'),median_umi=('total_umi','median'),median_genes=('detected_genes','median'),median_mito=('mito_fraction','median'))
    summary.to_csv(OUT/'qc_summary.csv')
    return a

def bh(p):
    p=np.asarray(p); q=np.full(p.shape,np.nan); ok=np.isfinite(p); v=p[ok]; order=np.argsort(v)
    corrected=np.minimum.accumulate((v[order]*len(v)/np.arange(1,len(v)+1))[::-1])[::-1]
    tmp=np.empty(len(v)); tmp[order]=np.minimum(corrected,1); q[ok]=tmp
    return q

def regress(x,y,cov=None):
    """Columnwise standardized OLS with HC3 SE; missing rows handled by caller."""
    x=np.asarray(x,float); y=np.asarray(y,float)
    if x.ndim==1:x=x[:,None]
    n,g=x.shape; beta=np.full(g,np.nan); se=beta.copy(); p=beta.copy()
    for j in range(g):
        z=x[:,j]; good=np.isfinite(z)&np.isfinite(y)
        if cov is not None:good &= np.isfinite(cov).all(axis=1)
        z=z[good]; yy=y[good]; nn=len(z)
        if nn<6 or np.std(z,ddof=1)<1e-12 or np.std(yy,ddof=1)<1e-12:continue
        z=(z-z.mean())/z.std(ddof=1); yy=(yy-yy.mean())/yy.std(ddof=1)
        X=np.column_stack([np.ones(nn),z])
        if cov is not None:
            cc=cov[good]; cc=cc[:,np.std(cc,axis=0)>1e-12]
            if cc.size:X=np.column_stack([X,(cc-cc.mean(axis=0))/cc.std(axis=0)])
        if np.linalg.matrix_rank(X)<X.shape[1] or nn-X.shape[1]<3:continue
        inv=np.linalg.inv(X.T@X); b=inv@X.T@yy; e=yy-X@b
        h=np.sum((X@inv)*X,axis=1)
        if (h>=0.999999).any():continue
        V=inv@(X.T@(((e/(1-h))**2)[:,None]*X))@inv
        beta[j]=b[1]; se[j]=np.sqrt(max(V[1,1],0)); p[j]=2*stats.t.sf(abs(b[1]/se[j]),nn-X.shape[1]) if se[j]>0 else np.nan
    return beta,se,p

def aggregate(a, mask, logx, strict_t=False):
    o=a.obs; samples=sorted(o.Sample.unique()); rows=[]; xs=[]; within=[]; mus=[]; props=[]
    lookup={g:i for i,g in enumerate(a.var_names)}
    def score(idx,panel):return float(np.asarray(logx[idx][:,[lookup[g] for g in panel if g in lookup]].mean(axis=1)).mean()) if len(idx) else np.nan
    for sample in samples:
        ix=np.flatnonzero(mask & (o.Sample==sample).to_numpy())
        sub=o.iloc[ix]; mac=ix[sub.Cell_subtype.isin(['Alveolar Mac','mo-Mac'])]; tc=ix[sub.Cell_type=='T lymphocytes']
        if strict_t: tc=ix[(sub.Cell_type=='T lymphocytes') & ~sub.Cell_subtype.isin(['NA','NK','Undetermined'])]
        if len(mac)<CFG['min_macrophages'] or len(tc)<CFG['min_t_cells']:continue
        states=[ix[sub.Cell_subtype==s] for s in ['Alveolar Mac','mo-Mac']]
        mu=np.vstack([np.asarray(logx[s].mean(axis=0)).ravel() if len(s) else np.full(a.n_vars,np.nan) for s in states])
        prop=np.array([len(s)/len(mac) for s in states]); mus.append(mu); props.append(prop)
        xs.append(np.asarray(logx[mac].mean(axis=0)).ravel())
        cd8=ix[sub.Cell_subtype.isin(['Naive CD8+ T','Cytotoxic CD8+ T','Exhausted CD8+ T'])]
        rows.append({'sample':sample,'patient_id':sub.patient_id.iloc[0],'macrophages':len(mac),'T_cells':len(tc),'CD8_cells':len(cd8),'mo_fraction':prop[1],'t_inhibitory':score(tc,CFG['signatures']['t_inhibitory']),'cd8_inhibitory':score(cd8,CFG['signatures']['t_inhibitory']),'t_cytotoxic':score(tc,CFG['signatures']['t_cytotoxic']),'mac_lipid':score(mac,CFG['signatures']['mac_lipid']),'mac_antigen':score(mac,CFG['signatures']['mac_antigen']),'age':sub.age.iloc[0],'sex_male':sub.sex_male.iloc[0],'double_histology':'Double' in sub.histology.iloc[0],'log_mac_umi':np.log1p(o.iloc[mac].total_umi).mean()})
    frame=pd.DataFrame(rows); mu=np.array(mus); prop=np.array(props)
    std=np.sum(mu*prop.mean(axis=0)[None,:,None],axis=1)
    comp=prop@np.nanmean(mu,axis=0)
    return frame,np.array(xs),std,comp

def analyze(a):
    o=a.obs; mask=o.retained.to_numpy()
    norm=sparse.diags(CFG['normalization_total']/o.total_umi.to_numpy().clip(1))@a.X
    norm=norm.tocsr().astype(np.float32); norm.data=np.log1p(norm.data)
    panel_genes=set(sum(CFG['signatures'].values(),[])+sum(CFG['annotation_markers'].values(),[]))
    present={k:[g for g in v if g in a.var_names] for k,v in CFG['signatures'].items()}
    assert all(len(v)>=3 for v in present.values())
    (OUT/'signature_coverage.json').write_text(json.dumps(present,indent=2))
    f,x,within,comp=aggregate(a,mask,norm); assert f.patient_id.is_unique
    f.to_csv(OUT/'patient_features.csv',index=False)
    mac=mask&o.Cell_subtype.isin(['Alveolar Mac','mo-Mac']).to_numpy()
    det=np.asarray((a.X[mac]>0).mean(axis=0)).ravel()
    eligible=(det>=CFG['candidate_min_detection'])&((x>0).sum(axis=0)>=6)&(x.std(axis=0)>1e-8)&~a.var_names.isin(panel_genes)&~a.var_names.str.match('^(MT-|RPL|RPS)')
    ids=np.flatnonzero(eligible); names=a.var_names[ids]; xx=x[:,ids]; y=f.t_inhibitory.to_numpy()
    b,se,p=regress(xx,y); bc,sc,pc=regress(xx,y,f[['mo_fraction']].to_numpy()); bw,sw,pw=regress(within[:,ids],y)
    result=pd.DataFrame({'gene_id':'','gene_symbol':names,'cohort_id':CFG['cohort'],'patient_n':len(f),'macrophage_programme':'gene_mean_log1p_10k','t_cell_programme':'t_inhibitory','association_effect':b,'association_se':se,'p_value':p,'fdr':bh(p),'composition_adjusted_effect':bc,'composition_adjusted_p':pc,'composition_adjusted_fdr':bh(pc),'within_state_effect':bw,'within_state_p':pw,'within_state_fdr':bh(pw),'detection_fraction':det[ids],'model_id':'patient_OLS_HC3_v1'})
    result['within_state_patient_n']=np.isfinite(within[:,ids]).sum(axis=0)
    hgnc=ROOT/'work/hgnc_complete_set.txt'
    if hgnc.exists():
        mapping=pd.read_csv(hgnc,sep='\t',dtype=str).drop_duplicates('symbol',keep=False).set_index('symbol').hgnc_id
        result['gene_id']=result.gene_symbol.map(mapping).fillna('')
    loo=[]
    for i in range(len(f)):
        keep=np.arange(len(f))!=i; bb,_,_=regress(xx[keep],y[keep]); loo.append(bb)
    loo=np.array(loo); result['loo_effect_min']=np.nanmin(loo,axis=0); result['loo_effect_max']=np.nanmax(loo,axis=0); result['loo_sign_fraction']=np.mean(np.sign(loo)==np.sign(b)[None,:],axis=0)
    result.sort_values(['fdr','p_value']).to_csv(OUT/'transcriptomic_candidates.csv',index=False)
    pd.DataFrame(loo.T,index=names,columns=['omit_'+p for p in f.patient_id]).to_csv(OUT/'leave_one_patient_out.csv')
    sensitivity=[]
    for label,cov,end,take in [('age',f[['age']].to_numpy(),y,np.ones(len(f),bool)),('sex',f[['sex_male']].to_numpy(),y,np.ones(len(f),bool)),('library_size',f[['log_mac_umi']].to_numpy(),y,np.ones(len(f),bool)),('exclude_double_histology',None,y,~f.double_histology.to_numpy()),('cytotoxic',None,f.t_cytotoxic.to_numpy(),np.ones(len(f),bool)),('CD8',None,f.cd8_inhibitory.to_numpy(),f.CD8_cells.to_numpy()>=20)]:
        bb,ss,pp=regress(xx[take],end[take],None if cov is None else cov[take]); sensitivity.append(pd.DataFrame({'gene_symbol':names,'analysis':label,'patient_n':int(take.sum()),'effect':bb,'se':ss,'p_value':pp,'fdr':bh(pp)}))
    for label,other in [('retain_doublets',o.qc_pass.to_numpy()),('adaptive_qc',(o.adaptive_pass&~o.predicted_doublet).to_numpy()),('strict_T_annotation',mask)]:
        ff,xxx,_,_=aggregate(a,other,norm,strict_t=(label=='strict_T_annotation')); bb,ss,pp=regress(xxx[:,ids],ff.t_inhibitory.to_numpy()); sensitivity.append(pd.DataFrame({'gene_symbol':names,'analysis':label,'patient_n':len(ff),'effect':bb,'se':ss,'p_value':pp,'fdr':bh(pp)}))
    pd.concat(sensitivity).to_csv(OUT/'sensitivity_models.csv',index=False)
    pd.DataFrame(x[:,ids],index=f.patient_id,columns=names).to_csv(OUT/'patient_macrophage_expression.csv')
    # Exact descriptive decomposition: S = composition + within - reference + interaction.
    pd.DataFrame({'gene_symbol':names,'between_patient_sd_total':x[:,ids].std(axis=0,ddof=1),'sd_composition_only':comp[:,ids].std(axis=0,ddof=1),'sd_standardized_within':np.nanstd(within[:,ids],axis=0,ddof=1),'sd_interaction':np.nanstd(x[:,ids]-comp[:,ids]-within[:,ids],axis=0,ddof=1),'complete_state_patients':np.isfinite(within[:,ids]).sum(axis=0)}).to_csv(OUT/'composition_decomposition.csv',index=False)
    # Annotation diagnostics on the same data: explicitly not independent validation.
    markers=list(dict.fromkeys(sum(CFG['annotation_markers'].values(),[]))); mid=[a.var_names.get_loc(g) for g in markers if g in a.var_names]; markers=[a.var_names[j] for j in mid]
    profiles=[]
    for subtype in sorted(o.loc[mask,'Cell_subtype'].unique()):
        ix=mask&(o.Cell_subtype==subtype).to_numpy(); vals=np.asarray(norm[ix][:,mid].mean(axis=0)).ravel(); profiles.append(pd.Series(vals,index=markers,name=subtype))
    profiles=pd.DataFrame(profiles); profiles.to_csv(OUT/'annotation_marker_means.csv')
    plot(a,f,result,profiles,x,ids)
    run={'cohort':CFG['cohort'],'input_cells':a.n_obs,'genes':a.n_vars,'retained_cells':int(mask.sum()),'patients':len(f),'tested_genes':len(result),'primary_fdr_005':int((result.fdr<.05).sum()),'composition_fdr_005':int((result.composition_adjusted_fdr<.05).sum()),'gene_ids_mapped':int(result.gene_id.ne('').sum()),'config':CFG,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'work/umi_matrix.txt.gz',ROOT/'work/sample_metadata.xlsx',ROOT/'work/GSE131907_cell_annotation.txt.gz',ROOT/'configs/phase2.json',Path(__file__)]},'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','anndata','scanpy','statsmodels','matplotlib']},'timestamp_utc':pd.Timestamp.now(tz='UTC').isoformat()}
    (OUT/'run_manifest.json').write_text(json.dumps(run,indent=2)); report(run,result,f)
    a.obs['analysis_retained']=mask; a.write_h5ad(ROOT/'data/curated/primary_qc.h5ad',compression='gzip')

def plot(a,f,r,profiles,x,ids):
    plt.rcParams.update({'figure.dpi':130,'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,3,figsize=(12,4))
    for ax,col in zip(axs,['total_umi','detected_genes','mito_fraction']):
        data=[g[col].to_numpy() for _,g in a.obs.groupby('Sample',observed=True)]; ax.boxplot(data,showfliers=False); ax.set_title(col); ax.set_xlabel('Sample (alphabetical)')
    fig.suptitle('Primary lung cohort: deposited-cell QC distributions'); fig.tight_layout(); fig.savefig(OUT/'plots/qc.png'); plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4)); axs[0].bar(f.patient_id,1-f.mo_fraction,label='Alveolar Mac'); axs[0].bar(f.patient_id,f.mo_fraction,bottom=1-f.mo_fraction,label='mo-Mac'); axs[0].tick_params(axis='x',rotation=60); axs[0].set_ylabel('Fraction of retained macrophages'); axs[0].legend(fontsize=8)
    axs[1].scatter(f.mo_fraction,f.t_inhibitory); [axs[1].annotate(p,(x,y),fontsize=7) for p,x,y in zip(f.patient_id,f.mo_fraction,f.t_inhibitory)]; axs[1].set(xlabel='mo-Mac fraction',ylabel='T inhibitory expression proxy'); fig.tight_layout(); fig.savefig(OUT/'plots/composition.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4)); ax.scatter(r.association_effect,-np.log10(r.p_value.clip(lower=1e-30)),s=6,alpha=.4); ax.set(xlabel='Standardized patient association',ylabel='-log10 unadjusted p',title='Exploratory associations; BH FDR reported in table'); fig.tight_layout(); fig.savefig(OUT/'plots/associations.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,8)); im=ax.imshow(profiles,aspect='auto',cmap='viridis'); ax.set_xticks(range(len(profiles.columns)),profiles.columns,rotation=90); ax.set_yticks(range(len(profiles)),profiles.index); fig.colorbar(im,ax=ax,label='Mean log1p counts per 10k'); ax.set_title('Published annotation consistency (not independent validation)'); fig.tight_layout(); fig.savefig(OUT/'plots/annotation.png'); plt.close(fig)

def report(run,r,f):
    top=r.sort_values('p_value').head(10)
    lines=['# Descriptive transcriptomic baseline','',f"Analyzed {run['patients']} primary lung-tumor patients; {run['input_cells']:,} deposited cells, {run['retained_cells']:,} retained after QC/doublet assessment; {run['tested_genes']:,} eligible macrophage genes.",'',f"Primary BH FDR <0.05: **{run['primary_fdr_005']} genes**. Composition-adjusted BH FDR <0.05: **{run['composition_fdr_005']} genes**.",'','## Interpretation','These are exploratory patient-level expression associations, not measured immune suppression, gene causality, target validation or predictive performance. Small patient count limits power and covariate adjustment. Candidate order reflects statistical evidence only; functional outcomes were not used.','', '## Leading unadjusted associations','| Gene | Effect | p | FDR | Composition-adjusted effect | LOO sign fraction |','|---|---:|---:|---:|---:|---:|']
    for row in top.itertuples():lines.append(f'| {row.gene_symbol} | {row.association_effect:.3f} | {row.p_value:.3g} | {row.fdr:.3g} | {row.composition_adjusted_effect:.3f} | {row.loo_sign_fraction:.2f} |')
    lines+=['','## Methods and reproducibility','See phase2_protocol.md and configs/phase2.json for prespecified signatures, QC, candidate filters, denominator and inference. Run `python phase2.py` from the project. Counts are streamed into a sparse primary-lung cache. The complete deposited matrix is parsed and gzip integrity checked during ingestion. Sample/patient mapping uses the source workbook. results/run_manifest.json records hashes, software and configuration.','', '## Limitations','Published cell labels are retained and marker consistency is inspected on the same data; this is not independent validation. Source preprocessing and prior filtering cannot be undone. Scrublet is a probabilistic screen with assumed 5% rate, not verified doublet truth. Patient and capture batch are confounded; no study integration is applied. Separate age/sex/library-size sensitivity models avoid a highly parameterized model. All-T-cell scores include subtype-composition variation; CD8-restricted and cytotoxic sensitivities are separate. Missing genes are reported in signature coverage; unresolved stable IDs stay blank. Single cohort cannot establish generalization.','', '## Outputs','Candidate table, eight sensitivity analyses, leave-one-patient-out effects, per-patient expression/features, cell QC and doublet calls, marker diagnostics, composition decomposition and four figures are in results/. Primary and QC-annotated sparse count files are in data/curated/.','', '## Figures','![QC](../results/plots/qc.png)','![Composition](../results/plots/composition.png)','![Associations](../results/plots/associations.png)','![Annotation](../results/plots/annotation.png)']
    (ROOT/'reports/transcriptomic_baseline.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':
    log('Starting Phase 2'); a=ingest(); a=qc(a); analyze(a); log('Phase 2 analysis complete')
