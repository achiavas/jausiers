#!/usr/bin/env python3
"""
sole.py - calcolo solare headless per il mod "jausiers".

Riusa i moduli di jausiers_sun3d_py (solar_position, church_geometry,
wall_projection) senza PyVista e stampa un JSON su stdout.

Uso:
  python3 sole.py                         # facciata 160 (valore del modello)
  python3 sole.py --asse 156.2            # asse lungo 0-360, anche modulo 180
  python3 sole.py --facciata 152          # normale uscente della facciata
  python3 sole.py --asse 156 --data 2026-12-06

L'asse trovato dalla ricerca e' spesso noto solo modulo 180: fra
asse e asse+180 si sceglie come facciata quello piu' vicino al valore
del modello (160, facciata a SSE, abside a NNW), poi si ruota tutto
l'edificio (facciata, cappelle e le 5 pareti absidali misurate) della
stessa differenza.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # Python >= 3.9
except ImportError:  # Python 3.8, come viewer_3d.py
    from backports.zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "jausiers_sun3d_py"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC, help="cartella jausiers_sun3d_py")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--asse", type=float, help="azimut dell'asse lungo (gradi da nord)")
    g.add_argument("--facciata", type=float, help="azimut della normale uscente della facciata")
    ap.add_argument("--data", help="giorno da analizzare, AAAA-MM-GG (default: oggi)")
    ap.add_argument("--passo", type=int, default=10, help="passo in minuti")
    args = ap.parse_args()

    sys.path.insert(0, HERE)
    from ruota import ruota  # noqa: E402

    r = ruota(args.src, asse=args.asse, facciata=args.facciata)
    cg, facade, delta, source = r["cg"], r["facade"], r["delta"], r["fonte"]
    from solar_position import solar_position  # noqa: E402
    from wall_projection import project_window_with_walls  # noqa: E402

    church = cg.default_church()

    tz = ZoneInfo(cg.TIMEZONE_NAME)
    year = (date.fromisoformat(args.data) if args.data else date.today()).year
    days = [
        ("Giorno scelto" if args.data else "Oggi",
         date.fromisoformat(args.data) if args.data else date.today()),
        ("Solstizio d'inverno", date(year, 12, 21)),
        ("Equinozio di primavera", date(year, 3, 20)),
        ("Solstizio d'estate", date(year, 6, 21)),
        ("San Nicola (6 dicembre)", date(year, 12, 6)),
    ]

    out_days = []
    for label, d in days:
        lit: dict[str, list[str]] = {}
        sunrise = sunset = None
        noon = {"alt": -99.0}
        t = datetime(d.year, d.month, d.day, tzinfo=tz)
        end = t + timedelta(days=1)
        while t < end:
            sun = solar_position(t, cg.LATITUDE_DEG, cg.LONGITUDE_DEG)
            hhmm = t.strftime("%H:%M")
            if sun.is_up:
                sunrise = sunrise or hhmm
                sunset = hhmm
                if sun.altitude_deg > noon["alt"]:
                    noon = {"ora": hhmm, "alt": round(sun.altitude_deg, 1),
                            "az": round(sun.azimuth_deg, 1)}
                for win in church.windows:
                    if win.group == "porta":
                        continue
                    if project_window_with_walls(church, win.local_outline(),
                                                 win.wall_azimuth_deg, sun):
                        lit.setdefault(win.name, []).append(hhmm)
            t += timedelta(minutes=args.passo)
        windows = [
            {"nome": n, "da": times[0], "a": times[-1], "minuti": len(times) * args.passo}
            for n, times in lit.items()
        ]
        windows.sort(key=lambda w: w["da"])
        out_days.append({
            "etichetta": label, "data": d.isoformat(),
            "alba": sunrise, "tramonto": sunset, "culminazione": noon,
            "vetrate": windows,
        })

    json.dump({
        "fonte_azimut": source,
        "asse_input": args.asse,
        "facciata_az": round(facade, 1),
        "abside_az": round((facade + 180.0) % 360.0, 1),
        "rotazione_vs_modello": round(delta, 1),
        "lat": cg.LATITUDE_DEG, "lon": cg.LONGITUDE_DEG,
        "passo_min": args.passo,
        "giorni": out_days,
    }, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
