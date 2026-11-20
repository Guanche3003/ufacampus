# UFA Campus — copie statique rebrandée

Reproduction statique de **184 pages** de capacademy.fr, avec l’identité **UFA Campus** appliquée sur l’ensemble du site. Le rebranding ne modifie ni le catalogue ni le contenu pédagogique des fiches ; un outil interne permet d’éditer leurs titres, descriptions et dates (voir plus bas).

## Contenu

- `index.html` + un dossier par route (`planning/index.html`, `formations/.../index.html`, …) : toutes les pages générées.
- `assets/static/` : feuille de style Tailwind d’origine et polices Poppins / Inter.
- `assets/remote/` : images et ressources téléchargées depuis le site d’origine.
- `assets/logo-ufa-campus.png` et `icon-cap.png` : logo fourni, utilisé pour le header, le footer et le favicon.
- `manifest.webmanifest` : manifeste PWA local au nom de UFA Campus.
- `site-fixes.css` et `site.js` : ajustements et interactions (menus déroulants avec délai de fermeture et pont de survol, menu mobile, diaporama, carrousels, FAQ, widget de contact au survol et au clic avec priorité sur le bouton bleu, assistant conversationnel « Poser une question », cookies). Référencés avec `?v=8` dans les pages pour éviter un ancien fichier en cache.
- `build_all.py` : générateur initial (crawl de capacademy.fr, téléchargement des ressources, réécriture des liens).
- `apply_ufa.py` : post-traitement de rebranding à exécuter après `build_all.py`.
- `check_links.py` : vérification des liens internes.
- `inscription/wizard.js`, `inscription/sessions.js`, `build_sessions.py` : formulaire d’inscription en 5 étapes, sessions extraites du planning et générateur de ces sessions.
- `pages-list.txt` : liste des 184 pages générées.
- Outil d’édition interne : `admin_server.py`, `admin/`, `content_engine.py`, `apply_content.py`, `passenger_wsgi.py` (entrée WSGI o2switch) et `content/formations-overrides.json`.

## Identité et sources

- Marque : **UFA Campus** partout (titres, header, footer, textes institutionnels, alt/aria, sous-marques).
- Coordonnées, équipe et adresses : https://aspr-formations.fr/ (contact, CGU, à propos).
- Identifiants légaux : https://www.pappers.fr/entreprise/ufa-campus-939687869
  - SAS au capital de 5 000 €
  - SIREN 939 687 869 · SIRET siège 939 687 869 00015
  - RCS Bobigny · NAF 85.59B · TVA FR52 939687869
  - Siège : 2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance
- Contact unique : Ufacampus3@gmail.com · 0981888222
- Un seul lieu : 2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance (pas de centre à Herblay).
- Les slugs et URLs existants contenant `herblay` sont conservés pour ne pas casser les liens.
- Les anciens identifiants CAP et le NDA historique ont été retirés. Aucun numéro de certificat Qualiopi non vérifié n’est affiché.

## Lancer le site

Les chemins absolus (`/planning`, `/formations/...`) nécessitent un serveur HTTP local :

```bash
python -m http.server 4321
```

Puis ouvrir `http://127.0.0.1:4321/`.

## Formulaire d’inscription

La page `/inscription/` propose un parcours en **5 étapes** :

1. **Formation et session** — choix de la formation, puis des sessions réellement planifiées (dates, lieu, modalité, places, lien vers la fiche). Le choix « Dates à convenir » reste toujours disponible ; un format peut être indiqué.
2. **Coordonnées** — civilité, nom, prénom, e-mail, téléphone, date de naissance, ville, mode de contact préféré.
3. **Financement et situation** — financement envisagé, situation, employeur/OPCO, aménagements éventuels, message.
4. **Documents** — pièce d’identité, CV/diplôme, justificatif de financement et autres fichiers (plusieurs fichiers possibles). Formats acceptés : PDF, JPG, PNG, DOC, DOCX. Taille totale maximale : **10 Mo**, contrôlée avant l’envoi. Chaque fichier peut être retiré.
5. **Vérification** — récapitulatif de toute la demande, consentement RGPD, puis envoi.

La navigation est accessible au clavier, les erreurs sont affichées à côté du champ concerné et le focus est déplacé vers l’étape suivante. Le formulaire reste soumis **nativerment** (pas d’AJAX) à FormSubmit, ce qui fonctionne aussi bien sur Vercel que sur o2switch sans serveur d’application. La destination des e-mails est celle déjà configurée dans l’`action` du formulaire (`aghilles.touahri@gmail.com`) ; pensez à la vérifier si vous souhaitez recevoir les demandes sur `Ufacampus3@gmail.com`.

### Mettre à jour la liste des sessions

Les sessions affichées sont extraites de `planning/index.html`. Après chaque modification du planning :

```bash
python build_sessions.py
```

Cela régénère `inscription/sessions.js` (fichier statique, aucune dépendance). Les formations sans session planifiée affichent automatiquement le choix « Dates à convenir ».

## Modifier les fiches formation (outil interne)

Outil sans dépendance. En local, le serveur n'écoute que sur `127.0.0.1` :

```bash
python admin_server.py
```

Puis ouvrir `http://127.0.0.1:4322/`. L’interface liste les **98 fiches** (34 catalogue + 64 pages par ville), avec recherche et filtres. Pour chaque fiche, elle permet de modifier :

- titre de la page, titre affiché (H1), nom dans les données structurées ;
- description SEO, description visible, description structurée ;
- texte de « Prochaine session » et liste des sessions (une par ligne).

