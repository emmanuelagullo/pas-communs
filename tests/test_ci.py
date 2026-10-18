from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pas_communs.ci import verifier_django


class CiTests(unittest.TestCase):
    def test_settings_reservees_aux_tests_et_pas_de_pip_implicite(self):
        with tempfile.TemporaryDirectory() as t,patch('pas_communs.ci.subprocess.run') as run:
            root=Path(t);(root/'manage.py').touch();(root/'controle.py').touch()
            verifier_django(root,settings_tests='fictif.settings_tests',controles=['controle.py'],timing=True)
            commandes=[appel.args[0][1:] for appel in run.call_args_list]
            self.assertEqual(commandes[0],['manage.py','check'])
            self.assertFalse(any('--settings=' in v for c in commandes[:2] for v in c))
            self.assertIn('--settings=fictif.settings_tests',commandes[2])
            self.assertEqual(commandes[-1],[str((root/'controle.py').resolve())])
            self.assertFalse(any('pip' in c for c in commandes))

    def test_echec_interrompt_avant_tests_et_controles(self):
        with tempfile.TemporaryDirectory() as t,patch('pas_communs.ci.subprocess.run',
                side_effect=subprocess.CalledProcessError(1,'check')) as run:
            (Path(t)/'manage.py').touch()
            with self.assertRaises(subprocess.CalledProcessError):verifier_django(t,pip_check=True)
            self.assertEqual(run.call_count,1)

    def test_controle_exterieur_refuse_avant_toute_commande(self):
        with tempfile.TemporaryDirectory() as t,patch('pas_communs.ci.subprocess.run') as run:
            root=Path(t);(root/'manage.py').touch()
            with self.assertRaises(ValueError):verifier_django(root,controles=['../exterieur.py'])
            run.assert_not_called()

    def test_migration_et_pip_sont_des_choix_explicites(self):
        with tempfile.TemporaryDirectory() as t,patch('pas_communs.ci.subprocess.run') as run:
            (Path(t)/'manage.py').touch()
            verifier_django(t,migrer=True,pip_check=True)
            commandes=[a.args[0][1:] for a in run.call_args_list]
            self.assertIn(['manage.py','migrate','--noinput'],commandes)
            self.assertEqual(commandes[-1],['-m','pip','check'])
