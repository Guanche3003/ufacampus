"""Point d'entrée WSGI pour cPanel > Setup Python App (o2switch).

À renseigner dans cPanel :
    Application startup file  : passenger_wsgi.py
    Application entry point   : application

Variables à ajouter avec « Add Variable » :
    UFA_SITE_ROOT      /home/<utilisateur>/<dossier-du-domaine>
    UFA_ADMIN_USER     identifiant de l'administration
    UFA_ADMIN_PASSWORD mot de passe de l'administration
    UFA_ADMIN_PREFIX   /admin   (ou laisser vide si l'application est sur un sous-domaine)
"""

import os

# Les variables d'environnement sont lues au moment de l'import par
# content_engine et admin_server : ne pas déplacer ces lignes après l'import.
SITE_ROOT = os.environ.get('UFA_SITE_ROOT', '').strip()
if SITE_ROOT:
    os.environ['UFA_SITE_ROOT'] = os.path.abspath(os.path.expanduser(SITE_ROOT))

import admin_server  # noqa: E402

application = admin_server.application
