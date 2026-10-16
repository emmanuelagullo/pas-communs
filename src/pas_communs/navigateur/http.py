"""Environnement HTTP virtuel commun ; Django conserve CSRF et permissions."""
import sys
from http.cookies import SimpleCookie
from urllib.parse import urlsplit


def environnement(request, script_name, cookies, input_file, input_size, *, origine=None):
    url = urlsplit(request["url"])
    if origine is not None:
        origine_url = urlsplit(origine)
        if (url.scheme, url.netloc) != (origine_url.scheme, origine_url.netloc):
            raise ValueError("Origine HTTP étrangère")
        if url.path != script_name and not url.path.startswith(script_name + "/"):
            raise ValueError("Chemin hors de l’application")
    path = url.path.removeprefix(script_name) or "/"
    environ = {
        "REQUEST_METHOD": request["method"], "PATH_INFO": path,
        "QUERY_STRING": url.query, "SCRIPT_NAME": script_name,
        "SERVER_NAME": url.hostname, "SERVER_PORT": str(url.port or 443),
        "SERVER_PROTOCOL": "HTTP/1.1", "REMOTE_ADDR": "127.0.0.1",
        "wsgi.version": (1, 0), "wsgi.url_scheme": url.scheme,
        "wsgi.input": input_file, "wsgi.errors": sys.stderr,
        "wsgi.multithread": False, "wsgi.multiprocess": False, "wsgi.run_once": False,
        "CONTENT_LENGTH": str(input_size),
        "HTTP_COOKIE": "; ".join(f"{k}={v}" for k, v in cookies.items()),
    }
    for key, value in request["headers"]:
        key = key.upper().replace("-", "_")
        if key in {"COOKIE", "HOST", "CONTENT_LENGTH"}:
            continue
        environ[key if key == "CONTENT_TYPE" else "HTTP_" + key] = value
    environ["HTTP_HOST"] = url.netloc
    return environ


def retenir_cookies(entetes, cookies):
    publics = []
    for key, value in entetes:
        if key.lower() == "set-cookie":
            for name, morsel in SimpleCookie(value).items():
                if morsel["max-age"] == "0":
                    cookies.pop(name, None)
                else:
                    cookies[name] = morsel.value
        else:
            publics.append([key, value])
    return publics
