#!/usr/bin/env python3
"""
vetrate_laterali_da_foto.py
---------------------------
Foto RADDRIZZATE delle vetrate laterali dalle foto dell'utente
video/vetrate_laterali/a.jpg ... i.jpg (prese dal basso, vetrata chiara
su fondo scuro).

Giro (a..h): dalla prima a sinistra entrando lungo il lato Ovest verso
l'abside (a, b, c, d), poi il lato Est dall'abside verso l'ingresso (e, f,
g, h). Le vetrate che si fronteggiano sono gemelle: croci (a-h), calici
(b-g), quadrilobi (c-f), reticoli blu (d-e). La i (quadrilobo col
triangolo, sopra una cornice) va sui due lati corti dell'abside.

Per ogni foto:
  1. il vetro si riconosce dal colore (saturo e luminoso sul fondo scuro):
     la sagoma piu' grande;
  2. angoli in basso (a mano dove il riconoscimento sbaglia: MANUALE);
     fianchi = rette interpolate sui bordi sinistro e
     destro nella parte bassa (fino all'imposta dell'arco, che sta a
     (head - sill) / (head + freccia - sill) dell'altezza);
  3. omografia dei 4 punti (angoli in basso, fianchi all'imposta) sul
     rettangolo della finestra del modello: larghezza x davanzale..chiave,
     lo spazio texture di build_window_photo_overlays().
-> photos/vetrata_laterale_<lettera>.jpg

Uso:  .venv/bin/python vetrate_laterali_da_foto.py
"""
from __future__ import annotations

import os

import cv2
import numpy as np

from church_geometry import APSE_WINDOW_WIDTH_M, APSE_WINDOW_SILL_M, APSE_WINDOW_HEAD_M, APSE_WINDOW_ARCH_RISE_M

QUI = os.path.dirname(os.path.abspath(__file__))
CARTELLA = os.path.join(QUI, "video", "vetrate_laterali")
PX_PER_M = 300
LETTERE = "abcdefghi"
# angoli misurati a mano dove il riconoscimento automatico sbaglia
# (b: il bordo basso si confonde con la cornice): basso-sx, basso-dx,
# fianco destro e sinistro all'imposta dell'arco
MANUALE = {"b": [(310, 1740), (1096, 1630), (1100, 703), (366, 729)]}


def sagoma(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = (((hsv[..., 1] > 70) & (hsv[..., 2] > 70)) | (hsv[..., 2] > 200)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(st[1:, 4]))
    return (lab == k).astype(np.uint8)


def punti(m, frazione_imposta):
    ys, xs = np.nonzero(m)
    y0, y1 = ys.min(), ys.max()
    righe = np.arange(int(y0 + (y1 - y0) * 0.45), int(y1 - (y1 - y0) * 0.04))
    righe = np.array([y for y in righe if m[y].any()])
    sx = np.array([np.nonzero(m[y])[0].min() for y in righe])
    dx = np.array([np.nonzero(m[y])[0].max() for y in righe])
    ps, pd = np.polyfit(righe, sx, 1), np.polyfit(righe, dx, 1)
    # bordo basso: retta sui punti piu' bassi fra i due fianchi
    cols = np.arange(int(np.polyval(ps, y1) + 10), int(np.polyval(pd, y1) - 10))
    cols = np.array([x for x in cols if 0 <= x < m.shape[1] and m[:, x].any()])
    basso = np.array([np.nonzero(m[:, x])[0].max() for x in cols])
    pb = np.polyfit(cols, basso, 1)
    # angoli in basso: incrocio dei fianchi col bordo basso
    def incrocio(pf):
        # x = pf0*y + pf1 ; y = pb0*x + pb1
        y = (pb[0] * pf[1] + pb[1]) / (1 - pb[0] * pf[0])
        return np.array([pf[0] * y + pf[1], y])
    bs, bd = incrocio(ps), incrocio(pd)
    ya = y1 - (y1 - y0) * frazione_imposta
    ss, sd = np.array([np.polyval(ps, ya), ya]), np.array([np.polyval(pd, ya), ya])
    return bs, bd, sd, ss


def main():
    larg = APSE_WINDOW_WIDTH_M
    h_imp, h_tot = APSE_WINDOW_HEAD_M - APSE_WINDOW_SILL_M, APSE_WINDOW_HEAD_M + APSE_WINDOW_ARCH_RISE_M - APSE_WINDOW_SILL_M
    W, H = int(larg * PX_PER_M), int(h_tot * PX_PER_M)
    dst = np.float32([(0, H), (W, H), (W, H - h_imp * PX_PER_M), (0, H - h_imp * PX_PER_M)])
    controllo = []
    for l in LETTERE:
        im = cv2.imread(os.path.join(CARTELLA, f"{l}.jpg"))
        src = np.float32(MANUALE[l] if l in MANUALE else punti(sagoma(im), h_imp / h_tot))
        out = cv2.warpPerspective(im, cv2.getPerspectiveTransform(src, dst), (W, H), flags=cv2.INTER_CUBIC)
        cv2.imwrite(os.path.join(QUI, "photos", f"vetrata_laterale_{l}.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 90])
        c = im.copy()
        cv2.polylines(c, [np.int32(src)], True, (0, 255, 0), 6)
        controllo.append(cv2.resize(c, (300, 400)))
        controllo.append(cv2.resize(out, (int(400 * W / H), 400)))
        print(f"{l}: angoli {np.round(src).astype(int).tolist()}")
    righe = [np.hstack(controllo[i:i + 6]) for i in range(0, 18, 6)]
    w = max(r.shape[1] for r in righe)
    cv2.imwrite(os.path.join(CARTELLA, "_controllo.jpg"), np.vstack([cv2.copyMakeBorder(r, 0, 0, 0, w - r.shape[1], cv2.BORDER_CONSTANT) for r in righe]))


if __name__ == "__main__":
    main()
