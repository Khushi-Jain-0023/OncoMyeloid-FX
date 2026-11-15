"""Local, read-only preview. Serves only the frontend's exported directory."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404)
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent / 'frontend/dist'
    if not (root / 'index.html').exists():
        raise SystemExit('Run python build_frontend.py first.')
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(root)))
    print(f'OncoMyeloid-FX: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
