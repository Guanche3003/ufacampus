import os, re, html
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
missing = {}
total = 0
for dirpath, _, files in os.walk(ROOT):
    if any(part in ('_next', 'assets', 'exp') for part in dirpath.split(os.sep)):
        continue
    for name in files:
        if not name.endswith('.html'):
            continue
        p = os.path.join(dirpath, name)
        s = open(p, encoding='utf-8', errors='replace').read()
        for href in re.findall(r'href="(/[^"]*)"', s):
            href = html.unescape(href)
            u = urlsplit(href)
            path = u.path
            if not path.startswith('/') or path.startswith('/_next') or path.startswith('//'):
                continue
            if path.lower().endswith(('.png','.jpg','.svg','.webp','.ico','.css','.js','.json','.webmanifest','.pdf')):
                continue
            total += 1
            rel = 'index.html' if path == '/' else path.strip('/') + '/index.html'
            if not os.path.exists(os.path.join(ROOT, rel)):
                missing.setdefault(path, set()).add(os.path.relpath(p, ROOT))

print('liens internes vérifiés:', total)
print('cibles manquantes:', len(missing))
for path, srcs in sorted(missing.items())[:60]:
    print(' ', path, '<-', list(srcs)[:2])
