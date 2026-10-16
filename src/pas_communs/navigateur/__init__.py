"""Ressources statiques PWA distribuées dans le wheel, sans téléchargement à l’usage."""
from importlib.resources import files
from pathlib import Path

RESSOURCES = ("stockage.mjs", "transport.mjs", "capacites.mjs")


def copier_ressources(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for nom in RESSOURCES:
        (destination / nom).write_bytes(files(__package__).joinpath(nom).read_bytes())
