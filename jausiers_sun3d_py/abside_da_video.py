#!/usr/bin/env python3
"""
abside_da_video.py
------------------
Foto dell'interno dell'abside, CENTRATA sulla geometria vera del modello,
da due video:

  IMG_9759.mov  camminata lungo la navata centrale: l'ultimo fotogramma
                vede l'abside dall'asse, simmetrica (fonte PRINCIPALE);
  IMG_9760.mov  panoramica ravvicinata dal pavimento alla volta, presa
                da sinistra (riempie cio' che la prima non vede).

Per ogni fonte:
  1. immagine: un fotogramma, oppure il mosaico della panoramica
     (foto_da_video.mosaico, camera che ruota su se stessa);
  2. focale: stimata con la posa (fotogramma) o dalla rotazione fra
     fotogrammi (mosaico; ~860 px su 1920 = grandangolo 0.5x);
  3. posizione e orientamento della camera dalle vetrate dell'abside
     visibili (chiave e davanzale; posizioni 3D da church_geometry.py),
     con vincoli morbidi noti (altezza ~1.5 m; sull'asse per IMG_9759);
  4. ogni punto della parete dell'abside (stesso percorso del pannello
     curvo: raccordo Ovest, 5 lati del pentagono, raccordo Est; da
     APSE_PHOTO_HEIGHT_BOTTOM a APSE_PHOTO_HEIGHT_TOP) viene proiettato
     nell'immagine: la texture e' lo "sviluppo" della parete vera;
  5. RIFINITURA: le vetrate della foto vengono portate ESATTAMENTE sulle
     vetrate del modello (quelle rosse). Ogni punto misurato viene
     riproiettato sulla parete per sapere dove cade nella texture; una
     deformazione morbida (thin-plate spline, bordi fermi) lo sposta
     sulla posizione del modello.

Le due texture si uniscono: vale la principale, l'altra riempie i buchi.

Uso:  .venv/bin/python abside_da_video.py
"""
from __future__ import annotations

import math
import os
import subprocess
import tempfile

import cv2
import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.optimize import least_squares

from church_geometry import default_church
from foto_da_video import fotogrammi, mosaico
from reference_photos import APSE_PHOTO_HEIGHT_BOTTOM, APSE_PHOTO_HEIGHT_TOP

QUI = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(QUI, "photos", "abside_interno.jpg")
PX_PER_M = 100
BIANCO = np.array((240, 245, 247), np.uint8)

AB = ["Abside - lato corto Ovest", "Abside - pannello smussato Ovest", "Abside - pannello di fondo",
      "Abside - pannello smussato Est", "Abside - lato corto Est"]

# Punti misurati: nome vetrata -> {"chiave": (x, y), "davanzale": (x, y)}
FONTI = [
    dict(  # principale: vista dall'asse, ultimo tratto della camminata
        nome="IMG_9759 (asse)", video="video/IMG_9759.mov", dalla_fine_s=0.9,
        su_asse=True,
        punti={
            AB[1]: {"chiave": (1505, 310), "davanzale": (1510, 495)},
            AB[2]: {"davanzale": (1867, 570)},          # chiave dietro il lampadario
            AB[3]: {"chiave": (2200, 340), "davanzale": (2205, 527)},
        },
    ),
    dict(  # riempimento: panoramica ravvicinata (mosaico, fotogramma di riferimento = quello di mezzo)
        nome="IMG_9760 (panoramica)", video="video/IMG_9760.mov", mosaico=True,
        su_asse=False,
        punti={
            AB[1]: {"chiave": (1252, 593), "davanzale": (1248, 735)},
            AB[2]: {"chiave": (1470, 744), "davanzale": (1470, 862)},
            AB[3]: {"chiave": (1708, 773), "davanzale": (1708, 873)},
            AB[4]: {"chiave": (1926, 588), "davanzale": (1930, 705)},
        },
    ),
]


def _rod(v):
    return cv2.Rodrigues(np.asarray(v, np.float64).reshape(3, 1))[0]


