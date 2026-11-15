"""Export existing research outputs for a read-only, buildless website."""
from pathlib import Path
import hashlib
import json
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'frontend/dist'


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')


def number(value):
    return None if pd.isna(value) else float(value)


def build():
    # Fail closed if the frozen analysis inputs no longer match their provenance.
    for filename in ['phase3_manifest.json', 'phase4_manifest.json']:
        for name, expected in read_json('results/' + filename)['input_sha256'].items():
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f'Analysis input changed: {name}')
    for directory in ['data', 'downloads']:
        (OUT / directory).mkdir(parents=True, exist_ok=True)
    for filename in ['index.html', 'styles.css', 'app.js', 'model.mjs', 'favicon.svg']:
        shutil.copyfile(ROOT / 'frontend' / filename, OUT / filename)
    p2 = read_json('results/run_manifest.json')
    p3 = read_json('results/phase3_manifest.json')
    p4 = read_json('results/phase4_manifest.json')
    p5 = read_json('results/phase5_verification.json')
    assert p5['status'] == 'passed'
    evidence = pd.read_parquet(ROOT / 'data/curated/functional_evidence.parquet').set_index('evidence_id')
    ranks = pd.read_csv(ROOT / 'results/integrated_rankings.csv', float_precision='round_trip')
    stability = pd.read_csv(ROOT / 'results/phase4_rank_resampling.csv').set_index(['endpoint', 'gene_symbol'])
    coverage = {}
    for endpoint, group in ranks.groupby('endpoint'):
        rows = []
        for row in group.itertuples():
            source = evidence.loc[row.source_ids] if pd.notna(row.source_ids) else None
            uncertainty = stability.loc[(endpoint, row.gene_symbol)] if (endpoint, row.gene_symbol) in stability.index else None
            rows.append({
                'symbol': row.gene_symbol, 'id': None if pd.isna(row.gene_id) else row.gene_id,
                'rank': number(row.rank), 'score': number(row.ranking_value),
                'effect': number(row.association_effect), 'p': number(row.p_value), 'fdr': number(row.fdr),
                'marker': number(row.marker_selection_contrast),
                'source': None if source is None else str(row.source_ids),
                'doi': None if source is None else source.doi,
                'sourceLocation': None if source is None else source.source_location,
                'mouseSymbol': None if source is None else source.mouse_symbol,
                'mouseId': None if source is None or pd.isna(source.mouse_gene_id) else source.mouse_gene_id,
                'frequency': None if uncertainty is None else number(uncertainty.top20_frequency_all_draws),
                'rankLow': None if uncertainty is None else number(uncertainty.rank_q025),
                'rankHigh': None if uncertainty is None else number(uncertainty.rank_q975),
            })
        assert len(rows) == p2['tested_genes'] and len({r['symbol'] for r in rows}) == len(rows)
        coverage[endpoint] = {'total': len(rows), 'ranked': sum(r['rank'] is not None for r in rows)}
        write_json(OUT / 'data' / f'{endpoint}.json', rows)
    documents = [
        ('feasibility', 'Feasibility audit', 'reports/feasibility.md'),
        ('baseline', 'Transcriptomic baseline', 'reports/transcriptomic_baseline.md'),
        ('evidence', 'Evidence and rankings', 'reports/phase3_evidence_ranking.md'),
        ('benchmark', 'Robustness and benchmarking', 'reports/benchmark.md'),
        ('final-report', 'Final research report', 'reports/final_report.md'),
        ('scoring', 'Scoring specification', 'reports/scoring_spec.md'),
        ('reproducibility', 'Reproducibility guide', 'reports/reproducibility.md'),
    ]
    for key, _, source in documents:
        shutil.copyfile(ROOT / source, OUT / 'downloads' / f'{key}.md')
    # Report image links retain their original relative locations in downloads.
    for path in (ROOT / 'results/plots').glob('*.png'):
        target = OUT / 'results/plots' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for filename in ['baseline_rankings.csv', 'integrated_rankings.csv', 'phase4_rank_resampling.csv']:
        shutil.copyfile(ROOT / 'results' / filename, OUT / 'downloads' / filename)
    summary = {
        'release': p5['version'], 'patients': p2['patients'], 'genes': p2['tested_genes'],
        'retainedCells': p2['retained_cells'], 'primaryDiscoveries': p2['primary_fdr_005'],
        'markerRecords': p3['quantitative_records'], 'qualitativeRecords': p3['qualitative_records'],
        'bootstrapDraws': p4['bootstrap_draws'], 'validation': p4['decision']['decision'],
        'independentRecords': p4['decision']['eligible_independent_records'], 'coverage': coverage,
        'documents': [{'id': key, 'title': title, 'url': f'downloads/{key}.md'} for key, title, _ in documents],
        'sourceHashes': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in [
            'results/run_manifest.json', 'results/phase3_manifest.json', 'results/phase4_manifest.json',
            'results/phase5_verification.json', 'results/integrated_rankings.csv']},
    }
    write_json(OUT / 'data/summary.json', summary)
    print(f'Frontend ready: {p2["tested_genes"]:,} candidates × {len(coverage)} endpoints. Scientific outputs unchanged.')


if __name__ == '__main__':
    build()
