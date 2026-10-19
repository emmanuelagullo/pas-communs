"""Moteur ZIP/SQLite partagé, sans Django ni dépendance native supplémentaire."""

import hashlib
import json
import shutil
import sqlite3
import stat
import tempfile
import uuid
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from .chemins import composants_portables, verifier_arbre


VERSION = 1
TAILLE_MAX = 10 * 1024**3
FICHIERS_MAX = 100_000
RESULTAT = "resultat-restauration.json"


@dataclass(frozen=True)
class ProfilPaquet:
    """Identité applicative et disposition ; aucune table métier dans le socle."""
    application: str
    format: str
    base: str
    accepter_sans_application: bool = False

    def __post_init__(self):
        if not self.application or not self.format:
            raise ValueError("Identité de paquet vide.")
        if (not self.base or self.base in {".", "..", "secret-key", "manifest.json", "media"}
                or "/" in self.base or "\\" in self.base or ":" in self.base):
            raise ValueError("Nom de base invalide.")
        composants_portables(self.base)


@dataclass(frozen=True)
class Preparation:
    etape: Path
    date_sauvegarde: str | None
    ancien: Path
    nom_archive: str
    nombre_medias: int


def _empreinte(fichier):
    somme = hashlib.sha256()
    while bloc := fichier.read(1024 * 1024):
        somme.update(bloc)
    return somme.hexdigest()


def creer_sauvegarde(paquet, destination, *, profil, taille_bloc=None,
                     metadonnees=None, fichiers_externes=None):
    """Écrire un ZIP cohérent de la base, de la clé et des médias."""
    paquet = Path(paquet)
    metadonnees = metadonnees or {}
    if set(metadonnees) & {"format", "version", "application", "files", "created_at"}:
        raise ValueError("Métadonnées réservées au moteur de sauvegarde.")
    for nom in (profil.base, "secret-key"):
        if not (paquet / nom).is_file() or (paquet / nom).is_symlink():
            raise ValueError("Base ou clé absente, ou lien symbolique refusé.")
    if taille_bloc is not None and not 0 < taille_bloc <= 1024**2:
        raise ValueError("Taille de bloc invalide")
    with tempfile.TemporaryDirectory(prefix=".copie-sqlite-", dir=paquet.parent) as dossier:
        base = Path(dossier) / profil.base
        with closing(sqlite3.connect(paquet / profil.base)) as origine:
            with closing(sqlite3.connect(base)) as copie:
                origine.backup(copie)
        fichiers = {
            profil.base: base,
            "secret-key": paquet / "secret-key",
        }
        if (paquet / "media").is_symlink():
            raise ValueError("Lien symbolique refusé pour le dossier des médias.")
        for chemin in sorted((paquet / "media").rglob("*")):
            if chemin.is_symlink():
                raise ValueError(f"Lien symbolique refusé dans les médias : {chemin}")
            if chemin.is_file():
                fichiers[chemin.relative_to(paquet).as_posix()] = chemin
        empreintes = {}
        externes = fichiers_externes or {}
        for nom in externes:
            if not nom.startswith('media/'):
                raise ValueError("Chemin de média externe invalide.")
        verifier_arbre([*fichiers, *externes, 'manifest.json'])
        with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
            for nom, chemin in fichiers.items():
                with chemin.open("rb") as source:
                    empreintes[nom] = _empreinte(source)
                if taille_bloc is None:
                    archive.write(chemin, nom)
                else:
                    # OPFS : amortir les appels synchrones sans charger le fichier.
                    info = ZipInfo.from_file(chemin, nom)
                    info.compress_type = ZIP_DEFLATED
                    with chemin.open("rb") as source, archive.open(info, "w") as sortie:
                        shutil.copyfileobj(source, sortie, length=taille_bloc)
            for nom, (taille, ouvrir) in (fichiers_externes or {}).items():
                if (not nom.startswith("media/") or any(p in {"", ".", ".."} for p in nom.split("/"))
                        or "\\" in nom or nom in fichiers or nom.endswith("/")):
                    raise ValueError("Chemin de média externe invalide.")
                empreinte, copies = hashlib.sha256(), 0
                info = ZipInfo(nom)
                info.compress_type = ZIP_DEFLATED
                with ouvrir() as source, archive.open(info, "w", force_zip64=True) as sortie:
                    while bloc := source.read(taille_bloc or 1024**2):
                        copies += len(bloc)
                        if copies > taille:
                            raise ValueError("Un média a changé pendant l'export.")
                        empreinte.update(bloc)
                        sortie.write(bloc)
                if copies != taille:
                    raise ValueError("Un média a changé pendant l'export.")
                empreintes[nom] = empreinte.hexdigest()
            archive.writestr(
                "manifest.json",
                json.dumps({
                    "format": profil.format, "version": VERSION, "application": profil.application,
                    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "files": empreintes,
                    **metadonnees,
                }),
            )


