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
  releases GitHub ; seuls les tags sans suffixe publient automatiquement la PWA,
  à partir des artefacts validés sans
  reconstruction ; la reprise manuelle reste disponible. Sur main, la publication
  PWA reste manuelle. Les déploiements serveur gardent leur procédure séparée
  et ne sont pas modifiés implicitement
  par une extraction du socle ou une publication de programme/PWA.

## Travail et vérifications dans ce dépôt

Lire README.md et CONTRATS.md, puis les contrats du domaine : PAQUETS.md,
LOCAL.md, AUTHENTIFICATION.md, PWA.md, SERVEUR.md, CI-PUBLICATION.md, PDF.md,
PUBLICATION.md et QUALIFICATION.md. JALONS.md décrit l'historique, pas l'état courant.
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

#SOC3c : lire LOCAL.md (macOS). Identifier le système par pas_communs.plateforme,
jamais par os.name. macOS est livré en arm64 seulement, non signé ; ne pas
inventer de bundle_identifiant par défaut ni ajouter Intel, universal2 ou
Windows ARM64 sans besoin explicite. Le PDF natif macOS n'existe que si le produit
passe pango_variable à assembler ; ne l'annoncer qu'après une sonde verte sans Homebrew
(--isoler-homebrew) et en indiquant la version minimale de macOS mesurée. Les noms historiques des archives Windows et Linux sont inchangés.
Le PDF natif macOS charge une seule copie de chaque bibliothèque (pango_macos) : ne pas rétablir
le chargement de libharfbuzz-subset ni de copies propres à WeasyPrint sans une sonde qui reproduit
un paquet embarquant sa propre copie (Pillow).
Une erreur de démarrage macOS passe par pas_communs.notification : ne pas l'avaler, ne pas
construire de commande shell avec un message.
Le message de moteur absent (pas_communs.moteur) et le shortcode aide-installation
décrivent l'état réel des programmes (non signés, macOS arm64, Ubuntu 24.04) : les
mettre à jour ensemble si cet état change, avant d'avancer un gitlink Hugo.
tests/application_minimale se construit depuis le wheel installé, jamais depuis src/ ;
ne pas y mettre de métier ni la promouvoir en produit. Ses étapes informatives et le
job macOS ne deviennent bloquants que par décision explicite.

#SOC3b : les ressources Inno Setup et PowerShell sont dans le wheel. Préserver
l’AppId et les chemins Petits Pas ; les données restent hors du programme.
Tester les ressources installées et les CI Windows des deux consommateurs.
Ne jamais lancer le banc d’installation sur un compte contenant des données.


#AUD : lire les contrats actualisés et la recette QUALIFICATION.md de pas-communs.
La version 0.8.0 est publiée et adoptée ; préserver son tag et ses octets.
Une modification documentaire seule ne demande pas de nouveau wheel. Les
consommateurs peuvent conserver des versions différentes, explicitement épinglées.
Préserver les noms ZIP historiques portables ; refuser les alias Windows à
l'export comme à l'import sans renommer les données. Le runtime Pyodide est
sélectionné explicitement dans les constructeurs ; les politiques de promotion
et de déploiement restent applicatives. Qualifier les octets du wheel et les
deux consommateurs ; aucune installation pip n'est implicite dans cette recette.

#SOC — copies : lire SAUVEGARDES.md pour le candidat 0.9.0. Les tables à vider
restent choisies par le produit ; le socle ne connaît aucun modèle CHRS/scolaire.
Ne pas appliquer une restauration tant que HTTP et les connexions sont ouverts.

#SOC — sites publics : lire HUGO.md. Le thème Hugo sous hugo/pas est consommé
par un sous-module épinglé, indépendamment du wheel Python. Les contenus, liens,
comptes fictifs et publications restent applicatifs. Vérifier les deux sites,
les liens/ancres et le rendu responsive avant d’avancer leurs gitlinks.


## Aides contextuelles et erreurs compréhensibles

Pour chaque champ ou action dont le sens n'est pas évident, expliquer l'intention,
la cible (personne, groupe, période), l'effet et les limites utiles. Éviter les
aides qui répètent simplement le libellé ; ne pas imposer une bulle à chaque item.
Les informations indispensables à la saisie ou au consentement restent visibles,
près du champ ou de la confirmation, avec `help_text` / `aria-describedby`.
Les détails secondaires peuvent être dépliables (`details` / `summary` natifs),
accessibles au clavier et au tactile, sans dépendance nouvelle par défaut.
Une vraie info-bulle au survol doit aussi être accessible au focus, rester
lisible quand on la survole et pouvoir être fermée avec Échap. Ne pas utiliser
`title` comme unique aide. Référence :
https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html .

Une erreur de champ est rattachée au champ nommé, visible dans le choix de saisie
actif, et associée à son contrôle. Un résumé d'erreurs renvoie aux champs ; ne
pas aplatir une ValidationError structurée en message global anonyme. Préserver
les valeurs saisies et la validation serveur sans JavaScript.

Avant une nouvelle abstraction d'aide, examiner les mécanismes existants des
deux produits. Les mots et règles métier restent dans chaque application ; le
socle ne fournit un composant que si des usages réels justifient son extraction.
Vérifier les parcours modifiés au clavier, sur écran étroit et sans JavaScript ;
distinguer les tests du HTML des observations réelles en navigateur.
