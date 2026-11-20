#!/usr/bin/env python3
"""Post-traitement UFA Campus à appliquer après build_all.py.

- remplace l’identité CAP Compétences Academy par UFA Campus ;
- remplace les logos, coordonnées et sous-marques ;
- réécrit les pages légales, de contact et de certification ;
- unifie le site sur un seul lieu (Neuilly-Plaisance), un seul téléphone
  (0981888222) et un seul e-mail (Ufacampus3@gmail.com) ;
- supprime les anciens certificats PDF et le bandeau obsolète.

Le script est idempotent : il peut être exécuté plusieurs fois de suite.
Les slugs et URLs existants contenant « herblay » sont conservés afin de ne
pas casser les liens internes et externes.
"""

import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE_LOGO = r"C:\Users\aghil\AppData\Local\Temp\opencode\uploads\1e27c90a-1ab9-4ee2-bca3-b6c708d7fd87\image.png"
LOGO_REL = "assets/logo-ufa-campus.png"

PHONE = "0981888222"
EMAIL = "Ufacampus3@gmail.com"
ADDRESS = "2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance"
MAPS_URL = (
    "https://www.google.com/maps/search/?api=1&amp;query="
    "2%20rue%20Vincent%20Van%20Gogh%2C%2093360%20Neuilly-Plaisance"
)

LEGAL = {
    "siren": "939 687 869",
    "siret": "939 687 869 00015",
    "rcs": "Bobigny",
    "capital": "5 000 €",
    "forme": "SAS (Société par actions simplifiée)",
    "naf": "85.59B — Autres enseignements",
    "tva": "FR52 939687869",
    "address": f"{ADDRESS}, France",
    "email": EMAIL,
    "phone": PHONE,
}

BANNER_START = '<div class="relative bg-gradient-to-r from-navy to-brand text-white print:hidden">'
BANNER_END = '</div><header'

