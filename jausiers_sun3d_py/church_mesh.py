"""
church_mesh.py
---------------
Costruisce la mesh 3D SOLIDA (volumetrica) della chiesa a partire dal
modello parametrico di `church_geometry.py`: mura con spessore reale,
tetto, pavimento (soletta), vetrate come inserti vetrati solidi
incassati nello spessore del muro.

Tutto e' costruito nel sistema di coordinate MONDO usato da
`ChurchModel.local_to_enu`: X = Est, Y = Nord, Z = Alto (metri) -
lo stesso sistema "Z-up" che PyVista/VTK usano di default.
"""

from __future__ import annotations

import math

import numpy as np
import pyvista as pv

from church_geometry import (
    banchi_scatole,
    APSE_RECESS_M, GRADINI_N, GRADINO_ALZATA_M, GRADINO_PEDATA_M,
    CAPPELLA_GRADINI_N, CAPPELLA_GRADINO_ALZATA_M, CAPPELLA_GRADINO_PEDATA_M, CHAPEL_ARCH_RADIUS_M,
    ALTARI_CAPPELLE, ALTARE_CAPPELLA_LARGHEZZA_M, ALTARE_CAPPELLA_PROFONDITA_M, ALTARE_CAPPELLA_ALTEZZA_M,
    CHAPEL_PROJECTION_DEPTH_M as _DD, CHAPEL_PROJECTION_WIDTH_M as _DW,
    BANCHI_U_INIZIO_M, BANCHI_PASSO_M, BANCHI_V_CORRIDOIO_M, BANCHI_V_ESTERNO_M,
    ALTARE_U_CENTRO_M, ALTARE_LARGHEZZA_M, ALTARE_PROFONDITA_M, ALTARE_ALTEZZA_M,
    RISCALDAMENTO_U_M, RISCALDAMENTO_V_M, RISCALDAMENTO_LARGHEZZA_M, RISCALDAMENTO_PROFONDITA_M,
    RISCALDAMENTO_ALTEZZA_M,
    PULPITO_FRA_CAPPELLE, PULPITO_RAGGIO_M, PULPITO_PIANO_M, PULPITO_PARAPETTO_M,
    PULPITO_BALDACCHINO_M, PULPITO_CIMA_M,
    ORGANO_U_M, ORGANO_V_M, ORGANO_LARGHEZZA_M, ORGANO_PROFONDITA_M, ORGANO_ALTEZZA_M,
    CORNICIONE_BASE_M, CORNICIONE_CIMA_M, CORNICIONE_SPORGENZA_M,
    VOLTA_ABSIDE_CHIAVE_M, VOLTA_ABSIDE_LUNETTE_M, VOLTA_ABSIDE_NT, VOLTA_ABSIDE_NA, VOLTA_ABSIDE_NM,
    VOLTA_NAVATA_CHIAVE_M, VOLTA_NAVATA_LUNETTE_M, VOLTA_NAVATA_LUNETTA_LARGA_M,
    LAMPADARIO_ALTO_M, LAMPADARIO_BASSO_M, LAMPADARIO_RAGGIO_BRACCI_M, LAMPADARIO_N_BRACCI,
    LAMPADARIO_RAGGIO_BRACCI_BASSO_M, LAMPADARI_NAVATA_U_M, LAMPADARIO_NAVATA_ALTO_M, LAMPADARIO_NAVATA_BASSO_M,
    BUSSOLA_LARGHEZZA_M, BUSSOLA_PROFONDITA_M, BUSSOLA_ALTEZZA_M, PORTONE_LARGHEZZA_M, PORTONE_ALTEZZA_M,
    LESENA_LARGHEZZA_M, LESENA_SPORGENZA_M, LESENA_ZOCCOLO_M, CROCE_CONSACRAZIONE_M, CORNICIONE_BASE_M as _CB,
    BALAUSTRA_U_M, BALAUSTRA_ALTEZZA_M, BALAUSTRA_VARCO_M,
    ChurchModel, Window, WALL_HEIGHT_M, ROOF_RIDGE_RISE_M as _ROOF_RIDGE_RISE_M,
    TOWER_U_CENTER_M, TOWER_V_CENTER_M, TOWER_WIDTH_U_M, TOWER_WIDTH_V_M,
    TOWER_BODY_HEIGHT_M, TOWER_SPIRE_HEIGHT_M,
    CHAPEL_ROOF_HEIGHT_M, CHAPEL_ROOF_PITCH_RISE_M, CHAPEL_ROW_MARGIN_M, CHAPEL_PROJECTION_DEPTH_M,
    CHAPEL_PROJECTION_WIDTH_M,
    NARTHEX_WIDTH_M, NARTHEX_DEPTH_M, NARTHEX_HEIGHT_AT_WALL_M, NARTHEX_HEIGHT_AT_EDGE_M,
    CHAPEL_WINDOW_RECESS_M,
    APSE_EXTERNAL_HEIGHT_M, APSE_ROOF_RIDGE_RISE_M,
)

WALL_THICKNESS_M = 0.70   # spessore muro (stima: muratura in pietra tipica)
FLOOR_THICKNESS_M = 0.30  # spessore soletta pavimento (solo estetico)
ROOF_RIDGE_RISE_M = _ROOF_RIDGE_RISE_M   # sincronizzato con church_geometry.py


# =====================================================================
# Geometria di supporto (poligoni in pianta locale u,v)
# =====================================================================

