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

#SOC3 extrait le runtime local et l’assembleur PyInstaller ; voir LOCAL.md.
Les installateurs historiques Petits Pas restent propres au produit.

#SOC4a livre les primitives et leur première adoption ; voir AUTHENTIFICATION.md.
#SOC4b intègre le parcours renforcé CHRS, les secours, la récupération, les
limites et la révocation. Les modèles CHRS restent dans son dépôt et aucun
modèle TOTP commun n’est créé. Le parcours du prototype est testé ; ce jalon
ne qualifie pas le déploiement réseau de production, qui reste #SOC6.

#SOC5a livre les primitives navigateur du wheel 0.4.0 et un premier parcours
CHRS fictif hors connexion. Les coques et Workers restent dans les produits.
Voir PWA.md. #SOC5a ne clôt pas le moteur ; #SOC5b le complète ci-dessous.

#SOC5b clôt #SOC5 sur le périmètre Chromium/Linux automatisé : copies/restauration
CHRS, reprise et mise à jour ; les adaptateurs des produits restent distincts.
Les appareils terrain et autres navigateurs restent à qualifier. Aucun usage
CHRS réel n'est validé. La publication finale du candidat 0.4.0 précède les deux
applications ; #SOC6 pourra ensuite traiter les recettes serveur/CI/publication.

#SOC6a ajoute les profils serveur volontaires et le contrat HTTPS 0.5.0,
avec bancs WSGI fictifs dans les deux produits. Les profils historiques restent
inchangés. #SOC6b complète les recettes et bancs réseau ci-dessous ; aucun
déploiement ni dossier CHRS réel validé sous #SOC6a.

#SOC6b clôt #SOC6 : même recette Django dans les deux forges, primitives de
candidats adoptées par les deux produits et vrais échanges HTTP sur Gunicorn
local. La publication reste explicite par produit, avec 0.5.0 épinglée.
Les services PostgreSQL existants restent dans la CI Petits Pas ; leur résultat
distant et la chaîne TLS réelle restent à confirmer chez l'exploitant.

#SOC7a inventorie les extensions dans [EXTENSIONS.md](EXTENSIONS.md). Aucun
second usage CHRS d'images, documents ou traitements n'est encore implémenté :
aucune extraction ni nouvelle version du wheel n'est imposée. Développer les
parcours CHRS, puis ouvrir SOC7b seulement sur un besoin commun constaté.
SOC7 reste conditionnel ; ce cadrage ne qualifie pas la production CHRS.

#SOC7b : [PDF.md](PDF.md) décrit le moteur WeasyPrint adopté par les deux
produits et le backend texte facultatif pour l'export PWA CHRS. Les templates,
droits et politiques restent métier. Version 0.6.0 distincte de 0.5.0 ; aucun
modèle, format de paquet ou stockage existant déplacé.

#SOC3b : version 0.7.0, installateur Windows Inno Setup et banc PowerShell
communs aux deux produits. Conserver les identités historiques de Petits Pas ;
Pas à Pas dispose d’un setup propre et du ZIP portable. Voir LOCAL.md.


#AUD1–#AUD3 : 0.8.0 était candidate à la livraison ; elle est désormais publiée. Chemins ZIP portables dans les deux sens,
qualification conjointe avec provenance des octets, description cohérente du
runtime et validateurs de promotion sans accès réseau. Les politiques et
profils d'exploitation restent dans les produits ; voir QUALIFICATION.md.
