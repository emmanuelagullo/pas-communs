# Pas communs

Le socle technique de **Petits Pas** et de **Pas à Pas — Accompagnement**.

#SOC2 introduit le paquet Python `pas-communs` / module `pas_communs`, version
`0.1.0`. #SOC3 le complète avec la version `0.2.0` : exécution locale et
assemblage PyInstaller communs. Premier composant : moteur de paquets ZIP réunissant SQLite, clé et
médias. Ce moteur reste en Python pur et bibliothèque standard uniquement,
sans Django ni modèle métier. Les modules d’authentification #SOC4a emploient
Django et les dépendances crypto seulement dans les profils qui les utilisent.

- [Exécution et assemblage locaux](LOCAL.md)
- [Contrat du moteur et compatibilité](PAQUETS.md)
- [Publication et adoption](PUBLICATION.md)
- [Frontières métier](CONTRATS.md)
- [Jalons](JALONS.md)

## Développer sans publier

Depuis le dépôt de l'une des applications, avec son environnement Python activé :

```sh
python -m pip install -e ../pas-communs --no-build-isolation
```

Le backend de construction indiqué dans `pyproject.toml` doit être installé ;
au besoin installer au préalable `../pas-communs/requirements-construction.txt`.
Ne pas utiliser une installation éditable pour une distribution publiée.

## Construire et vérifier

Python 3.12 ou plus récent pour les outils (module `tomllib`) ; le moteur
lui-même accepte Python 3.10 ou plus récent, dont Python 3.14/Pyodide.

```sh
python -m pip install -r requirements-construction.txt
python scripts/construire-wheel.py
python -m pip install --no-deps dist/pas_communs-0.5.0-py3-none-any.whl
python -m unittest discover -s tests
python -m pip check
```

Le script construit deux fois avec le même environnement et refuse une
différence d'octets. Les horodatages ZIP sont fixés ; `dist/SHA256SUMS` contient
l'empreinte du wheel. Aucune publication PyPI n'est nécessaire.
Les tests s'exécutent depuis le wheel installé, sans importer le dossier `src`.
GitLab vérifie Linux/Python 3.12, 3.13 et 3.14 ; GitHub ajoute Windows/Python 3.12.
Les plateformes applicatives restent qualifiées dans chaque produit.

Aucun service supplémentaire : le paquet est installé avec les dépendances des
applications, inclus par PyInstaller et livré dans les wheels du bundle PWA.
Il n'exige aucun réseau à l'utilisation sur les appareils autonomes.

Code et documentation : AGPL-3.0-or-later, voir LICENSE. Le moteur est extrait
de Petits Pas ; les principes d'autorisation et le métier restent dans les applications.

## Première extraction d’authentification (#SOC4a)

La version 0.3.0 ajoute les primitives de mot de passe, TOTP et session.
Voir [AUTHENTIFICATION.md](AUTHENTIFICATION.md) pour leur contrat et les limites.
Aucun modèle utilisateur déplacé ; #SOC4 n’est pas terminé par cette extraction.

## Première extraction PWA (#SOC5a)

La version 0.4.0 ajoute les primitives navigateur et les ressources JavaScript
embarquées dans le wheel. Voir [PWA.md](PWA.md) pour le contrat, les frontières
et les étapes restantes. Node 24 sert aux tests JavaScript, pas à l'exécution
Django ou au programme de bureau. Le prototype CHRS reste fictif.

#SOC5b termine le candidat 0.4.0 avant sa première publication : copies et reprise
CHRS qualifiées, sans factorisation forcée des coques. Lire PWA.md et les
qualifications des produits. Ne pas employer le wheel candidat de #SOC5a avec
les nouvelles empreintes ; reconstruire/publier les octets finaux.

## Profils serveur explicites (#SOC6a)

La version 0.5.0 ajoute `pas_communs.serveur.configuration_https`, sans import
Django ni dépendance supplémentaire. Les deux produits l'adoptent dans des
profils volontaires distincts des réglages historiques, locaux et navigateur.
Lire SERVEUR.md et CI-PUBLICATION.md pour le complément #SOC6b.
La version 0.4.0 publiée reste immuable.

#SOC6b finalise 0.5.0 : recette Django commune aux forges, primitives d'identité
et d'intégrité des candidats, et banc HTTP Gunicorn local. Lire CI-PUBLICATION.md.
Aucun workflow distant mobile ou registre supplémentaire n'est requis. Les
décisions de déploiement/publication restent dans chaque produit.
