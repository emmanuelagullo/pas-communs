import json
from pathlib import Path
import tempfile
import unittest
from pas_communs import publication as p

SHA='a'*40


class PublicationTests(unittest.TestCase):
    def test_identite_independante_de_la_forge_et_sans_git_en_ci(self):
        def interdit():raise AssertionError('git appelé malgré un commit CI')
        self.assertEqual(p.identite({'GITHUB_SHA':SHA},interdit)['application_version'],'dev.aaaaaaaa')
        self.assertEqual(p.identite({'CI_COMMIT_SHA':SHA,'CI_COMMIT_TAG':'0.5.0'},interdit)['tag'],'0.5.0')
        with self.assertRaises(ValueError):p.identite({'CI_COMMIT_SHA':SHA,'CI_COMMIT_TAG':'main'})

    def test_format_produit_commit_cible_et_fichier_altere_refuses(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f=root/'programme.zip';f.write_bytes(b'fictif')
            r=p.manifeste('produit-a',p.identite({'GITHUB_SHA':SHA}),'programme','linux',[f],{})
            self.assertEqual(p.verifier(r,root,format='produit-a',commit=SHA),{'programme.zip'})
            for kwargs in [{'format':'produit-b'},{'format':'produit-a','commit':'b'*40},{'format':'produit-a','target':'windows'}]:
                with self.assertRaises(ValueError):p.verifier(r,root,**kwargs)
            r['files'][0]['name']='../programme.zip'
            with self.assertRaises(ValueError):p.verifier(r,root,format='produit-a')
            r['files'][0]['name']='programme.zip';f.write_bytes(b'altere')
            with self.assertRaises(ValueError):p.verifier(r,root,format='produit-a')

    def test_doublons_et_lien_symbolique_refuses(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f=root/'programme.zip';f.write_bytes(b'fictif')
            with self.assertRaises(ValueError):p.manifeste('a',{},'programme','linux',[f,f])
            lien=root/'lien.zip'
            try:lien.symlink_to(f)
            except OSError:return
            with self.assertRaises(ValueError):p.decrire(lien)

    def test_bundle_normal_requis_et_aucun_fichier_supplementaire(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f=root/'worker.js';f.write_bytes(b'fictif')
            c={'testMode':False,'application':'fictif','version':'test.0123',
               'assets':[{'url':'/worker.js','sha256':p.sha256(f)}]}
            def ecrire(): (root/'config.json').write_text(json.dumps(c))
            def verifier():return p.verifier_bundle(root,version=r'test\.[0-9]{4}',requis={'worker.js'},application='fictif')
            ecrire();verifier()
            for mode in [True,None]:
                c['testMode']=mode;ecrire()
                with self.assertRaises(ValueError):verifier()
            c['testMode']=False;ecrire();(root/'secret-key').write_bytes(b'fictif')
            with self.assertRaises(ValueError):verifier()
            (root/'secret-key').unlink();f.write_bytes(b'altere')
            with self.assertRaises(ValueError):verifier()
