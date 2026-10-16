"""Téléchargements de construction PWA avec TLS, cache et remplacement atomique."""
import hashlib
from pathlib import Path
import http.client
import shutil
import ssl
import tempfile
import time
import urllib.request
import urllib.error

PYODIDE = "314.0.7"
BASE = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE}/full/"

def telecharger(url, target, empreinte=None, tentatives=4):
    """Cache complet, remplacement atomique et reprises réseau bornées ; TLS vérifié."""
    if target.is_file() and target.stat().st_size and (
        empreinte is None or hashlib.sha256(target.read_bytes()).hexdigest() == empreinte
    ):
        return
    for numero in range(tentatives):
        temporaire = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=target.name + ".", suffix=".part", delete=False) as fichier:
                temporaire = Path(fichier.name)
                with urllib.request.urlopen(url, timeout=120) as response:
                    shutil.copyfileobj(response, fichier)
                    attendu = response.headers.get("Content-Length")
                    if attendu is not None and fichier.tell() != int(attendu):
                        raise http.client.IncompleteRead(b"", int(attendu) - fichier.tell())
            if not temporaire.stat().st_size:
                raise RuntimeError("Téléchargement vide : " + url)
            if empreinte and hashlib.sha256(temporaire.read_bytes()).hexdigest() != empreinte:
                raise RuntimeError("Empreinte incorrecte : " + url)
            temporaire.replace(target)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException, ssl.SSLError) as erreur:
            if isinstance(erreur, urllib.error.HTTPError) and erreur.code not in {408, 429, 500, 502, 503, 504}:
                raise
            cause = getattr(erreur, "reason", erreur)
            if isinstance(cause, ssl.SSLCertVerificationError) or numero + 1 == tentatives:
                raise
            print(f"Téléchargement interrompu ({numero + 1}/{tentatives}) : {target.name} ; nouvel essai…", flush=True)
            time.sleep(2 ** numero)
        finally:
            if temporaire is not None:
                temporaire.unlink(missing_ok=True)


def verifier_runtime(lock, version="314.0.7"):
    info = lock.get("info", {})
    if info.get("abi_version") != "2026_0" or info.get("python") != "3.14.2":
        raise ValueError(f"Cache runtime incompatible avec Pyodide {version} : utiliser un dossier propre à cette version.")


def nettoyer_runtime(runtime, fichiers):
    # Une reconstruction ne doit pas distribuer les anciens codecs/stdlibs.
    for fichier in runtime.iterdir():
        if fichier.is_file() and fichier.name not in fichiers:
            fichier.unlink()