REPLACEMENTS = [
    # Identité principale.
    ("CAP COMPÉTENCES ACADEMY", "UFA CAMPUS"),
    ("CAP Compétenses Academy", "UFA Campus"),
    ("CAP Compétences Academy", "UFA Campus"),
    ("CAP Compétenses", "UFA Campus"),
    ("CAP Compétences", "UFA Campus"),
    ("CAP COMPETENCES ACADEMY", "UFA CAMPUS"),
    ("CAP Competences Academy", "UFA Campus"),
    ("CAP COMPETENCES", "UFA CAMPUS"),
    ("CAP Competences", "UFA Campus"),
    ("ASPR FORMATION devient CAP COMPÉTENCES ACADEMY", "Notre histoire"),
    ("ASPR Formation devient UFA Campus", "Notre histoire"),
    ("ASPR FORMATION devient UFA CAMPUS", "Notre histoire"),
    ("ASPR FORMATIONSSSSS devient UFA CAMPUS", "Notre histoire"),
    ("ASPR FORMATIONSSSS devient UFA CAMPUS", "Notre histoire"),
    ("ASPR FORMATIONSS devient UFA CAMPUS", "Notre histoire"),
    ("UFA CAMPUS devient UFA CAMPUS", "Notre histoire"),
    ("UFA Campus devient UFA Campus", "Notre histoire"),
    # Ancre résiduelle dans un guide (href et id).
    ("l-accompagnement-de-cap-competences-academy-a-herblay-95",
     "l-accompagnement-de-ufa-campus-a-herblay-95"),
    # Sous-marques.
    ("CAP Secure Academy", "UFA Campus Sécurité"),
    ("CAP Secur Academy", "UFA Campus Sécurité"),
    ("CAP Secure", "UFA Campus Sécurité"),
    ("CAP Transport Academy", "UFA Campus Transport"),
    ("CAP Transport", "UFA Campus Transport"),
    # Logos.
    ("/assets/remote/cap-competences-academy-logo.png", f"/{LOGO_REL}"),
    ("/assets/remote/aspr-formation-logo-v2.png", f"/{LOGO_REL}"),
    ("https://capacademy.fr/cap-competences-academy-logo.png", f"https://capacademy.fr/{LOGO_REL}"),
    # Coordonnées.
    ("01 39 09 01 99", "+33 1 39 09 01 99"),
    ("0139090199", "+33139090199"),
    ("0033139090199", "+33139090199"),
    ("07 58 48 26 04", "+33 6 50 10 66 40"),
    ("0758482604", "+33650106640"),
    ("0033758482604", "+33650106640"),
    ("wa.me/33758482604", "wa.me/33650106640"),
    ("contact@capacademy.fr", "contact@aspr-formations.fr"),
    ("accueil@capacademy.fr", "contact@aspr-formations.fr"),
    # Mentions légales obsolètes.
    ("991 407 198 00027", LEGAL["siret"]),
    ("991 407 198", LEGAL["siren"]),
    ("FR40991407198", LEGAL["tva"]),
    ("FR41399687869", LEGAL["tva"]),
    ("RCS 991 407 198 R.C.S. Pontoise", f"{LEGAL['siren']} R.C.S. {LEGAL['rcs']}"),
    ("R.C.S. Pontoise", f"R.C.S. {LEGAL['rcs']}"),
    ("EURL (Entreprise unipersonnelle à responsabilité limitée)", LEGAL["forme"]),
    ("Capital social : <!-- -->100 €", f"Capital social : <!-- -->{LEGAL['capital']}"),
    ("85.59A — Formation continue d&#x27;adultes", LEGAL["naf"]),
    ("85.59A", "85.59B"),
    ("SASU au capital de 1 000 €", f"SAS au capital de {LEGAL['capital']}"),
    ("SASU (Société par actions simplifiée unipersonnelle)", LEGAL["forme"]),
    ("2-4 rue Vincent Van Gogh", "2 rue Vincent Van Gogh"),
    ("2-4 Rue Vincent Van Gogh", "2 Rue Vincent Van Gogh"),
    ("4-2 rue Vincent van Gogh", "2 rue Vincent Van Gogh"),
    ("11 93 12064 93", ""),
    # Certification : suppressions des références CAP non transférables.
    ("certificat délivré par QUALITIA Certification, accréditation COFRAC n°5-0617",
     "certification Qualiopi au titre des actions de formation"),
    ("QUALITIA Certification (COFRAC n°5-0617)", "Certifié Qualiopi"),
    ("QUALITIA Certification — n° 26FOR00069.1", "Certification Qualiopi"),
    ("QUALITIA Certification, certificat n° 26FOR00069.1", "Certification Qualiopi"),
    ("certifié QUALITIA Certification (Qualiopi — certificat n° 26FOR00069.1)",
     "certifié Qualiopi au titre des actions de formation"),
    ("Certifié Qualiopi (<!-- -->QUALITIA Certification<!-- -->)", "Certifié Qualiopi"),
    ("QUALITIA Certification", "Certification Qualiopi"),
    ("Certificat de conformité n°<!-- --> <!-- -->26FOR00069.1", "Certification Qualiopi — actions de formation"),
    ("26FOR00069.1", "Qualiopi"),
]

# Coordonnées uniques : un seul lieu, un seul téléphone, un seul e-mail.
CONTACT_REPLACEMENTS = [
    ("+33 1 39 09 01 99", PHONE),
    ("+33139090199", PHONE),
    ("01 39 09 01 99", PHONE),
    ("0139090199", PHONE),
    ("0033139090199", PHONE),
    ("+33 6 50 10 66 40", PHONE),
    ("+33650106640", PHONE),
    ("06 50 10 66 40", PHONE),
    ("0650106640", PHONE),
    ("0758482604", PHONE),
    ("0033758482604", PHONE),
    ("+33 9 81 88 82 22", PHONE),
    ("+33981888222", PHONE),
    ("09 81 88 82 22", PHONE),
    ("wa.me/33650106640", "wa.me/33981888222"),
    ("wa.me/33758482604", "wa.me/33981888222"),
    ("contact@aspr-formations.fr", EMAIL),
    ("asprherblay@gmail.com", EMAIL),
    ("contact@capacademy.fr", EMAIL),
    ("accueil@capacademy.fr", EMAIL),
    # Itinéraire de l’ancien centre de Herblay -> siège de Neuilly-Plaisance.
    ("Gare de Saint-Ouen-l&#x27;Aumône Liesse (RER C / ligne H), puis bus 1225, arrêt « Les Tilleuls ».",
     "Métro Robespierre (ligne 9), puis quelques minutes à pied."),
    # Lien Google Maps de l’ancienne adresse.
    ("https://www.google.com/maps/search/?api=1&amp;query=27%20rue%20du%20Gros%20Murger%2C%2095220%20Herblay",
     MAPS_URL),
]

