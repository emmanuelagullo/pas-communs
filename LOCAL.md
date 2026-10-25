# Exécution et assemblage locaux — contrat actuel

Les mécanismes introduits avec Pas communs 0.2.0 sont communs aux programmes Petits Pas et
Pas à Pas — Accompagnement. Le format ZIP #SOC2 et son API ne changent pas.

## Runtime

`pas_communs.local` fournit :

- `paquet_par_defaut(application)` : dossier XDG sous Linux, LOCALAPPDATA sous
  Windows, `~/Library/Application Support` sous macOS ; le slug du produit distingue toujours ses données ;
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
une archive : ZIP Windows (`NOM-windows.zip`), tar.gz Linux (`NOM-linux.tar.gz`)
ou image disque macOS (`NOM-macos-arm64.dmg`). Une erreur de vérification
interdit la création de la nouvelle archive. Construire sur le système cible.

## Moteur de fenêtre absent (#SOC3c)

`pas_communs.moteur` sonde le composant système et fournit un message en français,
sans jargon : WebView2 sous Windows (clé `pv` documentée par Microsoft), GTK 3 et
WebKitGTK 4.1 sous Linux, WebKit sous macOS. `signaler_moteur(nom, notifier=...)`
notifie sans jamais bloquer : une clé de registre absente n'interdit pas toujours
l'ouverture de la fenêtre, et un produit ne doit pas empêcher un démarrage possible.
Chaque produit appelle `signaler_moteur` avant `creer_fenetre` et affiche le message
dans sa fenêtre d'erreur ; ce branchement relève du produit, non fait ici. L'installateur
Windows signale aussi un WebView2 non détecté en fin d'installation, jamais en mode
silencieux.

## macOS (#SOC3c)

Cibles livrées : Windows x64, Linux x86_64 (Ubuntu 24.04) et **macOS arm64
seulement**. Intel n'est pas livré et Windows ARM64 non plus : l'ajout attend un
besoin explicite. Le système est identifié par `pas_communs.plateforme.systeme`
(`sys.platform`), jamais par `os.name`, qui classait macOS avec Linux.

Le `.spec` du produit appelle `assembler(..., bundle_identifiant="fr.inria.produit")`.
L'identifiant est obligatoire sous macOS, ignoré ailleurs, et doit rester stable :
il fait l'identité du programme. Le socle n'en fournit jamais par défaut. Le
résultat est un `NOM.app` (dossier PyInstaller embarqué, exécutable arm64 sans
console) puis un DMG avec raccourci vers Applications. PyWebView emploie WKWebView
via PyObjC : aucun moteur à embarquer. Les données restent hors du `.app`, sous
`~/Library/Application Support/<application>/paquet-autonome`.

Le programme n'est **ni signé ni notarisé**. Depuis macOS Sequoia, l'ouverture
passe par Réglages Système → Confidentialité et sécurité → « Ouvrir quand même » ;
le produit doit le dire à ses utilisateurs.

PDF natif (WeasyPrint/Pango). Un Mac d'utilisateur n'a pas Homebrew et macOS ne
cherche pas les bibliothèques par nom hors de /usr/lib. Pour l'embarquer, le `.spec`
passe `pango_variable="NOM_DE_VARIABLE"` à `assembler`, et la variable d'environnement
désigne, à la construction, le dossier des dylibs (`/opt/homebrew/lib`) : les six
bibliothèques que WeasyPrint charge sont copiées dans le bundle, PyInstaller y ajoute
leurs dépendances et réécrit leurs chemins. Sans variable, aucun PDF natif n'est
embarqué. Au lancement, `pas_communs.pdf` appelle `pango_macos.preparer_pango_embarque()`
(un produit qui importe WeasyPrint lui-même l'appelle avant) : cffi charge ces
bibliothèques par chemin absolu et fontconfig reçoit une configuration minimale vers
les polices du système (`/System/Library/Fonts`, `/Library/Fonts`, `~/Library/Fonts`).
Les bibliothèques Homebrew imposent leur propre version minimale de macOS, que le
qualificateur mesure (« Version minimale de macOS exigée par le bundle ») : la lire
avant de la promettre aux utilisateurs. GLib, Pango, HarfBuzz, FontConfig et leurs
dépendances sont sous licences libres propres (LGPL, MIT) : en redistribuant le `.app`,
joindre leurs notices, à vérifier par le produit.
L'application minimale `tests/application_minimale` qualifie cette chaîne en CI sur les
trois systèmes (voir QUALIFICATION.md) ; elle ne remplace pas les bancs des produits.
Les imports PyObjC listés par l'assembleur et la fenêtre WKWebView ont été vus verts
sur le runner macOS arm64 ; ni un Mac réel ni un essai interactif ne les remplacent.

Depuis #SOC3b (0.7.0), `pas_communs.installateur_windows` génère et compile
l'installateur Inno Setup depuis une configuration JSON du produit. Le modèle
`.iss` et le banc PowerShell sont des ressources du wheel. Inno Setup reste
un outil de construction Windows, sans dépendance supplémentaire au runtime.

```sh
python -m pas_communs.installateur_windows --configuration scripts/installateur-windows.json
# Sur un runner Windows jetable seulement :
python -m pas_communs.installateur_windows --configuration scripts/installateur-windows.json --verifier
```

Construire le programme avant le setup. La version provient du fichier généré
version-application.txt (UTF-8 avec ou sans BOM), ou de --version. Le nom et
l'AppId, l'URL publique et le dossier de données sont explicites dans le JSON.
Le programme est installé sous LOCALAPPDATA/Programs/<programme>/app sans
élévation. L'AppId, le raccourci et le chemin Petits Pas sont conservés pour
reconnaître les installations existantes. Aucun format de données ne change.

Le banc --verifier refuse un compte avec installation ou données déjà présentes.
Il exige un environnement CI, installe, contrôle le raccourci et le vrai
exécutable (--verifier-distribution), réinstalle puis désinstalle. Un fichier
fictif dans le dossier de données doit rester identique à chaque étape ; seul
ce témoin est ensuite retiré. Aucune directive ne supprime les données. Le ZIP
portable reste disponible en parallèle du setup.

La compilation et les contrôles Windows des deux produits sont en CI GitHub ;
ils ne remplacent pas un essai interactif sur Windows 10/11 ou la qualification
du moteur WebView2. Le setup ne fournit pas WebView2 ni signature numérique.
Les publications applicatives suivent les workflows des produits : automatiques
après une construction de tag qualifiée, avec reprise manuelle. Elles promeuvent
le setup vérifié sans reconstruction, avec son empreinte.

## Qualification

Tester le socle, chaque `.spec`, le premier compte CHRS, le verrou entre
processus, l'arrêt des requêtes et la persistance après relance. Une vérification
sans fenêtre ne qualifie pas le moteur graphique, les téléchargements du système
ou la restauration réelle sur Windows/Linux/macOS. Ces essais restent dans les produits.
Ne pas déduire une compatibilité universelle Linux de la seule construction
Ubuntu 24.04. Les paquets de données ne sont jamais remplacés par les mises à
jour du programme.
