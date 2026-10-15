# Frontières retenues pour #SOC1

## Deux produits indépendants

| Sujet | Contrat |
| --- | --- |
| Métier | Modèles, migrations, écrans et permissions restent dans chaque application. |
| Identité | Partager un mécanisme de connexion n'implique ni comptes communs ni SSO. |
| Exécution | Serveur, bureau et navigateur embarqueront le même code métier de leur application. |
| Données | Bases, médias, secrets, répertoires et espaces navigateur propres à chaque produit. |
| Sauvegarde | Le futur format identifie le produit ; refuser une archive de l'autre application avant écriture. |
| Compatibilité | Conserver les archives et noms historiques de Petits Pas ; prévoir une reconnaissance explicite, sans renommage global. |
| Publication | Une version du socle est adoptée et validée séparément par chaque produit. |

Le socle ne doit importer aucun modèle métier. Les applications appellent le
socle et lui fournissent les décisions métier nécessaires par des fonctions
explicites, uniquement lorsque l'extraction en établit le besoin.

## Périmètre du prototype CHRS

#SOC1 : connexion, accueil, liste paginée, création et consultation d'une personne.
Une désignation permet une identité provisoire ou incomplète ; prénom facultatif.
Identifiant technique stable, date de création et auteur. Aucun dossier social.

Le prototype représente un seul espace d'essai fictif. Aucune isolation entre
établissements n'est implémentée. Les comptes ayant le droit de consultation
voient toutes les personnes fictives de cet espace. Les permissions Django
`view_personne` et `add_personne` sont explicites ; être connecté ne suffit pas.
L'administration technique n'est pas un rôle social. Le superutilisateur de
Django sert seulement à préparer le compte de démonstration en ligne de commande.

Le modèle utilisateur CHRS est déclaré dès la première migration dans son propre
module `identites`, sans lien avec les personnes accompagnées. Il n'est pas
encore mutualisé. Éviter tout changement ultérieur improvisé d'AUTH_USER_MODEL.

Ce périmètre n'autorise pas une mise en production avec des données réelles.
Le profil livré est un serveur de développement en boucle locale. Authentification
renforcée, sauvegardes, exploitation et habilitations métier restent à intégrer.

## Cible métier après #SOC1

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

Ces décisions ne bloquent pas l'espace fictif unique de #SOC1. Ne pas déduire
les réponses des classes, années scolaires ou fonctions de Petits Pas.
