"""Identité déclarée et intégrité d'artefacts, sans API de forge ni secret."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sys

TAG = re.compile(r'[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[A-Za-z0-9.-]+)?\Z')


def identite(environnement=None, commit_local=lambda: ''):
    env = os.environ if environnement is None else environnement
    commit = env.get('CI_COMMIT_SHA') or env.get('GITHUB_SHA') or commit_local()
    if not re.fullmatch(r'[a-fA-F0-9]{40,64}', commit or ''):
        raise ValueError('Commit de construction introuvable.')
    tag = env.get('CI_COMMIT_TAG') or (env.get('GITHUB_REF_NAME') if env.get('GITHUB_REF_TYPE') == 'tag' else None)
    if tag and not TAG.fullmatch(tag):
        raise ValueError('Tag de version invalide.')
    return {'commit':commit.lower(), 'tag':tag, 'application_version':tag or 'dev.'+commit[:8].lower()}


def sha256(path):
    somme = hashlib.sha256()
    with Path(path).open('rb') as entree:
        while bloc := entree.read(1024**2):
            somme.update(bloc)
    return somme.hexdigest()


def decrire(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Fichier régulier requis : '+str(path))
    return {'name':path.name, 'size':path.stat().st_size, 'sha256':sha256(path)}


def manifeste(format, identite, mode, target, fichiers, environnement=None):
    env = os.environ if environnement is None else environnement
    result = {'format':format, 'schema':1, **identite, 'mode':mode, 'target':target,
        'built_at':datetime.now(timezone.utc).isoformat(), 'python':sys.version.split()[0],
        'ci':{'provider':'gitlab' if env.get('CI_PIPELINE_ID') else 'github' if env.get('GITHUB_RUN_ID') else 'local',
              'run':env.get('CI_PIPELINE_ID') or env.get('GITHUB_RUN_ID'),
              'job':env.get('CI_JOB_ID') or env.get('GITHUB_JOB'), 'attempt':env.get('GITHUB_RUN_ATTEMPT')},
        'files':[decrire(p) for p in fichiers]}
    if not result['files'] or len({f['name'] for f in result['files']}) != len(result['files']):
        raise ValueError('Fichiers absents ou noms répétés.')
    return result


def verifier(record, folder, *, format, commit=None, tag=None, mode=None, target=None):
    if not isinstance(record,dict) or record.get('format') != format or record.get('schema') != 1:
        raise ValueError('Manifeste de publication invalide.')
    for key, expected in [('commit',commit),('tag',tag),('mode',mode),('target',target)]:
        if expected is not None and record.get(key) != expected:
            raise ValueError('Manifeste incompatible : '+key)
    if tag and record.get('application_version') != tag:
        raise ValueError('Version embarquée différente du tag.')
    if not isinstance(record.get('files'),list) or not record['files']:
        raise ValueError('Liste des fichiers absente.')
    names = set()
    for entry in record['files']:
        name = entry.get('name') if isinstance(entry,dict) else None
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',name) or name in names:
            raise ValueError('Nom de fichier invalide ou répété.')
        names.add(name)
        if decrire(Path(folder)/name) != entry:
            raise ValueError('Fichier altéré : '+name)
    return names


def verifier_bundle(root, *, version, requis, application=None):
    """Contrôler les statiques d'un bundle normal ; aucune publication."""
    import json
    from pathlib import PurePosixPath
    root = Path(root)
    config = json.loads((root/'config.json').read_text())
    if config.get('testMode') is not False:
        raise ValueError('Bundle de test ou mode indéterminé : publication refusée.')
    if application is not None and config.get('application') != application:
        raise ValueError('Application du bundle incorrecte.')
    if not re.fullmatch(version, config.get('version','')):
        raise ValueError('Version du bundle invalide.')
    expected = {'config.json'}
    if not isinstance(config.get('assets'),list):raise ValueError('Liste des assets absente.')
    for asset in config['assets']:
        url = asset['url'];parts = PurePosixPath(url.removeprefix('/')).parts
        if (not url.startswith('/') or not parts or any(p in {'.','..'} for p in parts)
                or '\\' in url or url != '/'+'/'.join(parts)):
            raise ValueError("Chemin d'asset invalide.")
        name='/'.join(parts)
        if name in expected or not re.fullmatch(r'[a-f0-9]{64}',asset['sha256']):
            raise ValueError('Asset répété ou empreinte invalide.')
        expected.add(name)
        path=root.joinpath(*parts)
        if path.is_symlink() or sha256(path) != asset['sha256']:
            raise ValueError('Asset altéré : '+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != expected or not set(requis) <= actual:
        raise ValueError('Bundle incomplet ou fichiers non déclarés.')
    if any(PurePosixPath(name).name=='secret-key' or name.endswith('.sqlite3') for name in actual):
        raise ValueError('Données locales présentes dans le bundle.')
    return config
