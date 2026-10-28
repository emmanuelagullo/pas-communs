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
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

import pas_communs
from pas_communs import construire_bureau, installateur_windows, notification
from pas_communs.plateforme import systeme

ICI = Path(__file__).resolve().parent
NOM = "PasCommunsMinimale"
RESULTATS = []


class Echec(Exception):
    pass


@contextmanager
def etape(titre, *, obligatoire=True, strict=False):
    print("::group::" + titre, flush=True)
    info = {}
    try:
        yield info
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        detail = (exc.stderr or exc.stdout or str(exc)) if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        detail = " ".join(str(detail).split()[-60:]) or type(exc).__name__
        bloquant = obligatoire or strict
        RESULTATS.append((titre, "ÉCHEC" if bloquant else "avertissement", detail, bloquant))
        print(("::error::" if bloquant else "::warning::") + titre + " : " + detail, flush=True)
    else:
        RESULTATS.append((titre, "ok", info.get("detail", ""), False))
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


MAGIES_MACH_O = (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe")


def binaires_mach_o(dossier):
    trouves = []
    for chemin in sorted(Path(dossier).rglob("*")):
        if chemin.is_file() and not chemin.is_symlink():
            with chemin.open("rb") as f:
                if f.read(4) in MAGIES_MACH_O:
                    trouves.append(chemin)
    return trouves


def dependances_hors_systeme(fichier):
    """Dépendances d'un Mach-O qui ne viennent ni du système ni du bundle (@loader_path, @rpath...)."""
    sortie = subprocess.run(["otool", "-L", str(fichier)], check=True, capture_output=True, text=True).stdout
    chemins = [ligne.strip().split(" (")[0] for ligne in sortie.splitlines()[1:] if ligne.strip()]
    return [c for c in chemins if not c.startswith(("/usr/lib/", "/System/Library/", "@"))]


def version_minimale(fichier):
    """Plus haute version minimale de macOS exigée par un Mach-O, comme tuple (ex. (15, 0))."""
    sortie = subprocess.run(["otool", "-l", str(fichier)], check=True, capture_output=True, text=True).stdout
    versions, attente = [], None
    for ligne in sortie.splitlines():
        mots = ligne.split()
        if len(mots) == 2 and mots[0] == "cmd":
            attente = {"LC_BUILD_VERSION": "minos", "LC_VERSION_MIN_MACOSX": "version"}.get(mots[1])
        elif attente and len(mots) == 2 and mots[0] == attente:
            versions.append(tuple(int(x) for x in mots[1].split(".") if x.isdigit()))
            attente = None
    return max(versions, default=(0,))


def chemins_dyld(sortie):
    """Chemins des bibliothèques chargées, d'après DYLD_PRINT_LIBRARIES (lignes « dyld[pid]: <UUID> /chemin »)."""
    return [m.group(1).strip() for m in re.finditer(r"dyld\[\d+\]: <[0-9A-Fa-f-]+> (/\S.*)$", sortie, re.M)]


def verifier_une_copie_de_harfbuzz(chemins):
    """Exactement un HarfBuzz et aucun libharfbuzz-subset : le PDF ne mélange pas deux copies."""
    harfbuzz = sorted({c for c in chemins if os.path.basename(c) == "libharfbuzz.0.dylib"})
    allegement = sorted({c for c in chemins if os.path.basename(c) == "libharfbuzz-subset.0.dylib"})
    if len(harfbuzz) != 1:
        raise Echec(f"{len(harfbuzz)} copies de libharfbuzz chargées : {harfbuzz}")
    if allegement:
        raise Echec(f"libharfbuzz-subset chargée, alors qu'elle doit être ignorée : {allegement}")
    return harfbuzz[0]


@contextmanager
def homebrew_masque():
    """Retire /opt/homebrew le temps d'une sonde : le programme doit se suffire à lui-même."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise Echec("--isoler-homebrew exige un runner CI jetable.")
    prefixe, masque = Path("/opt/homebrew"), Path("/opt/homebrew-masque")
    if not prefixe.is_dir():
        yield
        return
    subprocess.run(["sudo", "mv", str(prefixe), str(masque)], check=True)
    try:
        yield
    finally:
        subprocess.run(["sudo", "mv", str(masque), str(prefixe)], check=True)


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
    p.add_argument("--isoler-homebrew", action="store_true",
                   help="macOS, CI seulement : masquer /opt/homebrew pendant la sonde PDF.")
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
                        with etape("Alerte de démarrage : script AppleScript compilable (informatif)",
                                   obligatoire=False, strict=a.strict) as info:
                            piege = 'Guillemets "ici", barre \\ inverse, accents é è ’ et\nsaut de ligne'
                            subprocess.run(["osacompile", "-e", notification.script_alerte("Pas communs minimale", piege),
                                "-o", str(temporaire / "alerte.scpt")], check=True, capture_output=True, text=True)
                            info["detail"] = "texte piégé compilé par osacompile"
                        fichiers = binaires_mach_o(dossier)
                        with etape("Autonomie : aucune dépendance hors du système ni du bundle (informatif)",
                                   obligatoire=False, strict=a.strict) as info:
                            externes = {f.name: dependances_hors_systeme(f) for f in fichiers}
                            externes = {nom: deps for nom, deps in externes.items() if deps}
                            if externes:
                                nom, deps = next(iter(externes.items()))
                                raise Echec(f"{len(externes)} fichier(s) dépendent d'un chemin externe, ex. {nom} : {deps[0]}")
                            info["detail"] = f"{len(fichiers)} fichiers Mach-O vérifiés"
                        with etape("Version minimale de macOS exigée par le bundle (informatif)",
                                   obligatoire=False, strict=a.strict) as info:
                            exigences = sorted(((version_minimale(f), f.name) for f in fichiers), reverse=True)
                            version, nom = exigences[0]
                            info["detail"] = "macOS " + ".".join(map(str, version)) + " ou plus, imposé par " + nom
                    with etape("Moteur de fenêtre détecté (informatif)", obligatoire=False, strict=a.strict):
                        print(lancer(programme, "--verifier-moteur", env=dict(os.environ)))
                    if a.avec_pdf and cible != "windows":
                        with etape("PDF natif (informatif)", obligatoire=False, strict=a.strict) as info:
                            if a.isoler_homebrew and cible == "macos":
                                with homebrew_masque():
                                    print(lancer(programme, "--verifier-pdf", env=dict(os.environ)))
                                info["detail"] = "Homebrew masqué pendant la sonde"
                            else:
                                print(lancer(programme, "--verifier-pdf", env=dict(os.environ)))
                    if a.avec_pdf and cible == "macos":
                        with etape("Une seule copie de HarfBuzz chargée dans le processus (informatif)",
                                   obligatoire=False, strict=a.strict) as info:
                            sortie = subprocess.run([str(programme), "--verifier-pdf"], capture_output=True, text=True,
                                timeout=180, env={**os.environ, "DYLD_PRINT_LIBRARIES": "1"})
                            if sortie.returncode != 0:
                                raise Echec("La sonde PDF a échoué : " + (sortie.stderr or sortie.stdout)[-300:])
                            info["detail"] = verifier_une_copie_de_harfbuzz(chemins_dyld(sortie.stdout + sortie.stderr))
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