# Remplacements de lieu. Les occurrences minuscules (slugs, URLs, ancres)
# sont masquées avant ces remplacements puis restaurées telles quelles.
PLACEHOLDER = '@@UFAKEEP{}@@'
LOWER_HERBLAY = re.compile(r'[a-z0-9@/:._?=&%+-]*herblay[a-z0-9@/:._?=&%+-]*')
PLACE_REPLACEMENTS = [
    ("Herblay (Val-d&#x27;Oise)", "Neuilly-Plaisance (Seine-Saint-Denis)"),
    ("Herblay (Val-d'Oise)", "Neuilly-Plaisance (Seine-Saint-Denis)"),
    ("Herblay (95)", "Neuilly-Plaisance (93)"),
    ("Herblay-sur-Seine", "Neuilly-Plaisance"),
    ("Herblay", "Neuilly-Plaisance"),
    ("95220", "93360"),
    # Ancienne rue du centre de Herblay -> siège de Neuilly-Plaisance.
    ("27 rue du Gros Murger", "2 rue Vincent Van Gogh"),
    # Certains blocs répètent l’adresse après un commentaire Next.js.
    ("2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance<!-- -->, 93360 Neuilly-Plaisance",
     "2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance"),
    ("2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance, 93360 Neuilly-Plaisance",
     "2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance"),
    # Herblay était dans le Val-d'Oise ; Neuilly-Plaisance est en Seine-Saint-Denis.
    ("Neuilly-Plaisance (95)", "Neuilly-Plaisance (93)"),
    ("Neuilly-Plaisance (Val-d&#x27;Oise)", "Neuilly-Plaisance (Seine-Saint-Denis)"),
    ("Neuilly-Plaisance (Val-d'Oise)", "Neuilly-Plaisance (Seine-Saint-Denis)"),
    ('"addressRegion":"Val-d\'Oise"', '"addressRegion":"Seine-Saint-Denis"'),
    ('"addressRegion":"Val-d&#x27;Oise"', '"addressRegion":"Seine-Saint-Denis"'),
]

FOOTER_PATTERN = re.compile(r'UFA Campus<!-- --> · .*?<!-- -->UFA Campus</p>', re.S)
FOOTER_NEW = (
    'UFA Campus<!-- --> · SAS au capital de 5 000 €<!-- --> · SIREN <!-- -->939 687 869<!-- --> · '
    'SIRET <!-- -->939 687 869 00015<!-- --> · RCS Bobigny · NAF 85.59B<!-- --> · TVA <!-- -->FR52 939687869<!-- --> · '
    'Certifié Qualiopi<!-- --> · ©<!-- --> <!-- -->2026<!-- --> <!-- -->UFA Campus'
)

LINKEDIN_PATTERN = re.compile(
    r'<a\b[^>]*href="https://www\.linkedin\.com/in/cap-competences-2083903a6"[^>]*>.*?</a>',
    re.S,
)

