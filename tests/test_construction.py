from pathlib import Path
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from pas_communs import construction


class ConstructionTests(unittest.TestCase):
    def test_windows_sans_pdf_ne_demande_pas_pango_et_collecte_ressources(self):
        with tempfile.TemporaryDirectory() as t:
            racine = Path(t)
            (racine / "scripts").mkdir()
            (racine / "scripts/lancer-local.py").write_text("# lanceur fictif")
            hooks = ModuleType("PyInstaller.utils.hooks")
            hooks.collect_data_files = lambda p, **kw: [(p, "ressources-fictives")]
            hooks.collect_submodules = lambda p, **kw: [p + ".module_fictif"]
            modules = {n: ModuleType(n) for n in ["PyInstaller", "PyInstaller.utils"]}
            modules[hooks.__name__] = hooks
            appels = []
            def analyser(entrees, **options):
                self.assertEqual(entrees, [str(racine / "scripts/lancer-local.py")])
                self.assertEqual(options["binaries"], [])
                self.assertIn("pas_communs.module_fictif", options["hiddenimports"])
                self.assertIn(("webview", "ressources-fictives"), options["datas"])
                self.assertIn((str(racine / "templates"), "templates"), options["datas"])
                return SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])
            espace = {"Analysis": analyser, "PYZ": lambda _: None,
                "EXE": lambda *args, **kw: appels.append(kw), "COLLECT": lambda *args, **kw: kw["name"]}
            with patch.dict("sys.modules", modules), patch.object(construction, "os", SimpleNamespace(name="nt", environ={} )):
                nom = construction.assembler(racine, espace, nom="ApplicationFictive",
                    settings="fictif.settings", ressources=[("templates", "templates")], paquets=["fictif"])
            self.assertEqual(nom, "ApplicationFictive")
            self.assertFalse(appels[0]["console"])
