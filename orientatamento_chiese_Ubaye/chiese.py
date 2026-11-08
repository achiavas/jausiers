#!/usr/bin/env python3
"""
Orientamento delle chiese in una zona (default: valle dell'Ubaye) e confronto con la pendenza.

Per ogni edificio di culto cristiano mappato in OpenStreetMap:
  1. calcola l'azimut dell'asse lungo (rettangolo minimo ruotato), in gradi da nord, 0-180;
  2. calcola la deviazione dall'asse est-ovest (0 = est-ovest, 90 = nord-sud);
  3. stima pendenza e direzione di massima discesa dal DEM IGN (RGE ALTI);
  4. calcola l'angolo tra asse della chiesa e linea di massima pendenza (0 = parallelo).

LIMITI (importanti):
  - l'asse e' noto solo modulo 180 gradi: lo script NON sa dove sia l'abside;
  - i contorni OSM possono includere sacrestie, campanili, annessi;
  - le chiese ricostruite possono non coincidere con quelle storiche;
  - l'endpoint altimetrico IGN va verificato (vedi ALTI): se cambia, aggiornare l'URL.

Uso:
  pip install requests shapely numpy
  python analizza_orientamento_chiese.py                      # Ubaye
  python analizza_orientamento_chiese.py --bbox 44.60 6.60 44.90 7.00   # S W N E
  python analizza_orientamento_chiese.py --no-dem             # solo orientamento
  python analizza_orientamento_chiese.py --no-commune         # senza ricerca del comune
  python analizza_orientamento_chiese.py --catholic-only
"""
import argparse
import csv
import math
import sys
import time

import numpy as np
import requests
from shapely.geometry import Polygon

OVERPASS = "https://overpass-api.de/api/interpreter"
ALTI = "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json"
GEO = "https://geo.api.gouv.fr/communes"  # comune che contiene un punto (solo Francia)
HEADERS = {"User-Agent": "orientamento-chiese/1.0 (ricerca storica)"}

# Ubaye (S, W, N, E), da affinare
DEFAULT_BBOX = (44.20, 6.50, 44.55, 6.90)


# ---------------------------------------------------------------- geometria
def to_xy(coords_ll, lon0, lat0):
    """(lon, lat) -> metri locali (x est, y nord), proiezione equirettangolare."""
    kx = 111320.0 * math.cos(math.radians(lat0))
    ky = 110540.0
    return [((lon - lon0) * kx, (lat - lat0) * ky) for lon, lat in coords_ll]


def axis_azimuth_xy(xy):
    """Azimut (0-180, da nord) dell'asse lungo, lunghezza lunga e corta."""
    poly = Polygon(xy)
    mrr = poly.minimum_rotated_rectangle
    c = np.array(mrr.exterior.coords)[:4]
    e1, e2 = c[1] - c[0], c[2] - c[1]
    l1, l2 = np.hypot(*e1), np.hypot(*e2)
    e, long_len, short_len = (e1, l1, l2) if l1 >= l2 else (e2, l2, l1)
    az = math.degrees(math.atan2(e[0], e[1])) % 180.0
    return az, long_len, short_len


def dev_from_east_west(axis_az):
    """0 = asse est-ovest, 90 = asse nord-sud."""
    return abs(axis_az - 90.0)


def plane_fit(points_xyz):
    """z = a*x + b*y + c -> (pendenza in gradi, azimut di discesa 0-360)."""
    p = np.asarray(points_xyz, dtype=float)
    A = np.c_[p[:, 0], p[:, 1], np.ones(len(p))]
    (a, b, _), *_ = np.linalg.lstsq(A, p[:, 2], rcond=None)
    slope = math.degrees(math.atan(math.hypot(a, b)))
    downhill = math.degrees(math.atan2(-a, -b)) % 360.0
    return slope, downhill


def axis_vs_fall_line(axis_az, downhill_az):
    """Angolo (0-90) tra asse e linea di massima pendenza; 0 = parallelo."""
    d = abs(axis_az - (downhill_az % 180.0))
    return min(d, 180.0 - d)


# ------------------------------------------------------------------ dati
def fetch_churches(bbox, catholic_only=False):
    s, w, n, e = bbox
    den = '["denomination"~"catholic"]' if catholic_only else ""
    q = (
        f'[out:json][timeout:180];'
        f'way["amenity"="place_of_worship"]["religion"="christian"]{den}'
        f'({s},{w},{n},{e});out tags geom;'
    )
    r = requests.post(OVERPASS, data={"data": q}, headers=HEADERS, timeout=200)
    r.raise_for_status()
    return r.json().get("elements", [])


