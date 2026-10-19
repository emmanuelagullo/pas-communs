"""Construction Inno Setup commune ; identité et chemins restent propres au produit."""
import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys

RESSOURCES = Path(__file__).with_name("installateur")


def configuration(fichier):
    valeurs = json.loads(Path(fichier).read_text(encoding="utf-8"))
    attendus = {"programme", "nom", "app_id", "url", "donnees"}
    if set(valeurs) != attendus or any(not isinstance(v, str) or not v for v in valeurs.values()):
        raise ValueError("Configuration d'installateur invalide.")
    for cle in ("programme", "app_id"):
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", valeurs[cle]):
            raise ValueError("Identifiant Windows invalide : " + cle)
    if any(any(c in v for c in '\r\n"{}@') for v in valeurs.values()):
        raise ValueError("Caractère réservé Inno Setup.")
    if not re.fullmatch(r"https://[A-Za-z0-9./_-]+", valeurs["url"]):
        raise ValueError("URL publique HTTPS requise.")
    donnees = PureWindowsPath(valeurs["donnees"])
    if (donnees.is_absolute() or donnees.drive or len(donnees.parts) < 2
            or any(not re.fullmatch(r"[A-Za-z0-9_-]+", p) for p in donnees.parts)
            or donnees.parts[0].lower() == "programs"):
        raise ValueError("Les données doivent rester hors du programme installé.")
    return valeurs


def preparer(fichier, racine, version):
    c = configuration(fichier)
    if not re.fullmatch(r"(?:[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[A-Za-z0-9.-]+)?|dev(?:\.[a-fA-F0-9]{8})?)", version):
        raise ValueError("Version d'installateur invalide.")
    racine = Path(racine).resolve()
    source = racine / "dist" / c["programme"]
    if not (source / (c["programme"] + ".exe")).is_file():
        raise ValueError("Construire le programme Windows avant son installateur.")
    sortie = racine / "dist"
    substitutions = {**{k.upper(): v for k, v in c.items()}, "VERSION": version,
                      "SOURCE": str(source), "SORTIE": str(sortie),
                      "NOM_PASCAL": c["nom"].replace("'", "''")}
    texte = (RESSOURCES / "windows.iss").read_text(encoding="utf-8")
    for cle, valeur in substitutions.items():
        # Les chemins absolus sont fournis par le système, pas par le fichier produit.
        if any(x in valeur for x in '\r\n"'):
            raise ValueError("Valeur Inno Setup invalide.")
        texte = texte.replace("@@" + cle + "@@", valeur)
    dossier = sortie / "installateur"
    dossier.mkdir(exist_ok=True)
    script = dossier / (c["programme"] + ".iss")
    script.write_text(texte, encoding="utf-8-sig")
    return script, sortie / (c["programme"] + "-Setup-" + version + "-x64.exe")


def construire(fichier, racine, version, compilateur=None, verifier=False):
    if sys.platform != "win32":
        raise ValueError("Compiler l'installateur sur Windows.")
    script, setup = preparer(fichier, racine, version)
    compilateur = compilateur or shutil.which("ISCC.exe")
    if not compilateur:
        candidats = sorted(Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")).glob("Inno Setup */ISCC.exe"))
        compilateur = str(candidats[-1]) if candidats else None
    if not compilateur:
        raise ValueError("Installer Inno Setup avant la construction.")
    subprocess.run([compilateur, str(script)], check=True)
    if not setup.is_file():
        raise ValueError("Installateur compilé absent.")
    if verifier:
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(RESSOURCES / "verifier-windows.ps1"), "-Configuration", str(Path(fichier).resolve()),
                        "-Setup", str(setup), "-Version", version], check=True)
    return setup


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--configuration", type=Path, required=True)
    p.add_argument("--racine", type=Path, default=Path.cwd())
    p.add_argument("--version")
    p.add_argument("--iscc")
    p.add_argument("--verifier", action="store_true", help="Installation/réinstallation/désinstallation sur un runner CI jetable.")
    p.add_argument("--preparer", action="store_true", help="Générer seulement le script Inno Setup.")
    a = p.parse_args()
    version = a.version or (a.racine / "version-application.txt").read_text(encoding="utf-8-sig").strip()
    if a.preparer:
        print(preparer(a.configuration, a.racine, version)[0])
    else:
        print(construire(a.configuration, a.racine, version, a.iscc, a.verifier))


if __name__ == "__main__":
    main()
