"""Moteur d'édition des fiches formation (stockage séparé, réappliquable).

Les modifications sont enregistrées dans content/formations-overrides.json puis
réappliquées au HTML par apply_content.py. Le HTML d'origine reste intact dans
sa structure : seules les valeurs des champs déclarés ci-dessous sont remplacées.
"""

import glob
import html
import json
import os
import re

# En local, la racine du site est ce dossier. Sur o2switch, le code Python est
# placé hors du dossier du domaine : la variable UFA_SITE_ROOT désigne alors le
# dossier public qui contient les pages HTML (à définir dans Setup Python App).
ROOT = os.path.abspath(os.path.expanduser(
    os.environ.get('UFA_SITE_ROOT') or os.path.dirname(os.path.abspath(__file__))
))
OVERRIDES_FILE = os.path.join(ROOT, 'content', 'formations-overrides.json')


def decode_html(value):
    return html.unescape(value)


def encode_html(value):
    return html.escape(value, quote=True)


def decode_json(value):
    try:
        return json.loads('"' + value + '"')
    except (ValueError, TypeError):
        return decode_html(value)


def encode_json(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]


# Chaque champ associe un libellé à une liste de motifs regex à un seul groupe.
# L'ordre des motifs est stable : il sert de clé aux valeurs d'origine enregistrées.
FIELDS = [
    {
        'key': 'titre_page',
        'label': 'Titre de la page (onglet, SEO, réseaux sociaux)',
        'regexes': [
            r'<title>(.*?)</title>',
            r'<meta property="og:title" content="(.*?)"/>',
            r'<meta name="twitter:title" content="(.*?)"/>',
        ],
        'decode': decode_html,
        'encode': encode_html,
    },
    {
        'key': 'titre_h1',
        'label': 'Titre affiché (H1)',
        'regexes': [r'<h1[^>]*>(.*?)</h1>'],
        'decode': decode_html,
        'encode': encode_html,
    },
    {
        'key': 'nom_formation',
        'label': 'Nom de la formation (données structurées)',
        'regexes': [r'"@type":"Course","name":"((?:[^"\\]|\\.)*)","description"'],
        'decode': decode_json,
        'encode': encode_json,
    },
    {
        'key': 'description_seo',
        'label': 'Description SEO (méta, réseaux sociaux)',
        'regexes': [
            r'<meta name="description" content="(.*?)"/>',
            r'<meta property="og:description" content="(.*?)"/>',
            r'<meta name="twitter:description" content="(.*?)"/>',
        ],
        'decode': decode_html,
        'encode': encode_html,
    },
    {
        'key': 'description_intro',
        'label': 'Description d’introduction (visible sur la fiche)',
        'regexes': [
            r'<p class="mt-2 max-w-2xl text-white/70">(.*?)</p>',
            r'<p class="mt-3 max-w-2xl text-\[15px\] text-white/75">(.*?)</p>',
        ],
        'decode': decode_html,
        'encode': encode_html,
    },
    {
        'key': 'description_ld',
        'label': 'Description (données structurées)',
        'regexes': [r'"@type":"Course","name":".*?","description":"((?:[^"\\]|\\.)*)","url"'],
        'decode': decode_json,
        'encode': encode_json,
    },
    {
        'key': 'prochaine_session',
        'label': 'Prochaine session (texte affiché)',
        'regexes': [r'Prochaine session</div><div[^>]*>(.*?)</div>'],
        'decode': decode_html,
        'encode': encode_html,
    },
]

SESSION_BLOCK = re.compile(r'<ul class="space-y-3">(.*?)</ul>', re.S)
SESSION_ITEM = re.compile(
    r'(<div class="font-display text-\[14px\] font-bold first-letter:capitalize text-navy">)(.*?)(</div>)',
    re.S,
)


def discover_pages():
    """Liste des 98 fiches formation, chemins relatifs avec séparateurs '/'."""
    found = []
    for pattern in ('formations/*/*/index.html', 'formation/*/index.html'):
        for path in glob.glob(os.path.join(ROOT, pattern)):
            rel = os.path.relpath(path, ROOT).replace('\\', '/')
            if rel in ('formations/index.html', 'formation/index.html'):
                continue
            found.append(rel)
    return sorted(found)


def load_overrides():
    if not os.path.isfile(OVERRIDES_FILE):
        return {}
    with open(OVERRIDES_FILE, encoding='utf-8') as fh:
        return json.load(fh)


