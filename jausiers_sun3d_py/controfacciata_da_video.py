#!/usr/bin/env python3
"""
controfacciata_da_video.py
--------------------------
Foto RADDRIZZATA della controfacciata (il muro d'ingresso visto da
dentro) dal fotogramma a 15.6 s di IMG_9758: va dietro alle strutture
3D (bussola col portone, altarino col fonte, armadio, confessionale).

  - omografia dal piano del muro (v, quota) alla foto: spigoli del muro
    con i fianchi sotto il cornicione (8.9 m) e alla base (dove poggiano
    fonte e confessionale); larghezza = la navata, 13.37 m;
  - stessa correzione della dominante calda usata per i colori degli
    arredi (church_mesh._C): il muro portato al bianco degli interni;
  - sotto i banchi (in basso) la foto non vede il muro: lo si completa
    col colore del muro.
-> photos/controfacciata_interno.jpg, da terra a CONTROFACCIATA_ALTEZZA_M
   (sotto i davanzali delle vetrate), larga quanto la navata.

Uso:  .venv/bin/python controfacciata_da_video.py
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import cv2
import numpy as np

from church_geometry import NAVE_WIDTH_M, CORNICIONE_BASE_M
from reference_photos import CONTROFACCIATA_ALTEZZA_M

QUI = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(QUI, "video", "IMG_9758.mov")
USCITA = os.path.join(QUI, "photos", "controfacciata_interno.jpg")
PX_PER_M = 80
# punti del muro nel fotogramma (3840 x 2160); a sinistra nella foto = Est (v < 0)
SPIGOLI = {(-1, CORNICIONE_BASE_M): (1346, 552), (1, CORNICIONE_BASE_M): (2747, 552),
           (-1, 0.0): (1346, 1545), (1, 0.0): (2747, 1545)}
Y_BANCHI = 1525          # sotto questa riga della foto ci sono i banchi
# guadagno per canale (RGB) che porta il muro della foto (183, 171, 155) al
# bianco degli interni (0xf7f5f0)
GUADAGNO = np.array([247 / 183, 245 / 171, 240 / 155])


def fotogramma(t=15.6):
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.png")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", VIDEO, "-frames:v", "1", f, "-y"], check=True)
        return cv2.imread(f)


def main():
    im = fotogramma()
    wh = NAVE_WIDTH_M / 2
    src = np.float32([(lato * wh, q) for (lato, q) in SPIGOLI])
    dst = np.float32(list(SPIGOLI.values()))
    M = cv2.getPerspectiveTransform(src, dst)
    W, H = int(NAVE_WIDTH_M * PX_PER_M), int(CONTROFACCIATA_ALTEZZA_M * PX_PER_M)
    v = -wh + (np.arange(W) + 0.5) / PX_PER_M
    q = CONTROFACCIATA_ALTEZZA_M - (np.arange(H) + 0.5) / PX_PER_M
    V, Q = np.meshgrid(v, q)
    P = np.stack([V, Q, np.ones_like(V)], -1) @ M.T
    mx, my = (P[..., 0] / P[..., 2]).astype(np.float32), (P[..., 1] / P[..., 2]).astype(np.float32)
    out = cv2.remap(im, mx, my, cv2.INTER_CUBIC).astype(np.float32)
    out = (out * GUADAGNO[::-1][None, None, :]).clip(0, 255)
    muro = np.median(out[(my > 700) & (my < 900) & (np.abs(V) > 3.2) & (np.abs(V) < 6)].reshape(-1, 3), 0)
    out[my >= Y_BANCHI] = muro
    cv2.imwrite(USCITA, out.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{USCITA}: {W}x{H} px, {NAVE_WIDTH_M} x {CONTROFACCIATA_ALTEZZA_M} m")


if __name__ == "__main__":
    main()
