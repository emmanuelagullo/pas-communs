"""Assemblage PyInstaller commun, paramètres de ressources propres au produit."""
import os
from pathlib import Path

from .plateforme import ARCHITECTURE_MACOS, systeme


def _verifier_identifiant_bundle(identifiant):
    autorises = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.")
    if (not identifiant or "." not in identifiant or identifiant.startswith(".")
            or identifiant.endswith(".") or any(c not in autorises for c in identifiant)):
        raise ValueError("macOS : bundle_identifiant explicite et stable requis, par exemple fr.inria.produit.")


def assembler(racine, espace, *, nom, settings, ressources, paquets,
              imports=(), entree="scripts/lancer-local.py", pango_variable=None,
              paquets_ressources=(), exclusions=(), plateforme=None,
              bundle_identifiant=None):
    from PyInstaller.utils.hooks import collect_data_files, collect_submodules
    cible = systeme(plateforme, strict=True)
    if cible == "macos":
        # L'identifiant fixe l'identité du programme pour macOS : jamais de valeur par défaut.
        _verifier_identifiant_bundle(bundle_identifiant)
    racine = Path(racine).resolve()
    if not (racine / entree).is_file():
        raise FileNotFoundError(f"Lanceur introuvable : {racine / entree}")
    os.environ["DJANGO_SETTINGS_MODULE"] = settings
    donnees = [(str(racine / source), cible) for source, cible in ressources]
    for paquet in paquets_ressources:
        donnees += collect_data_files(paquet, includes=["templates/**", "static/**"])
    imports = list(imports)
    outils = {"pas_communs.construction", "pas_communs.construire_bureau", "pas_communs.construction_pwa", "pas_communs.navigateur", "pas_communs.ci", "pas_communs.qualification_http", "pas_communs.qualification", "pas_communs.promotion"}
    def module_runtime(nom_module):
        return not any(nom_module == outil or nom_module.startswith(outil + ".") for outil in outils) and not any(
            p == "tests" or p.startswith(("test_", "tests_")) for p in nom_module.split("."))
    for paquet in ("pas_communs", *paquets):
        imports += collect_submodules(paquet, filter=module_runtime)
    if cible == "windows":
        imports += ["webview.platforms.winforms", "webview.platforms.edgechromium"]
        donnees += collect_data_files("webview", includes=["lib/**"])
        pango_bin = os.environ.get(pango_variable) if pango_variable else None
        binaires = []
        if pango_variable:
            if not pango_bin:
                raise RuntimeError(f"Définir {pango_variable} vers le dossier UCRT64/bin de MSYS2.")
            dossier_pango = Path(pango_bin)
            bibliotheques_pango = [
                "libgobject-2.0-0.dll", "libpango-1.0-0.dll",
                "libpangoft2-1.0-0.dll", "libharfbuzz-0.dll",
                "libharfbuzz-subset-0.dll", "libfontconfig-1.dll",
            ]
            manquantes = [nom for nom in bibliotheques_pango if not (dossier_pango / nom).is_file()]
            if manquantes:
                raise FileNotFoundError(f"DLL Windows manquantes dans {dossier_pango} : {manquantes}")
            # PyInstaller analyse les dépendances transitives de ces DLL et les place
            # dans _internal ; WeasyPrint les cherchera dans ce dossier au lancement.
            binaires = [(str(dossier_pango / nom), ".") for nom in bibliotheques_pango]

    elif cible == "macos":
        # WKWebView via PyObjC : aucun moteur à embarquer. Le PDF natif (Pango)
        # n'est pas assemblé ici ; sa qualification sous macOS reste à faire.
        binaires = []
        imports += ["webview.platforms.cocoa", "objc", "Foundation", "AppKit", "WebKit", "PyObjCTools",
            "UniformTypeIdentifiers"]
    else:
        binaires = []
        imports += ["webview.platforms.gtk", "gi.repository.Gtk", "gi.repository.WebKit2"]
        # PyInstaller ne voit pas les imports dynamiques de PyWebView. Sur Guix,
        # les typelibs WebKit sont fournis par GI_TYPELIB_PATH et non par Python.
        chemins_typelibs = [Path(chemin) for chemin in os.environ.get("GI_TYPELIB_PATH", "").split(os.pathsep) if chemin]
        chemins_typelibs += [Path("/usr/lib/x86_64-linux-gnu/girepository-1.0"), Path("/usr/lib/girepository-1.0")]
        for version in ("4.1", "4.0"):
            typelib = next((dossier / f"WebKit2-{version}.typelib" for dossier in chemins_typelibs if (dossier / f"WebKit2-{version}.typelib").is_file()), None)
            if typelib:
                donnees.append((str(typelib), "gi_typelibs"))

    analyse = espace["Analysis"](
        [str(racine / entree)], pathex=[str(racine)], binaries=binaires,
        datas=donnees, hiddenimports=imports, hookspath=[], hooksconfig={},
        runtime_hooks=[], excludes=[*exclusions, *sorted(outils), "PyInstaller"], noarchive=False,
    )
    archive = espace["PYZ"](analyse.pure)
    options_exe = {"name": nom, "console": cible == "linux"}
    if cible == "macos":
        options_exe["target_arch"] = ARCHITECTURE_MACOS
    programme = espace["EXE"](archive, analyse.scripts, [], exclude_binaries=True, **options_exe)
    collecte = espace["COLLECT"](programme, analyse.binaries, analyse.datas,
        strip=False, upx=False, name=nom)
    if cible != "macos":
        return collecte
    # Le dossier PyInstaller est conservé : le .app l'embarque, sans binaire monolithique.
    return espace["BUNDLE"](collecte, name=nom + ".app", bundle_identifier=bundle_identifiant,
        info_plist={"CFBundleName": nom, "NSHighResolutionCapable": True})
