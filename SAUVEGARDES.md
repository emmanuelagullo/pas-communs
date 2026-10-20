# #SOC — harmonisation des sauvegardes locales

## Comparaison avant changement

Les deux produits ont déjà le même moteur ZIP version 1, avec SQLite, clé,
manifestes SHA-256 et médias. L'identité/format/base restent propres au produit.
Petits Pas est la référence : validation dans une préparation, confirmation,
arrêt HTTP puis connexions fermées, remplacement avec état précédent conservé.
La PWA active un pointeur OPFS transactionnel dans un Worker séparé.

Pas à Pas limitait son adaptateur PWA aux deux fichiers base/clé, donc refusait
un ZIP natif contenant des médias pourtant autorisés par le moteur. Le programme
natif n'exposait pas le parcours de remplacement. Les commandes restauraient
uniquement un nouveau dossier, et restent utilisables avec le même contrat.

## Plus petite harmonisation

0.9.0 ajoute `RestaurationLocale`, extraction de l'état de préparation/confirmation
Petits Pas, et `vider_tables_copie(base, tables)`, mécanisme SQLite sans modèle
ni choix de table. Les façades produits gardent les décisions : sessions Django
pour Petits Pas ; sessions et compteurs d'authentification pour Pas à Pas.
Les clés locales, mots de passe hachés, UUID, FK, M2M, permissions et facteurs
TOTP restent dans le ZIP privé. Aucun secret SMTP ou clé de chiffrement TOTP
externe au paquet n'est ajouté ; aucun facteur inscrit n'est déprotégé.

Les ZIP historiques, formats et noms publiés restent inchangés. Une sauvegarde
locale complète n'est ni une projection serveur ni un jeu de démonstration :
elle reste privée. Produire une démonstration distribuable demanderait un jeu
fictif construit séparément ; ne jamais redistribuer un ZIP privé « nettoyé ».

Pas à Pas conserve son adaptateur simple : ZIP et contenu décompressé au plus
64 Mio, 5 000 entrées manifeste compris, clé 64 Kio. Les médias opaques sont
conservés ; aucune fonctionnalité de pièces jointes métier n'est ajoutée.
Les transferts volumineux OPFS de Petits Pas restent propres à son parcours.
Les plafonds historiques de Petits Pas ne changent pas.

## Qualification et adoption

Publier le nouveau wheel immuable 0.9.0 après vérification, puis vérifier son
SHA-256 public, ensuite appliquer/pousser les deux adoptions applicatives.
Ne modifier ni le tag ni les octets de 0.8.0 et des programmes déjà publiés.
Les nouvelles PWA/programmes doivent être construits et qualifiés séparément.
Aucune commande d'exploitation serveur ni configuration d'instance ne change.

Socle : wheel reproductible installé, unittest, tests d'authentification Django
neutre et Node. Petits Pas : tests des paquets et témoins historiques, aperçus,
restaurations Django et banc PWA existant. Pas à Pas : suite Django, contrôles
migrations, banc Pyodide (PWA → CLI native → PWA avec CHRS1–4 et média), puis
banc Chromium aux deux chemins, avec refus, annulation, sauvegarde précédente,
interruption avant/après commit et restauration native.
Les workflows de programmes gardent Ubuntu/Windows et le setup. Exécuter aussi
le parcours interactif téléchargement/restauration/redémarrage sur les systèmes
cibles ; CPython Linux ne prouve pas WebView2/Windows.
