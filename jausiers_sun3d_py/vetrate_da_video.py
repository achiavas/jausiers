#!/usr/bin/env python3
"""
vetrate_da_video.py
-------------------
Foto RADDRIZZATE delle tre vetrate della facciata, viste dall'interno,
da un fotogramma del video IMG_9756.mov.

Come:
  1. un fotogramma nitido (t = 4.0 s, piena risoluzione 3840x2160);
  2. i vetri si riconoscono dal colore (saturazione alta); di ogni
     vetrata si prendono i due angoli in basso e la chiave dell'arco;
  3. i 9 punti corrispondono a punti noti del piano di facciata
     (davanzali, larghezze e chiavi da church_geometry.py): da li'
     un'omografia, cioe' la prospettiva esatta di quel piano. Unica
     incognita in piu': la distanza delle vetrate laterali dall'asse,
     che le piantine non quotano (FACADE_SIDE_WINDOW_OFFSET_M = 1.45,
     stimata) - viene stimata insieme all'omografia;
  4. ogni vetrata viene ricampionata in vista frontale CENTRATA SUL
     SUO VETRO: il riquadro del vetro riconosciuto nel fotogramma,
     riportato sul piano di facciata, viene steso sul rettangolo della
     finestra 3D (larghezza x davanzale..chiave), che e' esattamente
     lo spazio texture usato da build_window_photo_overlays().

Risultato della stima (stampato a ogni esecuzione): distanza laterale
~2.10 m, errore medio ~17 px sui 9 punti; con 1.45 m l'errore sale
a ~74 px. Il valore nel modello NON viene cambiato da qui.

Uso:  .venv/bin/python vetrate_da_video.py
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import cv2
import numpy as np
from scipy.optimize import least_squares

from church_geometry import (
    FACADE_CENTRAL_WINDOW_ARCH_RISE_M, FACADE_CENTRAL_WINDOW_HEAD_M, FACADE_CENTRAL_WINDOW_SILL_M,
    FACADE_CENTRAL_WINDOW_WIDTH_M, FACADE_SIDE_WINDOW_ARCH_RISE_M, FACADE_SIDE_WINDOW_HEAD_M,
    FACADE_SIDE_WINDOW_OFFSET_M, FACADE_SIDE_WINDOW_SILL_M, FACADE_SIDE_WINDOW_WIDTH_M,
)

QUI = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(QUI, "video", "IMG_9756.mov")
ISTANTE_S = 4.0
PX_PER_M = 300

# (file, centro orizzontale con segno: -1 Est, 0 centro, +1 Ovest)
# Dall'interno, guardando la facciata, l'Ovest (+v) e' a DESTRA.
VETRATE = [
    ("vetrata_facciata_est.jpg", -1),
    ("vetrata_facciata_centrale.jpg", 0),
    ("vetrata_facciata_ovest.jpg", +1),
]


def fotogramma() -> np.ndarray:
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ISTANTE_S), "-i", VIDEO,
                        "-frames:v", "1", "-q:v", "2", f, "-y"], check=True)
        return cv2.imread(f)


def vetri(im: np.ndarray):
    """Maschere dei vetri colorati: (etichette, indici delle 3 vetrate da sinistra a destra)."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 1] > 90) & (hsv[..., 2] > 110)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    grandi = sorted([i for i in range(1, n) if st[i, 4] > 50000], key=lambda i: st[i, 0])
    return lab, grandi