Les champs absents d’une fiche (ex. dates sur les pages par ville) sont désactivés. La durée, le prix et le programme pédagogique ne sont pas éditables.

### Flux de travail

1. Modifier une fiche dans l’interface puis cliquer sur **Enregistrer les modifications** : les valeurs sont écrites dans `content/formations-overrides.json` (le HTML n’est pas encore touché).
2. Cliquer sur **Appliquer au site** : `apply_content.py` réécrit les pages concernées. Les autres pages ne bougent pas.
3. **Réinitialiser la fiche** restaure les valeurs d’origine et retire la surcharge.

Équivalent en ligne de commande :

```bash
python apply_content.py                 # applique les surcharges
python apply_content.py --list          # liste les fiches modifiées
python apply_content.py --reset formations/securite/ssiap-1-initial/index.html
python apply_content.py --reset-all     # restaure toutes les fiches
```

Les surcharges sont stockées **hors du HTML** et réappliquées après une régénération. L’ordre canonique est :

```bash
python build_all.py && python apply_ufa.py && python apply_content.py && python check_links.py
```

`apply_content.py` est idempotent : un second passage ne modifie aucun fichier. `apply_ufa.py` réapplique également le formulaire d’inscription en 5 étapes depuis `content/inscription-form.html` et régénère `inscription/sessions.js` à partir du planning.

## Déploiement sur o2switch

L’offre o2switch fournit l’outil **Setup Python App** (Phusion Passenger + WSGI) dans cPanel. Le site continue d’être servi comme site **statique** par Apache ; seul l’outil d’édition tourne en Python. Les deux utilisent **le même dossier de fichiers**, donc aucune synchronisation n’est nécessaire.

> Si votre offre est un hébergement **exclusivement statique**, sans outil Setup Python App, l’éditeur ne peut pas y être exécuté : il faut alors modifier localement puis transférer les fichiers, ou activer l’outil Python dans cPanel (offre o2switch standard).

### 1. Répartir les fichiers

**Dossier public du domaine** (ex. `/home/LOGIN/votredomaine.fr/`) : tout le site statique (`index.html`, les dossiers de pages, `_next/`, `assets/`, `site.js`, `site-fixes.css`, `manifest.webmanifest`, `icon-cap.png`) **et** le dossier `content/` contenant `formations-overrides.json`.

**Dossier de l’application Python** (hors du dossier du domaine, ex. `/home/LOGIN/ufa-admin/`) : `passenger_wsgi.py`, `admin_server.py`, `content_engine.py`, `apply_content.py`, ainsi que le dossier `admin/` (interface). o2switch recommande explicitement de garder les sources Python hors du dossier lié au domaine : si l’application est arrêtée, ce dossier devient accessible directement.

Les envois se font par FTP ou par le gestionnaire de fichiers cPanel.

### 2. Créer l’application dans cPanel

1. cPanel → **Setup Python App** → **Create Application**.
2. **Python Version** : `3.11`.
3. **Application Root** : `/home/LOGIN/ufa-admin` (le dossier Python, pas celui du domaine).
4. **Application URL** : créer d’abord le sous-domaine `admin.votredomaine.fr` dans **Domaines → Sous-domaines**, puis le sélectionner. Si l’interface propose un chemin, `/admin` sur le domaine principal convient aussi.
5. **Application Startup File** : `passenger_wsgi.py`.
6. **Application Entry Point** : `application`.
7. **Passenger log file** : conserver la valeur proposée par cPanel.
8. **Add Variable** (repeat pour chacune) :

   | Variable | Valeur |
   | --- | --- |
   | `UFA_SITE_ROOT` | `/home/LOGIN/votredomaine.fr` |
   | `UFA_ADMIN_USER` | identifiant de l’administration |
   | `UFA_ADMIN_PASSWORD` | mot de passe solide |
   | `UFA_ADMIN_PREFIX` | vide pour un sous-domaine, `/admin` si monté sur le domaine principal |

9. Cliquer sur **Create**.

Aucun `requirements.txt` n’est nécessaire : le projet n’utilise que la bibliothèque standard Python.

### 3. Utilisation

- Ouvrir `https://admin.votredomaine.fr/` : le navigateur demande les identifiants HTTP Basic définis plus haut. Le site public reste sur `https://votredomaine.fr/`.
- Après **chaque modification des fichiers Python**, cliquer sur **Restart** dans Setup Python App.
- Dans l’interface, **Appliquer au site** réécrit directement les pages HTML du dossier public : pas de redéploiement à faire.
- Activer aussi le certificat SSL gratuit (Let’s Encrypt) pour le sous-domaine `admin.`.

### 4. Dépannage

- Si cPanel a généré un `passenger_wsgi.py` « Hello World », remplacer son contenu par celui du projet puis cliquer sur **Restart**.
- Page d’erreur Passenger : ajouter `PassengerAppEnv development` et `PassengerFriendlyErrorPages on` dans le `.htaccess` du dossier du sous-domaine (cPanel le crée automatiquement), puis relire le **Passenger log file** et **cPanel → Erreurs Apache**.
- Erreur d’écriture : vérifier que `UFA_SITE_ROOT` pointe bien sur le dossier public et que les fichiers appartiennent à l’utilisateur cPanel.
- Mot de passe oublié : modifier la variable `UFA_ADMIN_PASSWORD` dans Setup Python App puis **Restart**.

## Vérifications

- 184 pages générées.
- 13 970 liens internes de navigation vérifiés (`python check_links.py`), 0 cible manquante.
- Aucune image locale manquante.
- Menus, FAQ, diaporamas, carrousels, widget contact et cookies vérifiés.