def preparer_restauration(source, parent, nom_paquet="paquet-autonome", *,
                         profil, taille_max=TAILLE_MAX, fichiers_max=FICHIERS_MAX,
                         migrations_connues=None):
    """Parcours synchrone serveur/bureau du même validateur progressif."""
    travail = iterer_restauration(source, parent, nom_paquet, profil=profil, taille_max=taille_max,
                                 fichiers_max=fichiers_max, migrations_connues=migrations_connues)
    while True:
        try:
            next(travail)
        except StopIteration as fin:
            return fin.value


def iterer_restauration(source, parent, nom_paquet="paquet-autonome", *,
                       profil, taille_max=TAILLE_MAX, fichiers_max=FICHIERS_MAX,
                       migrations_connues=None, ouvrir_destination=None):
    """Valider le ZIP avant de préparer un nouveau paquet sans toucher à l'ancien."""
    with ZipFile(source) as archive:
        entrees = archive.infolist()
        noms = [entree.filename for entree in entrees]
        if len(noms) != len(set(noms)) or len(noms) > fichiers_max:
            raise ValueError("Archive trop volumineuse ou noms de fichiers répétés.")
        if "manifest.json" not in noms:
            raise ValueError("Manifeste du paquet absent.")
        if archive.getinfo("manifest.json").file_size > 1024 * 1024:
            raise ValueError("Manifeste trop volumineux.")
        manifeste = json.loads(archive.read("manifest.json"))
        if not isinstance(manifeste, dict):
            raise ValueError("Manifeste invalide.")
        application = manifeste.get("application")
        if application != profil.application and not (
                "application" not in manifeste and profil.accepter_sans_application):
            raise ValueError("Sauvegarde d’une autre application ou identité absente.")
        if manifeste.get("format") != profil.format or manifeste.get("version") != VERSION:
            raise ValueError("Format de sauvegarde inconnu.")
        attendus = manifeste.get("files")
        date_sauvegarde = manifeste.get("created_at")
        if date_sauvegarde is not None:
            try:
                date_sauvegarde = datetime.fromisoformat(date_sauvegarde).isoformat()
            except (TypeError, ValueError) as exc:
                raise ValueError("Date de sauvegarde invalide.") from exc
        if not isinstance(attendus, dict) or not {profil.base, "secret-key"} <= attendus.keys():
            raise ValueError("Base ou clé absente de la sauvegarde.")
        if set(noms) != set(attendus) | {"manifest.json"}:
            raise ValueError("Le contenu ne correspond pas au manifeste.")
        if sum(e.file_size for e in entrees) > taille_max:
            raise ValueError("La sauvegarde dépasse la taille autorisée.")

        # Valider tous les noms avant toute extraction, sur Linux comme Windows.
        verifier_arbre(noms)

        etape = Path(tempfile.mkdtemp(prefix=".restauration-", dir=parent))
        try:
            cibles = set()
            for entree in entrees:
                nom = entree.filename
                if nom == "manifest.json":
                    continue
                elements = composants_portables(nom)
                if (
                    not elements or any(p in {"", ".", ".."} for p in elements)
                    or (nom not in {profil.base, "secret-key"} and elements[0] != "media")
                    or nom.startswith("/") or "\\" in nom or entree.is_dir()
                    or stat.S_ISLNK(entree.external_attr >> 16)
                ):
                    raise ValueError("Chemin invalide dans la sauvegarde.")
                cible = etape.joinpath(*elements)
                if not cible.is_relative_to(etape):
                    raise ValueError("Chemin hors du dossier de préparation.")
                if cible in cibles:
                    raise ValueError("Chemin répété dans la sauvegarde.")
                cibles.add(cible)
                cible.parent.mkdir(parents=True, exist_ok=True)
                somme = hashlib.sha256()
                yield {"phase": "ouvrir", "chemin": str(cible), "taille": entree.file_size,
                       "hash": attendus[nom], "media": nom.startswith("media/")}
                destination = ouvrir_destination(cible) if ouvrir_destination else cible.open("xb")
                with archive.open(entree) as entree_zip, destination as sortie:
                    while bloc := entree_zip.read(1024 * 1024):
                        sortie.write(bloc)
                        somme.update(bloc)
                if somme.hexdigest() != attendus[nom]:
                    raise ValueError(f"Fichier altéré dans la sauvegarde : {nom}")
                yield {"phase": "fermer", "chemin": str(cible), "taille": entree.file_size,
                       "hash": somme.hexdigest(), "media": nom.startswith("media/")}
            if not (etape / "secret-key").read_text(encoding="utf-8").strip():
                raise ValueError("Clé vide dans la sauvegarde.")
            with closing(sqlite3.connect(etape / profil.base)) as connexion:
                if connexion.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise ValueError("Base SQLite endommagée.")
                if not connexion.execute(
                    "SELECT 1 FROM sqlite_master WHERE name = 'django_migrations'"
                ).fetchone():
                    raise ValueError("La base ne contient pas les migrations Django.")
                if connexion.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError("Relations SQLite invalides.")
                if migrations_connues is not None:
                    appliquees = set(connexion.execute(
                        "SELECT app, name FROM django_migrations"
                    ).fetchall())
                    if appliquees - set(migrations_connues):
                        raise ValueError("Cette sauvegarde provient d'une version plus récente ou incompatible de cette application.")

            (etape / "media").mkdir(exist_ok=True)
            (etape / "secret-key").chmod(0o600)
            ancien = parent / (
                f".{nom_paquet}-avant-restauration-"
                f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
            )
            return Preparation(
                etape, date_sauvegarde, ancien,
                Path(getattr(source, "name", "sauvegarde.zip")).name,
                sum(nom.startswith("media/") for nom in attendus),
            )
        except BaseException:
            shutil.rmtree(etape)
            raise


def appliquer_restauration(paquet, preparation):
    """Remplacer le paquet après l'arrêt du serveur, en gardant l'original."""
    etape = preparation.etape
    ancien = preparation.ancien
    if (etape.parent != paquet.parent or not etape.is_dir()
            or ancien.parent != paquet.parent or ancien.exists()):
        raise ValueError("Dossier de restauration invalide.")
    (etape / RESULTAT).write_text(json.dumps({
        "date_sauvegarde": preparation.date_sauvegarde,
        "nom_archive": preparation.nom_archive,
        "nombre_medias": preparation.nombre_medias,
        "ancien": str(ancien),
        "applique_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }), encoding="utf-8")
    paquet.rename(ancien)
    try:
        etape.rename(paquet)
    except BaseException:
        ancien.rename(paquet)
        raise
    return ancien


def lire_resultat(paquet):
    chemin = paquet / RESULTAT
    return json.loads(chemin.read_text(encoding="utf-8")) if chemin.exists() else None
