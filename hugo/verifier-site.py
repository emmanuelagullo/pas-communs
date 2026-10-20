#!/usr/bin/env python3
"""Contrôler le HTML Hugo, les liens et ancres internes, sans réseau."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

class Page(HTMLParser):
    def __init__(self, texte):
        super().__init__(); self.ids=set(); self.liens=[]; self.h1=0; self.main=0
        self.lang=False; self.titre=False; self.alias=False
        self.feed(texte)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='html': self.lang=a.get('lang','').startswith('fr')
        if tag=='title': self.titre=True
        if tag=='meta' and a.get('http-equiv','').lower()=='refresh': self.alias=True
        if tag=='h1': self.h1+=1
        if tag=='main': self.main+=1
        if tag=='nav' and not (a.get('aria-label') or a.get('aria-labelledby')):
            raise ValueError('Navigation sans nom accessible')
        if 'id' in a:
            if a['id'] in self.ids: raise ValueError('Identifiant répété : '+a['id'])
            self.ids.add(a['id'])
        self.liens += [a[k] for k in ('href','src') if k in a]

def verifier(sortie, base):
    sortie=sortie.resolve(); origin=urlsplit(base)
    if origin.scheme!='https' or not origin.netloc or not base.endswith('/'):
        raise ValueError('URL HTTPS terminée par / requise')
    pages={}
    for chemin in sortie.rglob('*.html'):
        try:
            p=Page(chemin.read_text(encoding='utf-8')); pages[chemin]=p
            if not p.titre: raise ValueError('Titre absent')
            if not p.alias and (not p.lang or p.h1!=1 or p.main!=1):
                raise ValueError(f'Langue française, main ou h1 invalide ({p.main} main, {p.h1} h1)')
        except ValueError as e: raise ValueError(f'{chemin.relative_to(sortie)} : {e}') from e
    if not pages: raise ValueError('Aucune page HTML')
    erreurs=[]
    for chemin,p in pages.items():
        relatif=chemin.relative_to(sortie).as_posix()
        adresse=urljoin(base,relatif.removesuffix('index.html'))
        for lien in p.liens:
            u=urlsplit(urljoin(adresse,lien))
            if u.scheme not in ('https','http') or u.netloc!=origin.netloc: continue
            if not u.path.startswith(origin.path): continue # autre produit de la même origine
            cible=sortie/unquote(u.path[len(origin.path):])
            if u.path.endswith('/'): cible=cible/'index.html'
            cible=cible.resolve()
            if not cible.is_relative_to(sortie) or not cible.is_file():
                erreurs.append(f'{relatif} → {lien}'); continue
            if u.fragment and cible in pages and unquote(u.fragment) not in pages[cible].ids:
                erreurs.append(f'{relatif} → ancre absente {lien}')
    if erreurs: raise ValueError('\n'.join(sorted(set(erreurs))))
    print(f'{len(pages)} pages : liens, ancres, identifiants, langue, main/h1 et navigation OK')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sortie',type=Path,required=True);p.add_argument('--base-url',required=True)
    a=p.parse_args()
    try: verifier(a.sortie,a.base_url)
    except ValueError as e: p.exit(1,str(e)+'\n')
