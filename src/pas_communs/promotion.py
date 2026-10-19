"""Contrôles de promotion communs ; aucun appel de forge ni décision produit."""
from pathlib import Path
import re
import stat
from zipfile import ZipFile
from .chemins import composants_portables, verifier_arbre
from .publication import TAG


def verifier_execution(run, tag, *, depot, workflow):
    if (not isinstance(tag, str) or not TAG.fullmatch(tag)
            or run.get('head_repository', {}).get('full_name') != depot
            or run.get('conclusion') != 'success' or run.get('status') != 'completed'
            or run.get('path') != workflow or run.get('head_branch') != tag
            or run.get('event') not in ('push', 'workflow_dispatch')):
        raise ValueError('Choisir une construction réussie du tag, avec le workflow des programmes.')
    if not re.fullmatch(r'[a-f0-9]{40}', run.get('head_sha', '')):
        raise ValueError('Commit de construction invalide.')
    return run['head_sha']


def verifier_tag_distant(lignes, tag, commit):
    """Interpréter ls-remote, y compris un tag annoté ; les E/S restent produit."""
    refs = dict((ref, sha) for sha, ref in (ligne.split('\t') for ligne in lignes.splitlines()))
    ref = 'refs/tags/' + tag
    if refs.get(ref + '^{}', refs.get(ref)) != commit:
        raise ValueError('Tag absent ou différent sur une forge.')


def selectionner_evenement(evenement, nom_evenement, reference, *, depot, workflow):
    if nom_evenement == 'workflow_dispatch':
        if reference != 'refs/heads/main':
            raise ValueError('Lancer la reprise manuelle depuis main.')
        valeurs = evenement.get('inputs', {})
        run, tag = str(valeurs.get('run', '')), valeurs.get('tag', '')
        if not run.isdecimal() or int(run) <= 0 or not isinstance(tag, str) or not TAG.fullmatch(tag):
            raise ValueError('Construction positive et tag numérique requis.')
        return run, tag
    if nom_evenement != 'workflow_run':
        raise ValueError('Événement de publication inattendu.')
    run = evenement.get('workflow_run', {})
    if (evenement.get('action') != 'completed' or run.get('event') != 'push'
            or run.get('conclusion') != 'success' or run.get('status') != 'completed'
            or run.get('head_repository', {}).get('full_name') != depot
            or run.get('path') != workflow or not TAG.fullmatch(run.get('head_branch') or '')):
        return None
    verifier_execution(run, run['head_branch'], depot=depot, workflow=workflow)
    identifiant = str(run.get('id', ''))
    if not identifiant.isdecimal() or int(identifiant) <= 0:
        raise ValueError('Identifiant de construction invalide.')
    return identifiant, run['head_branch']


def extraire_artefact(archive, dossier):
    """Petits artefacts plats uniquement ; fusion identique entre plateformes."""
    dossier = Path(dossier)
    with ZipFile(archive) as zipped:
        entrees = zipped.infolist()
        if len(entrees) > 20 or sum(e.file_size for e in entrees) > 1024**3:
            raise ValueError('Artefact trop volumineux.')
        verifier_arbre(e.filename for e in entrees)
        for entree in entrees:
            if (len(composants_portables(entree.filename)) != 1 or entree.is_dir()
                    or stat.S_ISLNK(entree.external_attr >> 16)):
                raise ValueError('Chemin non autorisé dans un artefact.')
            destination = dossier / entree.filename
            if destination.is_symlink():
                raise ValueError('Lien symbolique dans la destination.')
            contenu = zipped.read(entree)
            if destination.exists():
                if destination.read_bytes() != contenu:
                    raise ValueError('Fichier divergent entre artefacts : ' + entree.filename)
            else:
                destination.write_bytes(contenu)
