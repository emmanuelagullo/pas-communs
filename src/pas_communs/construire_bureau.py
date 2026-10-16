"""Construire un .spec applicatif avec PyInstaller installé dans le Python courant."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def construire(projet, spec, nom):
    from PyInstaller.__main__ import run
    projet = Path(projet).resolve()
    if not nom or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in nom):
        raise ValueError("Nom d’exécutable invalide.")
    if not Path(spec).is_absolute():
        spec = projet / spec
    # Le constructeur est une opération de CLI ; cwd ne concerne pas un serveur.
    os.chdir(projet)
    run(["--noconfirm", "--clean", str(spec)])
    programme = projet / "dist" / nom / (nom + (".exe" if os.name == "nt" else ""))
    subprocess.run([str(programme), "--verifier-distribution"], check=True)
    format_archive = "zip" if os.name == "nt" else "gztar"
    suffixe = "windows" if os.name == "nt" else "linux"
    return Path(shutil.make_archive(str(projet / "dist" / (nom + "-" + suffixe)),
        format_archive, root_dir=projet / "dist", base_dir=nom))


def main():
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--projet", type=Path, default=Path.cwd())
    analyseur.add_argument("--spec", required=True)
    analyseur.add_argument("--nom", required=True)
    args = analyseur.parse_args()
    print(construire(args.projet, args.spec, args.nom))


if __name__ == "__main__":
    main()
