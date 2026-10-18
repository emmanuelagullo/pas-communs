import unittest
from pas_communs.serveur import configuration_https

CLE = "cle-aleatoire-fictive-pour-tests-uniquement-8293746510-ABCDE"


class ServeurTests(unittest.TestCase):
    def configuration(self, **options):
        return configuration_https(**{"cle":CLE, "hotes":"serveur.fictif.example, [::1]",
            "origines":"https://serveur.fictif.example,https://localhost:8443", **options})

    def test_https_sans_confiance_automatique_aux_entetes(self):
        s = self.configuration()
        self.assertFalse(s["DEBUG"])
        self.assertTrue(s["SECURE_SSL_REDIRECT"])
        self.assertTrue(s["SESSION_COOKIE_SECURE"])
        self.assertTrue(s["CSRF_COOKIE_SECURE"])
        self.assertIsNone(s["SECURE_PROXY_SSL_HEADER"])
        self.assertFalse(s["USE_X_FORWARDED_HOST"])
        self.assertFalse(s["SECURE_HSTS_INCLUDE_SUBDOMAINS"])
        self.assertFalse(s["SECURE_HSTS_PRELOAD"])
        self.assertEqual(s["ALLOWED_HOSTS"],["serveur.fictif.example","[::1]"])
        self.assertEqual(s["X_FRAME_OPTIONS"],"DENY")

    def test_proxy_est_une_decision_explicite(self):
        self.assertEqual(self.configuration(proxy_https="oui")["SECURE_PROXY_SSL_HEADER"],("HTTP_X_FORWARDED_PROTO","https"))
        for valeur in ["true", "", True]:
            with self.subTest(valeur=valeur),self.assertRaises(ValueError):self.configuration(proxy_https=valeur)

    def test_cle_faible_refusee_sans_la_recopier_dans_erreur(self):
        for cle in ["secret-fictif-court", "a"*64,"django-insecure-"+CLE]:
            with self.subTest(cle=cle),self.assertRaises(ValueError) as erreur:self.configuration(cle=cle)
            self.assertNotIn(cle,str(erreur.exception))

    def test_hotes_et_origines_ambigus_refuses(self):
        for hotes in ["", "*", ".example.org", "https://example.org", "example.org:8000", "example.org:", "user@example.org", "example.org/", "example.org,,autre.org"]:
            with self.subTest(hotes=hotes),self.assertRaises(ValueError):self.configuration(hotes=hotes)
        for origines in ["", "http://example.org", "https://*.example.org", "https://user@example.org", "https://example.org/", "https://example.org?x=1", "https://example.org#x", "https://example.org:invalide"]:
            with self.subTest(origines=origines),self.assertRaises(ValueError):self.configuration(origines=origines)

    def test_hsts_borne_sans_activation_globale_implicite(self):
        for valeur in ["-1", "1.5", "oui", "31536001"]:
            with self.subTest(valeur=valeur),self.assertRaises(ValueError):self.configuration(hsts=valeur)
        self.assertEqual(self.configuration(hsts="0")["SECURE_HSTS_SECONDS"],0)
        self.assertEqual(self.configuration(hsts="31536000")["SECURE_HSTS_SECONDS"],31536000)
