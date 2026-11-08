"""
reference_photos.py
--------------------
Colloca le foto reali fornite dall'utente come pannelli testurizzati
nel modello 3D, vicino al punto a cui si riferiscono - per dare un
riscontro visivo concreto rispetto al modello geometrico astratto.

4 foto: abside (pannello CURVO, vedi sotto), entrata della navata, e
le due pareti laterali ("bas-côtés") viste dall'interno - allineate
per larghezza all'estensione utile reale della navata, cosi' le
finestre visibili nella foto corrispondono approssimativamente alle
vetrate di cleristorio del modello 3D.

Il pannello dell'abside NON e' piatto: e' costruito come una striscia
di quadrilateri che segue i 5 lati reali del pentagono absidale
(`ChurchModel.apse_vertices()`), con la coordinata U della texture
proporzionale alla distanza percorsa lungo il perimetro - una
proiezione "panoramica" semplificata, molto piu' fedele di un singolo
rettangolo piatto floating davanti all'abside.

Le foto sono in /photos accanto a questo file. Ogni voce sotto
specifica dove agganciare il pannello (coordinate locali u,v,w
dell'edificio - stesso sistema usato in tutto il progetto) e verso
quale direzione deve essere rivolto (la normale del pannello, in
modo che sia leggibile stando dentro la navata).
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

import numpy as np
import pyvista as pv

from church_geometry import (ChurchModel, NAVE_LENGTH_M, NAVE_WIDTH_M, WALL_HEIGHT_M, APSE_EXTERNAL_HEIGHT_M,
                             CHAPEL_ROW_MARGIN_M, N_CHAPELS_PER_SIDE, CHAPEL_ARCH_RADIUS_M,
                             CHAPEL_ARCH_SPRING_M, CHAPEL_PROJECTION_DEPTH_M)

PHOTOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")

_NAVE_U_CENTER = NAVE_LENGTH_M / 2.0
_WH = NAVE_WIDTH_M / 2.0
# una campata di cappella, fra i centri di due pilastri (6.08 m)
_CAMPATA = (NAVE_LENGTH_M - 2 * CHAPEL_ROW_MARGIN_M) / N_CHAPELS_PER_SIDE
_BC_MARGIN = NAVE_LENGTH_M * 0.06
_BC_SPAN = NAVE_LENGTH_M - 2 * _BC_MARGIN   # estensione utile navata (~23.6 m)


@dataclass(frozen=True)
class PhotoCard:
    filename: str
    caption: str
    u: float
    v: float
    w_bottom: float     # altezza da terra del bordo inferiore
    width_m: float
    height_m: float
    facing: str          # "plus_v" | "minus_v" | "plus_u" | "minus_u" | "down"
    # True = visibile solo dal lato verso cui e' rivolta (es. la facciata
    # esterna non deve comparire guardando la controfacciata da dentro)
    solo_fronte: bool = False
    # True = pannello di una cappella con NICCHIA (vedi NICCHIE): l'arco
    # d'ingresso viene bucato, e dentro si vede la nicchia in profondita'
    foro_cappella: bool = False


# --- Pannelli PIATTI (facciata esterna e cappelle) ---
PHOTO_CARDS: list[PhotoCard] = [
    # --- Facciata esterna: foto reale ritagliata (sfondo rimosso),
    #     agganciata all'ESTERNO del muro di facciata (u leggermente
    #     negativo, appena staccata dal muro per evitare z-fighting),
    #     rivolta verso l'esterno (facing="minus_u") - visibile
    #     guardando l'edificio da fuori, come nella foto reale.
    #     Dimensioni calcolate dalla foto stessa: scala determinata
    #     dall'altezza (gronda muro a 16.56 m e colmo tetto a 23.13 m
    #     nel modello, confrontati con i pixel corrispondenti nella
    #     foto - le due stime di scala risultanti concordano al 2%,
    #     quindi piu' affidabili della larghezza, che soffre di
    #     leggera prospettiva/distorsione della foto). Il pannello
    #     copre da terra fino al colmo del tetto (include quindi anche
    #     il timpano/gronda visibili nella foto, non solo il muro
    #     verticale) ed e' leggermente piu' largo (15.93 m) del muro
    #     reale (13.37 m) per garantire copertura completa. ---
    PhotoCard(
        filename="facciata_esterna.png",
        caption="Facciata esterna (foto reale)",
        # foto adattata con facciata_da_foto.py: le sue vetrate coincidono con
        # quelle del modello; il pannello va da terra a 23.5 m (oltre il colmo)
        # sul filo esterno del muro, 2 cm davanti alla faccia esterna delle
        # vetrate (church_mesh.build_window_solid): la foto le copre esattamente
        u=-0.76, v=0.0, w_bottom=0.0, width_m=20.0, height_m=26.5,
        facing="minus_u", solo_fronte=True,
    ),
    # --- Pareti laterali: le vecchie foto im1.jpg/im2.jpg (intere
    #     pareti viste dal basso, non raddrizzate) sono state TOLTE su
    #     richiesta dell'utente: non corrispondevano alle cappelle.
    #     Restano i file in photos/ e i ritagli delle vetrate presi da
    #     li' (CHAPEL_WINDOW_PHOTOS). Ora ogni cappella ha la sua foto. ---
    # --- Cappelle, una campata per foto: foto RADDRIZZATE e IN SCALA
    #     ricavate dai video con foto_da_video.py (mosaico dei
    #     fotogrammi, vista resa frontale, scala dalla campata fra i
    #     centri dei pilastri = _CAMPATA). Coprono la campata da
    #     pilastro a pilastro, dal pavimento fin sopra l'arco, appena
    #     staccate dal filo muro (v piu' interno) per non coprire le
    #     macchie di luce disegnate sulla parete. ---
    PhotoCard(
        filename="cappella_ovest_1.jpg",
        caption="Prima cappella a sinistra entrando (Ovest), dal video IMG_9734",
        u=CHAPEL_ROW_MARGIN_M + 0.5 * _CAMPATA, v=_WH - 0.15, w_bottom=0.09,
        width_m=_CAMPATA, height_m=8.77,
        facing="minus_v", foro_cappella=True,
    ),
    PhotoCard(
        filename="cappella_ovest_2.jpg",
        caption="Seconda cappella a sinistra entrando (Ovest), da IMG_9758 (21 s)",
        u=CHAPEL_ROW_MARGIN_M + 1.5 * _CAMPATA, v=_WH - 0.15, w_bottom=0.0,
        width_m=_CAMPATA, height_m=6.73,
        facing="minus_v", foro_cappella=True,
    ),
    PhotoCard(
        filename="cappella_est_2.jpg",
        caption="Seconda cappella a destra entrando (Est), dal video IMG_9738",
        u=CHAPEL_ROW_MARGIN_M + 1.5 * _CAMPATA, v=-_WH + 0.15, w_bottom=0.0,
        width_m=_CAMPATA, height_m=8.72,
        facing="plus_v", foro_cappella=True,
    ),
    PhotoCard(
        filename="cappella_ovest_4.jpg",
        caption="Quarta cappella a sinistra entrando (Ovest), dal video IMG_9740",
        u=CHAPEL_ROW_MARGIN_M + 3.5 * _CAMPATA, v=_WH - 0.15, w_bottom=0.0,
        width_m=_CAMPATA, height_m=8.19,
        facing="minus_v", foro_cappella=True,
    ),
    PhotoCard(
        filename="cappella_ovest_3.jpg",
        caption="Terza cappella a sinistra entrando (Ovest), dal video IMG_9742",
        u=CHAPEL_ROW_MARGIN_M + 2.5 * _CAMPATA, v=_WH - 0.15, w_bottom=0.0,
        width_m=_CAMPATA, height_m=7.80,
        facing="minus_v", foro_cappella=True,
    ),
    PhotoCard(
        filename="cappella_est_4.jpg",
        caption="Quarta cappella a destra entrando (Est), da IMG_9758 (0.5 s)",
        u=CHAPEL_ROW_MARGIN_M + 3.5 * _CAMPATA, v=-_WH + 0.15, w_bottom=0.0,
        width_m=_CAMPATA, height_m=7.31,
        facing="plus_v", foro_cappella=True,
    ),
    # Terza a destra: la foto (singola, presa dentro l'arco) cade tutta
    # dentro l'apertura, quindi non ha un pannello sul filo della navata:
    # e' solo NICCHIA (vedi sotto).
]

# --- NICCHIE delle cappelle: profondita' -----------------------------
#     Ogni cappella con foto e' una nicchia vera dietro l'arco
#     d'ingresso: fondo a CHAPEL_PROJECTION_DEPTH_M (2.19 m), due fianchi
#     e una volta a botte a tutto sesto (arco: CHAPEL_ARCH_RADIUS_M,
#     CHAPEL_ARCH_SPRING_M). Le texture (nome_fondo, _lato_sx, _lato_dx,
#     _volta) sono calcolate da foto_da_video.py ricostruendo il punto da
#     cui e' stata scattata la foto: ogni superficie prende la sua parte di
#     foto alla scala giusta (la pala d'altare sul fondo e' ~1/3 piu'
#     grande che in una proiezione piatta). Le parti non visibili dal
#     punto di presa sono bianche.
#     (nome, lato: +1 Ovest = sinistra entrando, -1 Est; indice campata
#     dall'ingresso). "Destra nella foto" = +u a Ovest, -u a Est.
NICCHIA_Z0 = -0.15   # le superfici partono dal piano dei pannelli (v = Wh - 0.15)

# --- Pavimento: texture dal video IMG_9757 (pavimento_da_video.py): una
#     "piastrella" lunga PAVIMENTO_PERIODO_M lungo la navata (si ripete) e
#     larga PAVIMENTO_LARGHEZZA_M di traverso, centrata sull'asse (v = 0),
#     con il corridoio e le sue fasce ocra al centro. ---
PAVIMENTO_FILENAME = "pavimento.jpg"
PAVIMENTO_PERIODO_M = 5.0
PAVIMENTO_LARGHEZZA_M = 18.0
# --- Tetto e muri esterni: texture ripetibili dal video IMG_9765
#     (tetto_muri_da_video.py): scandole di legno (2 file, ~0.36 m l'una)
#     e intonaco grezzo. Dimensioni reali di una ripetizione. ---
CONTROFACCIATA_ALTEZZA_M = 13.3   # foto della controfacciata: fin sotto i davanzali delle vetrate
TETTO_TEXTURE_FILENAME = "tetto_esterno.jpg"
TETTO_TEXTURE_M = (2.4, 0.72)       # lungo la gronda, lungo la falda (vista isotropa)
MURO_TEXTURE_FILENAME = "muro_esterno.jpg"
MURO_TEXTURE_M = 1.0
NICCHIE = [
    ("cappella_ovest_1", +1, 0),
    ("cappella_est_1", -1, 0),
    ("cappella_ovest_2", +1, 1),
    ("cappella_est_2", -1, 1),
    ("cappella_est_3", -1, 2),
    ("cappella_ovest_4", +1, 3),
    ("cappella_ovest_3", +1, 2),
    ("cappella_est_4", -1, 3),
]
_N_ARCO = 32


def _arco_aperto(X, Y, margine=0.0):
    """True se (X, Y) - coordinate sul piano dell'arco, X dal centro -
    cade dentro l'apertura d'ingresso della cappella."""
    R, S = CHAPEL_ARCH_RADIUS_M + margine, CHAPEL_ARCH_SPRING_M
    return abs(X) < R and (Y < S or X * X + (Y - S) ** 2 < R * R)


def card_con_foro(card: PhotoCard):
    """Pannello di cappella con l'arco d'ingresso bucato. Ritorna
    (punti locali u,v,w; coordinate texture; triangoli). X va da sinistra
    a destra come la foto, centrato sul pannello."""
    BL, BR, TR, TL = _card_corners_local(card)
    W, H, wb = card.width_m, card.height_m, card.w_bottom
    R, S = CHAPEL_ARCH_RADIUS_M, CHAPEL_ARCH_SPRING_M
    top = wb + H

    def P(X, Y):
        t = (X + W / 2) / W
        return ((BL[0] + t * (BR[0] - BL[0]), BL[1] + t * (BR[1] - BL[1]), Y),
                (t, (Y - wb) / H))

    pts, uvs, tris = [], [], []

    def quad(a, b, c, d):  # quattro (X, Y) in senso antiorario visto dal fronte
        i = len(pts)
        for X, Y in (a, b, c, d):
            p, uv = P(X, Y); pts.append(p); uvs.append(uv)
        tris.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])

    quad((-W / 2, wb), (-R, wb), (-R, top), (-W / 2, top))
    quad((R, wb), (W / 2, wb), (W / 2, top), (R, top))
    for k in range(_N_ARCO):
        t0, t1 = math.pi * k / _N_ARCO, math.pi * (k + 1) / _N_ARCO
        x0, x1 = -R * math.cos(t0), -R * math.cos(t1)
        y0, y1 = S + R * math.sin(t0), S + R * math.sin(t1)
        quad((x0, y0), (x1, y1), (x1, top), (x0, top))
    return pts, uvs, tris


def nicchia_parti(lato: int, indice: int, church: ChurchModel):
    """Le quattro superfici della nicchia: lista di (suffisso, punti
    locali, coordinate texture, triangoli). Le coordinate texture seguono
    le immagini scritte da foto_da_video.texture_nicchia()."""
    # fondo 5 cm davanti al muro di fondo della cappella del modello (che e'
    # semitrasparente: se coincidessero lo coprirebbe di bianco)
    R, S, d, z0 = CHAPEL_ARCH_RADIUS_M, CHAPEL_ARCH_SPRING_M, CHAPEL_PROJECTION_DEPTH_M - 0.05, NICCHIA_Z0
    uc = church.chapel_u_positions()[indice]

    def L(X, Y, Z):  # X a destra nella foto, Y in alto, Z in profondita'
        return (uc + lato * X, lato * (_WH + Z), Y)

    parti = []
    # fondo: rettangolo fino all'imposta + mezzo cerchio
    pts, uvs, tris = [], [], []
    def add(X, Y, Z, uv):
        pts.append(L(X, Y, Z)); uvs.append(uv); return len(pts) - 1
    H = S + R
    a = add(-R, 0, d, (0, 0)); b = add(R, 0, d, (1, 0))
    c = add(R, S, d, (1, S / H)); e = add(-R, S, d, (0, S / H))
    tris += [(a, b, c), (a, c, e)]
    centro = add(0, S, d, (0.5, S / H))
    arco = [add(-R * math.cos(math.pi * k / _N_ARCO), S + R * math.sin(math.pi * k / _N_ARCO), d,
                ((1 - math.cos(math.pi * k / _N_ARCO)) / 2, (S + R * math.sin(math.pi * k / _N_ARCO)) / H))
            for k in range(_N_ARCO + 1)]
    tris += [(centro, arco[k + 1], arco[k]) for k in range(_N_ARCO)]
    parti.append(("fondo", pts, uvs, tris))
    # fianchi
    for suff, X in (("lato_sx", -R), ("lato_dx", R)):
        pts = [L(X, 0, z0), L(X, 0, d), L(X, S, d), L(X, S, z0)]
        parti.append((suff, pts, [(0, 0), (1, 0), (1, 1), (0, 1)], [(0, 1, 2), (0, 2, 3)]))
    # volta a botte
    pts, uvs, tris = [], [], []
    for k in range(_N_ARCO + 1):
        th = math.pi * k / _N_ARCO
        X, Y = -R * math.cos(th), S + R * math.sin(th)
        pts += [L(X, Y, z0), L(X, Y, d)]
        uvs += [(k / _N_ARCO, 0), (k / _N_ARCO, 1)]
    for k in range(_N_ARCO):
        i = 2 * k
        tris += [(i, i + 2, i + 3), (i, i + 3, i + 1)]
    parti.append(("volta", pts, uvs, tris))
    return parti


def apertura_cappella(church: ChurchModel, u: float, v: float, w: float, margine: float = 0.0) -> bool:
    """True se il punto locale (u, v, w) del muro della navata cade
    nell'arco d'ingresso di una cappella CON nicchia (serve a bucare il
    muro semitrasparente, che altrimenti sbiadirebbe la nicchia)."""
    for _, lato, indice in NICCHIE:
        if v * lato <= 0:
            continue
        uc = church.chapel_u_positions()[indice]
        if _arco_aperto(u - uc, w, margine):
            return True
    return False


# attori delle foto prese DENTRO la chiesa (cappelle: pannelli bucati e
# nicchie; abside), riempito da build_photo_actors: il viewer li mostra solo
# con la camera dentro la chiesa
ATTORI_CAPPELLE: list = []


def camera_dentro(church: ChurchModel, x: float, y: float, z: float) -> bool:
    """True se il punto (ENU) e' dentro la chiesa: navata, abside o una
    nicchia. Le foto delle cappelle si mostrano solo da dentro."""
    u, v = church.enu_to_local_uv(x, y)
    if z < 0 or z > WALL_HEIGHT_M + 6:
        return False
    if 0 <= u <= NAVE_LENGTH_M and abs(v) <= _WH:
        return True
    if NAVE_LENGTH_M < u < NAVE_LENGTH_M + 6 and abs(v) < _WH - 1.0:
        return True
    return (apertura_cappella(church, u, v, min(z, CHAPEL_ARCH_SPRING_M))
            and abs(v) <= _WH + CHAPEL_PROJECTION_DEPTH_M)


def _mesh_testurizzata(plotter, church, pts_local, uvs, tris, path, nome):
    pts = np.array([church.local_to_enu(*p) for p in pts_local])
    faces = np.hstack([[3, *t] for t in tris])
    mesh = pv.PolyData(pts, faces=faces)
    mesh.active_texture_coordinates = np.array(uvs, dtype=float)
    tex = pv.read_texture(path)
    return plotter.add_mesh(mesh, texture=tex, name=nome, show_edges=False, lighting=False)


# --- Foto reali delle vetrate laterali, una per vetrata, dalle foto
#     dell'utente a.jpg ... i.jpg (vetrate_laterali_da_foto.py): giro dalla
#     prima a sinistra entrando, lato Ovest verso l'abside (a-d), poi lato
#     Est dall'abside verso l'ingresso (e-h); la i sui due lati corti
#     dell'abside. Sovrapposte alla mesh piena delle vetrate, vedi
#     build_window_photo_overlays(). ---
CHAPEL_WINDOW_PHOTOS: dict[str, str] = {
    "Cappella Notre-Dame-du-Rosaire (Ovest)": "vetrata_laterale_a.jpg",
    "Cappella Saint-Joseph (Ovest)": "vetrata_laterale_b.jpg",
    "Cappella Sacre-Coeur (Ovest)": "vetrata_laterale_c.jpg",
    "Cappella Saint-Louis (Ovest)": "vetrata_laterale_d.jpg",
    "Cappella Sainte-Anne (Est)": "vetrata_laterale_e.jpg",
    "Cappella Saint-Antoine (Est)": "vetrata_laterale_f.jpg",
    "Cappella Coeur-Immacule-de-Marie (Est)": "vetrata_laterale_g.jpg",
    "Cappella Saint-Jean-Baptiste (Est)": "vetrata_laterale_h.jpg",
    "Abside - lato corto Ovest": "vetrata_laterale_i.jpg",
    "Abside - lato corto Est": "vetrata_laterale_i.jpg",
    # Vetrate della facciata viste dall'interno: raddrizzate da un
    # fotogramma del video IMG_9756 con vetrate_da_video.py.
    "Facciata - finestra centrale": "vetrata_facciata_centrale.jpg",
    "Facciata - finestra laterale Ovest": "vetrata_facciata_ovest.jpg",
    "Facciata - finestra laterale Est": "vetrata_facciata_est.jpg",
}

# --- Pannello CURVO dell'abside (vedi build_curved_apse_panel) ---
# sviluppo della parete vera dal video IMG_9760 (abside_da_video.py): le
# vetrate della foto cadono sulle vetrate del modello
APSE_PHOTO_FILENAME = "abside_interno.jpg"
APSE_PHOTO_HEIGHT_BOTTOM = 0.5
# CORRETTO: usava WALL_HEIGHT_M (altezza muro NAVATA, 16.56 m),
# risalente a prima che l'abside avesse un'altezza propria distinta -
# il pannello risultava "troppo alto" (segnalato dall'utente).
# L'abside ha ora il suo muro a 15.69 m (APSE_EXTERNAL_HEIGHT_M):
# usato quello, con lo stesso margine di rispetto dal soffitto.
APSE_PHOTO_HEIGHT_TOP = APSE_EXTERNAL_HEIGHT_M - 0.56


def _card_corners_local(card: PhotoCard):
    """4 angoli (u,v,w) del pannello, in ordine: basso-sx, basso-dx,
    alto-dx, alto-sx (rispetto a chi guarda il pannello frontalmente).
    Per facing="down" (non usato al momento, supportato per estensioni
    future) il pannello sarebbe orizzontale invece che verticale."""
    if card.facing == "down":
        half_w = card.width_m / 2.0
        half_h = card.height_m / 2.0
        p1 = (card.u - half_w, card.v - half_h, card.w_bottom)
        p2 = (card.u + half_w, card.v - half_h, card.w_bottom)
        p3 = (card.u + half_w, card.v + half_h, card.w_bottom)
        p4 = (card.u - half_w, card.v + half_h, card.w_bottom)
        return [p1, p2, p3, p4]

    half_w = card.width_m / 2.0
    if card.facing in ("plus_v", "minus_v"):
        # la larghezza corre lungo u; "sinistra/destra" viste da chi
        # guarda in direzione +-v dipendono dal verso della normale.
        # CORRETTO: il segno era invertito e le foto delle pareti
        # laterali risultavano speculari (im1: pulpito verso la
        # facciata; la cappella con la porta, prima a sinistra
        # entrando, verso l'abside). Chi guarda la parete Ovest (+v)
        # dall'interno ha la facciata (u piccolo) a SINISTRA, perche'
        # (u, v, w) e' una terna destrorsa.
        sign = -1.0 if card.facing == "plus_v" else 1.0
        left = (card.u - sign * half_w, card.v)
        right = (card.u + sign * half_w, card.v)
    else:
        # NOTA: "plus_u"/"minus_u" non sono simmetrici per riflessione
        # come plus_v/minus_v - il segno corretto e' stato verificato
        # empiricamente confrontando il testo delle meridiane nella
        # foto reale della facciata (era speculare con sign=-1 su
        # minus_u prima di questa correzione).
        sign = 1.0 if card.facing == "plus_u" else -1.0
        left = (card.u, card.v - sign * half_w)
        right = (card.u, card.v + sign * half_w)

    bottom_left = (left[0], left[1], card.w_bottom)
    bottom_right = (right[0], right[1], card.w_bottom)
    top_right = (right[0], right[1], card.w_bottom + card.height_m)
    top_left = (left[0], left[1], card.w_bottom + card.height_m)
    return [bottom_left, bottom_right, top_right, top_left]


def build_curved_apse_panel(
    plotter: pv.Plotter,
    church: ChurchModel,
    filename: str = APSE_PHOTO_FILENAME,
    height_bottom: float = APSE_PHOTO_HEIGHT_BOTTOM,
    height_top: float = APSE_PHOTO_HEIGHT_TOP,
) -> list:
    """
    Pannello fotografico NON piatto per l'abside: una striscia di
    quadrilateri che segue i 5 lati reali del pentagono absidale
    (`church.apse_vertices()`) PIU' i due tratti di raccordo verso il
    muro della navata (da (L,Wh) al primo vertice, e dall'ultimo
    vertice a (L,-Wh)) - senza questi due tratti il pannello lasciava
    un varco visibile proprio vicino alla torre ("non chiude verso il
    basso", segnalato dall'utente), dato che copriva solo il pentagono
    e non il raccordo con il filo della navata. La coordinata U della
    texture e' proporzionale alla distanza percorsa lungo il
    perimetro (proiezione panoramica semplificata): cosi' la foto
    "avvolge" la vera forma dell'abside e le finestre visibili nella
    foto cadono in corrispondenza approssimativa delle 5 vetrate
    reali, ciascuna sul proprio lato.
    """
    path = os.path.join(PHOTOS_DIR, filename)
    if not os.path.isfile(path):
        return []

    Wh = church.nave_width_m / 2.0
    L = church.nave_length_m
    verts_uv = [(L, Wh)] + church.apse_vertices() + [(L, -Wh)]
    # 10 cm verso l'interno: sul filo del muro dell'abside (bianco da dentro,
    # semitrasparente) la foto ne verrebbe coperta a chiazze
    cu = sum(p[0] for p in verts_uv) / len(verts_uv)
    verts_uv = [(u + 0.1 * (cu - u) / (math.hypot(cu - u, v) or 1), v - 0.1 * v / (math.hypot(cu - u, v) or 1))
                for u, v in verts_uv]
    cum = [0.0]
    for i in range(1, len(verts_uv)):
        d = math.hypot(verts_uv[i][0] - verts_uv[i - 1][0], verts_uv[i][1] - verts_uv[i - 1][1])
        cum.append(cum[-1] + d)
    total = cum[-1] if cum[-1] > 0 else 1.0

    pts: list[tuple[float, float, float]] = []
    tex_coords: list[list[float]] = []
    for i, (u_loc, v_loc) in enumerate(verts_uv):
        u_tex = cum[i] / total
        pts.append(church.local_to_enu(u_loc, v_loc, height_bottom))
        tex_coords.append([u_tex, 0.0])
        pts.append(church.local_to_enu(u_loc, v_loc, height_top))
        tex_coords.append([u_tex, 1.0])

    n = len(verts_uv)
    faces = []
    for i in range(n - 1):
        i0 = i * 2
        faces += [4, i0, i0 + 2, i0 + 3, i0 + 1]

    mesh = pv.PolyData(np.array(pts), faces=np.array(faces))
    mesh.active_texture_coordinates = np.array(tex_coords)
    try:
        tex = pv.read_texture(path)
    except Exception:
        return []

    actor = plotter.add_mesh(
        mesh, texture=tex, name=f"photo_curved_{filename}",
        show_edges=False, lighting=False,
    )
    actors = [actor]

    bottom_line = np.array(pts[0::2])
    top_line = np.array(pts[1::2])
    for line_pts, tag in [(bottom_line, "bottom"), (top_line, "top")]:
        line_mesh = pv.lines_from_points(line_pts)
        fa = plotter.add_mesh(
            line_mesh, color="#2b2b2b", line_width=2,
            name=f"photo_curved_frame_{filename}_{tag}",
        )
        actors.append(fa)

    return actors


def _window_along_vector(church: ChurchModel, window) -> tuple[float, float]:
    """Stessa identica formula usata da Window.local_outline() in
    church_geometry.py, per restare coerenti con la forma reale della
    vetrata (vedi commenti li' per la spiegazione)."""
    tangent_world_rad = math.radians(window.wall_azimuth_deg - 90.0)
    return church.enu_to_local_uv(math.sin(tangent_world_rad), math.cos(tangent_world_rad))


def _window_outward_vector(church: ChurchModel, window) -> tuple[float, float]:
    th = math.radians(window.wall_azimuth_deg)
    du, dv = church.enu_to_local_uv(math.sin(th), math.cos(th))
    mag = math.hypot(du, dv) or 1.0
    return du / mag, dv / mag


def build_window_photo_overlays(
    plotter: pv.Plotter,
    church: ChurchModel,
    mapping: dict[str, str] = None,
    inset: float = 0.03,      # 1 cm davanti alla faccia interna della vetrata (church_mesh.build_window_solid)
) -> list:
    """
    Sovrappone le foto reali (ritagliate da im1.jpg/im2.jpg) sulla
    faccia interna delle vetrate di cleristorio corrispondenti, al
    posto del colore pieno arancione della mesh sotto. Il pannello e'
    arretrato di `inset` metri verso l'interno della navata (opposto
    alla normale uscente) per restare chiaramente DAVANTI alla mesh
    piena e a qualunque macchia di luce che la sfiori, evitando
    z-fighting/sovrapposizioni indesiderate.

    Le coordinate texture sono calcolate proiettando ciascun punto del
    contorno reale della vetrata (`Window.local_outline()`, arco
    incluso) sulla stessa base locale (largo/alto) usata per costruire
    la vetrata stessa, cosi' la foto si adatta esattamente alla vera
    sagoma ad arco, non a un rettangolo.
    """
    if mapping is None:
        mapping = CHAPEL_WINDOW_PHOTOS
    actors = []
    windows_by_name = {w.name: w for w in church.windows}
    for name, filename in mapping.items():
        win = windows_by_name.get(name)
        if win is None:
            continue
        path = os.path.join(PHOTOS_DIR, filename)
        if not os.path.isfile(path):
            continue

        along = _window_along_vector(church, win)
        outward = _window_outward_vector(church, win)
        total_h = (win.head_m + win.arch_rise_m) - win.sill_m
        if total_h <= 0:
            continue

        outline = win.local_outline()
        pts = []
        tex_coords = []
        for (u, v, w) in outline:
            u_in = u - outward[0] * inset
            v_in = v - outward[1] * inset
            pts.append(church.local_to_enu(u_in, v_in, w))
            du_, dv_ = u - win.wall_point_uv[0], v - win.wall_point_uv[1]
            s = du_ * along[0] + dv_ * along[1]
            # CORRETTO: era 0.5 + s/width, foto speculari viste
            # dall'interno. `along` punta alla SINISTRA di chi guarda la
            # vetrata da dentro (azimut parete - 90), quindi U cresce
            # verso destra con il segno meno. Verificato sulle vetrate
            # della facciata (asta e stemma della vetrata Ovest).
            u_tex = 0.5 - s / win.width_m
            v_tex = (w - win.sill_m) / total_h
            tex_coords.append([u_tex, v_tex])

        # centro (per la triangolazione a ventaglio: piu' robusto di un
        # singolo n-gono per una sagoma non convessa come l'arco)
        cu = win.wall_point_uv[0] - outward[0] * inset
        cv = win.wall_point_uv[1] - outward[1] * inset
        cw = win.sill_m + total_h * 0.5
        pts.append(church.local_to_enu(cu, cv, cw))
        tex_coords.append([0.5, 0.5])
        center_idx = len(pts) - 1

        n = center_idx  # numero di punti del contorno (esclude il centro)
        faces = []
        for i in range(n):
            j = (i + 1) % n
            faces += [3, center_idx, i, j]

        mesh = pv.PolyData(np.array(pts), faces=np.array(faces))
        mesh.active_texture_coordinates = np.array(tex_coords)
        try:
            tex = pv.read_texture(path)
        except Exception:
            continue

        actor = plotter.add_mesh(
            mesh, texture=tex, name=f"windowphoto_{name}",
            show_edges=False, lighting=False,
        )
        actors.append(actor)

    return actors


def build_photo_actors(plotter: pv.Plotter, church: ChurchModel) -> list:
    """Aggiunge tutti i pannelli fotografici (piatti + il pannello
    curvo dell'abside) al plotter (nel subplot gia' attivo al momento
    della chiamata) e ritorna la lista degli attori creati, cosi' che
    possano essere nascosti/mostrati insieme."""
    actors = []
    ATTORI_CAPPELLE.clear()
    for card in PHOTO_CARDS:
        path = os.path.join(PHOTOS_DIR, card.filename)
        if not os.path.isfile(path):
            continue
        corners_local = _card_corners_local(card)
        pts = np.array([church.local_to_enu(u, v, w) for (u, v, w) in corners_local])
        if card.foro_cappella:
            p_l, uv, tr = card_con_foro(card)
            a = _mesh_testurizzata(plotter, church, p_l, uv, tr, path, f"photo_{card.filename}")
            ATTORI_CAPPELLE.append(a)  # visibili solo da dentro (viewer_3d)
            actors.append(a)
            continue

        mesh = pv.PolyData(pts, faces=np.array([4, 0, 1, 2, 3]))
        mesh.active_texture_coordinates = np.array(
            [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
        )
        try:
            tex = pv.read_texture(path)
        except Exception:
            continue

        actor = plotter.add_mesh(
            mesh, texture=tex, name=f"photo_{card.filename}",
            show_edges=False, lighting=False,
        )
        actors.append(actor)
        if card.solo_fronte:
            # i 4 angoli sono in senso antiorario visti dal fronte: la
            # normale punta verso chi guarda da fuori, il retro si scarta
            actor.GetProperty().BackfaceCullingOn()
            continue  # niente cornice: si vedrebbe anche da dentro

        # sottile cornice per leggibilita'
        frame_pts = np.vstack([pts, pts[0]])
        frame = pv.lines_from_points(frame_pts)
        frame_actor = plotter.add_mesh(
            frame, color="#2b2b2b", line_width=2, name=f"photo_frame_{card.filename}",
        )
        actors.append(frame_actor)

    for nome, lato, indice in NICCHIE:
        for suff, p_l, uv, tr in nicchia_parti(lato, indice, church):
            path = os.path.join(PHOTOS_DIR, f"{nome}_{suff}.jpg")
            if os.path.isfile(path):
                a = _mesh_testurizzata(plotter, church, p_l, uv, tr, path, f"nicchia_{nome}_{suff}")
                ATTORI_CAPPELLE.append(a)
                actors.append(a)

    abside = build_curved_apse_panel(plotter, church)
    ATTORI_CAPPELLE.extend(abside)  # foto presa da dentro: solo da dentro, come le cappelle
    actors.extend(abside)
    actors.extend(build_window_photo_overlays(plotter, church))
    return actors
