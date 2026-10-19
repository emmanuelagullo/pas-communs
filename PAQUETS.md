# Paquets ZIP/SQLite — contrat actuel

## API

```python
from pas_communs.paquets import ProfilPaquet, creer_sauvegarde, preparer_restauration

profil = ProfilPaquet("mon-application", "mon-format-paquet", "base.sqlite3")
creer_sauvegarde(dossier, destination_zip, profil=profil)
preparation = preparer_restauration(source_zip, parent_temporaire, profil=profil,
    migrations_connues=ensemble_des_migrations)
```

L'application choisit le profil et les migrations connues ; elle contrôle les
droits, la confirmation et l'arrêt des écritures avant une activation.
`preparation.etape` est une copie vérifiée ; elle doit être supprimée si abandonnée.
`appliquer_restauration` n'est utilisable qu'après arrêt de l'application et de
ses connexions : il renomme l'ancien paquet et le conserve. Il ne gère ni serveur,
ni permission, ni migration, ni synchronisation. Les préconditions de concurrence
restent celles du lanceur ou du service appelant.

`iterer_restauration` partage le validateur, émet les phases ouvrir/fermer et
accepte `ouvrir_destination` pour les transferts OPFS. Il faut épuiser ou fermer
le générateur ; une interruption nettoie sa préparation. Les fichiers externes
se lisent par blocs ; les callbacks de destination gardent leurs contraintes.

`metadonnees` contient les renseignements propres à une projection métier.
Les champs format/version/application/files/created_at sont réservés au moteur.
Le socle n'interprète pas les exports d'école ou de classe et ne sélectionne
aucune donnée : les projections et leurs autorisations restent dans Petits Pas.

## Format et reprise

Version du format ZIP : 1. Les manifestes contiennent `application`, `format`,
`version`, `created_at`, et les SHA-256 des fichiers. Les formats historiques
sont conservés ; l'ajout de l'identité n'est pas un changement du format SQL.
L'identité est un contrôle de compatibilité, pas une signature d'authenticité.

| Application | Identité | Format | Base |
| --- | --- | --- | --- |
| Petits Pas | petits-pas | petits-pas-paquet | carnet.sqlite3 |
| Pas à Pas — Accompagnement | pas-a-pas-accompagnement | pas-a-pas-accompagnement-paquet | accompagnement.sqlite3 |

La façade Petits Pas accepte les anciens manifestes sans `application`, mais
uniquement avec son format historique. Un champ `application` explicite différent
est toujours refusé. Le profil CHRS exige ce champ. Le mauvais produit est refusé
avant création du dossier temporaire. Les anciens validateurs Petits Pas peuvent
lire les nouveaux ZIP dont les autres champs historiques sont inchangés.
Aucun renommage des dossiers OPFS, cookies, tables ou migrations n'est introduit.

## Contrôles et limites

Copie SQLite via `backup()`, intégrité SQLite, relations, migrations connues si
fournies, correspondance exacte au manifeste, empreintes, refus des liens
symboliques, chemins hors paquet et destinations répétées. Base ou clé source
manquante : refus sans créer de base vide. Limites par défaut : 10 Gio et
100 000 fichiers ; la PWA conserve ses limites applicatives plus strictes.

Les données et ZIP ne sont pas chiffrés. La clé appartient au paquet local,
pas aux secrets du serveur. La sélection ou neutralisation des secrets serveur
reste impérativement effectuée par l'exporteur métier, jamais par ce moteur.
Les médias doivent rester stables pendant l'export ; le moteur ne coordonne pas
les transactions SQL et les écritures de fichiers des autres processus.


## Portabilité renforcée (0.8.0)

Import et export refusent les chemins non portables : lecteur Windows, flux
NTFS, composant vide/dot, caractères interdits, nom réservé et suffixe point ou
espace. Les collisions de casse concernent aussi les répertoires, de même que
les conflits fichier/répertoire. Aucun renommage automatique : corriger une
source atypique explicitement après diagnostic. Les noms ordinaires, accents,
formats ZIP/SQL et archives historiques conformes sont conservés.

Tous les noms d'une archive sont contrôlés avant de créer la préparation. Les
médias natifs et externes sont contrôlés avant d'ouvrir la destination ZIP ; un
export refusé pour son nom ne détruit donc pas une destination existante. Le
moteur n'ajoute pas de politique générale d'écrasement : les produits conservent
leur réservation exclusive et leurs confirmations.
