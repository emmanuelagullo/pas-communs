# Contrats actuels et frontières des produits

## Deux produits indépendants

| Sujet | Contrat |
| --- | --- |
| Métier | Modèles, migrations, écrans et permissions restent dans chaque application. |
| Identité | Partager un mécanisme de connexion n'implique ni comptes communs ni SSO. |
| Exécution | Serveur, bureau et navigateur exécutent le code métier de leur application, avec des adaptateurs propres à chaque mode. |
| Données | Bases, médias, secrets, répertoires et espaces navigateur propres à chaque produit. |
| Sauvegarde | Le format ZIP livré identifie le produit ; une archive étrangère est refusée avant extraction. Le profil Petits Pas accepte explicitement son format historique sans identité. |
| Compatibilité | Conserver les archives et noms historiques de Petits Pas ; prévoir une reconnaissance explicite, sans renommage global. |
| Publication | Chaque produit adopte et valide sa version épinglée ; les versions peuvent différer durablement. |

Le socle ne doit importer aucun modèle métier. Les applications appellent le
socle et lui fournissent les décisions métier nécessaires par des fonctions
explicites, uniquement lorsque l'extraction en établit le besoin.

## Mécanismes disponibles

Le socle 0.8.0 est publié : paquets SQLite, runtime et construction bureau,
installateur Windows, primitives d'authentification, stockage navigateur,
contrat HTTPS, recettes et validateurs de publication, moteurs PDF facultatifs.
Les contrats détaillés sont PAQUETS.md, LOCAL.md, AUTHENTIFICATION.md, PWA.md,
SERVEUR.md, CI-PUBLICATION.md, PDF.md et PUBLICATION.md. QUALIFICATION.md décrit
les vérifications ; JALONS.md retrace les étapes historiques.

Le moteur de paquets traite SQLite et médias, pas une sauvegarde PostgreSQL.
L'export d'une projection scolaire et ses autorisations restent dans Petits Pas.
Les primitives TOTP ne stockent ni ne consomment les facteurs ; cette atomicité
reste dans les produits. Coques PWA, modèles et parcours ne sont pas mutualisés.
Aucun choix de base serveur ou de rôle social ne découle d'une API technique.

## Périmètre actuel du prototype CHRS

Connexion, accueil, liste paginée, création et consultation d'une personne.
Une désignation permet une identité provisoire ou incomplète ; prénom facultatif.
Identifiant technique stable, date de création et auteur. Aucun dossier social.

Le prototype représente un seul espace d'essai fictif. Aucune isolation entre
établissements n'est implémentée. Les comptes ayant le droit de consultation
voient toutes les personnes fictives de cet espace. Les permissions Django
`view_personne` et `add_personne` sont explicites ; être connecté ne suffit pas.
L'administration technique n'est pas un rôle social. Les commandes de
préparation créent des comptes ordinaires avec ces permissions explicites ;
un superutilisateur technique n'est pas requis pour le parcours d'essai.

Le modèle utilisateur CHRS est déclaré dès la première migration dans son propre
module `identites`, sans lien avec les personnes accompagnées. Il reste propre au produit. Éviter tout changement ultérieur improvisé
d'AUTH_USER_MODEL.

Ce périmètre n'autorise pas une mise en production avec des données réelles.
Les profils source, bureau, navigateur et serveur volontaire sont livrés,
avec sauvegardes SQLite, parcours TOTP serveur et export de fiche PDF. Cela ne
qualifie pas l'exploitation de dossiers réels. Les habilitations et modèles
sociaux restent à définir ; V0-METIER.md dans Pas à Pas décrit le cadrage CHRS1
fictif mono-espace. Le choix PostgreSQL serveur y reste un chantier distinct
(voir BASE-CIBLE.md dans l'application), sans changer les profils actuels.

## Cible métier à implémenter dans Pas à Pas

Personnes (adultes ou mineurs, identité éventuellement incomplète), ménages avec
appartenances datées, accompagnement social indépendant de l'hébergement,
prestations accordées et réalisations effectives distinctes, bénéficiaires
explicites. Première V0 métier limitée à l'hébergement et aux repas.

Un séjour est une période d'admission effective avec affectations successives
(chambre, place, logement, y compris partenaire extérieur). Une absence temporaire
ne clôt pas automatiquement le séjour. Situation sociale simple : valeurs datées,
événements et courts bilans ; pas de reconstruction générale par événements.
Source d'orientation « 115 / SIAO » et référence externe facultative seulement.
Hors V0 : appels du 115, synchronisation SI-SIAO, facturation, dossier médical,
moteur de formulaires et reporting réglementaire exhaustif.

## Décisions ouvertes, à prendre avant le code concerné

- Quel périmètre isole les données : gestionnaire, établissement, service ?
- Qui consulte et modifie une personne ou un accompagnement, et pendant combien de temps ?
- Comment présenter une personne dans plusieurs ménages, services ou établissements ?
- Quelles dates et unités utiliser pour les repas et les nuitées ?
- Quelles protections imposer aux données locales avant tout usage réel ?

Ces décisions ne bloquent pas le prototype fictif unique. Le cadrage déjà retenu
pour CHRS1 se trouve dans V0-METIER.md, pas dans une analogie scolaire. Ne pas déduire
les réponses des classes, années scolaires ou fonctions de Petits Pas.

## Sites publics

Le thème autonome Hugo et son contrat de consommation sont dans HUGO.md.
Cette ressource de construction est épinglée par commit Git dans les sites,
indépendamment du wheel Python. Les sites et contenus restent applicatifs.
