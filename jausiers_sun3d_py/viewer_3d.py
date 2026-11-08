"""
viewer_3d.py
------------
Applicazione interattiva Python (PyVista/VTK) per esplorare la
proiezione solare attraverso le vetrate della chiesa di Jausiers su
un modello 3D SOLIDO (mura con spessore reale, tetto, pavimento,
vetrate incassate).

La finestra e' divisa in due pannelli SEPARATI (due renderer VTK
distinti, non un overlay): un pannello laterale con i controlli a
sinistra, e la vista 3D a destra. I due non si sovrappongono mai,
indipendentemente da come viene ridimensionata la finestra.

Uso:
    python3 viewer_3d.py

Controlli:
    - Trascina con il mouse (tasto sinistro) nel pannello 3D -> ruota
      il punto di vista
    - Tasto destro / rotellina (nel pannello 3D) -> zoom
    - Tasto centrale / shift+trascina           -> pan
    - Slider "Giorno dell'anno" e "Ora locale" nel pannello laterale
      -> cambiano data e ora (la data/ora corrente e' anche mostrata
      in grande sopra ciascuno slider)
    - Tasti 1 / 2 / 3   -> salta a solstizio d'inverno / equinozio /
                           solstizio d'estate (stesso anno)
    - Tasti n/s/e/w     -> vista dal lato Nord / Sud / Est / Ovest
    - Tasto t           -> vista dall'alto (pianta)
    - Tasto r           -> vista assonometrica di default
    - Barra spaziatrice -> avvia/ferma l'animazione (scorre l'ora)
    - Tasto h           -> mostra/nasconde il pannello "Storia e fonti"

Dipendenze:  pip install pyvista numpy shapely --break-system-packages
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # libreria standard da Python 3.9
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo  # pip install backports.zoneinfo tzdata
    except ImportError as exc:
        raise ImportError(
            "Modulo 'zoneinfo' non disponibile (richiede Python >= 3.9). "
            "Aggiorna Python, oppure esegui: "
            "pip install backports.zoneinfo tzdata --break-system-packages"
        ) from exc

import numpy as np
import pyvista as pv

from church_geometry import (default_church, LATITUDE_DEG, LONGITUDE_DEG, TIMEZONE_NAME, WALL_HEIGHT_M,
                             NAVE_LENGTH_M, NAVE_WIDTH_M, CHAPEL_PROJECTION_DEPTH_M)
from church_mesh import build_all, WALL_THICKNESS_M
from wall_projection import project_window_with_walls
from reference_photos import build_photo_actors, camera_dentro, ATTORI_CAPPELLE
from solar_position import solar_position
from storia_chiesa import testo_storia

# Muri BIANCHI visti da dentro (come nel sito, modelli/index.html):
# ogni triangolo viene orientato con la normale verso FUORI (lontano dal
# centro della navata, o della nicchia per cappelle e pilastri), poi il
# fronte ha il colore esterno e il retro (visto da dentro) e' bianco.
COLORE_INTERNO = "#f7f5f0"
OPACITA_INTERNA = 0.6


def orienta_verso_fuori(mesh: pv.PolyData, church, centro) -> pv.PolyData:
    mesh = mesh.triangulate()
    tri = mesh.faces.reshape(-1, 4)[:, 1:].copy()
    P = mesh.points
    a, b, c = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    n = np.cross(b - a, c - a)
    m = (a + b + c) / 3.0
    refs = []
    for x, y, _ in m:
        u, v = church.enu_to_local_uv(x, y)
        refs.append(church.local_to_enu(*centro(church, u, v)))
    dentro = np.einsum("ij,ij->i", n, m - np.array(refs)) < 0
    tri[dentro] = tri[dentro][:, [0, 2, 1]]
    out = pv.PolyData(P, np.c_[np.full(len(tri), 3), tri].ravel())
    return out


def fora_archi_cappelle(mesh: pv.PolyData, church) -> pv.PolyData:
    """Buca il muro della navata negli archi d'ingresso delle cappelle con
    nicchia: il muro e' semitrasparente e, davanti alla nicchia, la
    sbiadirebbe. Le facce lunghe dei due fianchi (interna ed esterna)
    vengono tolte e ricostruite con gli archi aperti (stessa forma di
    reference_photos.card_con_foro)."""
    from reference_photos import NICCHIE, _N_ARCO
    from church_geometry import CHAPEL_ARCH_RADIUS_M as R, CHAPEL_ARCH_SPRING_M as S
    m = mesh.triangulate()
    tri = m.faces.reshape(-1, 4)[:, 1:]
    P = m.points
    uh = np.array(church.local_to_enu(1, 0, 0)[:2]); vh = np.array(church.local_to_enu(0, 1, 0)[:2])
    U, V, W = P[:, :2] @ uh, P[:, :2] @ vh, P[:, 2]
    tv = V[tri]
    piatta = np.ptp(tv, axis=1) < 1e-3
    wh = NAVE_WIDTH_M / 2.0
    lungo = piatta & (np.abs(np.abs(tv[:, 0]) - wh) < WALL_THICKNESS_M + 0.05) & (np.ptp(U[tri], axis=1) > 5)
    # parete di fondo della navata (u = L, dove si apre l'abside): nel modello
    # la navata e' un rettangolo chiuso, ma li' c'e' l'arco trionfale aperto
    fondo = (U[tri].min(1) > NAVE_LENGTH_M - 0.05) & (np.ptp(U[tri], axis=1) < 1e-3)
    tri = tri[~fondo]; lungo = lungo[~fondo]; tv = V[tri]
    us = church.chapel_u_positions()
    nuovi_p, nuovi_t = [], []
    for livello in sorted({round(float(x), 4) for x in tv[lungo, 0]}):
        sel = lungo & (np.abs(tv[:, 0] - livello) < 1e-3)
        u0, u1 = U[tri[sel]].min(), U[tri[sel]].max()
        w0, w1 = W[tri[sel]].min(), W[tri[sel]].max()
        lato = 1 if livello > 0 else -1
        centri = sorted(us[i] for _, l, i in NICCHIE if l == lato)
        quads = []
        x = u0
        for uc in centri:
            quads.append(((x, w0), (uc - R, w0), (uc - R, w1), (x, w1)))
            for k in range(_N_ARCO):
                t0, t1 = math.pi * k / _N_ARCO, math.pi * (k + 1) / _N_ARCO
                a0, a1 = uc - R * math.cos(t0), uc - R * math.cos(t1)
                b0, b1 = S + R * math.sin(t0), S + R * math.sin(t1)
                quads.append(((a0, b0), (a1, b1), (a1, w1), (a0, w1)))
            x = uc + R
        quads.append(((x, w0), (u1, w0), (u1, w1), (x, w1)))
        for q in quads:
            i = len(nuovi_p)
            nuovi_p += [church.local_to_enu(qu, livello, qw) for qu, qw in q]
            nuovi_t += [(i, i + 1, i + 2), (i, i + 2, i + 3)]
    resto = tri[~lungo]
    pts = np.vstack([P, np.array(nuovi_p)])
    tutti = np.vstack([resto, np.array(nuovi_t) + len(P)])
    return pv.PolyData(pts, np.c_[np.full(len(tutti), 3), tutti].ravel())

TZ = ZoneInfo(TIMEZONE_NAME)
YEAR = 2026

GROUP_COLORS = {"cappella": "#f2a154", "abside": "#d1495b", "facciata": "#3a86ff", "porta": "#cfc7b0"}
WALL_COLOR = "#cfc7b0"
WALL_OPACITY = 0.28

MONTHS_IT = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
             "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

SIDEBAR_BG = "#161b22"
SCENE_BG = "#0d1117"
ACCENT = "#f2a154"
TEXT_COLOR = "#e8e8ec"
DIM_COLOR = "#8892a0"

# indici dei due pannelli (riga, colonna) nella griglia 1x2
SIDEBAR = (0, 0)
SCENE = (0, 1)


# --- Tetto e muri esterni tappezzati (texture da IMG_9765,
#     tetto_muri_da_video.py): per ogni faccia le coordinate texture sono
#     in metri sul suo piano (orizzontale lungo la faccia, e in su lungo
#     il muro o lungo la falda), divise per la misura di una ripetizione.
#     Facce inclinate (|nz| > 0.35) = falde: scandole; le altre: intonaco.
#     Stessa regola nel sito (index.html, tappezza). ---
OPACITA_ESTERNA = 0.75
OPACITA_TETTO = 0.9
_TEXTURE = {}


def _texture(nome):
    import os
    from reference_photos import PHOTOS_DIR
    if nome not in _TEXTURE:
        path = os.path.join(PHOTOS_DIR, nome)
        _TEXTURE[nome] = None
        if os.path.isfile(path):
            t = pv.read_texture(path)
            t.repeat = True
            _TEXTURE[nome] = t
    return _TEXTURE[nome]


def _dentro_la_chiesa(church, pts):
    """True per i punti (ENU) nello spazio interno di navata e abside:
    dentro la pianta e sotto la quota del muro (navata: muro alto; abside:
    il suo muro)."""
    from church_geometry import APSE_EXTERNAL_HEIGHT_M
    uh = np.array(church.local_to_enu(1, 0, 0)[:2]); vh = np.array(church.local_to_enu(0, 1, 0)[:2])
    U, V, W = pts[:, :2] @ uh, pts[:, :2] @ vh, pts[:, 2]
    poly = np.array(church.floor_outline_local()[:-1])
    dentro = np.zeros(len(pts), bool)
    j = len(poly) - 1
    for i in range(len(poly)):                     # punto nel poligono (raggio orizzontale)
        (ui, vi), (uj, vj) = poly[i], poly[j]
        attraversa = ((vi > V) != (vj > V)) & (U < (uj - ui) * (V - vi) / (vj - vi + 1e-12) + ui)
        dentro ^= attraversa
        j = i
    # solo navata e abside: le facce delle cappelle sono gia' tutte orientate
    # verso fuori dalla nicchia (e il muro della navata dietro le cappelle e'
    # una faccia unica, che fuori dalle cappelle e' esterna)
    wh = church.nave_width_m / 2.0
    alto = np.where(U > church.nave_length_m, APSE_EXTERNAL_HEIGHT_M, WALL_HEIGHT_M)
    return dentro & (np.abs(V) < wh) & (W > 0) & (W < alto)


def tappezza(mesh: pv.PolyData, church=None) -> list:
    """Divide la mesh in muri e falde ESTERNI, con le coordinate texture,
    e facce che guardano DENTRO la chiesa (senza texture: la texture si
    vede solo da fuori). [(parte, texture o None)]: None = faccia interna."""
    from reference_photos import MURO_TEXTURE_FILENAME, MURO_TEXTURE_M, TETTO_TEXTURE_FILENAME, TETTO_TEXTURE_M
    tri = mesh.triangulate()
    P = tri.points[tri.faces.reshape(-1, 4)[:, 1:]]
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    falda = np.abs(n[:, 2]) > 0.35
    interna = _dentro_la_chiesa(church, P.mean(1) + 0.3 * n) if church is not None else np.zeros(len(P), bool)
    if church is not None:
        # facciata esterna (faccia verso -u, sul filo della facciata): niente
        # intonaco ne' muro, la copre la foto della facciata
        uh = np.array(church.local_to_enu(1, 0, 0)[:2])
        interna |= (n[:, :2] @ uh < -0.9) & (P.mean(1)[:, :2] @ uh < 0.8)
    out = []
    for sel, (tw, th), nome in ((~falda & ~interna, (MURO_TEXTURE_M, MURO_TEXTURE_M), MURO_TEXTURE_FILENAME),
                                (falda & ~interna, TETTO_TEXTURE_M, TETTO_TEXTURE_FILENAME),
                                (interna, (1.0, 1.0), None)):
        if not sel.any():
            continue
        Ps, ns = P[sel], n[sel]
        t = np.cross([0.0, 0.0, 1.0], ns)
        piatte = np.linalg.norm(t, axis=1) < 1e-3
        t[piatte] = [1.0, 0.0, 0.0]
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        b = np.cross(ns, t)
        uv = np.c_[np.einsum("fkj,fj->fk", Ps, t).ravel() / tw, np.einsum("fkj,fj->fk", Ps, b).ravel() / th]
        k = len(Ps)
        parte = pv.PolyData(Ps.reshape(-1, 3), faces=np.c_[np.full(k, 3), np.arange(3 * k).reshape(-1, 3)].ravel())
        parte.active_texture_coordinates = uv
        out.append((parte, _texture(nome) if nome else None))
    return out


# --- Ombre opache degli oggetti interni nella luce delle vetrate (come nel
#     sito, dove le fa la shadow map della luce del sole): punti fitti in
#     ogni macchia di luce, da ognuno un raggio verso il sole; dove incontra
#     un banco, un altare, il pulpito... un quadratino scuro. Muri, tetto e
#     volte non contano (la luce che entra e' gia' calcolata a parte). ---
OMBRA_PASSO_M = 0.12
OMBRA_OPACITA = 0.55
OGGETTI_CHE_FANNO_OMBRA = ("banchi", "balaustra", "riscaldamento", "pulpito", "altare_oro", "altare_cera",
                           "altare_libro", "cornicione", "lampadario_cristallo", "lampadario_oro",
                           "lampadario_candele", "organo_legno", "organo_zoccolo", "altari_marmo", "altari_tovaglia")


def localizzatore_ombre(meshes: dict):
    """Un unico albero (vtkOBBTree) con tutti gli oggetti interni che fanno ombra."""
    import vtk
    parti = [meshes[k] for k in OGGETTI_CHE_FANNO_OMBRA if k in meshes]
    parti += [m for m, _ in meshes.get("arredi_muri", [])]
    parti += [p for _, d, _, _ in meshes.get("altari_cappelle", []) for p in d.values()]
    tutto = parti[0].triangulate()
    for p in parti[1:]:
        tutto = tutto.merge(p.triangulate())
    obb = vtk.vtkOBBTree()
    obb.SetDataSet(tutto)
    obb.BuildLocator()
    return obb


def ombre_nella_macchia(pts: np.ndarray, sun_dir: np.ndarray, obb) -> pv.PolyData | None:
    """Quadratini (lato OMBRA_PASSO_M) dei punti della macchia piana `pts` da
    cui il sole e' coperto da un oggetto interno; None se non ce ne sono."""
    import vtk
    o = pts[0]
    e1 = pts[1] - o
    e1 /= np.linalg.norm(e1) or 1.0
    n = np.zeros(3)
    for k in range(2, len(pts)):
        n = np.cross(pts[1] - o, pts[k] - o)
        if np.linalg.norm(n) > 1e-9:
            break
    if np.linalg.norm(n) < 1e-9:
        return None
    n /= np.linalg.norm(n)
    e2 = np.cross(n, e1)
    xy = np.c_[(pts - o) @ e1, (pts - o) @ e2]
    passo = OMBRA_PASSO_M
    (x0, y0), (x1, y1) = xy.min(0), xy.max(0)
    while (x1 - x0) * (y1 - y0) / passo ** 2 > 6000:      # al massimo ~6000 raggi per macchia
        passo *= 1.25
    gx, gy = np.meshgrid(np.arange(x0 + passo / 2, x1, passo), np.arange(y0 + passo / 2, y1, passo))
    gx, gy = gx.ravel(), gy.ravel()
    dentro = np.zeros(len(gx), bool)                      # punto nel poligono (raggio orizzontale)
    j = len(xy) - 1
    for i in range(len(xy)):
        (xi, yi), (xj, yj) = xy[i], xy[j]
        dentro ^= ((yi > gy) != (yj > gy)) & (gx < (xj - xi) * (gy - yi) / (yj - yi + 1e-12) + xi)
        j = i
    gx, gy = gx[dentro], gy[dentro]
    if len(gx) == 0:
        return None
    lato = -1.0 if np.dot(n, sun_dir) < 0 else 1.0       # la faccia verso il sole
    P = o + np.outer(gx, e1) + np.outer(gy, e2) + lato * n * 0.01
    hit = vtk.vtkPoints()
    coperti = []
    for k, p in enumerate(P):
        if obb.IntersectWithLine(p, p + sun_dir * 40.0, hit, None) != 0:
            coperti.append(k)
    if not coperti:
        return None
    h = passo / 2
    q = []
    for k in coperti:
        c = P[k] + lato * n * 0.005
        q += [c - h * e1 - h * e2, c + h * e1 - h * e2, c + h * e1 + h * e2, c - h * e1 + h * e2]
    m = len(coperti)
    faces = np.c_[np.full(m, 4), np.arange(4 * m).reshape(-1, 4)].ravel()
    return pv.PolyData(np.array(q), faces=faces)


