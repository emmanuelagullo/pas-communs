"""Primitives crypto sans modèle utilisateur et sans configuration Django."""
from importlib.util import find_spec
import unittest
from urllib.parse import parse_qs, urlparse
from pas_communs.authentification import totp

DEPENDANCES = all(find_spec(n) is not None for n in ("cryptography", "qrcode", "django_otp"))


@unittest.skipUnless(DEPENDANCES, "Installer requirements-tests-auth.txt pour ces essais")
class TotpTests(unittest.TestCase):
    def setUp(self):
        from cryptography.fernet import Fernet
        self.cles = [Fernet.generate_key()]
        self.secret = b"12345678901234567890"

    def code(self, instant):
        from django_otp.oath import TOTP
        generateur = TOTP(self.secret, step=30, digits=6)
        generateur.time = instant
        return f"{generateur.token():06d}"

    def test_vecteurs_rfc_et_pas_deja_accepte(self):
        self.assertEqual(self.code(59), "287082")
        self.assertEqual(totp.verifier_pas(self.secret, "287082", dernier_pas=0, instant=59), 1)
        self.assertIsNone(totp.verifier_pas(self.secret, "287082", dernier_pas=1, instant=59))

    def test_tolerance_et_format_strict(self):
        instant = 1800000000
        pas = instant // 30
        for ecart in [-1,0,1]:
            self.assertEqual(totp.verifier_pas(self.secret, self.code(instant+ecart*30),
                dernier_pas=pas-2, instant=instant), pas+ecart)
        for code in [self.code(instant+60), "１２３４５６", "12345", "1234567", "abc123"]:
            self.assertIsNone(totp.verifier_pas(self.secret, code, dernier_pas=pas-2, instant=instant))

    def test_chiffrement_rotation_et_separation_des_produits(self):
        from cryptography.fernet import Fernet, InvalidToken
        ancienne = self.cles[0]
        nouvelle = Fernet.generate_key()
        jeton = totp.chiffrer(self.secret, cles=[ancienne])
        self.assertNotIn(totp.cle_en_base32(self.secret), jeton)
        self.assertEqual(totp.dechiffrer(jeton, cles=[nouvelle, ancienne]), self.secret)
        with self.assertRaises(InvalidToken):
            totp.dechiffrer(jeton, cles=[nouvelle])
        neuf = totp.chiffrer(self.secret, cles=[nouvelle, ancienne])
        self.assertEqual(totp.dechiffrer(neuf, cles=[nouvelle]), self.secret)

    def test_emetteur_et_compte_fournis_explicitement(self):
        for emetteur in ["Petits Pas", "Pas à Pas — Accompagnement"]:
            uri = totp.uri_otpauth("compte fictif & essai", self.secret, emetteur=emetteur)
            valeurs = parse_qs(urlparse(uri).query)
            self.assertEqual(valeurs["issuer"], [emetteur])
            self.assertEqual(valeurs["secret"], [totp.cle_en_base32(self.secret)])
            self.assertTrue(totp.qr_svg(uri).startswith("<svg"))

    def test_codes_secours_format_et_empreinte_compatibles(self):
        code = totp.nouveau_code_secours()
        self.assertEqual(len(code), 16)
        self.assertEqual(totp.normaliser_code_secours(totp.presenter_code_secours(code).lower()), code)
        self.assertEqual(len(totp.empreinte_code_secours(code)),64)
        self.assertIsNone(totp.normaliser_code_secours("X" * 15))
