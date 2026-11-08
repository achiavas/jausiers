#!/usr/bin/env python3
"""
pavimento_da_video.py
---------------------
Texture del pavimento della chiesa dal primo fotogramma del video
IMG_9757.mov (ripreso dal corridoio centrale, guardando verso l'abside).

  1. vista dall'alto del pavimento: il punto di fuga delle due fasce ocra
     del corridoio da' la direzione dell'asse; con la focale (~1708 px su
     3840, grandangolo 0.5x come IMG_9759) e l'altezza della camera
     (ALTEZZA_CAMERA_M, stimata: telefono in mano) ogni punto a terra si
     proietta nel fotogramma;
  2. pietra: un riquadro fra le due fasce, vicino alla camera (dove la foto
     e' piu' nitida), specchiato per ripetersi senza giunture;
  3. corridoio: la striscia reale con le fasce ocra (CORRIDOIO_M per lato
     dall'asse), resa uniforme lungo l'asse (mediana per colonna, piu' un
     po' della grana della pietra);
  4. texture finale: una "piastrella" lunga PAVIMENTO_PERIODO_M lungo la
     navata e larga PAVIMENTO_LARGHEZZA_M di traverso (copre navata e
     cappelle), con il corridoio al centro (v = 0). I viewer la ripetono
     lungo la navata.

Uso:  .venv/bin/python pavimento_da_video.py
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import cv2
import numpy as np

from reference_photos import PAVIMENTO_LARGHEZZA_M, PAVIMENTO_PERIODO_M

QUI = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(QUI, "video", "IMG_9757.mov")
USCITA = os.path.join(QUI, "photos", "pavimento.jpg")
FOCALE = 1708.0
ALTEZZA_CAMERA_M = 1.5
CORRIDOIO_M = 0.75          # mezza larghezza della striscia con le fasce ocra
PX_PER_M = 60


def fotogramma():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.1", "-i", VIDEO, "-frames:v", "1",
                        "-q:v", "2", f, "-y"], check=True)
        return cv2.imread(f)


def punto_di_fuga(im):
    """Intersezione delle due fasce ocra del corridoio (rette x = a y + b)."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] >= 8) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 70) & (hsv[..., 2] > 120)).astype(np.uint8)
    h, w = m.shape
    m[: int(h * 0.53)] = 0; m[:, : int(w * 0.3)] = 0; m[:, int(w * 0.7):] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    rette = []
    for i in sorted(range(1, n), key=lambda i: -st[i, 4])[:2]:
        ys, xs = np.nonzero(lab == i)
        pts = np.array([(xs[ys == y].mean(), y) for y in range(ys.min(), ys.max(), 10) if (ys == y).sum() > 3])
        rette.append(np.polyfit(pts[:, 1], pts[:, 0], 1))
    (a1, b1), (a2, b2) = rette
    y = (b2 - b1) / (a1 - a2)
    return a1 * y + b1, y


def dall_alto(im, X, Z):
    """Pavimento visto dall'alto: X a destra, Z avanti lungo il corridoio."""
    cx, cy = im.shape[1] / 2, im.shape[0] / 2
    vx, vy = punto_di_fuga(im)
    d = np.array([(vx - cx) / FOCALE, (vy - cy) / FOCALE, 1.0]); d /= np.linalg.norm(d)
    up = np.array([0, -1.0, 0]); up -= up.dot(d) * d; up /= np.linalg.norm(up)
    right = np.cross(up, d)
    XX, ZZ = np.meshgrid(X, Z)
    P = XX[..., None] * right + ZZ[..., None] * d - ALTEZZA_CAMERA_M * up
    mx = (cx + FOCALE * P[..., 0] / P[..., 2]).astype(np.float32)
    my = (cy + FOCALE * P[..., 1] / P[..., 2]).astype(np.float32)
    return cv2.remap(im, mx, my, cv2.INTER_LINEAR)


def main() -> None:
    im = fotogramma()
    k = PX_PER_M
    # zona vicina alla camera: 2-4.5 m davanti, la piu' nitida
    Z = np.arange(4.5, 2.0, -1 / k)
    pietra = dall_alto(im, np.arange(-0.38, 0.38, 1 / k), Z)
    corr = dall_alto(im, np.arange(-CORRIDOIO_M, CORRIDOIO_M, 1 / k), Z)

    # pietra ripetibile: specchiata in orizzontale e verticale
    t = np.vstack([np.hstack([pietra, pietra[:, ::-1]]), np.hstack([pietra[::-1], pietra[::-1, ::-1]])])
    # solo la grana fine della pietra (luminanza, passa-alto) sul suo colore
    # medio: i riflessi colorati delle vetrate sul pavimento lucido, ripetuti,
    # farebbero un motivo a macchie
    t = t.astype(np.float32)
    colore = np.median(t.reshape(-1, 3), axis=0)
    lum = cv2.cvtColor(t.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    grana = lum - cv2.GaussianBlur(lum, (0, 0), 4)
    t = (colore[None, None, :] + 1.2 * grana[..., None]).clip(0, 255)

    W, H = int(PAVIMENTO_LARGHEZZA_M * k), int(PAVIMENTO_PERIODO_M * k)
    reps = (int(np.ceil(H / t.shape[0])), int(np.ceil(W / t.shape[1])), 1)
    out = np.tile(t, reps)[:H, :W]

    # corridoio: colore per colonna (mediana lungo l'asse) + grana della pietra
    profilo = np.median(corr.astype(np.float32), axis=0)           # (larghezza, 3)
    # il colore di fondo del corridoio = quello della pietra (niente riflessi):
    # resta solo la differenza delle fasce ocra
    base = np.median(profilo, axis=0)
    profilo = profilo - base + colore
    grana = out - out.reshape(-1, 3).mean(0)
    x0 = W // 2 - corr.shape[1] // 2
    banda = profilo[None, :, :] + grana[:, x0:x0 + corr.shape[1]] * 0.6
    # sfuma i bordi della banda nella pietra
    w = np.clip(np.minimum(np.arange(corr.shape[1]), np.arange(corr.shape[1])[::-1]) / (0.08 * k), 0, 1)
    out[:, x0:x0 + corr.shape[1]] = out[:, x0:x0 + corr.shape[1]] * (1 - w[None, :, None]) + banda * w[None, :, None]
    cv2.imwrite(USCITA, out.clip(0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{USCITA}: {W}x{H} px ({PAVIMENTO_LARGHEZZA_M} x {PAVIMENTO_PERIODO_M} m, si ripete lungo la navata)")


if __name__ == "__main__":
    main()
