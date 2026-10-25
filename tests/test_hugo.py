"""Thème Hugo partagé : site d'essai construit avec Hugo, puis contrôlé sans réseau."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

RACINE = Path(__file__).resolve().parents[1]
SITE = Path(__file__).with_name("site_exemple")
HUGO = shutil.which("hugo")


@unittest.skipUnless(HUGO or os.environ.get("PAS_COMMUNS_HUGO_OBLIGATOIRE"), "Hugo Extended absent")
class ThemeHugoTests(unittest.TestCase):
    def construire(self, destination, base_url, *, source=SITE):
        return subprocess.run([HUGO or "hugo", "--source", str(source), "--destination", str(destination),
            "--baseURL", base_url, "--panicOnWarning", "--minify"], capture_output=True, text=True, timeout=120)

    def test_site_d_essai_a_la_racine_et_sous_un_prefixe(self):
        for base in ("https://example.invalid/", "https://example.invalid/produit/"):
            with self.subTest(base=base), tempfile.TemporaryDirectory() as sortie:
                resultat = self.construire(sortie, base)
                self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
                verification = subprocess.run([sys.executable, str(RACINE / "hugo/verifier-site.py"),
                    "--sortie", sortie, "--base-url", base], capture_output=True, text=True)
                self.assertEqual(verification.returncode, 0, verification.stdout + verification.stderr)

    def test_aide_installation_ordre_et_contenu(self):
        with tempfile.TemporaryDirectory() as sortie:
            self.assertEqual(self.construire(sortie, "https://example.invalid/produit/").returncode, 0)
            page = (Path(sortie) / "telechargements/index.html").read_text(encoding="utf-8")
            positions = [page.index('id=installation-' + s) if 'id=installation-' + s in page
                else page.index('id="installation-' + s + '"') for s in ("windows", "macos", "linux")]
            self.assertEqual(positions, sorted(positions), "Ordre attendu : Windows, macOS, Linux.")
            for attendu in ("Exécuter quand même", "Ouvrir quand même", "produit-essai", "WebView2",
                            "gir1.2-webkit2-4.1", "Mac à puce Apple"):
                self.assertIn(attendu, page)
            self.assertIn("macOS 15 ou plus récent est nécessaire", page)  # défaut mesuré
            seul = (Path(sortie) / "windows/index.html").read_text(encoding="utf-8")
            self.assertIn("installation-windows", seul)
            self.assertNotIn("Ouvrir quand même", seul)
            self.assertNotIn("gir1.2-webkit2-4.1", seul)

    def test_version_minimale_de_macos_modifiable(self):
        with tempfile.TemporaryDirectory() as t:
            copie = Path(t) / "site"
            shutil.copytree(SITE, copie)
            (copie / "hugo.toml").write_text((SITE / "hugo.toml").read_text(encoding="utf-8")
                .replace('themesDir = "../../hugo"', 'themesDir = "' + (RACINE / "hugo").as_posix() + '"'), encoding="utf-8")
            (copie / "content/telechargements.md").write_text(
                "---\ntitle: Essai\n---\n\n{{< aide-installation nom=\"X\" dossier=\"x\" macos_min=\"16\" >}}\n", encoding="utf-8")
            self.assertEqual(self.construire(Path(t) / "public", "https://example.invalid/", source=copie).returncode, 0)
            page = (Path(t) / "public/telechargements/index.html").read_text(encoding="utf-8")
            self.assertIn("macOS 16 ou plus récent est nécessaire", page)

    def test_parametres_requis_et_systeme_inconnu_refuses(self):
        with tempfile.TemporaryDirectory() as t:
            copie = Path(t) / "site"
            shutil.copytree(SITE, copie)
            (copie / "hugo.toml").write_text((SITE / "hugo.toml").read_text(encoding="utf-8")
                .replace('themesDir = "../../hugo"', 'themesDir = "' + (RACINE / "hugo").as_posix() + '"'), encoding="utf-8")
            page = copie / "content/telechargements.md"
            for remplacement in ('{{< aide-installation dossier="x" >}}', '{{< aide-installation nom="X" >}}',
                                 '{{< aide-installation nom="X" dossier="x" systeme="beos" >}}'):
                with self.subTest(remplacement=remplacement):
                    page.write_text("---\ntitle: Essai\n---\n\n" + remplacement + "\n", encoding="utf-8")
                    resultat = self.construire(Path(t) / "public", "https://example.invalid/", source=copie)
                    self.assertNotEqual(resultat.returncode, 0)
                    self.assertIn("aide-installation", resultat.stdout + resultat.stderr)
