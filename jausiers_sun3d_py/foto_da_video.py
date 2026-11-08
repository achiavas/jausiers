#!/usr/bin/env python3
"""
foto_da_video.py
----------------
Da un video (panoramica fatta ruotando il telefono) a una foto
RADDRIZZATA e IN SCALA di una campata della chiesa, pronta per essere
applicata al modello 3D (reference_photos.py / sito).

Passi:
  1. fotogrammi dal video (ffmpeg, 3 al secondo, 1920 px);
  2. mosaico: omografie SIFT+RANSAC fra fotogrammi consecutivi, tutte
     riportate al fotogramma di riferimento (camera che ruota: le
     omografie sono esatte per tutta la scena);
  3. raddrizzamento: punti di fuga delle verticali e delle orizzontali
     (segmenti LSD + RANSAC); la focale si ricava dalla loro
     ortogonalita'; la vista viene ruotata finche' la parete e' frontale;
  4. scala: due riferimenti misurati nell'immagine raddrizzata (centri
     dei pilastri = una campata, CAMPATA_M dalle piantine) e la quota
     del pavimento. Il ritaglio va da un pilastro all'altro.

Le misure in pixel di ogni video sono in VIDEO qui sotto, misurate
sull'immagine raddrizzata (passo 3). Controllo: con questa scala il
cornicione cade a ~11.1 m, appena sotto i davanzali delle vetrate di
cleristorio (11.18 m, CHAPEL_WINDOW_SILL_M): coerente con le piantine.

Richiede OpenCV: usa l'ambiente locale  .venv/bin/python foto_da_video.py
Uso:  .venv/bin/python foto_da_video.py [nome]      (default: tutti)
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np

from church_geometry import (CHAPEL_ROW_MARGIN_M, NAVE_LENGTH_M, N_CHAPELS_PER_SIDE,
                             CHAPEL_ARCH_RADIUS_M, CHAPEL_ARCH_SPRING_M, CHAPEL_PROJECTION_DEPTH_M)

QUI = os.path.dirname(os.path.abspath(__file__))
CAMPATA_M = (NAVE_LENGTH_M - 2 * CHAPEL_ROW_MARGIN_M) / N_CHAPELS_PER_SIDE  # 6.08 m
PX_PER_M_USCITA = 150

# x dei centri dei due pilastri e y del pavimento, in pixel
# dell'immagine raddrizzata; rif = fotogramma di riferimento del mosaico.
VIDEO = {
    "cappella_ovest_1": dict(
        video="video/IMG_9734.mov", rif=12,
        x_pilastro_sx=1655, x_pilastro_dx=4360, y_pavimento=6780,
        nota="prima cappella a sinistra entrando (lato Ovest, u = 4.14 m)",
    ),
    "cappella_est_2": dict(
        video="video/IMG_9738.mov", rif=12,
        x_pilastro_sx=950, x_pilastro_dx=3058, y_pavimento=4276,
        nota="seconda cappella a destra entrando (lato Est, u = 10.22 m). "
             "Pavimento coperto dai banchi: scala e quota presi dalla prima "
             "cappella, con riferimenti uguali in tutte le campate: base dei "
             "capitelli e centro delle croci di consacrazione (4.40 m fra i due, "
             "croce a 3.37 m dal pavimento). Controllo: bordo interno del pilastro "
             "a 0.72 m dal centro, come nella prima cappella; plinto alto ~0.9 m.",
    ),
    "cappella_ovest_4": dict(
        video="video/IMG_9740.mov", rif=12,
        x_pilastro_sx=411, x_pilastro_dx=2789, y_pavimento=5399, px_per_m_verticale=458.0,
        nota="quarta cappella a sinistra entrando (lato Ovest, u = 22.38 m). Pavimento "
             "coperto dai banchi. Scala orizzontale dall'arco: intradosso largo 4.26 m "
             "all'imposta = 1665 px (391 px/m), centro x = 1600; pilastri a +-3.04 m. "
             "Scala VERTICALE diversa (raddrizzamento non isotropo): chiave "
             "dell'intradosso y = 1955 -> imposta y = 2955 (2.13 m) = 458 px/m, "
             "confermata da chiave -> zoccolo (6.57 m, 459 px/m). Pavimento dalla "
             "chiave a 7.52 m; controllo: zoccolo alto 0.94 m.",
    ),
    "cappella_ovest_3": dict(
        video="video/IMG_9742.mov", rif=12,
        x_pilastro_sx=54, x_pilastro_dx=2826, y_pavimento=4718, px_per_m_verticale=476.5, y_alto=1000,
        nota="terza cappella a sinistra entrando (lato Ovest, u = 16.30 m). Scala dall'arco: "
             "intradosso all'imposta da x=490 a x=2390 (raggio ~971 px -> 456 px/m), "
             "centro x = 1440, pilastri a +-3.04 m; in verticale chiave y = 1135 -> imposta "
             "y = 2150 (2.13 m) = 476.5 px/m; pavimento dalla chiave a 7.52 m. La foto non "
             "copre il pilastro sinistro in basso: angoli non coperti bianchi.",
    ),
    # Fotogramma singolo (IMG_9758 a 0.5 s): il video e' una camminata,
    # con parallasse, quindi niente mosaico.
    "cappella_est_4": dict(
        foto="video/cappella_est_4_foto.jpg",
        x_pilastro_sx=389, x_pilastro_dx=2031, y_pavimento=2255, y_alto=280,
        nota="quarta cappella a destra entrando (lato Est, u = 22.38 m). Scala isotropa "
             "(la croce di consacrazione raddrizzata e' un cerchio: 173 x 175 px): "
             "intradosso all'imposta da x=635 a x=1785 = 4.26 m -> 270 px/m, centro "
             "x = 1210, pilastri a +-3.04 m. Pavimento: dall'imposta (5.39 m, y~815) "
             "2270, dalla croce (3.37 m, y=1338) 2248 -> 2255. Chiave dell'arco "
             "fuori foto; angolo in alto a sinistra bianco.",
    ),
    "cappella_ovest_2": dict(
        foto="video/cappella_ovest_2_foto.jpg",
        x_pilastro_sx=2799, x_pilastro_dx=4081, y_pavimento=2370, px_per_m_verticale=214.0, y_alto=930,
        nota="seconda cappella a sinistra entrando (lato Ovest, u = 10.22 m), fotogramma "
             "di IMG_9758 a 21 s (camminata: niente mosaico). Scala dall'arco: intradosso "
             "all'imposta da x=2990 a x=3890 = 4.26 m -> 211 px/m, centro x = 3440, pilastri "
             "a +-3.04 m. Verticale: croce di consacrazione (3.37 m) y=1650 -> chiave "
             "dell'intradosso (7.52 m) y=760 = 214 px/m; pavimento 2370 da entrambe. "
             "Controllo: imposta (5.39 m) a y~1217, all'altezza dei capitelli. In alto la "
             "foto non copre la campata: angoli bianchi.",
    ),
    # Da una FOTO singola (niente mosaico), presa dentro l'arco: i pilastri
    # non si vedono, quindi la scala viene dall'arco stesso, con le misure
    # prese sulle prime due cappelle (stesse misure in tutte le campate):
    # intradosso largo 4.30 m all'imposta, chiave dell'intradosso a 7.52 m.
    # Qui: intradosso all'imposta da x=152 a x=1268 (1116 px -> 259.5 px/m),
    # chiave a y=108; controllo: chiave-imposta 2.09 m contro 2.15 attesi.
    # Il ritaglio e' il rettangolo coperto dalla foto (non tutta la campata).
    "cappella_est_3": dict(
        foto="video/cappella_est_3_foto.jpg",
        px_per_m=259.5, x_centro_campata=710, y_pavimento=2051,
        ritaglio=(215, 130, 1330, 1840),  # x0, y0, x1, y1 nell'immagine raddrizzata
        nota="terza cappella a destra entrando (lato Est, u = 16.30 m), foto dell'utente",
    ),
}


def fotogrammi(video: str, cartella: str) -> list[np.ndarray]:
    subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", "fps=3,scale=1920:-1",
                    "-q:v", "2", os.path.join(cartella, "%03d.jpg"), "-y"], check=True)
    return [cv2.imread(f) for f in sorted(glob.glob(os.path.join(cartella, "*.jpg")))]


def mosaico(imgs: list[np.ndarray], rif: int):
    sift = cv2.SIFT_create(4000)
    feats = [sift.detectAndCompute(cv2.cvtColor(i, cv2.COLOR_BGR2GRAY), None) for i in imgs]
    bf = cv2.BFMatcher()

    def omografia(a, b):  # punti di b -> a
        (ka, da), (kb, db) = feats[a], feats[b]
        m = [x for x, y in bf.knnMatch(db, da, k=2) if x.distance < 0.7 * y.distance]
        pb = np.float32([kb[x.queryIdx].pt for x in m])
        pa = np.float32([ka[x.trainIdx].pt for x in m])
        return cv2.findHomography(pb, pa, cv2.RANSAC, 3.0)[0]

    Hs = {rif: np.eye(3)}
    for i in range(rif + 1, len(imgs)):
        Hs[i] = Hs[i - 1] @ omografia(i - 1, i)
    for i in range(rif - 1, -1, -1):
        Hs[i] = Hs[i + 1] @ omografia(i + 1, i)

    h0, w0 = imgs[0].shape[:2]
    corn = np.float32([[0, 0], [w0, 0], [w0, h0], [0, h0]]).reshape(-1, 1, 2)
    allc = np.vstack([cv2.perspectiveTransform(corn, Hs[i]) for i in Hs])
    x0, y0 = allc.min(0).ravel()
    x1, y1 = allc.max(0).ravel()
    T = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]])
    W, H = int(x1 - x0), int(y1 - y0)
    acc = np.zeros((H, W, 3)); wsum = np.zeros((H, W))
    yy, xx = np.mgrid[0:h0, 0:w0]
    peso = (np.minimum(xx, w0 - xx) * np.minimum(yy, h0 - yy)).astype(np.float32) + 1
    for i in Hs:
        M = T @ Hs[i]
        wi = cv2.warpPerspective(peso, M, (W, H))
        acc += cv2.warpPerspective(imgs[i].astype(np.float32), M, (W, H)) * wi[..., None]
        wsum += wi
    out = (acc / np.maximum(wsum, 1e-6)[..., None]).clip(0, 255).astype(np.uint8)
    out[wsum == 0] = 0
    centro = (w0 / 2 + T[0, 2], h0 / 2 + T[1, 2])
    return out, centro


def punti_di_fuga(img: np.ndarray):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    L = cv2.createLineSegmentDetector().detect(g)[0][:, 0, :]
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1])
    L, ln = L[ln > 60], ln[ln > 60]
    ang = np.degrees(np.arctan2(L[:, 3] - L[:, 1], L[:, 2] - L[:, 0])) % 180
    p = np.c_[L[:, :2], np.ones(len(L))]
    q = np.c_[L[:, 2:], np.ones(len(L))]
    rette = np.cross(p, q)
    rette /= np.linalg.norm(rette[:, :2], axis=1)[:, None]
    medi = (p + q) / 2

    def ransac(sel, tol=2.0):
        R, w, M, P = rette[sel], ln[sel], medi[sel], p[sel]
        rng = np.random.default_rng(0)
        best = (0.0, None)
        for _ in range(4000):
            i, j = rng.choice(len(R), 2, replace=False)
            v = np.cross(R[i], R[j])
            r = np.cross(M, v)
            r /= np.linalg.norm(r[:, :2], axis=1)[:, None]
            inl = np.abs(np.sum(r * P, 1)) < tol
            if w[inl].sum() > best[0]:
                best = (w[inl].sum(), inl)
        inl = best[1]
        return np.linalg.svd(R[inl] * w[inl][:, None])[2][-1]

    return ransac((ang > 60) & (ang < 120)), ransac((ang < 30) | (ang > 150))


def raddrizza(img: np.ndarray, centro, vV, vH) -> np.ndarray:
    c = np.array(centro)
    p1, p2 = vV[:2] / vV[2], vH[:2] / vH[2]
    f = float(np.sqrt(-np.dot(p1 - c, p2 - c)))  # focale dall'ortogonalita'
    K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1]])
    dV = np.linalg.solve(K, vV); dV /= np.linalg.norm(dV)
    dH = np.linalg.solve(K, vH); dH /= np.linalg.norm(dH)
    if dV[1] < 0: dV = -dV
    if dH[0] < 0: dH = -dH
    dH -= (dH @ dV) * dV; dH /= np.linalg.norm(dH)
    Hr = K @ np.vstack([dH, dV, np.cross(dH, dV)]) @ np.linalg.inv(K)
    h, w = img.shape[:2]
    corn = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    cc = cv2.perspectiveTransform(corn, Hr)
    x0, y0 = cc.min(0).ravel(); x1, y1 = cc.max(0).ravel()
    M = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ Hr
    out = cv2.warpPerspective(img, M, (int(x1 - x0), int(y1 - y0)), flags=cv2.INTER_CUBIC)
    mask = cv2.warpPerspective((img.sum(2) > 0).astype(np.uint8) * 255, M, out.shape[1::-1])
    out[mask < 128] = 0
    # la vista raddrizzata e' una camera virtuale (stessa focale, stesso
    # centro di presa) con l'asse ottico perpendicolare alla parete: il
    # suo punto principale nell'immagine d'uscita serve per la profondita'
    return out, (f, float(c[0] - x0), float(c[1] - y0))


# --- Profondita' delle cappelle ------------------------------------
# Dalla vista raddrizzata si ricava dove stava il fotografo: con la
# scala sulla parete (px/m) e la focale f, la distanza dalla parete e'
# D = f / (px/m); il punto principale da' altezza e posizione laterale.
# Ogni punto 3D della nicchia (X a destra nella foto, Y in alto, z in
# profondita' oltre il filo della navata) cade nel pixel
#     x = cx + f (X - Xc) / (D + z),   y = cy - f (Y - Yc) / (D + z).
# Cosi' fondo, fianchi e volta prendono ciascuno la propria parte di
# foto alla scala giusta. Le parti che dal punto di presa non si vedono
# (nascoste dagli stipiti o fuori foto) prendono il grigio dei muri.
NICCHIA_Z0 = -0.15          # le superfici partono dal piano dei pannelli (v = Wh - 0.15)
# BGR: grigio dei muri delle cappelle nelle foto (mediana su pilastri e pareti
# di ovest_1, ovest_2, est_2, est_4), dove la foto non ha dati
GRIGIO_MURI = np.array([176, 182, 188], np.float32)
BIANCO = GRIGIO_MURI


MIN_PX_PER_M = 40.0


def _campiona(img, cam, X, Y, Z, assi, normale=None):
    """Colore della foto per i punti 3D (X, Y, Z) di una superficie.
    assi: le due direzioni (dX, dY, dZ) lungo cui corre la superficie; se
    la foto la vede con meno di MIN_PX_PER_M pixel per metro lungo una
    delle due (vista troppo di sbieco), quella parte resta bianca invece
    di diventare una striscia stirata."""
    f, fy, cx, cy, Xc, Yc, D = cam

    def px(Xa, Ya, Za):
        den = D + Za
        return cx + f * (Xa - Xc) / den, cy - fy * (Ya - Yc) / den

    x, y = px(X, Y, Z)
    e = 0.01
    nitido = np.ones(X.shape, bool)
    for dX, dY, dZ in assi:
        xa, ya = px(X + e * dX, Y + e * dY, Z + e * dZ)
        nitido &= np.hypot(xa - x, ya - y) / e >= MIN_PX_PER_M
    # visibile solo se il raggio passa dentro l'apertura dell'arco (z = 0)
    den = D + Z
    t = D / den
    Xf, Yf = Xc + (X - Xc) * t, Yc + (Y - Yc) * t
    R, S = CHAPEL_ARCH_RADIUS_M + 0.02, CHAPEL_ARCH_SPRING_M
    dentro = ((np.abs(Xf) <= R) & ((Yf <= S) | (Xf ** 2 + (Yf - S) ** 2 <= R ** 2))) | (Z <= 0.001)
    out = cv2.remap(img, x.astype(np.float32), y.astype(np.float32), cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.float32)
    vuoto = (out.sum(-1) == 0) | ~dentro | ~nitido | (den <= 0.1)
    if normale is not None:
        # la superficie prende la foto solo se la camera (in Z = -D) la vede
        # dal davanti: altrimenti e' vista dal retro, e resta bianca
        nX, nY, nZ = normale
        vuoto |= ((Xc - X) * nX + (Yc - Y) * nY + (-D - Z) * nZ) <= 0
    out[vuoto] = BIANCO
    return out.astype(np.uint8)


def texture_nicchia(img, cam, nome: str) -> None:
    R, S, d = CHAPEL_ARCH_RADIUS_M, CHAPEL_ARCH_SPRING_M, CHAPEL_PROJECTION_DEPTH_M
    k = PX_PER_M_USCITA
    def griglia(n_u, n_v):
        return np.meshgrid((np.arange(n_u) + 0.5) / n_u, 1 - (np.arange(n_v) + 0.5) / n_v)
    # fondo: X in [-R, R], Y in [0, S + R] (riga 0 = in alto)
    a, b = griglia(int(2 * R * k), int((S + R) * k))
    fondo = _campiona(img, cam, -R + 2 * R * a, (S + R) * b, np.full_like(a, d), ((1, 0, 0), (0, 1, 0)))
    # fianchi: u = profondita' da NICCHIA_Z0 a d, v = Y in [0, S]
    a, b = griglia(int((d - NICCHIA_Z0) * k), int(S * k))
    Z = NICCHIA_Z0 + (d - NICCHIA_Z0) * a
    sx = _campiona(img, cam, np.full_like(a, -R), S * b, Z, ((0, 0, 1), (0, 1, 0)), (1, 0, 0))
    dx = _campiona(img, cam, np.full_like(a, R), S * b, Z, ((0, 0, 1), (0, 1, 0)), (-1, 0, 0))
    # volta: u = angolo da sinistra (0) a destra (pi), v = profondita'
    a, b = griglia(int(np.pi * R * k), int((d - NICCHIA_Z0) * k))
    th = np.pi * a
    tang = (np.sin(th), np.cos(th), np.zeros_like(th))  # tangente all'arco
    volta = _campiona(img, cam, -R * np.cos(th), S + R * np.sin(th), NICCHIA_Z0 + (d - NICCHIA_Z0) * b,
                      ((0, 0, 1), tang), (np.cos(th), -np.sin(th), 0))
    for suff, im in (("fondo", fondo), ("lato_sx", sx), ("lato_dx", dx), ("volta", volta)):
        cv2.imwrite(os.path.join(QUI, "photos", f"{nome}_{suff}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 85])
    f, fy, cx, cy, Xc, Yc, D = cam
    print(f"{nome}: punto di presa a {D:.2f} m dalla parete, {Yc:.2f} m d'altezza, "
          f"{Xc:+.2f} m a destra del centro; texture della nicchia scritte")


def ritaglia(img: np.ndarray, p: dict):
    """Da pilastro a pilastro, dal pavimento fin dove la foto copre
    tutta la larghezza. Ritorna (immagine, quota bassa m, altezza m)."""
    x0, x1, yp = p["x_pilastro_sx"], p["x_pilastro_dx"], p["y_pavimento"]
    ppm = p.get("px_per_m_verticale", (x1 - x0) / CAMPATA_M)
    cov = img.sum(2) > 0
    cols = range(max(x0, 0), min(x1, img.shape[1]), 10)
    if "y_alto" in p:
        # ritaglio fisso (la foto non copre tutta la campata): dal pavimento
        # a y_alto; gli angoli non coperti prendono il grigio dei muri
        top, bot = p["y_alto"], yp
    else:
        top = max(int(np.argmax(cov[:, x])) for x in cols)
        bot = min(len(cov) - int(np.argmax(cov[::-1, x])) for x in cols)
        bot = min(bot, yp)  # mai sotto il pavimento
    pad = cv2.copyMakeBorder(img, 0, max(0, bot - img.shape[0]), max(0, -x0), max(0, x1 - img.shape[1]),
                             cv2.BORDER_CONSTANT, value=0)
    crop = pad[top:bot, x0 + max(0, -x0):x1 + max(0, -x0)].copy()
    crop[crop.sum(-1) == 0] = BIANCO.astype(np.uint8)
    w_basso = (yp - bot) / ppm
    altezza = (bot - top) / ppm
    out = cv2.resize(crop, (int(CAMPATA_M * PX_PER_M_USCITA), int(altezza * PX_PER_M_USCITA)),
                     interpolation=cv2.INTER_AREA)
    return out, w_basso, altezza


def ritaglia_foto(img: np.ndarray, p: dict):
    """Ritaglio esplicito (foto singola). Ritorna (immagine, quota bassa m,
    altezza m, larghezza m, spostamento m del centro verso DESTRA nella
    foto rispetto al centro della campata)."""
    x0, y0, x1, y1 = p["ritaglio"]
    ppm = p["px_per_m"]
    crop = img[y0:y1, x0:x1]
    larg, alt = (x1 - x0) / ppm, (y1 - y0) / ppm
    out = cv2.resize(crop, (int(larg * PX_PER_M_USCITA), int(alt * PX_PER_M_USCITA)),
                     interpolation=cv2.INTER_AREA)
    return out, (p["y_pavimento"] - y1) / ppm, alt, larg, ((x0 + x1) / 2 - p["x_centro_campata"]) / ppm


def elabora(nome: str, p: dict) -> None:
    if "foto" in p:
        im = cv2.imread(os.path.join(QUI, p["foto"]))
        mos, centro = im, (im.shape[1] / 2, im.shape[0] / 2)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            imgs = fotogrammi(os.path.join(QUI, p["video"]), tmp)
        mos, centro = mosaico(imgs, p["rif"])
    vV, vH = punti_di_fuga(mos)
    rett, (f, cx, cy) = raddrizza(mos, centro, vV, vH)
    if "ritaglio" in p:
        ppm, xc, yp = p["px_per_m"], p["x_centro_campata"], p["y_pavimento"]
    elif "x_pilastro_sx" in p:
        ppm = (p["x_pilastro_dx"] - p["x_pilastro_sx"]) / CAMPATA_M
        xc, yp = (p["x_pilastro_sx"] + p["x_pilastro_dx"]) / 2, p["y_pavimento"]
    if "ritaglio" in p or "x_pilastro_sx" in p:
        # scala verticale diversa dall'orizzontale se il raddrizzamento non e'
        # isotropo (focale stimata male): la camera ha allora fy != f
        ppm_v = p.get("px_per_m_verticale", ppm)
        D = f / ppm
        texture_nicchia(rett, (f, D * ppm_v, cx, cy, (cx - xc) / ppm, (yp - cy) / ppm_v, D), nome)
    if "ritaglio" in p:
        foto, w_basso, altezza, larg, dx = ritaglia_foto(rett, p)
        dest = os.path.join(QUI, "photos", f"{nome}.jpg")
        cv2.imwrite(dest, foto, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"{nome}: {dest}  {foto.shape[1]}x{foto.shape[0]} px, larghezza {larg:.2f} m, "
              f"da {w_basso:.2f} m, altezza {altezza:.2f} m, centro {dx:+.2f} m a destra nella foto")
        return
    if "x_pilastro_sx" not in p:
        # primo passaggio: salva l'immagine raddrizzata intera, su cui
        # misurare i centri dei pilastri e il pavimento da mettere in VIDEO
        dest = os.path.join(QUI, "video", f"{nome}_raddrizzata.jpg")
        cv2.imwrite(dest, rett, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(f"{nome}: misura pilastri e pavimento su {dest} ({rett.shape[1]}x{rett.shape[0]} px)")
        return
    foto, w_basso, altezza = ritaglia(rett, p)
    dest = os.path.join(QUI, "photos", f"{nome}.jpg")
    cv2.imwrite(dest, foto, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"{nome}: {dest}  {foto.shape[1]}x{foto.shape[0]} px, "
          f"larghezza {CAMPATA_M:.2f} m, da {w_basso:.2f} m, altezza {altezza:.2f} m")


if __name__ == "__main__":
    scelti = sys.argv[1:] or list(VIDEO)
    for n in scelti:
        elabora(n, VIDEO[n])
