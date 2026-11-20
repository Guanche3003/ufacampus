"""Applique au site les modifications de fiches formation enregistrées.

Usage :
    python apply_content.py                 # applique toutes les modifications
    python apply_content.py --list          # affiche les fiches modifiées
    python apply_content.py --reset CHEMIN  # restaure une fiche (ex: formations/securite/ssiap-1-initial/index.html)
    python apply_content.py --reset-all     # restaure toutes les fiches

Ce script est idempotent : un second passage ne modifie aucun fichier.
À lancer après apply_ufa.py (et après build_all.py si le site a été régénéré).
"""

import argparse
import sys

import content_engine as engine


def main():
    parser = argparse.ArgumentParser(
        description='Applique les surcharges de fiches formation au site statique.'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--list', action='store_true', help='liste les fiches modifiées')
    group.add_argument('--reset', metavar='CHEMIN', help='restaure une fiche')
    group.add_argument('--reset-all', action='store_true', help='restaure toutes les fiches')
    args = parser.parse_args()

    overrides = engine.load_overrides()

    if args.list:
        if not overrides:
            print('Aucune fiche modifiée.')
        for path in sorted(overrides):
            fields = ', '.join(sorted(k for k, v in overrides[path].items() if v.get('current')))
            print(f'{path} : {fields}')
        return 0

    if args.reset:
        if args.reset not in overrides:
            print(f'Fiche non modifiée : {args.reset}', file=sys.stderr)
            return 1
        engine.reset_page(args.reset)
        print(f'Fiche restaurée : {args.reset}')
        return 0

    if args.reset_all:
        paths = sorted(overrides)
        for path in paths:
            engine.reset_page(path)
        print(f'{len(paths)} fiche(s) restaurée(s).')
        return 0

    changed, missing = engine.apply_all()
    print(f'Fiches mises à jour : {len(changed)}')
    for path in changed:
        print(f'  {path}')
    if missing:
        print(f'Fiches introuvables : {len(missing)}', file=sys.stderr)
        for path in missing:
            print(f'  {path}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
