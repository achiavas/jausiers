"""
light_projection.py
--------------------
Proietta il contorno di una vetrata sul piano del pavimento (w=0),
seguendo la direzione reale dei raggi solari, con una vera geometria
3D (non un'approssimazione 2D).

Principio fisico
-----------------
Il Sole e' cosi' lontano che i suoi raggi arrivano paralleli. Se
(dE, dN, dU) e' il versore che punta dal suolo VERSO il Sole (est,
nord, alto), la luce si propaga nella direzione opposta:

    p = (-dE, -dN, -dU)

Per ogni vertice P=(x,y,z) del contorno della vetrata (in coordinate
mondo ENU, origine a terra), il raggio di luce che passa da quel
punto e':

    P(t) = P + t * p ,   t >= 0

Interseca il pavimento (z=0) quando:

    t* = -P.z / p.z

(richiede p.z < 0, cioe' il sole sopra l'orizzonte: dU>0 => p.z=-dU<0).
Il punto sul pavimento e':

    floor_point = (P.x + t*p.x, P.y + t*p.y)

Applicando questo a tutti i vertici del contorno della vetrata si
ottiene il poligono (la "macchia di luce") proiettato sul pavimento,
con la forma e l'allungamento realistici dovuti all'angolo di
incidenza del sole.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Polygon
from shapely.ops import unary_union

from solar_position import SolarPosition, sun_vector_enu


@dataclass(frozen=True)
class LightPatch:
    window_name: str
    group: str
    polygon_xy: list[tuple[float, float]]  # sul pavimento (est, nord relativi)
    incidence_cos: float  # coseno dell'angolo fra raggio e normale (0..1)


def window_is_facing_sun(wall_azimuth_deg: float, sun_azimuth_deg: float) -> bool:
    """True se il sole e' (almeno geometricamente) davanti alla parete,
    cioe' entro +/-90 gradi dalla normale uscente della parete."""
    diff = (sun_azimuth_deg - wall_azimuth_deg + 180.0) % 360.0 - 180.0
    return abs(diff) < 90.0


def project_window_to_floor(
    outline_enu: list[tuple[float, float, float]],
    wall_azimuth_deg: float,
    sun: SolarPosition,
) -> LightPatch | None:
    """
    Proietta il contorno (lista di punti x,y,z in ENU) sul pavimento
    z=0, secondo la direzione del sole. Restituisce None se il sole e'
    sotto l'orizzonte o e' dietro la parete (nessuna luce diretta).
    """
    if not sun.is_up:
        return None
    if not window_is_facing_sun(wall_azimuth_deg, sun.azimuth_deg):
        return None

    dE, dN, dU = sun_vector_enu(sun)
    # direzione di propagazione della luce (dal cielo verso il basso)
    pE, pN, pU = -dE, -dN, -dU
    if pU >= 0:
        return None  # per sicurezza (non dovrebbe accadere se sun.is_up)

    poly: list[tuple[float, float]] = []
    for (x, y, z) in outline_enu:
        t = -z / pU
        if t < 0:
            continue
        poly.append((x + t * pE, y + t * pN))

    if len(poly) < 3:
        return None

    import math

    wall_normal_rad = math.radians(wall_azimuth_deg)
    normal = (math.sin(wall_normal_rad), math.cos(wall_normal_rad), 0.0)
    incidence_cos = max(0.0, dE * normal[0] + dN * normal[1] + dU * normal[2])

    return LightPatch(window_name="", group="", polygon_xy=poly, incidence_cos=incidence_cos)


def clip_patch_to_footprint(
    polygon_xy: list[tuple[float, float]],
    footprint_xy: list[tuple[float, float]],
) -> list[list[tuple[float, float]]]:
    """
    Ritaglia il poligono proiettato (che matematicamente si estende sul
    piano infinito del pavimento) contro il perimetro reale della
    chiesa: la parte che cadrebbe "oltre" un muro non e' fisicamente
    raggiunta dalla luce sul pavimento (il muro la intercetta prima).

    Restituisce una lista di anelli (poligoni semplici); puo' essere
    vuota se il fascio non tocca affatto il pavimento interno, o
    contenere piu' di un poligono se il ritaglio lo spezza in parti
    separate.
    """
    try:
        beam = Polygon(polygon_xy)
        room = Polygon(footprint_xy)
        if not beam.is_valid:
            beam = beam.buffer(0)
        if not room.is_valid:
            room = room.buffer(0)
        clipped = beam.intersection(room)
    except Exception:
        return []

    if clipped.is_empty:
        return []

    geoms = getattr(clipped, "geoms", [clipped])
    rings: list[list[tuple[float, float]]] = []
    for g in geoms:
        if g.is_empty or g.area <= 0:
            continue
        rings.append(list(g.exterior.coords))
    return rings
