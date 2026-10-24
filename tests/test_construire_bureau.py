import os
from pathlib import Path
import shutil
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from pas_communs import construire_bureau


class ConstruireBureauTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.projet = Path(temp.name).resolve()
        ancien = os.getcwd()
        self.addCleanup(os.chdir, ancien)

    def test_chemins_des_programmes_par_systeme(self):
        dist = Path("dist")
        self.assertEqual(construire_bureau.chemin_programme(dist, "Prog", "windows"), dist / "Prog/Prog.exe")
        self.assertEqual(construire_bureau.chemin_programme(dist, "Prog", "linux"), dist / "Prog/Prog")
        self.assertEqual(construire_bureau.chemin_programme(dist, "Prog", "macos"),
            dist / "Prog.app/Contents/MacOS/Prog")

    def construire(self, plateforme, machine="x86_64"):
        """Construire sans PyInstaller ni exécutable réel ; retourne (archive, appels)."""
        dist = self.projet / "dist"
        appels = []
        def run(arguments):
            appels.append(("pyinstaller", arguments))
            (dist / "Prog").mkdir(parents=True)
            (dist / "Prog/Prog").write_text("programme fictif")
            (dist / "Prog.app/Contents/MacOS").mkdir(parents=True)
        def subprocess_run(commande, **kw):
            appels.append(("subprocess", commande))
        pyinstaller = ModuleType("PyInstaller"), ModuleType("PyInstaller.__main__")
        pyinstaller[1].run = run
        with patch.dict("sys.modules", {"PyInstaller": pyinstaller[0], "PyInstaller.__main__": pyinstaller[1]}), \
                patch.object(construire_bureau.sys, "platform", plateforme), \
                patch.object(construire_bureau.platform, "machine", lambda: machine), \
                patch.object(construire_bureau.subprocess, "run", subprocess_run), \
                patch.object(construire_bureau, "creer_dmg", lambda app, dest, volume: appels.append(("dmg", app, dest, volume)) or dest):
            archive = construire_bureau.construire(self.projet, "fictif.spec", "Prog")
        return archive, appels

    def test_noms_historiques_des_archives_windows_et_linux(self):
        for plateforme, attendu in (("linux", "Prog-linux.tar.gz"), ("win32", "Prog-windows.zip")):
            with self.subTest(plateforme=plateforme):
                archive, appels = self.construire(plateforme)
                self.assertEqual(archive.name, attendu)
                self.assertTrue(archive.is_file())
                self.assertEqual(appels[1][1][-1], "--verifier-distribution")
                shutil.rmtree(self.projet / "dist")

    def test_macos_arm64_produit_un_dmg_apres_verification_du_vrai_programme(self):
        archive, appels = self.construire("darwin", machine="arm64")
        self.assertEqual(archive.name, "Prog-macos-arm64.dmg")
        verification = appels[1][1]
        self.assertEqual(Path(verification[0]), self.projet / "dist/Prog.app/Contents/MacOS/Prog")
        self.assertEqual(verification[-1], "--verifier-distribution")
        self.assertEqual(appels[2][0], "dmg")
        self.assertEqual(appels[2][3], "Prog")

    def test_macos_intel_refuse_avant_toute_construction(self):
        with self.assertRaises(SystemExit) as ctx:
            self.construire("darwin", machine="x86_64")
        self.assertIn("arm64", str(ctx.exception))
        self.assertFalse((self.projet / "dist").exists())

    def test_systeme_non_pris_en_charge_refuse(self):
        with self.assertRaises(ValueError):
            self.construire("freebsd14")

    def test_dmg_contient_application_et_raccourci_et_utilise_hdiutil(self):
        application = self.projet / "Prog.app"
        (application / "Contents").mkdir(parents=True)
        (application / "Contents/Info.plist").write_text("fictif")
        (application / "Contents/lien").symlink_to("Info.plist")
        vus = {}
        def subprocess_run(commande, **kw):
            source = Path(commande[commande.index("-srcfolder") + 1])
            vus["commande"] = commande
            vus["application"] = (source / "Prog.app/Contents/Info.plist").read_text()
            vus["lien_conserve"] = (source / "Prog.app/Contents/lien").is_symlink()
            vus["raccourci"] = os.readlink(source / "Applications")
        with patch.object(construire_bureau.subprocess, "run", subprocess_run):
            resultat = construire_bureau.creer_dmg(application, self.projet / "Prog.dmg", "Prog")
        self.assertEqual(resultat, self.projet / "Prog.dmg")
        self.assertEqual(vus["commande"][:2], ["hdiutil", "create"])
        self.assertIn("UDZO", vus["commande"])
        self.assertEqual(vus["application"], "fictif")
        self.assertTrue(vus["lien_conserve"])
        self.assertEqual(vus["raccourci"], "/Applications")

    def test_nom_d_executable_invalide_refuse(self):
        pyinstaller = ModuleType("PyInstaller"), ModuleType("PyInstaller.__main__")
        pyinstaller[1].run = lambda arguments: None
        with patch.dict("sys.modules", {"PyInstaller": pyinstaller[0], "PyInstaller.__main__": pyinstaller[1]}), \
                patch.object(construire_bureau.sys, "platform", "linux"):
            with self.assertRaises(ValueError):
                construire_bureau.construire(self.projet, "fictif.spec", "nom invalide")
