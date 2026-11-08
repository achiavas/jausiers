#!/usr/bin/env python3
"""
fondo_da_foto.py
----------------
Migliora il FONDO di una nicchia di cappella con una foto frontale
dell'utente (piu' nitida del fotogramma del video). I quattro angoli del
quadro d'altare, misurati sulla foto e noti sul fondo (dimensioni dal
fondo calcolato da foto_da_video.py, scala 150 px/m), danno l'omografia
della foto sul piano del fondo. Il quadro viene CENTRATO sull'arco (come
e' davvero; nel fotogramma del video risultava spostato per lo scorcio).
Dove la foto non arriva (in alto) resta il fondo di prima, con un
raccordo sfumato. Se configurato, anche il FIANCO DESTRO della nicchia
(che dal punto di presa del video non si vedeva) dalla stessa foto.

Da eseguire DOPO foto_da_video.py (ne riscrive il fondo).
Uso:  .venv/bin/python fondo_da_foto.py
"""
from __future__ import annotations

import os

import cv2
import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))

FOTO = {
    "cappella_ovest_2": dict(
        foto="video/cappella_ovest_2_foto_utente.jpg",
        # angoli del quadro nella foto (x, y): alto-sx, alto-dx, basso-dx, basso-sx
        quadro_foto=[(425, 112), (574, 112), (574, 319), (425, 319)],
        # quadro sul fondo (150 px/m): largo 325 px (2.17 m), da y = 381 a 829
        # (da 1.99 a 4.97 m dal pavimento), centrato sull'arco
        quadro_larghezza_px=325, quadro_y=(381, 829),
        area_foto=(165, 0, 835, 500),   # parte della foto senza i margini bianchi
        # fianco destro: nella foto va dallo spigolo col fondo (x ~ 680, cioe'
        # 2.62 m dall'asse: la nicchia vera e' larga ~5.2 m) al bordo dell'arco
        # (x ~ 760; oltre c'e' il pilastro della navata con l'altoparlante).
        # Camera frontale: fondo a 68.7 px/m; dallo spigolo all'arco (2.34 m
        # di profondita') -> camera a 7.61 m dal fondo, focale ~523 px; centro
        # x = 500 (asse del quadro); in verticale centro y ~ 352 con la camera
        # a 1.5 m (dal quadro: y = 319 a 1.99 m, y = 112 a 4.97 m).
        lato_dx=dict(f=523.0, Z0=7.61, cx=500.0, cy=352.0, Yc=1.5, X=2.62, x_min=676, x_max=830),
        nota="seconda cappella a sinistra (Sant'Antonio), foto frontale dell'utente",
    ),
}


