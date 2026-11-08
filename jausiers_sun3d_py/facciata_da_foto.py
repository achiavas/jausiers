#!/usr/bin/env python3
"""
facciata_da_foto.py
-------------------
Adatta la foto della facciata esterna al modello 3D: le tre vetrate
della foto vengono portate ESATTAMENTE sulle vetrate del modello (quelle
blu: davanzali, larghezze e chiavi da church_geometry.py), mentre la
base, gli spigoli e il colmo della facciata restano dove li mettono le
piantine. Fra questi punti la foto si deforma in modo continuo
(thin-plate spline): il resto della facciata segue con dolcezza.

Sorgente: video/facciata_esterna_frontale.jpg (foto frontale fornita
dall'utente, 960 x 1439). La sagoma della chiesa (tetto, corpo centrale,
ali laterali) viene ritagliata: cielo, montagne e case vicine diventano
trasparenti. Uscita: photos/facciata_esterna.png (con trasparenza), che copre il
pannello della facciata (PHOTO_CARDS in reference_photos.py):
largo FACCIATA_LARGHEZZA_M, da 0 a FACCIATA_ALTEZZA_M.

X nella foto = da sinistra a destra come la vede chi sta FUORI, cioe'
-v nel modello: la vetrata laterale Ovest (v = +1.45) e' a sinistra.

Uso:  .venv/bin/python facciata_da_foto.py
"""
from __future__ import annotations

import os

import cv2
import numpy as np

from church_geometry import (
    FACADE_CENTRAL_WINDOW_ARCH_RISE_M, FACADE_CENTRAL_WINDOW_HEAD_M, FACADE_CENTRAL_WINDOW_SILL_M,
    FACADE_CENTRAL_WINDOW_WIDTH_M, FACADE_SIDE_WINDOW_ARCH_RISE_M, FACADE_SIDE_WINDOW_HEAD_M,
    FACADE_SIDE_WINDOW_OFFSET_M, FACADE_SIDE_WINDOW_SILL_M, FACADE_SIDE_WINDOW_WIDTH_M,
    NAVE_WIDTH_M, ROOF_RIDGE_RISE_M, WALL_HEIGHT_M,
)

QUI = os.path.dirname(os.path.abspath(__file__))
SORGENTE = os.path.join(QUI, "video", "facciata_esterna_frontale.jpg")
USCITA = os.path.join(QUI, "photos", "facciata_esterna.png")
FACCIATA_LARGHEZZA_M = 20.0     # copre tutta la sagoma nella foto (vedi main)
FACCIATA_ALTEZZA_M = 26.5
PX_PER_M = 40

# Punti misurati sulla foto frontale (960 x 1439 px): vani delle vetrate
# (angoli in basso e chiave dell'arco), spigoli del corpo centrale e delle
# ali a terra, colmo del tetto.
FOTO = {
    "sx_bs": (361.7, 610.0), "sx_bd": (391.7, 610.0), "sx_chiave": (376.7, 545.0),
    "c_bs": (415.0, 610.0), "c_bd": (463.3, 610.0), "c_chiave": (439.2, 513.3),
    "dx_bs": (486.7, 611.7), "dx_bd": (515.0, 611.7), "dx_chiave": (500.8, 547.3),
    "spigolo_sx": (162.0, 1040.0), "spigolo_dx": (722.0, 1040.0),
    "terra_sx": (295.4, 1040.0), "terra_c": (442.0, 1045.0), "terra_dx": (588.6, 1040.0),
    "bordo_sx": (118.0, 1042.0), "bordo_dx": (758.0, 1042.0),
    "colmo": (432.0, 195.0),
}
# Pilastri d'angolo: restano verticali. Lungo il loro bordo esterno
# (x = 162 e 722 nella foto) la quota segue la scala verticale delle
# vetrate (pavimento y = 1040 -> davanzali y = 610 a 13.37 m).
SCALA_VERTICALE = (1040.0 - 610.0) / FACADE_CENTRAL_WINDOW_SILL_M
Y_PILASTRI = (560.0, 760.0, 950.0)
for _y in Y_PILASTRI:
    FOTO[f"pil_sx_{int(_y)}"] = (162.0, _y)
    FOTO[f"pil_dx_{int(_y)}"] = (722.0, _y)
# Sagoma della chiesa nella foto (il resto diventa trasparente): tetto
# fino alle gronde, corpo centrale, ali laterali, fino a terra.
SAGOMA = [(432, 190), (760, 468), (726, 506), (726, 732), (760, 742), (760, 1052),
          (116, 1052), (116, 735), (158, 727), (158, 508), (116, 452)]


