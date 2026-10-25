"""Notification d'erreur des programmes de bureau sous macOS.

Un .app n'a pas de console : sans notification, un échec de démarrage ne dirait rien à
l'utilisateur. Utiliser avec local.demarrer_avec_journal :
    notifier=notification.notifier_macos("Petits Pas")
"""
import subprocess
import sys


def echapper_applescript(texte):
    """Rend un texte sûr dans une chaîne AppleScript entre guillemets (seuls \\ et \" sont spéciaux)."""
    return str(texte).replace("\\", "\\\\").replace('"', '\\"')


def litteral_applescript(texte):
    """Expression AppleScript d'un texte : les sauts de ligne deviennent « return », valable partout."""
    lignes = str(texte).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return " & return & ".join('"' + echapper_applescript(ligne) + '"' for ligne in lignes)


def script_alerte(titre, message):
    return (f"display alert {litteral_applescript(titre)} message {litteral_applescript(message)} "
            'as critical buttons {"OK"} default button "OK"')


def notifier_macos(application, *, executer=subprocess.run):
    """Retourne notifier(message) : affiche une alerte macOS, sans jamais masquer l'erreur d'origine."""
    def notifier(message):
        try:
            executer(["osascript", "-e", script_alerte(application, message)], check=False)
        except OSError:
            print(f"{application} : {message}", file=sys.stderr)
    return notifier