def elabora(nome: str, p: dict) -> None:
    dest = os.path.join(QUI, "photos", f"{nome}_fondo.jpg")
    fondo = cv2.imread(dest).astype(np.float32)
    H, W = fondo.shape[:2]
    foto = cv2.imread(os.path.join(QUI, p["foto"]))
    xc, (y0, y1), lw = W / 2, p["quadro_y"], p["quadro_larghezza_px"]
    dst = np.float32([(xc - lw / 2, y0), (xc + lw / 2, y0), (xc + lw / 2, y1), (xc - lw / 2, y1)])
    M = cv2.getPerspectiveTransform(np.float32(p["quadro_foto"]), dst)
    nuovo = cv2.warpPerspective(foto, M, (W, H), flags=cv2.INTER_CUBIC).astype(np.float32)
    x0, ya, x1, yb = p["area_foto"]
    maschera = np.zeros(foto.shape[:2], np.float32)
    maschera[ya + 2:yb - 2, x0 + 2:x1 - 2] = 1.0
    m = cv2.warpPerspective(maschera, M, (W, H))
    m = cv2.GaussianBlur(cv2.erode(m, np.ones((15, 15), np.uint8)), (0, 0), 12)[..., None]
    out = nuovo * m + fondo * (1 - m)
    cv2.imwrite(dest, out.clip(0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    alto = np.nonzero(m[:, W // 2, 0] > 0.5)[0]
    print(f"{nome}: {dest} - foto fino a {(H - alto.min()) / 150:.2f} m dal pavimento "
          f"({68.7:.1f} px/m nella foto -> 150 px/m)")


# Nicchia INTERA da una sola foto (cappelle senza video): dal trapezio del
# quadro (omografia del piano del fondo) si ricava la camera completa,
# focale compresa (centro ottico al centro della foto), e da li' ogni punto
# di fondo, fianchi e volta si proietta nella foto. Le parti che la foto
# non vede prendono il grigio dei muri, come in foto_da_video.texture_nicchia.
NICCHIE_DA_FOTO = {
    "cappella_est_1": dict(
        foto="video/cappella_est_1_foto_utente.jpg",
        quadro_foto=[(421, 92), (596, 100), (610, 347), (407, 339)],   # alto-sx, alto-dx, basso-dx, basso-sx
        # quadro grande come quello di Sant'Antonio, di fronte (2.17 x 2.98 m):
        # cosi' cade 1.5 m sopra la mensa dell'altare (y = 485 nella foto)
        quadro_m=(2.17, 2.98), quadro_basso_m=2.80,
        # spigoli fondo/fianchi nella foto all'altezza del fondo del quadro
        spigoli_x=(255, 750),
        area_foto=(165, 0, 835, 500), centro=(500, 250),
        # la focale dal solo trapezio del quadro non e' stabile (4 angoli):
        # quella della foto di Sant'Antonio, stessa macchina e stesso formato
        focale=523.0,
        nota="prima cappella a destra entrando (lato Est, u = 4.14 m), foto dell'utente",
    ),
}


def _camera_da_omografia(Hm, cx, cy):
    """K, R, t da un'omografia piano (X, Y, 0) -> foto, centro ottico noto."""
    h1, h2, h3 = Hm[:, 0], Hm[:, 1], Hm[:, 2]
    A1 = np.array([h1[0] - cx * h1[2], h1[1] - cy * h1[2]])
    A2 = np.array([h2[0] - cx * h2[2], h2[1] - cy * h2[2]])
    f2 = -(A1 @ A2) / (h1[2] * h2[2])
    if not f2 > 0:   # ortogonalita' degenere: uguaglianza delle norme
        f2 = (A1 @ A1 - A2 @ A2) / (h2[2] ** 2 - h1[2] ** 2)
    f = float(np.sqrt(f2))
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1.0]])
    B = np.linalg.inv(K) @ Hm
    lam = 1 / np.linalg.norm(B[:, 0])
    r1, r2, t = lam * B[:, 0], lam * B[:, 1], lam * B[:, 2]
    if t[2] < 0:
        r1, r2, t = -r1, -r2, -t
    R = np.c_[r1, r2, np.cross(r1, r2)]
    U, _, Vt = np.linalg.svd(R)
    return K, U @ Vt, t


def nicchia_da_foto(nome: str, p: dict) -> None:
    from church_geometry import (CHAPEL_ARCH_RADIUS_M as R, CHAPEL_ARCH_SPRING_M as S,
                                 CHAPEL_PROJECTION_DEPTH_M as d)
    from reference_photos import NICCHIA_Z0
    k = 150
    foto = cv2.imread(os.path.join(QUI, p["foto"]))
    (wq, hq), yq = p["quadro_m"], p["quadro_basso_m"]
    piano = np.float32([(-wq / 2, yq + hq), (wq / 2, yq + hq), (wq / 2, yq), (-wq / 2, yq)])
    if "focale" in p:
        # focale nota (stessa macchina della foto di Sant'Antonio): solo la posa
        f = p["focale"]
        K = np.array([[f, 0, p["centro"][0]], [0, f, p["centro"][1]], [0, 0, 1.0]])
        obj = np.c_[piano, np.zeros(4)].astype(np.float64)
        _, rv, tv = cv2.solvePnP(obj, np.float64(p["quadro_foto"]), K, None, flags=cv2.SOLVEPNP_IPPE)
        Rm, t = cv2.Rodrigues(rv)[0], tv.ravel()
    else:
        Hm = cv2.getPerspectiveTransform(piano, np.float32(p["quadro_foto"])).astype(float)
        K, Rm, t = _camera_da_omografia(Hm, *p["centro"])
    C = -Rm.T @ t                                     # camera nel riferimento del fondo (Z verso la camera)

    def proietta(X, Y, Z):
        P = np.stack([X, Y, Z], -1) @ Rm.T + t
        q = P @ K.T
        return q[..., 0] / q[..., 2], q[..., 1] / q[..., 2], P[..., 2]

    # meta' larghezza vera della nicchia: dove cadono gli spigoli nella foto
    xs = [proietta(np.array(X), np.array(yq), np.array(0.0))[0] for X in (-1.0, 1.0)]
    scala = (xs[1] - xs[0]) / 2
    xm = (xs[0] + xs[1]) / 2
    Xh = float(np.mean([abs(x - xm) / scala for x in p["spigoli_x"]]))
    x0, y0, x1, y1 = p["area_foto"]

    def campiona(X, Y, Z, normale):
        mx, my, prof = proietta(X, Y, Z)
        img = cv2.remap(foto, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC)
        verso = (C[None, None, :] - np.stack([X, Y, Z], -1)) @ np.array(normale)
        ok = (mx >= x0 + 1) & (mx <= x1 - 2) & (my >= y0 + 1) & (my <= y1 - 2) & (prof > 0.1) & (verso > 0)
        img[~ok] = (176, 182, 188)        # grigio dei muri (GRIGIO_MURI di foto_da_video.py)
        return img

    def griglia(n_u, n_v):
        return np.meshgrid((np.arange(n_u) + 0.5) / n_u, 1 - (np.arange(n_v) + 0.5) / n_v)

    a, b = griglia(int(2 * R * k), int((S + R) * k))
    fondo = campiona(-R + 2 * R * a, (S + R) * b, np.zeros_like(a), (0, 0, 1))
    a, b = griglia(int((d - NICCHIA_Z0) * k), int(S * k))
    Zf = d - (NICCHIA_Z0 + (d - NICCHIA_Z0) * a)      # distanza dal fondo
    sx = campiona(np.full_like(a, -Xh), S * b, Zf, (1, 0, 0))
    dx = campiona(np.full_like(a, Xh), S * b, Zf, (-1, 0, 0))
    a, b = griglia(int(np.pi * R * k), int((d - NICCHIA_Z0) * k))
    th = np.pi * a
    volta = campiona(-Xh * np.cos(th), S + R * np.sin(th), d - (NICCHIA_Z0 + (d - NICCHIA_Z0) * b),
                     (0, -1, 0))
    for suff, im in (("fondo", fondo), ("lato_sx", sx), ("lato_dx", dx), ("volta", volta)):
        cv2.imwrite(os.path.join(QUI, "photos", f"{nome}_{suff}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{nome}: focale {K[0, 0]:.0f} px, camera a {C[2]:.2f} m dal fondo, {C[1]:.2f} m d'altezza, "
          f"{C[0]:+.2f} m dal centro; nicchia larga {2 * Xh:.2f} m; texture scritte")


def lato_destro(nome: str, p: dict, foto: np.ndarray) -> None:
    """Fianco destro della nicchia dalla foto: per ogni punto del fianco
    (profondita' e quota, come nella texture di foto_da_video.texture_nicchia)
    la sua posizione nella foto con la camera frontale stimata."""
    from church_geometry import CHAPEL_ARCH_SPRING_M as S, CHAPEL_PROJECTION_DEPTH_M as d
    from reference_photos import NICCHIA_Z0
    dest = os.path.join(QUI, "photos", f"{nome}_lato_dx.jpg")
    vecchio = cv2.imread(dest).astype(np.float32)
    H, W = vecchio.shape[:2]
    c = p["lato_dx"]
    a, b = np.meshgrid((np.arange(W) + 0.5) / W, 1 - (np.arange(H) + 0.5) / H)
    Z = NICCHIA_Z0 + (d - NICCHIA_Z0) * a          # dal filo navata (0) al fondo (d)
    Y = S * b
    dist = c["Z0"] - (d - Z)                        # distanza dalla camera
    mx = (c["cx"] + c["f"] * c["X"] / dist).astype(np.float32)
    my = (c["cy"] - c["f"] * (Y - c["Yc"]) / dist).astype(np.float32)
    nuovo = cv2.remap(foto, mx, my, cv2.INTER_CUBIC).astype(np.float32)
    m = ((mx >= c["x_min"]) & (mx <= c["x_max"]) & (my >= 2) & (my <= foto.shape[0] - 3)).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 4)[..., None]
    out = nuovo * m + vecchio * (1 - m)
    cv2.imwrite(dest, out.clip(0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{nome}: {dest} - fianco destro dalla foto ({100 * float(m.mean()):.0f}% coperto)")


if __name__ == "__main__":
    for n, p in FOTO.items():
        elabora(n, p)
        if "lato_dx" in p:
            lato_destro(n, p, cv2.imread(os.path.join(QUI, p["foto"])))
    for n, p in NICCHIE_DA_FOTO.items():
        nicchia_da_foto(n, p)
