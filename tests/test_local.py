from contextlib import closing
from io import StringIO
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch

from pas_communs import local


class LocalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)

    def paquet(self):
        paquet = self.parent / "paquet"
        paquet.mkdir()
        (paquet / "secret-key").write_text("cle-fictive")
        with closing(sqlite3.connect(paquet / "base.sqlite3")) as db, db:
            db.execute("CREATE TABLE exemple (valeur TEXT)")
            db.execute("INSERT INTO exemple VALUES ('fictif')")
        return paquet

    def test_chemins_distincts_par_application_linux_et_windows(self):
        env = {"XDG_DATA_HOME": str(self.parent), "LOCALAPPDATA": str(self.parent)}
        a = local.paquet_par_defaut("application-a", environnement=env)
        b = local.paquet_par_defaut("application-b", environnement=env)
        self.assertNotEqual(a,b)
        self.assertEqual(local.paquet_par_defaut("application-a", environnement=env, plateforme="nt"), a)
        self.assertFalse(a.exists())

    def test_chemin_macos_sous_library_application_support(self):
        env = {"HOME": str(self.parent), "XDG_DATA_HOME": str(self.parent / "xdg"),
            "LOCALAPPDATA": str(self.parent / "windows")}
        attendu = self.parent / "Library/Application Support/application-a/paquet-autonome"
        self.assertEqual(local.paquet_par_defaut("application-a", environnement=env, plateforme="darwin"), attendu)
        self.assertEqual(local.paquet_par_defaut("application-a", environnement=env, plateforme="macos"), attendu)

    def test_valeurs_historiques_et_systemes_inconnus_gardent_le_comportement_linux(self):
        env = {"XDG_DATA_HOME": str(self.parent), "LOCALAPPDATA": str(self.parent / "windows")}
        attendu = self.parent / "application-a/paquet-autonome"
        for plateforme in ("posix", "linux", "linux2", "freebsd14"):
            with self.subTest(plateforme=plateforme):
                self.assertEqual(local.paquet_par_defaut("application-a", environnement=env, plateforme=plateforme), attendu)
        self.assertEqual(local.paquet_par_defaut("application-a", environnement=env, plateforme="win32"),
            self.parent / "windows/application-a/paquet-autonome")

    def test_verrou_refuse_autre_processus_et_survit_au_renommage(self):
        paquet = self.paquet()
        code = "from pathlib import Path; from pas_communs.local import verrouiller; import sys; "
        code += "p=Path(sys.argv[1]); "
        code += "verrouiller(p).__enter__()"
        with local.verrouiller(paquet):
            paquet.rename(self.parent / "ancien")
            resultat = subprocess.run([sys.executable, "-c", code, str(paquet)], capture_output=True, text=True)
            self.assertNotEqual(resultat.returncode, 0)
            self.assertIn("déjà ouvert", resultat.stderr)
        with local.verrouiller(paquet):
            pass

    def test_copie_et_sauvegarde_avant_migration(self):
        paquet = self.paquet()
        copie = self.parent / "copie"
        local.copier_paquet(paquet, copie, nom_base="base.sqlite3")
        self.assertEqual((copie / "secret-key").read_text(), "cle-fictive")
        with self.assertRaises(SystemExit):
            local.copier_paquet(paquet, copie, nom_base="base.sqlite3")
        local.proteger_avant_migration(paquet, nom_base="base.sqlite3")
        fichiers = list((paquet / "sauvegardes-migrations").glob("*.sqlite3"))
        self.assertEqual(len(fichiers), 1)
        with closing(sqlite3.connect(fichiers[0])) as db:
            self.assertEqual(db.execute("SELECT valeur FROM exemple").fetchone(), ("fictif",))

    def test_initialisation_conserve_cle_et_refuse_paquet_incomplet(self):
        paquet = self.paquet()
        self.assertEqual(local.initialiser_paquet(paquet, nom_base="base.sqlite3"), "cle-fictive")
        (paquet / "base.sqlite3").unlink()
        with self.assertRaises(SystemExit):
            local.initialiser_paquet(paquet, nom_base="base.sqlite3")
        self.assertFalse((paquet / "base.sqlite3").exists())

    def test_serveur_boucle_locale_et_blocage_ecritures(self):
        bloque = [False]
        ferme = []
        class Reponse:
            def __iter__(self):
                yield b"body {}"
            def close(self):
                ferme.append(True)
        def application(environ, start):
            start("200 OK", [("Content-Type", "text/css")])
            return Reponse()
        with local.ServeurBureau(application, ecritures_bloquees=lambda: bloque[0]) as serveur:
            self.assertEqual(serveur.serveur.server_address[0], "127.0.0.1")
            serveur.verifier_css("style.css")
            bloque[0] = True
            with self.assertRaises(HTTPError) as exc:
                urlopen(Request(serveur.url, data=b"ecriture"), timeout=3)
            self.assertEqual(exc.exception.code, 423)
            with urlopen(serveur.url, timeout=3) as reponse:
                self.assertEqual(reponse.status, 200)
        self.assertEqual(len(ferme), 2)
        self.assertFalse(serveur.thread.is_alive())

    def test_fermeture_attend_requete_active(self):
        entree = threading.Event()
        continuer = threading.Event()
        arrete = threading.Event()
        erreurs = []
        def application(environ, start):
            entree.set()
            continuer.wait(4)
            start("200 OK", [("Content-Type", "text/plain")])
            return [b"termine"]
        serveur = local.ServeurBureau(application)
        serveur.__enter__()
        def demander():
            try:
                with urlopen(serveur.url, timeout=5) as reponse:
                    reponse.read()
            except Exception as exc:
                erreurs.append(exc)
        client = threading.Thread(target=demander)
        client.start()
        self.assertTrue(entree.wait(3))
        fermeture = threading.Thread(target=lambda: (serveur.fermer(), arrete.set()))
        fermeture.start()
        self.assertFalse(arrete.wait(.1))
        continuer.set()
        client.join(5); fermeture.join(5)
        self.assertTrue(arrete.is_set())
        self.assertFalse(erreurs)

    def test_journal_enregistre_erreur_et_verification_sans_alerte(self):
        journal = self.parent / "logs/demarrage.log"
        def demarrer():
            raise RuntimeError("incident fictif")
        with self.assertRaises(SystemExit):
            local.demarrer_avec_journal(demarrer, journal, application="Application fictive",
                notifier=lambda msg: self.fail("Alerte inattendue"), interactif=False)
        self.assertIn("incident fictif", journal.read_text())


if __name__ == "__main__":
    unittest.main()
