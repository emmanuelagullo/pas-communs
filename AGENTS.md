# Consignes

## Écosystème, dépôts et responsabilités

Ces dépôts forment un même écosystème, avec trois responsabilités distinctes :

| Dépôt | Responsabilité | Référence Inria | Miroir GitHub |
| --- | --- | --- | --- |
| `pas-communs` | Socle et architecture techniques communs | <https://gitlab.inria.fr/pas-communs/pas-communs> | <https://github.com/emmanuelagullo/pas-communs> |
| `petits-pas` | Application métier : carnets de suivi en maternelle | <https://gitlab.inria.fr/petits-pas/petits-pas> | <https://github.com/emmanuelagullo/petits-pas> |
| `pas-a-pas-accompagnement` | Application métier : accueil et accompagnement social, notamment CHRS | <https://gitlab.inria.fr/pas-a-pas-accompagnement/pas-a-pas-accompagnement> | <https://github.com/emmanuelagullo/pas-a-pas-accompagnement> |

Inria est la référence du code ; GitHub est le miroir utilisé notamment pour
les constructions Windows/Linux et la publication des wheels et programmes.
Examiner le main public récent avant de préparer un patch. Les miroirs d'un
même dépôt doivent recevoir les mêmes commits et tags ; les versions des trois
dépôts restent indépendantes.

Les deux applications importent `pas_communs`, jamais le code de l'autre
application. Le socle est une bibliothèque embarquée, pas un service central.
Les mécanismes techniques partagés y résident : paquets et sauvegardes,
primitives d'authentification, exécution et construction locales, installateur
Windows, ressources navigateur, contrats serveur, recettes CI, intégrité des
publications et moteurs PDF. Se fier aux API réellement présentes et à leurs
contrats, sans supposer que toute l'infrastructure est déjà extraite.
Les modèles et migrations métier, rôles, permissions, parcours et contenus
restent propres aux applications. Comptes, bases, médias, secrets et espaces
navigateur sont séparés ; une primitive commune ne crée ni SSO ni équivalence
entre une école et un CHRS.

Les sites Hugo restent dans `site/` de chaque application. Les quatre dépôts
auxiliaires de publication ont les références Inria suivantes :

| Produit | Racine du domaine : redirection | Application navigateur : inclusion CI |
| --- | --- | --- |
| Petits Pas | <https://gitlab.inria.fr/petits-pas/petits-pas.gitlabpages.inria.fr> | <https://gitlab.inria.fr/petits-pas/petits-pas-pwa> |
| Pas à Pas | <https://gitlab.inria.fr/pas-a-pas-accompagnement/pas-a-pas-accompagnement.gitlabpages.inria.fr> | <https://gitlab.inria.fr/pas-a-pas-accompagnement/pas-a-pas-accompagnement-pwa> |

Ces auxiliaires ne contiennent ni second exemplaire de l'application, ni
bibliothèque métier, ni fork du socle. Aucun miroir GitHub de ces auxiliaires
n'est déclaré ici : ne pas en inventer un. Le préparateur PWA, les constructeurs,
les manifestes et les sources des sites se modifient dans le dépôt applicatif.

## Coévolution et séparation des préoccupations

- Pour une évolution strictement métier, intervenir dans l'application concernée.
  Dès qu'une évolution dépasse cette couche, examiner aussi le socle, l'autre
  application et les dépôts de publication affectés. Lire leurs AGENTS.md et
  contrats ; expliciter les impacts et les adaptations nécessaires.
- Factoriser ce qui est factorisable et harmoniser ce qui est harmonisable.
  Rechercher un mécanisme existant avant d'en recopier un. Extraire les mécanismes
  techniques communs dans pas-communs avec des paramètres ou façades propres aux
  produits ; harmoniser les conventions et recettes qui peuvent rester dans
  leurs dépôts. Justifier l'abstraction par les usages des deux applications,
  sans imposer un modèle métier commun ni une abstraction spéculative.
- Préparer ensemble les changements du socle et les adaptations des consommateurs.
  Vérifier les deux usages touchés, leurs compatibilités et leurs profils
  serveur/bureau/PWA pertinents. La CI du socle ne qualifie pas à elle seule
  les applications ; préserver sauvegardes historiques, données et identités.
- La version réellement adoptée est fixée par requirements-communs.txt (URL du
  wheel et SHA-256). Les mentions de versions dans les anciens jalons décrivent
  leur historique. Pour du code ou des ressources du socle, publier une nouvelle
  version immuable avant de pousser les consommateurs qui la requièrent. Une
  modification de documentation seule ne nécessite pas de nouveau wheel.
- Livrer les patches par dépôt avec l'ordre d'application, de publication et de
  vérification. Maintenir cette carte et les AGENTS.md affectés cohérents. Annoncer
  à l'avance tout changement de profils d'installation ou de commandes de
  déploiement pour permettre la préparation des instances existantes.
- Dans les deux applications, les tags numériques qualifiés déclenchent les
  releases GitHub et les publications PWA, à partir des artefacts validés sans
  reconstruction ; la reprise manuelle reste disponible. Sur main, la publication
  PWA reste manuelle. Les déploiements serveur gardent leur procédure séparée
  et ne sont pas modifiés implicitement
  par une extraction du socle ou une publication de programme/PWA.

## Travail et vérifications dans ce dépôt

Lire README.md, CONTRATS.md, PAQUETS.md, LOCAL.md, AUTHENTIFICATION.md, PUBLICATION.md et JALONS.md.
Ne jamais importer les modèles métier dans le socle. Préserver les données,
formats et migrations historiques de Petits Pas. Exemples fictifs uniquement.
Pour un changement de code ou de ressources, construire le wheel, l’installer
et exécuter les tests pertinents ; vérifier aussi `git diff --check`. Pour une
modification documentaire seule, contrôler les liens et la cohérence des
consignes. Préserver les phases progressives et les ZIP historiques.
Ne pas mettre à jour une version publiée en place. Livrer en patch git am, avec des sujets français et le repère du jalon.
Utiliser l’identité de commit explicitement indiquée ; si elle n’est pas
précisée, la demander avant de créer les commits.

## Contrats techniques hérités des jalons

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


#AUD : lire les contrats actualisés et la recette QUALIFICATION.md de pas-communs.
Le candidat 0.8.0 doit être publié immuablement avant de pousser ses consommateurs.
Préserver les noms ZIP historiques portables ; refuser les alias Windows à
l'export comme à l'import sans renommer les données. Le runtime Pyodide est
sélectionné explicitement dans les constructeurs ; les politiques de promotion
et de déploiement restent applicatives. Qualifier les octets du wheel et les
deux consommateurs ; aucune installation pip n'est implicite dans cette recette.
