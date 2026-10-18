"""Exercice HTTP local d'un WSGI Gunicorn, sans certificat ou hôte public.

Le produit fournit un environnement fictif déjà migré et collecté. Les
redirections ne sont jamais suivies et seuls les sockets loopback sont utilisés.
"""
from contextlib import contextmanager
import http.client
import os
import signal
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time


@contextmanager
def gunicorn(racine, application, environnement):
    if sys.platform == 'win32':
        raise RuntimeError('Ce banc Gunicorn est destiné aux runners Unix.')
    with socket.socket() as entree, tempfile.TemporaryFile() as journal:
        entree.bind(('127.0.0.1',0));entree.listen(128)
        port=entree.getsockname()[1]
        commande=[sys.executable,'-m','gunicorn','--workers','1','--threads','1',
            '--forwarded-allow-ips=','--bind',f'fd://{entree.fileno()}',
            '--access-logfile','/dev/null','--log-level','warning',application]
        processus=subprocess.Popen(commande,cwd=Path(racine),env=environnement,
            pass_fds=(entree.fileno(),),start_new_session=True,stdout=journal,stderr=journal)
        try:
            # Un vrai échange HTTP garantit que le worker a importé WSGI.
            limite=time.monotonic()+30
            while True:
                if processus.poll() is not None:
                    journal.seek(0)
                    raise RuntimeError('Gunicorn ne démarre pas : '+journal.read().decode(errors='replace'))
                try:
                    reponse=requete(port,'/health/',hote='serveur.fictif.example')
                    break
                except (OSError,http.client.HTTPException):
                    if time.monotonic()>=limite:raise RuntimeError('Délai de démarrage Gunicorn dépassé.') from None
                    time.sleep(.05)
            yield port
        finally:
            # Session propre : arrêter aussi les workers si le master échoue.
            try:os.killpg(processus.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:processus.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:os.killpg(processus.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                processus.wait(timeout=5)


def requete(port, chemin, *, hote, methode='GET', https_proxy=False):
    connexion=http.client.HTTPConnection('127.0.0.1',port,timeout=2)
    try:
        entetes={'Host':hote}
        if https_proxy:entetes['X-Forwarded-Proto']='https'
        connexion.request(methode,chemin,headers=entetes)
        reponse=connexion.getresponse()
        return reponse.status,dict(reponse.getheaders()),reponse.read()
    finally:connexion.close()


def verifier(racine, application, environnement, variable_proxy, statique):
    env={**environnement,variable_proxy:'non'}
    with gunicorn(racine,application,env) as port:
        statut,entetes,_=requete(port,'/health/',hote='serveur.fictif.example',https_proxy=True)
        if statut!=301 or entetes.get('Location')!='https://serveur.fictif.example/health/':
            raise AssertionError('Un en-tête HTTPS non approuvé a été accepté.')
    env[variable_proxy]='oui'
    with gunicorn(racine,application,env) as port:
        def lire(chemin,**kwargs):return requete(port,chemin,hote='serveur.fictif.example',https_proxy=True,**kwargs)
        statut,entetes,corps=lire('/health/')
        if statut!=200 or b'"ok"' not in corps or entetes.get('Strict-Transport-Security')!='max-age=3600':
            raise AssertionError('Health HTTPS/proxy ou HSTS incorrect.')
        if lire('/connexion/',methode='POST')[0]!=403:
            raise AssertionError('POST sans CSRF accepté.')
        statut,entetes,_=lire('/connexion/')
        if statut!=200 or 'Secure' not in entetes.get('Set-Cookie',''):
            raise AssertionError('Connexion ou cookie sécurisé incorrect.')
        if lire(statique)[0]!=200:raise AssertionError('Statique non servi.')
        if requete(port,'/health/',hote='etranger.fictif.example',https_proxy=True)[0]!=400:
            raise AssertionError('Hôte étranger accepté.')
    print('HTTP Gunicorn loopback : proxy explicite, Host, CSRF, cookie et statique : OK')
