"""Primitives TOTP extraites de Petits Pas ; aucun modèle ni secret global.

cryptography, qrcode et django-otp restent importés au moment de l’usage.
Le stockage atomique du dernier pas, les limites de tentatives et les sessions
restent obligatoires dans le produit appelant.
"""
import base64
import hashlib
import secrets
from io import BytesIO
from urllib.parse import quote

PAS = 30
CHIFFRES = 6
TOLERANCE = 1
OCTETS_CLE = 20


def _fernet(cles):
    from cryptography.fernet import Fernet, MultiFernet

    return MultiFernet([Fernet(cle) for cle in cles])


def chiffrer(cle, *, cles):
    return _fernet(cles).encrypt(cle).decode()


def dechiffrer(jeton, *, cles):
    return _fernet(cles).decrypt(jeton.encode())


def cle_en_base32(cle):
    return base64.b32encode(cle).decode().rstrip("=")


def uri_otpauth(nom_utilisateur, cle, *, emetteur):
    libelle = quote(f"{emetteur}:{nom_utilisateur}")
    return (
        f"otpauth://totp/{libelle}?secret={cle_en_base32(cle)}"
        f"&issuer={quote(emetteur)}&algorithm=SHA1&digits={CHIFFRES}&period={PAS}"
    )


def qr_svg(uri):
    """QR code en SVG, sans Pillow ; la déclaration XML est retirée pour
    pouvoir l'inclure directement dans une page HTML."""
    import qrcode
    import qrcode.image.svg

    image = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage, box_size=10)
    sortie = BytesIO()
    image.save(sortie)
    svg = sortie.getvalue().decode()
    return svg[svg.index("<svg"):]


def _normaliser(code):
    chiffres = "".join(str(code).split())
    if len(chiffres) != CHIFFRES or not chiffres.isascii() or not chiffres.isdigit():
        return None
    return int(chiffres)


ALPHABET_SECOURS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LONGUEUR_CODE_SECOURS = 16
NOMBRE_CODES_SECOURS = 10


def empreinte_code_secours(code_normalise):
    return hashlib.sha256(code_normalise.encode()).hexdigest()


def normaliser_code_secours(saisie):
    """Majuscules, sans espaces ni tirets ; None si la forme est impossible."""
    code = "".join(c for c in str(saisie or "").upper() if c not in " -")
    if len(code) != LONGUEUR_CODE_SECOURS or any(c not in ALPHABET_SECOURS for c in code):
        return None
    return code


def presenter_code_secours(code):
    return "-".join(code[i:i + 4] for i in range(0, LONGUEUR_CODE_SECOURS, 4))


def nouveau_code_secours():
    return "".join(secrets.choice(ALPHABET_SECOURS) for _ in range(LONGUEUR_CODE_SECOURS))


def verifier_pas(cle, code, *, dernier_pas, instant=None):
    """Retourne le pas accepté ou None ; l’appelant doit le persister atomiquement.

    Cette fonction ne consomme aucun code et ne limite pas les tentatives.
    Ne jamais l’exposer directement comme une authentification complète.
    """
    from django_otp.oath import TOTP
    jeton = _normaliser(code)
    if jeton is None:
        return None
    totp = TOTP(cle, step=PAS, digits=CHIFFRES)
    if instant is not None:
        totp.time = instant
    if not totp.verify(jeton, tolerance=TOLERANCE, min_t=dernier_pas + 1):
        return None
    return totp.t()
