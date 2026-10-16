# Authentification — première extraction #SOC4a

Pas communs 0.3.0 fournit des mécanismes ; chaque produit garde ses comptes,
modèles, migrations, relations et décisions d’accès. Aucun SSO, compte commun,
rôle générique ou correspondance école/CHRS n’est introduit.

## Périmètre effectivement livré

| Module | Usage | Frontière |
| --- | --- | --- |
| `authentification.mots_de_passe` | Plafond de 1 024 caractères avant hachage et validateur de création | Ne choisit pas les droits, la longueur minimale ou la politique de récupération. |
| `authentification.totp` | Chiffrement Fernet avec rotation, URI et QR, calcul/vérification des pas, format et empreinte des codes de secours | Ne stocke et ne consomme rien, n’authentifie personne, ne limite pas les tentatives. |
| `authentification.sessions` | Connexion récente, attente avant second facteur, fermeture ciblée des sessions DB | Ne décide pas qui doit utiliser le 2FA ou qui peut révoquer une session. |

Les clés de chiffrement et l’émetteur TOTP sont des arguments explicites.
Le socle ne lit aucun secret global ni variable d’environnement d’un produit.
Les importations de cryptography, django-otp et qrcode restent paresseuses.
Django n’est importé que par les modules et fonctions qui l’emploient.
Le wheel ne déclare aucune dépendance obligatoire supplémentaire ; les profils
applicatifs doivent installer les dépendances des fonctions effectivement utilisées.

`verifier_pas` renvoie un numéro de pas ou `None`. Il ne garantit l’absence de
rejeu que si le produit verrouille son enregistrement et persiste ce pas dans
la même transaction que sa consommation. Petits Pas conserve précisément son
stockage et ses transactions existants. Les codes de secours ne doivent jamais
être conservés en clair : seules leurs empreintes sont stockées par le produit,
avec consommation atomique. Le test neutre n’est pas une application exploitable.

## Sessions et compatibilité

Le backend de plafond ne connecte personne. Il précède le backend standard,
dont le chemin mémorisé par Django reste inchangé. Les façades historiques
`comptes.validators` et `comptes.backends` restent disponibles dans Petits Pas.
Les sessions déjà authentifiées restent lisibles ; aucun changement des tables,
formats de mot de passe ou noms des cookies Petits Pas.

L’attente avant second facteur tourne la clé de session sans appeler `login()`.
Elle expire après cinq minutes et lie le compte à son backend et à l’empreinte
d’authentification de son mot de passe. Avant le code, le backend doit encore
être autorisé et restituer un compte actif avec la même empreinte.
Un changement de mot de passe, une désactivation ou un retrait du backend
oblige donc à recommencer la connexion. Les anciennes attentes sans empreinte
sont abandonnées une seule fois lors de la mise à jour ; les sessions déjà
connectées ne sont pas concernées. L’appelant reste responsable du contrôle des
tentatives, de la consommation du code, de l’effacement de l’attente et du login.

`fermer_sessions_compte` ne traite que le backend de sessions Django en base.
Un autre stockage est refusé explicitement. Cette opération ne remplace pas
une réinitialisation du mot de passe ni les contrôles du second facteur.
Les durées de session, l’expiration, les cookies et la politique HTTPS restent
fixés par chaque application et chaque profil d’exécution.

## Adoption

Petits Pas emploie les primitives via ses façades, conserve ses tables TOTP,
les politiques par fonction scolaire, les écrans, les limites de tentatives,
les obligations et les parcours de secours. Le bureau et la PWA gardent leur
politique existante : cette extraction n’y active pas le 2FA.

Pas à Pas — Accompagnement utilise le plafond et la fermeture ciblée des sessions.
Ses noms de cookies sont propres au produit dans les profils source et bureau.
La commande technique n’ajoute aucune permission métier. Le CHRS n’a pas encore
d’inscription TOTP, d’obligation 2FA ou de récupération de compte accessible.
Aucun modèle TOTP commun ou CHRS n’est créé pour anticiper ces parcours.

## Suite #SOC4b

Avant de considérer #SOC4 terminé : intégrer dans le CHRS le parcours de connexion
renforcé, l’inscription et la récupération, avec limitation des tentatives et
journalisation ; qualifier les durées, cookies et déploiements. Déterminer qui
peut exiger/réinitialiser le second facteur et quelles sessions doivent être
révoquées, sans inventer des fonctions sociales à partir des rangs scolaires.
Le prototype CHRS reste réservé aux données fictives. Ces décisions et tests
ne sont pas remplacés par la seule présence des primitives dans le wheel.

## Vérifier

Installer le wheel et les dépendances de `requirements-tests-auth.txt`, puis :

```sh
python -m unittest discover -s tests
python tests/verifier_authentification_django.py
```

Les tests crypto sont optionnels sans dépendances, mais obligatoires dans les
CI du socle. L’application neutre emploie les comptes et sessions Django sans
modèle métier. Rejouer ensuite les tests TOTP, accès, récupération, mots de passe,
serveur et PWA de Petits Pas, ainsi que les droits et sessions du CHRS.
