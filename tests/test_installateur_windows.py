"""Contrat du wheel installé ; Inno Setup est exercé dans les CI des produits."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pas_communs import installateur_windows as w


class InstallateurTests(unittest.TestCase):
    def fixture(self, root, programme='PetitsPas'):
        c={'programme':programme,'nom':'Petits Pas','app_id':'PetitsPas.Local.EmmanuelAgullo',
           'url':'https://petits-pas.gitlabpages.inria.fr/petits-pas/',
           'donnees':r'petits-pas\paquet-autonome'}
        f=root/'produit.json';f.write_text(json.dumps(c),encoding='utf-8')
        source=root/'dist'/programme;source.mkdir(parents=True)
        (source/(programme+'.exe')).write_bytes(b'programme fictif')
        return f,c

    def test_identite_historique_et_conservation_des_donnees(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f,c=self.fixture(root)
            script,setup=w.preparer(f,root,'dev.1234abcd')
            texte=script.read_text(encoding='utf-8-sig')
            self.assertIn('AppId=PetitsPas.Local.EmmanuelAgullo',texte)
            self.assertIn(r'DefaultDirName={localappdata}\Programs\PetitsPas\app',texte)
            self.assertIn('PrivilegesRequired=lowest',texte)
            self.assertIn('WizardSilent',texte)
            self.assertNotIn('[UninstallDelete]',texte.split('[Languages]')[1])
            self.assertNotIn('@@',texte)
            self.assertEqual(setup.name,'PetitsPas-Setup-dev.1234abcd-x64.exe')
            self.assertTrue((w.RESSOURCES/'verifier-windows.ps1').is_file())
            c['nom']="Pas d'essai";f.write_text(json.dumps(c),encoding='utf-8')
            script,_=w.preparer(f,root,'0.2.0')
            self.assertIn("'Fermez Pas d''essai avant de continuer.'",script.read_text(encoding='utf-8-sig'))

    def test_identites_propres_aux_deux_produits(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f,c=self.fixture(root,'PasAPasAccompagnement')
            c.update(nom='Pas à Pas - Accompagnement',app_id='PasAPasAccompagnement.Local',
                     donnees=r'pas-a-pas-accompagnement\paquet-autonome')
            f.write_text(json.dumps(c),encoding='utf-8')
            script,_=w.preparer(f,root,'0.2.0')
            texte=script.read_text(encoding='utf-8-sig')
            self.assertIn('AppId=PasAPasAccompagnement.Local',texte)
            self.assertNotIn('PetitsPas',texte)

    def test_configuration_et_version_non_interpretables(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f,c=self.fixture(root)
            for cle,valeur in [('donnees',r'Programs\PetitsPas'),('donnees',r'C:\prive'),
                               ('donnees',r'..\prive'),('app_id','Nom\n[Code]'),('nom','{app}')]:
                with self.subTest(cle=cle,valeur=valeur):
                    f.write_text(json.dumps({**c,cle:valeur}),encoding='utf-8')
                    with self.assertRaises(ValueError):w.configuration(f)
            f.write_text(json.dumps(c),encoding='utf-8')
            with self.assertRaises(ValueError):w.preparer(f,root,'0.2.0"\n[Code]')

    def test_compilation_et_verification_attendent_les_processus(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f,c=self.fixture(root);setup=root/'dist/PetitsPas-Setup-0.2.0-x64.exe'
            def compiler(cmd,**kw):
                if cmd[0]=='ISCC.exe':setup.write_bytes(b'setup fictif')
            with patch.object(w.sys,'platform','win32'),patch.object(w.subprocess,'run',side_effect=compiler) as run:
                self.assertEqual(w.construire(f,root,'0.2.0','ISCC.exe',True),setup)
                self.assertEqual(len(run.call_args_list),2)
                self.assertTrue(all(a.kwargs['check'] for a in run.call_args_list))
                self.assertIn('-File',run.call_args_list[1].args[0])
