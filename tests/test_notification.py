import io
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace

from pas_communs import notification


class NotificationTests(unittest.TestCase):
    def test_echappement_des_caracteres_speciaux_d_applescript(self):
        self.assertEqual(notification.echapper_applescript('a"b\\c'), 'a\\"b\\\\c')
        self.assertEqual(notification.echapper_applescript("Élève ’test’\nligne 2"), "Élève ’test’\nligne 2")

    def test_script_d_alerte_et_ordre_des_echappements(self):
        script = notification.script_alerte('Petits "Pas"', 'Chemin C:\\x "journal"')
        self.assertEqual(script, 'display alert "Petits \\"Pas\\"" message "Chemin C:\\\\x \\"journal\\"" '
            'as critical buttons {"OK"} default button "OK"')

    def test_sauts_de_ligne_en_expression_return(self):
        self.assertEqual(notification.litteral_applescript("a\r\nb\nc"), '"a" & return & "b" & return & "c"')
        self.assertEqual(notification.litteral_applescript(""), '""')

    def test_notifier_lance_osascript_sans_shell_avec_le_script_en_argument_unique(self):
        appels = []
        notifier = notification.notifier_macos("Petits Pas", executer=lambda commande, **options: appels.append((commande, options)))
        notifier("Erreur\nvoir le journal")
        commande, options = appels[0]
        self.assertEqual(commande[:2], ["osascript", "-e"])
        self.assertEqual(len(commande), 3)
        self.assertIn('"Erreur" & return & "voir le journal"', commande[2])
        self.assertNotIn("\n", commande[2])
        self.assertFalse(options.get("shell", False))

    def test_osascript_absent_ne_masque_pas_l_erreur(self):
        def absent(*args, **options):
            raise FileNotFoundError("osascript")
        flux = io.StringIO()
        with redirect_stderr(flux):
            notification.notifier_macos("Petits Pas", executer=absent)("Démarrage impossible")
        self.assertIn("Démarrage impossible", flux.getvalue())