def save_overrides(data):
    os.makedirs(os.path.dirname(OVERRIDES_FILE), exist_ok=True)
    with open(OVERRIDES_FILE, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write('\n')


def read_html(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as fh:
        return fh.read()


def write_html(path, content):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8') as fh:
        fh.write(content)


def page_values(path):
    """Valeurs actuellement affichées et présence de chaque champ."""
    source = read_html(path)
    result = {}
    for field in FIELDS:
        found = []
        for pattern in field['regexes']:
            match = re.search(pattern, source, re.S)
            found.append(field['decode'](match.group(1)) if match else None)
        first = next((v for v in found if v is not None), '')
        result[field['key']] = {
            'label': field['label'],
            'display': first,
            'present': any(v is not None for v in found),
            'count': sum(v is not None for v in found),
            'originals': found,
        }
    block = SESSION_BLOCK.search(source)
    items = [decode_html(m.group(2)) for m in SESSION_ITEM.finditer(block.group(1))] if block else []
    result['sessions'] = {
        'label': 'Sessions à venir (une session par ligne)',
        'display': '\n'.join(items),
        'present': bool(items),
        'count': len(items),
        'originals': items,
    }
    return result


def overview():
    pages = []
    overrides = load_overrides()
    for path in discover_pages():
        values = page_values(path)
        if path in overrides:
            # L'interface montre la valeur en attente, même si le HTML n'est pas encore appliqué.
            for key, entry in overrides[path].items():
                if key in values and isinstance(entry, dict) and 'current' in entry:
                    values[key]['display'] = entry['current']
        rel = path.replace('.html', '').replace('/index', '')
        category = 'Catalogue' if path.startswith('formations/') else 'Par ville'
        pages.append({
            'path': path,
            'name': values['titre_page']['display'] or rel,
            'category': category,
            'modified': path in overrides,
            'fields': values,
        })
    return pages


def _replace_group(match, encoded):
    start = match.start(1) - match.start(0)
    end = match.end(1) - match.start(0)
    whole = match.group(0)
    return whole[:start] + encoded + whole[end:]


def apply_page(source, override):
    """Applique les overrides à un HTML. Idempotent."""
    result = source
    for field in FIELDS:
        key = field['key']
        if key not in override:
            continue
        entry = override[key]
        current = entry.get('current', '')
        originals = entry.get('originals', [])
        encoded = field['encode'](current)

        for pattern_index, pattern in enumerate(field['regexes']):
            original = originals[pattern_index] if pattern_index < len(originals) else None

            def repl(match, field=field, current=current, original=original, encoded=encoded):
                value = field['decode'](match.group(1))
                if value == current or (original is not None and value == original):
                    return _replace_group(match, encoded)
                return match.group(0)

            result = re.sub(pattern, repl, result, flags=re.S)

    if 'sessions' in override:
        entry = override['sessions']
        lines = entry.get('current', '').split('\n')
        originals = entry.get('originals', [])
        block = SESSION_BLOCK.search(result)
        if block:
            inner = block.group(1)
            items = list(SESSION_ITEM.finditer(inner))
            for index in reversed(range(len(items))):
                item = items[index]
                value = decode_html(item.group(2))
                if index >= len(lines):
                    continue
                if value != lines[index] and value not in originals:
                    continue
                replacement = encode_html(lines[index])
                start, end = item.start(2), item.end(2)
                inner = inner[:start] + replacement + inner[end:]
            result = result[:block.start(1)] + inner + result[block.end(1):]

    return result


def revert_page(source, override):
    """Restaure les valeurs d'origine d'une fiche."""
    result = source

    for field in FIELDS:
        key = field['key']
        if key not in override:
            continue
        originals = override[key].get('originals', [])
        current = override[key].get('current', '')
        encoded_current = field['encode'](current)

        for pattern_index, pattern in enumerate(field['regexes']):
            original = originals[pattern_index] if pattern_index < len(originals) else None

            def repl(match, field=field, original=original,
                     encoded_current=encoded_current, current=current):
                value = field['decode'](match.group(1))
                if value != current and field['encode'](value) != encoded_current:
                    return match.group(0)
                if original is not None:
                    return _replace_group(match, field['encode'](original))
                return match.group(0)

            result = re.sub(pattern, repl, result, flags=re.S)

    if 'sessions' in override:
        originals = override['sessions'].get('originals', [])
        current_lines = override['sessions'].get('current', '').split('\n')
        block = SESSION_BLOCK.search(result)
        if block:
            inner = block.group(1)
            items = list(SESSION_ITEM.finditer(inner))
            for index in reversed(range(len(items))):
                item = items[index]
                value = decode_html(item.group(2))
                if index >= len(originals):
                    continue
                if value != current_lines[index] and value not in originals:
                    continue
                start, end = item.start(2), item.end(2)
                inner = inner[:start] + encode_html(originals[index]) + inner[end:]
            result = result[:block.start(1)] + inner + result[block.end(1):]

    return result


def apply_all():
    overrides = load_overrides()
    changed = []
    missing = []
    for path, override in overrides.items():
        full = os.path.join(ROOT, path)
        if not os.path.isfile(full):
            missing.append(path)
            continue
        source = read_html(path)
        updated = apply_page(source, override)
        if updated != source:
            write_html(path, updated)
            changed.append(path)
    return changed, missing


def reset_page(path):
    overrides = load_overrides()
    if path not in overrides:
        return False
    source = read_html(path)
    write_html(path, revert_page(source, overrides[path]))
    del overrides[path]
    save_overrides(overrides)
    return True
