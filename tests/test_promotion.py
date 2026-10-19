from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from pas_communs import promotion as p


class PromotionTests(unittest.TestCase):
    def run_info(self):
        return {'id': 12, 'head_repository': {'full_name': 'fictif/produit'},
            'conclusion': 'success', 'status': 'completed', 'path': 'build.yml',
            'head_branch': '0.8.0', 'head_sha': 'a'*40, 'event': 'push'}

    def test_selection_et_refus_de_toutes_les_origines_etrangeres(self):
        kw = {'depot': 'fictif/produit', 'workflow': 'build.yml'}
        e = {'action': 'completed', 'workflow_run': self.run_info()}
        self.assertEqual(p.selectionner_evenement(e, 'workflow_run', 'refs/heads/main', **kw), ('12', '0.8.0'))
        for champ, valeur in [('conclusion', 'failure'), ('event', 'pull_request'),
                ('status', 'in_progress'), ('head_repository', {'full_name': 'fictif/fork'}),
                ('head_branch', 'main'), ('path', 'autre.yml')]:
            mauvais = {**e, 'workflow_run': {**self.run_info(), champ: valeur}}
            self.assertIsNone(p.selectionner_evenement(mauvais, 'workflow_run', '', **kw))
        with self.assertRaises(ValueError):
            p.selectionner_evenement({'inputs': {'run': '1', 'tag': '0.8.0'}},
                'workflow_dispatch', 'refs/heads/autre', **kw)

    def test_tags_annotations_et_divergences(self):
        p.verifier_tag_distant('b'*40+'\trefs/tags/0.8.0\n'+'a'*40+'\trefs/tags/0.8.0^{}\n', '0.8.0', 'a'*40)
        for lignes in ('', 'b'*40+'\trefs/tags/0.8.0\n'):
            with self.assertRaises(ValueError):
                p.verifier_tag_distant(lignes, '0.8.0', 'a'*40)

    def test_extraction_refuse_alias_et_conserve_fichier_existant(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for nom in ('../a', 'C:a', 'a:flux', 'CON.txt', 'a.', 'a/b'):
                source = BytesIO()
                with ZipFile(source, 'w') as z:
                    z.writestr(nom, b'fictif')
                source.seek(0)
                with self.assertRaises(ValueError):
                    p.extraire_artefact(source, root)
                self.assertEqual(list(root.iterdir()), [])
