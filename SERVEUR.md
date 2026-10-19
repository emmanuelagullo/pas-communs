# Profils serveur explicites — contrat actuel

Introduite avec la version 0.5.0, l’API `configuration_https` fournit un contrat : validation d'une clé stable,
d'hôtes exacts et d'origines CSRF HTTPS, puis réglages Django communs. Aucun
import Django, modèle, fichier de données ou accès réseau dans cette fonction.
Les deux applications la sélectionnent dans un nouveau module `settings_serveur`.
Les profils historiques, de bureau et PWA restent inchangés et disponibles.

## Contrat

- Clé d'au moins 50 caractères, diversité minimale et sans préfixe Django de
  développement. Ces contrôles ne prouvent pas l'aléa : générer une vraie clé
  aléatoire stable et la conserver hors Git.
- Hôtes explicites sans URL, port, joker ou suffixe générique ; origines HTTPS
  exactes sans chemin, identifiant utilisateur, fragment ou joker.
- DEBUG désactivé, redirection HTTPS, cookies de session/CSRF Secure, session
  HttpOnly, anti-sniffing et interdiction d'iframe. Durées et politiques de
  sessions, droits et modèles restent propres aux produits.
- Aucun X-Forwarded-Host. X-Forwarded-Proto n'est accepté qu'après choix explicite
  du déployeur (`proxy_https=oui`). Cela suppose un backend inaccessible au
  public et un proxy qui remplace cet en-tête : le module ne crée pas ce réseau.
- HSTS limité par défaut à 3 600 secondes, sans sous-domaines ni preload.
  La valeur 0 permet une phase de préparation ; elle produit un avertissement
  Django. Ne pas imposer HSTS à d'autres services du domaine par analogie.

Le contrôle ne choisit ni base, ni adresse IP cliente, ni SMTP, ni stockage des
médias, ni hébergeur. Les réglages produit gardent ces décisions. La confiance
au proxy HTTPS ne crée aucune confiance dans X-Forwarded-For : contrôler
séparément l'adresse vue par les limites d'authentification.

## Qualifier

Construire/installer le wheel puis lancer les tests habituels et ceux de
`test_serveur.py`. Chaque produit fournit `scripts/verifier-profil-serveur.py` :
base et clé fictives temporaires, migrations, collectstatic, check --deploy,
WSGI Django avec vérification des redirections, Host, cookies, CSRF et refus
des configurations ambiguës. Le banc ne lance aucun service public.

`check --deploy --fail-level ERROR` ne supprime pas les avertissements Django :
les recommandations de sous-domaines/preload HSTS ne sont pas activées de façon
implicite pour rendre ce contrôle vert. Le déployeur les examine selon son domaine.
Le banc WSGI vérifie le contrat applicatif ; il ne qualifie pas un certificat
public, une chaîne de reverse-proxys ni un hébergement donné.

#SOC6b complète ce contrat avec les recettes et candidats partagés, ainsi
qu'un banc HTTP Gunicorn local. Lire CI-PUBLICATION.md pour la clôture et
ses limites (TLS réel et résultats distants à confirmer).
Le CHRS reste réservé aux données fictives et à un espace unique.
