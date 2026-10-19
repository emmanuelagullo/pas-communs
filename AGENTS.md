# Consignes

Lire README.md, CONTRATS.md, PAQUETS.md, LOCAL.md, AUTHENTIFICATION.md, PUBLICATION.md et JALONS.md.
Ne jamais importer les modèles métier dans le futur socle. Préserver les données,
formats et migrations historiques de Petits Pas. Exemples fictifs uniquement.
Construire le wheel, installer ce wheel et exécuter les tests ; vérifier aussi
`git diff --check`. Préserver les phases progressives et les ZIP historiques.
Ne pas mettre à jour une version publiée en place. Livrer en patch git am, avec des sujets français et le repère du jalon.
Utiliser l’identité de commit explicitement indiquée ; si elle n’est pas
précisée, la demander avant de créer les commits.

#SOC3 : garder les imports Django/WebView/PyInstaller paresseux et préserver
les noms historiques Petits Pas. Fermer les requêtes avant restauration.

#SOC4a : les primitives TOTP ne consomment rien. Conserver les transactions,
limites de tentatives et politiques dans les produits. Exécuter aussi les tests
crypto et l’application Django neutre avec requirements-tests-auth.txt.

#SOC5a : lire PWA.md. Préserver les noms et anciens états OPFS Petits Pas.
Tester les ressources du wheel installé et `node --test tests/test_navigateur.mjs`.
La fabrique suppose un propriétaire unique ; ne pas enlever les Web Locks.
Ne pas qualifier la production ou terminer #SOC5 sur la seule base des tests Node.

#SOC5b : tester aussi informations() et le secours après remplacement. Le wheel
0.4.0 de #SOC5a était un candidat non publié ; adopter les octets finaux et leurs
empreintes dans les deux produits, sans modifier de version déjà publiée.

#SOC6a : lire SERVEUR.md. Le contrat HTTPS ne lit aucun environnement et
n'importe aucun modèle. Ne pas activer un proxy par défaut ni masquer les
recommandations check --deploy pour rendre un banc vert.

#SOC6b : lire CI-PUBLICATION.md. Ne pas ajouter d'installation pip implicite à
la recette, ni déplacer les assertions métier. Préserver le format de manifeste
Petits Pas, les décisions de promotion et le refus des bundles test/non marqués.
Le banc Gunicorn est loopback Unix, sans suivi de redirection publique.

#SOC7b : lire PDF.md. Ne pas importer les moteurs lourds au chargement du socle.
Préserver les façades et ressources des carnets historiques. Installer les
extras requirements-tests-pdf.txt dans les tests ; vérifier la police du wheel
et sa licence. Le rendu texte ne remplace pas les carnets scolaires avec images.

#SOC3b : les ressources Inno Setup et PowerShell sont dans le wheel. Préserver
l’AppId et les chemins Petits Pas ; les données restent hors du programme.
Tester les ressources installées et les CI Windows des deux consommateurs.
Ne jamais lancer le banc d’installation sur un compte contenant des données.
