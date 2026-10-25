# -*- mode: python ; coding: utf-8 -*-
import importlib.util
import os

from pas_communs.construction import assembler

# Le PDF natif n'est assemblé que si WeasyPrint est installé ; sous Windows, les DLL Pango
# ne sont collectées que si PAS_COMMUNS_PANGO_BIN est défini (profil PDF non qualifié ici).
assembler(
    SPECPATH, globals(), nom="PasCommunsMinimale", settings="minimale.reglages",
    ressources=[("minimale/ressources", "minimale/ressources"), ("version-application.txt", ".")],
    paquets=["minimale"],
    imports=["weasyprint"] if importlib.util.find_spec("weasyprint") else [],
    pango_variable="PAS_COMMUNS_PANGO_BIN" if os.environ.get("PAS_COMMUNS_PANGO_BIN") else None,
    bundle_identifiant="fr.inria.pascommuns.minimale",
)
