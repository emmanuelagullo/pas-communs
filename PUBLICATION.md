# Publication du wheel et adoption

## État courant : 0.8.0 publiée

Le tag 0.8.0 et son wheel sont immuables. Les deux applications l'adoptent au
20 octobre 2026, avec SHA-256
`38855af96c89ae059acdc8e99186dc935d42dd7957b6e1cb597bbd1bc4c81a51`.
Une correction documentaire de main ne doit ni recréer ce tag, ni remplacer
ses fichiers, ni imposer une nouvelle version aux consommateurs. Le README
entre dans les métadonnées du wheel : ne pas publier un rebuild de main sous
le numéro 0.8.0. Reproduire cette release depuis son tag exact seulement.

Pour une future modification de code/ressources : nouvelle version, tests et
publication immuable, puis adoption explicite par chaque consommateur concerné.
Ne pas imposer des versions identiques en permanence. Une évolution purement
métier ou documentaire ne republie pas le socle. Les branches et tags des
applications sont indépendants de ceux de la bibliothèque.

La CI utilise le jeton GitHub Actions intégré, avec permission `contents: write`
uniquement dans le job de publication. Aucun secret de déploiement supplémentaire.
Le tag doit correspondre à `pyproject.toml`. Les artefacts exacts du job réussi sont
promus sans reconstruction ; le brouillon est téléchargé et vérifié avant
publication. Une erreur peut laisser un brouillon à examiner, sans remplacer
une release existante. Les artefacts temporaires CI expirent ; les fichiers de
la release sont la dépendance durable. Ne pas déplacer un tag publié ou remplacer
un wheel déjà adopté ; corriger avec une nouvelle version.

## Dépendance applicative

Chaque produit possède `requirements-communs.txt` avec l'URL exacte du wheel
et `#sha256=...`. Ses requirements serveur, bureau et PWA incluent ce fichier.
`pip` télécharge et contrôle cette empreinte pendant l'installation/construction.
L'utilisation autonome ne télécharge aucun code. Un cache pip évite les transferts
répétés ; un échec d'accès à la release fait échouer la construction explicitement.

Pour développer avant publication : installer les dépendances du produit en
omettant provisoirement cette seule inclusion (dans un fichier temporaire), puis
installer le wheel local ou utiliser `pip install -e ../pas-communs`. Ne pas
committer ce contournement et ne pas publier de distribution avec une source
locale non identifiée. La livraison inclut un wheel candidat pour ces essais ;
la CI doit reconstruire le même wheel et retrouver son empreinte.

Avant publication, construire le wheel candidat avec le backend épinglé,
contrôler sa reproductibilité et exécuter QUALIFICATION.md. Les patches
consommateurs peuvent être testés localement avec ces octets ; ne les pousser
qu'après publication du wheel et vérification du SHA-256. Une CI verte ne
remplace pas les essais Windows et PWA des deux produits. Aucun déploiement
serveur n'est déclenché par cette procédure.

## Versions suivantes

Modifier le socle, augmenter la version, tester et publier le nouveau tag.
Mettre ensuite à jour l'URL et l'empreinte dans chaque application concernée,
puis exécuter sa propre CI. Une modification purement métier ne republie pas le
socle. Pas de suivi automatique de `main`, de `latest`, ni de branche Git mobile.
PyPI reste facultatif ; aucun registre privé, sous-module ou service n'est ajouté.


## Historique des adoptions SOC2–SOC6b (ne pas réexécuter pour 0.8.0)

Si #SOC2 n'a pas encore été adopté, il n'est pas nécessaire de publier un
wheel 0.1.0 ou 0.2.0 intermédiaire pour utiliser directement 0.3.0 : appliquer les trois
étapes dans chaque dépôt, publier d'abord le wheel 0.3.0, puis pousser les
applications avec leur dépendance finale. Les patches #SOC3 et #SOC4a sont incrémentaux.
Conserver Petits Pas 0.10 sur son commit antérieur à #SOC2.


## Candidat 0.4.0 (#SOC5a)

Appliquer les patches jusqu'à #SOC5a puis publier le wheel 0.4.0 validé avant
les applications qui l'épinglent. Si aucune version du socle n'est encore
publiée, il suffit de publier cette version finale ; les versions intermédiaires
ne sont pas nécessaires aux installations neuves. Les patches restent
incrémentaux, avec #SOC4b uniquement dans le socle et le CHRS.
Petits Pas 0.10 reste sur son commit antérieur à #SOC2.
Une CI de socle verte ne publie pas les PWA des produits.

#SOC5b finalise le candidat 0.4.0 non publié. Appliquer aussi #SOC5b avant de
créer son premier tag 0.4.0. Le wheel de #SOC5a est remplacé par celui de #SOC5b,
avec une nouvelle empreinte explicite dans les deux consommateurs. Ne jamais
remplacer les octets d'une release déjà publiée : cette procédure concerne
uniquement le candidat dont la publication a été différée.

## #SOC6a — version 0.5.0

La version 0.4.0 reste immuable. Publier 0.5.0 après la CI du socle, puis pousser
les applications qui l'épinglent. Le profil serveur est volontaire : cette
publication ne bascule aucune instance et ne publie aucun produit.

## Finalisation #SOC6b

0.5.0 était le candidat non publié de #SOC6a. Appliquer aussi #SOC6b, reconstruire
ou employer son wheel final et sa nouvelle empreinte, puis publier le premier
tag 0.5.0 après CI verte. Les deux consommateurs épinglent les mêmes octets.
Ne pas publier l'ancien candidat #SOC6a ni remplacer 0.4.0.
Les outils partagés décrivent/vérifient des octets ; ils ne donnent pas une
permission de publier les applications. Lire CI-PUBLICATION.md.

## Candidat 0.9.0 — sauvegardes locales

Ce patch prépare une nouvelle version ; il ne publie rien. Qualifier selon
SAUVEGARDES.md, publier le tag 0.9.0 sur les deux forges et promouvoir le wheel
exact vérifié. Comparer l'empreinte publique avec celles des deux patches
consommateurs avant leur adoption. Un écart impose de corriger les adoptions,
jamais de remplacer un wheel déjà publié.

## Candidat 0.10.0 — programmes macOS arm64

Ce patch prépare une nouvelle version ; il ne publie rien. Les consommateurs
gardent leur wheel adopté (0.9.0) jusqu'à la publication immuable de 0.10.0.
Après qualification (CI du socle, puis un banc de construction macOS), publier
le tag 0.10.0 sur les deux forges et promouvoir le wheel exact vérifié. Les
produits n'ont rien à changer pour Windows et Linux ; l'ajout de macOS dans
leurs workflows et leurs sites est une décision propre à chaque produit.
