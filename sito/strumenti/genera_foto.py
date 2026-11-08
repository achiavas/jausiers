#!/usr/bin/env python3
"""
genera_foto.py - incorpora nel sito (comune/photos-data.js) le foto di
jausiers_sun3d_py/photos, come base64: il sito deve funzionare anche
aperto con doppio click (file://), dove il browser non carica immagini
locali come texture.

Aggiorna solo le foto indicate; le altre voci restano come sono.
Ogni foto viene ricompressa (lato lungo max 1400 px, JPEG qualita' 80).

Uso:  python3 sito/strumenti/genera_foto.py cappella_ovest_1.jpg [altre.jpg ...]
"""
from __future__ import annotations

import base64
import io
import os
import re
import sys

from PIL import Image

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.normpath(os.path.join(QUI, ".."))
FOTO = os.path.normpath(os.path.join(SITO, "..", "jausiers_sun3d_py", "photos"))
DATI = os.path.join(SITO, "comune", "photos-data.js")
LATO_MAX = 1400


def data_uri(nome: str) -> str:
    im = Image.open(os.path.join(FOTO, nome))
    png = nome.lower().endswith(".png")          # PNG: si tiene la trasparenza
    im = im.convert("RGBA" if png else "RGB")
    im.thumbnail((LATO_MAX, LATO_MAX), Image.LANCZOS)
    buf = io.BytesIO()
    if png:
        im.save(buf, "PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    im.save(buf, "JPEG", quality=80, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main(nomi: list[str]) -> None:
    righe = open(DATI, encoding="utf-8").read().split("\n")
    fine = righe.index("};")
    for nome in nomi:
        nuova = f'  "{nome}": "{data_uri(nome)}",'
        i = next((k for k, r in enumerate(righe) if re.match(rf'\s*"{re.escape(nome)}":', r)), None)
        if i is None:
            righe.insert(fine, nuova); fine += 1
            print(f"aggiunta {nome} ({len(nuova) // 1024} KB)")
        else:
            righe[i] = nuova
            print(f"aggiornata {nome} ({len(nuova) // 1024} KB)")
    open(DATI, "w", encoding="utf-8").write("\n".join(righe))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