def angoli(im: np.ndarray) -> np.ndarray:
    """Per ogni vetrata, da sinistra a destra: basso-sx, basso-dx, chiave."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 1] > 90) & (hsv[..., 2] > 110)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    grandi = sorted([i for i in range(1, n) if st[i, 4] > 50000], key=lambda i: st[i, 0])
    if len(grandi) != 3:
        raise SystemExit(f"attese 3 vetrate, trovate {len(grandi)}")
    out = []
    for i in grandi:
        ys, xs = np.nonzero(lab == i)
        p = np.c_[xs, ys].astype(float)
        out += [p[np.argmax(-xs + ys)], p[np.argmax(xs + ys)], p[np.argmin(ys)]]
    return np.array(out)


def punti_facciata(d: float) -> np.ndarray:
    ws, wc = FACADE_SIDE_WINDOW_WIDTH_M, FACADE_CENTRAL_WINDOW_WIDTH_M
    s0, c0 = FACADE_SIDE_WINDOW_SILL_M, FACADE_CENTRAL_WINDOW_SILL_M
    ts = FACADE_SIDE_WINDOW_HEAD_M + FACADE_SIDE_WINDOW_ARCH_RISE_M
    tc = FACADE_CENTRAL_WINDOW_HEAD_M + FACADE_CENTRAL_WINDOW_ARCH_RISE_M
    return np.array([[-d - ws / 2, s0], [-d + ws / 2, s0], [-d, ts],
                     [-wc / 2, c0], [wc / 2, c0], [0, tc],
                     [d - ws / 2, s0], [d + ws / 2, s0], [d, ts]])


def proietta(h: np.ndarray, P: np.ndarray) -> np.ndarray:
    H = np.append(h, 1).reshape(3, 3)
    q = np.c_[P, np.ones(len(P))] @ H.T
    return q[:, :2] / q[:, 2:]


def stima(px: np.ndarray):
    d0 = FACADE_SIDE_WINDOW_OFFSET_M
    H0, _ = cv2.findHomography(punti_facciata(d0), px)
    x0 = np.append((H0 / H0[2, 2]).ravel()[:8], d0)
    r = least_squares(lambda p: (proietta(p[:8], punti_facciata(p[8])) - px).ravel(), x0, x_scale="jac")
    errore = float(np.sqrt(np.mean(r.fun ** 2)))
    return np.append(r.x[:8], 1).reshape(3, 3), float(r.x[8]), errore


def raddrizza(im: np.ndarray, H: np.ndarray, xc: float, larghezza: float, w0: float, w1: float,
              dim_m: tuple[float, float] | None = None) -> np.ndarray:
    """Ricampiona il rettangolo (xc +- larghezza/2, w0..w1) del piano di
    facciata; l'immagine ha le dimensioni dim_m = (larghezza, altezza) in
    metri (di default quelle del rettangolo stesso)."""
    dl, dh = dim_m or (larghezza, w1 - w0)
    W, Hh = int(dl * PX_PER_M), int(dh * PX_PER_M)
    xs = xc - larghezza / 2 + (np.arange(W) + 0.5) / W * larghezza
    ws = w1 - (np.arange(Hh) + 0.5) / Hh * (w1 - w0)    # riga 0 = chiave (in alto)
    X, Y = np.meshgrid(xs, ws)
    q = np.stack([X, Y, np.ones_like(X)], -1) @ H.T
    mx = (q[..., 0] / q[..., 2]).astype(np.float32)
    my = (q[..., 1] / q[..., 2]).astype(np.float32)
    return cv2.remap(im, mx, my, cv2.INTER_CUBIC)


def main() -> None:
    im = fotogramma()
    H, d, err = stima(angoli(im))
    lab, comp = vetri(im)
    print(f"distanza vetrate laterali dall'asse: {d:.3f} m (modello: {FACADE_SIDE_WINDOW_OFFSET_M} m), "
          f"errore medio {err:.1f} px")
    for nome, lato in VETRATE:
        if lato == 0:
            larg, w0 = FACADE_CENTRAL_WINDOW_WIDTH_M, FACADE_CENTRAL_WINDOW_SILL_M
            w1 = FACADE_CENTRAL_WINDOW_HEAD_M + FACADE_CENTRAL_WINDOW_ARCH_RISE_M
        else:
            larg, w0 = FACADE_SIDE_WINDOW_WIDTH_M, FACADE_SIDE_WINDOW_SILL_M
            w1 = FACADE_SIDE_WINDOW_HEAD_M + FACADE_SIDE_WINDOW_ARCH_RISE_M
        # centrata sul SUO vetro: il riquadro del vetro riconosciuto nel
        # fotogramma, riportato sul piano di facciata, riempie la finestra 3D
        k = [-1, 0, 1].index(lato)
        ys, xs = np.nonzero(lab == comp[k])
        q = np.c_[xs, ys, np.ones(len(xs))] @ np.linalg.inv(H).T
        X, Wq = q[:, 0] / q[:, 2], q[:, 1] / q[:, 2]
        x0, x1 = np.percentile(X, [0.3, 99.7])
        v0, v1 = np.percentile(Wq, [0.3, 99.7])
        print(f"{nome}: vetro nel piano x {x0:.2f}..{x1:.2f} m, quota {v0:.2f}..{v1:.2f} m "
              f"(finestra 3D: larga {larg:.2f}, {w0:.2f}..{w1:.2f} m)")
        out = raddrizza(im, H, (x0 + x1) / 2, x1 - x0, v0, v1, (larg, w1 - w0))
        dest = os.path.join(QUI, "photos", nome)
        cv2.imwrite(dest, out, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(f"{nome}: {out.shape[1]}x{out.shape[0]} px")


if __name__ == "__main__":
    main()