def _focale_da_rotazione(imgs) -> float:
    sift, bf = cv2.SIFT_create(4000), cv2.BFMatcher()
    F = [sift.detectAndCompute(cv2.cvtColor(i, cv2.COLOR_BGR2GRAY), None) for i in imgs]

    def H(a, b):
        (ka, da), (kb, db) = F[a], F[b]
        m = [x for x, y in bf.knnMatch(db, da, k=2) if x.distance < 0.7 * y.distance]
        return cv2.findHomography(np.float32([kb[x.queryIdx].pt for x in m]),
                                  np.float32([ka[x.trainIdx].pt for x in m]), cv2.RANSAC, 3.0)[0]
    h0, w0 = imgs[0].shape[:2]
    coppie = [H(i, i + 6) for i in range(0, len(imgs) - 6, 2)]

    def err(f):
        K = np.array([[f, 0, w0 / 2], [0, f, h0 / 2], [0, 0, 1.0]]); Ki = np.linalg.inv(K); e = 0.0
        for h in coppie:
            M = Ki @ h @ K; M /= np.cbrt(np.linalg.det(M)); e += np.sum((M @ M.T - np.eye(3)) ** 2)
        return e
    fs = np.arange(600, 4000, 10)
    return float(fs[int(np.argmin([err(f) for f in fs]))])


def immagine(fonte):
    video = os.path.join(QUI, fonte["video"])
    with tempfile.TemporaryDirectory() as tmp:
        if fonte.get("mosaico"):
            imgs = fotogrammi(video, tmp)
            mos, centro = mosaico(imgs, len(imgs) // 2)
            return mos, centro, _focale_da_rotazione(imgs)
        durata = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
        f_img = os.path.join(tmp, "f.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(durata - fonte["dalla_fine_s"]), "-i", video,
                        "-frames:v", "1", "-q:v", "2", f_img, "-y"], check=True)
        im = cv2.imread(f_img)
        return im, (im.shape[1] / 2, im.shape[0] / 2), None


def _punti(church, fonte):
    W = {w.name: w for w in church.windows}
    P3, px, chi = [], [], []
    for n, d in fonte["punti"].items():
        w = W[n]; u, v = w.wall_point_uv
        for tipo, xy in d.items():
            h = w.head_m + w.arch_rise_m if tipo == "chiave" else w.sill_m
            P3.append((u, v, h)); px.append(xy); chi.append((n, tipo))
    return np.array(P3, float), np.array(px, float), chi


def posa(church, fonte, cx, cy, f_noto):
    P3, px, _ = _punti(church, fonte)
    libera_f = f_noto is None

    def unpack(p):
        return _rod(p[:3]), p[3:6], (p[6] if libera_f else f_noto)

    def proj(p, P):
        R, C, f = unpack(p)
        q = (P - C) @ R.T
        return np.c_[cx + f * q[:, 0] / q[:, 2], cy + f * q[:, 1] / q[:, 2]], q[:, 2]

    def res(p):
        r = [(proj(p, P3)[0] - px).ravel(), [20 * (p[5] - 1.5)]]
        if fonte["su_asse"]:
            r.append([30 * p[4]])
        return np.concatenate(r)

    R0 = np.array([[0, -1, 0], [0, 0, -1], [1, 0, 0]], float)  # guarda verso +u, destra = -v
    best = None
    for u0 in (8, 12, 16, 20, 23):
        for v0 in ((0,) if fonte["su_asse"] else (1.5, 3)):
            for pitch in (0.0, 0.2, 0.4, 0.6):
                for f0 in ((1200, 1700, 2500) if libera_f else (None,)):
                    x0 = np.r_[cv2.Rodrigues(_rod([-pitch, 0, 0]) @ R0)[0].ravel(), u0, v0, 1.5]
                    if libera_f:
                        x0 = np.r_[x0, f0]
                    r = least_squares(res, x0, x_scale="jac")
                    e = float(np.sqrt(np.mean((proj(r.x, P3)[0] - px) ** 2)))
                    if (best is None or e < best[0]) and np.all(proj(r.x, P3)[1] > 0):
                        best = (e, r.x)
    e, p = best
    return unpack(p), e


