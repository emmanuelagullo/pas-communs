"""Identification des systèmes pris en charge par les programmes de bureau."""
import sys

# Seule architecture livrée pour macOS : Apple Silicon. Intel n'est pas qualifié.
ARCHITECTURE_MACOS = "arm64"


def systeme(plateforme=None, *, strict=False):
    """Retourner « windows », « macos » ou « linux ».

    Sans argument, la plateforme courante (sys.platform) est employée. Les
    valeurs historiques de os.name (« nt », « posix ») restent acceptées :
    « posix » désigne Linux, comme avant l'ajout de macOS. Un système inconnu
    est traité comme Linux pour les emplacements de données, et refusé si
    strict est vrai, pour ne jamais construire un programme sans contrat.
    """
    brute = (sys.platform if plateforme is None else plateforme).lower()
    if brute in {"nt", "windows"} or brute.startswith("win"):
        return "windows"
    if brute in {"darwin", "macos"}:
        return "macos"
    if brute in {"posix", "linux"} or brute.startswith("linux"):
        return "linux"
    if strict:
        raise ValueError("Système non pris en charge : " + brute)
    return "linux"
