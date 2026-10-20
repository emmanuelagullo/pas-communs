"""Cycle historique et neutralisation explicite de la seule copie."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from pas_communs.paquets import RestaurationLocale, vider_tables_copie


class RestaurationTests(unittest.TestCase):
    def test_annulation_puis_confirmation(self):
        with tempfile.TemporaryDirectory() as t:
            etape = Path(t) / "preparation"
            etape.mkdir()
            copie = SimpleNamespace(etape=etape)
            etat = RestaurationLocale()
            etat.retenir(copie)
            with self.assertRaises(ValueError):
                etat.retenir(copie)
            etat.annuler()
            self.assertFalse(etape.exists())
            etape.mkdir()
            etat.retenir(copie)
            self.assertIs(etat.confirmer(), copie)
            etat.annuler()  # une confirmation ne devient pas une suppression
            self.assertTrue(etape.exists())
            self.assertIs(etat.attente(), copie)
            with self.assertRaises(ValueError):
                etat.confirmer()

    def test_tables_explicitement_choisies_et_absentes(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t) / "copie.sqlite3"
            with self.assertRaises(ValueError):
                vider_tables_copie(base, ("sessions",))
            self.assertFalse(base.exists())
            with closing(sqlite3.connect(base)) as db, db:
                db.execute('CREATE TABLE sessions (valeur)')
                db.execute("INSERT INTO sessions VALUES ('session-fictive')")
                db.execute('CREATE TABLE facteurs (valeur)')
                db.execute("INSERT INTO facteurs VALUES ('facteur-fictif')")
            vider_tables_copie(base, ("sessions", "ancienne_table_absente"))
            with closing(sqlite3.connect(base)) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0], 0)
                self.assertEqual(db.execute('SELECT valeur FROM facteurs').fetchone()[0], 'facteur-fictif')
