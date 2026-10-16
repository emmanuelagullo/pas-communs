# Exécution et assemblage locaux — #SOC3

Pas communs 0.2.0 fournit les mécanismes communs aux programmes Petits Pas et
Pas à Pas — Accompagnement. Le format ZIP #SOC2 et son API ne changent pas.

## Runtime

`pas_communs.local` fournit :

- `paquet_par_defaut(application)` : dossier XDG sous Linux, LOCALAPPDATA sous
  Windows ; le slug du produit distingue toujours ses données ;
- `verrouiller` : verrou interprocessus voisin du dossier, conservé à travers
  les renommages et libéré à la fin du contexte ;
- `initialiser_paquet` : création de clé sous verrou, refus d'un paquet incomplet ;
- `copier_paquet` : copie cohérente SQLite et médias vers une nouvelle destination,
  sans remplacer la source ;
- `migration_necessaire` / `proteger_avant_migration` : détection Django paresseuse
  et copie SQLite technique avant évolution du schéma ;
- `ServeurBureau` : WSGI lié à 127.0.0.1 sur un port libre, sérialisation des
  requêtes, fermeture de l'itérable et attente de la requête active à l'arrêt ;
- `creer_fenetre` : ouverture PyWebView avec téléchargements autorisés ;
- `demarrer_avec_journal` : journal UTF-8 et notification d'échec sans console.

Le programme appelant choisit sa configuration Django, son nom de base et son
parcours d'installation. Il appelle `initialiser_paquet` sous le verrou, garde
le verrou pendant migrations et serveur, puis ferme le serveur avant toute
activation de restauration. La fonction de blocage des écritures est fournie
par l'application : le socle ne connaît ni école ni dossier social.

Django, PyWebView et PyInstaller sont des dépendances des profils bureau des
applications. Les sauvegardes #SOC2 restent utilisables sans eux ; aucune
importation de ces bibliothèques n'est ajoutée à `pas_communs.paquets`.
Les modules bureau ne sont pas employés par le worker PWA.

## Assemblage

`pas_communs.construction.assembler` est appelé depuis un petit `.spec` du produit.
Celui-ci énumère explicitement ses ressources, modules, nom d'exécutable,
configuration et éventuelles DLL Pango. L'algorithme commun conserve le dossier
PyInstaller (pas de binaire monolithique), les ressources WebView2 Windows et
les typelibs WebKitGTK Linux. Il n'embarque pas de données utilisateur. Les outils de construction du socle,
PyInstaller et les modules de tests applicatifs sont exclus du programme.

`python -m pas_communs.construire_bureau --spec CHEMIN --nom NOM` exécute le
`.spec`, exige le succès de `--verifier-distribution` du binaire, puis prépare
une archive ZIP Windows ou tar.gz Linux. Une erreur de vérification interdit
la création de la nouvelle archive. Construire sur le système cible.

Les installateurs Petits Pas (Inno Setup, raccourcis et gestion des versions)
sont conservés : ils continuent d'employer ses chemins et son exécutable.
Le CHRS fournit à ce stade des archives de programme à extraire, sans assistant
Windows ni création automatique de raccourcis. Leur publication publique reste
un chantier distinct ; les nouveaux workflows fournissent des artefacts d'essai.

## Qualification

Tester le socle, chaque `.spec`, le premier compte CHRS, le verrou entre
processus, l'arrêt des requêtes et la persistance après relance. Une vérification
sans fenêtre ne qualifie pas le moteur graphique, les téléchargements du système
ou la restauration réelle sur Windows/Linux. Ces essais restent dans les produits.
Ne pas déduire une compatibilité universelle Linux de la seule construction
Ubuntu 24.04. Les paquets de données ne sont jamais remplacés par les mises à
jour du programme.
