import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pas_communs import pango_macos

try:
    import cffi
except ImportError:  # extras PDF absents
    cffi = None


def bibliotheques_homebrew(dossier):
    """Imite Homebrew : fichier réel numéroté et lien de nom court pour pango et pangoft2."""
    for demande, reel in pango_macos.BIBLIOTHEQUES:
        (dossier / reel).write_bytes(b"dylib fictive " + reel.encode())
        if demande != reel:
            (dossier / demande).symlink_to(reel)


class FichiersAEmbarquerTests(unittest.TestCase):
    def test_la_bibliotheque_d_allegement_des_polices_n_est_pas_embarquee(self):
        noms = {demande for demande, _ in pango_macos.BIBLIOTHEQUES} | {reel for _, reel in pango_macos.BIBLIOTHEQUES}
        self.assertNotIn(pango_macos.BIBLIOTHEQUE_IGNOREE, noms)
        self.assertEqual(len(pango_macos.BIBLIOTHEQUES), 5)

    def test_images_chargees_ne_plante_pas_hors_de_macos(self):
        self.assertIsInstance(pango_macos._images_chargees(), list)

    def test_images_chargees_tolere_une_erreur_de_ctypes_comme_sous_windows(self):
        """ctypes.CDLL(None) lève TypeError sous Windows : jamais d'exception vers WeasyPrint."""
        import ctypes
        with patch.object(pango_macos.sys, "platform", "darwin"), patch.object(ctypes, "CDLL", side_effect=TypeError("None")):
            self.assertEqual(pango_macos._images_chargees(), [])

    def test_liens_resolus_vers_les_fichiers_reels(self):
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t).resolve()
            bibliotheques_homebrew(dossier)
            noms = sorted(chemin.name for chemin in pango_macos.fichiers_a_embarquer(dossier))
            self.assertEqual(noms, sorted(reel for _, reel in pango_macos.BIBLIOTHEQUES))

    def test_bibliotheque_manquante_nommee(self):
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            bibliotheques_homebrew(dossier)
            (dossier / "libharfbuzz.0.dylib").unlink()
            with self.assertRaises(FileNotFoundError) as ctx:
                pango_macos.fichiers_a_embarquer(dossier)
            self.assertIn("libharfbuzz.0.dylib", str(ctx.exception))


@unittest.skipIf(cffi is None, "cffi absent")
class PreparationAuLancementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.racine = Path(self.temp.name).resolve()
        self.appels = []
        original = cffi.FFI.dlopen
        self.addCleanup(setattr, cffi.FFI, "dlopen", original)
        self.addCleanup(setattr, pango_macos, "_pret", False)
        cffi.FFI.dlopen = lambda ffi, name, flags=0: self.appels.append((name, flags)) or "bibliotheque"
        # Par défaut aucune image déjà chargée : les essais ne dépendent pas de ctypes ni du système.
        stub = patch.object(pango_macos, "_images_chargees", return_value=[])
        stub.start()
        self.addCleanup(stub.stop)

    def gele_sous_macos(self, avec_pango=True):
        if avec_pango:
            bibliotheques_homebrew(self.racine)
            for demande, _ in pango_macos.BIBLIOTHEQUES:
                if (self.racine / demande).is_symlink():
                    (self.racine / demande).unlink()  # le bundle ne contient que les fichiers réels
        return (patch.object(pango_macos.sys, "platform", "darwin"),
                patch.object(pango_macos.sys, "frozen", True, create=True),
                patch.object(pango_macos.sys, "_MEIPASS", str(self.racine), create=True),
                patch.dict(os.environ, {}, clear=False))

    def preparer(self, **options):
        contextes = self.gele_sous_macos(**options)
        for contexte in contextes:
            contexte.start()
            self.addCleanup(contexte.stop)
        os.environ.pop("FONTCONFIG_FILE", None)
        return pango_macos.preparer_pango_embarque()

    def test_charge_les_noms_de_weasyprint_par_chemin_absolu_du_bundle(self):
        self.assertTrue(self.preparer())
        ffi = cffi.FFI()
        ffi.dlopen("libpango-1.0.dylib", 2)
        ffi.dlopen("libgobject-2.0.0.dylib")
        ffi.dlopen("libpango-1.0-0")  # nom absent du bundle : transmis tel quel, WeasyPrint essaie le suivant
        self.assertEqual(self.appels, [(str(self.racine / "libpango-1.0.0.dylib"), 2),
            (str(self.racine / "libgobject-2.0.0.dylib"), 0), ("libpango-1.0-0", 0)])

    def test_reutilise_l_image_deja_chargee_plutot_que_la_copie_du_bundle(self):
        """Pillow embarque son HarfBuzz : Pango y est rattaché, WeasyPrint doit utiliser le même."""
        self.assertTrue(self.preparer())
        deja = "/app/Frameworks/PIL/__dot__dylibs/libharfbuzz.0.dylib"
        with patch.object(pango_macos, "_images_chargees", return_value=["/usr/lib/libSystem.B.dylib", deja]):
            cffi.FFI().dlopen("libharfbuzz.0.dylib")
            cffi.FFI().dlopen("libpango-1.0.dylib")  # pas encore chargée : copie du bundle
        self.assertEqual(self.appels, [(deja, 0), (str(self.racine / "libpango-1.0.0.dylib"), 0)])

    def test_bibliotheque_d_allegement_des_polices_refusee(self):
        self.assertTrue(self.preparer())
        with self.assertRaises(OSError):
            cffi.FFI().dlopen("libharfbuzz-subset.0.dylib")
        self.assertEqual(self.appels, [])  # jamais transmise à dlopen : WeasyPrint passe par fontTools

    def test_configuration_fontconfig_vers_les_polices_du_systeme(self):
        self.assertTrue(self.preparer())
        configuration = Path(os.environ["FONTCONFIG_FILE"])
        self.assertTrue(configuration.is_file())
        texte = configuration.read_text(encoding="utf-8")
        for attendu in ("/System/Library/Fonts", "/Library/Fonts", "~/Library/Fonts", "<cachedir>"):
            self.assertIn(attendu, texte)

    def test_configuration_fontconfig_de_l_utilisateur_respectee(self):
        contextes = self.gele_sous_macos()
        for contexte in contextes:
            contexte.start()
            self.addCleanup(contexte.stop)
        os.environ["FONTCONFIG_FILE"] = "/chemin/utilisateur.conf"
        self.assertTrue(pango_macos.preparer_pango_embarque())
        self.assertEqual(os.environ["FONTCONFIG_FILE"], "/chemin/utilisateur.conf")

    def test_sans_effet_hors_programme_gele_ou_hors_macos_ou_sans_pango(self):
        self.assertFalse(pango_macos.preparer_pango_embarque())  # sources, Linux
        with patch.object(pango_macos.sys, "platform", "darwin"):
            self.assertFalse(pango_macos.preparer_pango_embarque())  # pas gelé
        self.assertFalse(self.preparer(avec_pango=False))  # gelé sous macOS, bundle sans Pango
        self.assertEqual(cffi.FFI.dlopen(cffi.FFI(), "libpango-1.0.dylib"), "bibliotheque")
        self.assertEqual(self.appels[-1][0], "libpango-1.0.dylib")
