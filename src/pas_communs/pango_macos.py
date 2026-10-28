"""PDF natif sous macOS : embarquer Pango dans le .app et le faire charger à WeasyPrint.

macOS ne cherche pas les bibliothèques par nom hors de /usr/lib, et un Mac d'utilisateur n'a pas
Homebrew. À la construction, les cinq bibliothèques que WeasyPrint charge sont copiées dans le
bundle (PyInstaller y ajoute leurs dépendances et réécrit leurs chemins) ; au lancement, cffi
reçoit leur chemin absolu et fontconfig une configuration minimale vers les polices du système.

Une seule copie de chaque bibliothèque doit vivre dans le processus. PyInstaller identifie les
dylibs par leur nom : si un autre paquet en embarque une du même nom (Pillow embarque HarfBuzz,
FreeType et libpng), Pango est rattaché à celle-là. WeasyPrint reçoit donc l'image déjà chargée
plutôt que sa propre copie ; mélanger deux HarfBuzz faisait planter hb_subset (SIGBUS). La
bibliothèque d'allègement des polices (libharfbuzz-subset) n'est ni embarquée ni chargée :
WeasyPrint se rabat alors sur fontTools, qu'il embarque déjà.
"""
import atexit
import os
from pathlib import Path
import sys
import tempfile

# (nom que WeasyPrint demande sous macOS, nom du fichier réel chez Homebrew)
BIBLIOTHEQUES = (
    ("libgobject-2.0.0.dylib", "libgobject-2.0.0.dylib"),
    ("libpango-1.0.dylib", "libpango-1.0.0.dylib"),
    ("libharfbuzz.0.dylib", "libharfbuzz.0.dylib"),
    ("libfontconfig.1.dylib", "libfontconfig.1.dylib"),
    ("libpangoft2-1.0.dylib", "libpangoft2-1.0.0.dylib"),
)
# Refusée au chargement : WeasyPrint alloue alors les polices avec fontTools (allow_fail=True).
BIBLIOTHEQUE_IGNOREE = "libharfbuzz-subset.0.dylib"
CONFIGURATION_POLICES = """<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir>/System/Library/Fonts</dir>
  <dir>/System/Library/Fonts/Supplemental</dir>
  <dir>/Library/Fonts</dir>
  <dir>~/Library/Fonts</dir>
  <cachedir>~/Library/Caches/fontconfig</cachedir>
  <alias><family>sans-serif</family><prefer><family>Helvetica Neue</family><family>Helvetica</family><family>Arial</family></prefer></alias>
  <alias><family>serif</family><prefer><family>Times New Roman</family><family>Times</family></prefer></alias>
  <alias><family>monospace</family><prefer><family>Menlo</family><family>Courier New</family></prefer></alias>
</fontconfig>
"""
_pret = False


def fichiers_a_embarquer(dossier):
    """Fichiers réels (liens symboliques résolus) à copier à la racine du bundle."""
    dossier = Path(dossier)
    trouves, manquants = [], []
    for demande, reel in BIBLIOTHEQUES:
        candidat = next((dossier / nom for nom in (demande, reel) if (dossier / nom).is_file()), None)
        if candidat is None:
            manquants.append(demande)
        else:
            trouves.append(candidat.resolve())
    if manquants:
        raise FileNotFoundError(f"Bibliothèques Pango manquantes dans {dossier} : {manquants}")
    return trouves


def _images_chargees():
    """Chemins des bibliothèques déjà chargées dans le processus (dyld) ; vide si indisponible."""
    try:
        import ctypes
        systeme = ctypes.CDLL(None)
        systeme._dyld_image_count.restype = ctypes.c_uint32
        systeme._dyld_get_image_name.restype = ctypes.c_char_p
        systeme._dyld_get_image_name.argtypes = [ctypes.c_uint32]
        noms = (systeme._dyld_get_image_name(i) for i in range(systeme._dyld_image_count()))
        return [nom.decode("utf-8", "replace") for nom in noms if nom]
    except (AttributeError, OSError):
        return []


def _ecrire_configuration_polices():
    descripteur, chemin = tempfile.mkstemp(prefix="pas-communs-fonts-", suffix=".conf")
    with os.fdopen(descripteur, "w", encoding="utf-8") as sortie:
        sortie.write(CONFIGURATION_POLICES)
    atexit.register(lambda: Path(chemin).unlink(missing_ok=True))
    return chemin


def preparer_pango_embarque():
    """Sous macOS dans un programme gelé dont le bundle contient Pango : retourne True une fois prêt.

    À appeler avant le premier import de WeasyPrint ; sans effet partout ailleurs.
    """
    global _pret
    if _pret:
        return True
    if sys.platform != "darwin" or not getattr(sys, "frozen", False):
        return False
    racine = Path(getattr(sys, "_MEIPASS", "") or ".")
    if not (racine / BIBLIOTHEQUES[0][1]).is_file():
        return False  # PDF natif non embarqué : WeasyPrint échouera avec son propre message.
    import cffi
    reels = dict(BIBLIOTHEQUES)
    original = cffi.FFI.dlopen

    def dlopen(self, name, flags=0):
        if isinstance(name, str) and "/" not in name:
            if name == BIBLIOTHEQUE_IGNOREE:
                raise OSError(f"{name} ignorée : WeasyPrint alloue les polices avec fontTools.")
            reel = reels.get(name, name)
            # Une seule copie par processus : réutiliser l'image qu'un autre composant a déjà chargée.
            chargee = next((c for c in _images_chargees() if os.path.basename(c) == reel), None) if name in reels else None
            candidat = Path(chargee) if chargee else racine / reel
            if chargee or candidat.is_file():
                return original(self, str(candidat), flags)
        return original(self, name, flags)

    cffi.FFI.dlopen = dlopen
    if not os.environ.get("FONTCONFIG_FILE"):
        os.environ["FONTCONFIG_FILE"] = _ecrire_configuration_polices()
    _pret = True
    return True
