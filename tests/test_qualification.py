from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from pas_communs.qualification import provenance_wheel, verifier_adoption


class QualificationTests(unittest.TestCase):
    def test_code_ressource_ou_adoption_divergente_refusee(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module = root/'module'
            module.mkdir()
            fichiers = {'__init__.py': b'# fictif', 'ressource.mjs': b'export const x=1;'}
            for nom, b in fichiers.items():
                (module/nom).write_bytes(b)
            wheel = root/'pas_communs-fictif-py3-none-any.whl'
            with ZipFile(wheel, 'w') as z:
                for nom, b in fichiers.items():
                    z.writestr('pas_communs/'+nom, b)
            provenance = provenance_wheel(wheel, racine=module)
            self.assertTrue(provenance['octets_importes_identiques'])
            requirement = root/'requirements-communs.txt'
            requirement.write_text('pas-communs @ https://fictif.invalid/'+wheel.name+'#sha256='+provenance['sha256']+'\n')
            verifier_adoption(root, provenance)
            requirement.write_text(requirement.read_text().replace(provenance['sha256'], 'a'*64))
            with self.assertRaises(ValueError):
                verifier_adoption(root, provenance)
            (module/'ressource.mjs').write_bytes(b'altere')
            with self.assertRaises(ValueError):
                provenance_wheel(wheel, racine=module)
            (module/'ressource.mjs').write_bytes(fichiers['ressource.mjs'])
            (module/'module_inattendu.py').write_bytes(b'# ancien')
            with self.assertRaises(ValueError):
                provenance_wheel(wheel, racine=module)
