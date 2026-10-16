# Jalons du socle

| Jalon | Livrable | Critère d'acceptation |
| --- | --- | --- |
| #SOC1 | Cadrage et application CHRS minimale | Créer puis retrouver une personne fictive sans installer les modèles scolaires. |
| #SOC2 | Moteur des paquets et sauvegardes | Adoption par les deux produits, archives historiques Petits Pas lisibles, archives croisées refusées. |
| #SOC3 | Lanceur local et construction | Chaque produit démarre et conserve ses données séparément ; essais Linux et Windows. |
| #SOC4 | Authentification | Connexion, sessions et TOTP communs ; politiques et habilitations métier indépendantes. |
| #SOC5 | Moteur PWA | Deux distributions avec identités et stockages séparés, reprise et mise à jour qualifiées. |
| #SOC6 | Serveur, CI et publication | Recettes réutilisables et versions du socle épinglées par produit. |
| #SOC7 | Extensions justifiées | Images, documents et traitements selon les deux besoins constatés. |

## Méthode d'extraction

1. Définir le comportement à préserver dans Petits Pas à partir du code courant.
2. Extraire un composant avec ses tests, sans refonte incidente.
3. L'exercer depuis une petite application neutre et depuis les deux produits.
4. Tester les migrations et anciennes archives si le changement les concerne.
5. Construire une version immuable ; chaque application l'adopte explicitement.

Les modèles Django et leurs identités de migration ne se déplacent pas comme
un simple module Python. Préserver les noms de tables, les références et les
content types existants exige une stratégie et des essais dédiés. Commencer
par les services et outils qui n'exigent pas ce déplacement.

## CI du premier composant commun (#SOC2)

Tests unitaires du composant, application neutre, intégration des deux produits.
Les scénarios métier et la qualification de leurs distributions restent dans
les applications. Les recettes partagées sont épinglées ; une CI du socle verte
ne publie aucun produit. Corrections de sécurité : publier le correctif commun,
puis suivre son adoption dans chaque application maintenue.

## Livraison

Commits en français, sans Signed-off-by. Utiliser l’identité de commit
explicitement indiquée ; si elle n’est pas précisée, la demander avant de
créer les commits. Pour chaque dépôt, fournir un patch `git format-patch` applicable
avec `git am`. Ne créer aucun compte ou service à partir d’une URL supposée.
Référence : <https://gitlab.inria.fr/pas-communs/pas-communs> ;
miroir : <https://github.com/emmanuelagullo/pas-communs>.

#SOC2 fournit le moteur, les tests et la publication du wheel ; voir PUBLICATION.md
pour l’ordre d’adoption dans les deux applications. Aucun modèle Django déplacé.
