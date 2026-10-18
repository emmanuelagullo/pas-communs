"""Contrat HTTPS Django explicite, sans import Django ni modèle métier.

Les produits choisissent leur clé, base, chemins et politique de proxy.
Ce module ne lit ni fichier ni variable d'environnement et ne déploie rien.
"""
from urllib.parse import urlsplit


def configuration_https(*, cle, hotes, origines, proxy_https="non", hsts="3600"):
    """Retourner uniquement les réglages communs d'un profil serveur volontaire.

    Erreurs sans valeur sensible : ne jamais recopier une clé dans un diagnostic.
    La robustesse cryptographique d'une clé doit venir de son générateur.
    """
    if (not isinstance(cle, str) or len(cle) < 50 or len(set(cle)) < 5
            or cle.startswith("django-insecure-")):
        raise ValueError("Le profil serveur exige une clé aléatoire stable d'au moins 50 caractères.")
    hotes = [h.strip() for h in hotes.split(",")] if isinstance(hotes, str) else list(hotes)
    if not hotes or any(not h or h != h.strip() or any(c.isspace() for c in h) for h in hotes):
        raise ValueError("Définir explicitement les hôtes du serveur.")
    for hote in hotes:
        try:
            url = urlsplit("https://" + hote)
            if ("*" in hote or hote.startswith(".") or hote.endswith(":") or not url.hostname
                    or url.username is not None or url.password is not None or url.port is not None
                    or url.path or url.query or url.fragment or url.netloc != hote):
                raise ValueError()
        except ValueError:
            raise ValueError("Les hôtes doivent être des noms ou IP exacts, sans URL, port ni joker.") from None
    origines = [o.strip() for o in origines.split(",")] if isinstance(origines, str) else list(origines)
    if not origines:
        raise ValueError("Définir explicitement les origines CSRF HTTPS.")
    for origine in origines:
        try:
            url = urlsplit(origine)
            if (url.scheme != "https" or not url.hostname or url.username is not None
                    or url.password is not None or url.path or url.query or url.fragment
                    or "*" in origine or any(c.isspace() for c in origine)):
                raise ValueError()
            url.port  # contrôle aussi les ports non numériques ou hors limites
        except ValueError:
            raise ValueError("Les origines CSRF doivent être des origines HTTPS exactes, sans chemin.") from None
    if proxy_https not in {"oui", "non"}:
        raise ValueError("La confiance au proxy HTTPS attend oui ou non.")
    try:
        secondes = int(hsts)
        if str(secondes) != str(hsts) or not 0 <= secondes <= 31536000:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError("La durée HSTS doit être un entier entre 0 et 31536000 secondes.") from None
    return {
        "SECRET_KEY": cle, "DEBUG": False, "ALLOWED_HOSTS": hotes,
        "CSRF_TRUSTED_ORIGINS": origines, "SECURE_SSL_REDIRECT": True,
        "SESSION_COOKIE_SECURE": True, "SESSION_COOKIE_HTTPONLY": True,
        "CSRF_COOKIE_SECURE": True, "SECURE_CONTENT_TYPE_NOSNIFF": True,
        "SECURE_HSTS_SECONDS": secondes, "SECURE_HSTS_INCLUDE_SUBDOMAINS": False,
        "SECURE_HSTS_PRELOAD": False, "X_FRAME_OPTIONS": "DENY",
        "SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https") if proxy_https == "oui" else None,
        "USE_X_FORWARDED_HOST": False,
    }
