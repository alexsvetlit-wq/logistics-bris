"""BRIS prototype: loopback-only UI and immutable SQLite calculation snapshots."""
import argparse
import json
import os
from pathlib import Path
import secrets
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webbrowser

ROOT = Path(__file__).resolve().parent

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS calculations (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, title TEXT NOT NULL, client TEXT NOT NULL, parent_id INTEGER REFERENCES calculations(id), snapshot TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS catalog (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, payload TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS catalog_history (revision INTEGER PRIMARY KEY, changed_at TEXT NOT NULL, payload TEXT NOT NULL)')
            seed = json.loads((ROOT / 'knowledge' / 'catalog.json').read_text(encoding='utf-8'))
            con.execute('INSERT OR IGNORE INTO catalog VALUES(1,0,?)', (json.dumps(seed, ensure_ascii=False),))
    def catalog(self):
        with self.connect() as con:
            row = con.execute('SELECT revision,payload FROM catalog WHERE id=1').fetchone()
            result = json.loads(row['payload'])
            result['revision'] = row['revision']
            return result
    def save_catalog(self, payload):
        if not isinstance(payload, dict) or any(not isinstance(payload.get(k), list) for k in ('providers','routes','offers','sources')):
            raise ValueError('Неверная структура справочника')
        revision = payload.get('revision')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT revision,payload FROM catalog WHERE id=1').fetchone()
            if revision != row['revision']:
                raise ValueError('Справочник изменён в другом окне. Обновите страницу.')
            con.execute('INSERT INTO catalog_history VALUES(?,?,?)', (revision,datetime.now(timezone.utc).isoformat(),row['payload']))
            payload['revision'] = revision + 1
            con.execute('UPDATE catalog SET revision=?,payload=? WHERE id=1', (revision+1,json.dumps(payload,ensure_ascii=False)))
        return revision+1
    def connect(self):
        con = sqlite3.connect(self.path)
        con.execute('PRAGMA foreign_keys=ON')
        con.row_factory = sqlite3.Row
        return con
    def save(self, snapshot, parent_id=None):
        fields = snapshot.get('fields', {})
        if not isinstance(fields, dict) or not isinstance(snapshot.get('costs'), list):
            raise ValueError('Неверная структура расчёта')
        if any(k.lower() in ('password', 'smtp_password', 'token', 'secret') for k in fields):
            raise ValueError('Пароли не сохраняются в расчётах')
        created = datetime.now(timezone.utc).isoformat()
        with self.connect() as con:
            if parent_id is not None and not con.execute('SELECT 1 FROM calculations WHERE id=?', (parent_id,)).fetchone():
                raise ValueError('Исходный расчёт не найден')
            cur = con.execute('INSERT INTO calculations(created_at,title,client,parent_id,snapshot) VALUES(?,?,?,?,?)', (created, str(fields.get('title', 'Расчёт')), str(fields.get('client', '')), parent_id, json.dumps(snapshot, ensure_ascii=False)))
            return cur.lastrowid
    def list(self):
        with self.connect() as con:
            return [dict(r) for r in con.execute('SELECT id,created_at,title,client,parent_id FROM calculations ORDER BY id DESC')]
    def get(self, identifier):
        with self.connect() as con:
            r = con.execute('SELECT * FROM calculations WHERE id=?', (identifier,)).fetchone()
            if r is None:
                return None
            data = dict(r)
            data['snapshot'] = json.loads(data['snapshot'])
            return data

def make_server(port=8765, data_dir=None):
    store = Store(Path(data_dir or ROOT / 'data') / 'bris.sqlite3')
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # avoid logging client data
        def send(self, status, body, mime='application/json; charset=utf-8'):
            raw = body.encode('utf-8') if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            self.wfile.write(raw)
        def host_ok(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        def api_ok(self):
            origin = self.headers.get('Origin')
            expected = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
            return self.host_ok() and self.headers.get('X-BRIS-Token') == token and (origin is None or origin in expected)
        def do_GET(self):
            if not self.host_ok():
                return self.send(403, {'error': 'Недопустимый адрес'})
            if self.path == '/catalog':
                html = (ROOT / 'web' / 'catalog.html').read_text(encoding='utf-8').replace('<meta charset="UTF-8">', '<meta charset="UTF-8"><meta name="bris-token" content="' + token + '">', 1)
                return self.send(200, html, 'text/html; charset=utf-8')
            if self.path in ('/', '/index.html'):
                html = (ROOT / 'web' / 'index.html').read_text(encoding='utf-8').replace('<meta charset="UTF-8">', '<meta charset="UTF-8"><meta name="bris-token" content="' + token + '">', 1)
                return self.send(200, html, 'text/html; charset=utf-8')
            if self.path.startswith('/api/') and not self.api_ok():
                return self.send(403, {'error': 'Доступ запрещён'})
            if self.path == '/api/catalog':
                return self.send(200, store.catalog())
            if self.path == '/api/calculations':
                return self.send(200, store.list())
            if self.path.startswith('/api/calculations/'):
                try:
                    result = store.get(int(self.path.rsplit('/', 1)[1]))
                except ValueError:
                    result = None
                return self.send(200 if result else 404, result or {'error': 'Расчёт не найден'})
            return self.send(404, {'error': 'Страница не найдена'})
        def do_POST(self):
            if not self.api_ok():
                return self.send(403, {'error': 'Доступ запрещён'})
            if self.path not in ('/api/calculations', '/api/catalog'):
                return self.send(404, {'error': 'Страница не найдена'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 1 or length > 2_000_000:
                    return self.send(413, {'error': 'Размер данных превышен'})
                payload = json.loads(self.rfile.read(length))
                if self.path == '/api/catalog':
                    revision = store.save_catalog(payload)
                    return self.send(200, {'revision': revision})
                identifier = store.save(payload['snapshot'], payload.get('parent_id'))
                return self.send(201, {'id': identifier})
            except (ValueError, TypeError, KeyError, AttributeError):
                return self.send(400, {'error': 'Проверьте структуру расчёта'})
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='BRIS Logistics — prototype')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    server = make_server(args.port, os.environ.get('BRIS_DATA_DIR'))
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'BRIS Logistics: {url}\nStop: Ctrl+C', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
