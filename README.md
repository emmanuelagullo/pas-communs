# Pas communs

Bibliothèque technique embarquée de **Petits Pas** et de **Pas à Pas —
Accompagnement**. Aucun service central, compte commun ou modèle métier partagé.

## État courant

**0.8.0 est publiée** et les deux applications l'adoptent au 20 octobre 2026.
Ses octets et son tag sont immuables. Les adoptions effectives se lisent dans
le requirements-communs.txt de chaque produit (URL et SHA-256), pas dans les
numéros des anciens jalons. Les applications peuvent adopter des versions
différentes : une coévolution se qualifie, elle ne force pas un alignement
permanent. Une correction documentaire seule ne demande pas de nouveau wheel.

| Mécanisme livré | Contrat / lecture |
| --- | --- |
| ZIP/SQLite, empreintes, préparation de restauration | [PAQUETS.md](PAQUETS.md) |
| Runtime bureau, assembleur et setup Windows | [LOCAL.md](LOCAL.md) |
| Primitives mots de passe, TOTP et sessions | [AUTHENTIFICATION.md](AUTHENTIFICATION.md) |
| Stockage navigateur, transport et ressources embarquées | [PWA.md](PWA.md) |
| Contrat HTTPS explicite | [SERVEUR.md](SERVEUR.md) |
| Recettes CI, manifestes et contrôles de promotion | [CI-PUBLICATION.md](CI-PUBLICATION.md) |
| Rendu PDF natif et backend texte facultatif | [PDF.md](PDF.md) |

Les modèles, migrations, droits, textes et décisions de publication restent
applicatifs. Commencer par [CONTRATS.md](CONTRATS.md), puis le contrat concerné.
[JALONS.md](JALONS.md) et [EXTENSIONS.md](EXTENSIONS.md) conservent la chronologie
des extractions ; ils ne remplacent pas l'inventaire actuel ci-dessus.
[PUBLICATION.md](PUBLICATION.md) décrit l'adoption et l'immutabilité ;
[QUALIFICATION.md](QUALIFICATION.md) décrit les vérifications conjointes.

## Développer sans publier

Sous Guix, conserver les dépendances de l'environnement. Depuis l'une des
applications (dépôts frères dans cet exemple) :

```sh
export PYTHONPATH="$(realpath ../pas-communs/src)${PYTHONPATH:+:$PYTHONPATH}"
python3 -c 'import pas_communs; print(pas_communs.__file__)'
```

Les essais de distribution utilisent les octets du wheel adopté ou candidat,
comme décrit dans QUALIFICATION.md. Une source locale ne remplace pas une
adoption épinglée. Hors Guix, une installation éditable dans un environnement
isolé reste possible, jamais pour une distribution publiée :

```sh
python -m pip install -e ../pas-communs --no-build-isolation
```

## Construire une future version et vérifier

Le paquet accepte Python >=3.10. Les outils sont qualifiés en CI sous Python
3.12, 3.13 et 3.14, avec Windows/Python 3.12 en complément. Le constructeur de
PWA est applicatif : Python hôte >=3.12, distinct de Python 3.14.2 embarqué
dans le runtime Pyodide 314.0.7 actuellement sélectionné par les produits.

Pour une évolution du code ou des ressources, préparer une nouvelle version
immuable avec le backend épinglé dans pyproject.toml. Le script suivant construit
deux fois et exige les mêmes octets ; dist/SHA256SUMS en donne l'empreinte :

```sh
python3 scripts/construire-wheel.py
```

Fournir les dépendances de requirements-construction.txt par l'environnement
choisi. Pour une simple évolution documentaire de main, **ne pas reconstruire
et republier 0.8.0** : son README entre aussi dans les métadonnées du wheel.
Reproduire une release exige son tag exact, jamais un main documentaire ultérieur.
Les tests du code inchangé peuvent utiliser le wheel public 0.8.0, avec les
dépendances de requirements-tests-auth.txt et requirements-tests-pdf.txt :

```sh
python3 -m unittest discover -s tests
python3 tests/verifier_authentification_django.py
node --test tests/test_navigateur.mjs
```

QUALIFICATION.md précise comment vérifier les octets réellement importés et
les consommateurs concernés. Les bancs des produits restent indispensables :
une CI du socle verte ne qualifie ni leurs appareils, ni leurs déploiements.

Aucun réseau n'est nécessaire au fonctionnement autonome après distribution.
Les dépendances lourdes restent facultatives et propres aux profils utilisateurs.
Code et documentation : AGPL-3.0-or-later, voir [LICENSE](LICENSE).

Le code prépare **0.10.2**, non publié par ce patch (0.10.0 et 0.10.1 sont publiées et immuables) : un seul
HarfBuzz chargé pour le PDF macOS quand un autre paquet embarque le sien, en plus de l'alerte de
démarrage, du nom affiché et des programmes macOS arm64 non
signés (identification du système, emplacement des données, bundle `.app` et DMG).
Voir [LOCAL.md](LOCAL.md). Les consommateurs restent sur leur wheel adopté
(requirements-communs.txt, 0.9.0 pour l'instant) tant que 0.10.0 n'est pas publié
immuablement ; 0.9.0 reste immuable. État de restauration extrait de Petits Pas
depuis 0.9.0 : voir [SAUVEGARDES.md](SAUVEGARDES.md).

## Sites publics Hugo

Le thème commun des deux applications se trouve dans `hugo/pas/`.
Il se consomme par sous-module Git épinglé, sans changer le wheel Python.
Lire [HUGO.md](HUGO.md) pour les frontières et la qualification des deux sites.
