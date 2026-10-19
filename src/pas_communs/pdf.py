"""Rendus PDF sans modèles ni droits ; dépendances chargées à l'utilisation."""
import mimetypes
from importlib.resources import files
from urllib.parse import quote, unquote


def url_media(nom, *, schema):
    return schema + quote(nom, safe='')


def recuperateur_medias(noms, *, schema, ouvrir, defaut=None):
    """Liste explicite de médias autorisés ; politique des autres URL fournie."""
    if defaut is None:
        from weasyprint import default_url_fetcher
        defaut = default_url_fetcher
    autorises = frozenset(noms)

    def recuperer(url):
        if not url.startswith(schema):
            return defaut(url)
        nom = unquote(url[len(schema):])
        if nom not in autorises:
            raise ValueError('Média non autorisé dans ce document.')
        return {'file_obj': ouvrir(nom, 'rb'), 'mime_type': mimetypes.guess_type(nom)[0],
                'redirected_url': url}
    return recuperer


def rendre_html(html, *, base_url, feuille_style, recuperer):
    """Même rendu WeasyPrint que les carnets historiques, sans interpréter le métier."""
    from weasyprint import CSS, HTML
    return HTML(string=html, base_url=base_url, media_type='print',
                url_fetcher=recuperer).write_pdf(stylesheets=[CSS(filename=feuille_style)])


def fiche_texte(titre, lignes):
    """PDF texte paginé autonome, utilisable aussi dans Pyodide ; aucun HTML/URL.

    Backend facultatif fpdf2 + FontTools/Pillow. Ne remplace pas un carnet avec
    images. Le contenu, l'ordre et les autorisations viennent du produit.
    """
    lignes = tuple(lignes)
    from fpdf import FPDF
    from fontTools.ttLib import TTFont
    police = files('pas_communs').joinpath('polices/DejaVuSans.ttf')
    with police.open('rb') as f:
        font = TTFont(f)
        cmap = font.getBestCmap()
        for text in [titre, *lignes]:
            if any(ord(c) not in cmap for c in text if c not in '\n\t\r'):
                raise ValueError('Un caractère ne peut pas être rendu avec la police disponible.')
        font.close()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font('Document', fname=str(police))
    pdf.set_title(titre)
    pdf.add_page()
    pdf.set_font('Document', size=16)
    pdf.multi_cell(0, 9, titre, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)
    pdf.set_font('Document', size=11)
    for ligne in lignes:
        # Aucun remplacement implicite de caractère ni interprétation de balise.
        pdf.multi_cell(0, 7, ligne.replace('\t', '    '), new_x='LMARGIN', new_y='NEXT')
        pdf.ln(2)
    return bytes(pdf.output())