class _Gruppo:
    """Piu' attori (muri e falde della stessa mesh) mostrati/nascosti insieme."""
    def __init__(self, attori):
        self.attori = attori

    def SetVisibility(self, v):
        for a in self.attori:
            a.SetVisibility(v)


class ChurchSunViewer:
    def __init__(self, off_screen: bool = False):
        self.church = default_church()
        self.wall_height = WALL_HEIGHT_M
        self.meshes = build_all(self.church, wall_height=self.wall_height)
        self._ombre_obb = localizzatore_ombre(self.meshes)

        self.day_of_year = 172  # ~21 giugno
        self.hour = 12.0
        self.light_patch_actors: list = []

        self.plotter = pv.Plotter(
            shape=(1, 2), col_weights=[0.27, 0.73],
            window_size=(1750, 1050), off_screen=off_screen, border=False,
        )

        self._build_sidebar_static()
        self._build_scene_static()
        self._build_widgets()

        self.update_scene(render=False)

        self.plotter.subplot(*SCENE)
        self._center_camera()

        self.plotter.subplot(*SCENE)
        self.plotter.add_key_event("1", lambda: self._jump_to(12, 21))
        self.plotter.add_key_event("2", lambda: self._jump_to(3, 20))
        # NOTA: "3", "e", "w" erano scorciatoie RISERVATE di VTK (non di
        # questa applicazione) - "3" attiva il rendering stereo (schermo
        # che appare "viola"), "e" chiude il programma (e' il tasto di
        # uscita di default dell'interactor), "w" passa in modalita'
        # wireframe (aspetto "trasparente"). Non sono sovrascrivibili
        # in modo affidabile da Python (sono gestite a livello C++ nella
        # classe base dell'interactor, non tramite observer rimovibili -
        # verificato con test mirati). Sostituite con tasti equivalenti
        # MA verificati sicuri (nessun effetto collaterale indesiderato).
        self.plotter.add_key_event("4", lambda: self._jump_to(6, 21))
        self.plotter.add_key_event("n", lambda: self._view_from(0))
        self.plotter.add_key_event("s", lambda: self._view_from(180))
        self.plotter.add_key_event("k", lambda: self._view_from(90))
        self.plotter.add_key_event("o", lambda: self._view_from(270))
        self.plotter.add_key_event("t", self._view_top)
        self.plotter.add_key_event("r", self._center_camera)
        self.plotter.add_key_event("space", self._toggle_play)
        self.plotter.add_key_event("p", self._toggle_photos)
        self.plotter.add_key_event("v", self._toggle_windows)
        self.plotter.add_key_event("h", self._toggle_storia)

        self._playing = False
        self._timer_id = None

    # -----------------------------------------------------------------
    # Pannello laterale (sinistra): elementi statici
    # -----------------------------------------------------------------
    def _build_sidebar_static(self):
        self.plotter.subplot(*SIDEBAR)
        self.plotter.set_background(SIDEBAR_BG)

        self.plotter.add_text(
            "JAUSIERS\nÉglise Saint-Nicolas-de-Myre",
            position=(0.06, 0.955), viewport=True, font_size=14,
            color=TEXT_COLOR, name="title",
        )

        # -- etichette fisse (non cambiano) --
        self.plotter.add_text("GIORNO DELL'ANNO", position=(0.06, 0.865),
                               viewport=True, font_size=11, color=DIM_COLOR,
                               name="lbl_day")
        self.plotter.add_text("ORA LOCALE (Europe/Paris)", position=(0.06, 0.645),
                               viewport=True, font_size=11, color=DIM_COLOR,
                               name="lbl_hour")

        legend_y = 0.205
        for i, (label, color) in enumerate([
            ("Cappelle laterali", GROUP_COLORS["cappella"]),
            ("Abside", GROUP_COLORS["abside"]),
            ("Facciata (ingresso)", GROUP_COLORS["facciata"]),
        ]):
            self.plotter.add_text(
                f"\u25A0 {label}", position=(0.06, legend_y - i * 0.032),
                viewport=True, font_size=11, color=color, name=f"legend_{i}",
            )

        hint = (
            "[1][2][4] solstizi/equinozio\n"
            "[N][S][K][O] viste laterali (K=Est)\n"
            "[T] pianta   [R] reset\n"
            "[Spazio] anima giornata\n"
            "[V] vetrate   [H] storia e fonti\n"
            "Trascina nel pannello 3D\n"
            "per ruotare - rotellina per zoom"
        )
        self.plotter.add_text(hint, position=(0.06, 0.02), viewport=True,
                               font_size=9, color=DIM_COLOR, name="hints")
        self.plotter.add_text("Mostra foto", position=(0.14, 0.245), viewport=True,
                               font_size=11, color=TEXT_COLOR, name="lbl_photos_checkbox")
        self.plotter.add_text("Mostra vetrate", position=(0.62, 0.245), viewport=True,
                               font_size=11, color=TEXT_COLOR, name="lbl_windows_checkbox")

    def _build_widgets(self):
        self.plotter.subplot(*SIDEBAR)
        self.day_slider = self.plotter.add_slider_widget(
            self._on_day_change, [1, 365], value=self.day_of_year,
            title=None,
            pointa=(0.06, 0.80), pointb=(0.93, 0.80),
            interaction_event="always", style="modern",
            color=ACCENT,
        )
        self.hour_slider = self.plotter.add_slider_widget(
            self._on_hour_change, [0.0, 23.983], value=self.hour,
            title=None,
            pointa=(0.06, 0.58), pointb=(0.93, 0.58),
            interaction_event="always", style="modern",
            color=ACCENT,
        )
        self.photos_checkbox = self.plotter.add_checkbox_button_widget(
            self._on_photos_checkbox, value=True,
            position=(28, 250), size=22,
            color_on=ACCENT, color_off="#3a3f4a", background_color=SIDEBAR_BG,
        )
        self.windows_checkbox = self.plotter.add_checkbox_button_widget(
            self._on_windows_checkbox, value=True,
            position=(255, 250), size=22,
            color_on=ACCENT, color_off="#3a3f4a", background_color=SIDEBAR_BG,
        )

    def _sync_sliders(self):
        self.day_slider.GetRepresentation().SetValue(self.day_of_year)
        self.hour_slider.GetRepresentation().SetValue(self.hour)

    # -----------------------------------------------------------------
    # Pannello 3D (destra): elementi statici
    # -----------------------------------------------------------------
    def _build_scene_static(self):
        self.plotter.subplot(*SCENE)
        self.plotter.set_background(SCENE_BG)
        self.plotter.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)

        m = self.meshes
        # pavimento vero (texture da IMG_9757, pavimento_da_video.py) se c'e'
        self._add_pavimento(m["floor"])
        # arredi in 3D (misure stimate dalle foto): banchi, altari
        self.plotter.add_mesh(m["banchi"], color="#7a4a2a", smooth_shading=False, name="banchi")
        self.plotter.add_mesh(m["riscaldamento"], color="#4e301c", smooth_shading=False, name="riscaldamento")
        self.plotter.add_mesh(m["pulpito"], color="#4e301c", smooth_shading=False, name="pulpito")
        self.plotter.add_mesh(m["organo_legno"], color="#b5793f", smooth_shading=False, name="organo_legno")
        self.plotter.add_mesh(m["organo_zoccolo"], color="#2a1a10", smooth_shading=False, name="organo_zoccolo")
        for k, col in (("oro", "#c9a33a"), ("cera", "#f5f1e6"), ("fiamma", "#ffcc44"), ("libro", "#7a1f1f")):
            self.plotter.add_mesh(m[f"altare_{k}"], color=col, smooth_shading=False, name=f"altare_{k}")
        for nome, parti, cf, cg in m["altari_cappelle"]:
            for chiave, col in (("fronte", cf), ("tovaglia", 0xf6f4ee), ("gradino", cg)):
                self.plotter.add_mesh(parti[chiave], color=f"#{col:06x}", smooth_shading=False, name=f"altare_{nome}_{chiave}")
        self.plotter.add_mesh(m["cornicione"], color="#e8e3d6", smooth_shading=False, name="cornicione")
        # volta dell'abside con la foto (volta_da_video.py, IMG_9757 a 10 s) e volta della navata
        tex_volta = _texture("volta_abside.jpg")
        if tex_volta is not None:
            tex_volta.repeat = False
            self.plotter.add_mesh(m["volta_abside"], texture=tex_volta, smooth_shading=True, name="volta_abside")
        else:
            self.plotter.add_mesh(m["volta_abside"], color="#d8e5c6", smooth_shading=True, name="volta_abside")
        # lampadario di cristallo appeso alla chiave della volta dell'abside
        self.plotter.add_mesh(m["lampadario_cristallo"], color="#fff1cf", opacity=0.8, smooth_shading=True,
                              ambient=0.5, name="lampadario_cristallo")
        self.plotter.add_mesh(m["lampadario_oro"], color="#c9a33a", smooth_shading=True, name="lampadario_oro")
        self.plotter.add_mesh(m["lampadario_candele"], color="#f5f1e6", smooth_shading=False, name="lampadario_candele")
        # controfacciata e lesene fra le cappelle (IMG_9758)
        for k, (parte, col) in enumerate(m["arredi_muri"]):
            self.plotter.add_mesh(parte, color=f"#{col:06x}", smooth_shading=False, name=f"arredo_muro_{k}")
        self.plotter.add_mesh(m["volta_navata"], color="#eeebe6", smooth_shading=True, name="volta_navata")
        self.plotter.add_mesh(m["arco_trionfale"], color="#f0ede6", smooth_shading=False, name="arco_trionfale")
        self.plotter.add_mesh(m["balaustra"], color="#2b2b2e", smooth_shading=False, name="balaustra")
        self.plotter.add_mesh(m["altari_marmo"], color="#d9d2c3", smooth_shading=False, name="altari_marmo")
        self.plotter.add_mesh(m["altari_tovaglia"], color="#f6f4ee", smooth_shading=False, name="altari_tovaglia")
        self._add_muro(m["walls"], "#cfc7b0", 0.28, "walls", self._centro_navata, fora=True)
        self._add_tetto(m["roof"], "#6b4a3a", 0.55, OPACITA_TETTO, "roof", self._centro_navata)
        self._add_muro(m["chapel_walls"], "#c8bda3", 0.35, "chapel_walls", self._centro_nicchia)
        self._add_muro(m["chapel_piers"], "#cfc7b0", 0.28, "chapel_piers", self._centro_nicchia)
        self._add_muro(m["apse_structure"], "#6b4a3a", 0.4, "apse_structure", self._centro_navata)
        self._add_tetto(m["tower"], "#a89a82", 0.55, 0.85, "tower", self._centro_torre)
        # il vecchio nartece (volta scura all'ingresso) non si mostra piu':
        # al suo posto la controfacciata in 3D (build_arredi_muri, IMG_9758)

        self.window_actors = {}
        for win in self.church.windows:
            mesh = m["windows"][win.name]
            opacity = WALL_OPACITY if win.group == "porta" else 0.5
            actor = self.plotter.add_mesh(
                mesh, color=GROUP_COLORS[win.group], opacity=opacity,
                name=f"win_{win.name}"
            )
            # ogni faccia della vetrata si vede solo dal suo lato (build_window_solid)
            actor.GetProperty().BackfaceCullingOn()
            self.window_actors[win.name] = actor

        p0 = np.array(self.church.local_to_enu(13, -3, 0.05))
        arrow = pv.Arrow(start=tuple(p0), direction=(0, 1, 0), scale=4.0)
        self.plotter.add_mesh(arrow, color="#ff5555", name="north_arrow")
        self.plotter.add_point_labels([tuple(p0 + np.array([0, 4.6, 0]))], ["N"],
                                       font_size=20, text_color="#ff5555",
                                       shape=None, show_points=False,
                                       name="north_label")

        self.plotter.add_light(pv.Light(light_type="scene light"))
        self.scene_light = self.plotter.renderer.lights[-1]
        self.scene_light.intensity = 0.9

        self.photo_actors = build_photo_actors(self.plotter, self.church)
        self.photos_visible = True
        self.plotter.add_on_render_callback(self._dentro_fuori, render_event=False)
        self.windows_visible = True

        # Pannello "Storia e fonti" (tasto H): testo in sovrimpressione in alto
        # a sinistra della vista 3D, nascosto all'avvio. Il testo viene da
        # storia_chiesa.py, che legge la scheda della ricerca sull'Ubaye.
        self.storia_actor = self.plotter.add_text(
            testo_storia(), position="upper_left", font_size=10,
            color=TEXT_COLOR, name="storia", font="courier",
        )
        tp = self.storia_actor.GetTextProperty()
        tp.SetBackgroundColor(pv.Color(SIDEBAR_BG).float_rgb)
        tp.SetBackgroundOpacity(0.88)
        tp.SetFrame(True)
        tp.SetFrameColor(pv.Color(ACCENT).float_rgb)
        self.storia_actor.SetVisibility(False)

    # -----------------------------------------------------------------
    # Camera (pannello 3D)
    # -----------------------------------------------------------------
    def _add_pavimento(self, mesh):
        import os
        from reference_photos import PHOTOS_DIR, PAVIMENTO_FILENAME, PAVIMENTO_PERIODO_M, PAVIMENTO_LARGHEZZA_M
        path = os.path.join(PHOTOS_DIR, PAVIMENTO_FILENAME)
        if not os.path.isfile(path):
            return self.plotter.add_mesh(mesh, color="#f1e9d8", smooth_shading=False, name="floor")
        mesh = mesh.copy()
        uv = []
        for x, y, z in mesh.points:
            u, v = self.church.enu_to_local_uv(x, y)
            # + z: le alzate dei gradini prendono la pietra invece di strisce
            uv.append((v / PAVIMENTO_LARGHEZZA_M + 0.5, (u + z) / PAVIMENTO_PERIODO_M))
        mesh.active_texture_coordinates = np.array(uv)
        tex = pv.read_texture(path)
        tex.repeat = True
        return self.plotter.add_mesh(mesh, texture=tex, smooth_shading=False, name="floor")

    @staticmethod
    def _centro_navata(church, u, v):
        return (NAVE_LENGTH_M / 2.0, 0.0, 5.0)

    @staticmethod
    def _centro_torre(church, u, v):
        from church_geometry import TOWER_U_CENTER_M, TOWER_V_CENTER_M
        return (TOWER_U_CENTER_M, TOWER_V_CENTER_M, 10.0)

    def _add_tetto(self, mesh, colore, opacita, opacita_tex, nome, centro):
        """Tetto o campanile: facce orientate verso fuori; da fuori scandole
        e intonaco, da dentro (retro) il colore di prima, senza texture."""
        mesh = orienta_verso_fuori(mesh, self.church, centro)
        for k, (parte, tex) in enumerate(tappezza(mesh, self.church)):
            if tex is None:
                continue          # facce interne o della facciata: non si disegnano (come nel sito)
            a = self.plotter.add_mesh(parte, texture=tex, opacity=opacita_tex, smooth_shading=False, name=f"{nome}_{k}")
            a.GetProperty().BackfaceCullingOn()
            b = self.plotter.add_mesh(parte.copy(), color=colore, opacity=opacita, smooth_shading=False,
                                      name=f"{nome}_{k}_retro")
            b.GetProperty().FrontfaceCullingOn()

    @staticmethod
    def _centro_nicchia(church, u, v):
        uc = min(church.chapel_u_positions(), key=lambda x: abs(x - u))
        return (uc, math.copysign(NAVE_WIDTH_M / 2.0 + CHAPEL_PROJECTION_DEPTH_M / 2.0, v), 3.0)

    def _add_muro(self, mesh, colore, opacita, nome, centro, fora=False):
        """Fronte (visto da fuori) tappezzato con intonaco e scandole veri
        (IMG_9765), retro (visto da dentro) bianco."""
        if fora:
            # due versioni: con gli archi aperti (vista da dentro, si vedono
            # le nicchie) e intera (vista da fuori); _dentro_fuori sceglie
            self._muro_intero = self._add_muro(mesh, colore, opacita, nome + "_intero", centro)
            mesh = fora_archi_cappelle(mesh, self.church)
        mesh = orienta_verso_fuori(mesh, self.church, centro)
        attori = []
        for k, (parte, tex) in enumerate(tappezza(mesh, self.church)):
            # fronte (visto da fuori): intonaco o scandole; il retro si scarta.
            # Facce che guardano dentro la chiesa: non si disegnano (sono le
            # facce delle cappelle che chiudono l'arco verso la navata)
            if tex is None:
                continue
            else:
                a = self.plotter.add_mesh(parte, texture=tex, opacity=max(opacita, OPACITA_ESTERNA),
                                          smooth_shading=False, name=f"{nome}_{k}")
            a.GetProperty().BackfaceCullingOn()
            # retro (visto da dentro): bianco, su un gemello che scarta il fronte
            b = self.plotter.add_mesh(parte.copy(), color=COLORE_INTERNO, opacity=OPACITA_INTERNA, ambient=0.6,
                                      diffuse=0.5, smooth_shading=False, name=f"{nome}_{k}_retro")
            b.GetProperty().FrontfaceCullingOn()
            attori += [a, b]
        gruppo = _Gruppo(attori)
        if fora:
            self._muro_bucato = gruppo
        return gruppo

    def _dentro_fuori(self, *_):
        """Foto delle cappelle e archi aperti solo con la camera dentro la chiesa."""
        if not hasattr(self, "photo_actors"):
            return
        dentro = camera_dentro(self.church, *self.plotter.renderers[self.plotter.renderers.loc_to_index(SCENE)].camera.position)
        if dentro == getattr(self, "_era_dentro", None) and self.photos_visible == getattr(self, "_foto_prima", None):
            return
        self._era_dentro, self._foto_prima = dentro, self.photos_visible
        for a in ATTORI_CAPPELLE:
            a.SetVisibility(dentro and self.photos_visible)
        self._muro_bucato.SetVisibility(dentro)
        self._muro_intero.SetVisibility(not dentro)

    def _center_camera(self):
        self.plotter.subplot(*SCENE)
        b = self.meshes["walls"].bounds
        cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, 3.0
        self.plotter.camera_position = [
            (cx - 30, cy - 42, 30), (cx, cy, cz), (0, 0, 1)
        ]
        self.plotter.render()

    def _view_from(self, compass_azimuth_deg, elevation_deg=20, distance=55):
        self.plotter.subplot(*SCENE)
        b = self.meshes["walls"].bounds
        cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, 4.0
        az = math.radians(compass_azimuth_deg)
        el = math.radians(elevation_deg)
        dx = distance * math.cos(el) * math.sin(az)
        dy = distance * math.cos(el) * math.cos(az)
        dz = distance * math.sin(el)
        self.plotter.camera_position = [
            (cx + dx, cy + dy, cz + dz), (cx, cy, cz), (0, 0, 1)
        ]
        self.plotter.render()

    def _view_top(self):
        self.plotter.subplot(*SCENE)
        b = self.meshes["walls"].bounds
        cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
        self.plotter.camera_position = [(cx, cy, 70), (cx, cy, 0), (0, 1, 0)]
        self.plotter.render()

    # -----------------------------------------------------------------
    # Callback slider / presets
    # -----------------------------------------------------------------
    def _on_day_change(self, value):
        self.day_of_year = int(round(value))
        self.update_scene()

    def _on_hour_change(self, value):
        self.hour = value
        self.update_scene()

    def _jump_to(self, month, day):
        date = datetime(YEAR, month, day)
        self.day_of_year = date.timetuple().tm_yday
        self._sync_sliders()
        self.update_scene()

    def _toggle_play(self):
        self._playing = not self._playing
        if self._playing:
            self._timer_id = self.plotter.add_timer_event(
                max_steps=100000, duration=80, callback=self._on_tick
            )
        else:
            # senza distruggere il timer, il vecchio continuava a
            # "ticchettare" in background (anche se _on_tick controlla
            # self._playing, e' inutile e ad ogni riavvio se ne
            # accumulava un altro) - premere Spazio non fermava mai
            # davvero l'animazione.
            timer_id = getattr(self, "_timer_id", None)
            if timer_id is not None:
                self.plotter.iren.destroy_timer(timer_id)
                self._timer_id = None

    def _toggle_photos(self):
        self.photos_visible = not self.photos_visible
        self._apply_photos_visibility()
        # tiene sincronizzato il checkbox visibile nella sidebar
        rep = getattr(self, "photos_checkbox", None)
        if rep is not None:
            rep.GetRepresentation().SetState(self.photos_visible)

    def _on_photos_checkbox(self, checked):
        self.photos_visible = checked
        self._apply_photos_visibility()

    def _apply_photos_visibility(self):
        self.plotter.subplot(*SCENE)
        for a in self.photo_actors:
            a.SetVisibility(self.photos_visible)
        self._foto_prima = None  # le foto delle cappelle seguono anche dentro/fuori
        self._dentro_fuori()
        self.plotter.render()

    def _toggle_windows(self):
        self.windows_visible = not self.windows_visible
        self._apply_windows_visibility()
        rep = getattr(self, "windows_checkbox", None)
        if rep is not None:
            rep.GetRepresentation().SetState(self.windows_visible)

    def _toggle_storia(self):
        self.storia_actor.SetVisibility(not self.storia_actor.GetVisibility())
        self.plotter.render()

    def _on_windows_checkbox(self, checked):
        self.windows_visible = checked
        self._apply_windows_visibility()

    def _apply_windows_visibility(self):
        self.plotter.subplot(*SCENE)
        for a in self.window_actors.values():
            a.SetVisibility(self.windows_visible)
        self.plotter.render()

    def _on_tick(self, step):
        if not self._playing:
            return
        self.hour += 0.15
        if self.hour >= 24.0:
            self.hour = 0.0
        self._sync_sliders()
        self.update_scene()

    # -----------------------------------------------------------------
    # Aggiornamento scena in base a data/ora correnti
    # -----------------------------------------------------------------
    def _current_datetime(self):
        date = datetime(YEAR, 1, 1) + timedelta(days=self.day_of_year - 1)
        hh = int(self.hour)
        mm = int(round((self.hour - hh) * 60))
        if mm == 60:
            mm = 0
            hh += 1
        return datetime(date.year, date.month, date.day, hh % 24, mm, tzinfo=TZ)

    def update_scene(self, render: bool = True):
        dt = self._current_datetime()
        sun = solar_position(dt, LATITUDE_DEG, LONGITUDE_DEG)

        self.plotter.subplot(*SCENE)
        for a in self.light_patch_actors:
            self.plotter.remove_actor(a, render=False)
        self.light_patch_actors = []

        lit_names = []

        if sun.is_up:
            az_rad = math.radians(sun.azimuth_deg)
            alt_rad = math.radians(sun.altitude_deg)
            sun_dir = np.array([
                math.sin(az_rad) * math.cos(alt_rad),
                math.cos(az_rad) * math.cos(alt_rad),
                math.sin(alt_rad),
            ])
            self.scene_light.position = tuple(sun_dir * 60)
            self.scene_light.focal_point = (0, 0, 0)
            self.scene_light.intensity = 0.5 + 0.6 * max(0.0, math.sin(alt_rad))

            for win in self.church.windows:
                if win.group == "porta":
                    continue  # la porta e' un solido opaco: non lascia passare luce, non cambia mai aspetto
                actor = self.window_actors[win.name]
                patches = project_window_with_walls(
                    self.church, win.local_outline(), win.wall_azimuth_deg, sun
                )
                if patches:
                    lit_names.append(win.name)
                    actor.GetProperty().SetOpacity(0.85)
                    actor.GetProperty().SetAmbient(0.45)
                    for patch in patches:
                        pts = np.array(patch.points_world)
                        if len(pts) < 3:
                            continue
                        n = len(pts)
                        face = np.array([n, *range(n)])
                        pm = pv.PolyData(pts, faces=face)
                        opacity = 0.5 if patch.surface == "pavimento" else 0.55
                        a = self.plotter.add_mesh(
                            pm, color=GROUP_COLORS[win.group], opacity=opacity,
                            name=None, render=False,
                        )
                        self.light_patch_actors.append(a)
                        # ombra opaca degli oggetti interni dentro la macchia
                        ombra = ombre_nella_macchia(pts, sun_dir, self._ombre_obb)
                        if ombra is not None:
                            self.light_patch_actors.append(self.plotter.add_mesh(
                                ombra, color="black", opacity=OMBRA_OPACITA, lighting=False, name=None, render=False))
                else:
                    actor.GetProperty().SetOpacity(0.4)
                    actor.GetProperty().SetAmbient(0.08)
        else:
            self.scene_light.intensity = 0.15
            for win in self.church.windows:
                if win.group == "porta":
                    continue
                actor = self.window_actors[win.name]
                actor.GetProperty().SetOpacity(0.4)
                actor.GetProperty().SetAmbient(0.08)

        self._update_texts(dt, sun, lit_names)
        if render:
            self.plotter.render()

    def _update_texts(self, dt, sun, lit_names):
        date_big = f"{dt.day} {MONTHS_IT[dt.month]}"
        time_big = f"{dt.hour:02d}:{dt.minute:02d}"

        self.plotter.subplot(*SIDEBAR)
        self.plotter.add_text(date_big, position=(0.06, 0.895), viewport=True,
                               font_size=26, color=TEXT_COLOR, name="big_date")
        self.plotter.add_text(time_big, position=(0.06, 0.675), viewport=True,
                               font_size=30, color=ACCENT, name="big_time")

        if sun.is_up:
            sun_str = f"Sole: azimut {sun.azimuth_deg:.1f}°\naltezza {sun.altitude_deg:.1f}°"
        else:
            sun_str = "Sole sotto l'orizzonte"
        self.plotter.add_text(sun_str, position=(0.06, 0.47), viewport=True,
                               font_size=12, color=TEXT_COLOR, name="sun_info")

        lit_str = "Vetrate illuminate:\n" + (
            "\n".join(f"  {n}" for n in lit_names) if lit_names else "  (nessuna)"
        )
        self.plotter.add_text(lit_str, position=(0.06, 0.28), viewport=True,
                               font_size=10, color=TEXT_COLOR, name="lit_list")

    # -----------------------------------------------------------------
    def show(self):
        self.plotter.show(title="Jausiers - Proiezione solare 3D")


if __name__ == "__main__":
    app = ChurchSunViewer()
    app.show()
