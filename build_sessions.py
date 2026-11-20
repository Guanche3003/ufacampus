import html
import json
import re

site = open('planning/index.html', encoding='utf-8').read()

MONTH_MAP = {
    'TFP APS': 'TFP APS — Agent de sécurité',
    'MAC APS': 'MAC APS — Recyclage',
    'SSIAP 1 initial': 'SSIAP 1 — Agent de sécurité incendie',
    'SSIAP 1 recyclage': 'SSIAP 1 — Recyclage ou Remise à niveau',
    'SSIAP 1 remise à niveau': 'SSIAP 1 — Recyclage ou Remise à niveau',
    "SSIAP 2 initial": "SSIAP 2 — Chef d'équipe incendie",
    'SSIAP 2 recyclage': 'SSIAP 2 — Recyclage ou Remise à niveau',
    'SSIAP 2 remise à niveau': 'SSIAP 2 — Recyclage ou Remise à niveau',
    'SSIAP 3 initial': 'SSIAP 3 — Chef de service incendie',
    'SSIAP 3 recyclage': 'SSIAP 3 — Chef de service incendie',
    'SSIAP 3 remise à niveau': 'SSIAP 3 — Chef de service incendie',
    'Sauveteur Secouriste du Travail (SST)': 'SST — Sauveteur Secouriste du Travail',
    'MAC SST': 'MAC SST — Recyclage secourisme',
    'Maintien et Actualisation des Compétences SST (MAC SST)': 'MAC SST — Recyclage secourisme',
    'Habilitation H0B0': 'Habilitation électrique H0B0 / BS',
    'Taxi': 'Formation Taxi — Préparation examen',
    'VTC': 'Formation VTC — Préparation examen',
    'Passerelle Taxi vers VTC': 'Passerelle Taxi vers VTC',
    'Passerelle VTC vers Taxi': 'Passerelle VTC vers Taxi',
    'TPMR': 'TPMR — Mobilité réduite',
}

month_positions = [
    (m.start(), re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))).strip())
    for m in re.finditer(r'<h2 class="mb-4 font-display text-lg font-bold capitalize text-navy">(.*?)</h2>', site, re.S)
]

def month_for(pos):
    current = ''
    for start, label in month_positions:
        if start < pos:
            current = label
        else:
            break
    return current

def txt(fragment):
    fragment = re.sub(r'<[^>]+>', ' ', fragment)
    return re.sub(r'\s+', ' ', html.unescape(fragment)).strip()

def after_svg(row, icon):
    m = re.search(r'lucide-' + icon + r'[^>]*>.*?</svg>(.*?)(?:</span>|</div>)', row, re.S)
    return txt(m.group(1)) if m else ''

sessions = []
for match in re.finditer(r'<li class="grid grid-cols-1 gap-2 px-5 py-4[^>]*>(.*?)</li>', site, re.S):
    row = match.group(1)
    date_m = re.search(r'lucide-calendar-days[^>]*>.*?</svg>(.*?)</div>', row, re.S)
    name_m = re.search(r'<span class="text-\[14px\] font-semibold text-navy">(.*?)</span>', row, re.S)
    if not (date_m and name_m):
        continue
    name = txt(name_m.group(1))
    if name not in MONTH_MAP:
        print('FORMATION NON MAPPÉE :', name)
        continue
    mode_m = re.search(r'rounded-full bg-surface px-2\.5 py-1 text-\[11px\] font-semibold text-muted">(.*?)</span>', row, re.S)
    link_m = re.search(r'href="(/formations/[^"]+)"[^>]*>Voir la fiche', row, re.S)
    sessions.append({
        'formation': MONTH_MAP[name],
        'date': txt(date_m.group(1)),
        'mois': month_for(match.start()),
        'nom': name,
        'lieu': after_svg(row, 'map-pin'),
        'horaires': after_svg(row, 'clock'),
        'places': after_svg(row, 'users'),
        'modalite': txt(mode_m.group(1)) if mode_m else '',
        'fiche': link_m.group(1) if link_m else '',
    })

with open('inscription/sessions.js', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('/* Sessions extraites du planning UFA Campus — généré automatiquement. */\n')
    fh.write('window.UFA_SESSIONS = ')
    json.dump(sessions, fh, ensure_ascii=False, separators=(',', ':'))
    fh.write(';\n')

print('sessions exportées :', len(sessions))
print('taille octets :', len(open('inscription/sessions.js', 'rb').read()))
