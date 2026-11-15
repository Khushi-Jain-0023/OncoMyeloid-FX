"""Produce plots, execute the Phase 3 notebook, and pin its dependencies."""
from pathlib import Path
import os
import sys
import importlib.metadata
import uuid
import asyncio
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nbformat
from nbclient import NotebookClient
from jupyter_client import AsyncKernelManager

ROOT = Path(__file__).resolve().parent
runtime = ROOT / 'work/jupyter-runtime'
runtime.mkdir(parents=True, exist_ok=True)
os.environ['IPYTHONDIR'] = str(ROOT / 'work/ipython')
os.environ['TEMP'] = os.environ['TMP'] = str(runtime)
rankings = pd.read_csv(ROOT / 'results/integrated_rankings.csv')
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), constrained_layout=True)
for ax, (endpoint, group) in zip(axes, rankings.groupby('endpoint')):
    g = group.dropna(subset=['ranking_value'])
    scatter = ax.scatter(g.transcriptomic_evidence, g.functional_evidence,
                        c=g.ranking_value, cmap='viridis', s=4, alpha=.5, vmin=0, vmax=1)
    ax.set(title=f'{endpoint}: {len(g):,} mapped candidates',
           xlabel='Transcriptomic evidence percentile', ylabel='Absolute marker-effect percentile')
fig.colorbar(scatter, ax=axes, label='Exploratory combined score')
fig.suptitle('Mouse marker evidence + human expression associations (not T-cell-function prediction)')
fig.savefig(ROOT / 'results/plots/phase3_evidence.png', dpi=150)
plt.close(fig)
nb = nbformat.v4.new_notebook()
nb.metadata.kernelspec = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb.cells = [
    nbformat.v4.new_markdown_cell('# Phase 3 — descriptive evidence integration\nThree mouse immune-marker endpoints remain separate. These rankings are not validated T-cell-function predictions. See reports/scoring_spec.md for the frozen heuristic and exclusions.'),
    nbformat.v4.new_code_cell("from pathlib import Path\nimport json, pandas as pd\nfrom IPython.display import display, Image\nROOT=Path.cwd()\nm=json.loads((ROOT/'results/phase3_manifest.json').read_text())\n{k:m[k] for k in ['screen_genes','quantitative_records','qualitative_records','direct_T_function_eligible_records','predictive_gate']}"),
    nbformat.v4.new_code_cell("e=pd.read_parquet(ROOT/'data/curated/functional_evidence.parquet')\ndisplay(e.groupby(['endpoint_class','partition'],dropna=False).size().rename('records').to_frame())\ndisplay(pd.read_csv(ROOT/'results/phase3_coverage.csv'))"),
    nbformat.v4.new_code_cell("display(pd.read_csv(ROOT/'results/phase3_qualitative_evidence.csv'))"),
    nbformat.v4.new_code_cell("r=pd.read_csv(ROOT/'results/integrated_rankings.csv')\nfor endpoint,g in r.groupby('endpoint'):\n    print(endpoint)\n    display(g.dropna(subset=['rank']).head(10)[['gene_symbol','gene_id','rank','ranking_value','marker_selection_contrast','fdr','source_ids']])"),
    nbformat.v4.new_code_cell("display(pd.read_csv(ROOT/'results/phase3_weight_sensitivity.csv'))\ndisplay(Image(filename=str(ROOT/'results/plots/phase3_evidence.png')))"),
    nbformat.v4.new_code_cell("# Reproduce only when deliberately enabled; outputs above are from the completed run.\nRUN_PIPELINE=False\nif RUN_PIPELINE:\n    import subprocess,sys\n    subprocess.run([sys.executable,str(ROOT/'phase3.py')],cwd=ROOT,check=True)"),
    nbformat.v4.new_markdown_cell('## Limits\nOne quantitative development family, mouse non-tumor context, immune-marker proxies, heuristic equal weighting, and unknown donor-level n. Unknown evidence is unranked, not negative. Six T-cell-function leads remain qualitative. No independent performance estimate is possible from this inventory.')
]
print('Figure saved; starting notebook kernel.', flush=True)
km = AsyncKernelManager(kernel_name='python3', connection_file=str(runtime / f'phase3-{uuid.uuid4().hex}.json'))
km.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
client = NotebookClient(nb, timeout=180, startup_timeout=60, resources={'metadata': {'path': str(ROOT)}}, km=km)
asyncio.run(client.async_execute(cleanup_kc=True))
nbformat.write(nb, ROOT / 'notebooks/03_evidence_ranking.ipynb')
packages = sorted({d.metadata['Name']: d.version for d in importlib.metadata.distributions()}.items(), key=lambda x: x[0].lower())
(ROOT / 'requirements-phase3-lock.txt').write_text('\n'.join(f'{n}=={v}' for n, v in packages) + '\n')
print('Phase 3 notebook executed; plot and dependency lock saved.', flush=True)
