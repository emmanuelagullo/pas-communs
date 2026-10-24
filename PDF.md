# PDF partagés — contrat actuel

Les moteurs ont été introduits en 0.6.0 sous SOC7b ; leur version adoptée
reste celle de requirements-communs.txt dans chaque produit.
Le socle ne connaît ni personne, élève, modèle Django, template ou droit.
Les imports WeasyPrint, fpdf2 et FontTools sont paresseux ; le wheel n'impose
aucune dépendance obligatoire supplémentaire.

## Moteur natif

rendre_html(html, base_url=..., feuille_style=..., recuperer=...) reprend
l'appel WeasyPrint historique de Petits Pas : media_type print et feuille CSS
fournie par son chemin. recuperateur_medias reçoit une liste de noms autorisés,
un schéma privé, une fonction d'ouverture et, éventuellement, un récupérateur
pour les autres URL. Sans surcharge, le comportement WeasyPrint historique est
conservé ; il ne constitue pas une restriction générale du réseau/fichier.
Les façades Petits Pas gardent leurs signatures, stockage, autorisations et
options. Pas à Pas refuse les autres ressources pour sa fiche sans images.
Les modèles HTML/CSS et le nom du téléchargement restent dans les produits.

WeasyPrint/Pango reste dans les profils serveur/bureau qui en ont besoin.
Windows exige les DLL Pango collectées dans le programme ; le CHRS reprend le
mécanisme d'assemblage déjà utilisé par Petits Pas, avec sa propre variable.
Aucun moteur natif n'est importé lors du démarrage de la PWA.

Compatibilité WeasyPrint : `recuperateur_medias` importe `default_url_fetcher`,
retiré de l'API publique en WeasyPrint 70 (présent jusqu'en 69.0, version de la
sonde de `tests/application_minimale`). Un produit qui adopterait 70 ou plus doit
d'abord faire évoluer cette façade ; aucun produit n'est touché tant qu'il garde
sa version épinglée.

## PDF texte dans le navigateur

fiche_texte(titre, lignes) produit des octets PDF paginés via fpdf2 et la police
DejaVu Sans embarquée (licence dans polices/LICENCE-DejaVu.txt). Aucun HTML,
URL, réseau ou média n'est interprété. Les caractères absents de cette police
sont refusés explicitement ; ne pas remplacer silencieusement les identités.
Ce n'est pas une promesse de couverture de tous les systèmes d'écriture.
Le rendu texte ne remplace pas celui des carnets scolaires avec photos.

Le profil Pyodide CHRS charge Pillow du runtime épinglé et les wheels purs
fpdf2, FontTools et defusedxml ; tous sont embarqués, sans réseau à l'export.
Les tests vérifient les octets dans le vrai runtime et le téléchargement hors
ligne dans Chromium. La PWA Petits Pas garde son adaptation d'impression
existante : elle ne proposait pas un téléchargement WeasyPrint auparavant.

## Vérifier et publier

Installer requirements-tests-pdf.txt en plus des dépendances de construction
et d'authentification ; les tests unitaires vérifient l'API native par doublure,
les médias autorisés et le PDF texte réellement produit (Unicode, pagination).
Les vrais rendus natifs sont vérifiés dans les produits. Les bancs de carnets
et images Petits Pas restent indispensables ; ne pas déduire la compatibilité
Pango/Windows d'un test du PDF texte sous CPython.

Publier le wheel immuable 0.6.0 après CI, puis adopter la même empreinte dans
les deux applications. Ne pas remplacer la release 0.5.0. Les polices incluses
ont leur licence propre ; le code reste AGPL-3.0-or-later.