def _polygon_signed_area(loop_uv: list[tuple[float, float]]) -> float:
    a = 0.0
    n = len(loop_uv)
    for i in range(n):
        x1, y1 = loop_uv[i]
        x2, y2 = loop_uv[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def offset_loop_outward(loop_uv: list[tuple[float, float]], distance: float) -> list[tuple[float, float]]:
    """Ritorna un anello (u,v) spostato verso l'esterno di `distance`
    metri (giunzione a mitria). loop_uv NON deve avere l'ultimo punto
    duplicato (poligono "aperto": n vertici distinti)."""
    pts = np.array(loop_uv, dtype=float)
    n = len(pts)
    sign = 1.0 if _polygon_signed_area(loop_uv) > 0 else -1.0

    def edge_normal(p1, p2):
        d = p2 - p1
        d = d / np.linalg.norm(d)
        rot = np.array([d[1], -d[0]]) if sign > 0 else np.array([-d[1], d[0]])
        return rot

    out = []
    for i in range(n):
        p_prev, p_cur, p_next = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        n1 = edge_normal(p_prev, p_cur)
        n2 = edge_normal(p_cur, p_next)
        avg = n1 + n2
        norm = np.linalg.norm(avg)
        avg_dir = n1 if norm < 1e-9 else avg / norm
        cos_half = float(np.dot(avg_dir, n1))
        miter = distance / cos_half if abs(cos_half) > 1e-3 else distance
        out.append(tuple(p_cur + avg_dir * miter))
    return out


def local_outward_dir_uv(church: ChurchModel, wall_azimuth_deg: float) -> tuple[float, float]:
    """Direzione (du,dv) unitaria, nel piano locale (u,v), corrispondente
    all'azimut di bussola dato (usa l'inversa della trasformazione
    locale->mondo gia' presente nel modello)."""
    th = math.radians(wall_azimuth_deg)
    east, north = math.sin(th), math.cos(th)
    u, v = church.enu_to_local_uv(east, north)
    mag = math.hypot(u, v)
    return (u / mag, v / mag)


# =====================================================================
# Costruttori di mesh elementari
# =====================================================================

def _pts_local_to_world(church: ChurchModel, pts_uvw) -> np.ndarray:
    return np.array([church.local_to_enu(u, v, w) for (u, v, w) in pts_uvw])


def flat_polygon(loop_uv, z: float, church: ChurchModel, reverse: bool = False) -> pv.PolyData:
    order = list(reversed(loop_uv)) if reverse else list(loop_uv)
    pts = _pts_local_to_world(church, [(u, v, z) for (u, v) in order])
    n = len(pts)
    face = np.array([n, *range(n)])
    return pv.PolyData(pts, faces=face)


def vertical_band(loop_uv, z0: float, z1: float, church: ChurchModel, closed: bool = True) -> pv.PolyData:
    n = len(loop_uv)
    pts = _pts_local_to_world(church, [(u, v, z0) for (u, v) in loop_uv] + [(u, v, z1) for (u, v) in loop_uv])
    faces = []
    n_edges = n if closed else n - 1
    for i in range(n_edges):
        j = (i + 1) % n
        faces += [4, i, j, n + j, n + i]
    return pv.PolyData(pts, faces=np.array(faces))


def ring_cap(inner_loop_uv, outer_loop_uv, z: float, church: ChurchModel) -> pv.PolyData:
    n = len(inner_loop_uv)
    pts = _pts_local_to_world(church, [(u, v, z) for (u, v) in inner_loop_uv] + [(u, v, z) for (u, v) in outer_loop_uv])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [4, i, j, n + j, n + i]
    return pv.PolyData(pts, faces=np.array(faces))


# =====================================================================
# Componenti principali dell'edificio
# =====================================================================

def build_floor(inner_loop_uv, church: ChurchModel, thickness: float = FLOOR_THICKNESS_M) -> pv.PolyData:
    top = flat_polygon(inner_loop_uv, 0.0, church, reverse=False)
    bottom = flat_polygon(inner_loop_uv, -thickness, church, reverse=True)
    side = vertical_band(inner_loop_uv, -thickness, 0.0, church)
    return top.merge(bottom).merge(side)


def _prisma(loop_uv, h, church: ChurchModel) -> pv.PolyData:
    """Prisma verticale da 0 a h sul contorno loop_uv (senza fondo)."""
    return flat_polygon(loop_uv, h, church, reverse=False).merge(vertical_band(loop_uv, 0.0, h, church))


def build_gradini(church: ChurchModel) -> pv.PolyData:
    """Tre gradini davanti all'arco trionfale, larghi quanto l'apertura
    dell'abside, piu' il pavimento rialzato dell'abside (vedi
    quota_pavimento in church_geometry.py)."""
    L = church.nave_length_m
    vh = church.nave_width_m / 2.0 - APSE_RECESS_M
    parti = []
    for k in range(1, GRADINI_N + 1):
        u0 = L - (GRADINI_N - k + 1) * GRADINO_PEDATA_M
        u1 = L - (GRADINI_N - k) * GRADINO_PEDATA_M
        parti.append(_prisma([(u0, vh), (u1, vh), (u1, -vh), (u0, -vh)], k * GRADINO_ALZATA_M, church))
    parti.append(_prisma(church.apse_vertices(), GRADINI_N * GRADINO_ALZATA_M, church))
    # due gradini all'ingresso di ogni cappella e il suo piano rialzato
    wh, a, p, R = church.nave_width_m / 2.0, CAPPELLA_GRADINO_ALZATA_M, CAPPELLA_GRADINO_PEDATA_M, CHAPEL_ARCH_RADIUS_M
    for uc in church.chapel_u_positions():
        for lato in (1.0, -1.0):
            for v0, v1, u0, u1, h in ((wh - p, wh, uc - R, uc + R, a),
                                      (wh, wh + p, uc - R, uc + R, CAPPELLA_GRADINI_N * a),
                                      (wh + p, wh + _DD, uc - _DW / 2, uc + _DW / 2, CAPPELLA_GRADINI_N * a)):
                lo, hi = sorted((lato * v0, lato * v1))
                parti.append(_prisma([(u0, hi), (u1, hi), (u1, lo), (u0, lo)], h, church))
    out = parti[0]
    for p in parti[1:]:
        out = out.merge(p)
    return out


def _scatola(loop_uv, w0, w1, church: ChurchModel) -> pv.PolyData:
    """Solido chiuso: contorno loop_uv (stesso verso del pavimento) da w0 a w1."""
    return (flat_polygon(loop_uv, w1, church, reverse=False)
            .merge(flat_polygon(loop_uv, w0, church, reverse=True))
            .merge(vertical_band(loop_uv, w0, w1, church)))


def _blocco(u0, u1, v0, v1, w0, w1, church: ChurchModel) -> pv.PolyData:
    lo, hi = min(v0, v1), max(v0, v1)
    return _scatola([(u0, hi), (u1, hi), (u1, lo), (u0, lo)], w0, w1, church)


def _unisci(parti):
    out = parti[0]
    for p in parti[1:]:
        out = out.merge(p)
    return out


def build_banchi(church: ChurchModel) -> pv.PolyData:
    """Banchi di legno in due file ai lati del corridoio (vedi banchi_scatole)."""
    return _unisci([_blocco(u0, u1, v0, v1, w0, w1, church) for (u0, u1, v0, v1, w0, w1) in banchi_scatole(church)])


def build_balaustra(church: ChurchModel) -> pv.PolyData:
    """Balaustra in ferro in cima ai gradini: corrimano, traversa bassa,
    montanti ogni ~1.2 m e sbarre sottili ogni 12 cm, in due tratti
    ai lati del varco centrale."""
    q = GRADINI_N * GRADINO_ALZATA_M
    h = BALAUSTRA_ALTEZZA_M
    u = BALAUSTRA_U_M
    vh = church.nave_width_m / 2.0 - APSE_RECESS_M
    parti = []
    for lato in (1.0, -1.0):
        a, b = lato * BALAUSTRA_VARCO_M / 2, lato * vh
        parti.append(_blocco(u - 0.05, u + 0.05, a, b, q + h - 0.06, q + h, church))    # corrimano
        parti.append(_blocco(u - 0.02, u + 0.02, a, b, q + 0.06, q + 0.10, church))     # traversa bassa
        lung = abs(b - a)
        n_mont = max(1, round(lung / 1.2))
        for k in range(n_mont + 1):
            v = a + (b - a) * k / n_mont
            parti.append(_blocco(u - 0.03, u + 0.03, v - 0.03, v + 0.03, q, q + h, church))
        n_sbarre = int(lung / 0.12)
        for k in range(1, n_sbarre):
            v = a + (b - a) * k / n_sbarre
            parti.append(_blocco(u - 0.01, u + 0.01, v - 0.01, v + 0.01, q + 0.10, q + h - 0.06, church))
    return _unisci(parti)


def build_altari(church: ChurchModel) -> tuple[pv.PolyData, pv.PolyData]:
    """L'altare in cima ai gradini (tavolo con tovaglia bianca): base in
    marmo e tovaglia che ricade sui lati. Ritorna (marmo, tovaglia)."""
    q = GRADINI_N * GRADINO_ALZATA_M
    h = ALTARE_ALTEZZA_M
    u0, u1 = ALTARE_U_CENTRO_M - ALTARE_PROFONDITA_M / 2, ALTARE_U_CENTRO_M + ALTARE_PROFONDITA_M / 2
    hw = ALTARE_LARGHEZZA_M / 2
    marmo = _blocco(u0 + 0.08, u1 - 0.08, -hw + 0.08, hw - 0.08, q, q + h - 0.02, church)
    tovaglia = _blocco(u0, u1, -hw, hw, q + h - 0.30, q + h, church)
    return marmo, tovaglia


def build_riscaldamento(church: ChurchModel) -> pv.PolyData:
    """Armadi in legno del riscaldamento ai due lati dell'abside: cassa
    alta, cornice in cima e griglia a lamelle sul fronte (verso la
    navata) nella parte alta."""
    q = GRADINI_N * GRADINO_ALZATA_M
    h = RISCALDAMENTO_ALTEZZA_M
    du, dv = RISCALDAMENTO_PROFONDITA_M / 2, RISCALDAMENTO_LARGHEZZA_M / 2
    u0, u1 = RISCALDAMENTO_U_M - du, RISCALDAMENTO_U_M + du
    parti = []
    for lato in (1.0, -1.0):
        c = lato * RISCALDAMENTO_V_M
        parti.append(_blocco(u0, u1, c - dv, c + dv, q, q + h, church))                       # cassa
        parti.append(_blocco(u0 - 0.04, u1 + 0.04, c - dv - 0.04, c + dv + 0.04, q + h - 0.08, q + h, church))  # cornice
        parti.append(_blocco(u0 - 0.03, u1, c - dv - 0.02, c + dv + 0.02, q, q + 0.12, church))  # zoccolo
        for k in range(8):                                                                      # lamelle
            w = q + h - 1.25 + k * 0.14
            parti.append(_blocco(u0 - 0.04, u0, c - dv + 0.06, c + dv - 0.06, w, w + 0.05, church))
    return _unisci(parti)


def _ottagono(cu, cv, r):
    pts = [(cu + r * math.cos(math.pi / 8 + k * math.pi / 4), cv + r * math.sin(math.pi / 8 + k * math.pi / 4))
           for k in range(8)]
    return pts if _polygon_signed_area(pts) < 0 else pts[::-1]


def _piramide(loop_uv, w0, punta, church: ChurchModel) -> pv.PolyData:
    """Piramide dal contorno loop_uv a quota w0 fino a punta = (u, v, w)."""
    n = len(loop_uv)
    pts = _pts_local_to_world(church, [(u, v, w0) for (u, v) in loop_uv] + [punta])
    faces = []
    for i in range(n):
        faces += [3, i, (i + 1) % n, n]
    return pv.PolyData(np.array(pts), faces=np.array(faces)).merge(flat_polygon(loop_uv, w0, church, reverse=True))


def build_pulpito(church: ChurchModel) -> pv.PolyData:
    """Pulpito in legno sul pilastro fra due cappelle a sinistra entrando
    (v = +Wh): sostegno, cassa ottagonale con cornici, pannello contro il
    pilastro e baldacchino a piramide con un pinnacolo in cima."""
    us = church.chapel_u_positions()
    u = (us[PULPITO_FRA_CAPPELLE[0]] + us[PULPITO_FRA_CAPPELLE[1]]) / 2
    wh = church.nave_width_m / 2.0
    r = PULPITO_RAGGIO_M
    v = wh - 0.15 - r                                    # centro della cassa, staccata dal pilastro
    w0, w1 = PULPITO_PIANO_M, PULPITO_PIANO_M + PULPITO_PARAPETTO_M
    parti = [
        _blocco(u - 0.25, u + 0.25, v - 0.1, wh, 0.0, w0, church),                       # sostegno
        _scatola(_ottagono(u, v, r * 0.7), w0 - 0.35, w0, church),                       # fondo rastremato
        _scatola(_ottagono(u, v, r), w0, w1, church),                                    # cassa
        _scatola(_ottagono(u, v, r + 0.06), w0, w0 + 0.10, church),                      # cornice bassa
        _scatola(_ottagono(u, v, r + 0.08), w1 - 0.08, w1, church),                      # cornice alta
        _blocco(u - 0.45, u + 0.45, wh - 0.10, wh, w1, PULPITO_BALDACCHINO_M, church),   # pannello sul pilastro
    ]
    rb = r + 0.25                                                                         # baldacchino
    parti.append(_scatola(_ottagono(u, v, rb), PULPITO_BALDACCHINO_M, PULPITO_BALDACCHINO_M + 0.20, church))
    parti.append(_piramide(_ottagono(u, v, rb - 0.05), PULPITO_BALDACCHINO_M + 0.20,
                           (u, v, PULPITO_CIMA_M), church))
    parti.append(_blocco(u - 0.06, u + 0.06, v - 0.06, v + 0.06, PULPITO_CIMA_M - 0.2, PULPITO_CIMA_M + 0.35, church))
    return _unisci(parti)


def build_organo(church: ChurchModel) -> tuple[pv.PolyData, pv.PolyData]:
    """Consolle dell'organo: cassa in legno chiaro con il leggio in cima
    (verso l'abside: l'organista guarda l'altare) e zoccolo scuro
    rientrato sotto (pedaliera). Ritorna (legno, zoccolo)."""
    du, dv = ORGANO_PROFONDITA_M / 2, ORGANO_LARGHEZZA_M / 2
    u, v, h = ORGANO_U_M, ORGANO_V_M, ORGANO_ALTEZZA_M
    legno = _unisci([
        _blocco(u - du, u + du, v - dv, v + dv, 0.14, h, church),                         # cassa
        _blocco(u + 0.05, u + 0.10, v - dv + 0.2, v + dv - 0.2, h, h + 0.38, church),     # leggio
        _blocco(u - du - 0.02, u + du + 0.02, v - dv - 0.02, v + dv + 0.02, h - 0.03, h, church),  # coperchio
    ])
    zoccolo = _blocco(u - du + 0.08, u + du - 0.04, v - dv + 0.06, v + dv - 0.06, 0.0, 0.14, church)
    return legno, zoccolo


def build_oggetti_altare(church: ChurchModel) -> dict:
    """Sull'altare: due candelieri dorati con candela accesa ai lati, un
    crocifisso dorato al centro (dalla parte dell'abside) e il messale
    rosso sul leggio, dalla parte del celebrante (verso l'abside: l'altare
    e' rivolto alla navata). Ritorna {oro, cera, fiamma, libro}."""
    w = GRADINI_N * GRADINO_ALZATA_M + ALTARE_ALTEZZA_M      # piano dell'altare
    u = ALTARE_U_CENTRO_M
    ub = u + ALTARE_PROFONDITA_M / 2 - 0.15                    # verso l'abside
    oro, cera, fiamma = [], [], []
    for v in (ALTARE_LARGHEZZA_M / 2 - 0.25, -(ALTARE_LARGHEZZA_M / 2 - 0.25)):
        oro += [_blocco(ub - 0.07, ub + 0.07, v - 0.07, v + 0.07, w, w + 0.04, church),             # piede
                _blocco(ub - 0.015, ub + 0.015, v - 0.015, v + 0.015, w + 0.04, w + 0.34, church),  # fusto
                _blocco(ub - 0.045, ub + 0.045, v - 0.045, v + 0.045, w + 0.34, w + 0.36, church)]  # piattello
        cera.append(_blocco(ub - 0.022, ub + 0.022, v - 0.022, v + 0.022, w + 0.36, w + 0.62, church))
        fiamma.append(_blocco(ub - 0.008, ub + 0.008, v - 0.008, v + 0.008, w + 0.63, w + 0.67, church))
    oro += [_blocco(ub - 0.08, ub + 0.08, -0.08, 0.08, w, w + 0.05, church),                       # crocifisso
            _blocco(ub - 0.015, ub + 0.015, -0.015, 0.015, w + 0.05, w + 0.62, church),
            _blocco(ub - 0.015, ub + 0.015, -0.12, 0.12, w + 0.45, w + 0.48, church)]
    ul = u + 0.05                                                                                     # messale
    libro = _unisci([_blocco(ul - 0.12, ul + 0.12, 0.30, 0.56, w, w + 0.06, church),
                     _blocco(ul - 0.14, ul + 0.14, 0.28, 0.58, w + 0.06, w + 0.10, church)])
    return {"oro": _unisci(oro), "cera": _unisci(cera), "fiamma": _unisci(fiamma), "libro": libro}


# profilo del cornicione: (da, a, sporgenza) in frazioni dell'altezza e
# della sporgenza totale, dal basso: due fasce dell'architrave, fregio,
# modanatura, fascia dei dentelli, fascia delle mensoline, cornice
_PROFILO_CORNICIONE = [(0.00, 0.13, 0.19), (0.13, 0.27, 0.26), (0.27, 0.63, 0.16),
                       (0.63, 0.70, 0.40), (0.70, 0.78, 0.52), (0.78, 0.90, 0.60), (0.90, 1.00, 1.00)]


def build_cornicione(church: ChurchModel) -> pv.PolyData:
    """Cornicione interno lungo i due fianchi della navata (sopra le
    cappelle) e la controfacciata, NON nell'abside: si ferma contro
    l'arco trionfale. Fasce sovrapposte che sporgono sempre di piu'
    verso l'alto, con le mensoline (ogni 0.5 m) sotto la cornice."""
    L, wh = church.nave_length_m, church.nave_width_m / 2.0
    muro = [(L, -wh), (0.0, -wh), (0.0, wh), (L, wh)]

    def dentro(d):                    # il percorso spostato di d verso l'interno
        return [(L, -(wh - d)), (d, -(wh - d)), (d, wh - d), (L, wh - d)]

    def fascia(a, b, w):              # striscia orizzontale fra due percorsi aperti
        pts = [(u, v, w) for (u, v) in a] + [(u, v, w) for (u, v) in b]
        n = len(a)
        faces = []
        for k in range(n - 1):
            faces += [4, k, k + 1, n + k + 1, n + k]
        return pv.PolyData(_pts_local_to_world(church, pts), faces=np.array(faces))

    h0, H, D = CORNICIONE_BASE_M, CORNICIONE_CIMA_M - CORNICIONE_BASE_M, CORNICIONE_SPORGENZA_M
    parti = []
    for a, b, d in _PROFILO_CORNICIONE:
        w0, w1 = h0 + a * H, h0 + b * H
        dd = dentro(d * D)
        parti += [vertical_band(dd, w0, w1, church, closed=False), fascia(muro, dd, w0), fascia(muro, dd, w1)]
        for k in (0, -1):             # testate contro l'arco trionfale
            parti.append(vertical_band([muro[k], dd[k]], w0, w1, church, closed=False))
    wm0, wm1 = h0 + 0.70 * H, h0 + 0.90 * H
    for i in range(len(muro) - 1):
        p, q = np.array(muro[i]), np.array(muro[i + 1])
        lung = np.linalg.norm(q - p)
        a = (q - p) / lung
        nrm = np.array([a[1], -a[0]])                      # verso l'interno
        k = int((lung - 0.5) / 0.5)
        for j in range(k + 1):
            c = p + a * (0.25 + j * (lung - 0.5) / max(k, 1))
            pts = [tuple(c + a * x + nrm * y) for x, y in ((-0.06, 0), (0.06, 0), (0.06, 0.9 * D), (-0.06, 0.9 * D))]
            if _polygon_signed_area(pts) > 0:
                pts = pts[::-1]
            parti.append(_scatola(pts, wm0, wm1, church))
    return _unisci(parti)


def _griglia(punti, church: ChurchModel) -> pv.PolyData:
    """Superficie da una griglia di punti locali punti[i][j] = (u, v, w)."""
    ni, nj = len(punti), len(punti[0])
    pts = _pts_local_to_world(church, [p for riga in punti for p in riga])
    faces = []
    for i in range(ni - 1):
        for j in range(nj - 1):
            a = i * nj + j
            faces += [4, a, a + 1, a + nj + 1, a + nj]
    return pv.PolyData(np.array(pts), faces=np.array(faces))


def bordo_volta_abside(church: ChurchModel) -> list:
    """Bordo della volta dell'abside, in ordine: i 5 lati del pentagono
    (imposta che sale a lunetta sopra ogni finestra), poi l'arco trionfale
    da Est a Ovest passando per la chiave dell'arco. [(u, v, w)]"""
    ap = church.apse_vertices()
    w0, wc, wl = CORNICIONE_CIMA_M, VOLTA_ABSIDE_CHIAVE_M, VOLTA_ABSIDE_LUNETTE_M
    pts = []
    for i in range(len(ap) - 1):
        p, q = np.array(ap[i]), np.array(ap[i + 1])
        for k in range(VOLTA_ABSIDE_NT):
            t = k / VOLTA_ABSIDE_NT
            P = p + (q - p) * t
            pts.append((P[0], P[1], w0 + (wl - w0) * math.sqrt(max(math.sin(math.pi * t), 0.0))))
    va, L = ap[0][1], church.nave_length_m
    for k in range(VOLTA_ABSIDE_NA + 1):
        f = math.pi * k / VOLTA_ABSIDE_NA
        pts.append((L, -va * math.cos(f), w0 + (wc - w0) * math.sin(f)))
    return pts


def chiave_volta_abside(church: ChurchModel) -> tuple:
    us = [p[0] for p in church.apse_vertices()]
    return ((min(us) + max(us)) / 2, 0.0, VOLTA_ABSIDE_CHIAVE_M)


def build_volta_abside(church: ChurchModel) -> tuple[pv.PolyData, pv.PolyData]:
    """Volta a ombrello dell'abside: da ogni punto del bordo (muro con le
    lunette, poi arco trionfale) un meridiano fino alla chiave, sopra il
    centro dell'abside. Coordinate texture: (posizione lungo il bordo,
    frazione del meridiano) - la texture e' fatta con la stessa regola
    (volta_da_video.py). Ritorna (volta con le coordinate texture, muro
    sopra l'arco trionfale)."""
    L, wh = church.nave_length_m, church.nave_width_m / 2.0
    ap = church.apse_vertices()
    w0, wc = CORNICIONE_CIMA_M, VOLTA_ABSIDE_CHIAVE_M
    K = np.array(chiave_volta_abside(church))
    bordo = bordo_volta_abside(church)
    ths = [math.pi / 2 * m / VOLTA_ABSIDE_NM for m in range(VOLTA_ABSIDE_NM + 1)]
    punti = [[(K[0] + (b[0] - K[0]) * math.cos(th), K[1] + (b[1] - K[1]) * math.cos(th),
               b[2] + (wc - b[2]) * math.sin(th)) for th in ths] for b in bordo]
    vele = _griglia(punti, church)
    n = len(bordo)
    vele.active_texture_coordinates = np.array([(i / (n - 1), m / VOLTA_ABSIDE_NM)
                                                 for i in range(n) for m in range(VOLTA_ABSIDE_NM + 1)])
    # muro sopra l'arco trionfale (u = L), dal bordo dell'arco (o dal
    # cornicione, fuori dall'apertura dell'abside) fino in cima al muro
    va = ap[0][1]
    righe = []
    for k in range(41):
        v = -wh + 2 * wh * k / 40
        basso = w0 + (wc - w0) * math.sqrt(max(0.0, 1 - (v / va) ** 2)) if abs(v) < va else w0
        righe.append([(L, v, basso), (L, v, WALL_HEIGHT_M)])
    return vele, _griglia(righe, church)


def build_volta_navata(church: ChurchModel) -> pv.PolyData:
    """Volta a botte della navata: da ogni fianco (muro a v = +-Wh, imposta
    sul cornicione che sale a lunetta sopra ogni finestra alta, centrate
    sulle cappelle) un quarto d'ellisse fino al colmo a v = 0."""
    L, wh = church.nave_length_m, church.nave_width_m / 2.0
    w0, wc, wl = CORNICIONE_CIMA_M, VOLTA_NAVATA_CHIAVE_M, VOLTA_NAVATA_LUNETTE_M
    meta = VOLTA_NAVATA_LUNETTA_LARGA_M / 2
    us = sorted(set([0.0, L] + [x for uc in church.chapel_u_positions()
                                for x in np.linspace(uc - meta, uc + meta, 13)] + list(np.linspace(0, L, 40))))

    def imposta(u):
        for uc in church.chapel_u_positions():
            t = (u - uc + meta) / (2 * meta)
            if 0 < t < 1:
                return w0 + (wl - w0) * math.sqrt(math.sin(math.pi * t))
        return w0
    ths = [math.pi / 2 * m / 12 for m in range(13)]
    parti = []
    for lato in (1.0, -1.0):
        parti.append(_griglia([[(u, lato * wh * math.cos(th), imposta(u) + (wc - imposta(u)) * math.sin(th))
                                for th in ths] for u in us], church))
    return _unisci(parti)


def build_altari_cappelle(church: ChurchModel) -> list:
    """Altare di ogni cappella, contro il fondo della nicchia (5 cm davanti
    al muro di fondo, come le foto): mensa del colore del paliotto,
    tovaglia bianca che ricade di 25 cm, gradino sopra la mensa verso il
    fondo. [(nome, {"fronte": mesh, "tovaglia": mesh, "gradino": mesh},
    colore fronte, colore gradino)]."""
    wh = church.nave_width_m / 2.0
    q = CAPPELLA_GRADINI_N * CAPPELLA_GRADINO_ALZATA_M
    hw, pr, h = ALTARE_CAPPELLA_LARGHEZZA_M / 2, ALTARE_CAPPELLA_PROFONDITA_M, ALTARE_CAPPELLA_ALTEZZA_M
    out = []
    for nome, lato, i, cf, cg in ALTARI_CAPPELLE:
        uc = church.chapel_u_positions()[i]
        fondo = wh + _DD - 0.07
        v = lambda x: lato * x
        parti = {
            "fronte": _blocco(uc - hw + 0.05, uc + hw - 0.05, v(fondo - pr + 0.05), v(fondo), q, q + h - 0.02, church),
            "tovaglia": _blocco(uc - hw, uc + hw, v(fondo - pr), v(fondo), q + h - 0.25, q + h, church),
            "gradino": _blocco(uc - hw + 0.15, uc + hw - 0.15, v(fondo - 0.32), v(fondo), q + h, q + h + 0.32, church),
        }
        out.append((nome, parti, cf, cg))
    return out


def _tornio(profilo, cu, cv, church: ChurchModel, n=24, angoli=(0.0, 2 * math.pi)) -> pv.PolyData:
    """Superficie di rivoluzione attorno all'asse verticale (cu, cv):
    profilo = [(quota, raggio)] dall'alto in basso; angoli = arco percorso
    (0 = verso +u)."""
    return _griglia([[(cu + r * math.cos(a), cv + r * math.sin(a), z) for z, r in profilo]
                     for a in np.linspace(angoli[0], angoli[1], n + 1)], church)


def _coppa(z0, z1, r0, n=5):
    """Profilo di una coppa di cristalli a n gradini, da z0 (raggio r0) a z1."""
    prof, dz = [], (z0 - z1) / n
    for k in range(n):
        r = r0 * (1 - k / n) ** 0.8 + 0.06 * k / n
        prof += [(z0 - k * dz, r), (z0 - (k + 1) * dz + 0.01, r * 0.9)]
    return prof + [(z1, 0.04)]


def _lampadario(cu, cv, aggancio, a, b, R1, R2, doppio, church: ChurchModel):
    """Un lampadario di cristallo: catena dall'aggancio, corona, anello
    dorato con le candele, coppa a gradini, sfera di vetro; se doppio,
    sotto la sfera un fuso di cristallo, un secondo anello e una seconda
    coppa. Ritorna (cristallo, oro, candele) come liste di mesh."""
    H = a - b
    if doppio:
        z1 = a - 0.13 * H; zc = z1 - 0.25 * H; rs = 0.04 * H
    else:
        z1 = a - 0.16 * H; zc = b + 0.2 * H; rs = 0.06 * H
    zs = zc - rs
    sfera = [(zs + rs * math.cos(t), rs * math.sin(t)) for t in np.linspace(0, math.pi, 9)]
    cristallo = [_tornio([(a, 0.05), (a - 0.06 * H, 0.18), (z1 + 0.02, 0.30)], cu, cv, church),
                 _tornio(_coppa(z1 - 0.02, zc, R1 * 0.92), cu, cv, church),
                 _tornio(sfera, cu, cv, church)]
    anelli = [(z1, R1)]
    if doppio:
        z2 = zs - rs - 0.29 * H
        cristallo += [_tornio([(zs - rs, 0.05), (z2 + 0.25 * (zs - rs - z2), R2 * 0.45), (z2 + 0.02, R2 * 0.78)], cu, cv, church),
                      _tornio(_coppa(z2 - 0.02, b + 0.03 * H, R2 * 0.92), cu, cv, church),
                      _tornio([(b + 0.03 * H, 0.04), (b, 0.0)], cu, cv, church)]
        anelli.append((z2, R2))
    else:
        cristallo.append(_tornio([(zs - rs, 0.03), (b, 0.0)], cu, cv, church))      # pendente in punta
    oro = [_blocco(cu - 0.02, cu + 0.02, cv - 0.02, cv + 0.02, a, aggancio, church),
           _tornio([(a + 0.06, 0.06), (a, 0.12), (a - 0.03, 0.10)], cu, cv, church)]
    candele = []
    for zr, R in anelli:
        oro.append(_tornio([(zr + 0.04, R + 0.03), (zr, R + 0.06), (zr - 0.04, R + 0.03), (zr - 0.04, 0.2),
                            (zr + 0.04, 0.2), (zr + 0.04, R + 0.03)], cu, cv, church))
        for k in range(LAMPADARIO_N_BRACCI):
            t = 2 * math.pi * (k + 0.5) / LAMPADARIO_N_BRACCI
            x, y = cu + R * math.cos(t), cv + R * math.sin(t)
            oro.append(_blocco(x - 0.035, x + 0.035, y - 0.035, y + 0.035, zr + 0.04, zr + 0.09, church))
            candele.append(_blocco(x - 0.018, x + 0.018, y - 0.018, y + 0.018, zr + 0.09, zr + 0.27, church))
    return cristallo, oro, candele


def build_lampadario(church: ChurchModel) -> dict:
    """I lampadari di cristallo: quello doppio appeso alla chiave della volta
    dell'abside e i due singoli sull'asse della navata, appesi al colmo
    della volta (vedi church_geometry.py). {"cristallo", "oro", "candele"}."""
    cu, cv, chiave = chiave_volta_abside(church)
    tutti = [_lampadario(cu, cv, chiave, LAMPADARIO_ALTO_M, LAMPADARIO_BASSO_M, LAMPADARIO_RAGGIO_BRACCI_M,
                         LAMPADARIO_RAGGIO_BRACCI_BASSO_M, True, church)]
    for u in LAMPADARI_NAVATA_U_M:
        tutti.append(_lampadario(u, 0.0, VOLTA_NAVATA_CHIAVE_M, LAMPADARIO_NAVATA_ALTO_M, LAMPADARIO_NAVATA_BASSO_M,
                                 LAMPADARIO_RAGGIO_BRACCI_M, LAMPADARIO_RAGGIO_BRACCI_M, False, church))
    return {k: _unisci([m for t in tutti for m in t[n]]) for n, k in enumerate(("cristallo", "oro", "candele"))}


# colori (RGB) dal video IMG_9758 (15.6 s), tolta la dominante calda: il
# muro della controfacciata riportato al bianco degli interni, cosi' bussola,
# altarino, fonte e lesene stanno nella stessa famiglia di toni dei muri
_C = dict(pietra=0xe6e1d7, legno=0x52362b, legno_chiaro=0x7a5232, rosso=0xb5221c, giallo=0xe0b020,
          oro=0xc9a33a, marmo_scuro=0x6b625a, bianco=0xefebe4, croce=0xb83a26, nero=0x1e1e1e,
          marmo_giallo=0xcfbb9b, quadro=0x6b5038, avorio=0xe9dcc0, fondo_altare=0xb3a89c, fonte=0xae987f,
          pannello=0xbab5ac, zoccolo=0xcfc9bd, legno_pannello=0x6a4634, legno_scuro=0x3a241b, nicchia=0x9aa3a6)


def _arco_verticale(u, v0, v1, w0, w_imposta, church: ChurchModel, n=20) -> pv.PolyData:
    """Lastra verticale (piano v-w a quota u) rettangolare con l'arco a
    tutto sesto in cima: da w0 all'imposta, poi la mezza circonferenza."""
    r, vc = (v1 - v0) / 2, (v0 + v1) / 2
    return _griglia([[(u, v, w0), (u, v, w_imposta + math.sqrt(max(r * r - (v - vc) ** 2, 0.0)))]
                     for v in np.linspace(v0, v1, n + 1)], church)


def _fascia_arco(u, vc, wc, r0, r1, church: ChurchModel, n=24) -> pv.PolyData:
    """Fascia a mezzo anello in un piano v-w (a quota u), centro (vc, wc)."""
    return _griglia([[(u, vc + r0 * math.cos(a), wc + r0 * math.sin(a)), (u, vc + r1 * math.cos(a), wc + r1 * math.sin(a))]
                     for a in np.linspace(0, math.pi, n + 1)], church)


def _raggio(u, vc, wc, r0, r1, a, larg, church: ChurchModel) -> pv.PolyData:
    """Raggio sottile (largo larg) da r0 a r1 all'angolo a, in un piano v-w."""
    c, s_, t = math.cos(a), math.sin(a), larg / 2
    return _griglia([[(u, vc + r * c - t * s_, wc + r * s_ + t * c), (u, vc + r * c + t * s_, wc + r * s_ - t * c)]
                     for r in (r0, r1)], church)


def _lastra_sopra_arco(u, v0, v1, wc, r, wtop, church: ChurchModel, n=24) -> pv.PolyData:
    """Lastra in un piano v-w da v0 a v1, dall'arco a tutto sesto (centro
    v = 0, imposta wc, raggio r) fino a wtop: il semicerchio resta aperto."""
    return _griglia([[(u, v, wc + math.sqrt(max(r * r - v * v, 0.0))), (u, v, wtop)]
                     for v in np.linspace(v0, v1, n + 1)], church)


def _bandiera(u, v0, v1, w0, w1, punta, church: ChurchModel, n=12) -> pv.PolyData:
    """Stendardo in un piano v-w: rettangolo da w0 a w1, con il bordo basso
    a punta (alto punta m) se punta > 0."""
    vc, hw = (v0 + v1) / 2, (v1 - v0) / 2
    return _griglia([[(u, v, w0 + punta * abs(v - vc) / hw), (u, v, w1)] for v in np.linspace(v0, v1, n + 1)], church)


def _disco_su_muro(u, v, w, r, church: ChurchModel, n=24) -> pv.PolyData:
    """Disco verticale sul muro di un fianco (piano u-w, a quota v)."""
    return _griglia([[(u, v, w), (u + r * math.cos(a), v, w + r * math.sin(a))]
                     for a in np.linspace(0, 2 * math.pi, n + 1)], church)


def build_arredi_muri(church: ChurchModel) -> list:
    """Controfacciata e lesene fra le cappelle (IMG_9758): [(mesh, colore)].
    Controfacciata: bussola in muratura col portone di legno ad arco,
    pinnacoli e cupoletta; stendardi rosso e giallo; altarino col fonte
    battesimale (Est); armadio e confessionale di legno (Ovest).
    Lesene: a ogni pilastro dei due fianchi zoccolo di finto marmo scuro,
    fusto bianco, capitello sotto il cornicione, croce di consacrazione e
    una stazione della Via Crucis; il grande crocifisso sul pilastro fra le
    prime due cappelle a destra (Est)."""
    out = []
    add = lambda m, c: out.append((m, _C[c]))
    wh = church.nave_width_m / 2.0
    bw, bd, bh = BUSSOLA_LARGHEZZA_M / 2, BUSSOLA_PROFONDITA_M, BUSSOLA_ALTEZZA_M
    pw, ph = PORTONE_LARGHEZZA_M / 2, PORTONE_ALTEZZA_M
    wi = ph - pw                                   # imposta dell'arco del portone
    we = bh - 0.6                                  # inizio della trabeazione
    # --- bussola: pilastri, riquadri ad arco, archivolto, trabeazione ---
    pil = pw + 0.35                                # filo interno dei pilastri
    for s_ in (-1, 1):
        v0, v1 = sorted((s_ * pil, s_ * bw))
        add(_blocco(0.0, bd, v0, v1, 0.0, we, church), "pietra")
        add(_blocco(bd, bd + 0.05, v0 - 0.03, v1 + 0.03, 0.0, 0.5, church), "zoccolo")          # zoccolo
        vc = s_ * (pil + bw) / 2
        add(_arco_verticale(bd + 0.01, vc - 0.3, vc + 0.3, 0.8, 3.9, church), "pannello")      # riquadro
        add(_blocco(bd, bd + 0.08, *sorted((s_ * (pw + 0.05), s_ * (pil + 0.05))), wi - 0.18, wi, church), "pietra")  # imposta
    add(_lastra_sopra_arco(bd, -pil, pil, wi, pw, we, church), "pietra")                       # sopra la porta, arco aperto
    add(_fascia_arco(bd + 0.03, 0.0, wi, pw + 0.02, pw + 0.32, church), "bianco")               # archivolto
    for s_ in (-1, 1):                                                                           # riquadri nei pennacchi
        add(_blocco(bd + 0.01, bd + 0.02, *sorted((s_ * (pw + 0.45), s_ * (pil - 0.08))), ph - 0.2, we - 0.15, church), "pannello")
    for w0, w1, d in ((we, we + 0.2, 0.05), (we + 0.2, we + 0.4, 0.02), (we + 0.4, bh, 0.15)):  # trabeazione
        add(_blocco(0.0, bd + d, -bw - d, bw + d, w0, w1, church), "pietra" if d != 0.02 else "pannello")
    # piedistalli, piramidi e pomi sopra gli angoli; cupoletta a punta
    for s_ in (-1, 1):
        vc = s_ * (bw - 0.3)
        add(_blocco(bd - 0.6, bd, vc - 0.3, vc + 0.3, bh, bh + 0.5, church), "pietra")
        add(_blocco(bd, bd + 0.01, vc - 0.18, vc + 0.18, bh + 0.1, bh + 0.4, church), "pannello")
        add(_tornio([(bh + 1.85, 0.0), (bh + 0.5, 0.36)], bd - 0.3, vc, church, 4, (math.pi / 4, math.pi / 4 + 2 * math.pi)), "pietra")
        add(_tornio([(bh + 2.03, 0.0), (bh + 1.97, 0.07), (bh + 1.91, 0.0)], bd - 0.3, vc, church, 12), "pietra")
    add(_tornio([(bh + 1.9, 0.0), (bh + 1.6, 0.25), (bh + 1.2, 0.95), (bh + 0.6, 1.45), (bh, 1.6)],
                0.02, 0.0, church, 24, (-math.pi / 2, math.pi / 2)), "pietra")
    # --- portone: stipite, ante a riquadri, traversa, lunetta a raggiera ---
    add(_arco_verticale(bd - 0.12, -pw, pw, 0.0, wi, church), "legno")
    for s_ in (-1, 1):                                                                           # sguanci
        add(_blocco(bd - 0.12, bd, *sorted((s_ * pw, s_ * (pw + 0.02))), 0.0, wi, church), "pietra")
        for w0, w1 in ((0.3, 1.6), (1.8, wi - 0.25)):                                             # riquadri
            add(_blocco(bd - 0.12, bd - 0.09, *sorted((s_ * 0.12, s_ * (pw - 0.12))), w0, w1, church), "legno_pannello")
    add(_blocco(bd - 0.12, bd - 0.08, -0.03, 0.03, 0.0, wi, church), "legno_scuro")              # battuta centrale
    add(_blocco(bd - 0.12, bd - 0.06, -pw, pw, wi - 0.12, wi, church), "legno_pannello")         # traversa
    for k in range(9):                                                                            # raggiera
        a = math.pi * (k + 0.5) / 9
        add(_raggio(bd - 0.11, 0.0, wi, 0.25, pw - 0.05, a, 0.035, church), "legno_scuro")
    add(_fascia_arco(bd - 0.11, 0.0, wi, 0.0, 0.25, church), "legno_pannello")
    # --- stendardi su un'asta: rosso con croci dorate e icona, giallo a punta ---
    for vc, col, punta in ((-2.36, "rosso", False), (2.40, "giallo", True)):
        u0 = bd + 0.12
        add(_blocco(u0 - 0.02, u0 + 0.02, vc - 0.62, vc + 0.62, 4.12, 4.16, church), "oro")      # asta
        for e in (-0.64, 0.64):
            add(_tornio([(4.2, 0.0), (4.14, 0.045), (4.08, 0.0)], u0, vc + e, church, 8), "oro")
        add(_bandiera(u0, vc - 0.5, vc + 0.5, 1.0, 4.1, 0.35 if punta else 0.0, church), col)
        add(_blocco(u0 + 0.005, u0 + 0.015, vc - 0.24, vc + 0.24, 2.95, 3.65, church), "oro")    # icona
        add(_blocco(u0 + 0.015, u0 + 0.02, vc - 0.19, vc + 0.19, 3.0, 3.6, church), "quadro")
        if not punta:
            for cv_, cw in ((-0.3, 3.85), (0.3, 3.85), (-0.3, 2.5), (0.3, 2.5), (-0.3, 1.8), (0.3, 1.8), (0.0, 1.3)):
                add(_blocco(u0 + 0.005, u0 + 0.012, vc + cv_ - 0.07, vc + cv_ + 0.07, cw - 0.015, cw + 0.015, church), "oro")
                add(_blocco(u0 + 0.005, u0 + 0.012, vc + cv_ - 0.015, vc + cv_ + 0.015, cw - 0.07, cw + 0.07, church), "oro")
    # --- battistero (Est): colonne a coppie, trabeazione, nicchie, fonte ---
    vb = -5.1
    add(_blocco(0.0, 0.3, vb - 1.35, vb + 1.35, 0.0, 4.6, church), "fondo_altare")
    add(_arco_verticale(0.31, vb - 0.5, vb + 0.5, 2.1, 3.4, church), "nicchia")                 # nicchia alta
    add(_tornio([(2.35, 0.32), (2.15, 0.25), (2.0, 0.08)], 0.45, vb, church, 16), "marmo_giallo")  # mensola
    add(_tornio([(3.55, 0.06), (3.4, 0.16), (3.0, 0.24), (2.6, 0.27), (2.35, 0.25)], 0.45, vb, church, 16), "avorio")  # statue
    add(_arco_verticale(0.31, vb - 0.42, vb + 0.42, 0.0, 1.4, church), "marmo_scuro")           # nicchia del fonte
    add(_tornio([(1.0, 0.45), (0.92, 0.45), (0.82, 0.34), (0.72, 0.12), (0.25, 0.1), (0.1, 0.22), (0.0, 0.22)],
                0.72, vb, church, 20), "fonte")                                                   # fonte su balaustro
    add(_tornio([(1.42, 0.06), (1.3, 0.2), (1.1, 0.4), (1.0, 0.44)], 0.72, vb, church, 20), "fonte")  # coperchio
    add(_blocco(0.70, 0.74, vb - 0.02, vb + 0.02, 1.42, 1.75, church), "oro")
    add(_blocco(0.70, 0.74, vb - 0.1, vb + 0.1, 1.6, 1.64, church), "oro")
    for v in (vb - 1.05, vb - 0.7, vb + 0.7, vb + 1.05):                                           # colonne
        add(_blocco(0.3, 0.66, v - 0.18, v + 0.18, 0.0, 1.0, church), "marmo_scuro")
        add(_blocco(0.28, 0.68, v - 0.2, v + 0.2, 0.95, 1.05, church), "marmo_scuro")
        add(_tornio([(3.85, 0.12), (2.4, 0.145), (1.05, 0.15)], 0.48, v, church, 14), "marmo_giallo")
        add(_blocco(0.32, 0.64, v - 0.17, v + 0.17, 3.85, 4.05, church), "marmo_giallo")         # capitello
    add(_blocco(0.0, 0.7, vb - 1.3, vb + 1.3, 4.05, 4.2, church), "marmo_giallo")               # architrave
    add(_blocco(0.0, 0.66, vb - 1.25, vb + 1.25, 4.2, 4.42, church), "nicchia")                 # fregio
    add(_blocco(0.0, 0.8, vb - 1.4, vb + 1.4, 4.42, 4.6, church), "marmo_giallo")               # cornice
    add(_blocco(0.1, 0.35, vb - 0.45, vb + 0.45, 4.6, 5.1, church), "marmo_giallo")             # cimasa
    add(_blocco(0.2, 0.26, vb - 0.04, vb + 0.04, 5.1, 5.8, church), "marmo_giallo")
    add(_blocco(0.2, 0.26, vb - 0.2, vb + 0.2, 5.5, 5.58, church), "marmo_giallo")
    for k in range(9):                                                                             # ringhiera
        v = vb - 1.3 + 2.6 * k / 8
        add(_blocco(1.2, 1.23, v - 0.015, v + 0.015, 0.0, 0.85, church), "nero")
    for w in (0.1, 0.82):
        add(_blocco(1.19, 1.24, vb - 1.32, vb + 1.32, w, w + 0.04, church), "nero")
    # --- armadio a due ante con cornice (Ovest) ---
    add(_blocco(0.0, 0.7, 2.95, 4.85, 0.0, 3.6, church), "legno")
    add(_blocco(0.0, 0.78, 2.9, 4.9, 3.6, 3.75, church), "legno_scuro")
    for v0, v1 in ((3.05, 3.85), (3.95, 4.75)):
        for w0, w1 in ((0.2, 1.6), (1.8, 3.4)):
            add(_blocco(0.7, 0.73, v0, v1, w0, w1, church), "legno_pannello")
    # --- confessionale: corpo centrale col frontone curvo e la grata, due ali ---
    add(_blocco(0.0, 0.9, 5.35, 6.2, 0.0, 2.6, church), "legno_chiaro")
    add(_arco_verticale(0.9, 5.35, 6.2, 2.6, 2.6, church), "legno_chiaro")                     # frontone (fronte)
    add(_blocco(0.0, 0.9, 5.4, 6.15, 2.6, 2.75, church), "legno_chiaro")
    add(_blocco(0.9, 0.93, 5.5, 6.05, 1.3, 2.25, church), "nero")                                # grata
    for k in range(5):
        v = 5.5 + 0.55 * (k + 0.5) / 5
        add(_blocco(0.93, 0.95, v - 0.01, v + 0.01, 1.3, 2.25, church), "legno_chiaro")
    for v0, v1 in ((4.95, 5.35), (6.2, 6.6)):
        add(_blocco(0.0, 0.8, v0, v1, 0.0, 2.2, church), "legno")
        add(_blocco(0.0, 0.85, v0, v1, 2.2, 2.3, church), "legno_scuro")
    add(_blocco(0.42, 0.48, 5.745, 5.805, 3.05, 3.5, church), "legno_chiaro")                     # croce
    add(_blocco(0.42, 0.48, 5.65, 5.9, 3.3, 3.35, church), "legno_chiaro")
    lw, sp, z = LESENA_LARGHEZZA_M / 2, LESENA_SPORGENZA_M, LESENA_ZOCCOLO_M
    us = church.chapel_u_positions()
    campata = us[1] - us[0]
    pilastri = [us[0] - campata / 2] + [u + campata / 2 for u in us]
    stazione = 0
    for k, up in enumerate(pilastri):
        for lato in (1.0, -1.0):
            muro = lato * (wh - 0.16)                     # davanti ai pannelli delle foto (wh - 0.15)
            dentro = lambda d: lato * (wh - 0.16 - d)
            add(_blocco(up - lw - 0.08, up + lw + 0.08, *sorted((muro, dentro(sp + 0.08))), 0.0, z, church), "marmo_scuro")
            add(_blocco(up - lw, up + lw, *sorted((muro, dentro(sp))), z, _CB - 0.35, church), "bianco")
            add(_blocco(up - lw - 0.1, up + lw + 0.1, *sorted((muro, dentro(sp + 0.1))), _CB - 0.35, _CB, church), "bianco")
            add(_disco_su_muro(up, dentro(sp + 0.01), CROCE_CONSACRAZIONE_M, 0.27, church), "croce")
            vc, c = dentro(sp + 0.02), CROCE_CONSACRAZIONE_M
            add(_blocco(up - 0.03, up + 0.03, *sorted((vc, dentro(sp + 0.03))), c - 0.2, c + 0.2, church), "nero")
            add(_blocco(up - 0.2, up + 0.2, *sorted((vc, dentro(sp + 0.03))), c - 0.03, c + 0.03, church), "nero")
            if stazione < 14:
                add(_blocco(up - 0.19, up + 0.19, *sorted((dentro(sp), dentro(sp + 0.04))), 1.75, 2.25, church), "legno")
                add(_blocco(up - 0.15, up + 0.15, *sorted((dentro(sp + 0.04), dentro(sp + 0.05))), 1.8, 2.2, church), "quadro")
                stazione += 1
            if lato < 0 and k == 1:
                add(_blocco(up - 0.06, up + 0.06, *sorted((dentro(sp), dentro(sp + 0.1))), 5.8, 8.2, church), "legno")
                add(_blocco(up - 0.6, up + 0.6, *sorted((dentro(sp), dentro(sp + 0.1))), 7.45, 7.57, church), "legno")
                add(_blocco(up - 0.1, up + 0.1, *sorted((dentro(sp + 0.1), dentro(sp + 0.22))), 6.3, 7.5, church), "avorio")
                add(_blocco(up - 0.55, up + 0.55, *sorted((dentro(sp + 0.1), dentro(sp + 0.18))), 7.38, 7.5, church), "avorio")
    return out


def build_walls(inner_loop_uv, church: ChurchModel, thickness: float = WALL_THICKNESS_M, height: float = WALL_HEIGHT_M):
    outer_loop_uv = offset_loop_outward(inner_loop_uv, thickness)
    outer_band = vertical_band(outer_loop_uv, 0.0, height, church)
    inner_band = vertical_band(inner_loop_uv, 0.0, height, church)
    top_ring = ring_cap(inner_loop_uv, outer_loop_uv, height, church)
    bottom_ring = ring_cap(inner_loop_uv, outer_loop_uv, 0.0, church)
    mesh = outer_band.merge(inner_band).merge(top_ring).merge(bottom_ring)
    return mesh, outer_loop_uv


def build_roof(outer_loop_uv, church: ChurchModel, wall_height: float, ridge_rise: float = ROOF_RIDGE_RISE_M) -> pv.PolyData:
    """
    Tetto a CAPANNA (due falde rettangolari + due frontoni
    triangolari alle estremita'), con un vero COLMO LINEARE lungo
    l'asse u (a v=0, dalla facciata alla rientranza absidale) -
    NON piu' un ventaglio da un punto centrale a tutti gli angoli
    del rettangolo (che produceva una piramide a 4 falde invece di
    un tetto a capanna, segnalato dall'utente: "e' un tetto
    rettangolare e non a spiovente" - cioe' doveva avere due sole
    falde inclinate, non quattro spicchi piramidali).
    """
    u_min = min(p[0] for p in outer_loop_uv)
    u_max = max(p[0] for p in outer_loop_uv)
    v_min = min(p[1] for p in outer_loop_uv)
    v_max = max(p[1] for p in outer_loop_uv)
    ridge_h = wall_height + ridge_rise

    # 4 angoli alla gronda (altezza wall_height) + 2 punti di colmo (v=0)
    eave_00 = (u_min, v_max, wall_height)   # facciata, lato Ovest
    eave_01 = (u_min, v_min, wall_height)   # facciata, lato Est
    eave_10 = (u_max, v_max, wall_height)   # rientranza absidale, lato Ovest
    eave_11 = (u_max, v_min, wall_height)   # rientranza absidale, lato Est
    ridge_0 = (u_min, 0.0, ridge_h)         # colmo, lato facciata
    ridge_1 = (u_max, 0.0, ridge_h)         # colmo, lato abside

    pts_uvw = [eave_00, eave_01, eave_10, eave_11, ridge_0, ridge_1]
    pts = _pts_local_to_world(church, pts_uvw)
    # indici: 0=eave_00 1=eave_01 2=eave_10 3=eave_11 4=ridge_0 5=ridge_1
    faces = [
        4, 0, 2, 5, 4,   # falda Ovest (rettangolo: eave_00-eave_10-ridge_1-ridge_0)
        4, 1, 4, 5, 3,   # falda Est (rettangolo: eave_01-ridge_0-ridge_1-eave_11)
        3, 0, 4, 1,      # frontone triangolare lato facciata
        3, 2, 3, 5,      # frontone triangolare lato abside
    ]
    return pv.PolyData(pts, faces=np.array(faces))


def build_chapel_wall_structures(
    church: ChurchModel,
    eave_height: float = CHAPEL_ROOF_HEIGHT_M,
    pitch_rise: float = CHAPEL_ROOF_PITCH_RISE_M,
) -> pv.PolyData:
    """
    Muro BASSO + tetto delle nicchie delle cappelle (8 strutture
    separate, una per nicchia), che sostituiscono la porzione di muro
    ALTO in quelle zone: il "nucleo" navata+abside (vedi
    ChurchModel.core_outline_local()) e' costruito senza le nicchie
    sporgenti, e per ciascuna delle 8 nicchie si costruisce qui una
    struttura a se' stante che si ferma all'altezza del tetto basso
    delle cappelle, invece di proseguire fino a WALL_HEIGHT_M come nel
    resto dell'edificio - la parte alta del muro non deve piu'
    "attraversare" il tetto basso, come accadeva prima quando le
    nicchie erano incluse nel muro alto unico.

    Ciascuna nicchia e' una superficie singola (senza spessore, a
    differenza del muro principale che ha spessore reale) per
    semplicita' - dettaglio secondario dell'edificio. Il tappo
    superiore e' inclinato (a falda unica): eave_height [magenta,
    Elevation Sud, 9.64 m] sul bordo esterno (v=Wh+dd, il filo della
    nicchia), eave_height+pitch_rise [9.64+1.31=10.95 m] sul bordo
    interno (v=Wh, dove incontra il muro alto della navata).

    Fra una nicchia e la successiva NON serve un pannello di
    collegamento aggiuntivo: il muro "nucleo" della navata
    (ChurchModel.nave_only_outline_local(), un semplice rettangolo
    continuo da u=0 a u=nave_length_m a v=+-Wh, altezza piena) copre
    gia' con continuita' tutto lo spazio fra una nicchia e l'altra -
    un pannello aggiuntivo nello stesso identico piano (v=Wh) causava
    z-fighting col muro nucleo, che a certi angoli di vista faceva
    sparire ENTRAMBE le superfici, mostrando un varco visivo (bug
    segnalato dall'utente e verificato: rimuovendo del tutto le
    nicchie e lasciando solo il muro nucleo, la copertura risultava
    perfettamente continua - la geometria del muro non aveva mai
    davvero un buco).
    """
    dw = CHAPEL_PROJECTION_WIDTH_M / 2.0
    dd = CHAPEL_PROJECTION_DEPTH_M
    Wh = church.nave_width_m / 2.0
    chapel_us = church.chapel_u_positions()
    h_inner = eave_height + pitch_rise
    h_outer = eave_height

    def one_niche(u_center, v_wall, v_far, mirror):
        # contorno della nicchia in pianta: ritorno - fondo - ritorno.
        # Il lato "ritorno" (v_wall) e' esteso di OVERLAP_M oltre il
        # filo del muro nucleo (invece di fermarsi esattamente li'),
        # cosi' le due mesh si compenetrano leggermente invece di
        # toccarsi su un piano/bordo coincidente - elimina qualsiasi
        # possibile z-fighting/varco visivo dovuto a precisione
        # numerica o angolo di vista, indipendentemente dalla causa
        # esatta (segnalato dall'utente come varco persistente).
        # Il muro nucleo ha spessore reale e si estende da v=Wh verso
        # l'ESTERNO (v crescente per Ovest, decrescente per Est) - per
        # sovrapporsi davvero al suo volume solido (non solo sfiorarne
        # il bordo) l'estensione deve andare nella STESSA direzione.
        OVERLAP_M = 0.05
        v_wall_ext = v_wall + OVERLAP_M if not mirror else v_wall - OVERLAP_M
        loop = [
            (u_center - dw, v_wall_ext), (u_center - dw, v_far),
            (u_center + dw, v_far), (u_center + dw, v_wall_ext),
        ]
        heights = [h_inner, h_outer, h_outer, h_inner]
        n = len(loop)
        pts_uvw = [(u, v, 0.0) for (u, v) in loop] + [(u, v, h) for (u, v), h in zip(loop, heights)]
        pts = _pts_local_to_world(church, pts_uvw)
        wall_faces = []
        for i in range(n):
            j = (i + 1) % n
            quad = [i, j, n + j, n + i] if not mirror else [n + i, n + j, j, i]
            wall_faces += [4, *quad]
        roof_faces = [4, n, n + 1, n + 2, n + 3] if not mirror else [4, n + 3, n + 2, n + 1, n]
        faces = wall_faces + roof_faces
        return pv.PolyData(pts, faces=np.array(faces))

    parts = []
    for u in chapel_us:
        parts.append(one_niche(u, Wh, Wh + dd, mirror=False))       # Ovest
        parts.append(one_niche(u, -Wh, -Wh - dd, mirror=True))      # Est

    result = parts[0]
    for p in parts[1:]:
        result = result.merge(p)
    return result


def build_chapel_piers(
    church: ChurchModel,
    eave_height: float = CHAPEL_ROOF_HEIGHT_M,
    pitch_rise: float = CHAPEL_ROOF_PITCH_RISE_M,
) -> pv.PolyData:
    """
    Riempimenti fra una nicchia di cappella e la successiva (e prima
    della prima/dopo l'ultima, fino alla rientranza absidale) - dal
    pavimento fino al TETTO della cappella (non piu' un tappo piatto
    alla gronda: segue lo stesso profilo inclinato delle nicchie
    stesse, da eave_height sul filo esterno a eave_height+pitch_rise
    sul filo interno, dove incontra il muro alto della navata).
    Sporgono alla STESSA profondita' delle nicchie (fino a
    v=Wh+CHAPEL_PROJECTION_DEPTH_M): l'utente ha chiarito che il
    problema non era un varco/buco nella mesh, ma una RIENTRANZA
    visibile dall'esterno (il muro nucleo, corretto ma arretrato
    rispetto alle cappelle sporgenti, appariva come un incavo).
    TRASPARENTI come i muri della chiesa (non piu' quasi opachi) - vedi
    opacita' in viewer_3d.py.
    """
    L = church.nave_length_m
    Wh = church.nave_width_m / 2.0
    dd = CHAPEL_PROJECTION_DEPTH_M
    margin = CHAPEL_ROW_MARGIN_M
    chapel_us = church.chapel_u_positions()
    dw = CHAPEL_PROJECTION_WIDTH_M / 2.0
    h_inner = eave_height + pitch_rise   # sul filo v=Wh (muro navata)
    h_outer = eave_height                # sul filo v=Wh+dd (gronda esterna)

    # confini dei tratti da riempire: dal margine alla prima cappella,
    # fra ciascuna coppia di cappelle successive, e dall'ultima al
    # margine opposto (verso l'abside) - 5 tratti in tutto per lato.
    edges = [margin]
    for u in chapel_us:
        edges.append(u - dw)
        edges.append(u + dw)
    edges.append(L - margin)
    segments = [(edges[i], edges[i + 1]) for i in range(0, len(edges) - 1, 2)]

    def fill_box(u0, u1, v_near, v_far, h_near, h_far):
        # scatola piena: fronte (v_far), due fianchi, tappo superiore inclinato
        loop = [(u0, v_near), (u0, v_far), (u1, v_far), (u1, v_near)]
        heights = [h_near, h_far, h_far, h_near]
        n = len(loop)
        pts_uvw = [(u, v, 0.0) for (u, v) in loop] + [(u, v, h) for (u, v), h in zip(loop, heights)]
        pts = _pts_local_to_world(church, pts_uvw)
        faces = []
        for i in range(n):
            j = (i + 1) % n
            faces += [4, i, j, n + j, n + i]
        faces += [4, n, n + 1, n + 2, n + 3]  # tappo superiore (ora inclinato, non piatto)
        return pv.PolyData(pts, faces=np.array(faces))

    parts = []
    for u0, u1 in segments:
        parts.append(fill_box(u0, u1, Wh, Wh + dd, h_inner, h_outer))
        parts.append(fill_box(u0, u1, -Wh, -Wh - dd, h_inner, h_outer))

    result = parts[0]
    for p in parts[1:]:
        result = result.merge(p)
    return result


def build_apse_wall_structure(
    church: ChurchModel,
    wall_height: float = APSE_EXTERNAL_HEIGHT_M,
    ridge_rise: float = APSE_ROOF_RIDGE_RISE_M,
) -> pv.PolyData:
    """
    Muro esterno + tetto dell'abside, separati dal "nucleo" navata
    (che ora si ferma al filo di rientranza absidale, vedi
    ChurchModel.nave_only_outline_local()).

    CORRETTO sulla base di una FOTO REALE del tetto dell'abside vista
    da dietro la chiesa (Elevation Nord - chevet): e' un classico
    tetto a PADIGLIONE SIMMETRICO ("cono"/piramide a base
    pentagonale) - tutte e 5 le falde salgono con la STESSA pendenza
    da un muro perimetrale ad altezza COSTANTE (wall_height, 15.69 m)
    fino a un UNICO colmo centrale (wall_height+ridge_rise, 19.85 m).

    Costruito come UN UNICO PolyData con un solo array di punti
    condiviso fra muro e tetto (non piu' pezzi separati uniti con
    merge()): un tentativo precedente teneva muro e tetto come oggetti
    distinti con punti duplicati alla stessa posizione fisica (il
    bordo superiore del muro e il bordo del ventaglio del tetto) - con
    rendering OPACO la differenza non si notava, ma con la trasparenza
    reale usata dall'app (opacita' 0.4) minuscole discrepanze di
    virgola mobile fra i due calcoli separati lasciavano una fessura
    visibile (segnalata dall'utente con screenshot: si vedeva
    attraverso il tetto fino alla foto interna). Include anche i
    pannelli di raccordo verticali ai due angoli della "bocca" (dove
    l'abside tocca il campanile), che risolvevano un problema
    separato di dislivello con l'altezza del campanile.
    """
    apse_loop = church.apse_vertices()  # 6 punti (5 lati) del pentagono, gia' locali (u,v)

    Wh = church.nave_width_m / 2.0
    L = church.nave_length_m
    loop = [(L, Wh)] + apse_loop + [(L, -Wh)]
    n = len(loop)  # 8 punti

    cu = sum(p[0] for p in apse_loop) / len(apse_loop)
    cv = sum(p[1] for p in apse_loop) / len(apse_loop)
    ridge_h = wall_height + ridge_rise

    OVERLAP_M = 0.05
    fill_h = TOWER_BODY_HEIGHT_M
    mouth_w_u, mouth_w_v = loop[0]
    mouth_e_u, mouth_e_v = loop[-1]
    pent0_u, pent0_v = apse_loop[0]   # primo vertice pentagono (falda "1")
    pent5_u, pent5_v = apse_loop[5]   # ultimo vertice pentagono (falda "5")

    # Punti: 0..7 = loop a z=0 (base muro) | 8..15 = loop a wall_height
    # (gronda, condiviso da muro E tetto) | 16 = colmo | poi gli
    # angoli dei due PANNELLI RETTANGOLARI (falde 1 e 5) che
    # collegano il campanile al resto del tetto.
    all_pts_local = (
        [(u, v, 0.0) for (u, v) in loop]
        + [(u, v, wall_height) for (u, v) in loop]
        + [(cu, cv, ridge_h)]
        # pannello Ovest (falda 1): rettangolo dalla bocca al primo
        # vertice del pentagono, dal filo del muro (wall_height) fino
        # all'altezza del campanile (fill_h) - sovrapposto di 5 cm
        # oltre la bocca per un raccordo sicuro col campanile.
        + [(mouth_w_u - OVERLAP_M, mouth_w_v, wall_height), (pent0_u, pent0_v, wall_height),
           (pent0_u, pent0_v, fill_h), (mouth_w_u - OVERLAP_M, mouth_w_v, fill_h)]
        # pannello Est (falda 5), speculare
        + [(mouth_e_u - OVERLAP_M, mouth_e_v, wall_height), (pent5_u, pent5_v, wall_height),
           (pent5_u, pent5_v, fill_h), (mouth_e_u - OVERLAP_M, mouth_e_v, fill_h)]
    )
    pts = _pts_local_to_world(church, all_pts_local)
    IDX_RIDGE = 2 * n
    IDX_FW0, IDX_FW1, IDX_FW2, IDX_FW3 = 2 * n + 1, 2 * n + 2, 2 * n + 3, 2 * n + 4
    IDX_FE0, IDX_FE1, IDX_FE2, IDX_FE3 = 2 * n + 5, 2 * n + 6, 2 * n + 7, 2 * n + 8

    faces = []
    # muro (aperto verso la bocca: non chiude l'ultimo lato)
    for i in range(n - 1):
        j = i + 1
        faces += [4, i, j, n + j, n + i]
    # tetto: SEPARATO in due parti, non piu' un unico ventaglio su
    # tutti gli 8 punti del loop (bug reale trovato: gli angoli dei
    # punti della bocca rispetto al centroide NON sono monotoni -
    # rompono la condizione "a stella" necessaria per un ventaglio
    # valido, producendo triangoli mal orientati/invisibili da
    # backface culling proprio nelle due falde 1 e 5, corrispondenti
    # esattamente al varco "molto largo" segnalato dall'utente,
    # sempre nello stesso punto, indipendente dalle foto).
    #
    # 1) ventaglio SOLO sui 6 vertici del vero pentagono (verificato
    #    a stella valida, angoli monotoni rispetto al centroide) - 5
    #    triangoli, uno per lato del pentagono. Verso di avvolgimento
    #    verificato con backface culling attivo (il verso originario
    #    risultava invertito, causa reale del difetto "sempre li',
    #    molto largo, corrisponde a due parti del tetto" - le normali
    #    del ventaglio principale puntavano verso l'INTERNO invece che
    #    verso l'esterno, fin dal primissimo tentativo a padiglione).
    for i in range(1, n - 2):
        j = i + 1
        faces += [3, IDX_RIDGE, n + j, n + i]
    # 2) due triangoli espliciti per le sezioni di ritorno (bocca ->
    #    primo/ultimo vertice pentagono), stesso verso corretto.
    faces += [3, IDX_RIDGE, n + 0, n + 1]           # bocca Ovest -> primo vertice
    faces += [3, IDX_RIDGE, n + (n - 2), n + (n - 1)]  # ultimo vertice -> bocca Est
    # 3) falda verso la navata (dal colmo al lato del pentagono lungo la
    #    bocca, fra primo e ultimo vertice): senza, dalla pianta il tetto
    #    dell'abside restava aperto con un buco triangolare.
    faces += [3, IDX_RIDGE, n + 1, n + (n - 2)]
    # pannelli RETTANGOLARI (falde 1 e 5) che collegano il campanile
    # al resto del tetto - sostituiscono le sottili strisce verticali
    # di un tentativo precedente (rivelatesi insufficienti a coprire
    # davvero il varco, segnalato dall'utente con screenshot: "riempi
    # con due tetti rettangolari per i pannelli 1 e 5").
    faces += [4, IDX_FW3, IDX_FW2, IDX_FW1, IDX_FW0]
    faces += [4, IDX_FE3, IDX_FE2, IDX_FE1, IDX_FE0]

    return pv.PolyData(pts, faces=np.array(faces))

def _faccia_vetrata(outline, du, dv, d, verso, church: ChurchModel) -> pv.PolyData:
    """Faccia col contorno della vetrata a distanza d verso l'esterno dal
    filo interno del muro, con la normale verso `verso` (+1 fuori, -1
    dentro): disegnata solo dal davanti, si vede solo da quel lato."""
    pts = [(u + du * d, v + dv * d, w) for (u, v, w) in outline]
    P = _pts_local_to_world(church, pts)
    n = np.cross(P[1] - P[0], P[2] - P[0])
    fuori = np.array(church.local_to_enu(du, dv, 0.0)) - np.array(church.local_to_enu(0.0, 0.0, 0.0))
    if np.dot(n, fuori) * verso < 0:
        P = P[::-1]
    return pv.PolyData(np.array(P), faces=np.array([len(P), *range(len(P))]))


def build_window_solid(win: Window, church: ChurchModel, wall_thickness: float = WALL_THICKNESS_M,
                        recess_from_exterior: float = 0.0) -> pv.PolyData:
    """
    Vetrata: due facce sottili col contorno della finestra, una appena
    dentro il filo interno del muro rivolta verso l'interno, una sul filo
    esterno rivolta verso l'esterno. Ciascuna si disegna solo dal davanti
    (i viewer scartano il retro): da dentro si vede solo quella interna,
    coperta esattamente dalla foto della vetrata, e non piu' quella
    esterna che, 70 cm dietro e vista attraverso il muro semitrasparente,
    sembrava spostata accanto alla foto. Le macchie di sole partono dal
    contorno sul filo interno (wall_projection.py): non cambiano.
    recess_from_exterior: arretramento di tutto verso l'interno (0 = come il muro).
    """
    outline = win.local_outline()  # [(u,v,w), ...] sul filo interno
    du, dv = local_outward_dir_uv(church, win.wall_azimuth_deg)
    r = recess_from_exterior
    return _faccia_vetrata(outline, du, dv, -0.02 - r, -1, church).merge(
        _faccia_vetrata(outline, du, dv, wall_thickness + 0.02 - r, 1, church))


def build_tower(
    church: ChurchModel,
    u_center: float = TOWER_U_CENTER_M,
    v_center: float = TOWER_V_CENTER_M,
    width_u: float = TOWER_WIDTH_U_M,
    width_v: float = TOWER_WIDTH_V_M,
    body_height: float = TOWER_BODY_HEIGHT_M,
    spire_height: float = TOWER_SPIRE_HEIGHT_M,
) -> pv.PolyData:
    """
    Campanile semplificato: corpo a base rettangolare (pianta
    TOWER_WIDTH_U_M x TOWER_WIDTH_V_M) dal suolo fino a body_height,
    sormontato da una guglia piramidale a base quadrata/rettangolare
    che sale per altri spire_height metri fino alla punta. Vedi
    church_geometry.py per la provenienza (misurata/stimata) di
    ciascuna quota.
    """
    hu, hv = width_u / 2.0, width_v / 2.0
    footprint = [
        (u_center - hu, v_center - hv),
        (u_center + hu, v_center - hv),
        (u_center + hu, v_center + hv),
        (u_center - hu, v_center + hv),
    ]

    # corpo: muro pieno (semplificato, non cavo) dal suolo alla gronda
    outer_band = vertical_band(footprint, 0.0, body_height, church)
    bottom_cap = flat_polygon(footprint, 0.0, church, reverse=True)
    top_cap_body = flat_polygon(footprint, body_height, church, reverse=False)

    # guglia: piramide a base rettangolare, apice sopra il centro
    apex_uvw = (u_center, v_center, body_height + spire_height)
    apex_world = church.local_to_enu(*apex_uvw)
    base_world = _pts_local_to_world(church, [(u, v, body_height) for (u, v) in footprint])
    n = len(footprint)
    spire_positions = np.vstack([apex_world, base_world])
    spire_faces = []
    for i in range(n):
        j = (i + 1) % n
        spire_faces.append([3, 0, 1 + i, 1 + j])
    spire_faces = np.hstack(spire_faces)
    spire = pv.PolyData(spire_positions, faces=spire_faces)

    return outer_band.merge(bottom_cap).merge(top_cap_body).merge(spire)


def build_narthex_vault(
    church: ChurchModel,
    width: float = NARTHEX_WIDTH_M,
    depth: float = NARTHEX_DEPTH_M,
    height_at_wall: float = NARTHEX_HEIGHT_AT_WALL_M,
    height_at_edge: float = NARTHEX_HEIGHT_AT_EDGE_M,
    n_segments: int = 10,
) -> pv.PolyData:
    """
    Nartece/vestibolo coperto all'ingresso: struttura SOLIDA e OPACA
    (non lascia passare luce) attaccata all'interno del muro di
    facciata, sopra il portale. Soffitto a profilo curvo (approssimato
    con un quarto di coseno fra i due punti quotati, vedi
    church_geometry.py), largo `width` (centrato sull'asse), profondo
    `depth` dal muro. Chiuso anche sui due fianchi per essere un
    solido vero e proprio che blocca la luce, non solo un guscio.
    """
    hv = width / 2.0
    delta_h = height_at_wall - height_at_edge

    # profilo del soffitto (u, w) - quarto di coseno da (0,height_at_wall) a (depth,height_at_edge)
    profile = []
    for i in range(n_segments + 1):
        t = i / n_segments
        u = depth * t
        w = height_at_edge + delta_h * math.cos(math.pi / 2.0 * t)
        profile.append((u, w))

    n = len(profile)

    # soffitto: superficie rigata fra i due fianchi (v=+hv e v=-hv), seguendo il profilo
    ceiling_pts_uvw = []
    for (u, w) in profile:
        ceiling_pts_uvw.append((u, hv, w))
    for (u, w) in profile:
        ceiling_pts_uvw.append((u, -hv, w))
    ceiling_pts = _pts_local_to_world(church, ceiling_pts_uvw)
    ceiling_faces = []
    for i in range(n - 1):
        j = i + 1
        ceiling_faces += [4, i, j, n + j, n + i]
    ceiling = pv.PolyData(ceiling_pts, faces=np.array(ceiling_faces))

    # fianchi (a v=+hv e v=-hv): riempiono il profilo curvo fino al pavimento, chiudendo il solido
    def side_wall(v, reverse):
        pts_uvw = [(u, v, 0.0) for (u, w) in profile] + [(u, v, w) for (u, w) in profile]
        pts = _pts_local_to_world(church, pts_uvw)
        faces = []
        for i in range(n - 1):
            j = i + 1
            quad = [i, j, n + j, n + i] if not reverse else [n + i, n + j, j, i]
            faces += [4] + quad
        return pv.PolyData(pts, faces=np.array(faces))

    side_pos = side_wall(hv, reverse=False)
    side_neg = side_wall(-hv, reverse=True)

    # parete di fondo (al bordo esterno, u=depth): chiude il solido verso la navata
    u_far, w_far = profile[-1]
    back_pts_uvw = [(u_far, hv, 0.0), (u_far, -hv, 0.0), (u_far, -hv, w_far), (u_far, hv, w_far)]
    back_pts = _pts_local_to_world(church, back_pts_uvw)
    back_wall = pv.PolyData(back_pts, faces=np.array([4, 0, 1, 2, 3]))

    return ceiling.merge(side_pos).merge(side_neg).merge(back_wall)


def build_all(church: ChurchModel, wall_height: float = WALL_HEIGHT_M):
    """Costruisce tutte le mesh solide dell'edificio.

    Ritorna un dict:
      floor, walls, roof, chapel_walls, apse_structure, tower  -> pv.PolyData singole
      windows                                                  -> {nome_vetrata: pv.PolyData}

    NOTA: il muro ALTO (walls) e il tetto principale (roof) sono
    costruiti sul SOLO rettangolo della navata (ChurchModel.
    nave_only_outline_local()) - SENZA le nicchie delle cappelle NE'
    il pentagono absidale. Le nicchie hanno un proprio muro BASSO +
    tetto separato (chapel_walls), e l'abside ha un proprio muro +
    tetto separato ad altezza diversa (apse_structure, MISURATA
    separatamente - vedi APSE_EXTERNAL_HEIGHT_M in church_geometry.py).
    Il PAVIMENTO usa invece il contorno completo (con nicchie e
    abside), dato che lo spazio interno si estende davvero li'.
    """
    inner_loop_full = church.floor_outline_local()[:-1]      # con nicchie+abside, per il pavimento
    inner_loop_nave = church.nave_only_outline_local()[:-1]  # solo navata, per muro alto + tetto

    floor = build_floor(inner_loop_full, church).merge(build_gradini(church))
    walls, outer_loop = build_walls(inner_loop_nave, church, height=wall_height)
    roof = build_roof(outer_loop, church, wall_height)
    chapel_walls = build_chapel_wall_structures(church)
    chapel_piers = build_chapel_piers(church)
    apse_structure = build_apse_wall_structure(church)
    # NOTA: CHAPEL_WINDOW_RECESS_M (1.31 m) non e' piu' applicato: le
    # vetrate delle cappelle sono tornate sul muro navata (v=Wh, vedi
    # church_geometry.py) per risolvere il conflitto con l'altezza del
    # tetto basso delle cappelle. Un arretramento di 1.31 m da quella
    # posizione (spessore muro solo 0.7 m) spingerebbe la vetrata
    # dentro lo spazio aperto della navata - non ha piu' un'interpretazione
    # fisica valida in questa posizione. Da riconsiderare se necessario.
    windows = {w.name: build_window_solid(w, church) for w in church.windows}
    tower = build_tower(church)
    narthex = build_narthex_vault(church)

    altari_marmo, altari_tovaglia = build_altari(church)
    organo_legno, organo_zoccolo = build_organo(church)
    oggetti = build_oggetti_altare(church)
    return {"banchi": build_banchi(church), "balaustra": build_balaustra(church),
            "riscaldamento": build_riscaldamento(church), "pulpito": build_pulpito(church),
            **{f"altare_{k}": m for k, m in oggetti.items()},
            "cornicione": build_cornicione(church), "altari_cappelle": build_altari_cappelle(church),
            **dict(zip(("volta_abside", "arco_trionfale"), build_volta_abside(church))),
            "volta_navata": build_volta_navata(church), "arredi_muri": build_arredi_muri(church),
            **{f"lampadario_{k}": m for k, m in build_lampadario(church).items()},
            "organo_legno": organo_legno, "organo_zoccolo": organo_zoccolo, "altari_marmo": altari_marmo, "altari_tovaglia": altari_tovaglia,
            "floor": floor, "walls": walls, "roof": roof, "chapel_walls": chapel_walls,
            "chapel_piers": chapel_piers,
            "apse_structure": apse_structure, "windows": windows, "tower": tower, "narthex": narthex}
