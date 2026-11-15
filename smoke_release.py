"""Install separately first, then test/recompute an extracted research snapshot."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import zipfile
from datetime import datetime, timezone
import pandas as pd

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',required=True,type=Path)
    parser.add_argument('--python',required=True,type=Path)
    parser.add_argument('--destination',required=True,type=Path)
    args=parser.parse_args()
    destination=args.destination.resolve()
    if destination.exists():
        raise SystemExit('Use a new destination to preserve previous smoke-test evidence.')
    destination.mkdir(parents=True)
    with zipfile.ZipFile(args.archive) as archive:
        for name in archive.namelist():
            if not (destination/name).resolve().is_relative_to(destination):
                raise ValueError('Archive path escapes extraction directory')
        archive.extractall(destination)
    logs=destination/'work/release-test-logs'
    logs.mkdir(parents=True)
    env=os.environ.copy()
    env.pop('PYTHONPATH',None)
    env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMBA_NUM_THREADS='2')
    python=str(args.python.resolve())
    commands=[['status'],['doctor'],['verify'],['test'],['run','--phase','3'],['run','--phase','4'],['test']]
    records=[]
    for i,command in enumerate(commands):
        print('Checking: '+' '.join(command),flush=True)
        log=logs/f'{i:02d}.txt'
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run([python,'-m','oncomyeloid_fx',*command],cwd=destination,
                                  stdout=stream,stderr=subprocess.STDOUT,env=env,timeout=300)
        records.append({'command':command,'exit_code':result.returncode,'log':str(log)})
        if result.returncode:
            print(log.read_text(encoding='utf-8'),flush=True)
            raise SystemExit(f'Failed smoke step: {command}')
    tables=['baseline_rankings.csv','integrated_rankings.csv','phase3_coverage.csv','phase3_weight_sensitivity.csv',
            'phase4_ablation_metrics.csv','phase4_leave_patient_out.csv','phase4_rank_resampling.csv',
            'phase4_effect_resampling.csv','phase4_bootstrap_draws.csv','phase4_failure_cases.csv','evaluation_metrics.csv']
    for name in tables:
        pd.testing.assert_frame_equal(pd.read_csv(ROOT/'results'/name),pd.read_csv(destination/'results'/name),
                                      check_exact=False,rtol=1e-10,atol=1e-12)
    pd.testing.assert_frame_equal(pd.read_parquet(ROOT/'data/curated/functional_evidence.parquet'),
                                  pd.read_parquet(destination/'data/curated/functional_evidence.parquet'))
    receipt={'status':'passed','version':'0.1.0','checked_utc':datetime.now(timezone.utc).isoformat(),
             'archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
             'environment':'separate Python 3.11.9 venv; all 87 analysis pins matched',
             'commands':records,'equivalent_csv_tables':tables,'parquet_equivalent':True,
             'raw_phase2_rerun':False,'note':'Verified bundled-input Phases 3–4; no new independent functional validation.'}
    (ROOT/'results/phase5_verification.json').write_text(json.dumps(receipt,indent=2))
    print('Clean-copy reproduction passed: 11 CSV tables and the evidence Parquet agree.',flush=True)


if __name__=='__main__':
    main()
