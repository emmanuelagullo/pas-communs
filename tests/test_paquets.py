from contextlib import closing
from io import BytesIO
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import stat
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

from pas_communs.paquets import (
    ProfilPaquet, creer_sauvegarde, preparer_restauration,
    iterer_restauration, appliquer_restauration, lire_resultat,
)


class PaquetsTests(unittest.TestCase):
    def setUp(self):
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        self.parent = Path(temporaire.name)
        self.paquet = self.parent / "source"
        self.paquet.mkdir()
        self.profil = ProfilPaquet("application-test", "format-test", "base.sqlite3")
        (self.paquet / "secret-key").write_text("cle-fictive")
        (self.paquet / "media").mkdir()
        (self.paquet / "media/photo.bin").write_bytes(b"media-fictif")
        with closing(sqlite3.connect(self.paquet / self.profil.base)) as db, db:
            db.execute("CREATE TABLE django_migrations (app TEXT, name TEXT)")
            db.execute("INSERT INTO django_migrations VALUES ('neutre', '0001')")
            db.execute("CREATE TABLE exemple (valeur TEXT)")
            db.execute("INSERT INTO exemple VALUES ('fictif')")

    def archive(self, **options):
        archive = BytesIO()
        creer_sauvegarde(self.paquet, archive, profil=self.profil, **options)
        archive.seek(0)
        return archive

    def modifier(self, source, *, manifeste=None, fichier=None):
        cible = BytesIO()
        with ZipFile(source) as entree, ZipFile(cible, "w") as sortie:
            for nom in entree.namelist():
                contenu = entree.read(nom)
                if nom == "manifest.json" and manifeste:
                    valeur = json.loads(contenu)
                    manifeste(valeur)
                    contenu = json.dumps(valeur).encode()
                if fichier and nom == "media/photo.bin":
                    contenu = fichier
                sortie.writestr(nom, contenu)
        cible.seek(0)
        return cible

    def test_aller_retour_et_remplacement_conservent_ancien(self):
        source = self.archive()
        copie = preparer_restauration(source, self.parent, profil=self.profil,
            migrations_connues={("neutre", "0001")})
        (self.paquet / "media/photo.bin").write_bytes(b"nouvelle-saisie")
        ancien = appliquer_restauration(self.paquet, copie)
        self.assertEqual((ancien / "media/photo.bin").read_bytes(), b"nouvelle-saisie")
        self.assertEqual((self.paquet / "media/photo.bin").read_bytes(), b"media-fictif")
        self.assertEqual(lire_resultat(self.paquet)["nombre_medias"], 1)

    def test_mauvais_produit_refuse_avant_toute_ecriture(self):
        autre = ProfilPaquet("autre-application", "format-test", "base.sqlite3", True)
        archive = self.archive()
        with patch("pas_communs.paquets.tempfile.mkdtemp") as creation:
            with self.assertRaisesRegex(ValueError, "autre application"):
                preparer_restauration(archive, self.parent, profil=autre)
            creation.assert_not_called()
        self.assertEqual((self.paquet / "media/photo.bin").read_bytes(), b"media-fictif")

    def test_absence_application_acceptee_uniquement_sur_demande(self):
        source = self.modifier(self.archive(), manifeste=lambda m: m.pop("application"))
        with self.assertRaisesRegex(ValueError, "identité absente"):
            preparer_restauration(source, self.parent, profil=self.profil)
        ancien = ProfilPaquet(self.profil.application, self.profil.format, self.profil.base, True)
        self.assertTrue(preparer_restauration(source, self.parent, profil=ancien).etape.is_dir())

    def test_format_et_version_restent_controles(self):
        for cle, valeur in [("format", "autre-format"), ("version", 999), ("application", None)]:
            with self.subTest(cle=cle):
                source = self.modifier(self.archive(), manifeste=lambda m: m.update({cle: valeur}))
                with self.assertRaises(ValueError):
                    preparer_restauration(source, self.parent, profil=self.profil)
                self.assertFalse(list(self.parent.glob(".restauration-*")))

    def test_empreinte_et_migrations_refusees_sans_modification(self):
        with self.assertRaisesRegex(ValueError, "altéré"):
            preparer_restauration(self.modifier(self.archive(), fichier=b"altere"), self.parent, profil=self.profil)
        with self.assertRaisesRegex(ValueError, "version plus récente"):
            preparer_restauration(self.archive(), self.parent, profil=self.profil, migrations_connues=set())
        self.assertFalse(list(self.parent.glob(".restauration-*")))

    def test_limites_appliquees_avant_extraction(self):
        for limites in [{"taille_max": 1}, {"fichiers_max": 1}]:
            with self.assertRaises(ValueError):
                preparer_restauration(self.archive(), self.parent, profil=self.profil, **limites)
        self.assertFalse(list(self.parent.glob(".restauration-*")))

    def test_interruption_et_erreur_destination_nettoient(self):
        travail = iterer_restauration(self.archive(), self.parent, profil=self.profil)
        self.assertEqual(next(travail)["phase"], "ouvrir")
        travail.close()
        self.assertFalse(list(self.parent.glob(".restauration-*")))
        def refus(_):
            raise OSError("disque fictif plein")
        travail = iterer_restauration(self.archive(), self.parent, profil=self.profil, ouvrir_destination=refus)
        with self.assertRaises(OSError):
            list(travail)
        self.assertFalse(list(self.parent.glob(".restauration-*")))

    def test_media_externe_progressif_et_taille_verifiee(self):
        donnees = b"fictif" * 300000
        source = self.archive(taille_bloc=4096, fichiers_externes={
            "media/externe.bin": (len(donnees), lambda: BytesIO(donnees))})
        copie = preparer_restauration(source, self.parent, profil=self.profil)
        self.assertEqual((copie.etape / "media/externe.bin").read_bytes(), donnees)
        for taille in [len(donnees)-1, len(donnees)+1]:
            with self.assertRaisesRegex(ValueError, "changé"):
                self.archive(fichiers_externes={"media/externe.bin": (taille, lambda: BytesIO(donnees))})

    def test_metadonnees_metier_ne_peuvent_pas_remplacer_identite(self):
        for champ in ["format", "version", "application", "files", "created_at"]:
            with self.assertRaisesRegex(ValueError, "réservées"):
                self.archive(metadonnees={champ: "fictif"})

    def test_export_sans_base_ne_cree_pas_de_base_vide(self):
        (self.paquet / self.profil.base).unlink()
        with self.assertRaises(ValueError):
            self.archive()
        self.assertFalse((self.paquet / self.profil.base).exists())

    def test_chemins_et_liens_dans_archive_refuses(self):
        for nom, lien in [("../echappe", False), ("media/lien", True), ("/absolu", False),
                          ('media/C:/echappe', False), ('media/D:echappe', False),
                          ('media/photo:flux', False), ('media/CON.txt', False),
                          ('media/photo.', False), ('media/photo ', False)]:
            source = BytesIO()
            with ZipFile(source, "w") as z:
                entrees = {"base.sqlite3": b"base", "secret-key": b"cle", nom: b"fictif"}
                for path, contenu in entrees.items():
                    info = ZipInfo(path)
                    if path == nom and lien:
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    z.writestr(info, contenu)
                z.writestr("manifest.json", json.dumps({"format": "format-test", "version": 1,
                    "application": "application-test", "files": {p: hashlib.sha256(b).hexdigest() for p,b in entrees.items()}}))
            with self.assertRaises(ValueError):
                preparer_restauration(source, self.parent, profil=self.profil)
            self.assertFalse(list(self.parent.glob(".restauration-*")))
            self.assertFalse((self.parent / "echappe").exists())

    def test_collisions_refusees_avant_creation_de_preparation(self):
        source = self.archive()
        cible = BytesIO()
        with ZipFile(source) as z, ZipFile(cible, 'w') as out:
            for nom in z.namelist():
                contenu = z.read(nom)
                if nom == 'manifest.json':
                    m = json.loads(contenu)
                    m['files']['media/PHOTO.bin'] = hashlib.sha256(b'autre').hexdigest()
                    contenu = json.dumps(m).encode()
                out.writestr(nom, contenu)
            out.writestr('media/PHOTO.bin', b'autre')
        cible.seek(0)
        with patch('pas_communs.paquets.tempfile.mkdtemp') as creer:
            with self.assertRaises(ValueError):
                preparer_restauration(cible, self.parent, profil=self.profil)
            creer.assert_not_called()

    def test_export_refuse_un_nom_que_import_refuserait(self):
        for nom in ('media/C:/a', 'media/a:flux', 'media/CON.txt', 'media/photo.bin'):
            sortie = BytesIO()
            with self.subTest(nom=nom), self.assertRaises(ValueError):
                creer_sauvegarde(self.paquet, sortie, profil=self.profil,
                    fichiers_externes={nom: (1, lambda: BytesIO(b'x'))})
            self.assertEqual(sortie.getvalue(), b'')

    @unittest.skipIf(__import__('os').name == 'nt', 'Noms non portables impossibles à créer sous Windows')
    def test_export_natif_refuse_collision_et_conserve_destination(self):
        (self.paquet/'media/PHOTO.bin').write_bytes(b'autre')
        destination = self.parent/'sauvegarde.zip'
        destination.write_bytes(b'ancienne copie')
        with self.assertRaises(ValueError):
            creer_sauvegarde(self.paquet, destination, profil=self.profil)
        self.assertEqual(destination.read_bytes(), b'ancienne copie')

    def test_echec_activation_retablit_paquet_source(self):
        preparation = preparer_restauration(self.archive(), self.parent, profil=self.profil)
        original = Path.rename
        def renommer(chemin, cible):
            if chemin == preparation.etape:
                raise OSError("échec fictif")
            return original(chemin, cible)
        with patch.object(Path, "rename", renommer):
            with self.assertRaises(OSError):
                appliquer_restauration(self.paquet, preparation)
        self.assertTrue((self.paquet / self.profil.base).is_file())
        self.assertFalse(preparation.ancien.exists())


if __name__ == "__main__":
    unittest.main()
