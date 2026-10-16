from importlib.resources import files
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from pas_communs.navigateur import RESSOURCES,copier_ressources
from pas_communs.navigateur.http import environnement,retenir_cookies


class NavigateurTests(unittest.TestCase):
    def test_ressources_du_wheel_copiees_sans_transformation(self):
        with tempfile.TemporaryDirectory() as temp:
            copier_ressources(temp)
            self.assertEqual(set(p.name for p in Path(temp).iterdir()),set(RESSOURCES))
            for nom in RESSOURCES:self.assertEqual((Path(temp)/nom).read_bytes(),files('pas_communs.navigateur').joinpath(nom).read_bytes())

    def test_http_conserve_csrf_corps_et_prefixe_sans_cookie_client(self):
        requete={'url':'https://fictif.example/chrs/app/personnes/?page=2','method':'POST','headers':[
            ['Cookie','autre=interdit'],['Host','faux'],['Content-Length','999'],['Content-Type','application/x-www-form-urlencoded'],
            ['Origin','https://fictif.example'],['Referer','https://fictif.example/chrs/app/']]}
        e=environnement(requete,'/chrs/app',{'session':'virtuelle'},BytesIO(b'x=1'),3,origine='https://fictif.example')
        self.assertEqual(e['SCRIPT_NAME'],'/chrs/app');self.assertEqual(e['PATH_INFO'],'/personnes/')
        self.assertEqual(e['CONTENT_LENGTH'],'3');self.assertEqual(e['HTTP_HOST'],'fictif.example')
        self.assertEqual(e['HTTP_COOKIE'],'session=virtuelle');self.assertEqual(e['wsgi.input'].read(),b'x=1')
        self.assertEqual(e['HTTP_ORIGIN'],'https://fictif.example')
        for url in ['https://etranger.example/chrs/app/','https://fictif.example/autre/']:
            with self.assertRaises(ValueError):environnement({**requete,'url':url},'/chrs/app',{},BytesIO(),0,origine='https://fictif.example')

    def test_cookies_virtuels_pas_exposes_aux_entetes_navigateur(self):
        cookies={}
        self.assertEqual(retenir_cookies([['Set-Cookie','session=interne; HttpOnly; Secure'],['Content-Type','text/html']],cookies),[['Content-Type','text/html']])
        self.assertEqual(cookies,{'session':'interne'})
        retenir_cookies([['Set-Cookie','session=""; Max-Age=0']],cookies);self.assertEqual(cookies,{})
