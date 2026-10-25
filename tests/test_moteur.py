import unittest
from unittest.mock import patch

from pas_communs import moteur


def registre(valeurs):
    return lambda racine, chemin, valeur: valeurs.get((racine, chemin, valeur))


CLE_64 = ("HKLM", "SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\" + moteur.GUID_WEBVIEW2, "pv")
CLE_UTILISATEUR = ("HKCU", "Software\\Microsoft\\EdgeUpdate\\Clients\\" + moteur.GUID_WEBVIEW2, "pv")


class MoteurTests(unittest.TestCase):
    def test_webview2_detecte_selon_les_emplacements_documentes(self):
        self.assertEqual(moteur.version_webview2(registre({CLE_64: "131.0.2903.86"})), "131.0.2903.86")
        self.assertEqual(moteur.version_webview2(registre({CLE_UTILISATEUR: " 140.0.1 "})), "140.0.1")

    def test_webview2_absent_si_valeur_vide_nulle_ou_inconnue(self):
        for valeurs in ({}, {CLE_64: ""}, {CLE_64: "0.0.0.0"}, {CLE_64: None}, {CLE_64: 5}):
            with self.subTest(valeurs=valeurs):
                self.assertIsNone(moteur.version_webview2(registre(valeurs)))

    def test_lecture_du_registre_retourne_none_hors_windows(self):
        with patch.object(moteur.sys, "platform", "linux"):
            self.assertIsNone(moteur.lire_registre("HKLM", "SOFTWARE\\Absent", "pv"))

    def test_disponibilite_par_systeme(self):
        self.assertTrue(moteur.moteur_disponible("win32", lire=registre({CLE_64: "1.0"})))
        self.assertFalse(moteur.moteur_disponible("win32", lire=registre({})))
        self.assertTrue(moteur.moteur_disponible("darwin"))
        self.assertTrue(moteur.moteur_disponible("linux", webkitgtk=lambda: True))
        self.assertFalse(moteur.moteur_disponible("linux", webkitgtk=lambda: False))

    def test_messages_nomment_le_produit_et_la_marche_a_suivre(self):
        windows = moteur.message_moteur_absent("Petits Pas", "win32")
        self.assertIn("Petits Pas", windows)
        self.assertIn(moteur.URL_WEBVIEW2, windows)
        self.assertIn("ignorer", windows)
        self.assertIn("gir1.2-webkit2-4.1", moteur.message_moteur_absent("Petits Pas", "linux"))
        self.assertIn("Mise à jour de logiciels", moteur.message_moteur_absent("Petits Pas", "darwin"))

    def test_signaler_ne_notifie_que_si_le_moteur_manque_et_ne_bloque_pas(self):
        messages = []
        self.assertTrue(moteur.signaler_moteur("Produit", notifier=messages.append, plateforme="win32",
            lire=registre({CLE_64: "1.0"})))
        self.assertEqual(messages, [])
        self.assertFalse(moteur.signaler_moteur("Produit", notifier=messages.append, plateforme="win32",
            lire=registre({})))
        self.assertEqual(len(messages), 1)
        self.assertIn("Produit", messages[0])
