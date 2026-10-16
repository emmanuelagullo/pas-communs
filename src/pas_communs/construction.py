"""Assemblage PyInstaller commun, paramètres de ressources propres au produit."""
import os
from pathlib import Path


def assembler(racine, espace, *, nom, settings, ressources, paquets,
              imports=(), entree="scripts/lancer-local.py", pango_variable=None,
              paquets_ressources=(), exclusions=()):
    from PyInstaller.utils.hooks import collect_data_files, collect_submodules
    racine = Path(racine).resolve()
    if not (racine / entree).is_file():
        raise FileNotFoundError(f"Lanceur introuvable : {racine / entree}")
    os.environ["DJANGO_SETTINGS_MODULE"] = settings
    donnees = [(str(racine / source), cible) for source, cible in ressources]
    for paquet in paquets_ressources:
        donnees += collect_data_files(paquet, includes=["templates/**", "static/**"])
    imports = list(imports)
    outils = {"pas_communs.construction", "pas_communs.construire_bureau"}
    def module_runtime(nom_module):
        return nom_module not in outils and not any(
            p == "tests" or p.startswith(("test_", "tests_")) for p in nom_module.split("."))
    for paquet in ("pas_communs", *paquets):
        imports += collect_submodules(paquet, filter=module_runtime)
    if os.name == "nt":
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
    programme = espace["EXE"](archive, analyse.scripts, [], exclude_binaries=True,
        name=nom, console=os.name != "nt")
    return espace["COLLECT"](programme, analyse.binaries, analyse.datas,
        strip=False, upx=False, name=nom)
