#!/usr/bin/env python3
"""
tetto_muri_da_video.py
----------------------
Texture ripetibili del TETTO (scandole di legno) e dei MURI esterni
(intonaco grezzo) dal video IMG_9765.mov, ripreso dalla collina: la
chiesa vista dall'alto, fotogramma a 0.6 s (3840 x 2160).

  tetto: un quadrilatero sulla falda Est della navata (gronda e
         direzione verso il colmo) raddrizzato in vista frontale; scala
         dalle scandole, larghe ~0.11 m (vista raddrizzata isotropa:
         ~337 px/m). Tolto il riflesso chiaro
         (inpaint), corretta la luce (divisione per la media locale),
         ritagliate 2 file esatte sopra la barra paraneve e
         raccordati i bordi a destra/sinistra: si ripete senza giunture.
         -> photos/tetto_esterno.jpg, TETTO_TEXTURE_M x TETTO_TEXTURE_M[1]
  muri:  un tratto pulito di intonaco sul fianco: suo colore medio e
         contrasto della grana; grana rifatta come rumore periodico con
         macchioline scure sparse (si ripete senza giunture). -> photos/muro_esterno.jpg, MURO_TEXTURE_M per lato

Uso:  .venv/bin/python tetto_muri_da_video.py
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import cv2
import numpy as np

from reference_photos import MURO_TEXTURE_M, TETTO_TEXTURE_M

QUI = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(QUI, "video", "IMG_9765.mov")
PX_PER_M = 337


def fotogramma(t=0.6):
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.png")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", VIDEO, "-frames:v", "1", f, "-y"], check=True)
        return cv2.imread(f)


def luce_uniforme(im, sigma):
    f = im.astype(np.float32)
    media = cv2.GaussianBlur(f, (0, 0), sigma)
    return (f / np.maximum(media, 1) * f.reshape(-1, 3).mean(0)).clip(0, 255)


def _bordi_file(g):
    """Quote (y) delle righe scure fra una fila di scandole e l'altra."""
    prof = cv2.GaussianBlur(g.mean(1).reshape(-1, 1).astype(np.float32), (1, 15), 0).ravel()
    H = len(prof)
    minimi = [y for y in range(8, H - 8) if prof[y] == prof[max(0, y - 30):y + 31].min()]
    return minimi


def tetto(im):
    v = np.array([-450., -420.])                      # verso il colmo, nella foto
    A, B = np.array([2050., 1370.]), np.array([2600., 1205.])
    src = np.float32([A + 0.6 * v, B + 0.6 * v, B, A])
    W, H = 900, 560
    r = cv2.warpPerspective(im, cv2.getPerspectiveTransform(src, np.float32([[0, 0], [W, 0], [W, H], [0, H]])), (W, H))
    # riflesso chiaro (striscia bianca) via; luce uniforme
    g = cv2.cvtColor(r, cv2.COLOR_BGR2GRAY)
    m = cv2.dilate((g > 170).astype(np.uint8) * 255, np.ones((9, 9), np.uint8))
    r = cv2.inpaint(r, m, 7, cv2.INPAINT_TELEA)
    r = luce_uniforme(r, 60)
    # due file esatte, sopra la barra paraneve (righe fra le file a y = 106,
    # 229, 348 nella vista raddrizzata; la barra e' a y ~ 350-380)
    y0, y1 = 106, 348
    t = r[y0:y1]
    # raccordo destra/sinistra
    k = 80
    a = np.linspace(0, 1, k)[None, :, None]
    t = np.concatenate([t[:, -k:] * (1 - a) + t[:, :k] * a, t[:, k:-k]], axis=1)
    print(f"tetto: due file y {y0}..{y1} = {(y1 - y0) / PX_PER_M:.2f} m, "
          f"larghezza {t.shape[1] / PX_PER_M:.2f} m")
    return cv2.resize(t, (int(TETTO_TEXTURE_M[0] * PX_PER_M), int(TETTO_TEXTURE_M[1] * PX_PER_M))), (y1 - y0) / PX_PER_M / 2


def muro(im):
    """Intonaco: colore medio e contrasto della grana dal tratto pulito del
    video, grana rifatta come rumore PERIODICO (filtrato in frequenza: si
    ripete senza giunture e senza il disegno a specchio) piu' macchioline
    scure sparse, come nell'intonaco grezzo della foto."""
    p = im[1700:1790, 2305:2395].astype(np.float32)     # sotto una finestra, intonaco pulito
    colore = np.median(p.reshape(-1, 3), axis=0)
    lum = cv2.cvtColor(p.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    contrasto = float((lum - cv2.GaussianBlur(lum, (0, 0), 6)).std())
    n = int(MURO_TEXTURE_M * 256)
    rng = np.random.default_rng(9765)
    fy, fx = np.meshgrid(np.fft.fftfreq(n), np.fft.fftfreq(n), indexing="ij")
    f = np.hypot(fx, fy)

    def rumore(scala_px):
        r = np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((n, n))) * np.exp(-(f * scala_px) ** 2)))
        return r / r.std()

    grana = 0.8 * rumore(1.5) + 0.5 * rumore(6) + 0.35 * rumore(30)
    macchie = np.zeros((n, n), np.float32)
    for _ in range(int(140 * MURO_TEXTURE_M ** 2)):
        y, x, r = rng.integers(0, n), rng.integers(0, n), rng.uniform(0.8, 2.8)
        for dy in (-n, 0, n):
            for dx in (-n, 0, n):
                cv2.circle(macchie, (int(x + dx), int(y + dy)), int(round(r)), float(rng.uniform(0.6, 1.0)), -1)
    macchie = cv2.GaussianBlur(macchie, (0, 0), 0.8)
    t = colore[None, None, :] + contrasto * grana[..., None] - 45 * macchie[..., None]
    return t.clip(0, 255)


def main():
    im = fotogramma()
    t, fila = tetto(im)
    cv2.imwrite(os.path.join(QUI, "photos", "tetto_esterno.jpg"), t.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"tetto_esterno.jpg: {t.shape[1]}x{t.shape[0]} px, {TETTO_TEXTURE_M} m (file di scandole ~{fila:.2f} m)")
    m = muro(im)
    cv2.imwrite(os.path.join(QUI, "photos", "muro_esterno.jpg"), m.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"muro_esterno.jpg: {m.shape[1]}x{m.shape[0]} px, {MURO_TEXTURE_M} m per lato")


if __name__ == "__main__":
    main()
