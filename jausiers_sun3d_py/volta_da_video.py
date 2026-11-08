#!/usr/bin/env python3
"""
volta_da_video.py
-----------------
Texture della VOLTA DELL'ABSIDE dal fotogramma a 10 s di IMG_9757
(camminata nel corridoio, la camera guarda in alto verso l'abside).

La geometria dell'abside nel modello non coincide al centimetro con
quella vera (vedi APSE_FACET_LENGTHS_M in church_geometry.py: il lato di
fondo e' 3.84 m nel modello contro 6.58 rilevati), quindi niente
proiezione con una camera: la volta viene "sviluppata" come la foto
dell'abside. Ogni punto del bordo della volta del modello
(church_mesh.bordo_volta_abside: i 5 lati con le lunette, poi l'arco
trionfale) ha il suo punto nella foto:
  - spigoli del pentagono = piedi dei costoloni sul cornicione;
  - a meta' di ogni lato la lunetta sale fino alla sua cima (stessa
    legge sqrt(sin) dell'imposta nel modello);
  - l'arco trionfale = mezza ellisse nella foto (imposte e chiave).
Ogni meridiano va dal suo punto del bordo alla rosetta dove convergono i
costoloni (frazione 1 - cos, come la quota del meridiano). Il lampadario
che pende davanti alla volta viene cancellato (inpaint) prima.
-> photos/volta_abside.jpg: colonne = posizione lungo il bordo,
   righe = frazione del meridiano (riga 0 = bordo), come le coordinate
   texture della mesh.

Uso:  .venv/bin/python volta_da_video.py
"""
from __future__ import annotations

import math
import os
import subprocess
import tempfile

import cv2
import numpy as np

from church_geometry import VOLTA_ABSIDE_NA, VOLTA_ABSIDE_NT, default_church
from church_mesh import bordo_volta_abside

QUI = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(QUI, "video", "IMG_9757.mov")
ISTANTE_S = 10.0
USCITA = os.path.join(QUI, "photos", "volta_abside.jpg")

# punti misurati nel fotogramma (3840 x 2160)
CHIAVE = (1844, 443)                                  # rosetta
PIEDI = [(1300, 720), (1454, 732), (1714, 821), (1996, 825), (2221, 743), (2390, 725)]  # spigoli, da Ovest a Est
CIME_LUNETTE = [None, (1614, 589), (1849, 654), (2107, 593), None]   # lati corti: stimate sotto
SALITA_LATI_CORTI = 230                               # px, i lati corti si vedono quasi di taglio
ARCO = dict(centro=(1845, 722), a=545, b=472)          # mezza ellisse dell'arco trionfale


def fotogramma():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.png")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ISTANTE_S), "-i", VIDEO, "-frames:v", "1", f, "-y"], check=True)
        return cv2.imread(f)


def senza_lampadario(im):
    """Cancella i lampadari (oro e cristalli, molto saturi e luminosi) e
    i fili che li reggono."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 1] > 110) & (hsv[..., 2] > 150) & (hsv[..., 0] < 35)).astype(np.uint8) * 255
    m[1100:] = 0
    m = cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)), np.ones((21, 21), np.uint8))
    return cv2.inpaint(im, m, 9, cv2.INPAINT_TELEA)


def bordo_nella_foto() -> np.ndarray:
    """Un punto della foto per ogni punto del bordo della volta del modello."""
    pts = []
    for i in range(5):
        a, b = np.array(PIEDI[i], float), np.array(PIEDI[i + 1], float)
        if CIME_LUNETTE[i] is None:
            salita = np.array([0.0, -SALITA_LATI_CORTI])
        else:
            salita = np.array(CIME_LUNETTE[i], float) - (a + b) / 2
        for k in range(VOLTA_ABSIDE_NT):
            t = k / VOLTA_ABSIDE_NT
            pts.append(a + (b - a) * t + salita * math.sqrt(max(math.sin(math.pi * t), 0.0)))
    (cx, cy), A, B = ARCO["centro"], ARCO["a"], ARCO["b"]
    for k in range(VOLTA_ABSIDE_NA + 1):
        f = math.pi * k / VOLTA_ABSIDE_NA          # da Est (destra nella foto) a Ovest
        pts.append((cx + A * math.cos(f), cy - B * math.sin(f)))
    return np.array(pts)


def main():
    im = senza_lampadario(fotogramma())
    bordo = bordo_nella_foto()
    assert len(bordo) == len(bordo_volta_abside(default_church()))
    W, H = 1800, 420
    s = (np.arange(W) + 0.5) / W * (len(bordo) - 1)
    i0 = np.clip(np.floor(s).astype(int), 0, len(bordo) - 2)
    b = bordo[i0] + (bordo[i0 + 1] - bordo[i0]) * (s - i0)[:, None]           # (W, 2)
    th = (np.arange(H) + 0.5) / H * math.pi / 2
    fr = (1 - np.cos(th))[:, None, None]                                       # (H, 1, 1)
    xy = b[None, :, :] + (np.array(CHIAVE, float)[None, None, :] - b[None, :, :]) * fr
    out = cv2.remap(im, xy[..., 0].astype(np.float32), xy[..., 1].astype(np.float32), cv2.INTER_CUBIC)
    out = out[::-1]                      # riga 0 dell'immagine = chiave (v texture = 1 in alto)
    cv2.imwrite(USCITA, out, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{USCITA}: {W}x{H} px ({len(bordo)} punti del bordo)")


if __name__ == "__main__":
    main()