def fetch_named_points(bbox, catholic_only=False):
    """Nodi e relazioni di culto con nome: servono a dare un nome ai contorni (way) senza nome."""
    s, w, n, e = bbox
    den = '["denomination"~"catholic"]' if catholic_only else ""
    sel = f'["amenity"="place_of_worship"]["religion"="christian"]{den}["name"]({s},{w},{n},{e})'
    q = f'[out:json][timeout:180];(node{sel};relation{sel};way{sel};);out tags center;'
    r = requests.post(OVERPASS, data={"data": q}, headers=HEADERS, timeout=200)
    r.raise_for_status()
    pts = []
    for el in r.json().get("elements", []):
        c = el.get("center") or ({"lat": el["lat"], "lon": el["lon"]} if "lat" in el else None)
        if c:
            pts.append((c["lon"], c["lat"], el["tags"]["name"]))
    return pts


def nearest_name(lon, lat, named_points, max_m=60.0):
    """Nome del punto con nome piu' vicino entro max_m metri, altrimenti ''."""
    kx = 111320.0 * math.cos(math.radians(lat))
    ky = 110540.0
    best, best_d = "", max_m
    for plon, plat, nm in named_points:
        d = math.hypot((plon - lon) * kx, (plat - lat) * ky)
        if d < best_d:
            best, best_d = nm, d
    return best


def sample_dem(lon, lat, spacing_m=25.0):
    """Griglia 3x3 intorno al punto; restituisce [(x, y, z)] in metri locali."""
    kx = 111320.0 * math.cos(math.radians(lat))
    ky = 110540.0
    offs = [-spacing_m, 0.0, spacing_m]
    pts = [(dx, dy) for dx in offs for dy in offs]
    lons = "|".join(f"{lon + dx / kx:.7f}" for dx, dy in pts)
    lats = "|".join(f"{lat + dy / ky:.7f}" for dx, dy in pts)
    r = requests.get(
        ALTI,
        params={"lon": lons, "lat": lats, "resource": "ign_rge_alti_wld", "zonly": "false"},
        headers=HEADERS,
        timeout=60,
    )
    r.raise_for_status()
    els = r.json()["elevations"]
    out = []
    for (dx, dy), el in zip(pts, els):
        z = el.get("z")
        if z is None or z < -1000:  # nodata
            return None
        out.append((dx, dy, z))
    return out


