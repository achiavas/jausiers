#!/usr/bin/env python3
"""
verifica_sync.py - controlla che Python (jausiers_sun3d_py) e sito
(JavaScript) usino le stesse misure.

Le misure vengono dalle piantine e vivono in due copie: i moduli Python
e il loro porting JS. Questo script confronta ogni costante numerica
(NOME = valore) dei moduli portati e segnala:
  - valori diversi (errore),
  - costanti presenti da una parte sola (avviso).
Esce con codice 1 se trova anche un solo valore diverso.

Regola: quando cambi una misura, cambiala nel Python E nel sito, poi
lancia questo script.

Uso:  python3 sito/strumenti/verifica_sync.py
"""
from __future__ import annotations

import ast
import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.normpath(os.path.join(QUI, ".."))
PY = os.path.normpath(os.path.join(SITO, "..", "jausiers_sun3d_py"))

COPPIE = [
    ("church_geometry.py", "church-geometry.js"),
    ("church_mesh.py", "church-mesh.js"),
    ("wall_projection.py", "wall-projection.js"),
    ("reference_photos.py", "reference-photos.js"),
    ("solar_position.py", "solar-position.js"),
]

# Nel sito il valore delle piantine ha un nome esplicito, perche'
# l'orientamento mostrato puo' essere ruotato (parametri.js).
ALIAS_JS = {
    "FACADE_AZIMUTH_DEG": "FACADE_AZIMUTH_PIANTINE_DEG",
    "APSE_FACET_AZIMUTHS_DEG": "APSE_FACET_AZIMUTHS_PIANTINE_DEG",
}
# Costanti che esistono da una parte sola per motivi noti.
SOLO_UNA_PARTE = {"ELEVATION_M", "RAD", "TIMEZONE_NAME"}


def valore(testo: str):
    """Numero, lista di numeri o stringa; None se e' un'espressione."""
    # prima il commento, poi il punto e virgola ("1.93;  // nota")
    t = re.sub(r"\s*(#|//).*$", "", testo.strip())
    t = t.rstrip(";").strip()
    try:
        v = ast.literal_eval(t)
    except Exception:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, (list, tuple)) and all(isinstance(x, (int, float)) for x in v):
        return [float(x) for x in v]
    if isinstance(v, str):
        return v
    return None


def costanti_py(path: str) -> dict:
    out = {}
    for riga in open(path, encoding="utf-8"):
        m = re.match(r"^(_?[A-Z][A-Z0-9_]*)\s*(?::\s*[\w\[\], ]+)?=\s*(.+)$", riga)
        if m:
            v = valore(m.group(2))
            if v is not None:
                out[m.group(1).lstrip("_")] = v
    return out


def costanti_js(path: str) -> dict:
    out = {}
    for riga in open(path, encoding="utf-8"):
        m = re.match(r"^const\s+([A-Z][A-Z0-9_]*)\s*=\s*(.+)$", riga)
        if m:
            v = valore(m.group(2))
            if v is not None:
                out[m.group(1)] = v
    return out


def uguali(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(abs(x - y) < 1e-9 for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) < 1e-9
    return a == b


def main() -> int:
    errori = avvisi = confrontate = 0
    for fpy, fjs in COPPIE:
        cpy = costanti_py(os.path.join(PY, fpy))
        cjs = costanti_js(os.path.join(SITO, "comune", fjs))
        usati_js = set()
        for nome, vpy in sorted(cpy.items()):
            nome_js = ALIAS_JS.get(nome, nome)
            if nome_js not in cjs:
                if nome not in SOLO_UNA_PARTE:
                    print(f"  avviso  {fpy}: {nome} = {vpy} non c'e' in {fjs}")
                    avvisi += 1
                continue
            usati_js.add(nome_js)
            confrontate += 1
            if not uguali(vpy, cjs[nome_js]):
                print(f"  ERRORE  {nome}: Python {vpy}  !=  sito {cjs[nome_js]}  ({fpy} / {fjs})")
                errori += 1
        for nome_js in sorted(set(cjs) - usati_js):
            if nome_js not in SOLO_UNA_PARTE and nome_js not in cpy:
                print(f"  avviso  {fjs}: {nome_js} non c'e' in {fpy}")
                avvisi += 1
    print(f"\n{confrontate} costanti confrontate, {errori} diverse, {avvisi} avvisi.")
    print("OK: Python e sito usano le stesse misure." if not errori else "Da allineare.")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
