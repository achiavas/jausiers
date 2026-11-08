// parametri.js - quale orientamento usa il modello 3D.
//
// Le misure della chiesa vengono dalle PIANTINE cartacee (diagnostico
// 2016, Michel Trubert ACMH): sono la base. Un azimut trovato online
// (ricerca /chiesa, dati/ricerca.js) o da OSM (dati/chiese_ubaye.js) e'
// solo un CONFRONTO, che si attiva esplicitamente dall'indirizzo:
//
//   index.html                    -> piantine (facciata 160)
//   index.html?fonte=online       -> asse trovato dalla ricerca
//   index.html?fonte=osm          -> asse OSM (orientamento_chiese.csv)
//   index.html?asse=156.2         -> un asse qualsiasi
//
// Stessa regola di mods/jausiers/scripts/ruota.py: l'asse e' noto modulo
// 180, la facciata e' la direzione piu' vicina a quella delle piantine;
// tutto l'edificio (facciata, cappelle, 5 pareti absidali) ruota di delta.
"use strict";

const URL_PARAMS = new URLSearchParams(window.location.search);

function angDiff(a, b) {
  return Math.abs((((a - b + 180.0) % 360.0) + 360.0) % 360.0 - 180.0);
}

function mod360(x) {
  return ((x % 360.0) + 360.0) % 360.0;
}

function asseOsmJausiers() {
  const chiese = window.CHIESE_UBAYE || [];
  const c = chiese.find((r) => /Saint-Nicolas/.test(r.nome) && /Jausiers/.test(r.commune));
  return c ? c.axis_az : undefined;
}

function scegliOrientamento(facciataPiantine) {
  const ricerca = window.RICERCA || {};
  let fonte = URL_PARAMS.get("fonte") || "piantine";
  let asse;
  if (URL_PARAMS.has("asse") && Number.isFinite(parseFloat(URL_PARAMS.get("asse")))) {
    fonte = "manuale";
    asse = parseFloat(URL_PARAMS.get("asse"));
  } else if (fonte === "online") {
    asse = ricerca.azimutAsse;
  } else if (fonte === "osm") {
    asse = asseOsmJausiers();
  }
  if (asse === undefined || asse === null || !Number.isFinite(asse)) {
    fonte = "piantine";
    asse = undefined;
  }
  let facciata = facciataPiantine;
  if (asse !== undefined) {
    const a = mod360(asse);
    const b = mod360(a + 180.0);
    facciata = angDiff(a, facciataPiantine) <= angDiff(b, facciataPiantine) ? a : b;
  }
  const delta = mod360(facciata - facciataPiantine + 180.0) - 180.0;
  return { fonte, asse, facciata, delta, facciataPiantine };
}

// Indirizzo della stessa pagina con altri parametri (lingua, fonte, giorno, ora).
function urlCon(cambi) {
  const p = new URLSearchParams(window.location.search);
  for (const [k, v] of Object.entries(cambi)) {
    if (v === undefined || v === null || v === "") p.delete(k);
    else p.set(k, String(v));
  }
  const q = p.toString();
  return window.location.pathname + (q ? "?" + q : "");
}
