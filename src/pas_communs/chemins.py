"""Noms portables des archives privées et publiques, indépendants du système."""
import re

_RESERVE = re.compile(r"(?:CON|PRN|AUX|NUL|CLOCK\$|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])\Z", re.I)


def composants_portables(nom):
    """Refuser les alias Windows et traversées, sans renommer de donnée."""
    if not isinstance(nom, str) or not nom:
        raise ValueError("Chemin vide ou non textuel dans l'archive.")
    elements = nom.split('/')
    for element in elements:
        if (not element or element in {'.', '..'} or element.endswith((' ', '.'))
                or any(ord(c) < 32 or c in '<>:"\\|?*' for c in element)
                or _RESERVE.fullmatch(element.split('.')[0].rstrip(' '))):
            raise ValueError("Chemin non portable dans l'archive : " + nom)
    return tuple(elements)


def verifier_arbre(noms):
    """Détecter aussi les alias de répertoires et conflits fichier/répertoire."""
    racine = {}
    for nom in noms:
        elements = composants_portables(nom)
        niveau = racine
        for index, element in enumerate(elements):
            # Arbre plutôt que tous les préfixes copiés : coût linéaire en
            # composants, même avec un chemin d'archive anormalement profond.
            cle = element.casefold()
            noeud = niveau.setdefault(cle, {'nom': element, 'fichier': False, 'enfants': {}})
            if noeud['nom'] != element:
                raise ValueError("Collision de casse dans l'archive : " + nom)
            if noeud['fichier']:
                raise ValueError("Chemin répété ou conflit fichier/répertoire : " + nom)
            if index == len(elements) - 1:
                if noeud['enfants']:
                    raise ValueError("Conflit fichier/répertoire dans l'archive : " + nom)
                noeud['fichier'] = True
            niveau = noeud['enfants']
