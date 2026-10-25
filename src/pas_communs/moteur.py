"""Moteur de fenêtre des programmes de bureau : sonde et message pour non-informaticiens.

La sonde Windows suit la détection documentée par Microsoft (clé pv de WebView2). Elle
reste un indice : un produit affiche le message sans bloquer, car une clé absente
n'interdit pas toujours l'ouverture de la fenêtre.
"""
import sys

from .plateforme import systeme

GUID_WEBVIEW2 = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
URL_WEBVIEW2 = "https://developer.microsoft.com/microsoft-edge/webview2/"
_CLES_WEBVIEW2 = (
    ("HKLM", "SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\" + GUID_WEBVIEW2),
    ("HKCU", "Software\\Microsoft\\EdgeUpdate\\Clients\\" + GUID_WEBVIEW2),
    ("HKLM", "SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\" + GUID_WEBVIEW2),
)


def lire_registre(racine, chemin, valeur):
    """Valeur texte du registre Windows, ou None ; toujours None hors Windows."""
    if sys.platform != "win32":
        return None
    import winreg
    base = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}[racine]
    try:
        with winreg.OpenKey(base, chemin) as cle:
            contenu, genre = winreg.QueryValueEx(cle, valeur)
    except OSError:
        return None
    return contenu if genre == winreg.REG_SZ else None


def version_webview2(lire=lire_registre):
    for racine, chemin in _CLES_WEBVIEW2:
        version = lire(racine, chemin, "pv")
        if isinstance(version, str) and version.strip() not in ("", "0.0.0.0"):
            return version.strip()
    return None


def _webkitgtk_present():
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("WebKit2", "4.1")
        from gi.repository import WebKit2  # noqa: F401
    except (ImportError, ValueError):
        return False
    return True


def moteur_disponible(plateforme=None, *, lire=lire_registre, webkitgtk=_webkitgtk_present):
    cible = systeme(plateforme)
    if cible == "windows":
        return version_webview2(lire) is not None
    if cible == "macos":
        return True  # WKWebView fait partie de macOS.
    return bool(webkitgtk())


def message_moteur_absent(application, plateforme=None):
    cible = systeme(plateforme)
    if cible == "windows":
        return (f"{application} utilise le composant Microsoft Edge WebView2, qui n’a pas été détecté "
            "sur cet ordinateur.\n\n"
            f"Pour l’installer : ouvrez {URL_WEBVIEW2}, téléchargez « Evergreen Bootstrapper » "
            "(ou « Evergreen Standalone Installer » sans connexion Internet), lancez-le, puis "
            f"relancez {application}.\n\n"
            "Si la fenêtre s’ouvre normalement malgré ce message, vous pouvez l’ignorer.")
    if cible == "linux":
        return (f"{application} a besoin de GTK 3 et de WebKitGTK 4.1, qui n’ont pas été détectés.\n\n"
            "Sous Ubuntu 24.04, dans un terminal : sudo apt install gir1.2-gtk-3.0 gir1.2-webkit2-4.1\n"
            f"Relancez ensuite {application}. Les autres distributions ne sont pas qualifiées.")
    return (f"{application} utilise WebKit, qui fait partie de macOS et n’a pas pu être chargé.\n\n"
        "Mettez macOS à jour (Réglages Système, Général, Mise à jour de logiciels), "
        f"puis relancez {application}.")


def signaler_moteur(application, *, notifier, plateforme=None, **sondes):
    """Notifier si le moteur semble absent ; retourne True s'il est disponible. Ne bloque jamais."""
    if moteur_disponible(plateforme, **sondes):
        return True
    notifier(message_moteur_absent(application, plateforme))
    return False
