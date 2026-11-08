"""
ruota.py - ruota il modello di jausiers_sun3d_py su un azimut dato, senza
modificarne i file. Va chiamato PRIMA di importare gli altri moduli
(church_mesh, wall_projection, reference_photos, viewer_3d), che copiano
le costanti di church_geometry al momento dell'import.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass


def angdiff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def ruota(src: str, asse: float | None = None, facciata: float | None = None) -> dict:
    sys.path.insert(0, src)
    import church_geometry as cg

    base = cg.FACADE_AZIMUTH_DEG
    if facciata is not None:
        facade, fonte = facciata % 360.0, "facciata"
    elif asse is not None:
        a = asse % 360.0
        # asse noto modulo 180: la facciata e' la direzione piu' vicina al modello (SSE)
        facade, fonte = min((a, (a + 180.0) % 360.0), key=lambda x: angdiff(x, base)), "asse"
    else:
        facade, fonte = base, "modello"
    delta = (facade - base + 180.0) % 360.0 - 180.0

    real = cg.ChurchModel

    @dataclass(frozen=True)
    class ChurchModelRuotato(real):  # type: ignore[misc, valid-type]
        facade_azimuth_deg: float = facade

    cg.FACADE_AZIMUTH_DEG = facade
    cg.APSE_FACET_AZIMUTHS_DEG = [(x + delta) % 360.0 for x in cg.APSE_FACET_AZIMUTHS_DEG]
    cg.ChurchModel = ChurchModelRuotato
    return {"cg": cg, "facade": facade, "delta": delta, "fonte": fonte}
