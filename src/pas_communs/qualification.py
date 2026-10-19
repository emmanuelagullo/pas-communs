"""Qualification conjointe explicite, sans installation, publication ni déploiement."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile
import pas_communs


def provenance_wheel(wheel, *, racine=None):
    wheel = Path(wheel).resolve()
    racine = Path(racine or pas_communs.__file__).resolve()
    if racine.is_file():
        racine = racine.parent
    with ZipFile(wheel) as archive:
        attendus = {nom.removeprefix('pas_communs/'): archive.read(nom)
            for nom in archive.namelist() if nom.startswith('pas_communs/') and not nom.endswith('/')}
    if '__init__.py' not in attendus:
        raise ValueError('Wheel pas-communs incomplet.')
    presents = {p.relative_to(racine).as_posix() for p in racine.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if presents != set(attendus) or any((racine/nom).read_bytes() != b for nom, b in attendus.items()):
        raise ValueError('Le socle importé diffère des octets du wheel candidat (code ou ressources).')
    return {'wheel': wheel.name, 'sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
        'version': pas_communs.__version__, 'module': str(racine),
        'octets_importes_identiques': True}


def verifier_adoption(projet, provenance):
    lignes = [l.strip() for l in (projet/'requirements-communs.txt').read_text().splitlines()
        if l.strip() and not l.lstrip().startswith('#')]
    if (len(lignes) != 1 or not lignes[0].endswith('/' + provenance['wheel'] + '#sha256=' + provenance['sha256'])
            or not lignes[0].startswith('pas-communs @ https://')):
        raise ValueError('Wheel différent de la dépendance épinglée : ' + str(projet))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--socle', type=Path, required=True)
    parser.add_argument('--petits-pas', type=Path, required=True)
    parser.add_argument('--accompagnement', type=Path, required=True)
    parser.add_argument('--rapport', type=Path)
    args = parser.parse_args()
    rapport = {'socle': provenance_wheel(args.wheel), 'projets': {}, 'controles': []}
    projets = {'socle': args.socle.resolve(), 'petits-pas': args.petits_pas.resolve(),
        'accompagnement': args.accompagnement.resolve()}
    for nom, projet in projets.items():
        if nom != 'socle':
            verifier_adoption(projet, rapport['socle'])
        rapport['projets'][nom] = {
            'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=projet, text=True).strip(),
            'modifications_locales': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=projet))}
    with tempfile.TemporaryDirectory(prefix='qualification-pas-') as temp:
        env = {**os.environ, 'ACCOMPAGNEMENT_DONNEES': str(Path(temp)/'accompagnement'),
            'ACCOMPAGNEMENT_2FA': 'desactive', 'DJANGO_SETTINGS_MODULE': 'carnet.settings_tests',
            'DATABASE_URL': 'sqlite:///' + str(Path(temp)/'ecole.sqlite3')}
        commandes = [('socle', ['-m', 'unittest', 'discover', '-s', 'tests']),
            ('socle', ['tests/verifier_authentification_django.py']),
            ('petits-pas', ['-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_paquet_local.py']),
            ('petits-pas', ['-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_publier_paquets.py']),
            ('petits-pas', ['-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_publication_automatique.py']),
            ('petits-pas', ['scripts/qualifier-totp.py']),
            ('accompagnement', ['manage.py', 'check']),
            ('accompagnement', ['manage.py', 'makemigrations', '--check', '--dry-run']),
            ('accompagnement', ['manage.py', 'test', '--noinput']),
            ('accompagnement', ['-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_publication*.py'])]
        for nom, commande in commandes:
            environnement = {**env, 'DJANGO_SETTINGS_MODULE':
                'carnet.settings_tests' if nom == 'petits-pas' else 'pas_a_pas_accompagnement.settings'}
            if nom == 'socle':
                environnement.pop('DJANGO_SETTINGS_MODULE', None)
            print('Qualification :', nom, *commande, flush=True)
            subprocess.run([sys.executable, *commande], cwd=projets[nom], env=environnement, check=True)
            rapport['controles'].append({'projet': nom, 'commande': commande, 'resultat': 'reussi'})
    rapport['limites'] = ['Pas de qualification graphique, appareil PWA, TLS ou déploiement distant.',
        'Les bancs Windows/Linux et vrais Pyodide restent à exécuter dans les CI des produits.']
    texte = json.dumps(rapport, ensure_ascii=False, indent=2) + '\n'
    if args.rapport:
        args.rapport.write_text(texte, encoding='utf-8')
    print(texte)


if __name__ == '__main__':
    main()
