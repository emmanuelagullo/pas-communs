"""Application neutre : vrais comptes et sessions Django, aucun modèle métier."""
import unittest
from django.conf import settings
settings.configure(
    SECRET_KEY="cle-fictive-pour-les-tests-uniquement", USE_TZ=True,
    INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    AUTHENTICATION_BACKENDS=["pas_communs.authentification.mots_de_passe.PlafondMotDePasse",
                            "django.contrib.auth.backends.ModelBackend"],
)
import django
django.setup()
from django.contrib.auth import authenticate, get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.management import call_command
from django.test import override_settings
from unittest.mock import patch
from pas_communs.authentification import sessions
from pas_communs.authentification.mots_de_passe import MaximumLengthValidator

call_command("migrate",verbosity=0)


class SessionsTests(unittest.TestCase):
    def setUp(self):
        get_user_model().objects.all().delete()
        self.user = get_user_model().objects.create_user("fictif", password="mot-de-passe-fictif")
        self.user.backend = "django.contrib.auth.backends.ModelBackend"
        self.session = SessionStore()
        self.session.create()

    def attente(self):
        avant = self.session.session_key
        sessions.commencer_attente(self.session,self.user,cle="attente",maintenant=1000)
        self.assertNotEqual(avant,self.session.session_key)
        self.assertNotIn("_auth_user_id",self.session)

    def test_attente_expire_ou_malformee(self):
        self.attente()
        self.assertEqual(sessions.compte_en_attente(self.session,cle="attente",maintenant=1100)[0],self.user)
        self.assertIsNone(sessions.compte_en_attente(self.session,cle="attente",maintenant=1301)[0])
        for valeur in [[], "invalide", {"jusqua":float("nan")}, {"jusqua": "9999"}, {}]:
            self.session["attente"]=valeur
            self.assertEqual(sessions.compte_en_attente(self.session,cle="attente"),(None,None))
            self.assertNotIn("attente",self.session)

    def test_changement_mot_de_passe_revoque_attente(self):
        self.attente()
        self.user.set_password("autre-mot-de-passe-fictif");self.user.save()
        self.assertIsNone(sessions.compte_en_attente(self.session,cle="attente",maintenant=1100)[0])

    def test_compte_desactive_ou_backend_retire(self):
        self.attente()
        self.user.is_active=False;self.user.save()
        self.assertIsNone(sessions.compte_en_attente(self.session,cle="attente",maintenant=1100)[0])
        self.user.is_active=True;self.user.save();self.attente()
        with override_settings(AUTHENTICATION_BACKENDS=[]):
            self.assertIsNone(sessions.compte_en_attente(self.session,cle="attente",maintenant=1100)[0])

    def test_ancien_format_ou_compte_supprime_refuses(self):
        self.attente();del self.session["attente"]["hash"]
        self.assertIsNone(sessions.compte_en_attente(self.session,cle="attente",maintenant=1100)[0])
        self.attente();self.user.delete()
        self.assertIsNone(sessions.compte_en_attente(self.session,cle="attente",maintenant=1100)[0])

    def test_connexion_recente_horodatage_absent_ou_futur(self):
        self.assertFalse(sessions.connexion_recente(self.session,maintenant=1000))
        sessions.noter_authentification(self.session,maintenant=1000)
        self.assertTrue(sessions.connexion_recente(self.session,maintenant=1100))
        self.assertFalse(sessions.connexion_recente(self.session,maintenant=1301))
        self.assertFalse(sessions.connexion_recente(self.session,maintenant=999))

    def test_fermeture_limitee_au_compte_choisi_et_stockage_db(self):
        self.session["_auth_user_id"]=str(self.user.pk);self.session.save()
        autre=SessionStore();autre["_auth_user_id"]="99999";autre.save()
        self.assertEqual(sessions.fermer_sessions_compte(self.user),1)
        self.assertFalse(SessionStore().exists(self.session.session_key))
        self.assertTrue(SessionStore().exists(autre.session_key))
        with override_settings(SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies"):
            with self.assertRaises(ImproperlyConfigured):sessions.fermer_sessions_compte(self.user)

    def test_plafond_refuse_avant_hachage_et_ne_devient_pas_backend_de_session(self):
        with patch.object(get_user_model(),"check_password") as verifier:
            self.assertIsNone(authenticate(username="fictif",password="x"*1025))
            verifier.assert_not_called()
        with self.assertRaises(ValidationError):MaximumLengthValidator().validate("x"*1025)
        MaximumLengthValidator().validate("x"*1024)
        user=authenticate(username="fictif",password="mot-de-passe-fictif")
        self.assertEqual(user.backend,"django.contrib.auth.backends.ModelBackend")


if __name__=="__main__":unittest.main()
