#!/usr/bin/env python3
"""
genera_dati.py - porta nel sito i dati che nascono altrove:

  orientatamento_chiese_Ubaye/orientamento_chiese.csv        (chiese.py)
      -> sito/comune/dati/chiese_ubaye.js   window.CHIESE_UBAYE = [...]
  orientatamento_chiese_Ubaye/ricerca_saint_nicolas_jausiers.json  (/chiesa)
      -> sito/comune/dati/ricerca.js        window.RICERCA = {...} | null
  jausiers_sun3d_py/storia_jausiers.json  (cronologia dal diagnostico 2016)
      -> sito/comune/dati/storia_jausiers.js  window.STORIA_JAUSIERS = {...} | null
  jausiers_sun3d_py/ricerca_orientamento_ubaye/mappa_orientamento_ubaye.html
      -> sito/comune/dati/mappa_orientamento_ubaye.html (copia, cartina della pagina storia)

Il sito si apre anche con doppio click (file://), dove il browser non
legge i .json: per questo i dati diventano piccoli file .js.
Il mod jausiers scrive gia' comune/dati/ricerca.js a ogni salva_ricerca; questo
script serve dopo aver rilanciato chiese.py o per rigenerare tutto.

Uso:  python3 sito/strumenti/genera_dati.py
"""
from __future__ import annotations

import csv
import json
import os

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.normpath(os.path.join(QUI, ".."))
PROGETTO = os.path.normpath(os.path.join(SITO, ".."))
ORIENT = os.path.join(PROGETTO, "orientatamento_chiese_Ubaye")
DATI = os.path.join(SITO, "comune", "dati")

NUMERICI = {"lon", "lat", "area_m2", "elongation", "axis_az", "dev_from_EW",
            "slope_deg", "downhill_az", "axis_vs_fallline"}


def num(x: str):
    if x == "":
        return None
    v = float(x)
    return int(v) if v.is_integer() and "." not in x else v


def chiese() -> list[dict]:
    path = os.path.join(ORIENT, "orientamento_chiese.csv")
    righe, visti = [], set()
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["osm_url"] in visti:  # il CSV puo' contenere righe ripetute
                continue
            visti.add(r["osm_url"])
            righe.append({k: (num(v) if k in NUMERICI else v) for k, v in r.items()})
    # Se c'e' la ricerca di jausiers_sun3d_py, aggiunge verso dell'abside,
    # affidabilita', epoca e protezione (chiese.py conosce l'asse solo modulo 180).
    extra = os.path.join(PROGETTO, "jausiers_sun3d_py", "ricerca_orientamento_ubaye", "storia_fonti.json")
    if os.path.exists(extra):
        with open(extra, encoding="utf-8") as f:
            per_url = {f"https://www.openstreetmap.org/{c['osm']}": c for c in json.load(f)}
        for r in righe:
            c = per_url.get(r["osm_url"])
            if c:
                r.update(apse_az=c["apse_az"], facade_az=c["facade_az"], affidabilita=c["affidabilita"],
                         epoca=c.get("epoca"), protezione=c.get("protezione"),
                         storia=c.get("storia") or [], fonti_storia=c.get("fonti") or [])
    return righe


def ricerca():
    path = os.path.join(ORIENT, "ricerca_saint_nicolas_jausiers.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def storia_jausiers():
    """Cronologia di Saint-Nicolas dal diagnostico 2016 e dalla delibera del
    1668 (jausiers_sun3d_py/storia_jausiers.json, scritto a mano)."""
    path = os.path.join(PROGETTO, "jausiers_sun3d_py", "storia_jausiers.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def copia_mappa() -> bool:
    """Copia nel sito la cartina dell'orientamento delle chiese dell'Ubaye
    (jausiers_sun3d_py/ricerca_orientamento_ubaye/mappa_orientamento_ubaye.html,
    pagina autonoma con i dati dentro, prodotta da build_mappa.py): la
    pagina storia la mostra nella sezione Orientamento."""
    import shutil
    src = os.path.join(PROGETTO, "jausiers_sun3d_py", "ricerca_orientamento_ubaye", "mappa_orientamento_ubaye.html")
    if not os.path.exists(src):
        return False
    shutil.copyfile(src, os.path.join(DATI, "mappa_orientamento_ubaye.html"))
    return True


def scrivi(nome: str, variabile: str, valore) -> None:
    os.makedirs(DATI, exist_ok=True)
    testo = (f"// Generato da strumenti/genera_dati.py: non modificare a mano.\n"
             f"window.{variabile} = {json.dumps(valore, ensure_ascii=False, indent=1)};\n")
    with open(os.path.join(DATI, nome), "w", encoding="utf-8") as f:
        f.write(testo)
    print(f"scritto dati/{nome}")


def main() -> None:
    c = chiese()
    scrivi("chiese_ubaye.js", "CHIESE_UBAYE", c)
    r = ricerca()
    scrivi("ricerca.js", "RICERCA", r)
    scrivi("storia_jausiers.js", "STORIA_JAUSIERS", storia_jausiers())
    print("cartina dell'Ubaye: " + ("copiata" if copia_mappa() else "assente"))
    print(f"{len(c)} chiese; ricerca: {'presente' if r else 'assente (lancia /chiesa)'}")


if __name__ == "__main__":
    main()
