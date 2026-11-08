#!/usr/bin/env python3
"""
viewer.py - apre il viewer 3D di jausiers_sun3d_py (viewer_3d.py) con
l'edificio ruotato sull'azimut trovato dalla ricerca.

  python3 viewer.py --asse 156.2
  python3 viewer.py                 # facciata del modello (160)
  python3 viewer.py --prova         # costruisce la scena off-screen ed esce
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "jausiers_sun3d_py"))
sys.path.insert(0, HERE)

from ruota import ruota  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--asse", type=float)
    ap.add_argument("--prova", action="store_true")
    args = ap.parse_args()

    r = ruota(args.src, asse=args.asse)
    os.chdir(args.src)
    import viewer_3d  # noqa: E402  (dopo ruota: legge le costanti ruotate)

    app = viewer_3d.ChurchSunViewer(off_screen=args.prova)
    print(f"viewer 3D: facciata {r['facade']:.1f}, rotazione {r['delta']:+.1f} ({r['fonte']})", flush=True)
    if args.prova:
        print("finestre:", len(app.church.windows), "facciata modello:", app.church.facade_azimuth_deg)
        return
    app.plotter.title = f"Jausiers - facciata {r['facade']:.1f}°"
    app.show()


if __name__ == "__main__":
    main()
