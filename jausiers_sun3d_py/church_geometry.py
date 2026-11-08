"""
church_geometry.py
-------------------
Modello geometrico parametrico della chiesa Saint-Nicolas-de-Myre di
Jausiers, costruito a partire dai dati estratti dal diagnostico
strutturale (planimetria 1:200, pianta di carpenteria quotata, piano
catastale con freccia nord, foto delle facciate, ELEVATION OUEST
1:100, pianta "Relevé de désordres" 1:100).

VALORI CERTI (dal documento):
- Lunghezza navata (facciata -> arco trionfale): 26.85 m
- Larghezza fuori tutto (con cappelle laterali): 14.52 m
- 4 cappelle per lato, nominate nella planimetria
- Abside poligonale a 5 lati ("chevet a 5 pans"), di cui 3 lati con
  finestra
- 3 finestre sopra il portale d'ingresso (una grande centrale ad arco
  + due laterali piu' piccole)
- Facciata d'ingresso = lato "sud" (vi e' una meridiana storica);
  coro/abside orientato verso nord-ovest (testo del report)
- Le cappelle sono NICCHIE SPORGENTI reali (vedi pianta "Relevé de
  désordres"), non semplici finestre su una parete piatta: la pianta
  non e' un rettangolo.
- Le 4 vetrate per lato viste in ELEVATION OUEST sono finestre ALTE
  (in cleristorio, sopra il tetto a spiovente delle cappelle/bas-
  côtés), non finestre basse nella nicchia della cappella.

VALORI MISURATI SU ELEVATION OUEST (scala 1/100, righello grafico
nel disegno, ~37.5 px/m nella scansione usata):
- Gronda muro alto (navata): ~12.1 m dal livello del pavimento
  interno
- Finestre di cleristorio: davanzale ~6.3 m, imposta arco ~8.5 m,
  freccia arco ~0.95 m, larghezza ~1.3 m
- Gronda del tetto basso delle cappelle/bas-côtés: ~4.8 m

VALORI STIMATI DA MISURAZIONE SUI DISEGNI (planimetria + piano
catastale con freccia nord), DA VERIFICARE:
- Azimut della facciata (normale uscente, verso cui "guarda" il
  portale): ~160 gradi (SSE). Il report descrive il coro come rivolto
  a "nord-ovest": la misurazione sui disegni da' per l'abside un
  azimut leggermente piu' vicino a NNW (~340 gradi) che a NW puro
  (315 gradi) - la differenza e' dentro il margine di errore di
  lettura di un disegno in scala 1:200/1:1000. Le tavole "ELEVATION
  OUEST"/"ELEVATION EST" per i due lati lunghi suggeriscono che i
  disegnatori arrotondano ai punti cardinali piu' vicini per comodita'
  di etichettatura, non necessariamente l'azimut esatto.

VALORI NON TROVATI NEL DOCUMENTO (placeholder ragionevoli, DA
SOSTITUIRE con misure reali):
- Dimensioni precise delle finestre dell'abside e della facciata
  (nessuna elevazione dedicata trovata per queste; stimate per
  coerenza proporzionale con le finestre di cleristorio misurate)
- Sagoma esatta dell'abside (approssimata come pentagono)
- Profondita'/larghezza esatte delle nicchie delle cappelle (stimate)

Tutte le quote "stimate" sono raccolte in cima al file per essere
modificate facilmente senza toccare la logica.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# =====================================================================
# 1. PARAMETRI MODIFICABILI
# =====================================================================

# --- Posizione geografica (WGS84) ---
LATITUDE_DEG = 44.41978
LONGITUDE_DEG = 6.73401
ELEVATION_M = 1240.0          # quota approssimativa di Jausiers, m s.l.m.
TIMEZONE_NAME = "Europe/Paris"

# --- Orientamento dell'edificio ---
# Azimut (da Nord, orario) della normale uscente della FACCIATA
# (direzione verso cui guarda chi esce dal portale principale).
# STIMATO dai disegni (vedi docstring sopra). Modificabile.
FACADE_AZIMUTH_DEG = 160.0

# --- Dimensioni principali: MISURATE sulla pianta "Relevé de
#     désordres - Plan des abords" (Michel Trubert ACMH, 1/200,
#     09/2016) - quote colorate dirette, non piu' stimate. ---
NAVE_LENGTH_M = 26.52     # facciata -> arco trionfale (asse navata) [verde]
NAVE_WIDTH_M = 13.37      # larghezza fuori tutto, incl. cappelle [rosso]
N_CHAPELS_PER_SIDE = 4

# --- Altezze principali: MISURATE su Elevation Sud/Est (Michel
#     Trubert ACMH, 1/100). WALL_HEIGHT_M gia' confermato (rosso
#     Elevation Sud = 16.55, scarto <0.1% dal valore precedente).
#     ROOF_RIDGE_RISE_M e CHAPEL_ROOF_HEIGHT_M corretti sulla base
#     delle quote colorate della stessa elevazione. ---
WALL_HEIGHT_M = 16.56          # pavimento -> gronda muro alto (navata)
CHAPEL_ROOF_HEIGHT_M = 9.64    # pavimento -> gronda tetto basso cappelle/bas-côtés [magenta, Elevation Sud]
# Risalita del tetto basso delle cappelle, dalla gronda (esterno)
# fino al punto in cui il muro esterno della cappella incontra il
# muro alto della navata (dove il tetto basso "si ferma") - MISURATA
# su Elevation Sud (Michel Trubert ACMH, 1/100) [arancione, indicato
# dalla freccia ciano, 1.31 m]. Sostituisce una stima precedente (1.2 m).
CHAPEL_ROOF_PITCH_RISE_M = 1.31
ROOF_RIDGE_RISE_M = 6.57       # sopra WALL_HEIGHT_M, sommita' del tetto della navata [ciano, Elevation Sud]

# --- Nicchie delle cappelle: MISURATE sulla pianta "Relevé de
#     désordres" (vedi sopra). CHAPEL_PROJECTION_DEPTH_M corretto
#     drasticamente rispetto alla stima precedente (0.38 m): l'analisi
#     pixel del nuovo documento mostra chiaramente una nicchia molto
#     piu' profonda (viola = i due fianchi della nicchia, non
#     l'arretramento residuo come ipotizzato prima). ---
CHAPEL_PROJECTION_DEPTH_M = 2.19   # sporgenza oltre il filo della navata [viola]
CHAPEL_PROJECTION_WIDTH_M = 4.82   # larghezza della nicchia in pianta [arancione]

# --- Arco d'ingresso delle cappelle: MISURATO sulle foto raddrizzate
#     (foto_da_video.py), uguale nelle cappelle Ovest 1 ed Est 2:
#     intradosso a tutto sesto, raggio 2.13 m (largo 4.26 m), imposta a
#     5.39 m, chiave a 7.52 m dal pavimento. Usato per dare profondita'
#     alle cappelle (nicchia: fondo, fianchi, volta - reference_photos.py). ---
CHAPEL_ARCH_RADIUS_M = 2.13
CHAPEL_ARCH_SPRING_M = 5.39

# --- Gradini del presbiterio: tre gradini davanti all'arco trionfale
#     (u da NAVE_LENGTH_M - 3*pedata a NAVE_LENGTH_M), larghi quanto
#     l'apertura dell'abside (|v| <= Wh - APSE_RECESS_M); l'abside e'
#     rialzata di GRADINI_N * GRADINO_ALZATA_M. Alzata e pedata STIMATE
#     (misure tipiche), da verificare. ---
GRADINI_N = 3
GRADINO_ALZATA_M = 0.16
GRADINO_PEDATA_M = 0.32

# --- Arredi (dalle foto IMG_9757/IMG_9759, misure STIMATE):
#     banchi in due file ai lati del corridoio centrale, dal fondo
#     della chiesa fino a ~1.5 m dai gradini; altare (tavolo con
#     tovaglia bianca) ~1 m dietro la balaustra in cima ai gradini
#     (l'unico altare: la pala di fondo resta quella della foto). ---
BANCHI_U_INIZIO_M = 5.0          # primo banco (bordo davanti del sedile)
BANCHI_PASSO_M = 0.95            # distanza fra le file
BANCHI_V_CORRIDOIO_M = 1.15      # meta' larghezza del corridoio centrale
BANCHI_V_ESTERNO_M = 5.0         # estremita' verso le cappelle (corridoio laterale ~1.7 m)
ALTARE_U_CENTRO_M = NAVE_LENGTH_M + 2.4
ALTARE_LARGHEZZA_M = 2.2
ALTARE_PROFONDITA_M = 0.9
ALTARE_ALTEZZA_M = 0.95
# balaustra in ferro battuto in cima ai gradini, larga quanto l'apertura
# dell'abside, con un varco al centro (stimato) per passare
BALAUSTRA_U_M = NAVE_LENGTH_M + 0.15
BALAUSTRA_ALTEZZA_M = 0.9
BALAUSTRA_VARCO_M = 1.2
# armadi in legno del riscaldamento, ai due lati dell'ingresso dell'abside,
# subito dietro la balaustra (griglia a lamelle in alto, verso la navata)
RISCALDAMENTO_U_M = NAVE_LENGTH_M + 0.6        # centro
RISCALDAMENTO_V_M = 4.6                         # centro, per lato
RISCALDAMENTO_LARGHEZZA_M = 1.4
RISCALDAMENTO_PROFONDITA_M = 0.6
RISCALDAMENTO_ALTEZZA_M = 2.9
# pulpito in legno sul pilastro fra la 3a e la 4a cappella a sinistra
# entrando (lato Ovest, v = +Wh), da IMG_9758 a 24 s; quote stimate
# confrontandolo con l'arco della cappella (imposta a 5.39 m)
PULPITO_FRA_CAPPELLE = (2, 3)        # indici delle cappelle (0 = vicino all'ingresso)
PULPITO_RAGGIO_M = 0.6               # cassa ottagonale
PULPITO_PIANO_M = 2.2                # fondo della cassa
PULPITO_PARAPETTO_M = 1.1            # altezza della cassa
PULPITO_BALDACCHINO_M = 5.0          # sotto del baldacchino
PULPITO_CIMA_M = 6.6                 # punta della piramide del baldacchino
# consolle dell'organo (legno chiaro), a sinistra entrando contro il muro
# Ovest, fra l'ultima fila di banchi e i gradini (IMG_9759, IMG_9758)
ORGANO_U_M = NAVE_LENGTH_M - GRADINI_N * GRADINO_PEDATA_M - 1.1   # centro
ORGANO_V_M = 4.3                     # centro
ORGANO_LARGHEZZA_M = 1.4             # lungo v (tastiera)
ORGANO_PROFONDITA_M = 0.65
ORGANO_ALTEZZA_M = 0.95
# cornicione interno (trabeazione in stucco) tutto intorno, sopra gli
# archi delle cappelle e lungo l'abside (IMG_9755): architrave a fasce,
# fregio, dentelli, mensoline e cornice sporgente. Quote stimate dalla
# foto dell'abside (la trabeazione vi sta fra ~8.9 e ~10.4 m).
CORNICIONE_BASE_M = 8.9
CORNICIONE_CIMA_M = 10.4
CORNICIONE_SPORGENZA_M = 0.62
# volta dell'abside a ombrello (IMG_9757, ultimo fotogramma): costoloni
# dagli angoli del pentagono (sul cornicione) fino alla chiave dietro
# l'arco trionfale; sopra ogni finestra una lunetta (la volta vi parte da
# VOLTA_ABSIDE_LUNETTE_M, sopra l'arco della finestra). Quote stimate.
VOLTA_ABSIDE_CHIAVE_M = 15.0
VOLTA_ABSIDE_LUNETTE_M = 14.2
# la chiave (rosetta dove convergono i costoloni, IMG_9757 a 10 s) sta
# sopra il centro dell'abside, non dietro l'arco trionfale: la volta e' un
# ombrello dal bordo (muro dell'abside con le lunette, poi l'arco
# trionfale) fino alla chiave. Suddivisione del bordo e dei meridiani
# (la stessa nella texture, volta_da_video.py).
VOLTA_ABSIDE_NT = 14        # punti per lato del pentagono
VOLTA_ABSIDE_NA = 24        # punti lungo l'arco trionfale
VOLTA_ABSIDE_NM = 14        # punti lungo ogni meridiano
# volta della navata: a botte dal cornicione al colmo, con una lunetta
# sopra ogni finestra alta (centrate sulle cappelle). Quote stimate.
VOLTA_NAVATA_CHIAVE_M = 16.3
VOLTA_NAVATA_LUNETTE_M = 14.2
VOLTA_NAVATA_LUNETTA_LARGA_M = 3.2
# lampadario di cristallo dell'abside (video IMG_9739): DOPPIO, appeso con
# una catena alla chiave della volta. Dall'alto: corona di cristallo,
# anello dorato con le candele, coppa di cristalli a gradini, sfera di
# vetro, fuso di fili di cristallo, secondo anello di candele, seconda
# coppa a gradini. L'anello basso e' all'altezza delle statue in cima alla
# pala. Misure STIMATE dalle proporzioni nel video.
LAMPADARIO_ALTO_M = 12.1
LAMPADARIO_BASSO_M = 8.8
LAMPADARIO_RAGGIO_BRACCI_M = 0.65        # anello alto
LAMPADARIO_RAGGIO_BRACCI_BASSO_M = 0.57  # anello basso
LAMPADARIO_N_BRACCI = 12
# tre lampadari singoli sull'asse della navata (foto della navata): uno
# sopra il primo pilastro, uno a meta' navata, uno davanti all'arco trionfale; appesi al colmo
# della volta, all'altezza delle finestre alte. Stimati.
LAMPADARI_NAVATA_U_M = (7.2, 15.9, 24.6)
LAMPADARIO_NAVATA_ALTO_M = 13.9
LAMPADARIO_NAVATA_BASSO_M = 11.2

# --- Controfacciata (IMG_9758, 15-17 s; misure stimate in proporzione al
#     cornicione, largo quanto la navata). v > 0 = Ovest, a destra guardando
#     la controfacciata da dentro. ---
BUSSOLA_LARGHEZZA_M = 5.6       # struttura in muratura attorno al portone
BUSSOLA_PROFONDITA_M = 1.2
BUSSOLA_ALTEZZA_M = 5.5         # cornice; pinnacoli e cupoletta sopra
PORTONE_LARGHEZZA_M = 2.6
PORTONE_ALTEZZA_M = 4.8         # alla chiave dell'arco
# --- Lesene fra le cappelle (stesse misure su tutti i pilastri) ---
LESENA_LARGHEZZA_M = 1.0
LESENA_SPORGENZA_M = 0.12
LESENA_ZOCCOLO_M = 1.0
CROCE_CONSACRAZIONE_M = 3.37    # quota del centro (misurata nelle foto)


# --- Due gradini all'ingresso di ogni cappella: il primo in navata
#     davanti all'arco, il secondo nello spessore dell'arco; il pavimento
#     della cappella e' a 2 * CAPPELLA_GRADINO_ALZATA_M. Larghi quanto
#     l'arco (2 * CHAPEL_ARCH_RADIUS_M). Misure STIMATE. ---
CAPPELLA_GRADINI_N = 2
CAPPELLA_GRADINO_ALZATA_M = 0.15
CAPPELLA_GRADINO_PEDATA_M = 0.30

# --- Altari delle cappelle: mensa contro il fondo della nicchia, tovaglia
#     bianca, gradino sopra la mensa (verso il fondo). Colori presi dalle
#     foto (parte bassa del fondo di ogni nicchia, fondo_da_foto.py /
#     foto_da_video.py): (nome, lato, indice, colore davanti, colore gradino).
#     Misure STIMATE. ---
ALTARE_CAPPELLA_LARGHEZZA_M = 2.0
ALTARE_CAPPELLA_PROFONDITA_M = 0.75
ALTARE_CAPPELLA_ALTEZZA_M = 0.95
ALTARI_CAPPELLE = [
    ("cappella_ovest_1", +1, 0, 0xe8e4dc, 0xa79c91),   # bianco: la tovaglia scende fino a terra; gradino di marmo chiaro
    ("cappella_ovest_2", +1, 1, 0x8c6f52, 0xa07838),   # Sant'Antonio: paliotto a piastrelle sotto il pizzo; gradino di legno dorato
    ("cappella_ovest_3", +1, 2, 0x466e78, 0xaf9150),   # paliotto verde-azzurro; gradino dorato
    ("cappella_ovest_4", +1, 3, 0x867f71, 0x867f71),   # altare non visibile nelle foto (banchi): pietra grigia
    ("cappella_est_1", -1, 0, 0xa58c5a, 0x8a8270),   # marmo giallo e grigio come la pala
    ("cappella_est_2", -1, 1, 0x344e8c, 0x966e46),   # paliotto blu (I M J); gradino di marmo rosso e oro
    ("cappella_est_3", -1, 2, 0x28231e, 0xaa8c50),   # paliotto nero e oro (REQUIESCANT IN PACE); gradino dorato
    ("cappella_est_4", -1, 3, 0x464b41, 0xb4965a),   # paliotto di marmo verde scuro; gradino dorato
]


def quota_cappella(u: float, v: float) -> float | None:
    """Quota del pavimento se (u, v) e' sui gradini o dentro una cappella,
    altrimenti None."""
    wh, av = NAVE_WIDTH_M / 2.0, abs(v)
    if av < wh - CAPPELLA_GRADINO_PEDATA_M or av > wh + CHAPEL_PROJECTION_DEPTH_M:
        return None
    campata = (NAVE_LENGTH_M - 2 * CHAPEL_ROW_MARGIN_M) / N_CHAPELS_PER_SIDE
    for i in range(N_CHAPELS_PER_SIDE):
        du = abs(u - (CHAPEL_ROW_MARGIN_M + (i + 0.5) * campata))
        piano = CAPPELLA_GRADINI_N * CAPPELLA_GRADINO_ALZATA_M
        if av >= wh + CAPPELLA_GRADINO_PEDATA_M and du <= CHAPEL_PROJECTION_WIDTH_M / 2:
            return piano
        if du <= CHAPEL_ARCH_RADIUS_M:
            return piano if av >= wh else CAPPELLA_GRADINO_ALZATA_M
    return None


def banchi_scatole(church) -> list[tuple[float, float, float, float, float, float]]:
    """Le scatole (u0, u1, v0, v1, w0, w1) dei banchi: sedile, schienale
    (verso la facciata: si guarda l'abside), mensola sotto e due fianchi.
    Dal fondo fino a ~1.5 m dal primo gradino. Servono alla mesh e alla
    luce delle vetrate che cade sui banchi."""
    u_fine = church.nave_length_m - GRADINI_N * GRADINO_PEDATA_M - 1.5
    out = []
    u = BANCHI_U_INIZIO_M
    while u + 0.45 <= u_fine:
        for lato in (1.0, -1.0):
            a, b = sorted((lato * BANCHI_V_CORRIDOIO_M, lato * BANCHI_V_ESTERNO_M))
            out.append((u, u + 0.40, a, b, 0.42, 0.46))              # sedile
            out.append((u - 0.04, u, a, b, 0.46, 0.92))              # schienale
            out.append((u + 0.10, u + 0.40, a, b, 0.10, 0.14))       # mensola sotto
            for v in (a, b):                                         # fianchi
                out.append((u - 0.06, u + 0.45, v - 0.03, v + 0.03, 0.0, 0.95))
        u += BANCHI_PASSO_M
    return out


def quota_pavimento(u: float, v: float) -> float:
    """Quota del pavimento in (u, v): 0 in navata, i gradini davanti
    all'arco trionfale, GRADINI_N * GRADINO_ALZATA_M nell'abside, i
    gradini e il piano delle cappelle."""
    qc = quota_cappella(u, v)
    if qc is not None:
        return qc
    if abs(v) > NAVE_WIDTH_M / 2.0 - APSE_RECESS_M:
        return 0.0
    u0 = NAVE_LENGTH_M - GRADINI_N * GRADINO_PEDATA_M
    if u < u0:
        return 0.0
    if u >= NAVE_LENGTH_M:
        return GRADINI_N * GRADINO_ALZATA_M
    return (math.floor((u - u0) / GRADINO_PEDATA_M) + 1) * GRADINO_ALZATA_M

# --- Margine navata prima/dopo le cappelle: MISURATO (marrone,
#     ~1.10 m) - sostituisce la stima proporzionale precedente
#     (6% della lunghezza navata). Vedi ChurchModel.chapel_u_positions(). ---
CHAPEL_ROW_MARGIN_M = 1.10

# --- Abside: VERO PENTAGONO A 5 LATI, ciascuno con una finestra
#     (confermato dall'utente e verificato per via indipendente sulla
#     pianta "Relevé de désordres" con analisi automatica dei pixel
#     delle 5 zone evidenziate: non e' un esagono a parete piatta come
#     ipotizzato in una versione precedente - quell'ipotesi nasceva da
#     un'errata lettura del punto di convergenza delle nervature della
#     volta, "Fig.12", che e' il colmo della volta a raggiera e non un
#     vertice di muratura).
#
#     C'e' inoltre una RIENTRANZA: l'abside non e' a filo con la
#     navata, ma arretra di APSE_RECESS_M su ciascun lato prima che
#     inizi il pentagono vero e proprio - ora MISURATA direttamente
#     (nero, ~1.31 m), non piu' stimata dall'annotazione generica
#     dell'utente (~2.6 m).
#
#     I 5 azimut delle pareti restano quelli misurati in precedenza
#     (regressione lineare sui pixel, calibrati sull'azimut noto delle
#     pareti di cappella) - non sono cambiati con questo documento.
#     Le LUNGHEZZE dei 5 lati sono MISURATE direttamente (giallo 5.48
#     per i lati corti, magenta 4.38 per i pannelli smussati, ciano
#     6.58 per il pannello di fondo) MA non chiudono esattamente il
#     pentagono insieme alla NAVE_WIDTH_M/APSE_RECESS_M misurate
#     separatamente (scarto di chiusura 2.72 m se usate alla lettera -
#     normale per una rilevazione sul campo con quote ridondanti che
#     non tornano al millimetro).
#
#     CORRETTE risolvendo un sistema lineare 2x2 (chiusura esatta sia
#     in u che in v) che lascia i lati corti al valore misurato esatto
#     (5.48, non influiscono sulla chiusura per simmetria) e i due
#     pannelli smussati quasi al valore misurato (4.391 vs 4.38
#     misurato, scarto 0.3%). L'AGGIUSTAMENTO RICADE QUASI INTERAMENTE
#     sul pannello di fondo: 3.84 m contro 6.58 m misurato (-42%) - uno
#     scarto grande, non spiegato solo da imprecisione di misura;
#     probabile errore di lettura del pannello di fondo su questo
#     documento o incoerenza fra le quote della pianta. Da verificare
#     con l'utente; nel frattempo usata la soluzione a chiusura esatta
#     (scarto residuo <0.001 mm) per garantire un modello 3D valido. ---
APSE_RECESS_M = 1.31                 # arretramento rispetto al filo navata, per lato [nero]
APSE_FACET_AZIMUTHS_DEG = [250.0, 301.4, 340.9, 17.6, 70.0]  # misurati (invariati)
APSE_FACET_LENGTHS_M = [5.48, 4.3912, 3.8396, 4.3912, 5.48]  # chiusura esatta (vedi sopra) - pannello di fondo da verificare

# --- Vetrate di cleristorio (cappelle): MISURATE su Elevation Sud
#     (Michel Trubert ACMH, 1/100) - base(larghezza)=1.10, altezza
#     totale=2.30, davanzale a 11.18 m. head_m e arch_rise_m derivati
#     assumendo arco a tutto sesto (freccia = base/2 = 0.55) - non
#     quotati direttamente, da verificare. ---
CHAPEL_WINDOW_WIDTH_M = 1.10
CHAPEL_WINDOW_SILL_M = 11.18      # altezza davanzale dal pavimento
CHAPEL_WINDOW_HEAD_M = 12.93      # altezza dell'imposta dell'arco
CHAPEL_WINDOW_ARCH_RISE_M = 0.55  # freccia dell'arco a tutto sesto (ipotesi)

# Arretramento della vetrata rispetto al filo esterno del muro (non
# a filo, ma incassata in una strombatura profonda) - MISURATO su
# Elevation Sud (Michel Trubert ACMH, 1/100) [arancione, 1.31 m].
CHAPEL_WINDOW_RECESS_M = 1.31

# --- Vetrate abside: MISURATE su Elevation Sud (Michel Trubert ACMH,
#     1/100). 4 delle 5 vetrate = stesse dimensioni delle cappelle
#     (1.10 x 2.30, davanzale 11.18 m). La QUINTA (lato Est, adiacente
#     al campanile "CLOCHER" - vedi pianta "Relevé de désordres") ha
#     dimensioni diverse: 1.29 x 2.90. head_m/arch_rise_m derivati
#     come sopra (arco a tutto sesto, non quotati direttamente). ---
APSE_WINDOW_WIDTH_M = 1.10
APSE_WINDOW_SILL_M = 11.18
APSE_WINDOW_HEAD_M = 12.93
APSE_WINDOW_ARCH_RISE_M = 0.55

# vetrata absidale lato campanile ("Abside - lato corto Est"): unica
# con dimensioni diverse dalle altre 4
APSE_WINDOW_CLOCHER_WIDTH_M = 1.29
APSE_WINDOW_CLOCHER_SILL_M = 11.18
APSE_WINDOW_CLOCHER_HEAD_M = 13.435
APSE_WINDOW_CLOCHER_ARCH_RISE_M = 0.645

# --- Vetrate facciata: MISURATE su Elevation Sud (Michel Trubert
#     ACMH, 1/100). Davanzale a 13.37 m per tutte e 3. head_m/
#     arch_rise_m derivati come sopra (arco a tutto sesto, non
#     quotati direttamente). ---
FACADE_CENTRAL_WINDOW_WIDTH_M = 1.53
FACADE_CENTRAL_WINDOW_SILL_M = 13.37
FACADE_CENTRAL_WINDOW_HEAD_M = 15.235
FACADE_CENTRAL_WINDOW_ARCH_RISE_M = 0.765

FACADE_SIDE_WINDOW_WIDTH_M = 0.99
FACADE_SIDE_WINDOW_SILL_M = 13.37
FACADE_SIDE_WINDOW_HEAD_M = 14.625
FACADE_SIDE_WINDOW_ARCH_RISE_M = 0.495
FACADE_SIDE_WINDOW_OFFSET_M = 1.93  # distanza dall'asse: dalla foto frontale della facciata a scala
                                    # uniforme (1.93; da dentro, vetrate_da_video.py: ~2.1). Era 1.45, stimata

# --- Portale d'ingresso: MISURATO sulla pianta "Elevation Sud"
#     (Michel Trubert ACMH, scala 1/100) - vedi quote colorate.
#     width_m = 3.30 (blu, misurato); l'ampiezza in pixel non
#     corrispondeva esattamente all'evidenziazione blu (che sembra
#     tracciare solo l'anta lignea, non l'intero portale in pietra) -
#     usato comunque il valore quotato come autoritativo.
#     head_m e arch_rise_m NON sono quotati direttamente: derivati
#     dall'altezza totale misurata (verde, 4.38 m dal suolo alla base
#     del rosone) assumendo un arco a tutto sesto (freccia = meta'
#     larghezza) - ipotesi ragionevole ma non confermata dal disegno,
#     da verificare. Modellato come le vetrate (stessa classe Window),
#     senza foto/texture - solo la mesh colorata piena. ---
FACADE_DOOR_WIDTH_M = 3.30
FACADE_DOOR_SILL_M = 0.0
FACADE_DOOR_ARCH_RISE_M = 1.65   # = width/2, ipotesi arco a tutto sesto
FACADE_DOOR_HEAD_M = 2.73        # = 4.38 (verde) - 1.65 (freccia ipotizzata)

# --- Nartece/vestibolo coperto all'ingresso: struttura interna
#     SOLIDA e OPACA (non lascia passare luce), MISURATA sulla pianta
#     "Relevé de désordres" (Michel Trubert ACMH, 1/200) - quote
#     colorate vicino al portale. Soffitto curvo (a volta), alto
#     6.58 m dove incontra il muro di facciata, che scende come un
#     profilo curvo (approssimato con un quarto di coseno, non una
#     vera equazione di cerchio - "semicerchio" usato in senso
#     descrittivo) fino a 4.49 m alla distanza di 2.63 m dal muro
#     [rosso = profondita']. Larghezza 4.38 m [verde], centrata
#     sull'asse della navata come il portale sottostante. ---
NARTHEX_WIDTH_M = 4.38
NARTHEX_DEPTH_M = 2.63
NARTHEX_HEIGHT_AT_WALL_M = 6.58
NARTHEX_HEIGHT_AT_EDGE_M = 4.49

# --- Campanile: posizione sul lato "Ovest" del modello (quello di
#     "Cappella Notre-Dame-du-Rosaire") - CORRETTO dall'utente, che
#     aveva prima confermato la lettura pixel dell'etichetta "CLOCHER"
#     sulla pianta (adiacente al lato "Est"), poi segnalato un errore
#     e indicato il lato opposto come quello corretto.
#     Impronta (~5.4 x 4.6 m) e posizione (u,v) STIMATE dalla
#     posizione in pixel del rettangolo "CLOCHER" relativa allo
#     spigolo di rientranza absidale (u=NAVE_LENGTH_M, v=-(Wh-recess)),
#     non da una quota esplicita - precisione minore rispetto alle
#     altre misure di questo modello.
#     Altezze MISURATE su "Elevation Est" (Michel Trubert ACMH, 1/100):
#     corpo (base -> gronda) = 19.85 m [arancione], sommita' guglia
#     (base -> punta) = 35.54 m [rosso] -> guglia alta 15.69 m
#     [ciano, = 35.54-19.85, coerenza confermata]. Dettagli minori
#     (cornice/lanterna: verde 4.15 m, magenta 2.31 m) NON modellati
#     singolarmente - la guglia e' semplificata come piramide unica. ---
TOWER_U_CENTER_M = 29.2       # stimato (vedi sopra)
TOWER_V_CENTER_M = 7.7        # stimato (vedi sopra) - lato "Ovest" del modello (corretto dall'utente)
TOWER_WIDTH_U_M = 5.4         # impronta lungo l'asse navata, stimata
TOWER_WIDTH_V_M = 4.6         # impronta trasversale, stimata
TOWER_BODY_HEIGHT_M = 19.85   # base -> gronda del corpo [arancione]
TOWER_SPIRE_HEIGHT_M = 15.69  # gronda -> punta guglia [ciano]

# --- Abside: altezza esterna e tetto MISURATI su "Elevation Est"
#     (Michel Trubert ACMH, 1/100), DISTINTI dall'altezza della navata
#     (WALL_HEIGHT_M): l'abside ha un proprio muro + tetto separati,
#     a FALDA UNICA (non un padiglione - vedi build_apse_wall_structure
#     in church_mesh.py): sale da APSE_EXTERNAL_HEIGHT_M (bordo esterno
#     del pentagono, punto piu' lontano dalla navata) fino a
#     APSE_EXTERNAL_HEIGHT_M+APSE_ROOF_RIDGE_RISE_M (dove incontra il
#     muro alto della navata).
#
#     APSE_EXTERNAL_HEIGHT_M = punto BASSO della falda, al bordo
#     esterno del pentagono [ciano, 15.69 m].
#     APSE_ROOF_RIDGE_RISE_M = risalita fino al punto ALTO, dove la
#     falda incontra il muro alto della navata - derivato dall'utente
#     come (altezza colmo tetto navata) - (differenza blu) =
#     23.38 - 3.53 = 19.85 m; risalita = 19.85 - 15.69 = 4.16 m.
#     Coerente con la stima precedente (verde, 4.15 m) - la doppia via
#     di calcolo si conferma reciprocamente entro 1 cm. ---
APSE_EXTERNAL_HEIGHT_M = 15.69
APSE_ROOF_RIDGE_RISE_M = 4.16


# =====================================================================
# 2. STRUTTURE DATI
# =====================================================================

@dataclass(frozen=True)
class Window:
    """
    Una vetrata, descritta nel sistema di coordinate LOCALE
    dell'edificio (u = lungo la navata, dalla facciata [u=0] verso
    l'abside; v = trasversale; w = verticale, pavimento a w=0).

    - wall_point_uv: punto della parete su cui e' centrata la vetrata
      (proiezione in pianta del centro della base della vetrata),
      in coordinate (u, v).
    - wall_azimuth_deg: azimut (bussola) della normale uscente del
      muro in quel punto (permette pareti non parallele, es. abside).
    - width_m, sill_m, head_m: geometria della parte rettangolare.
    - arch_rise_m: se >0, la vetrata ha una sommita' ad arco (a tutto
      sesto/ogivale semplificato) di freccia pari a questo valore,
      sopra head_m.
    """
    name: str
    group: str  # "cappella", "abside", "facciata"
    wall_point_uv: tuple[float, float]
    wall_azimuth_deg: float
    width_m: float
    sill_m: float
    head_m: float
    arch_rise_m: float = 0.0
    n_arch_points: int = 8

    def local_outline(self) -> list[tuple[float, float, float]]:
        """
        Restituisce i punti (u, v, w) del contorno della vetrata
        (rettangolo + eventuale arco), nel piano della parete.

        IMPORTANTE: `wall_azimuth_deg` e' un azimut di BUSSOLA (sistema
        mondo), mentre questo metodo lavora nel sistema LOCALE (u,v)
        dell'edificio - i due sistemi sono ruotati fra loro di
        FACADE_AZIMUTH_DEG. La direzione "lungo la parete" va quindi
        calcolata proiettando la direzione mondo sugli assi locali
        (stessa trasformazione usata da ChurchModel.enu_to_local_uv),
        NON applicando seno/coseno grezzi all'azimut mondiale come se
        fosse gia' un angolo locale (errore presente in una versione
        precedente: funzionava solo per la facciata, per coincidenza
        geometrica, e produceva vetrate mal orientate - quindi mai
        illuminate - su tutte le altre pareti).
        """
        u0, v0 = self.wall_point_uv
        half = self.width_m / 2.0

        # direzione "lungo la parete" nel sistema locale (u,v):
        # ruoto la normale (azimut mondo) di -90 gradi e proietto sugli
        # assi locali u_hat/v_hat (stessa rotazione rigida usata in
        # tutto il resto del modello, definita da FACADE_AZIMUTH_DEG).
        tangent_world_rad = math.radians(self.wall_azimuth_deg - 90.0)
        az_u = math.radians((FACADE_AZIMUTH_DEG + 180.0) % 360.0)
        az_v = math.radians((FACADE_AZIMUTH_DEG + 90.0) % 360.0)
        u_hat = (math.sin(az_u), math.cos(az_u))
        v_hat = (math.sin(az_v), math.cos(az_v))
        east = math.sin(tangent_world_rad)
        north = math.cos(tangent_world_rad)
        along = (east * u_hat[0] + north * u_hat[1], east * v_hat[0] + north * v_hat[1])

        pts: list[tuple[float, float, float]] = []
        left = (u0 - along[0] * half, v0 - along[1] * half)
        right = (u0 + along[0] * half, v0 + along[1] * half)

        pts.append((left[0], left[1], self.sill_m))
        pts.append((right[0], right[1], self.sill_m))
        pts.append((right[0], right[1], self.head_m))

        if self.arch_rise_m > 0:
            for i in range(1, self.n_arch_points):
                t = math.pi * i / self.n_arch_points
                x = math.cos(t) * half
                y = math.sin(t) * self.arch_rise_m
                pu = u0 + along[0] * x
                pv = v0 + along[1] * x
                pts.append((pu, pv, self.head_m + y))

        pts.append((left[0], left[1], self.head_m))
        return pts

    def local_outline_with_uv(self) -> list[tuple[tuple[float, float, float], tuple[float, float]]]:
        """
        Come local_outline(), ma ritorna anche la coordinata texture
        (u_tex, v_tex) in [0,1]x[0,1] per ciascun punto - per applicare
        una foto reale sulla vetrata invece di un colore piatto.
        u_tex=0 al bordo sinistro, 1 al bordo destro; v_tex=0 al
        davanzale, 1 alla sommita' dell'arco (o dell'imposta se non
        c'e' arco).
        """
        outline = self.local_outline()
        top = self.head_m + self.arch_rise_m
        half = self.width_m / 2.0

        u0, v0 = self.wall_point_uv
        tangent_world_rad = math.radians(self.wall_azimuth_deg - 90.0)
        az_u = math.radians((FACADE_AZIMUTH_DEG + 180.0) % 360.0)
        az_v = math.radians((FACADE_AZIMUTH_DEG + 90.0) % 360.0)
        u_hat = (math.sin(az_u), math.cos(az_u))
        v_hat = (math.sin(az_v), math.cos(az_v))
        east = math.sin(tangent_world_rad)
        north = math.cos(tangent_world_rad)
        along = (east * u_hat[0] + north * u_hat[1], east * v_hat[0] + north * v_hat[1])
        mag = math.hypot(*along) or 1.0

        result = []
        for (pu, pv, pw) in outline:
            # posizione lungo la parete, ri-derivata proiettando sul
            # versore "along" (stesso usato per costruire l'outline)
            x_along = ((pu - u0) * along[0] + (pv - v0) * along[1]) / (mag * mag)
            u_tex = (x_along + half) / (2 * half) if half > 0 else 0.5
            v_tex = (pw - self.sill_m) / (top - self.sill_m) if top > self.sill_m else 0.0
            result.append(((pu, pv, pw), (u_tex, v_tex)))
        return result


@dataclass(frozen=True)
class ChurchModel:
    facade_azimuth_deg: float = FACADE_AZIMUTH_DEG
    nave_length_m: float = NAVE_LENGTH_M
    nave_width_m: float = NAVE_WIDTH_M
    windows: list[Window] = field(default_factory=list)

    def local_to_enu(self, u: float, v: float, w: float) -> tuple[float, float, float]:
        az_u = math.radians((self.facade_azimuth_deg + 180.0) % 360.0)
        az_v = math.radians((self.facade_azimuth_deg + 90.0) % 360.0)
        u_hat = (math.sin(az_u), math.cos(az_u))
        v_hat = (math.sin(az_v), math.cos(az_v))
        east = u * u_hat[0] + v * v_hat[0]
        north = u * u_hat[1] + v * v_hat[1]
        return (east, north, w)

    def window_enu_outline(self, win: Window) -> list[tuple[float, float, float]]:
        return [self.local_to_enu(u, v, w) for (u, v, w) in win.local_outline()]

    def enu_to_local_uv(self, east: float, north: float) -> tuple[float, float]:
        az_u = math.radians((self.facade_azimuth_deg + 180.0) % 360.0)
        az_v = math.radians((self.facade_azimuth_deg + 90.0) % 360.0)
        u_hat = (math.sin(az_u), math.cos(az_u))
        v_hat = (math.sin(az_v), math.cos(az_v))
        u = east * u_hat[0] + north * u_hat[1]
        v = east * v_hat[0] + north * v_hat[1]
        return (u, v)

    def chapel_u_positions(self) -> list[float]:
        n = N_CHAPELS_PER_SIDE
        margin = CHAPEL_ROW_MARGIN_M  # misurato (marrone, ~1.10 m) - vedi costante
        usable = self.nave_length_m - 2 * margin
        return [margin + usable * (i + 0.5) / n for i in range(n)]

    def segment_outward_azimuth(self, p1_uv: tuple[float, float], p2_uv: tuple[float, float]) -> float:
        """
        Azimut di bussola della normale USCENTE di un segmento di
        parete (da p1 a p2, coordinate locali u,v), verificato in modo
        indipendente (non assunto): fra le due perpendicolari
        possibili al segmento, sceglie quella che punta LONTANO dal
        centro della navata (u=nave_length/2, v=0), che per pareti
        perimetrali e' sempre il lato esterno.
        """
        mx, my = (p1_uv[0] + p2_uv[0]) / 2.0, (p1_uv[1] + p2_uv[1]) / 2.0
        dx, dy = p2_uv[0] - p1_uv[0], p2_uv[1] - p1_uv[1]
        norm = math.hypot(dx, dy)
        dx, dy = dx / norm, dy / norm
        perp = (-dy, dx)
        center = (self.nave_length_m / 2.0, 0.0)
        to_center = (center[0] - mx, center[1] - my)
        if perp[0] * to_center[0] + perp[1] * to_center[1] > 0:
            perp = (-perp[0], -perp[1])  # punta verso il centro: inverto
        p_a = self.local_to_enu(mx, my, 0.0)
        p_b = self.local_to_enu(mx + perp[0], my + perp[1], 0.0)
        return math.degrees(math.atan2(p_b[0] - p_a[0], p_b[1] - p_a[1])) % 360.0

    def apse_vertices(self) -> list[tuple[float, float]]:
        """
        Vertici del pentagono absidale (5 lati, uno per finestra),
        CON la rientranza rispetto al filo della navata. Costruito
        "camminando" lungo i 5 lati usando i loro azimut REALI
        (misurati, vedi APSE_FACET_AZIMUTHS_DEG) e lunghezze stimate
        (APSE_FACET_LENGTHS_M), a partire dal punto di rientranza sul
        lato Ovest fino al punto di rientranza sul lato Est.
        """
        L = self.nave_length_m
        Wh = self.nave_width_m / 2.0

        u, v = L, Wh - APSE_RECESS_M
        pts = [(u, v)]
        for az, length in zip(APSE_FACET_AZIMUTHS_DEG, APSE_FACET_LENGTHS_M):
            tangent_az = math.radians(az + 90.0)
            along = self.enu_to_local_uv(math.sin(tangent_az), math.cos(tangent_az))
            u += along[0] * length
            v += along[1] * length
            pts.append((u, v))
        return pts

    def floor_outline_local(self) -> list[tuple[float, float]]:
        """
        Contorno REALE della pianta (navata + nicchie sporgenti delle
        8 cappelle + abside pentagonale CON rientranza), in
        coordinate locali (u,v).

        La pianta NON e' un semplice rettangolo: ogni cappella forma
        una nicchia che sporge oltre il filo della navata, e l'abside
        arretra rispetto al filo navata (APSE_RECESS_M) prima di
        aprirsi nel vero pentagono a 5 lati (vedi
        APSE_FACET_AZIMUTHS_DEG - misurati direttamente sulla pianta
        "Relevé de désordres").
        """
        L = self.nave_length_m
        Wh = self.nave_width_m / 2.0

        dw = CHAPEL_PROJECTION_WIDTH_M / 2.0
        dd = CHAPEL_PROJECTION_DEPTH_M
        chapel_us = self.chapel_u_positions()

        ne_side: list[tuple[float, float]] = [(0.0, Wh)]
        for u in chapel_us:
            ne_side.append((u - dw, Wh))
            ne_side.append((u - dw, Wh + dd))
            ne_side.append((u + dw, Wh + dd))
            ne_side.append((u + dw, Wh))
        ne_side.append((L, Wh))

        apse = self.apse_vertices()  # rientranza Ovest -> pentagono -> rientranza Est

        sw_side: list[tuple[float, float]] = [(L, -Wh)]
        for u in reversed(chapel_us):
            sw_side.append((u + dw, -Wh))
            sw_side.append((u + dw, -Wh - dd))
            sw_side.append((u - dw, -Wh - dd))
            sw_side.append((u - dw, -Wh))
        sw_side.append((0.0, -Wh))

        outline = ne_side + apse + sw_side
        outline.append(outline[0])
        return outline

    def core_outline_local(self) -> list[tuple[float, float]]:
        """
        Contorno "nucleo" della navata+abside, SENZA le nicchie
        sporgenti delle cappelle (lati Ovest/Est semplici, a filo
        v=+-Wh) - usato per il muro ALTO della navata (fino a
        WALL_HEIGHT_M), che si ferma al filo della navata invece di
        proseguire dentro le nicchie: le nicchie hanno un proprio
        muro BASSO separato (vedi build_chapel_wall_structures() in
        church_mesh.py), coerente con il tetto basso delle cappelle
        che le sormonta.
        """
        L = self.nave_length_m
        Wh = self.nave_width_m / 2.0
        apse = self.apse_vertices()
        outline = [(0.0, Wh), (L, Wh)] + apse + [(L, -Wh), (0.0, -Wh)]
        outline.append(outline[0])
        return outline

    def nave_only_outline_local(self) -> list[tuple[float, float]]:
        """
        Come core_outline_local(), ma SENZA il pentagono absidale
        (solo il rettangolo della navata) - usato per il muro ALTO
        della navata, che ora si ferma al filo di rientranza
        dell'abside (u=nave_length_m) invece di proseguire nel
        pentagono: l'abside ha un proprio muro ed un proprio tetto
        separati (vedi build_apse_wall_structure() in church_mesh.py),
        ad un'altezza diversa da quella della navata (MISURATA su
        Elevation Est, Michel Trubert ACMH, 1/100).
        """
        L = self.nave_length_m
        Wh = self.nave_width_m / 2.0
        outline = [(0.0, Wh), (L, Wh), (L, -Wh), (0.0, -Wh)]
        outline.append(outline[0])
        return outline

    def floor_outline_enu(self) -> list[tuple[float, float]]:
        return [self.local_to_enu(u, v, 0.0)[:2] for (u, v) in self.floor_outline_local()]


# =====================================================================
# 3. COSTRUZIONE DELLE 14 VETRATE
# =====================================================================

def build_default_windows() -> list[Window]:
    windows: list[Window] = []

    ne_names = ["Notre-Dame-du-Rosaire", "Saint-Joseph", "Sacre-Coeur", "Saint-Louis"]
    sw_names = ["Saint-Jean-Baptiste", "Coeur-Immacule-de-Marie", "Saint-Antoine", "Sainte-Anne"]

    church_tmp = ChurchModel()  # solo per chapel_u_positions()
    chapel_us = church_tmp.chapel_u_positions()
    Wh = NAVE_WIDTH_M / 2.0
    # Le vetrate delle cappelle sono finestre di CLERISTORIO sul muro
    # alto della navata (v=Wh), non sulla parete di fondo della
    # nicchia: il loro davanzale (11.18 m) e' interamente SOPRA la
    # gronda del tetto basso delle cappelle (9.64 m, vedi
    # CHAPEL_ROOF_HEIGHT_M) - se posizionate sulla parete della
    # nicchia (come in una versione precedente) risultano tagliate
    # fuori dal tetto basso, apparendo "troppo alte" e scollegate
    # dall'architettura. Sul muro navata, sopra il tetto basso,
    # l'altezza torna coerente con WALL_HEIGHT_M (16.56 m, confermato
    # da Elevation Sud, 16.55 m rosso).

    for i, u in enumerate(chapel_us):
        windows.append(Window(
            name=f"Cappella {ne_names[i]} (Ovest)",
            group="cappella",
            wall_point_uv=(u, Wh),
            wall_azimuth_deg=(FACADE_AZIMUTH_DEG + 90.0) % 360.0,
            width_m=CHAPEL_WINDOW_WIDTH_M,
            sill_m=CHAPEL_WINDOW_SILL_M,
            head_m=CHAPEL_WINDOW_HEAD_M,
            arch_rise_m=CHAPEL_WINDOW_ARCH_RISE_M,
        ))
        windows.append(Window(
            name=f"Cappella {sw_names[i]} (Est)",
            group="cappella",
            wall_point_uv=(u, -Wh),
            wall_azimuth_deg=(FACADE_AZIMUTH_DEG - 90.0) % 360.0,
            width_m=CHAPEL_WINDOW_WIDTH_M,
            sill_m=CHAPEL_WINDOW_SILL_M,
            head_m=CHAPEL_WINDOW_HEAD_M,
            arch_rise_m=CHAPEL_WINDOW_ARCH_RISE_M,
        ))

    church_tmp2 = ChurchModel()
    apse_pts = church_tmp2.apse_vertices()  # 6 punti: rientranza-O, 5 vertici pentagono, rientranza-E
    apse_names = [
        "Abside - lato corto Ovest",
        "Abside - pannello smussato Ovest",
        "Abside - pannello di fondo",
        "Abside - pannello smussato Est",
        "Abside - lato corto Est",
    ]
    for i in range(5):
        p1, p2 = apse_pts[i], apse_pts[i + 1]
        mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
        az = APSE_FACET_AZIMUTHS_DEG[i]
        is_clocher_side = (apse_names[i] == "Abside - lato corto Ovest")
        windows.append(Window(
            name=apse_names[i],
            group="abside",
            wall_point_uv=mid,
            wall_azimuth_deg=az,
            width_m=APSE_WINDOW_CLOCHER_WIDTH_M if is_clocher_side else APSE_WINDOW_WIDTH_M,
            sill_m=APSE_WINDOW_CLOCHER_SILL_M if is_clocher_side else APSE_WINDOW_SILL_M,
            head_m=APSE_WINDOW_CLOCHER_HEAD_M if is_clocher_side else APSE_WINDOW_HEAD_M,
            arch_rise_m=APSE_WINDOW_CLOCHER_ARCH_RISE_M if is_clocher_side else APSE_WINDOW_ARCH_RISE_M,
        ))

    windows.append(Window(
        name="Facciata - finestra centrale",
        group="facciata",
        wall_point_uv=(0.0, 0.0),
        wall_azimuth_deg=FACADE_AZIMUTH_DEG,
        width_m=FACADE_CENTRAL_WINDOW_WIDTH_M,
        sill_m=FACADE_CENTRAL_WINDOW_SILL_M,
        head_m=FACADE_CENTRAL_WINDOW_HEAD_M,
        arch_rise_m=FACADE_CENTRAL_WINDOW_ARCH_RISE_M,
    ))
    windows.append(Window(
        name="Facciata - finestra laterale Ovest",
        group="facciata",
        wall_point_uv=(0.0, FACADE_SIDE_WINDOW_OFFSET_M),
        wall_azimuth_deg=FACADE_AZIMUTH_DEG,
        width_m=FACADE_SIDE_WINDOW_WIDTH_M,
        sill_m=FACADE_SIDE_WINDOW_SILL_M,
        head_m=FACADE_SIDE_WINDOW_HEAD_M,
        arch_rise_m=FACADE_SIDE_WINDOW_ARCH_RISE_M,
    ))
    windows.append(Window(
        name="Facciata - finestra laterale Est",
        group="facciata",
        wall_point_uv=(0.0, -FACADE_SIDE_WINDOW_OFFSET_M),
        wall_azimuth_deg=FACADE_AZIMUTH_DEG,
        width_m=FACADE_SIDE_WINDOW_WIDTH_M,
        sill_m=FACADE_SIDE_WINDOW_SILL_M,
        head_m=FACADE_SIDE_WINDOW_HEAD_M,
        arch_rise_m=FACADE_SIDE_WINDOW_ARCH_RISE_M,
    ))
    windows.append(Window(
        name="Facciata - portale d'ingresso",
        group="porta",
        wall_point_uv=(0.0, 0.0),
        wall_azimuth_deg=FACADE_AZIMUTH_DEG,
        width_m=FACADE_DOOR_WIDTH_M,
        sill_m=FACADE_DOOR_SILL_M,
        head_m=FACADE_DOOR_HEAD_M,
        arch_rise_m=FACADE_DOOR_ARCH_RISE_M,
    ))

    return windows


def default_church() -> ChurchModel:
    return ChurchModel(windows=build_default_windows())