LEGAL_NEW = f'''<div id="mentions-legales" class="scroll-mt-24"><h2 class="mb-2 font-display text-lg font-bold text-navy">Éditeur du site</h2><div class="space-y-1"><p>Le site <strong>UFA Campus</strong> est édité par la société <strong>UFA Campus</strong>, {LEGAL['forme']} au capital de {LEGAL['capital']}, dont le siège social est situé {LEGAL['address']}</p><p>Raison sociale : <!-- -->UFA Campus</p><p>Forme juridique : <!-- -->{LEGAL['forme']}</p><p>Capital social : <!-- -->{LEGAL['capital']}</p><p>Siège social : <!-- -->{LEGAL['address']}</p><p>SIREN : <!-- -->{LEGAL['siren']}</p><p>SIRET (siège) : <!-- -->{LEGAL['siret']}</p><p>RCS : <!-- -->{LEGAL['siren']}<!-- --> R.C.S. <!-- -->{LEGAL['rcs']}</p><p>N° TVA intracommunautaire : <!-- -->{LEGAL['tva']}</p><p>Code NAF / APE : <!-- -->{LEGAL['naf']}</p><p>Contact administratif : <!-- --><a href="mailto:{LEGAL['email']}" class="text-brand hover:underline">{LEGAL['email']}</a> — <a href="tel:{PHONE}" class="text-brand hover:underline">{LEGAL['phone']}</a></p></div></div><div><h2 class="mb-2 font-display text-lg font-bold text-navy">Présidence</h2><p class="text-sm text-muted">ASPR FORMATION, présidente de UFA Campus. TALEB Said, président directeur général d’ASPR FORMATION.</p></div><div><h2 class="mb-2 font-display text-lg font-bold text-navy">Équipe dirigeante ASPR FORMATION</h2><p class="text-sm text-muted">RAMDAN BEY Azzedine, Directeur général · TALEB Said, Directeur général · SLIMANI Nesrine, Responsable administration · AMROUN Fatma, Responsable commercial et communication.</p></div><div><h2 class="mb-2 font-display text-lg font-bold text-navy">Certification qualité</h2><p class="text-sm text-muted">UFA Campus est certifié Qualiopi au titre des actions de formation.</p></div>'''

CGV_NEW = f'''<section><h2 class="text-xl font-bold text-navy">1. Objet</h2><p>Les présentes conditions générales de vente régissent les prestations de formation proposées par UFA Campus, {LEGAL['forme']} au capital de {LEGAL['capital']}, dont le siège social est situé {LEGAL['address']}, immatriculée au RCS de {LEGAL['rcs']} sous le numéro {LEGAL['siren']} (SIRET {LEGAL['siret']}, NAF 85.59B, TVA {LEGAL['tva']}). Contact : {LEGAL['email']} — {LEGAL['phone']}.</p><p>UFA Campus est certifié Qualiopi au titre des actions de formation.</p></section><section><h2 class="text-xl font-bold text-navy">2. Inscription</h2><p>Toute inscription est confirmée par écrit. Les modalités, le calendrier, le lieu et le prix sont précisés dans la convention ou le devis transmis au stagiaire ou à l’entreprise.</p></section>'''

RGPD_NEW = f'''<section><h2 class="text-xl font-bold text-navy">1. Responsable du traitement</h2><p>Le responsable du traitement est UFA Campus, {LEGAL['forme']} au capital de {LEGAL['capital']}, siège social : {LEGAL['address']}, immatriculée au RCS de {LEGAL['rcs']} sous le numéro {LEGAL['siren']} (SIRET {LEGAL['siret']}, TVA {LEGAL['tva']}, NAF 85.59B). Pour toute question relative à vos données personnelles, écrivez à <a href="mailto:{LEGAL['email']}" class="text-brand hover:underline">{LEGAL['email']}</a> ou appelez le <a href="tel:{PHONE}" class="text-brand hover:underline">{LEGAL['phone']}</a>.</p></section>'''

