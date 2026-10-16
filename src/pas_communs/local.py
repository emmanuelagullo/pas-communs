"""Exécution locale commune : fichiers, migrations, boucle HTTP et journal."""
import os
import secrets
import shutil
import sqlite3
import sys
import tempfile
import threading
import traceback
from contextlib import closing, contextmanager, redirect_stdout, redirect_stderr
from datetime import datetime
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.request import urlopen
from wsgiref.simple_server import WSGIServer, make_server

if os.name == "nt":
    import msvcrt
else:
    import fcntl


def paquet_par_defaut(application, *, environnement=None, plateforme=None):
    environnement = os.environ if environnement is None else environnement
    plateforme = os.name if plateforme is None else plateforme
    if not application or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in application):
        raise ValueError("Identifiant d’application invalide.")
    if plateforme == "nt":
        racine = Path(environnement.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    else:
        racine = Path(environnement.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    return racine.expanduser() / application / "paquet-autonome"


@contextmanager
def verrouiller(paquet):
    # Le verrou doit survivre au renommage du paquet lors d'une restauration.
    with (paquet.parent / f".{paquet.name}.verrou").open("a+b") as verrou:
        try:
            if os.name == "nt":
                verrou.seek(0)
                if not verrou.read(1):
                    verrou.seek(0)
                    verrou.write(b"\0")
                    verrou.flush()
                verrou.seek(0)
                msvcrt.locking(verrou.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(verrou, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as exc:
            raise SystemExit(f"Ce paquet est déjà ouvert : {paquet}") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                verrou.seek(0)
                msvcrt.locking(verrou.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(verrou, fcntl.LOCK_UN)


def copier_paquet(source, destination, *, nom_base):
    source = Path(source).resolve()
    destination = Path(destination).absolute()
    if destination.resolve() == source or destination.resolve().is_relative_to(source):
        raise SystemExit("La destination doit être extérieure à la source.")
    if not (source / nom_base).is_file() or not (source / "secret-key").is_file():
        raise SystemExit(f"Paquet source incomplet : {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise SystemExit(f"Destination déjà présente : {destination}")
    with verrouiller(source):
        temporaire = Path(tempfile.mkdtemp(prefix=".paquet-autonome-", dir=destination.parent))
        try:
            shutil.copy2(source / "secret-key", temporaire / "secret-key")
            if (source / "media").is_dir():
                shutil.copytree(source / "media", temporaire / "media")
            else:
                (temporaire / "media").mkdir()
            with closing(sqlite3.connect(source / nom_base)) as ancienne:
                with closing(sqlite3.connect(temporaire / nom_base)) as nouvelle:
                    ancienne.backup(nouvelle)
                    if nouvelle.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                        raise RuntimeError("La copie SQLite ne passe pas le contrôle d'intégrité.")
            temporaire.rename(destination)
        finally:
            if temporaire.exists():
                shutil.rmtree(temporaire)
    print(f"Paquet copié : {destination}")
    print(f"L'original a été conservé : {source}")


def migration_necessaire(paquet, *, nom_base):
    """Repérer un schéma existant à faire évoluer avant d'ouvrir la progression."""
    base = paquet / nom_base
    if not base.is_file():
        return False
    with closing(sqlite3.connect(base)) as connexion:
        if not connexion.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'django_migrations'"
        ).fetchone():
            return False
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executeur = MigrationExecutor(connection)
    return bool(executeur.migration_plan(executeur.loader.graph.leaf_nodes()))


def proteger_avant_migration(paquet, *, nom_base):
    """Copier la base avant de modifier son schéma."""
    base = paquet / nom_base
    sauvegardes = paquet / "sauvegardes-migrations"
    sauvegardes.mkdir(exist_ok=True)
    chemin = sauvegardes / f"avant-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.sqlite3"
    with closing(sqlite3.connect(base)) as origine, closing(sqlite3.connect(chemin)) as copie:
        origine.backup(copie)
        if copie.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            chemin.unlink()
            raise RuntimeError("La sauvegarde avant migration est invalide.")
    print(f"Copie de la base avant migration : {chemin}")


def initialiser_paquet(paquet, *, nom_base):
    """À appeler sous verrou. Refuse un paquet incomplet, conserve sa clé."""
    paquet = Path(paquet)
    cle = paquet / "secret-key"
    if paquet.exists() and cle.exists() != (paquet / nom_base).exists():
        raise SystemExit(f"Paquet incomplet (base ou clé manquante) : {paquet}")
    paquet.mkdir(parents=True, exist_ok=True)
    (paquet / "media").mkdir(exist_ok=True)
    try:
        with cle.open("x", encoding="utf-8") as sortie:
            sortie.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    valeur = cle.read_text(encoding="utf-8").strip()
    if not valeur:
        raise SystemExit(f"Clé locale vide : {cle}")
    return valeur


class ServeurLocal(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = False


class ServeurBureau:
    """Boucle locale, requêtes sérialisées et fermeture avant modification des données."""
    def __init__(self, application, *, verrou=None, ecritures_bloquees=None,
                 message_blocage="Une opération est en attente. Redémarrez l’application.\n"):
        self.verrou = verrou or threading.RLock()
        self._ferme = False
        self._demarre = False
        def locale(environ, start_response):
            with self.verrou:
                if self._ferme or (ecritures_bloquees is not None and ecritures_bloquees()
                        and environ.get("REQUEST_METHOD") not in {"GET", "HEAD", "OPTIONS"}):
                    start_response("423 Locked", [("Content-Type", "text/plain; charset=utf-8")])
                    yield message_blocage.encode("utf-8")
                    return
                iterable = application(environ, start_response)
                try:
                    yield from iterable
                finally:
                    if hasattr(iterable, "close"):
                        iterable.close()
        self.serveur = make_server("127.0.0.1", 0, locale, server_class=ServeurLocal)
        self.thread = threading.Thread(target=self.serveur.serve_forever, name="pas-communs-local", daemon=True)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.serveur.server_port}/"

    def verifier_css(self, chemin):
        with urlopen(self.url + chemin.lstrip("/"), timeout=5) as reponse:
            if "text/css" not in reponse.headers.get("Content-Type", ""):
                raise RuntimeError("Le CSS local n’est pas servi correctement.")

    def __enter__(self):
        try:
            self.thread.start()
        except BaseException:
            self.serveur.server_close()
            raise
        self._demarre = True
        return self

    def fermer(self):
        if self._demarre:
            self.serveur.shutdown()
            # Attendre la requête active avant de rendre la main à la restauration.
            # Les requêtes déjà en file recevront ensuite un refus, sans écrire.
            with self.verrou:
                self._ferme = True
            self.thread.join(timeout=5)
            self._demarre = False
        self.serveur.server_close()

    def __exit__(self, *exc):
        self.fermer()


def creer_fenetre(titre, url, *, commandes=None):
    import webview
    webview.settings["ALLOW_DOWNLOADS"] = True
    return webview.create_window(titre, url, js_api=commandes)


def demarrer_avec_journal(demarrer, journal, *, application, notifier, interactif=True):
    try:
        journal.parent.mkdir(parents=True, exist_ok=True)
        sortie = journal.open("w", encoding="utf-8", buffering=1)
    except OSError as exc:
        if interactif:
            notifier(f"{application} n’a pas pu démarrer ni écrire son journal.\n{journal}\n{exc}")
        raise SystemExit(1) from exc
    with sortie, redirect_stdout(sortie), redirect_stderr(sortie):
        try:
            return demarrer()
        except SystemExit as exc:
            if exc.code is None or exc.code == 0:
                return
            traceback.print_exc()
            if interactif:
                notifier(f"{application} n’a pas pu démarrer.\nUn diagnostic a été enregistré ici :\n{journal}")
            raise
        except Exception:
            traceback.print_exc()
            if interactif:
                notifier(f"{application} n’a pas pu démarrer.\nUn diagnostic a été enregistré ici :\n{journal}")
            raise SystemExit(1)
