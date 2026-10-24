"""Application WSGI minimale servie par ServeurBureau."""
import json
from pathlib import Path

import pas_communs

from .reglages import NOM_APPLICATION

RESSOURCES = Path(__file__).with_name("ressources")
PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>Pas communs — application minimale</title>
<link rel="stylesheet" href="/style.css"></head>
<body><h1>Pas communs — application minimale</h1>
<p>Cette fenêtre qualifie les programmes de bureau du socle. Aucune donnée réelle.</p>
<p id="identifiant">%s</p></body></html>
"""


def application(environ, start_response):
    chemin = environ.get("PATH_INFO", "/")
    if chemin == "/":
        corps, type_contenu = (PAGE % NOM_APPLICATION).encode("utf-8"), "text/html; charset=utf-8"
    elif chemin == "/style.css":
        corps, type_contenu = (RESSOURCES / "style.css").read_bytes(), "text/css; charset=utf-8"
    elif chemin == "/sante":
        corps = json.dumps({"application": NOM_APPLICATION, "pas_communs": pas_communs.__version__}).encode("utf-8")
        type_contenu = "application/json"
    else:
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Introuvable.\n"]
    start_response("200 OK", [("Content-Type", type_contenu), ("Content-Length", str(len(corps)))])
    return [corps]
