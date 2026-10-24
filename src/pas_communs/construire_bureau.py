"""Construire un .spec applicatif avec PyInstaller installé dans le Python courant."""
import argparse
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .plateforme import ARCHITECTURE_MACOS, systeme

_NOM_VALIDE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"


def chemin_programme(dist, nom, cible):
    """Exécutable construit, vérifié par --verifier-distribution."""
    dist = Path(dist)
    if cible == "windows":
        return dist / nom / (nom + ".exe")
    if cible == "macos":
        return dist / (nom + ".app") / "Contents/MacOS" / nom
    return dist / nom / nom


def creer_dmg(application, destination, volume):
    """Image disque avec le .app et un raccourci vers Applications, sans signature."""
    application = Path(application)
    with tempfile.TemporaryDirectory() as temporaire:
        contenu = Path(temporaire) / volume
        contenu.mkdir()
        # Les liens symboliques internes du .app doivent être conservés.
        shutil.copytree(application, contenu / application.name, symlinks=True)
        (contenu / "Applications").symlink_to("/Applications")
        subprocess.run(["hdiutil", "create", "-volname", volume, "-srcfolder", str(contenu),
            "-ov", "-format", "UDZO", str(destination)], check=True)
    return Path(destination)


def construire(projet, spec, nom):
    from PyInstaller.__main__ import run
    cible = systeme(strict=True)
    if cible == "macos" and platform.machine() != ARCHITECTURE_MACOS:
        raise SystemExit("macOS : seule l’architecture " + ARCHITECTURE_MACOS + " est livrée ; "
            "construire sur un Mac Apple Silicon.")
    projet = Path(projet).resolve()
    if not nom or any(c not in _NOM_VALIDE for c in nom):
        raise ValueError("Nom d’exécutable invalide.")
    if not Path(spec).is_absolute():
        spec = projet / spec
    # Le constructeur est une opération de CLI ; cwd ne concerne pas un serveur.
    os.chdir(projet)
    dist = projet / "dist"
    # PyInstaller fixe ses dossiers par défaut au chargement du module, avant ce chdir.
    run(["--noconfirm", "--clean", "--distpath", str(dist), "--workpath", str(projet / "build"), str(spec)])
    subprocess.run([str(chemin_programme(dist, nom, cible)), "--verifier-distribution"], check=True)
    if cible == "macos":
        return creer_dmg(dist / (nom + ".app"), dist / (nom + "-macos-" + ARCHITECTURE_MACOS + ".dmg"), nom)
    format_archive = "zip" if cible == "windows" else "gztar"
    return Path(shutil.make_archive(str(dist / (nom + "-" + cible)),
        format_archive, root_dir=dist, base_dir=nom))


def main():
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--projet", type=Path, default=Path.cwd())
    analyseur.add_argument("--spec", required=True)
    analyseur.add_argument("--nom", required=True)
    args = analyseur.parse_args()
    print(construire(args.projet, args.spec, args.nom))


if __name__ == "__main__":
    main()
