import hashlib
import io
from pathlib import Path
import ssl
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
from pas_communs import construction_pwa as moteur


class Reponse(io.BytesIO):
    headers={"Content-Length":"6"}


class ConstructionPwaTests(unittest.TestCase):
    def test_contrat_runtime_unique_et_selection_explicite(self):
        runtime = moteur.RUNTIME_314_0_7
        bon = {'info': {'python': runtime.python, 'abi_version': runtime.abi}}
        moteur.verifier_runtime(bon, runtime=runtime)
        moteur.verifier_runtime(bon, runtime.version)
        with self.assertRaises(ValueError):
            moteur.verifier_runtime(bon, 'autre-version')
        autre = moteur.RuntimePyodide('fictif', '9.9', 'fictive')
        with self.assertRaises(ValueError):
            moteur.verifier_runtime(bon, runtime=autre)
        moteur.verifier_runtime({'info': {'python': '9.9', 'abi_version': 'fictive'}}, runtime=autre)
        self.assertIn('/vfictif/full/', autre.base)

    def test_reprise_et_cache_valide_sans_nouveau_reseau(self):
        with tempfile.TemporaryDirectory() as temp:
            cible=Path(temp)/'runtime'
            with patch.object(moteur.urllib.request,'urlopen',side_effect=[urllib.error.URLError('interruption'),Reponse(b'complet')]) as reseau,patch.object(moteur.time,'sleep'):
                # Taille cohérente avec le contenu, puis réemploi du cache SHA.
                Reponse.headers={"Content-Length":"7"}
                h=hashlib.sha256(b'complet').hexdigest()
                moteur.telecharger('https://fictif.invalid/runtime',cible,h)
                moteur.telecharger('https://fictif.invalid/runtime',cible,h)
                self.assertEqual(reseau.call_count,2)
            self.assertEqual(cible.read_bytes(),b'complet')
            self.assertFalse(list(Path(temp).glob('*.part')))

    def test_certificat_invalide_ne_declenche_pas_de_contournement(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(moteur.urllib.request,'urlopen',side_effect=urllib.error.URLError(ssl.SSLCertVerificationError('certificat'))),patch.object(moteur.time,'sleep') as attente:
            with self.assertRaises(urllib.error.URLError):moteur.telecharger('https://fictif.invalid',Path(temp)/'runtime')
            attente.assert_not_called()
