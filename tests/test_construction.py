from pathlib import Path
import os
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from pas_communs import construction


class ConstructionTests(unittest.TestCase):
    def test_windows_sans_pdf_ne_demande_pas_pango_et_collecte_ressources(self):
        with tempfile.TemporaryDirectory() as t:
            # Windows peut fournir TEMP via son alias court (RUNNER~1).
            # L'assembleur transmet volontairement les chemins résolus.
            racine = Path(t).resolve()
            (racine / "scripts").mkdir()
            (racine / "scripts/lancer-local.py").write_text("# lanceur fictif")
            hooks = ModuleType("PyInstaller.utils.hooks")
            hooks.collect_data_files = lambda p, **kw: [(p, "ressources-fictives")]
            hooks.collect_submodules = lambda p, **kw: [p + ".module_fictif"]
            modules = {n: ModuleType(n) for n in ["PyInstaller", "PyInstaller.utils"]}
            modules[hooks.__name__] = hooks
            appels = []
            def analyser(entrees, **options):
                self.assertEqual(entrees, [str(racine / "scripts/lancer-local.py")])
                self.assertEqual(options["binaries"], [])
                self.assertIn("pas_communs.module_fictif", options["hiddenimports"])
                self.assertIn(("webview", "ressources-fictives"), options["datas"])
                self.assertIn((str(racine / "templates"), "templates"), options["datas"])
                return SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])
            espace = {"Analysis": analyser, "PYZ": lambda _: None,
                "EXE": lambda *args, **kw: appels.append(kw), "COLLECT": lambda *args, **kw: kw["name"]}
            with patch.dict("sys.modules", modules), patch.object(construction, "os", SimpleNamespace(name="nt", environ={} )):
                nom = construction.assembler(racine, espace, nom="ApplicationFictive",
                    settings="fictif.settings", ressources=[("templates", "templates")], paquets=["fictif"],
                    plateforme="win32")
            self.assertEqual(nom, "ApplicationFictive")
            self.assertFalse(appels[0]["console"])

    def assembler_fictif(self, plateforme, **options):
        """Assembler sans PyInstaller : retourne les appels reçus par l'espace du .spec."""
        with tempfile.TemporaryDirectory() as t:
            racine = Path(t).resolve()
            (racine / "scripts").mkdir()
            (racine / "scripts/lancer-local.py").write_text("# lanceur fictif")
            hooks = ModuleType("PyInstaller.utils.hooks")
            hooks.collect_data_files = lambda p, **kw: []
            hooks.collect_submodules = lambda p, **kw: [p + ".module_fictif"]
            modules = {n: ModuleType(n) for n in ["PyInstaller", "PyInstaller.utils"]}
            modules[hooks.__name__] = hooks
            appels = {}
            def enregistrer(nom_appel, resultat=None):
                def appel(*args, **kw):
                    appels[nom_appel] = (args, kw)
                    return resultat if resultat is not None else nom_appel
                return appel
            def analyser(entrees, **kw):
                appels["Analysis"] = (entrees, kw)
                return SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])
            espace = {"Analysis": analyser, "PYZ": lambda _: None, "EXE": enregistrer("EXE"),
                "COLLECT": enregistrer("COLLECT"), "BUNDLE": enregistrer("BUNDLE")}
            with patch.dict("sys.modules", modules):
                resultat = construction.assembler(racine, espace, nom="ApplicationFictive",
                    settings="fictif.settings", ressources=[], paquets=[], plateforme=plateforme, **options)
        return resultat, appels

    def test_linux_garde_la_console_et_ne_produit_pas_de_bundle(self):
        resultat, appels = self.assembler_fictif("linux")
        self.assertEqual(resultat, "COLLECT")
        self.assertNotIn("BUNDLE", appels)
        self.assertTrue(appels["EXE"][1]["console"])
        self.assertNotIn("target_arch", appels["EXE"][1])
        self.assertIn("webview.platforms.gtk", appels["Analysis"][1]["hiddenimports"])

    def test_macos_produit_un_bundle_arm64_sans_console(self):
        resultat, appels = self.assembler_fictif("darwin", bundle_identifiant="fr.inria.fictif")
        self.assertEqual(resultat, "BUNDLE")
        exe = appels["EXE"][1]
        self.assertFalse(exe["console"])
        self.assertEqual(exe["target_arch"], "arm64")
        bundle = appels["BUNDLE"][1]
        self.assertEqual(bundle["name"], "ApplicationFictive.app")
        self.assertEqual(bundle["bundle_identifier"], "fr.inria.fictif")
        self.assertTrue(bundle["info_plist"]["NSHighResolutionCapable"])
        imports = appels["Analysis"][1]["hiddenimports"]
        self.assertIn("webview.platforms.cocoa", imports)
        # PyWebView 6 l'importe dans une fonction : invisible pour l'analyse statique.
        self.assertIn("UniformTypeIdentifiers", imports)
        self.assertNotIn("webview.platforms.gtk", imports)
        self.assertNotIn("webview.platforms.winforms", imports)
        self.assertEqual(appels["Analysis"][1]["binaries"], [])

    def test_macos_refuse_un_identifiant_de_bundle_absent_ou_invalide(self):
        for identifiant in (None, "", "sansPoint", ".fr.inria", "fr.inria.", "fr.inria.é", "fr inria.fictif"):
            with self.subTest(identifiant=identifiant), self.assertRaises(ValueError):
                self.assembler_fictif("darwin", bundle_identifiant=identifiant)

    def test_identifiant_de_bundle_ignore_hors_macos(self):
        for plateforme in ("linux", "win32"):
            with self.subTest(plateforme=plateforme):
                resultat, appels = self.assembler_fictif(plateforme, bundle_identifiant="fr.inria.fictif")
                self.assertEqual(resultat, "COLLECT")
                self.assertNotIn("BUNDLE", appels)

    def test_systeme_non_pris_en_charge_refuse(self):
        with self.assertRaises(ValueError):
            self.assembler_fictif("freebsd14")

    def test_macos_embarque_pango_si_demande(self):
        from pas_communs import pango_macos
        with tempfile.TemporaryDirectory() as dossier:
            dossier = Path(dossier).resolve()
            for demande, reel in pango_macos.BIBLIOTHEQUES:
                (dossier / reel).write_bytes(b"x")
                if demande != reel:
                    (dossier / demande).symlink_to(reel)
            with patch.dict("os.environ", {"PANGO_MACOS_FICTIF": str(dossier)}):
                _, appels = self.assembler_fictif("darwin", bundle_identifiant="fr.inria.fictif",
                    pango_variable="PANGO_MACOS_FICTIF")
            binaires = appels["Analysis"][1]["binaries"]
            self.assertEqual(sorted(Path(source).name for source, _ in binaires),
                sorted(reel for _, reel in pango_macos.BIBLIOTHEQUES))
            self.assertEqual({destination for _, destination in binaires}, {"."})

    def test_macos_pango_demande_sans_dossier_ou_incomplet_refuse(self):
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("PANGO_MACOS_FICTIF", None)
            with self.assertRaises(RuntimeError):
                self.assembler_fictif("darwin", bundle_identifiant="fr.inria.fictif", pango_variable="PANGO_MACOS_FICTIF")
        with tempfile.TemporaryDirectory() as vide, patch.dict("os.environ", {"PANGO_MACOS_FICTIF": vide}):
            with self.assertRaises(FileNotFoundError):
                self.assembler_fictif("darwin", bundle_identifiant="fr.inria.fictif", pango_variable="PANGO_MACOS_FICTIF")
