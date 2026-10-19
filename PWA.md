# Navigateur — #SOC5a

La version 0.4.0 contient une première extraction, employée par les deux
produits. Ce jalon ne termine pas #SOC5 et ne publie aucune nouvelle PWA.

## Composants communs

- `navigateur/stockage.mjs` : fabrique de stockage OPFS immuable, pointeur
  IndexedDB transactionnel, état précédent et état de secours ; mêmes plafonds
  historiques (base/fichier 64 Mio, ensemble 256 Mio, 5 000 entrées).
- `transport.mjs` : échanges MessageChannel et délais des opérations longues.
- `capacites.mjs` : vérification d'une écriture OPFS depuis un Worker.
- `navigateur.crypto` : adaptations PBKDF2/scrypt de Python vers PyCryptodome
  dans WASM, sans changement des mots de passe ni des paramètres de hachage.
- `navigateur.http` : environnement WSGI et cookies virtuels ; les vues Django
  gardent CSRF, connexion et permissions. Aucun partage de session entre produits.
- `construction_pwa` : téléchargement avec reprise, vérification du runtime
  épinglé et nettoyage de son cache. Aucun téléchargement lors de l'import.

`copier_ressources(destination)` copie les trois modules JavaScript du wheel
installé dans le bundle statique. Leur empreinte entre dans le manifeste de
chaque produit. Aucun paquet npm commun ni CDN supplémentaire à l'utilisation.
Chaque produit sélectionne explicitement RUNTIME_314_0_7 : version Pyodide,
version Python et ABI viennent du même objet immuable. verifier_runtime contrôle
ces valeurs ; l'ancien argument version n'est accepté que s'il correspond au
contrat choisi. Aucun changement du runtime distribué n'est introduit en 0.8.0.
Le bureau exclut ces outils de construction et ressources navigateur inutilisés.

## Contrat de stockage

La fabrique exige un identifiant d'application, une base, un nom IndexedDB,
un répertoire OPFS et un chemin de publication. Chaque instance a son état
propre. Essai et aperçu sont des suffixes explicites du profil Petits Pas.
Les manifestes écrits portent l'identité du produit ; un manifeste étranger
est refusé. Seul le profil Petits Pas accepte ses anciens ZIP et manifestes
sans identité. Les noms de ses bases et répertoires historiques sont conservés.
Le format public des sauvegardes n'est pas modifié par ces manifestes internes.

Un propriétaire unique, protégé par Web Lock dans la coque du produit, sérialise
les requêtes. Le stockage ne fournit pas lui-même ce verrou. Écrire puis vider
les nouveaux blobs, écrire le manifeste, activer le pointeur transactionnel,
puis seulement répondre à la saisie. Aucun blob confirmé n'est écrasé.
Une interruption avant activation garde l'état antérieur ; après activation,
le nouvel état est confirmé. Un défaut de nettoyage après commit ne l'annule pas.
Une corruption est un refus d'ouverture, jamais un espace vide de remplacement.

Changer d'origine ou de chemin crée un autre espace : ce n'est pas une migration.
Les noms et scopes évitent les collisions accidentelles ; ils ne constituent
pas une barrière de sécurité entre applications d'une même origine. Aucun
chiffrement du stockage navigateur ni synchronisation n'est ajouté.

## Frontière conservée dans les produits

Coque, Service Worker, contrôle des mises à jour, Worker WSGI, installation,
modèles, migrations, inventaire des fichiers et parcours de sauvegarde restent
propres à chaque application dans cette première tranche. Petits Pas conserve
ses transferts OPFS, WORKERFS, aperçus et confirmations métier. Le prototype
CHRS n'embarque ni modèles scolaires ni écrans d'export d'école.

## Clôture du moteur (#SOC5b)

Le CHRS ajoute les copies ZIP au format du moteur commun, vérifiées dans un
Worker neuf avant confirmation. L'activation conserve l'état précédent. La
fabrique expose `informations()` (présence, version, secours disponible), sans
modifier les anciens appels ni les noms et formats Petits Pas. Un export de
secours lit les fichiers confirmés sans migrer ni ouvrir une session Django.
Une corruption n'est jamais remplacée silencieusement par une base vide.
Une restauration confirmée passe `reutiliser=false` au dernier argument de
`save` : aucun blob ni manifeste actuel potentiellement altéré n'est réutilisé,
même si le pointeur annonce la même empreinte. Les appels historiques gardent
le réemploi des blobs pour les médias volumineux. Un secours déjà endommagé
reste refusé, sans prétendre pouvoir réparer ses octets.

Les essais des deux produits qualifient le moteur PWA sur Chromium/Linux :
installation, anciennes données, mise à jour explicite, interruption et reprise.
Les coques/Workers restent volontairement propres aux produits : la petite
application CHRS n'a pas les transferts ni médias scolaires. #SOC5 est clos dans
ce périmètre technique ; cela n'autorise pas des dossiers CHRS réels et ne vaut
pas qualification Safari/iOS, Firefox, Windows ou appareils terrain.
Le stockage local peut être effacé par le navigateur ; garder des ZIP privés
hors appareil. Pas de chiffrement ni synchronisation ajouté.

## Vérifier

Construire et installer le wheel puis lancer les tests Python habituels.
Les ressources copiées doivent provenir de ce wheel. Le contrat JavaScript se
teste avec Node 24 : `node --test tests/test_navigateur.mjs`. Ce banc modélise
les transactions et les interruptions ; il ne remplace pas les essais OPFS
réels dans les bancs Chromium de chaque produit, ni les appareils terrain.