_CONTACT_CARDS_RAW = '''<div class="text-[13px] font-bold text-navy">Siège — Neuilly-Plaisance</div><div class="text-[13px] text-muted">2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance</div></div></div><div class="flex items-start gap-3 rounded-xl bg-surface p-4"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-map-pin mt-0.5 text-brand" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path><circle cx="12" cy="10" r="3"></circle></svg><div><div class="text-[13px] font-bold text-navy">Centre — Herblay-sur-Seine</div><div class="text-[13px] text-muted">27 rue du Gros Murger, 95220 Herblay-sur-Seine</div></div></div><div class="flex items-start gap-3 rounded-xl bg-surface p-4"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-phone mt-0.5 text-brand" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92Z"></path></svg><div><div class="text-[13px] font-bold text-navy">Téléphone</div><div class="text-[13px] text-muted"><a href="tel:+33981888222" class="hover:underline">+33 9 81 88 82 22</a> · <a href="tel:+33650106640" class="hover:underline">+33 6 50 10 66 40</a></div></div></div><div class="flex items-start gap-3 rounded-xl bg-surface p-4"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-mail mt-0.5 text-brand" aria-hidden="true"><rect width="20" height="16" x="2" y="4" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg><div><div class="text-[13px] font-bold text-navy">E-mail</div><div class="text-[13px] text-muted"><a href="mailto:contact@aspr-formations.fr" class="hover:underline">contact@aspr-formations.fr</a></div><div class="text-[13px] text-muted"><a href="mailto:asprherblay@gmail.com" class="hover:underline">asprherblay@gmail.com</a> (Herblay)</div></div></div><div class="flex items-start gap-3 rounded-xl bg-surface p-4"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-clock mt-0.5 text-brand" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg><div><div class="text-[13px] font-bold text-navy">Horaires</div><div class="text-[13px] text-muted">Du lundi au vendredi, 9h–18h</div></div></div></div></div>'''

PHONE_CARD_PATTERN = re.compile(
    r'(<div class="text-\[13px\] font-bold text-navy">Téléphone</div>)'
    r'<div class="text-\[13px\] text-muted">(?:(?!</div>).)*</div>',
    re.S,
)
EMAIL_CARD_PATTERN = re.compile(
    r'(<div class="text-\[13px\] font-bold text-navy">E-mail</div>)'
    r'<div class="text-\[13px\] text-muted">(?:(?!</div>).)*</div>'
    r'<div class="text-\[13px\] text-muted">(?:(?!</div>).)*</div>',
    re.S,
)


def remove_center_card(s: str) -> str:
    """Supprime la carte « Centre — Herblay-sur-Seine » du bloc contact."""
    i = s.find('Centre — Herblay-sur-Seine')
    if i < 0:
        return s
    start = s.rfind('<div class="flex items-start gap-3 rounded-xl bg-surface p-4">', 0, i)
    end = s.find('</div></div></div>', i)
    if start < 0 or end < 0:
        return s
    return s[:start] + s[end + len('</div></div></div>'):]


def unify_contact_cards(s: str) -> str:
    """Réduit les cartes Téléphone et E-mail à un seul moyen de contact."""
    s = PHONE_CARD_PATTERN.sub(
        lambda m: m.group(1)
        + f'<div class="text-[13px] text-muted"><a href="tel:{PHONE}" class="hover:underline">{PHONE}</a></div>',
        s,
    )
    s = EMAIL_CARD_PATTERN.sub(
        lambda m: m.group(1)
        + f'<div class="text-[13px] text-muted"><a href="mailto:{EMAIL}" class="hover:underline">{EMAIL}</a></div>',
        s,
    )
    return s


CONTACT_CARDS_NEW = unify_contact_cards(remove_center_card(_CONTACT_CARDS_RAW))

OLD_PDFS = ['/certificat-qualiopi.pdf', '/cap-agrement-cnaps.pdf', '/cap-habilitation-sst-inrs.pdf']