def modello() -> dict:
    ws, wc, d = FACADE_SIDE_WINDOW_WIDTH_M, FACADE_CENTRAL_WINDOW_WIDTH_M, FACADE_SIDE_WINDOW_OFFSET_M
    s0, c0 = FACADE_SIDE_WINDOW_SILL_M, FACADE_CENTRAL_WINDOW_SILL_M
    ts = FACADE_SIDE_WINDOW_HEAD_M + FACADE_SIDE_WINDOW_ARCH_RISE_M
    tc = FACADE_CENTRAL_WINDOW_HEAD_M + FACADE_CENTRAL_WINDOW_ARCH_RISE_M
    wh, L = NAVE_WIDTH_M / 2, FACCIATA_LARGHEZZA_M / 2
    return {
        "sx_bs": (-d - ws / 2, s0), "sx_bd": (-d + ws / 2, s0), "sx_chiave": (-d, ts),
        "c_bs": (-wc / 2, c0), "c_bd": (wc / 2, c0), "c_chiave": (0.0, tc),
        "dx_bs": (d - ws / 2, s0), "dx_bd": (d + ws / 2, s0), "dx_chiave": (d, ts),
        "spigolo_sx": (-wh, 0.0), "spigolo_dx": (wh, 0.0),
        "terra_sx": (-3.5, 0.0), "terra_c": (0.0, 0.0), "terra_dx": (3.5, 0.0),
        "bordo_sx": (-L, 0.0), "bordo_dx": (L, 0.0),
        "colmo": (0.0, WALL_HEIGHT_M + ROOF_RIDGE_RISE_M),
        **{f"pil_{lato}_{int(y)}": (seg * wh, (1040.0 - y) / SCALA_VERTICALE)
           for lato, seg in (("sx", -1), ("dx", 1)) for y in Y_PILASTRI},
    }


def main() -> None:
    """SENZA deformazioni: la foto e' frontale (verticali raddrizzate), quindi
    basta una similitudine - stessa scala in orizzontale e in verticale,
    presa dal suolo ai davanzali delle vetrate (13.37 m), e centro sulla
    vetrata centrale. (Prima una thin-plate spline portava anche gli
    spigoli del corpo centrale sui muri della navata a +-6.685 m: ma nella
    foto quel corpo, alla stessa scala, e' largo ~17 m, cioe' comprende le
    cappelle, e la facciata veniva compressa di ~25% in orizzontale.)
    Gli altri punti misurati (FOTO) servono solo da controllo."""
    im = cv2.imread(SORGENTE)
    s_px = (FOTO["spigolo_sx"][1] - FOTO["c_bs"][1]) / FACADE_CENTRAL_WINDOW_SILL_M   # px/m
    x0 = (FOTO["c_bs"][0] + FOTO["c_bd"][0]) / 2
    y0 = FOTO["spigolo_sx"][1]
    W, H = int(FACCIATA_LARGHEZZA_M * PX_PER_M), int(FACCIATA_ALTEZZA_M * PX_PER_M)
    X = -FACCIATA_LARGHEZZA_M / 2 + (np.arange(W) + 0.5) / PX_PER_M
    Y = FACCIATA_ALTEZZA_M - (np.arange(H) + 0.5) / PX_PER_M
    XX, YY = np.meshgrid(X, Y)
    mx, my = (x0 + s_px * XX).astype(np.float32), (y0 - s_px * YY).astype(np.float32)
    out = cv2.remap(im, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    sagoma = np.zeros(im.shape[:2], np.uint8)
    cv2.fillPoly(sagoma, [np.int32(SAGOMA)], 255)
    alfa = cv2.remap(sagoma, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    cv2.imwrite(USCITA, np.dstack([out, alfa]))
    m = lambda n: ((FOTO[n][0] - x0) / s_px, (y0 - FOTO[n][1]) / s_px)
    print(f"{USCITA}: {W}x{H} px, {FACCIATA_LARGHEZZA_M} x {FACCIATA_ALTEZZA_M} m, {s_px:.1f} px/m nella foto")
    print(f"  nella foto: corpo centrale da {m('spigolo_sx')[0]:+.2f} a {m('spigolo_dx')[0]:+.2f} m; "
          f"vetrate laterali a {m('sx_chiave')[0]:+.2f} e {m('dx_chiave')[0]:+.2f} m (modello +-{FACADE_SIDE_WINDOW_OFFSET_M}); "
          f"chiavi {m('sx_chiave')[1]:.2f} / {m('c_chiave')[1]:.2f} m; colmo {m('colmo')[1]:.2f} m")


if __name__ == "__main__":
    main()
