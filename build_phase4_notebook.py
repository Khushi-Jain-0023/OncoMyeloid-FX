"""Execute the Phase 4 results notebook using the current interpreter."""
from pathlib import Path
import os
import sys
import uuid
import asyncio

ROOT = Path(__file__).resolve().parent
runtime = ROOT / 'work/jupyter-runtime'
runtime.mkdir(parents=True, exist_ok=True)
os.environ['TEMP'] = os.environ['TMP'] = str(runtime)
os.environ['IPYTHONDIR'] = str(ROOT / 'work/ipython')

import nbformat
from nbclient import NotebookClient
from jupyter_client import AsyncKernelManager

nb = nbformat.v4.new_notebook()
nb.metadata.kernelspec = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb.cells = [
    nbformat.v4.new_markdown_cell('# Phase 4 — benchmark eligibility and robustness\nDecision: **inconclusive**. Independent quantitative T-cell-function outcomes are unavailable. Patient resampling measures descriptive rank stability, not functional prediction accuracy.'),
    nbformat.v4.new_code_cell("from pathlib import Path\nimport json, pandas as pd\nfrom IPython.display import display,Image\nROOT=Path.cwd()\nm=json.loads((ROOT/'results/phase4_manifest.json').read_text())\ndisplay(m['decision'])\ndisplay(pd.read_csv(ROOT/'results/evaluation_metrics.csv'))"),
    nbformat.v4.new_code_cell("display(pd.read_csv(ROOT/'results/phase4_family_audit.csv'))\ndisplay(pd.read_csv(ROOT/'results/phase4_leave_patient_out.csv'))"),
    nbformat.v4.new_code_cell("display(pd.read_csv(ROOT/'results/phase4_ablation_metrics.csv'))"),
    nbformat.v4.new_code_cell("draws=pd.read_csv(ROOT/'results/phase4_bootstrap_draws.csv')\ndisplay(draws[['unique_patients','estimable_genes']].describe())\nr=pd.read_csv(ROOT/'results/phase4_rank_resampling.csv')\nfor endpoint,g in r.groupby('endpoint'):\n    print(endpoint)\n    display(g.sort_values(['reference_rank','gene_symbol']).head(10))"),
    nbformat.v4.new_code_cell("for name in ['phase4_ablations','phase4_rank_ranges']:\n    display(Image(filename=str(ROOT/f'results/plots/{name}.png')))"),
    nbformat.v4.new_code_cell("RUN_PIPELINE=False\nif RUN_PIPELINE:\n    import subprocess,sys\n    subprocess.run([sys.executable,str(ROOT/'phase4.py')],cwd=ROOT,check=True)"),
    nbformat.v4.new_markdown_cell('## Limits\nOnly 11 human patients and one quantitative mouse-marker study family. Bootstrap repeats whole patient pairs, holding marker evidence, annotation and gene selection fixed. Percentile ranges are exploratory, not calibrated CIs. Different T-cell endpoints are not independent replication. Missing test metrics remain missing. See reports/benchmark.md, reports/leakage_audit.md and reports/phase4_protocol.md.')
]
km = AsyncKernelManager(kernel_name='python3', connection_file=str(runtime / f'phase4-{uuid.uuid4().hex}.json'))
km.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
client = NotebookClient(nb, timeout=180, startup_timeout=60, resources={'metadata': {'path': str(ROOT)}}, km=km)
asyncio.run(client.async_execute(cleanup_kc=True))
nbformat.write(nb, ROOT / 'notebooks/04_benchmark_robustness.ipynb')
print('Phase 4 notebook executed and saved.', flush=True)