def replace_place(s: str) -> str:
    """Remplace Herblay par Neuilly-Plaisance sans toucher aux slugs/URLs."""
    protected: list[str] = []

    def protect(m: re.Match) -> str:
        protected.append(m.group(0))
        return PLACEHOLDER.format(len(protected) - 1)

    s = LOWER_HERBLAY.sub(protect, s)
    for old, new in PLACE_REPLACEMENTS:
        s = s.replace(old, new)
    s = re.sub(
        r"(Neuilly-Plaisance[^<]{0,80}?)dans le Val-d(?:&#x27;|')Oise",
        r"\1en Seine-Saint-Denis",
        s,
    )
    for idx, value in enumerate(protected):
        s = s.replace(PLACEHOLDER.format(idx), value)
    return s


def replace_between(s: str, start: str, end: str, replacement: str, path: str) -> str:
    i = s.find(start)
    j = s.find(end, i + len(start)) if i >= 0 else -1
    if i < 0 or j < 0:
        raise RuntimeError(f'{path}: bloc introuvable ({start[:60]})')
    return s[:i] + replacement + s[j:]


def remove_banner(s: str) -> str:
    i = s.find(BANNER_START)
    if i < 0:
        return s
    j = s.find(BANNER_END, i)
    if j < 0:
        raise RuntimeError('fin du bandeau introuvable')
    return s[:i] + s[j + len('</div>'):]


def patch_logo_tags(s: str) -> str:
    s = s.replace('width="2000" height="672"', 'width="640" height="640"')
    s = s.replace('class="h-12 w-auto max-w-none object-contain lg:h-20"',
                  'class="h-12 w-auto max-w-full object-contain lg:h-20"')
    return s.replace('class="h-16 w-auto"',
                     'class="h-16 w-auto max-w-full object-contain"')


def patch_html(path: str) -> bool:
    rel = os.path.relpath(path, ROOT).replace('\\', '/')
    s = open(path, encoding='utf-8', errors='replace').read()
    original = s

    s = remove_banner(s)
    for old, new in REPLACEMENTS:
        s = s.replace(old, new)

    # Bloc de contact : une seule adresse, un seul téléphone, un seul e-mail.
    if rel == 'contact/index.html':
        if 'Siège — Neuilly-Plaisance' not in s:
            start = '<div class="text-[13px] font-bold text-navy">Siège</div>'
            end = '<div class="mt-16"><h2 class="mb-6 text-center font-display text-2xl font-extrabold text-navy">Nous trouver</h2>'
            i = s.find(start)
            j = s.find(end, i) if i >= 0 else -1
            if i >= 0 and j >= 0:
                s = s[:i] + CONTACT_CARDS_NEW + s[j:]
        s = remove_center_card(s)
        s = unify_contact_cards(s)

    for old, new in CONTACT_REPLACEMENTS:
        s = s.replace(old, new)
    s = replace_place(s)

    # Version des fichiers statiques : évite de servir une ancienne copie en cache.
    s = re.sub(r'(href="/site-fixes\.css)(?:\?v=\d+)?(")', r'\1?v=7\2', s)
    s = re.sub(r'(src="/site\.js)(?:\?v=\d+)?(")', r'\1?v=7\2', s)

    s = patch_logo_tags(s)
    s = FOOTER_PATTERN.sub(FOOTER_NEW + '</p>', s)
    s = LINKEDIN_PATTERN.sub('', s)

    # Anciens numéros CNAPS/INRS du pied de page uniquement (le contenu des
    # fiches formation n'est pas modifié).
    s = re.sub(
        r'<p class="mt-3 text-\[11px\] leading-relaxed text-white/50">'
        r'Autorisation et habilitation : <!-- -->.*?</p>',
        '', s, flags=re.S,
    )

    # Anciens PDF : remplacements par des mentions "en cours de mise à jour".
    for src in OLD_PDFS:
        s = re.sub(r'<a\b[^>]*href="' + re.escape(src) + r'"[^>]*>.*?</a>',
                   '<span class="inline-flex items-center gap-2 rounded-lg bg-surface px-3 py-2 text-[13px] text-muted">Certification Qualiopi — document en cours de mise à jour</span>',
                   s, flags=re.S)
        s = re.sub(r'<object\b[^>]*data="' + re.escape(src) + r'".*?</object>',
                   '<div class="rounded-xl border border-line bg-surface p-8 text-center text-sm text-muted">Document en cours de mise à jour. Contactez-nous pour obtenir la pièce officielle.</div>',
                   s, flags=re.S)

    if rel == 'mentions-legales/index.html':
        s = replace_between(
            s,
            '<div id="mentions-legales" class="scroll-mt-24">',
            '<div><h2 class="mb-2 font-display text-lg font-bold text-navy">Hébergement',
            LEGAL_NEW,
            rel,
        )

    if rel == 'cgv/index.html':
        i = s.find('<section><h2 class="text-xl font-bold text-navy">1. Objet</h2>')
        j = s.find('<p class="text-sm text-slate-500">Dernière mise à jour')
        if i >= 0 and j >= 0:
            s = s[:i] + CGV_NEW + s[j:]

    if rel == 'politique-confidentialite/index.html':
        s = replace_between(
            s,
            '<section><h2 class="text-xl font-bold text-navy">1. Responsable du traitement</h2>',
            '<section><h2 class="text-xl font-bold text-navy">2. Données collectées</h2>',
            RGPD_NEW,
            rel,
        )

    if rel == 'certification-qualiopi/index.html':
        for label in ['N° de certificat', 'Organisme certificateur', 'Validité', 'Site certifié']:
            s = re.sub(
                r'<div class="flex items-start gap-3 rounded-xl border border-line bg-white p-4">'
                r'(?:(?!</div></div>).)*?' + re.escape(label) + r'(?:(?!</div></div>).)*?</div></div>',
                '', s, flags=re.S,
            )
        for ident in ['2026-0137368-FOR-1101008', 'H39494/2026/SST-1/O/12', '20/10/2026',
                      '19/06/2026', 'jusqu&#x27;au 18/06/2031']:
            s = re.sub(
                r'<div class="flex gap-1\.5"><dt class="font-semibold text-navy">[^<]*(?:<!-- -->)?[^<]*</dt>'
                r'<dd class="text-body">' + re.escape(ident) + r'</dd></div>',
                '', s,
            )
        s = s.replace('<dl class="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[13px]"></dl>', '')

    if s != original:
        open(path, 'w', encoding='utf-8').write(s)
        return True
    return False


