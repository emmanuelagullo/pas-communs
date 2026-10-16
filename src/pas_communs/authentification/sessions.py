"""Outils de session Django, sans identité ni politique d’autorisation commune."""
import math
import time


def noter_authentification(session, *, cle="connexion_le", maintenant=None):
    session[cle] = int(time.time() if maintenant is None else maintenant)


def connexion_recente(session, *, cle="connexion_le", delai=300, maintenant=None):
    depuis = session.get(cle)
    maintenant = time.time() if maintenant is None else maintenant
    return type(depuis) is int and 0 <= maintenant - depuis <= delai


def commencer_attente(session, utilisateur, *, cle, delai=300, maintenant=None):
    """Après authenticate(), avant login() : aucune session authentifiée créée."""
    maintenant = time.time() if maintenant is None else maintenant
    session.cycle_key()
    session[cle] = {
        "pk": utilisateur.pk, "backend": utilisateur.backend,
        "jusqua": maintenant + delai,
        "hash": utilisateur.get_session_auth_hash(),
    }


def compte_en_attente(session, *, cle, delai=300, maintenant=None):
    """Revalide compte, backend et mot de passe avant le second facteur.

    Les attentes historiques sans empreinte sont abandonnées ; les sessions
    déjà authentifiées ne sont pas modifiées. L’appelant consomme ensuite le
    code atomiquement, efface l’attente et appelle login().
    """
    from django.conf import settings
    from django.contrib.auth import load_backend
    from django.utils.crypto import constant_time_compare
    maintenant = time.time() if maintenant is None else maintenant
    attente = session.get(cle)
    if isinstance(attente, dict):
        fin = attente.get("jusqua")
        backend = attente.get("backend")
        empreinte = attente.get("hash")
        if (type(fin) in (int, float) and math.isfinite(fin)
                and 0 <= fin - maintenant <= delai
                and backend in settings.AUTHENTICATION_BACKENDS
                and isinstance(empreinte, str) and empreinte
                and isinstance(attente.get("pk"), (int, str))):
            try:
                utilisateur = load_backend(backend).get_user(attente["pk"])
            except (ValueError, TypeError, OverflowError):
                utilisateur = None
            if (utilisateur is not None and utilisateur.is_active
                    and constant_time_compare(empreinte, utilisateur.get_session_auth_hash())):
                return utilisateur, attente
    session.pop(cle, None)
    return None, None


def fermer_sessions_compte(utilisateur):
    """Ferme les sessions Django en base du seul compte choisi ; renvoie le nombre.

    Ne convient pas aux sessions cookies signées ni à un autre stockage.
    Une attente de second facteur n’est pas authentifiée : l’empreinte y est
    revalidée séparément. Aucune permission ni obligation 2FA n’est modifiée.
    """
    from django.conf import settings
    from django.contrib.sessions.models import Session
    from django.core.exceptions import ImproperlyConfigured
    from django.utils import timezone
    if settings.SESSION_ENGINE != "django.contrib.sessions.backends.db":
        raise ImproperlyConfigured("La fermeture des sessions exige le stockage Django en base.")
    nombre = 0
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        if session.get_decoded().get("_auth_user_id") == str(utilisateur.pk):
            session.delete()
            nombre += 1
    return nombre
