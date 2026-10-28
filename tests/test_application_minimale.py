"""L'application minimale de qualification, exécutée depuis les sources (sans PyInstaller)."""
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import unittest

import pas_communs
from pas_communs import installateur_windows

FIXTURE = Path(__file__).with_name("application_minimale")
LANCEUR = FIXTURE / "scripts/lancer-local.py"


class ApplicationMinimaleTests(unittest.TestCase):
    def executer(self, *arguments, env=None, attendu=0):
        environnement = {**os.environ, **(env or {})}
        environnement["PYTHONPATH"] = os.pathsep.join(
            [str(FIXTURE), *([environnement["PYTHONPATH"]] if environnement.get("PYTHONPATH") else [])])
        resultat = subprocess.run([sys.executable, str(LANCEUR), *arguments], cwd=FIXTURE,
            env=environnement, capture_output=True, text=True, timeout=60)
        self.assertEqual(resultat.returncode == 0, attendu == 0, resultat.stdout + resultat.stderr)
        return resultat.stdout

    def test_version_et_verification_de_distribution(self):
        self.assertEqual(self.executer("--version").strip(), pas_communs.__version__)
        self.assertIn("Distribution vérifiée", self.executer("--verifier-distribution"))
        # Le banc d'installation Windows relit cette version dans le programme installé.
        self.assertEqual((FIXTURE / "version-application.txt").read_text(encoding="utf-8").strip(), "dev")

    def test_donnees_hors_du_programme_selon_le_systeme(self):
        with tempfile.TemporaryDirectory() as t:
            env = {"HOME": t, "XDG_DATA_HOME": str(Path(t) / "xdg"), "LOCALAPPDATA": str(Path(t) / "local")}
            chemin = Path(self.executer("--chemin-donnees", env=env).strip())
            self.assertTrue(chemin.is_relative_to(t), chemin)
            self.assertEqual(chemin.parts[-2:], ("pas-communs-minimale", "paquet-autonome"))
            attendu = {"win32": "local", "darwin": "Library"}.get(sys.platform, "xdg")
            self.assertEqual(chemin.relative_to(t).parts[0], attendu)

    def test_temoin_conserve_entre_deux_lancements(self):
        with tempfile.TemporaryDirectory() as t:
            paquet = str(Path(t) / "donnees" / "paquet")
            self.executer("--temoin", "lire", "--paquet", paquet, attendu=1)
            self.executer("--temoin", "ecrire", "--paquet", paquet)
            self.assertIn("Témoin relu", self.executer("--temoin", "lire", "--paquet", paquet))

    def test_spec_installateur_et_dependances_sont_exploitables(self):
        with tempfile.TemporaryDirectory() as t:
            py_compile.compile(str(FIXTURE / "minimale.spec"), cfile=str(Path(t) / "spec.pyc"), doraise=True)
        configuration = installateur_windows.configuration(FIXTURE / "installateur-windows.json")
        self.assertEqual(configuration["programme"], "PasCommunsMinimale")
        for fichier in ("requirements-bureau.txt", "requirements-pdf.txt"):
            for ligne in (FIXTURE / fichier).read_text(encoding="utf-8").splitlines():
                if ligne.strip() and not ligne.startswith("#"):
                    self.assertIn("==", ligne, ligne)
        self.assertIn('bundle_identifiant="fr.inria.pascommuns.minimale"',
            (FIXTURE / "minimale.spec").read_text(encoding="utf-8"))


