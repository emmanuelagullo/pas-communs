# Pas communs

Le socle technique de **Petits Pas** et de **Pas à Pas — Accompagnement**.

#SOC2 introduit le paquet Python `pas-communs` / module `pas_communs`, version
`0.1.0`. #SOC3 le complète avec la version `0.2.0` : exécution locale et
assemblage PyInstaller communs. Premier composant : moteur de paquets ZIP réunissant SQLite, clé et
médias. Python pur, bibliothèque standard uniquement, sans Django ni modèle métier.

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
python -m pip install --no-deps dist/pas_communs-0.2.0-py3-none-any.whl
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
