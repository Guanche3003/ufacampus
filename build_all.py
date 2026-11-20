#!/usr/bin/env python3
"""Génère une copie statique de toutes les pages de capacademy.fr.

- parcourt les liens internes du site
- récupère le HTML et le CSS d'origine
- télécharge les images et polices localement
- réécrit les liens pour un fonctionnement en /chemin/index.html
"""
import os
import re
import html as htmlmod
import hashlib
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://capacademy.fr"
ROOT = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = "/_next/static/immutable/chunks/1b8e-p4tudj0e.css"
MAX_PAGES = 400
SKIP_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.woff', '.woff2',
            '.js', '.css', '.json', '.txt', '.xml', '.webmanifest', '.pdf', '.zip')


def fetch(url, retries=2):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SiteMirror/1.0)"})
    last = None
    for _ in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def path_to_file(route):
    if route == "/" or route == "":
        return "index.html"
    return route.strip("/") + "/index.html"


def normalize(raw, current="/"):
    if not raw:
        return None
    raw = htmlmod.unescape(raw.strip())
    if raw.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', 'javascript:', '#')):
        return None
    if raw.startswith(BASE):
        raw = raw[len(BASE):]
    if not raw.startswith('/'):
        raw = urllib.parse.urljoin(current, raw)
    parts = urllib.parse.urlsplit(raw)
    path = urllib.parse.unquote(parts.path)
    if path.lower().endswith(SKIP_EXT):
        return None
    if path.startswith(('/_next', '/api', '/cdn-cgi')):
        return None
    if not path.startswith('/'):
        path = '/' + path
    return path.rstrip('/') or '/'


def discover():
    seen = {"/"}
    queue = ["/"]
    pages = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        while queue and len(seen) < MAX_PAGES:
            batch = []
            while queue and len(batch) < 12:
                r = queue.pop(0)
                if r in pages:
                    continue
                batch.append(r)
            if not batch:
                break
            futures = {ex.submit(fetch, BASE + r): r for r in batch}
            for fut in as_completed(futures):
                r = futures[fut]
                try:
                    text = fut.result().decode('utf-8', 'replace')
                except Exception as e:  # noqa: BLE001
                    print('  ! fetch', r, e)
                    continue
                pages[r] = text
                for href in re.findall(r'href="([^"]+)"', text):
                    p = normalize(href, r)
                    if p and p not in seen:
                        seen.add(p)
                        queue.append(p)
            print(f'  discovered {len(pages)} pages, {len(queue)} in queue')
    return pages


def matching_close(s, open_idx, open_tag, close_tag):
    depth = 0
    i = open_idx
    while i < len(s):
        o = s.find(open_tag, i)
        c = s.find(close_tag, i)
        if c == -1:
            return len(s)
        if o != -1 and o < c:
            depth += 1
            i = o + len(open_tag)
        else:
            depth -= 1
            i = c + len(close_tag)
            if depth == 0:
                return c
    return len(s)


# ---------- assets ----------
ASSETS = {}
LOCK = set()


def register_asset(url):
    """Retourne l'URL locale d'un asset et l'enregistre pour téléchargement."""
    url = htmlmod.unescape(url or '')
    if not url:
        return None
    if url.startswith('/_next/image?'):
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        target = q.get('url', [''])[0]
        return register_asset(target)
    if url.startswith(BASE):
        url = url[len(BASE):]
    if url.startswith('//'):
        url = 'https:' + url
    if url.startswith(('http://', 'https://')):
        parsed = urllib.parse.urlsplit(url)
        ext = os.path.splitext(parsed.path)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico', '.woff2'):
            ext = '.jpg'
        key = hashlib.md5(url.encode()).hexdigest()[:16] + ext
        local = 'assets/remote/external/' + key
        source = url
    elif url.startswith('/'):
        source_path = urllib.parse.urlsplit(url).path
        local = 'assets/remote' + source_path
        source = BASE + source_path
    else:
        return None
    if local not in ASSETS:
        ASSETS[local] = source
    return '/' + local.replace('\\', '/')


def download_assets():
    todo = dict(ASSETS)
    print(f'downloading {len(todo)} assets...')
    ok = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {}
        for local, source in todo.items():
            full = os.path.join(ROOT, local)
            if os.path.exists(full) and os.path.getsize(full) > 0:
                ok += 1
                continue
            futures[ex.submit(fetch, source)] = (local, source)
        for fut in as_completed(futures):
            local, source = futures[fut]
            try:
                data = fut.result()
                full = os.path.join(ROOT, local)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, 'wb') as f:
                    f.write(data)
                ok += 1
            except Exception as e:  # noqa: BLE001
                print('  ! asset', source, e)
    print(f'  assets ok: {ok}/{len(todo)}')


# ---------- HTML transformation ----------
def rewrite_links(s):
    def repl(m):
        attr, val = m.group(1), m.group(2)
        val = htmlmod.unescape(val)
        if attr == 'href':
            if val.startswith('/') and not val.startswith('//'):
                parts = urllib.parse.urlsplit(val)
                p = parts.path
                frag = ('#' + parts.fragment) if parts.fragment else ''
                if p == '/' or p.lower().endswith(SKIP_EXT):
                    new = p + frag
                else:
                    new = p.rstrip('/') + '/' + frag
                return 'href="%s"' % htmlmod.escape(new, quote=True)
            return m.group(0)
        # src / srcset / imageSrcSet
        if attr.lower() == 'srcset':
            candidates = []
            for chunk in val.split(','):
                bits = chunk.strip().split()
                if not bits:
                    continue
                local = register_asset(bits[0])
                if local:
                    candidates.append(local + (' ' + ' '.join(bits[1:]) if len(bits) > 1 else ''))
            return ' ' if candidates else ' '
        local = register_asset(val)
        if local:
            return '%s="%s"' % (attr, local)
        return m.group(0)
    return re.sub(r'\b(srcSet|srcset|imageSrcSet|src|href)="([^"]*)"', repl, s)


