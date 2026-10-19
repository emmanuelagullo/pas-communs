import io
import sys
import unittest
from unittest.mock import Mock, patch
from pas_communs.pdf import recuperateur_medias, rendre_html, fiche_texte, url_media


class PdfTests(unittest.TestCase):
    def test_import_sans_moteur_natif(self):
        import subprocess
        subprocess.run([sys.executable,'-c',"import sys; import pas_communs.pdf; assert 'weasyprint' not in sys.modules and 'fpdf' not in sys.modules"],check=True)

    def test_medias_explicitement_autorises(self):
        ouvrir=Mock(return_value=io.BytesIO(b'fictif'));defaut=Mock(return_value={'string':b'public'})
        f=recuperateur_medias(['photo été.jpg'],schema='test-media:',ouvrir=ouvrir,defaut=defaut)
        self.assertEqual(f(url_media('photo été.jpg',schema='test-media:'))['mime_type'],'image/jpeg')
        ouvrir.assert_called_once_with('photo été.jpg','rb')
        with self.assertRaises(ValueError):f('test-media:autre.jpg')
        self.assertEqual(f('https://public.invalid/')['string'],b'public')
        defaut.assert_called_once_with('https://public.invalid/')

    def test_contrat_rendu_historique(self):
        faux=Mock();faux.HTML.return_value.write_pdf.return_value=b'%PDF-fictif'
        fetch=Mock()
        with patch.dict(sys.modules,{'weasyprint':faux}):
            self.assertEqual(rendre_html('<h1>Fictif</h1>',base_url='base',feuille_style='style.css',recuperer=fetch),b'%PDF-fictif')
        faux.HTML.assert_called_once_with(string='<h1>Fictif</h1>',base_url='base',media_type='print',url_fetcher=fetch)
        faux.CSS.assert_called_once_with(filename='style.css')

    def test_pdf_texte_unicode_et_pagination(self):
        from pypdf import PdfReader
        data=fiche_texte('Fiche fictive', ['Élodie — Αλέξανδρος — Мария', *['Ligne fictive '+str(i) for i in range(100)]])
        r=PdfReader(io.BytesIO(data))
        self.assertGreater(len(r.pages),1)
        texte=''.join(p.extract_text() for p in r.pages)
        self.assertIn('Élodie — Αλέξανδρος — Мария',texte)
        self.assertIn('Ligne fictive 99',texte)
        with self.assertRaises(ValueError):fiche_texte('Fictif',['\x00'])
