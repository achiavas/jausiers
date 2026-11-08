"""
storia_chiesa.py
----------------
Testo "Storia e fonti" di Saint-Nicolas-de-Myre per il pannello del
visualizzatore 3D (tasto H).

La storia e le fonti NON sono duplicate qui: vengono lette da
ricerca_orientamento_ubaye/storia_fonti.py (la stessa scheda usata dalla
cartina dell'Ubaye), così un'eventuale correzione va fatta in un posto
solo. Se quella cartella manca, si usa un testo minimo di riserva.
"""
from __future__ import annotations

import importlib.util
import os
import textwrap

from church_geometry import FACADE_AZIMUTH_DEG, LATITUDE_DEG, LONGITUDE_DEG

OSM_ID = "way/93932532"
LARGHEZZA_RIGA = 64  # caratteri, per il pannello in sovrimpressione

_RICERCA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "ricerca_orientamento_ubaye", "storia_fonti.py")


def _carica_scheda():
    try:
        spec = importlib.util.spec_from_file_location("storia_fonti_ubaye", _RICERCA)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        scheda = mod.STORIA[OSM_ID]
        fonti = [mod.FONTI[k] for k in scheda.get("fonti", [])]
        return scheda, fonti
    except Exception:  # cartella di ricerca assente o modificata
        return ({"epoca": "completata verso il 1670; consacrata nel 1686",
                 "protezione": "Monumento storico, classificata nel 1921 (PA00080407)",
                 "storia": ["Chiesa barocca della Controriforma, consacrata a san Nicola di Mira nel 1686."]},
                [])


def testo_storia() -> str:
    """Testo già impaginato (righe a capo) per il pannello del viewer."""
    scheda, fonti = _carica_scheda()
    w = lambda s, ind="": textwrap.fill(s, LARGHEZZA_RIGA, initial_indent=ind,
                                        subsequent_indent=" " * len(ind))
    abside = (FACADE_AZIMUTH_DEG + 180) % 360
    righe = ["STORIA E FONTI  -  Saint-Nicolas-de-Myre, Jausiers", ""]
    if scheda.get("epoca"):
        righe.append(w(scheda["epoca"], "Epoca: "))
    if scheda.get("protezione"):
        righe.append(w(scheda["protezione"], "Tutela: "))
    righe.append(f"Orientamento: facciata {FACADE_AZIMUTH_DEG:.0f}° (SSE), abside {abside:.0f}° (NNO)")
    righe.append(f"Coordinate: {LATITUDE_DEG:.5f} N, {LONGITUDE_DEG:.5f} E")
    righe.append("")
    for par in scheda.get("storia", []):
        righe += [w(par), ""]
    if scheda.get("orient"):
        righe += [w(scheda["orient"], "Nota: "), ""]
    righe.append(w("Nella valle dell'Ubaye solo 14 absidi affidabili su 35 guardano tra "
                   "NE ed E: Jausiers, con l'abside a NNO, rientra nel gruppo delle chiese "
                   "rivolte a nord (Barcelonnette, Enchastrayes, La Condamine)."))
    righe += ["", "Fonti:"]
    for titolo, url in fonti:
        righe.append(w(titolo, "  - "))
        if url.startswith("http"):
            righe.append("    " + url)
    righe.append("  - Mérimée PA00080407: pop.culture.gouv.fr/notice/merimee/PA00080407")
    righe.append("  - OpenStreetMap " + OSM_ID)
    righe += ["", "[H] chiudi"]
    return "\n".join(righe)


if __name__ == "__main__":
    print(testo_storia())
