# Extensions justifiées — #SOC7a

## Mise à jour après SOC7b et AUD

L'inventaire ci-dessous est historique (SOC6b). Depuis SOC7b, le CHRS dispose
d'une fiche PDF : les appels natifs sont partagés dans pas_communs.pdf et le
backend texte PWA reste facultatif. Le socle prépare 0.8.0 ; son adoption réelle
reste fixée par les requirements des consommateurs. Cet ajout ne justifie
aucune GED, politique d'image ou infrastructure de tâches commune.

## Décision à l'issue de SOC6b (historique)

Ne pas extraire de composant supplémentaire pour l'instant. Les mécanismes
nécessaires aux deux produits (paquets, exécution locale, authentification,
stockage navigateur, profils HTTPS, recettes CI et candidats de publication)
sont disponibles en 0.5.0. Le prochain besoin commun doit être démontré par
un parcours CHRS, plutôt que déduit des fonctions scolaires.

Ce cadrage ne clôt pas toutes les extensions possibles de SOC7. Il clôt son
inventaire initial ; les extractions suivantes sont conditionnelles. Aucune
nouvelle version du wheel ni modification des empreintes n'est nécessaire.

## État observé et candidats

Audit des arbres SOC6b : pas-communs c77e642, Pas à Pas 83bd999 et Petits Pas
2762d39. Ce sont les bases de cette livraison, pas une affirmation sur les
branches distantes qui peuvent continuer d'évoluer.

| Sujet | État Petits Pas | État Pas à Pas | Décision / déclencheur |
| --- | --- | --- | --- |
| Images privées | `suivi/services/medias.py` décode, oriente, nettoie et réduit JPEG/PNG/WebP ; `medias_django.py` adapte le résultat aux fichiers Django. | Aucune saisie de fichier dans les vues personnes. | Garder dans Petits Pas. Extraire seulement si un parcours CHRS exige réellement la même transformation. |
| Documents joints | Les médias scolaires sont liés aux traces et à leur présentation ; ils ne constituent pas une GED universelle. | Ni modèle ni parcours documentaire. | Définir d'abord type, rattachement, droits, conservation et nécessité de garder l'original. |
| PDF produits | `_generer_pdf` et `_recuperateur_pdf` dans `suivi/views.py` utilisent WeasyPrint, le stockage et une liste de médias autorisés. | Aucun document à produire. | Attendre un document CHRS défini. Un appel commun à WeasyPrint seul ne justifie pas une nouvelle couche. |
| Traitements différés | `ExportTemporaire`, `ExportEcole`, `ExportClasse`, `exports_ecole.py` et `imports_ecole.py` portent des états et décisions scolaires. | Aucun travail métier différé. | Ne pas copier les tables, ajouter de file ou imposer Celery. Extraire une mécanique seulement après un second traitement concret. |
| Audit technique/métier | `EvenementAudit` est rattaché à une école et à un acteur ; `suivi/audit.py` est appelé explicitement par les services. | Date et auteur de création de personne ; pas de journal métier durable. | Créer les événements nécessaires au CHRS dans son propre modèle ; pas de FK générique ou de journal partagé par analogie. |
| Chronologie sociale | Les observations pédagogiques et leurs dates ont leur propre sens. | Pas encore d'accompagnement ni de situation sociale. | Historique métier CHRS, distinct du journal des modifications. Pas de reconstruction générale par événements. |
| Organisations et droits | Écoles, classes, années et fonctions, avec contrôles applicatifs. | Espace fictif unique ; permissions explicites de lecture/création. | Définir le périmètre CHRS avant toute isolation. Ne pas renommer école en structure ou classe en service. |

Le traitement des images scolaires conserve un JPEG normalisé et ne conserve
pas le brut. Un éventuel justificatif social peut demander une autre politique :
sa lisibilité et son original ne peuvent pas être sacrifiés par héritage du
profil scolaire. Ce besoin reste à établir, aucun justificatif n'est ajouté ici.

Le récupérateur PDF Petits Pas contrôle les médias de son schéma privé ; ses
autres URL sont déléguées au récupérateur WeasyPrint. Ce constat n'est pas un
audit complet des entrées HTML ni une qualification de son utilisation pour
un nouveau métier. Ne pas promettre une politique commune de ressources à
partir de cet adaptateur.

## Conditions d'une extraction suivante

Avant de créer une API commune :

1. Disposer d'un parcours utile dans chaque produit, avec exemples fictifs et
   décisions propres à chacun. Une simple possibilité future ne suffit pas.
2. Identifier la mécanique réellement identique, ses entrées et ses sorties.
   Les seuils, droits, modèles, migrations, textes et choix de conservation
   restent dans les produits. Ne pas faire entrer les mots trace, couverture,
   école ou accompagnement dans une nouvelle API technique commune.
3. Comparer le coût de l'extraction à celui de deux petits adaptateurs. Conserver
   les adaptateurs si le partage n'apporte pas de correction ou de test utile.
4. Préserver les façades et le comportement Petits Pas, exercer le composant
   neutre et les deux usages, puis qualifier les modes réellement concernés.
5. Ajouter les bibliothèques lourdes uniquement aux profils qui les utilisent.
   Ne pas rendre Pillow, WeasyPrint/Pango ou une file de tâches obligatoires
   pour importer le socle, démarrer le CHRS ou construire sa PWA.
6. Publier une nouvelle version immuable uniquement si le wheel change, puis
   adopter son empreinte dans chaque consommateur. Ne pas retoucher 0.5.0.

La compatibilité Pyodide d'un nouveau moteur ou d'une dépendance native doit
être exercée dans le navigateur ; une réussite CPython ne la démontre pas.
Préserver aussi anciennes archives, ressources et espaces OPFS si concernés.

## Suite de développement

Développer désormais les parcours CHRS dans son dépôt. Le document
`V0-METIER.md` de Pas à Pas propose les tranches, leurs décisions ouvertes et
leurs critères d'acceptation. Il ne crée pas de fonction accessible.

SOC7b pourra être ouvert lorsqu'une tranche révèle un second usage concret
(images, documents ou traitements). Si aucune extraction n'est justifiée, le
socle reste en 0.5.0 et le développement métier peut continuer indépendamment.
La qualification de production CHRS demeure distincte : l'espace fictif unique
n'établit ni les habilitations d'équipe ni une isolation entre établissements.