class QualifierMacOSTests(unittest.TestCase):
    """Fonctions d'analyse Mach-O du qualificateur, avec une sortie otool simulée (aucun Mac requis)."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        specification = importlib.util.spec_from_file_location("qualifier_macos", FIXTURE / "qualifier.py")
        cls.qualifier = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(cls.qualifier)

    def avec_otool(self, sortie):
        from types import SimpleNamespace
        from unittest.mock import patch
        return patch.object(self.qualifier.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=sortie))

    def test_dependances_hors_systeme(self):
        sortie = ("/x/libpango.dylib:\n"
                  "\t@loader_path/libglib-2.0.0.dylib (compatibility version 8801.0.0)\n"
                  "\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0)\n"
                  "\t/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation (compatibility version 150.0.0)\n"
                  "\t/opt/homebrew/opt/glib/lib/libgobject-2.0.0.dylib (compatibility version 8801.0.0)\n")
        with self.avec_otool(sortie):
            self.assertEqual(self.qualifier.dependances_hors_systeme("x"), ["/opt/homebrew/opt/glib/lib/libgobject-2.0.0.dylib"])

    def test_version_minimale_build_version_et_version_min(self):
        recent = ("Load command 9\n      cmd LC_BUILD_VERSION\n  cmdsize 32\nplatform 1\n    minos 15.0\n      sdk 15.2\n")
        ancien = ("Load command 8\n      cmd LC_VERSION_MIN_MACOSX\n  cmdsize 16\n  version 10.13\n      sdk 10.15\n")
        with self.avec_otool(recent):
            self.assertEqual(self.qualifier.version_minimale("x"), (15, 0))
        with self.avec_otool(ancien):
            self.assertEqual(self.qualifier.version_minimale("x"), (10, 13))
        with self.avec_otool(""):
            self.assertEqual(self.qualifier.version_minimale("x"), (0,))

    def test_binaires_mach_o_reconnus_par_leur_signature(self):
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            (dossier / "lib.dylib").write_bytes(b"\xcf\xfa\xed\xfe" + b"0" * 8)
            (dossier / "fat.so").write_bytes(b"\xca\xfe\xba\xbe" + b"0" * 8)
            (dossier / "texte.txt").write_text("pas un binaire")
            (dossier / "lien.dylib").symlink_to("lib.dylib")
            self.assertEqual([c.name for c in self.qualifier.binaires_mach_o(dossier)], ["fat.so", "lib.dylib"])

    def test_une_seule_copie_de_harfbuzz_d_apres_dyld(self):
        pillow = ("dyld[3310]: <05FBCD3C-2519-367D-AF95-03EB8556F75B> /Users/runner/work/p/dist/P.app/Contents/Frameworks/"
                  "PIL/__dot__dylibs/libharfbuzz.0.dylib\n")
        racine = ("dyld[3310]: <AA00CD3C-2519-367D-AF95-03EB8556F75B> /Users/runner/work/p/dist/P.app/Contents/Frameworks/"
                  "libharfbuzz.0.dylib\n")
        allegement = ("dyld[3310]: <E42886F2-4AAB-3883-95FF-85A3D395943E> /Users/runner/work/p/dist/P.app/Contents/Frameworks/"
                      "libharfbuzz-subset.0.dylib\n")
        bruit = "dyld[3310]: <810C8199-1154-38F6-A9C2-6ECEB7E30E1B> /System/Library/PrivateFrameworks/ViewBridge.framework/Versions/A/ViewBridge\nBus error\n"
        chemins = self.qualifier.chemins_dyld(bruit + pillow + allegement)
        self.assertEqual(len(chemins), 3)
        self.assertTrue(chemins[1].endswith("PIL/__dot__dylibs/libharfbuzz.0.dylib"))
        self.assertEqual(self.qualifier.verifier_une_copie_de_harfbuzz(self.qualifier.chemins_dyld(bruit + racine)),
            "/Users/runner/work/p/dist/P.app/Contents/Frameworks/libharfbuzz.0.dylib")
        for sortie, attendu in ((pillow + racine, "2 copies"), (bruit, "0 copies"), (racine + allegement, "libharfbuzz-subset")):
            with self.subTest(attendu=attendu), self.assertRaises(self.qualifier.Echec) as erreur:
                self.qualifier.verifier_une_copie_de_harfbuzz(self.qualifier.chemins_dyld(sortie))
            self.assertIn(attendu, str(erreur.exception))
