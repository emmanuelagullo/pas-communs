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
