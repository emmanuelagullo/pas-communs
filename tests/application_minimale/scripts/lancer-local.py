"""Lanceur de l'application minimale : exerce les mécanismes du socle, sans métier.

Les options de vérification n'ouvrent aucune fenêtre, sauf --fenetre-auto, qui
ouvre la vraie fenêtre PyWebView, attend le chargement de la page puis la ferme.
"""
import argparse
import json
import sqlite3
import sys
import tempfile
import threading
from contextlib import closing
from pathlib import Path
from urllib.request import urlopen

import pas_communs
from pas_communs import local, moteur
from pas_communs.plateforme import systeme
from minimale.application import RESSOURCES, application
from minimale.reglages import NOM_APPLICATION, NOM_BASE

MOTEURS = {"windows": "webview.platforms.winforms", "macos": "webview.platforms.cocoa",
           "linux": "webview.platforms.gtk"}


def preparer(paquet):
    paquet.parent.mkdir(parents=True, exist_ok=True)
    with local.verrouiller(paquet):
        local.initialiser_paquet(paquet, nom_base=NOM_BASE)
        with closing(sqlite3.connect(paquet / NOM_BASE)) as base, base:
            base.execute("CREATE TABLE IF NOT EXISTS temoin (valeur TEXT NOT NULL)")


def verifier_distribution():
    """Contrôles sans fenêtre ni donnée utilisateur ; le moteur n'est importé que dans un programme gelé."""
    if getattr(sys, "frozen", False):
        __import__(MOTEURS[systeme(strict=True)])
    with tempfile.TemporaryDirectory() as temporaire:
        paquet = Path(temporaire) / "donnees" / "paquet"
        preparer(paquet)
        with local.ServeurBureau(application) as serveur:
            with urlopen(serveur.url, timeout=5) as reponse:
                if NOM_APPLICATION.encode() not in reponse.read():
                    raise RuntimeError("La page locale n'est pas servie.")
            serveur.verifier_css("style.css")
            with urlopen(serveur.url + "sante", timeout=5) as reponse:
                if json.load(reponse)["pas_communs"] != pas_communs.__version__:
                    raise RuntimeError("Version du socle incohérente.")
    print("Distribution vérifiée : " + pas_communs.__version__)


def verifier_moteur():
    """Sonde du moteur de fenêtre : échoue si le composant système semble absent."""
    if not moteur.signaler_moteur(NOM_APPLICATION, notifier=lambda message: print(message, file=sys.stderr)):
        raise SystemExit(1)
    print("Moteur de fenêtre détecté.")


def verifier_pdf():
    from pas_communs import pdf
    recuperer = pdf.recuperateur_medias([], schema="media:", ouvrir=open)
    octets = pdf.rendre_html("<p>Sonde PDF</p>", base_url=str(RESSOURCES),
                             feuille_style=str(RESSOURCES / "style.css"), recuperer=recuperer)
    if not octets.startswith(b"%PDF"):
        raise RuntimeError("WeasyPrint n'a pas produit de PDF.")
    print("PDF natif vérifié : %d octets" % len(octets))


def temoin(paquet, action):
    preparer(paquet)
    with closing(sqlite3.connect(paquet / NOM_BASE)) as base:
        if action == "ecrire":
            with base:
                base.execute("INSERT INTO temoin (valeur) VALUES ('conserve')")
            print("Témoin écrit : " + str(paquet))
        else:
            ligne = base.execute("SELECT valeur FROM temoin").fetchone()
            if not ligne or ligne[0] != "conserve":
                raise SystemExit("Témoin absent : les données n'ont pas été conservées.")
            print("Témoin relu : " + str(paquet))


def ouvrir(serveur, delai):
    import webview
    # Indice seulement : la fenêtre est tentée même si la sonde se trompe.
    moteur.signaler_moteur(NOM_APPLICATION, notifier=lambda message: print(message, file=sys.stderr))
    fenetre = local.creer_fenetre("Pas communs — application minimale", serveur.url)
    chargee = threading.Event()
    fenetre.events.loaded += chargee.set
    etat = {}

    def fermer():
        etat["chargee"] = chargee.wait(delai)
        fenetre.destroy()

    webview.start(fermer if delai else None)
    if delai and not etat.get("chargee"):
        raise SystemExit("La page n'a pas été chargée dans la fenêtre.")
    if delai:
        print("Fenêtre vérifiée : page chargée.")


def lancer(paquet, *, sans_fenetre, delai):
    preparer(paquet)
    with local.verrouiller(paquet), local.ServeurBureau(application) as serveur:
        if sans_fenetre:
            print(serveur.url, flush=True)
            threading.Event().wait()
        else:
            ouvrir(serveur, delai)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="store_true")
    p.add_argument("--verifier-distribution", action="store_true")
    p.add_argument("--verifier-pdf", action="store_true")
    p.add_argument("--verifier-moteur", action="store_true")
    p.add_argument("--chemin-donnees", action="store_true")
    p.add_argument("--temoin", choices=("ecrire", "lire"))
    p.add_argument("--sans-fenetre", action="store_true")
    p.add_argument("--fenetre-auto", type=int, metavar="SECONDES")
    p.add_argument("--paquet", type=Path)
    a = p.parse_args(argv)
    paquet = a.paquet or local.paquet_par_defaut(NOM_APPLICATION)
    if a.version:
        print(pas_communs.__version__)
    elif a.verifier_distribution:
        verifier_distribution()
    elif a.verifier_pdf:
        verifier_pdf()
    elif a.verifier_moteur:
        verifier_moteur()
    elif a.chemin_donnees:
        print(paquet)
    elif a.temoin:
        temoin(paquet, a.temoin)
    else:
        lancer(paquet, sans_fenetre=a.sans_fenetre, delai=a.fenetre_auto)


if __name__ == "__main__":
    main()
