"""Administration des fiches formation : application WSGI + serveur local.

Usage local :
    python admin_server.py
    puis http://127.0.0.1:4322/

Usage o2switch (cPanel > Setup Python App) :
    Application startup file : passenger_wsgi.py
    Application entry point  : application

Variables d'environnement utiles (à ajouter dans Setup Python App > Add Variable) :
    UFA_SITE_ROOT     chemin absolu du dossier public contenant les pages HTML
    UFA_ADMIN_USER    identifiant HTTP Basic (avec UFA_ADMIN_PASSWORD)
    UFA_ADMIN_PASSWORD mot de passe HTTP Basic
    UFA_ADMIN_PREFIX  préfixe de montage, par défaut /admin

Aucune dépendance autre que la bibliothèque standard Python.
"""

import base64
import hmac
import json
import os
from wsgiref.simple_server import make_server, WSGIRequestHandler

import content_engine as engine

HERE = os.path.dirname(os.path.abspath(__file__))
ADMIN_DIR = os.path.join(HERE, 'admin')
HOST = '127.0.0.1'
PORT = 4322
PREFIX = (os.environ.get('UFA_ADMIN_PREFIX') or '/admin').rstrip('/')

CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
}


class QuietHandler(WSGIRequestHandler):
    """Journal réduit : une ligne par requête, sans données privées."""

    def log_message(self, fmt, *args):
        print(f'[{self.address_string()}] {fmt % args}')


class AdminApplication:
    """Application WSGI : même code en local et derrière Passenger/o2switch."""

    def __call__(self, environ, start_response):
        path = self._path(environ)
        method = environ.get('REQUEST_METHOD', 'GET').upper()

        if not self._authorized(environ):
            return self._challenge(start_response)

        if method == 'GET':
            return self._get(start_response, path)
        if method == 'POST':
            return self._post(start_response, path, environ)
        return self._error(start_response, '405 Method Not Allowed')

    # ---------- utilitaires ----------

    @staticmethod
    def _path(environ):
        """Retire le préfixe de montage, quel que soit l'endroit où Passenger le place."""
        full = (environ.get('SCRIPT_NAME', '') or '') + (environ.get('PATH_INFO', '') or '/')
        if not full:
            full = '/'
        if PREFIX:
            if full == PREFIX:
                return '/'
            if full.startswith(PREFIX + '/'):
                return full[len(PREFIX):]
        return full

    @staticmethod
    def _authorized(environ):
        user = os.environ.get('UFA_ADMIN_USER')
        password = os.environ.get('UFA_ADMIN_PASSWORD')
        if not user or not password:
            return True  # aucun mot de passe configuré (usage local)
        header = environ.get('HTTP_AUTHORIZATION', '')
        if not header.startswith('Basic '):
            return False
        try:
            raw = base64.b64decode(header[6:]).decode('utf-8')
            given_user, _, given_password = raw.partition(':')
        except (ValueError, UnicodeDecodeError):
            return False
        return (hmac.compare_digest(given_user, user)
                and hmac.compare_digest(given_password, password))

    @staticmethod
    def _respond(start_response, status, body, content_type, extra=None):
        if isinstance(body, str):
            body = body.encode('utf-8')
        headers = [
            ('Content-Type', content_type),
            ('Content-Length', str(len(body))),
            ('Cache-Control', 'no-store'),
            ('X-Content-Type-Options', 'nosniff'),
        ]
        if extra:
            headers.extend(extra)
        start_response(status, headers)
        return [body]

    @staticmethod
    def _json(start_response, payload, status='200 OK'):
        return AdminApplication._respond(
            start_response, status,
            json.dumps(payload, ensure_ascii=False),
            'application/json; charset=utf-8',
        )

    @staticmethod
    def _error(start_response, status='404 Not Found'):
        return AdminApplication._respond(
            start_response, status, 'Ressource introuvable.', 'text/plain; charset=utf-8'
        )

    @staticmethod
    def _challenge(start_response):
        return AdminApplication._respond(
            start_response, '401 Unauthorized',
            'Authentification requise.', 'text/plain; charset=utf-8',
            [('WWW-Authenticate', 'Basic realm="Administration UFA Campus", charset="UTF-8"')],
        )

    @staticmethod
    def _body(environ):
        try:
            length = int(environ.get('CONTENT_LENGTH') or 0)
        except ValueError:
            length = 0
        if not length:
            return {}
        try:
            return json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return {}

    @staticmethod
    def _file(start_response, name):
        path = os.path.join(ADMIN_DIR, name)
        if not os.path.isfile(path):
            return AdminApplication._error(start_response)
        with open(path, 'rb') as fh:
            body = fh.read()
        content_type = CONTENT_TYPES.get(os.path.splitext(name)[1], 'application/octet-stream')
        return AdminApplication._respond(start_response, '200 OK', body, content_type)

    # ---------- routes ----------

    def _get(self, start_response, path):
        if path in ('/', '/index.html'):
            return self._file(start_response, 'index.html')
        if path == '/app.js':
            return self._file(start_response, 'app.js')
        if path == '/style.css':
            return self._file(start_response, 'style.css')
        if path == '/api/overview':
            return self._json(start_response, {
                'pages': engine.overview(),
                'modified': len(engine.load_overrides()),
                'site_root': engine.ROOT,
            })
        return self._error(start_response)

    def _post(self, start_response, path, environ):
        if path not in ('/api/save', '/api/reset', '/api/apply'):
            return self._error(start_response)
        data = self._body(environ)

        if path == '/api/save':
            page = data.get('path', '')
            if page not in engine.discover_pages():
                return self._json(start_response, {'ok': False, 'error': 'Fiche inconnue'}, '400 Bad Request')
            overrides = engine.load_overrides()
            entry = overrides.get(page, {})
            current_values = engine.page_values(page)
            for key, display in data.get('fields', {}).items():
                if key not in current_values:
                    continue
                if key in entry and 'originals' in entry[key]:
                    originals = entry[key]['originals']
                else:
                    originals = current_values[key]['originals']
                display = '' if display is None else str(display)
                if not display.strip():
                    # Champ vidé : on rétablit la valeur d'origine à l'application.
                    display = next((v for v in originals if v is not None), '')
                entry[key] = {'originals': originals, 'current': display}
            if entry:
                overrides[page] = entry
            else:
                overrides.pop(page, None)
            engine.save_overrides(overrides)
            return self._json(start_response, {'ok': True, 'modified': len(overrides)})

        if path == '/api/reset':
            page = data.get('path', '')
            if page not in engine.discover_pages():
                return self._json(start_response, {'ok': False, 'error': 'Fiche inconnue'}, '400 Bad Request')
            return self._json(start_response, {'ok': engine.reset_page(page)})

        changed, missing = engine.apply_all()
        return self._json(start_response, {
            'ok': True, 'changed': changed, 'missing': missing,
        })


# Point d'entrée utilisé par Phusion Passenger (passenger_wsgi.py) et par le serveur local.
application = AdminApplication()


def main():
    print(f'Administration UFA Campus : http://{HOST}:{PORT}/')
    print(f'Racine du site : {engine.ROOT}')
    print('Ctrl+C pour arrêter le serveur.')
    server = make_server(HOST, PORT, application, handler_class=QuietHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServeur arrêté.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
