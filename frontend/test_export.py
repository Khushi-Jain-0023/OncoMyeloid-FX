"""Check the exported website against the completed research artifacts."""
import hashlib
import json
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from serve_frontend import Handler
from build_frontend import build

DIST = ROOT / 'frontend/dist'


@pytest.fixture(scope='module', autouse=True)
def exported_snapshot():
    build()


def test_export_matches_research():
    summary = json.loads((DIST / 'data/summary.json').read_text())
    assert summary['patients'] == 11
    assert summary['genes'] == 6124
    assert summary['primaryDiscoveries'] == 0
    for name, expected in summary['sourceHashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    for endpoint in ('MHCII', 'CD40', 'PDL1'):
        rows = json.loads((DIST / f'data/{endpoint}.json').read_text())
        assert len(rows) == 6124
        ranked = [row for row in rows if row['rank'] is not None]
        assert len(ranked) == 5155
        assert all(row['source'] and row['doi'] and row['sourceLocation'] for row in ranked)
        assert all(row['score'] is None for row in rows if row['rank'] is None)
    for document in summary['documents']:
        assert (DIST / document['url']).is_file()


def test_static_server_serves_modules_and_data():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(DIST)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        base = f'http://127.0.0.1:{server.server_port}'
        with urlopen(base + '/model.mjs', timeout=5) as response:
            assert response.status == 200
            assert 'javascript' in response.headers['Content-Type']
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
        with urlopen(base + '/data/summary.json', timeout=5) as response:
            assert json.load(response)['genes'] == 6124
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
