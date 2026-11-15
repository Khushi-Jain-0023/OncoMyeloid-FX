"""Small dependency-free CLI for the accompanying versioned research snapshot."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
from . import __version__

SCRIPTS = {
    '2': ['phase2.py','summarize_phase2.py','build_notebook.py','verify_phase2.py'],
    '3': ['phase3.py','build_phase3_notebook.py','verify_phase3.py'],
    '4': ['phase4.py','build_phase4_notebook.py','verify_phase4.py'],
}


def project_path(value):
    root = Path(value).expanduser().resolve()
    if not (root/'configs/phase2.json').is_file() or not (root/'results/phase4_manifest.json').is_file():
        raise ValueError('Select an extracted OncoMyeloid-FX research release with --project PATH.')
    return root


def checksum(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(root):
    path = root/'RELEASE_MANIFEST.json'
    if not path.is_file():
        raise ValueError('No RELEASE_MANIFEST.json; use the packaged research release for integrity verification.')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if not manifest.get('files'):
        raise ValueError('Empty release manifest')
    failures = []
    for name, expected in manifest['files'].items():
        target = (root/name).resolve()
        if not target.is_relative_to(root.resolve()) or Path(name).is_absolute():
            raise ValueError('Unsafe path in release manifest')
        if not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('Invalid SHA256 in release manifest')
        if not target.is_file():
            failures.append(f'missing: {name}')
        elif checksum(target) != expected:
            failures.append(f'changed: {name}')
    if failures:
        raise ValueError('Release integrity failed:\n'+'\n'.join(failures))
    return {'status':'passed', 'release':manifest['version'], 'checked_files':len(manifest['files']),
            'note':'Integrity only; not independent scientific validation.'}


def status(root):
    p2=json.loads((root/'results/run_manifest.json').read_text())
    p3=json.loads((root/'results/phase3_manifest.json').read_text())
    p4=json.loads((root/'results/phase4_manifest.json').read_text())
    return {'release':__version__, 'patients':p2['patients'], 'candidate_genes':p2['tested_genes'],
            'primary_fdr_005':p2['primary_fdr_005'], 'quantitative_marker_records':p3['quantitative_records'],
            'validation_decision':p4['decision']['decision'],
            'independent_functional_test_records':p4['decision']['eligible_independent_records'],
            'scope':'descriptive; no validated functional prediction'}


def doctor(root):
    checks=[]
    for line in (root/'requirements-phase3-lock.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, expected=line.split('==')
        try:
            actual=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual=None
        checks.append({'package':name,'expected':expected,'installed':actual,'matches':actual==expected})
    mismatches=[row for row in checks if not row['matches']]
    ok=sys.version_info[:2]==(3,11) and not mismatches
    return {'status':'passed' if ok else 'environment_mismatch','python':sys.version.split()[0],
            'checked_packages':len(checks),'mismatches':mismatches}


def main(argv=None):
    parser=argparse.ArgumentParser(description='OncoMyeloid-FX descriptive research release')
    parser.add_argument('--version',action='version',version=__version__)
    parser.add_argument('--project',default='.',help='Path to extracted research snapshot (default: current directory)')
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ['status','verify','doctor','test']:
        commands.add_parser(name)
    run=commands.add_parser('run',help='Recompute outputs in a working copy; changes release hashes')
    run.add_argument('--phase',choices=list(SCRIPTS),required=True)
    args=parser.parse_args(argv)
    try:
        root=project_path(args.project)
        if args.command in ['status','verify','doctor']:
            result={'status':status,'verify':verify,'doctor':doctor}[args.command](root)
            print(json.dumps(result,indent=2))
            return 0 if result.get('status')!='environment_mismatch' else 1
        if args.command=='test':
            return subprocess.run([sys.executable,'-m','pytest','tests','-q'],cwd=root).returncode
        for script in SCRIPTS[args.phase]:
            if not (root/script).is_file():
                raise ValueError(f'Missing research script: {script}')
        for script in SCRIPTS[args.phase]:
            print(f'Running {script}',flush=True)
            outcome=subprocess.run([sys.executable,str(root/script)],cwd=root)
            if outcome.returncode:
                return outcome.returncode
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(str(error),file=sys.stderr)
        return 1
