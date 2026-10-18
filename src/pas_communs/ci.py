"""Recette Django commune, appelable depuis chaque forge ou depuis Guix.

Installation et dépendances restent explicites dans la forge. Aucun shell,
publication, secret, modèle ou recherche d'identité dans ce lanceur.
"""
import argparse
from pathlib import Path
import subprocess
import sys


def verifier_django(racine, *, settings_tests=None, durations=None, timing=False,
                     controles=(), migrer=False, pip_check=False):
    racine = Path(racine).resolve()
    if not (racine/'manage.py').is_file():
        raise ValueError('manage.py absent du projet.')
    scripts = []
    for controle in controles:
        chemin = (racine/controle).resolve()
        if not chemin.is_relative_to(racine) or not chemin.is_file() or chemin.suffix != '.py':
            raise ValueError('Contrôle Python absent ou extérieur au projet.')
        scripts.append(chemin)
    commandes = [['manage.py','check'],['manage.py','makemigrations','--check','--dry-run']]
    if migrer:
        commandes.append(['manage.py','migrate','--noinput'])
    tests = ['manage.py','test']
    if settings_tests:tests.append('--settings='+settings_tests)
    if durations is not None:
        if durations < 0:raise ValueError('Nombre de durées négatif.')
        tests += ['--durations',str(durations)]
    if timing:tests.append('--timing')
    commandes += [tests,*[[str(script)] for script in scripts]]
    if pip_check:commandes.append(['-m','pip','check'])
    for commande in commandes:
        print('Contrôle : '+' '.join(commande),flush=True)
        subprocess.run([sys.executable,*commande],cwd=racine,check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('recette',choices=['django'])
    p.add_argument('--racine',type=Path,default=Path.cwd())
    p.add_argument('--settings-tests')
    p.add_argument('--durations',type=int)
    p.add_argument('--timing',action='store_true')
    p.add_argument('--controle',action='append',default=[])
    p.add_argument('--migrer',action='store_true')
    p.add_argument('--pip-check',action='store_true')
    args=p.parse_args()
    try:
        verifier_django(args.racine,settings_tests=args.settings_tests,durations=args.durations,
            timing=args.timing,controles=args.controle,migrer=args.migrer,pip_check=args.pip_check)
    except (ValueError,subprocess.CalledProcessError) as erreur:
        p.exit(1,str(erreur)+'\n')


if __name__=='__main__':main()
