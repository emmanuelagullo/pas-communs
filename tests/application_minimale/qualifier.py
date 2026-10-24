"""Qualifier le programme de bureau de l'application minimale à partir du wheel installé.

Le socle doit être installé comme wheel (jamais depuis src/). Les étapes obligatoires
(construction, archive, vérification du programme extrait, données) font échouer le
script ; la fenêtre, le PDF natif, la signature et l'installateur Windows sont
informatifs tant qu'ils n'ont pas été stabilisés en CI (option --strict).
"""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

import pas_communs
from pas_communs import construire_bureau, installateur_windows
from pas_communs.plateforme import systeme

ICI = Path(__file__).resolve().parent
NOM = "PasCommunsMinimale"
RESULTATS = []


class Echec(Exception):
    pass


@contextmanager
def etape(titre, *, obligatoire=True, strict=False):
    print("::group::" + titre, flush=True)
    try:
        yield
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        detail = (exc.stderr or exc.stdout or str(exc)) if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        detail = " ".join(str(detail).split()[-60:]) or type(exc).__name__
        bloquant = obligatoire or strict
        RESULTATS.append((titre, "ÉCHEC" if bloquant else "avertissement", detail, bloquant))
        print(("::error::" if bloquant else "::warning::") + titre + " : " + detail, flush=True)
    else:
        RESULTATS.append((titre, "ok", "", False))
    finally:
        print("::endgroup::", flush=True)


def lancer(programme, *arguments, env=None, timeout=180, prefixe=()):
    resultat = subprocess.run([*prefixe, str(programme), *arguments], env=env, capture_output=True,
        text=True, timeout=timeout, check=True)
    return resultat.stdout


def isole(racine):
    env = dict(os.environ)
    env.update(HOME=str(racine), XDG_DATA_HOME=str(racine / "xdg"), LOCALAPPDATA=str(racine / "local"))
    return env


@contextmanager
def extraire(archive, cible, temporaire):
    """Rend le programme extrait comme le ferait l'utilisateur : zip, tar.gz ou DMG copié."""
    if cible == "windows":
        zipfile.ZipFile(archive).extractall(temporaire)
        yield temporaire / NOM / (NOM + ".exe"), temporaire / NOM
    elif cible == "linux":
        with tarfile.open(archive) as t:
            t.extractall(temporaire, filter="data")
        yield temporaire / NOM / NOM, temporaire / NOM
    else:
        montage = temporaire / "volume"
        montage.mkdir()
        subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", str(montage), str(archive)],
            check=True, capture_output=True, text=True)
        try:
            if os.readlink(montage / "Applications") != "/Applications":
                raise Echec("Le raccourci Applications du DMG est absent ou incorrect.")
            copie = temporaire / (NOM + ".app")
            shutil.copytree(montage / (NOM + ".app"), copie, symlinks=True)
            yield copie / "Contents/MacOS" / NOM, copie
        finally:
            subprocess.run(["hdiutil", "detach", str(montage), "-force"], capture_output=True)


def ecrire_resume():
    lignes = ["## Qualification de l'application minimale (" + systeme() + ", " + platform.machine() + ")", "",
        "Socle : pas-communs " + pas_communs.__version__, "", "| Étape | Résultat | Détail |", "|---|---|---|"]
    lignes += [f"| {t} | {r} | {d.replace('|', '/')[:300]} |" for t, r, d, _ in RESULTATS]
    texte = "\n".join(lignes) + "\n"
    print(texte)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as sortie:
            sortie.write(texte)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version-attendue", help="Version exacte du socle installé (ex. 0.10.0).")
    p.add_argument("--avec-fenetre", action="store_true", help="Ouvrir la vraie fenêtre PyWebView.")
    p.add_argument("--avec-pdf", action="store_true", help="Sonde PDF natif (WeasyPrint).")
    p.add_argument("--avec-installateur", action="store_true", help="Installateur Windows et son banc.")
    p.add_argument("--strict", action="store_true", help="Les étapes informatives deviennent bloquantes.")
    a = p.parse_args()
    cible = systeme(strict=True)

    with etape("Origine : wheel installé, version attendue"):
        emplacement = Path(pas_communs.__file__).resolve()
        if (ICI.parents[1] / "src") in emplacement.parents:
            raise Echec("pas_communs vient de src/ : installer le wheel avant de qualifier.")
        if a.version_attendue and pas_communs.__version__ != a.version_attendue:
            raise Echec(f"Version installée {pas_communs.__version__}, attendue {a.version_attendue}.")
        print(emplacement, pas_communs.__version__)

    archive = None
    with etape("Construction du programme et vérification de la distribution"):
        archive = construire_bureau.construire(ICI, "minimale.spec", NOM)
        print(archive)

    if archive:
        with tempfile.TemporaryDirectory() as t:
            temporaire = Path(t)
            with etape("Archive : extraction et programme extrait"):
                (temporaire / "extrait").mkdir()
                with extraire(archive, cible, temporaire / "extrait") as (programme, dossier):
                    if lancer(programme, "--version").strip() != pas_communs.__version__:
                        raise Echec("Le programme embarque une autre version du socle.")
                    lancer(programme, "--verifier-distribution")
                    donnees = temporaire / "donnees"
                    env = isole(donnees)
                    chemin = Path(lancer(programme, "--chemin-donnees", env=env).strip())
                    if not chemin.is_relative_to(donnees) or chemin.is_relative_to(dossier):
                        raise Echec(f"Dossier de données inattendu : {chemin}")
                    lancer(programme, "--temoin", "ecrire", env=env)
                    lancer(programme, "--temoin", "lire", env=env)
                    if not (chemin / "secret-key").is_file():
                        raise Echec("Le paquet de données n'a pas été créé au chemin annoncé.")
                    # Les étapes suivantes réutilisent le programme extrait avant sa suppression.
                    if cible == "macos":
                        with etape("Architecture et signature ad hoc (informatif)", obligatoire=False, strict=a.strict):
                            print(subprocess.run(["lipo", "-archs", str(programme)], check=True, capture_output=True, text=True).stdout)
                            subprocess.run(["codesign", "--verify", "--verbose=1", str(dossier)], check=True, capture_output=True, text=True)
                    if a.avec_pdf and cible != "windows":
                        with etape("PDF natif (informatif)", obligatoire=False, strict=a.strict):
                            print(lancer(programme, "--verifier-pdf", env=dict(os.environ)))
                    if a.avec_fenetre:
                        with etape("Fenêtre PyWebView réelle (informatif)", obligatoire=False, strict=a.strict):
                            prefixe = ("xvfb-run", "-a") if cible == "linux" and not os.environ.get("DISPLAY") else ()
                            print(lancer(programme, "--fenetre-auto", "30", "--paquet", str(temporaire / "fenetre" / "paquet"),
                                env=dict(os.environ), timeout=120, prefixe=prefixe))

    if a.avec_installateur and cible == "windows":
        with etape("Installateur Windows : installation, réinstallation, désinstallation (informatif)",
                   obligatoire=False, strict=a.strict):
            print(installateur_windows.construire(ICI / "installateur-windows.json", ICI, "dev", verifier=True))

    ecrire_resume()
    if any(bloquant and resultat == "ÉCHEC" for _, resultat, _, bloquant in RESULTATS):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