def clean_head(raw):
    m = re.search(r'<head[^>]*>(.*?)</head>', raw, re.S | re.I)
    if not m:
        return '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    head = m.group(1)
    head = re.sub(r'<script[^>]*>.*?</script>', '', head, flags=re.S | re.I)
    head = re.sub(r'<link[^>]*as="script"[^>]*>', '', head, flags=re.I)
    head = re.sub(r'<link[^>]*as="image"[^>]*>', '', head, flags=re.I)
    head = re.sub(r'<link[^>]*rel="preload"[^>]*>', '', head, flags=re.I)
    head = head.replace(CSS_PATH, CSS_PATH)
    head += '\n<link rel="stylesheet" href="/site-fixes.css">\n'
    return head


def extract_main(raw):
    body = re.search(r'<body[^>]*>(.*)</body>', raw, re.S | re.I)
    if not body:
        return None, None, None
    b = body.group(1)
    start = b.find('<main')
    if start == -1:
        return b, '', ''
    end = matching_close(b, start, '<main', '</main>')
    end += len('</main>')
    prefix, main_block, suffix = b[:start], b[start:end], b[end:]
    inner = main_block.find('<main', main_block.find('>') + 1)
    if inner != -1:
        inner_end = matching_close(main_block, inner, '<main', '</main>')
        content = main_block[inner + main_block[inner:].find('>') + 1:inner_end]
    else:
        content = main_block
        # retirer les balises <main> englobantes
        open_end = content.find('>')
        close_start = content.rfind('</main>')
        if open_end != -1 and close_start > open_end:
            content = content[open_end + 1:close_start]
        # retirer l'en-tête dupliqué éventuel
        h = content.find('<header')
        if h != -1:
            he = matching_close(content, h, '<header', '</header>') + len('</header>')
            content = content[:h] + content[he:]
    prefix = re.sub(r'<script[^>]*>.*?</script>', '', prefix, flags=re.S | re.I)
    suffix = re.sub(r'<script[^>]*>.*?</script>', '', suffix, flags=re.S | re.I)
    prefix = re.sub(r'<noscript[^>]*>.*?</noscript>', '', prefix, flags=re.S | re.I)
    suffix = re.sub(r'<noscript[^>]*>.*?</noscript>', '', suffix, flags=re.S | re.I)
    return prefix, content, suffix


def html_attrs(raw):
    m = re.match(r'.*?<html([^>]*)>', raw, re.S | re.I)
    attrs = m.group(1) if m else ''
    cls = re.search(r'class="([^"]*)"', attrs)
    style = re.search(r'style="([^"]*)"', attrs)
    out = ''
    if cls:
        out += ' class="%s"' % cls.group(1)
    if style:
        out += ' style="%s"' % htmlmod.escape(style.group(1), quote=True)
    return out


def build_page(route, raw):
    head = clean_head(raw)
    prefix, content, suffix = extract_main(raw)
    if content is None:
        return None
    body = (prefix or '') + '<main id="contenu">' + content + '</main>' + (suffix or '')
    body = rewrite_links(body)
    body = body.replace('</body>', '<script src="/site.js" defer></script></body>')
    if '</body>' not in body:
        body += '<script src="/site.js" defer></script>'
    attrs = html_attrs(raw)
    return ('<!DOCTYPE html><html lang="fr"%s><head>%s</head><body class="font-sans">%s</body></html>'
            % (attrs, head, body))


def main():
    print('discovering pages...')
    pages = discover()
    print(f'found {len(pages)} pages')

    # CSS + polices
    os.makedirs(os.path.join(ROOT, '_next/static/immutable/chunks'), exist_ok=True)
    css_local = os.path.join(ROOT, CSS_PATH.lstrip('/'))
    if not os.path.exists(css_local):
        data = fetch(BASE + CSS_PATH)
        os.makedirs(os.path.dirname(css_local), exist_ok=True)
        with open(css_local, 'wb') as f:
            f.write(data)
    css = open(css_local, encoding='utf-8', errors='replace').read()
    for font in re.findall(r'\.\./media/([A-Za-z0-9_.-]+\.woff2)', css):
        p = '_next/static/immutable/media/' + font
        full = os.path.join(ROOT, p)
        if not os.path.exists(full):
            try:
                data = fetch(BASE + '/_next/static/immutable/media/' + font)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, 'wb') as f:
                    f.write(data)
            except Exception as e:  # noqa: BLE001
                print('  ! font', font, e)

    outputs = {}
    for route, raw in pages.items():
        out = build_page(route, raw)
        if out:
            outputs[path_to_file(route)] = out
    download_assets()

    for rel, content in outputs.items():
        full = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
    print(f'written {len(outputs)} pages')
    with open(os.path.join(ROOT, 'pages-list.txt'), 'w', encoding='utf-8') as f:
        for r in sorted(pages):
            f.write(r + '\n')


if __name__ == '__main__':
    main()