def commune_from_point(lon, lat):
    """Nome del comune (e dipartimento) che contiene il punto; '' se non trovato."""
    try:
        r = requests.get(
            GEO,
            params={"lat": lat, "lon": lon, "fields": "nom,departement", "format": "json"},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data:
            c = data[0]
            dep = c.get("departement", {}).get("code", "")
            return f"{c['nom']} ({dep})" if dep else c["nom"]
    except Exception as exc:
        print(f"Comune non trovato per {lat:.5f},{lon:.5f}: {exc}", file=sys.stderr)
    return ""


# ------------------------------------------------------------------ analisi
def analyze(elements, use_dem=True, use_commune=True, named_points=None,
            min_area=80, max_area=3000, min_elong=1.3):
    rows = []
    for el in elements:
        geom = el.get("geometry")
        if not geom or len(geom) < 4:
            continue
        ll = [(p["lon"], p["lat"]) for p in geom]
        if ll[0] != ll[-1]:
            continue  # solo poligoni chiusi
        lon0 = sum(p[0] for p in ll) / len(ll)
        lat0 = sum(p[1] for p in ll) / len(ll)
        xy = to_xy(ll, lon0, lat0)
        poly = Polygon(xy)
        if not poly.is_valid or not (min_area <= poly.area <= max_area):
            continue
        az, L, S = axis_azimuth_xy(xy)
        if S == 0 or L / S < min_elong:
            continue  # troppo tozzo: l'asse non e' significativo
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:fr") or tags.get("old_name") or ""
        if not name and named_points:
            name = nearest_name(lon0, lat0, named_points)  # nome da nodo/relazione vicina
        commune = commune_from_point(lon0, lat0) if use_commune else ""
        if use_commune:
            time.sleep(0.05)
        if not commune:
            commune = tags.get("addr:city", "")
        if not name:
            kind = {"chapel": "Cappella", "church": "Chiesa", "cathedral": "Cattedrale"}.get(
                tags.get("building", ""), "Edificio di culto")
            place = tags.get("addr:place") or commune
            name = f"{kind} senza nome ({place})" if place else f"{kind} senza nome"
        row = {
            "nome": name,
            "commune": commune,
            "lieu_dit": tags.get("addr:place") or tags.get("addr:suburb") or tags.get("addr:hamlet") or "",
            "osm_url": f"https://www.openstreetmap.org/way/{el['id']}",
            "denomination": tags.get("denomination", ""),
            "lon": round(lon0, 6),
            "lat": round(lat0, 6),
            "area_m2": round(poly.area),
            "elongation": round(L / S, 2),
            "axis_az": round(az, 1),
            "dev_from_EW": round(dev_from_east_west(az), 1),
            "slope_deg": "",
            "downhill_az": "",
            "axis_vs_fallline": "",
        }
        if use_dem:
            try:
                pts = sample_dem(lon0, lat0)
                if pts:
                    slope, down = plane_fit(pts)
                    row["slope_deg"] = round(slope, 1)
                    row["downhill_az"] = round(down, 1)
                    row["axis_vs_fallline"] = round(axis_vs_fall_line(az, down), 1)
            except Exception as exc:  # rete/API: continuare senza DEM
                print(f"DEM non disponibile per {el['id']}: {exc}", file=sys.stderr)
            time.sleep(0.2)
        rows.append(row)
    return rows


def summarize(rows):
    n = len(rows)
    print(f"\nChiese analizzate: {n}")
    if not n:
        return
    ew = sum(1 for r in rows if r["dev_from_EW"] <= 20)
    print(f"Asse entro 20 gradi da est-ovest: {ew} ({100 * ew / n:.0f}%)")
    steep = [r for r in rows if r["slope_deg"] != "" and r["slope_deg"] >= 5]
    if steep:
        par = sum(1 for r in steep if r["axis_vs_fallline"] <= 20)
        print(f"Su pendenza >= 5 gradi: {len(steep)}; asse entro 20 gradi dalla "
              f"linea di massima pendenza: {par} ({100 * par / len(steep):.0f}%)")
    print("\nDistribuzione azimut dell'asse (classi di 15 gradi):")
    bins = [0] * 12
    for r in rows:
        bins[min(int(r["axis_az"] // 15), 11)] += 1
    for i, c in enumerate(bins):
        print(f"  {i * 15:3d}-{i * 15 + 15:3d} | {'#' * c} {c}")
    print("\nRiferimento Jausiers: asse ~150 (apse a ~330), dev_from_EW ~60.")


def print_table(rows):
    """Elenco ordinato per comune, con nome, azimut dell'asse e confronto con la pendenza."""
    print(f"\n{'Comune':26} {'Nome':38} {'asse':>5} {'devEW':>6} {'pend':>5} {'vs pend.':>8}")
    print("-" * 92)
    for r in rows:
        print(
            f"{r['commune'][:26]:26} {r['nome'][:38]:38} "
            f"{r['axis_az']:5.0f} {r['dev_from_EW']:6.0f} "
            f"{str(r['slope_deg']):>5} {str(r['axis_vs_fallline']):>8}"
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=DEFAULT_BBOX)
    ap.add_argument("--catholic-only", action="store_true")
    ap.add_argument("--no-dem", action="store_true")
    ap.add_argument("--no-commune", action="store_true", help="non cercare il comune (piu' veloce)")
    ap.add_argument("--out", default="orientamento_chiese.csv")
    args = ap.parse_args()

    els = fetch_churches(tuple(args.bbox), args.catholic_only)
    print(f"Oggetti OSM scaricati: {len(els)}")
    named = fetch_named_points(tuple(args.bbox), args.catholic_only)
    print(f"Punti con nome (nodi/relazioni/way): {len(named)}")
    rows = analyze(els, use_dem=not args.no_dem, use_commune=not args.no_commune, named_points=named)
    rows.sort(key=lambda r: (r["commune"], r["nome"]))
    if rows:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Scritto {args.out}")
    print_table(rows)
    summarize(rows)


if __name__ == "__main__":
    main()