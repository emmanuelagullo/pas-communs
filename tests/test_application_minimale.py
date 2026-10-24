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
