"""
wall_projection.py
-------------------
Estende la proiezione della luce solare: quando il raggio attraverso
una vetrata NON raggiunge il pavimento entro il perimetro
dell'edificio (perche' l'incidenza e' troppo radente), invece di
scartare quel tratto la macchia di luce viene disegnata sulla PARETE
VERTICALE INTERNA che il raggio incontra per prima - esattamente come
un fascio di torcia che, se troppo inclinato, illumina la parete di
fondo invece del pavimento.

Principio geometrico
---------------------
Per un punto P=(u,v,w) del contorno della vetrata (coordinate locali
dell'edificio) e una direzione di propagazione p=(pu,pv,pw) (con
pw<0, il raggio scende), il raggio e' P + t*p, t>=0. Due famiglie di
superfici possono fermarlo:

  - il PAVIMENTO (w=0):            t_floor = -w / pw
  - le PARETI interne (verticali, una per ogni lato del perimetro
    `church.floor_outline_local()`, alte WALL_HEIGHT_M): per ciascun
    segmento di parete si risolve l'intersezione fra la proiezione in
    pianta del raggio (una semiretta da (u,v) in direzione (pu,pv)) e
    il segmento stesso; se l'intersezione cade nel tratto utile del
    segmento E l'altezza del raggio in quel punto e' fra 0 e
    WALL_HEIGHT_M, e' un possibile "colpo".

Vince il t piu' piccolo positivo (la prima superficie incontrata).

Per gestire correttamente vetrate la cui macchia cade IN PARTE sul
pavimento e IN PARTE su una parete (il caso piu' comune e piu'
interessante: il raggio "scavalca" lo spigolo pavimento-parete), il
contorno della vetrata viene prima infittito con punti aggiuntivi
lungo ogni lato, poi si cammina lungo il contorno infittito
raggruppando i punti consecutivi che cadono sulla STESSA superficie
in poligoni separati (uno per il pavimento, uno per ciascuna parete
coinvolta), condividendo i punti di passaggio fra un gruppo e il
successivo cosi' che i poligoni risultanti si accostino senza
lasciare un vuoto visibile nello spigolo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from church_geometry import (
    banchi_scatole,
    ChurchModel, WALL_HEIGHT_M, NAVE_WIDTH_M, NAVE_LENGTH_M, APSE_RECESS_M,
    CHAPEL_ARCH_RADIUS_M, CHAPEL_ARCH_SPRING_M, CHAPEL_PROJECTION_WIDTH_M,
    CHAPEL_ROOF_HEIGHT_M, CHAPEL_ROOF_PITCH_RISE_M, CHAPEL_PROJECTION_DEPTH_M,
    APSE_EXTERNAL_HEIGHT_M, quota_pavimento,
)
from solar_position import SolarPosition, sun_vector_enu

# Le macchie di luce sulle pareti si disegnano staccate dal filo del muro
# di tanto verso l'interno, davanti alle foto appoggiate alle pareti.
STACCO_PARETE_M = 0.2

EDGE_SUBDIVISIONS = 6  # punti aggiuntivi per lato del contorno della vetrata


def _wall_height_at_point(u: float, v: float) -> float:
    """
    Altezza REALE del muro interno nel punto (u,v) del perimetro
    (`church.floor_outline_local()`), usata per limitare correttamente
    dove un raggio di sole puo' colpire una parete. Non e' piu'
    un'unica WALL_HEIGHT_M uniforme: le nicchie delle cappelle hanno
    un'altezza molto piu' bassa (9.64-10.95 m, tetto inclinato) e
    l'abside ha la sua altezza propria (15.69 m) - usare WALL_HEIGHT_M
    ovunque causava macchie di luce segmentate/interrotte quando la
    luce di una vetrata di cleristorio (11-13 m, sopra il vero tetto
    delle nicchie) veniva erroneamente fermata da un "muro" che a
    quell'altezza non esiste piu' nella nicchia.
    """
    Wh = NAVE_WIDTH_M / 2.0
    L = NAVE_LENGTH_M
    if u > L - 1e-6:
        # zona absidale (oltre la rientranza) - altezza propria dell'abside
        return APSE_EXTERNAL_HEIGHT_M + 4.15  # muro + colmo tetto, margine prudenziale
    if abs(v) > Wh + 1e-6:
        # dentro una nicchia di cappella: profilo inclinato del tetto basso
        depth_frac = (abs(v) - Wh) / CHAPEL_PROJECTION_DEPTH_M
        depth_frac = max(0.0, min(1.0, depth_frac))
        return CHAPEL_ROOF_HEIGHT_M + CHAPEL_ROOF_PITCH_RISE_M * (1.0 - depth_frac)
    return WALL_HEIGHT_M


@dataclass(frozen=True)
class LightSurfacePatch:
    """Una porzione della macchia di luce, gia' pronta per il
    rendering: punti (x,y,z) nel sistema mondo, sulla superficie
    reale colpita (pavimento o una parete)."""
    surface: str                              # "pavimento" oppure "parete"
    points_world: list[tuple[float, float, float]]


def _densify_loop(points: list[tuple[float, float, float]], subdivisions: int) -> list[tuple[float, float, float]]:
    n = len(points)
    dense = []
    for i in range(n):
        p0 = points[i]
        p1 = points[(i + 1) % n]
        for k in range(subdivisions):
            t = k / subdivisions
            dense.append(tuple(p0[j] + (p1[j] - p0[j]) * t for j in range(3)))
    return dense


def _ray_vs_segment_xy(p0, direction, seg_a, seg_b):
    """Interseca la semiretta p0 + t*direction (t>=0) col segmento
    seg_a->seg_b, nel piano (u,v). Ritorna (t, s) con s in [0,1] la
    posizione lungo il segmento, oppure None."""
    x1, y1 = p0
    dx, dy = direction
    x2, y2 = x1 + dx, y1 + dy
    x3, y3 = seg_a
    x4, y4 = seg_b
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    s = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / denom
    if t >= 1e-6 and 0.0 <= s <= 1.0:
        return t, s
    return None


def _schermi_cappelle(church):
    """Il muro della navata davanti a ogni cappella (v = +-Wh, largo quanto
    la nicchia): il raggio lo attraversa solo dentro l'arco d'ingresso.
    [(a, b, uc)] con a, b estremi (u, v) e uc il centro della cappella."""
    wh, dw = church.nave_width_m / 2.0, CHAPEL_PROJECTION_WIDTH_M / 2.0
    return [((uc - dw, lato * wh), (uc + dw, lato * wh), uc)
            for uc in church.chapel_u_positions() for lato in (1.0, -1.0)]


def _dentro_arco(u, w, uc):
    """True se (u, w) sul muro della navata cade nell'apertura dell'arco."""
    x = u - uc
    R, S = CHAPEL_ARCH_RADIUS_M, CHAPEL_ARCH_SPRING_M
    return abs(x) < R and (w < S or x * x + (w - S) ** 2 < R * R)


def _dentro_pianta(u, v, perimeter):
    dentro, j = False, len(perimeter) - 2
    for i in range(len(perimeter) - 1):
        (ui, vi), (uj, vj) = perimeter[i], perimeter[j]
        if (vi > v) != (vj > v) and u < (uj - ui) * (v - vi) / (vj - vi + 1e-12) + ui:
            dentro = not dentro
        j = i
    return dentro


def _ritaglia(poli, asse, limite, sopra):
    """Sutherland-Hodgman: tiene la parte di poli con p[asse] >= limite
    (sopra=True) o <= limite (sopra=False)."""
    dentro = (lambda p: p[asse] >= limite) if sopra else (lambda p: p[asse] <= limite)
    out = []
    for i, cur in enumerate(poli):
        prev = poli[i - 1]
        if dentro(cur) != dentro(prev):
            t = (limite - prev[asse]) / (cur[asse] - prev[asse])
            out.append(tuple(a + t * (b - a) for a, b in zip(prev, cur)))
        if dentro(cur):
            out.append(cur)
    return out


STACCO_BANCO_M = 0.012   # la luce sui banchi poco sopra il legno


def luce_sui_banchi(church, pavimento_uvw, verso_sole):
    """La macchia sul pavimento rimandata indietro lungo i raggi del sole
    sulle facce dei banchi rivolte al sole (sedili, schienali, fianchi):
    il fascio di luce le attraversa prima di arrivare a terra. Proiezione
    parallela = affine, quindi basta proiettare il poligono e ritagliarlo
    sul rettangolo della faccia. Restituisce poligoni (u, v, w) locali."""
    su, sv, sw = verso_sole
    s = (su, sv, sw)
    out = []
    pu = [p[0] for p in pavimento_uvw]
    pv = [p[1] for p in pavimento_uvw]
    for box in banchi_scatole(church):
        u0, u1, v0, v1, w0, w1 = box
        lim = ((u0, u1), (v0, v1), (w0, w1))
        # facce: (asse della normale, valore, segno); il fondo non si vede
        for asse, val, segno in ((2, w1, 1), (0, u0, -1), (0, u1, 1), (1, v0, -1), (1, v1, 1)):
            if s[asse] * segno <= 1e-6:
                continue                      # faccia non rivolta al sole
            # sposta il pavimento sulla faccia: P + t s con P[asse] + t s[asse] = val
            # (filtro veloce: la faccia si trova fra i punti del pavimento spostati)
            proiettati = []
            for p in pavimento_uvw:
                t = (val - p[asse]) / s[asse]
                proiettati.append(tuple(p[k] + t * s[k] for k in range(3)))
            altri = [k for k in range(3) if k != asse]
            poli = proiettati
            for k in altri:
                if max(q[k] for q in poli) < lim[k][0] or min(q[k] for q in poli) > lim[k][1]:
                    poli = []
                    break
                poli = _ritaglia(poli, k, lim[k][0], True)
                if not poli:
                    break
                poli = _ritaglia(poli, k, lim[k][1], False)
                if not poli:
                    break
            if len(poli) >= 3:
                d = [0.0, 0.0, 0.0]
                d[asse] = segno * STACCO_BANCO_M
                out.append([(q[0] + d[0], q[1] + d[1], q[2] + d[2]) for q in poli])
    return out


def _first_hit(u0, v0, w0, pu, pv, pw, perimeter, wall_height, schermi=()):
    """Trova la prima superficie colpita dal raggio uscente da
    (u0,v0,w0) in direzione (pu,pv,pw). Ritorna una tupla:
    ("pavimento", (u,v)) oppure ("parete", edge_index, s, height).

    L'altezza massima della parete NON e' piu' uniforme (il parametro
    wall_height resta come fallback/tetto massimo assoluto): per
    ciascun segmento si usa l'altezza REALE interpolata fra i due
    estremi del segmento (vedi _wall_height_at_point), cosi' un raggio
    che passa SOPRA una nicchia di cappella bassa non viene fermato da
    un muro che a quell'altezza non esiste piu'.
    """
    t_floor = (-w0 / pw) if pw < 0 else math.inf
    # gradini e abside rialzata: il raggio si ferma alla quota vera
    for _ in range(3):
        if not math.isfinite(t_floor):
            break
        q = quota_pavimento(u0 + pu * t_floor, v0 + pv * t_floor)
        if q >= w0:
            break
        t_floor = (q - w0) / pw

    best_t = t_floor
    best = ("pavimento", (u0 + pu * t_floor, v0 + pv * t_floor)) if math.isfinite(t_floor) else None
    # fuori dalla pianta non c'e' pavimento della chiesa (raggio uscito)
    if best is not None and not _dentro_pianta(*best[1], perimeter):
        best, best_t = None, math.inf

    for i in range(len(perimeter) - 1):
        seg_a, seg_b = perimeter[i], perimeter[i + 1]
        hit = _ray_vs_segment_xy((u0, v0), (pu, pv), seg_a, seg_b)
        if hit is None:
            continue
        t, s = hit
        height = w0 + pw * t
        h_a = _wall_height_at_point(*seg_a)
        h_b = _wall_height_at_point(*seg_b)
        local_wall_height = h_a + s * (h_b - h_a)
        if 0.0 <= height <= local_wall_height and t < best_t:
            best_t = t
            best = ("parete", i, s, height)

    # muro della navata davanti alle cappelle: ferma il raggio fuori dall'arco
    for k, (a, b, uc) in enumerate(schermi):
        hit = _ray_vs_segment_xy((u0, v0), (pu, pv), a, b)
        if hit is None:
            continue
        t, s = hit
        height = w0 + pw * t
        u = a[0] + s * (b[0] - a[0])
        if 0.0 <= height <= WALL_HEIGHT_M and t < best_t and not _dentro_arco(u, height, uc):
            best_t = t
            best = ("parete", len(perimeter) - 1 + k, s, height)

    return best


def project_window_with_walls(
    church: ChurchModel,
    outline_local_uvw: list[tuple[float, float, float]],
    wall_azimuth_deg: float,
    sun: SolarPosition,
    wall_height: float = WALL_HEIGHT_M,
) -> list[LightSurfacePatch]:
    """
    Proietta il contorno di una vetrata (coordinate locali u,v,w)
    lungo la direzione del sole, disegnando la macchia sul pavimento
    E/O sulle pareti verticali interne che il raggio incontra per
    primo. Ritorna una lista di LightSurfacePatch (puo' essere vuota
    se il sole e' sotto l'orizzonte o non illumina questa parete).
    """
    if not sun.is_up:
        return []

    diff = (sun.azimuth_deg - wall_azimuth_deg + 180.0) % 360.0 - 180.0
    if abs(diff) >= 90.0:
        return []

    dE, dN, dU = sun_vector_enu(sun)
    du, dv = church.enu_to_local_uv(dE, dN)
    pu, pv, pw = -du, -dv, -dU
    if pw >= 0:
        return []

    perimeter = church.floor_outline_local()  # anello chiuso: ultimo punto = primo
    dense = _densify_loop(outline_local_uvw, EDGE_SUBDIVISIONS)

    schermi = _schermi_cappelle(church)
    # tutti i tratti di parete: il perimetro della pianta, poi i muri davanti alle cappelle
    segmenti = [(perimeter[i], perimeter[i + 1]) for i in range(len(perimeter) - 1)] + [(a, b) for a, b, _ in schermi]
    hits = [_first_hit(u, v, w, pu, pv, pw, perimeter, wall_height, schermi) for (u, v, w) in dense]
    if all(h is None for h in hits):
        return []

    # --- raggruppa i punti consecutivi con la stessa superficie ---
    def surf_key(h):
        if h is None:
            return None
        return h[0] if h[0] == "pavimento" else (h[0], h[1])

    n = len(hits)
    # ruota la lista cosi' da iniziare a un cambio di gruppo (evita di
    # spezzare in due un gruppo che "avvolge" l'inizio/fine dell'anello)
    start = 0
    for i in range(n):
        if surf_key(hits[i]) != surf_key(hits[i - 1]):
            start = i
            break
    order = [(start + i) % n for i in range(n)]

    groups: list[list[int]] = []
    for idx in order:
        if hits[idx] is None:
            continue
        if groups and surf_key(hits[idx]) == surf_key(hits[groups[-1][-1]]):
            groups[-1].append(idx)
        else:
            groups.append([idx])

    # unisce un eventuale primo/ultimo gruppo residuo dello stesso tipo
    if len(groups) > 1 and surf_key(hits[groups[0][0]]) == surf_key(hits[groups[-1][-1]]):
        groups[0] = groups[-1] + groups[0]
        groups.pop()

    # --- condivide un punto di cucitura fra gruppi adiacenti, cosi' i
    #     poligoni si accostano senza vuoti visibili ---
    original_first = [g[0] for g in groups]  # per riconoscere il tipo del gruppo, ignorando la cucitura
    for gi in range(len(groups)):
        prev_group = groups[gi - 1]
        groups[gi] = [prev_group[-1]] + groups[gi]

    a2 = 0.0
    for i in range(len(perimeter) - 1):
        a2 += perimeter[i][0] * perimeter[i + 1][1] - perimeter[i + 1][0] * perimeter[i][1]
    verso_perimetro = a2                  # < 0: perimetro in senso orario (interno a destra)
    patches: list[LightSurfacePatch] = []
    for gi, group in enumerate(groups):
        if len(group) < 3:
            continue
        kind = hits[original_first[gi]][0]

        def to_world(h):
            if h[0] == "pavimento":
                u, v = h[1]
                return church.local_to_enu(u, v, quota_pavimento(u, v) + 0.02)
            _, edge_i, s, height = h
            seg_a, seg_b = segmenti[edge_i]
            u = seg_a[0] + s * (seg_b[0] - seg_a[0])
            v = seg_a[1] + s * (seg_b[1] - seg_a[1])
            # STACCO_PARETE verso l'interno: sul filo del muro le foto (pannelli
            # delle cappelle 15 cm dentro, fondi delle nicchie, pannello
            # dell'abside) coprirebbero la macchia di luce
            du, dv = seg_b[0] - seg_a[0], seg_b[1] - seg_a[1]
            n = math.hypot(du, dv) or 1.0
            iu, iv = (dv / n, -du / n) if verso_perimetro < 0 else (-dv / n, du / n)
            if edge_i >= len(perimeter) - 1:          # muro davanti a una cappella: verso la navata
                iu, iv = 0.0, -math.copysign(1.0, v)
            return church.local_to_enu(u + STACCO_PARETE_M * iu, v + STACCO_PARETE_M * iv, height)

        pts = [to_world(hits[idx]) for idx in group if hits[idx] is not None]
        if len(pts) >= 3:
            patches.append(LightSurfacePatch(surface=kind, points_world=pts))
        if kind == "pavimento":
            # la stessa luce, prima di toccare terra, cade sui banchi
            pav = [(hits[idx][1][0], hits[idx][1][1], quota_pavimento(*hits[idx][1]))
                   for idx in group if hits[idx] is not None and hits[idx][0] == "pavimento"]
            if len(pav) >= 3:
                for poli in luce_sui_banchi(church, pav, (-pu, -pv, -pw)):
                    patches.append(LightSurfacePatch(surface="banco", points_world=[church.local_to_enu(*q) for q in poli]))

    return patches
