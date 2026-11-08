# Saint-Nicolas-de-Myre, Jausiers — la luce del sole in 3D

Modello 3D della chiesa di Saint-Nicolas-de-Myre a Jausiers (Alpes-de-Haute-Provence,
valle dell'Ubaye). Calcola dove entra la luce del sole attraverso le vetrate, per
qualsiasi giorno dell'anno e ora, e la proietta sul pavimento, sulle pareti e sui banchi,
con le ombre degli arredi.

Il progetto ha **due versioni dello stesso modello**, che usano le stesse misure e la
stessa logica:

| | Che cos'è | Come si apre |
|---|---|---|
| `sito/` | Sito web statico (HTML + JavaScript, three.js), in italiano e francese. Funziona anche da telefono. | un qualsiasi server web statico (vedi sotto) |
| `jausiers_sun3d_py/` | Programma Python da desktop (PyVista/VTK) con gli stessi calcoli | `python viewer_3d.py` |

## Cosa si vede

- La chiesa in 3D, dentro e fuori: navata, abside con volta a ombrello, 8 cappelle
  laterali con i loro altari, controfacciata con bussola e battistero, pulpito, organo,
  banchi, balaustra, lampadari, Via Crucis, tetto in scandole e intonaco esterno.
- Le pareti sono rivestite con foto vere della chiesa (raddrizzate dai video e dalle foto).
- Due cursori, **giorno dell'anno** e **ora locale** (Europe/Paris, con l'ora legale):
  le macchie di luce colorate delle vetrate si muovono sul pavimento, sulle pareti e sui
  banchi; gli arredi fanno ombra.
- Viste rapide: ciascuna cappella, facciata interna, abside, esterno, facciata esterna.
- Pagina **Storia**: cronologia (dal 1668), orientamento della chiesa, cartine e fonti.

## Avviare il sito in locale

```bash
cd sito
python3 -m http.server 8765
```

Poi aprire <http://localhost:8765/>. La cartella `sito/` è già pronta per essere pubblicata
così com'è (per esempio con GitHub Pages).

## Avviare il programma Python

```bash
cd jausiers_sun3d_py
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python viewer_3d.py
```

Tasti utili: `1` `2` `4` solstizi/equinozio, `N` `S` `K` `O` viste laterali, `T` pianta,
`R` reset, `Spazio` anima la giornata, `V` vetrate, `H` storia e fonti.

## Struttura dei file

### `jausiers_sun3d_py/` — il modello (Python)

| File | A cosa serve |
|---|---|
| `church_geometry.py` | Tutte le misure della chiesa (navata, cappelle, abside, gradini, arredi, vetrate) e la quota del pavimento |
| `church_mesh.py` | Costruisce le mesh 3D: muri, tetto, volte, gradini, altari, banchi, pulpito, organo, lampadari… |
| `solar_position.py` | Posizione del sole (azimut, altezza) per data, ora e luogo |
| `wall_projection.py` | Proietta la luce di ogni vetrata sul primo ostacolo: pavimento, pareti (con gli archi delle cappelle) e banchi |
| `light_projection.py` | Proiezione semplice sul solo pavimento (versione precedente) |
| `reference_photos.py` | Dove va ogni foto sulle pareti, nelle cappelle e sulle vetrate |
| `viewer_3d.py` | Il programma interattivo: scena, cursori, macchie di luce e ombre |
| `storia_chiesa.py`, `storia_jausiers.json` | Testo della storia e cronologia (italiano e francese) |
| `*_da_video.py`, `*_da_foto.py` | Script usati una volta per ricavare le foto dai video e raddrizzarle (cappelle, abside, volta, facciata, vetrate, pavimento, tetto) |
| `photos/` | Le foto raddrizzate usate come texture |
| `video/` | Foto di partenza (i video originali `.mov` non sono nel repository: sono troppo grandi) |
| `ricerca_orientamento_ubaye/` | Ricerca sull'orientamento delle chiese dell'Ubaye: dati, fonti e cartina |
| `README.md` | Diario dettagliato dello sviluppo |

### `sito/` — il sito web

| File | A cosa serve |
|---|---|
| `modelli/index.html`, `modelli/storia.html` | I modelli delle pagine (si modificano questi) |
| `it/`, `fr/` | Le pagine generate in italiano e in francese (da non modificare a mano) |
| `index.html` | Pagina d'ingresso: sceglie la lingua |
| `comune/church-geometry.js`, `church-mesh.js`, `wall-projection.js`, `solar-position.js`, `reference-photos.js` | Gli stessi calcoli della parte Python, tradotti in JavaScript |
| `comune/i18n.js` | Testi in italiano e francese |
| `comune/photos-data.js` | Le foto incorporate nel sito |
| `comune/dati/` | Storia, ricerca e cartina dell'Ubaye in formato per il sito |
| `comune/three.min.js`, `orbit-controls-lite.js`, `triangulate.js`, `paris-time.js`, `parametri.js` | Librerie e utilità |
| `strumenti/genera_pagine.py` | Genera `it/` e `fr/` dai modelli |
| `strumenti/genera_foto.py` | Incorpora le foto in `photos-data.js` |
| `strumenti/genera_dati.py` | Copia storia, ricerca e cartina in `comune/dati/` |
| `strumenti/verifica_sync.py` | Controlla che Python e sito usino le stesse misure |

Dopo una modifica al sito:

```bash
cd sito
python3 strumenti/genera_pagine.py
python3 strumenti/verifica_sync.py
```

### Altre cartelle

| Cartella | A cosa serve |
|---|---|
| `orientatamento_chiese_Ubaye/` | Tabella e script sull'orientamento delle chiese della valle |
| `mods/jausiers/` | Un pannello aggiuntivo per Claude Code usato durante la ricerca (non serve al sito) |

## Fonti

Diagnostico dell'edificio del 2016, deliberazione del 1668, base Mérimée (PA00080407),
OpenStreetMap, planimetria catastale, foto e video fatti nella chiesa. I PDF originali
non sono nel repository.
