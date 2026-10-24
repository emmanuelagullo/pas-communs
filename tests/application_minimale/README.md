# Application minimale de qualification (#SOC3c)

Application WSGI sans métier ni donnée réelle, qui exerce la chaîne des programmes
de bureau du socle : `assembler`, `construire_bureau`, PyWebView, emplacement des
données, verrou, SQLite et, en option, le PDF natif et l'installateur Windows.
Elle n'est pas dans le wheel et ne remplace ni les tests ni les bancs des produits.

Elle est construite **à partir du wheel installé**, jamais depuis `src/` :

```
python -m pip install --no-deps dist/pas_communs-<version>-py3-none-any.whl
python -m pip install -r tests/application_minimale/requirements-bureau.txt
python tests/application_minimale/qualifier.py --version-attendue <version>
```

`qualifier.py` refuse un socle importé depuis `src/`. Sont **obligatoires** : la
construction et `--verifier-distribution` du programme gelé, l'extraction de
l'archive (zip, tar.gz ou DMG copié), la version embarquée, le dossier de données
hors du programme et la persistance d'un témoin entre deux lancements. Sont
**informatifs** (`--strict` les rend bloquants) : `--avec-fenetre` (vraie fenêtre
PyWebView), `--avec-pdf` (WeasyPrint), signature ad hoc macOS et, sous Windows,
`--avec-installateur`.

Linux exige PyGObject, GTK et WebKitGTK 4.1 d'Ubuntu : utiliser le Python du
système (`python3 -m venv --system-site-packages`), comme `.github/actions/bureau-minimal`.
Le workflow `programmes-minimaux.yml` l'exécute à chaque commit ;
`qualification-publication.yml` le rejoue sur le wheel téléchargé depuis la release.
