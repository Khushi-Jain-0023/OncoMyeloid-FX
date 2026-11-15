"""Generate and execute the results notebook against the completed pipeline outputs."""
from pathlib import Path
import json, sys, importlib.metadata
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parent
nb=nbformat.v4.new_notebook()
nb.cells=[
 nbformat.v4.new_markdown_cell('# Phase 2 — descriptive lung transcriptomics\nPatient-level exploratory analysis of GSE131907. No claim of measured T-cell suppression or causal target validation. See the protocol and manifest for definitions and provenance.'),
 nbformat.v4.new_code_cell("from pathlib import Path\nimport json, pandas as pd\nfrom IPython.display import display, Image\nROOT=Path.cwd()\nassert (ROOT/'results/run_manifest.json').exists()\nmanifest=json.loads((ROOT/'results/run_manifest.json').read_text())\n{k:manifest[k] for k in ['patients','input_cells','retained_cells','tested_genes','primary_fdr_005','composition_fdr_005']}"),
 nbformat.v4.new_markdown_cell('## Reproduce\nInstall requirements-lock.txt in Python 3.11, download the three GEO files documented in README.md, then run the cell below with RUN_PIPELINE=True. The executed notebook uses the already completed outputs rather than silently recalculating them.'),
 nbformat.v4.new_code_cell("RUN_PIPELINE=False\nif RUN_PIPELINE:\n    import subprocess, sys\n    subprocess.run([sys.executable, str(ROOT/'phase2.py')],cwd=ROOT,check=True)"),
 nbformat.v4.new_code_cell("display(pd.read_csv(ROOT/'results/qc_summary.csv'))\ndisplay(pd.read_csv(ROOT/'results/patient_features.csv'))"),
 nbformat.v4.new_code_cell("candidates=pd.read_csv(ROOT/'results/transcriptomic_candidates.csv')\ndisplay(candidates.head(20))"),
 nbformat.v4.new_code_cell("s=pd.read_csv(ROOT/'results/sensitivity_models.csv')\ndisplay(s.groupby('analysis').agg(patients=('patient_n','first'),genes=('gene_symbol','size'),fdr_005=('fdr',lambda x:(x<.05).sum())))"),
 nbformat.v4.new_code_cell("for name in ['qc','composition','associations','annotation']:\n    display(Image(filename=str(ROOT/f'results/plots/{name}.png')))"),
 nbformat.v4.new_markdown_cell('## Limits\nOnly 11 patients from one cohort. Patient and capture effects cannot be independently estimated. Published annotations and marker checks are not independent validation. All-T-cell scores mix T-cell states; CD8 and cytotoxic sensitivities are separate. Doublet calls are uncertain. Associations and FDR are exploratory; absence of significance is not evidence of no biology.')]
nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
# Explicit kernel path avoids global/user installation of a kernelspec.
from jupyter_client import KernelManager
runtime=ROOT/'work/jupyter-runtime'
runtime.mkdir(parents=True,exist_ok=True)
km=KernelManager(kernel_name='python3',connection_file=str(runtime/'phase2-kernel.json'))
km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
NotebookClient(nb,timeout=180,resources={'metadata':{'path':str(ROOT)}},km=km).execute(cleanup_kc=True)
nbformat.write(nb,ROOT/'notebooks/02_transcriptomics.ipynb')
packages=sorted({d.metadata['Name']:d.version for d in importlib.metadata.distributions()}.items(),key=lambda x:x[0].lower())
(ROOT/'requirements-lock.txt').write_text('\n'.join(f'{n}=={v}' for n,v in packages)+'\n')
print('Executed notebook and dependency lock written',flush=True)
