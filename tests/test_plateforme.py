import unittest
from unittest.mock import patch

from pas_communs import plateforme


class PlateformeTests(unittest.TestCase):
    def test_systemes_pris_en_charge_et_valeurs_historiques(self):
        attendus = {"win32": "windows", "nt": "windows", "windows": "windows",
            "darwin": "macos", "macos": "macos",
            "linux": "linux", "linux2": "linux", "posix": "linux"}
        for brut, systeme in attendus.items():
            with self.subTest(brut=brut):
                self.assertEqual(plateforme.systeme(brut, strict=True), systeme)

    def test_plateforme_courante_par_defaut(self):
        for brut, systeme in (("win32", "windows"), ("darwin", "macos"), ("linux", "linux")):
            with self.subTest(brut=brut), patch.object(plateforme.sys, "platform", brut):
                self.assertEqual(plateforme.systeme(), systeme)

    def test_systeme_inconnu_refuse_en_mode_strict_seulement(self):
        self.assertEqual(plateforme.systeme("freebsd14"), "linux")
        with self.assertRaises(ValueError):
            plateforme.systeme("freebsd14", strict=True)

    def test_macos_livre_uniquement_arm64(self):
        self.assertEqual(plateforme.ARCHITECTURE_MACOS, "arm64")
