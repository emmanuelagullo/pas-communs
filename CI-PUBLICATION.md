# Recettes CI et intégrité des publications — contrat actuel

Les mécanismes ont été introduits sous SOC6b puis complétés sous AUD. Leur
version adoptée reste fixée par chaque consommateur ; les numéros de jalons
ci-dessous sont historiques. Les contrôles de promotion de 0.8.0 ne choisissent
ni une destination, ni une politique de préversions PWA.


## Recette partagée dans le wheel

La commande python -m pas_communs.ci django exécute check, absence de migration
manquante et tests. --settings-tests, --durations et --timing ne touchent qu'aux
tests. --controle scripts/banc.py ajoute un contrôle Python du produit après
les tests ; tout échec arrête la recette. --migrer et --pip-check sont explicites ;
rien n'installe de paquet automatiquement. Sous Guix/PYTHONPATH, omettre
--pip-check permet de continuer sans pip.

Les forges gardent installation, matrice, services et stockage d'artefacts.
Le produit garde ses scripts et assertions métier. La recette vient du wheel
épinglé par SHA-256, pas d'un include YAML sur main ou d'une branche Git mobile.
Pas de runner maison ni nouveau registre. Les tests PostgreSQL Petits Pas
gardent leur service GitLab et leur DATABASE_URL ; le banc isolé du profil
serveur utilise volontairement SQLite fictif.

## Contrôler des octets avant publication

publication.identite, decrire, manifeste et verifier partagent empreinte,
taille, commit/tag déclaré, mode/cible et provenance déclarée du job. Le produit
fournit l'identifiant de format ; les manifestes croisés sont refusés.
Le format historique Petits Pas reste inchangé (schema 1), avec ses façades,
notes et politiques de promotion dans son dépôt. Le CHRS produit son propre
manifeste pour les archives construites, sans publier de release ou de site.

verifier_bundle refuse testMode absent/vrai, mauvaise version/application,
chemins et empreintes invalides, fichiers supplémentaires et bases/clés locales
visibles parmi les statiques. Il ne remplace pas les tests du produit, n'audite
pas le contenu de toute archive et ne prouve pas la provenance cryptographique
d'un exécutable. Le manifeste n'est ni une signature ni la preuve d'une CI verte.
Les publishers gardent leurs contrôles d'origine/job réussi/tag/cible.
Aucun jeton ou donnée d'exploitation n'entre dans ces manifestes.

Le CHRS archive un bundle normal préalablement vérifié, puis décrit et vérifie
le ZIP exact. Ses artefacts restent temporaires et fictifs ; pas de publication
automatique. Les recettes de publication Petits Pas restent en place avec
les mêmes garde-fous, sans reconstruction de l'artefact promu.
Le wheel du socle reste publié par son workflow tagué existant, après tests,
avec SHA256SUMS et vérification du téléchargement du brouillon.

## Réseau du profil serveur

Les scripts produits préparent leurs bases/statiques fictifs et utilisent
qualification_http pour démarrer un vrai Gunicorn lié à un socket loopback
hérité. Les réponses ne sont jamais suivies vers un domaine public. Le banc
contrôle redirection sans proxy approuvé, puis health, Host, CSRF, cookie Secure
et statiques avec le proxy explicitement adopté. Les processus sont arrêtés et
récoltés même sur échec. Ce banc Unix ne configure ni certificat ni hébergeur.

Gunicorn est lancé avec --forwarded-allow-ips="" : sinon son propre traitement
de X-Forwarded-Proto peut précéder la décision explicite de Django. Un déployeur
doit protéger son backend et faire remplacer les en-têtes par son vrai proxy.
La confiance dans l'adresse IP cliente et les limites de tentatives reste une
décision produit/exploitation, distincte de la confiance HTTPS.

## Clôture

#SOC6 est clos pour ces recettes communes, profils volontaires et bancs locaux.
Les migrations, permissions, secrets, médias et organisations restent produits.
Les forges et appareils réels doivent confirmer chaque adoption. Aucun usage
CHRS réel ou hébergement public n'est autorisé par la seule clôture technique.
Les certificats, SMTP et topologies réelles sont à vérifier chez l'exploitant.
La version 0.5.0 finale doit être publiée avant ses consommateurs ; garder
0.4.0 immuable. La suite #SOC7 dépendra des deux besoins métier constatés,
sans bibliothèque générique imposée pour documents ou organisations.