def create_assets() -> None:
    os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
    shutil.copyfile(SOURCE_LOGO, os.path.join(ROOT, LOGO_REL))
    shutil.copyfile(SOURCE_LOGO, os.path.join(ROOT, 'icon-cap.png'))

    manifest = {
        "name": "UFA Campus",
        "short_name": "UFA Campus",
        "description": "UFA Campus — organisme de formation certifié Qualiopi.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0D1B3E",
        "theme_color": "#0D1B3E",
        "icons": [{"src": "/icon-cap.png", "sizes": "640x640", "type": "image/png"}],
    }
    with open(os.path.join(ROOT, 'manifest.webmanifest'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')

    for name in OLD_PDFS:
        path = os.path.join(ROOT, name.lstrip('/'))
        if os.path.exists(path):
            os.remove(path)


def patch_site_js() -> None:
    path = os.path.join(ROOT, 'site.js')
    s = open(path, encoding='utf-8').read()
    original = s
    for old, new in REPLACEMENTS:
        s = s.replace(old, new)
    for old, new in CONTACT_REPLACEMENTS:
        s = s.replace(old, new)
    s = replace_place(s)
    s = s.replace("['ASPR devient CAP', '/aspr-devient-cap-competences/']",
                  "['Notre histoire', '/a-propos/']")
    if s != original:
        open(path, 'w', encoding='utf-8').write(s)


def main() -> None:
    create_assets()
    updated = 0
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in ('_next', 'assets', '_backup_before_ufa')]
        for name in fn:
            if name.endswith('.html'):
                updated += patch_html(os.path.join(dp, name))
    patch_site_js()
    print(f'Pages HTML traitées : {updated}')
    print('Assets, manifeste, site.js et anciens PDF mis à jour.')


if __name__ == '__main__':
    main()
