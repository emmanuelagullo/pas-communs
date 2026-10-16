#!/usr/bin/env python3
"""Construire deux wheels et refuser une différence d’octets."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parent.parent


def main():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    nom = f"pas_communs-{version}-py3-none-any.whl"
    environnement = {**os.environ, "SOURCE_DATE_EPOCH": "1767225600", "PYTHONHASHSEED": "0"}
    with tempfile.TemporaryDirectory() as temp:
        wheels = []
        for i in range(2):
            sortie = Path(temp) / str(i)
            subprocess.run([sys.executable, "-m", "build", "--wheel", "--no-isolation",
                            "--outdir", str(sortie)], cwd=ROOT, env=environnement, check=True)
            wheels.append(sortie / nom)
        if wheels[0].read_bytes() != wheels[1].read_bytes():
            raise SystemExit("Wheel non reproductible : publication refusée.")
        dossier = ROOT / "dist"
        dossier.mkdir(exist_ok=True)
        for ancien in dossier.glob("*.whl"):
            ancien.unlink()
        shutil.copyfile(wheels[0], dossier / nom)
        empreinte = hashlib.sha256(wheels[0].read_bytes()).hexdigest()
        (dossier / "SHA256SUMS").write_text(f"{empreinte}  {nom}\n")
        print(f"{nom} : {empreinte}")


if __name__ == "__main__":
    main()
