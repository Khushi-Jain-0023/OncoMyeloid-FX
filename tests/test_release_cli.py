import hashlib
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from oncomyeloid_fx.cli import verify, main


def test_integrity_detects_changed_and_missing_files(tmp_path):
    target=tmp_path/'result.csv'
    target.write_text('gene,score\nA,1\n')
    manifest={'version':'test','files':{'result.csv':hashlib.sha256(target.read_bytes()).hexdigest()}}
    (tmp_path/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest))
    assert verify(tmp_path)['checked_files']==1
    target.write_text('gene,score\nA,0\n')
    with pytest.raises(ValueError,match='changed'):
        verify(tmp_path)
    target.unlink()
    with pytest.raises(ValueError,match='missing'):
        verify(tmp_path)


def test_manifest_cannot_escape_snapshot(tmp_path):
    (tmp_path/'RELEASE_MANIFEST.json').write_text(json.dumps({'version':'test','files':{'../outside':'a'*64}}))
    with pytest.raises(ValueError,match='Unsafe'):
        verify(tmp_path)


def test_missing_project_fails_clearly(tmp_path,capsys):
    assert main(['--project',str(tmp_path),'status'])==1
    assert 'extracted OncoMyeloid-FX' in capsys.readouterr().err
