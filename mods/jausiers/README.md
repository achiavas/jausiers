# jausiers

Mod di Claude Code con un pannello a due blocchi per l'Église Saint-Nicolas-de-Myre di Jausiers.

**Blocco 1 · Ricerca.** `/chiesa` (o il pulsante "Avvia ricerca") registra lo strumento
`salva_ricerca` e avvia un turno in cui Claude cerca sul web l'orientamento (azimut dell'asse)
e la storia della chiesa. Lo strumento salva i risultati con le fonti nel pannello e in
`../../orientatamento_chiese_Ubaye/ricerca_saint_nicolas_jausiers.md` (+ `.json`).

**Blocco 2 · Sole.** Esegue `scripts/sole.py`, che riusa `jausiers_sun3d_py`
(`solar_position`, `church_geometry`, `wall_projection`) senza PyVista e calcola alba,
tramonto, culminazione e le vetrate illuminate per oggi, solstizi, equinozio e San Nicola.
Quando il blocco 1 salva un azimut, il blocco 2 ruota il modello su quell'asse e ricalcola.

**Blocco 3 · Vista 3D.** All'avvio della sessione il mod apre sempre `viewer_3d.py` (PyVista)
in una finestra a parte, tramite `scripts/viewer.py`, che ruota l'edificio sull'asse trovato.
Quando la ricerca salva un nuovo azimut la finestra si riapre ruotata; se la chiudi, la riapri
dal pulsante "Apri vista 3D".

Requisiti: `/usr/local/bin/python3` con numpy, shapely e backports.zoneinfo (Python 3.8).
Per un altro interprete cambia `PYTHON` in `hooks/register.tsx`.

Avvio: `claude --plugin-dir /Users/andreew_1/Documents/eglise_jausiers/mods/jausiers`