def percorso(church):
    L, Wh = church.nave_length_m, church.nave_width_m / 2.0
    vv = [(L, Wh)] + church.apse_vertices() + [(L, -Wh)]
    cum = [0.0]
    for a, b in zip(vv, vv[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return vv, cum


def sviluppa(img, cx, cy, R, C, f, vv, cum):
    """Texture (n_v x n_u) della parete vista dalla camera, e maschera dei pixel validi."""
    tot = cum[-1]
    n_u = int(tot * PX_PER_M)
    n_v = int((APSE_PHOTO_HEIGHT_TOP - APSE_PHOTO_HEIGHT_BOTTOM) * PX_PER_M)
    s = (np.arange(n_u) + 0.5) / PX_PER_M
    U = np.interp(s, cum, [q[0] for q in vv]); V = np.interp(s, cum, [q[1] for q in vv])
    Wq = APSE_PHOTO_HEIGHT_TOP - (np.arange(n_v) + 0.5) / PX_PER_M
    UU, WW = np.meshgrid(U, Wq); VV, _ = np.meshgrid(V, Wq)
    q = (np.stack([UU, VV, WW], -1).reshape(-1, 3) - C) @ R.T
    ok = q[:, 2] > 0.1
    z = np.where(ok, q[:, 2], 1)
    x = np.where(ok, cx + f * q[:, 0] / z, -1).reshape(n_v, n_u).astype(np.float32)
    y = np.where(ok, cy + f * q[:, 1] / z, -1).reshape(n_v, n_u).astype(np.float32)
    out = cv2.remap(img, x, y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return out, out.sum(-1) > 0


def _texture_xy(s, w, n_v):
    return s * PX_PER_M, (APSE_PHOTO_HEIGHT_TOP - w) * PX_PER_M


def coppie_vetrate(church, fonte, cx, cy, R, C, f, vv, cum):
    """Per ogni punto misurato: dove cade nella texture (riproiettato sulla
    parete del suo lato) e dove dovrebbe cadere (vetrata del modello)."""
    W = {w.name: w for w in church.windows}
    _, px, chi = _punti(church, fonte)
    reali, giusti = [], []
    for (n, tipo), (x, y) in zip(chi, px):
        k = AB.index(n) + 1                    # lato k del percorso (0 = raccordo Ovest)
        a, b = np.array(vv[k]), np.array(vv[k + 1])
        d = R.T @ np.array([(x - cx) / f, (y - cy) / f, 1.0])
        # intersezione del raggio con il piano verticale del lato
        t_dir = (b - a) / np.linalg.norm(b - a); nrm = np.array([-t_dir[1], t_dir[0]])
        lam = np.dot(a - C[:2], nrm) / np.dot(d[:2], nrm)
        P = C + lam * d
        s_reale = cum[k] + np.dot(P[:2] - a, t_dir)
        w = W[n]
        h = w.head_m + w.arch_rise_m if tipo == "chiave" else w.sill_m
        s_giusto = (cum[k] + cum[k + 1]) / 2
        reali.append((s_reale, P[2])); giusti.append((s_giusto, h))
    return np.array(reali), np.array(giusti)


def rifinisci(tex, reali, giusti):
    """Thin-plate spline: i punti 'reali' della texture vanno sui 'giusti';
    i bordi restano fermi."""
    n_v, n_u = tex.shape[:2]
    def to_px(a):
        return np.c_[a[:, 0] * PX_PER_M, (APSE_PHOTO_HEIGHT_TOP - a[:, 1]) * PX_PER_M]
    dst, src = to_px(giusti), to_px(reali)
    bordo = [(x, y) for x in np.linspace(0, n_u, 9) for y in (0, n_v)] + \
            [(x, y) for x in (0, n_u) for y in np.linspace(0, n_v, 5)]
    bordo = np.array(bordo, float)
    rbf = RBFInterpolator(np.vstack([dst, bordo]), np.vstack([src - dst, np.zeros_like(bordo)]),
                          kernel="thin_plate_spline", smoothing=1.0)
    yy, xx = np.mgrid[0:n_v, 0:n_u].astype(np.float32)
    off = rbf(np.c_[xx.ravel(), yy.ravel()]).reshape(n_v, n_u, 2).astype(np.float32)
    return cv2.remap(tex, xx + off[..., 0], yy + off[..., 1], cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)


# Zone della vista principale (IMG_9759) con persone e panche in primo
# piano, in metri sulla parete sviluppata: (s da, s a, quota da, quota a).
# Li' vale la panoramica IMG_9760, che riprende la stessa parete senza
# persone; il passaggio e' sfumato su SFUMATURA_M.
ZONE_PERSONE = [
    (12.6, 15.2, 0.5, 2.9),   # le due persone in piedi davanti all'altare
    (15.6, 19.9, 0.5, 2.5),   # le persone sedute sulla panca
    (0.0, 26.2, 0.5, 1.15),   # schienali delle panche lungo il bordo basso
]
SFUMATURA_M = 0.25


def togli_persone(finale, texture):
    (_, _), (sec, sec_ok) = texture[0], texture[1]
    n_v, n_u = finale.shape[:2]
    m = np.zeros((n_v, n_u), np.float32)
    for s0, s1, w0, w1 in ZONE_PERSONE:
        x0, x1 = int(s0 * PX_PER_M), int(s1 * PX_PER_M)
        y0, y1 = int((APSE_PHOTO_HEIGHT_TOP - w1) * PX_PER_M), int((APSE_PHOTO_HEIGHT_TOP - w0) * PX_PER_M)
        m[max(y0, 0):min(y1, n_v), max(x0, 0):min(x1, n_u)] = 1.0
    k = int(SFUMATURA_M * PX_PER_M) | 1
    m = cv2.GaussianBlur(m, (2 * k + 1, 2 * k + 1), k / 2)
    m *= sec_ok.astype(np.float32)
    out = finale.astype(np.float32) * (1 - m[..., None]) + sec.astype(np.float32) * m[..., None]
    return out.clip(0, 255).astype(np.uint8)


def main() -> None:
    church = default_church()
    vv, cum = percorso(church)
    finale = None
    texture = []
    for fonte in FONTI:
        img, (cx, cy), f_noto = immagine(fonte)
        (R, C, f), err = posa(church, fonte, cx, cy, f_noto)
        tex, _ = sviluppa(img, cx, cy, R, C, f, vv, cum)
        reali, giusti = coppie_vetrate(church, fonte, cx, cy, R, C, f, vv, cum)
        scarto = np.abs(reali - giusti).max(0)
        tex = rifinisci(tex, reali, giusti)
        valido = tex.sum(-1) > 0
        print(f"{fonte['nome']}: camera (u, v, w) = {np.round(C, 2)} m, focale {f:.0f} px, "
              f"errore {err:.1f} px; vetrate spostate al massimo di "
              f"{scarto[0]:.2f} m in orizzontale e {scarto[1]:.2f} m in verticale")
        texture.append((tex, valido))
        if os.environ.get("ABSIDE_DEBUG"):
            cv2.imwrite(os.path.join(os.environ["ABSIDE_DEBUG"], f"tex_{len(texture)}.jpg"), tex)
        if finale is None:
            finale = tex.copy(); pieno = valido
        else:
            buco = ~pieno & valido
            finale[buco] = tex[buco]; pieno |= valido
    finale = togli_persone(finale, texture)
    finale[~pieno & (finale.sum(-1) == 0)] = BIANCO
    cv2.imwrite(USCITA, finale, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{USCITA}: {finale.shape[1]}x{finale.shape[0]} px")


if __name__ == "__main__":
    main()
