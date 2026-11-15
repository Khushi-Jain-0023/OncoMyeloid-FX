"""Build an auditable research ZIP without runtimes, caches or raw single-cell counts."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent


def selected_files():
    files=list(ROOT.glob('*.py'))+list(ROOT.glob('*.md'))+list(ROOT.glob('requirements*.txt'))
    files += [ROOT/n for n in ['pyproject.toml','MANIFEST.in','.gitignore','.gitattributes']]
    for directory in ['configs','reports','notebooks','results','data/registry','data/sources/phase3']:
        files += [p for p in (ROOT/directory).rglob('*') if p.is_file()]
    for directory in ['src/oncomyeloid_fx','tests']:
        files += list((ROOT/directory).glob('*.py'))
    files += list((ROOT/'dist').glob('*.whl'))+list((ROOT/'dist').glob('*.tar.gz'))
    files += [ROOT/'data/curated/functional_evidence.parquet', ROOT/'work/hgnc_complete_set.txt']
    return sorted(set(p for p in files if p.is_file() and '__pycache__' not in p.parts))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    required=['dist/oncomyeloid_fx-0.1.0-py3-none-any.whl','reports/final_report.md',
              'reports/reproducibility.md','results/phase4_verification.json']
    for name in required:
        if not (ROOT/name).is_file():
            raise SystemExit(f'Missing release artifact: {name}')
    try:
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
    except (OSError,subprocess.CalledProcessError):
        revision=None
    files=selected_files()
    manifest={'version':'0.1.0','created_utc':datetime.now(timezone.utc).isoformat(),
              'git_revision':revision,'scientific_status':'inconclusive_independent_validation',
              'omitted':['raw UMI matrix','H5AD caches','Python runtimes and dependencies'],
              'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p,p.relative_to(ROOT).as_posix())
        archive.writestr('RELEASE_MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(args.output) as archive:
        assert archive.testzip() is None
    checksum=hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(args.output.suffix+'.sha256').write_text(f'{checksum}  {args.output.name}\n')
    print(json.dumps({'archive':str(args.output),'files':len(files),'sha256':checksum,'git_revision':revision},indent=2))


if __name__=='__main__':
    main()
