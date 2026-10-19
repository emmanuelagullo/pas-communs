from pathlib import PureWindowsPath
import unittest
from pas_communs.chemins import composants_portables, verifier_arbre


class CheminsTests(unittest.TestCase):
    def test_chemins_portables_restent_dans_la_preparation_windows(self):
        for lecteur in ('C:', 'D:'):
            racine = PureWindowsPath(lecteur + '/preparation')
            for nom in ('media/photo.jpg', 'media/École/production 1.png'):
                self.assertTrue(racine.joinpath(*composants_portables(nom)).is_relative_to(racine))

    def test_alias_windows_refuses_sur_tous_les_systemes(self):
        for nom in ('media/C:/a', 'media/D:a', 'media/a:flux', 'media/CON.txt',
                    'media/CON .txt', 'media/lpt1', 'media/COM¹.txt', 'media/NUL', 'media/a.',
                    'media/a ', 'media/a?.txt', 'media/a\x00', '/media/a',
                    'media//a', 'media/./a', 'media/../a', 'media/a\\b'):
            with self.subTest(nom=nom), self.assertRaises(ValueError):
                composants_portables(nom)

    def test_collisions_de_fichiers_et_repertoires(self):
        for noms in (['media/A', 'media/a'], ['media/A/x', 'media/a/y'],
                     ['media/a', 'media/a/x'], ['media/a/x', 'media/a'],
                     ['media/a', 'media/a']):
            with self.subTest(noms=noms), self.assertRaises(ValueError):
                verifier_arbre(noms)
        verifier_arbre(['base.sqlite3', 'media/école/a', 'media/école/b'])
