# Publication du wheel et adoption

## Adoption courante (#SOC3)

1. Appliquer les patches #SOC2 puis #SOC3 de Pas communs et pousser son `main` sur les deux forges.
2. Attendre les contrôles, puis poser le tag `0.2.0` sur le commit validé et
   pousser ce même tag sur les deux forges.
3. Le workflow GitHub teste, construit et publie un wheel et `SHA256SUMS` dans
   une release GitHub. GitLab reste la source de référence et vérifie le code.
4. Vérifier que la release est publique et que son empreinte correspond à celle
   épinglée dans les patches des deux applications.
5. Appliquer ensuite les patches applicatifs. Ne pas les déployer avant cette
   publication : l'URL de dépendance ne devient disponible qu'à cette étape.

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

## Versions suivantes

Modifier le socle, augmenter la version, tester et publier le nouveau tag.
Mettre ensuite à jour l'URL et l'empreinte dans chaque application concernée,
puis exécuter sa propre CI. Une modification purement métier ne republie pas le
socle. Pas de suivi automatique de `main`, de `latest`, ni de branche Git mobile.
PyPI reste facultatif ; aucun registre privé, sous-module ou service n'est ajouté.


Si #SOC2 n'a pas encore été adopté, il n'est pas nécessaire de publier un
wheel 0.1.0 intermédiaire pour utiliser directement 0.2.0 : appliquer les deux
étapes dans chaque dépôt, publier d'abord le wheel 0.2.0, puis pousser les
applications avec leur dépendance finale. Les patches #SOC3 sont incrémentaux.
Conserver Petits Pas 0.10 sur son commit antérieur à #SOC2.
