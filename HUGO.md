# Sites publics Hugo (#SOC)

`hugo/pas/` est un thème Hugo autonome, dérivé du site Petits Pas (AGPL-3.0-or-later).
Les contenus publics Petits Pas restent CC-BY-SA-4.0 ; aucun contenu métier,
compte, sauvegarde ou secret n’est incorporé au thème.

## Consommation explicite

Chaque application conserve `site/` et épingle **un commit Git exact** de ce
socle dans le sous-module `site/theme-communs`. Le miroir GitHub public sert au
clonage ; publier auparavant le même commit sur la référence Inria et le miroir.
Hugo utilise `themesDir = "theme-communs/hugo"` et `theme = "pas"`.

```sh
git submodule update --init site/theme-communs
hugo --source site --minify --panicOnWarning
```

Aucun Go, module Hugo distant, téléchargement à chaque rendu, pip ni wheel
supplémentaire n’est requis. Cette dépendance de construction du site est
indépendante du wheel Python épinglé dans requirements-communs.txt. Une évolution
Hugo seule ne change ni la version Python ni les installations serveur/bureau/PWA.
Ne pas mettre à jour le sous-module avec `--remote` dans la CI : le gitlink du
consommateur est la version adoptée. Pour évoluer : publier le socle, avancer
explicitement le gitlink de chaque consommateur, vérifier les deux sites.

## Frontières

Commun : base HTML, métadonnées, navigation et pied de page pilotés par les
menus Hugo, listes/pages/fiches de guide, recherche progressive sans réseau,
encadré `parcours`, styles et contrôleur de recherche. Le thème corrige aussi
les anciens main imbriqués des fiches Petits Pas.

Propres au produit : page d’accueil et son illustration, contenus et URL,
menus, jeux fictifs et identifiants publics, statuts de publication, captures,
catalogues des téléchargements et préparation des documents techniques.
Le partial `acces-demonstration.html` reste applicatif : les comptes et droits
scolaires n’ont pas d’équivalence CHRS. Les shortcodes métier le restent aussi.
La recherche prend `params.guidePlaceholder`. La couleur des métadonnées prend
`params.themeColor`. La feuille `static/css/identite.css` de chaque produit
redéfinit les variables `--accent`, `--accent-dark`, `--ink`, `--muted`,
`--paper`, `--cream`, `--sun`, `--line` et `--tint` au besoin.

Aide à l'installation des programmes de bureau : le shortcode
`{{< aide-installation nom="Produit" dossier="identifiant-donnees" >}}` rend les
trois systèmes pour un public non informaticien, dans l'ordre Windows, macOS puis
Linux (`systeme="windows"`, `"macos"` ou `"linux"` pour un seul). Il donne
l'avertissement SmartScreen, WebView2 absent, la procédure « Ouvrir quand même »
de macOS, les paquets Ubuntu, la version minimale de macOS (`macos_min`, 15 par défaut, mesurée par
la qualification), l'emplacement des données et la désinstallation. Les
noms de fichiers à télécharger et les liens restent dans le catalogue du produit,
qui encadre le shortcode. Le texte dit l'état réel : programmes non signés, macOS
sur puce Apple seulement, Ubuntu 24.04 seul qualifié. Si cet état change, modifier
le shortcode avant d'avancer les gitlinks. `tests/site_exemple` construit ce thème
en CI (`theme-hugo.yml`) ; aucun produit n'est touché tant que son gitlink n'avance pas.

Navigation principale : `menus.main` ; liens complémentaires : `menus.footer`.
Employer `pageRef` pour les pages internes, ce qui conserve aria-current dans
les sous-rubriques. `params.projectPath` désigne la page projet depuis la 404.
Le thème n’impose aucune URL ni contenu métier. Les contenus conservés dans
les applications évitent une traduction artificielle entre écoles et CHRS.

## Vérification

Hugo Extended 0.140.2 avec `--panicOnWarning`, aux URL racine et préfixées.
Après les préparations propres à chaque site, exécuter :

```sh
python3 site/theme-communs/hugo/verifier-site.py --sortie site/public --base-url https://example.invalid/produit/
```

Le contrôle porte sur les liens internes et ancres, les identifiants uniques,
un seul main et h1 par page, la langue et les noms de navigation. Les pages
de redirection Hugo (aliases) sont contrôlées pour leur cible, sans exiger de
contenu principal. Il ne remplace pas la revue visuelle, le clavier, les
contrastes et le navigateur mobile. Les ressources générées absentes doivent
être produites par la préparation métier avant le contrôle complet.
