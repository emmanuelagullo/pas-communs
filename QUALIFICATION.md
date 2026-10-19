# Qualification conjointe du socle et des consommateurs

La recette n'installe rien, ne publie rien et ne déploie rien. Elle requiert les
dépendances de construction/tests du socle et celles des deux profils serveur,
PDF et 2FA dans l'environnement choisi. Les profils CHRS restent explicites :
ne pas les fusionner pour cette recette. Sous Guix, utiliser l'environnement
de développement contenant ces dépendances ; aucun pip local n'est imposé.
Un environnement contenant Gunicorn/Pango permet ensuite les bancs serveur.

## Candidat reproductible et provenance

Depuis pas-communs, construire avec le backend épinglé dans pyproject.toml :

```sh
python3 scripts/construire-wheel.py
```

Le script construit deux fois et exige les mêmes octets. Une construction
Guix avec d'autres versions d'outils peut être utile au développement mais ne
doit pas être supposée identique au candidat CI. Comparer SHA256SUMS.

Pour tester sans installer le wheel, l'extraire dans un **dossier neuf** privé :

```sh
qualification_dir=$(mktemp -d)
python3 -m zipfile -e dist/pas_communs-0.8.0-py3-none-any.whl "$qualification_dir"
PYTHONPATH="$qualification_dir${PYTHONPATH:+:$PYTHONPATH}" python3 -m pas_communs.qualification \
  --wheel dist/pas_communs-0.8.0-py3-none-any.whl --socle . \
  --petits-pas ../petits-pas --accompagnement ../pas-a-pas-accompagnement
```

Adapter les chemins à l'arborescence réelle. Un wheel déjà installé convient
aussi ; ne pas laisser un PYTHONPATH masquer le candidat par une autre version.
La recette compare **tous** les fichiers Python et ressources importés aux
octets du wheel, et son SHA-256 aux deux requirements-communs.txt. Elle refuse
les fichiers supplémentaires. Elle affiche version, empreinte, chemin importé,
commits des trois dépôts et présence de modifications locales. `--rapport`
permet d'enregistrer ce relevé sans données métier. Le chemin importé indique
explicitement si l'on utilise une installation, une extraction ou les sources.

## Couverture et suite

La recette exerce tests du socle et authentification neutre, anciennes archives
Petits Pas, refus de promotion et concurrence TOTP sur SQLite fichier, puis
checks, migrations attendues, tests Django et publications simulées CHRS.
Les bases des parcours Django de cette recette sont temporaires ; ne pas fournir
de secrets ou de configuration d'instance. Aucun appel de publication réel.

Compléter par `node --test tests/test_navigateur.mjs`, les tests Django complets
Petits Pas dans sa matrice et les bancs serveur des deux produits. Les CI des
produits qualifient les mêmes dépendances épinglées, les vrais Pyodide/Chromium,
les archives Linux/Windows et le setup. Un résultat local n'est pas une preuve
de qualification graphique, d'appareil PWA, de TLS ou d'exploitation serveur.

Publier une nouvelle version immuable du socle seulement après ces contrôles,
puis vérifier l'empreinte publique avant de pousser les consommateurs. Les
tags et versions applicatifs restent indépendants. Les déploiements serveur
conservent leurs procédures : cette adoption n'exige aucun nouveau réglage.
