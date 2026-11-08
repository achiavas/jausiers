// reference-photos.js
// Porting 1:1 di reference_photos.py — vedi quel file per la
// spiegazione completa. Qui le funzioni ritornano descrittori di
// geometria "grezzi" ({positions, uvs, indices, filename}) pronti da
// convertire in THREE.Mesh nel file principale (index.html), non
// oggetti Three.js direttamente, per restare testabili in Node senza
// bisogno di un contesto WebGL.

const NAVE_U_CENTER = NAVE_LENGTH_M / 2.0;
const WH = NAVE_WIDTH_M / 2.0;
// una campata di cappella, fra i centri di due pilastri (6.08 m)
const CAMPATA = (NAVE_LENGTH_M - 2 * CHAPEL_ROW_MARGIN_M) / N_CHAPELS_PER_SIDE;
const BC_MARGIN = NAVE_LENGTH_M * 0.06;
const BC_SPAN = NAVE_LENGTH_M - 2 * BC_MARGIN;

const PHOTO_CARDS = [
  {
    filename: "facciata_esterna.png",
    caption: "Facciata esterna (foto reale)",
    // foto adattata con facciata_da_foto.py (vetrate sulle vetrate del modello)
    // sul filo esterno del muro, 2 cm davanti alla faccia esterna delle vetrate
    u: -0.76, v: 0.0, wBottom: 0.0, widthM: 20.0, heightM: 26.5,
    facing: "minus_u", soloFronte: true, // non visibile da dentro
  },
  // Pareti laterali: le vecchie foto im1/im2 (non raddrizzate) sono
  // state TOLTE: non corrispondevano alle cappelle (vedi reference_photos.py).
  // Cappelle, una campata per foto: raddrizzate e in scala con
  // foto_da_video.py (vedi reference_photos.py).
  {
    filename: "cappella_ovest_1.jpg",
    caption: "Prima cappella a sinistra entrando (Ovest), dal video IMG_9734",
    u: CHAPEL_ROW_MARGIN_M + 0.5 * CAMPATA, v: WH - 0.15, wBottom: 0.09,
    widthM: CAMPATA, heightM: 8.77,
    facing: "minus_v", foroCappella: true,
  },
  {
    filename: "cappella_ovest_2.jpg",
    caption: "Seconda cappella a sinistra entrando (Ovest), da IMG_9758 (21 s)",
    u: CHAPEL_ROW_MARGIN_M + 1.5 * CAMPATA, v: WH - 0.15, wBottom: 0.0,
    widthM: CAMPATA, heightM: 6.73,
    facing: "minus_v", foroCappella: true,
  },
  {
    filename: "cappella_est_2.jpg",
    caption: "Seconda cappella a destra entrando (Est), dal video IMG_9738",
    u: CHAPEL_ROW_MARGIN_M + 1.5 * CAMPATA, v: -WH + 0.15, wBottom: 0.0,
    widthM: CAMPATA, heightM: 8.72,
    facing: "plus_v", foroCappella: true,
  },
  {
    filename: "cappella_ovest_4.jpg",
    caption: "Quarta cappella a sinistra entrando (Ovest), dal video IMG_9740",
    u: CHAPEL_ROW_MARGIN_M + 3.5 * CAMPATA, v: WH - 0.15, wBottom: 0.0,
    widthM: CAMPATA, heightM: 8.19,
    facing: "minus_v", foroCappella: true,
  },
  {
    filename: "cappella_ovest_3.jpg",
    caption: "Terza cappella a sinistra entrando (Ovest), dal video IMG_9742",
    u: CHAPEL_ROW_MARGIN_M + 2.5 * CAMPATA, v: WH - 0.15, wBottom: 0.0,
    widthM: CAMPATA, heightM: 7.80,
    facing: "minus_v", foroCappella: true,
  },
  {
    filename: "cappella_est_4.jpg",
    caption: "Quarta cappella a destra entrando (Est), da IMG_9758 (0.5 s)",
    u: CHAPEL_ROW_MARGIN_M + 3.5 * CAMPATA, v: -WH + 0.15, wBottom: 0.0,
    widthM: CAMPATA, heightM: 7.31,
    facing: "plus_v", foroCappella: true,
  },
  // Terza a destra: la foto cade tutta dentro l'arco, quindi niente
  // pannello sul filo della navata: e' solo NICCHIA (vedi sotto).
];

// NICCHIE delle cappelle: profondita' (porting di reference_photos.py,
// vedi li' la spiegazione). [nome, lato (+1 Ovest, -1 Est), indice campata]
const NICCHIA_Z0 = -0.15;
// Pavimento: texture dal video IMG_9757 (vedi reference_photos.py)
const PAVIMENTO_FILENAME = "pavimento.jpg";
const PAVIMENTO_PERIODO_M = 5.0;
const PAVIMENTO_LARGHEZZA_M = 18.0;
// Tetto e muri esterni: texture ripetibili dal video IMG_9765 (vedi reference_photos.py)
const CONTROFACCIATA_ALTEZZA_M = 13.3;
const TETTO_TEXTURE_FILENAME = "tetto_esterno.jpg";
const TETTO_TEXTURE_M = [2.4, 0.72];
const MURO_TEXTURE_FILENAME = "muro_esterno.jpg";
const MURO_TEXTURE_M = 1.0;
const NICCHIE = [
  ["cappella_ovest_1", +1, 0],
  ["cappella_est_1", -1, 0],
  ["cappella_ovest_2", +1, 1],
  ["cappella_est_2", -1, 1],
  ["cappella_est_3", -1, 2],
  ["cappella_ovest_4", +1, 3],
  ["cappella_ovest_3", +1, 2],
  ["cappella_est_4", -1, 3],
];
const N_ARCO = 32;

function arcoAperto(X, Y, margine = 0) {
  const R = CHAPEL_ARCH_RADIUS_M + margine, S = CHAPEL_ARCH_SPRING_M;
  return Math.abs(X) < R && (Y < S || X * X + (Y - S) ** 2 < R * R);
}

// Pannello di cappella con l'arco d'ingresso bucato -> {positions, uvs, indices}
function buildCardConForo(card, church) {
  const [BL, BR] = cardCornersLocal(card);
  const W = card.widthM, H = card.heightM, wb = card.wBottom, top = wb + H;
  const R = CHAPEL_ARCH_RADIUS_M, S = CHAPEL_ARCH_SPRING_M;
  const positions = [], uvs = [], indices = [];
  const P = (X, Y) => {
    const t = (X + W / 2) / W;
    positions.push(church.localToEnu(BL[0] + t * (BR[0] - BL[0]), BL[1] + t * (BR[1] - BL[1]), Y));
    uvs.push([t, (Y - wb) / H]);
  };
  const quad = (a, b, c, d) => {
    const i = positions.length;
    for (const [X, Y] of [a, b, c, d]) P(X, Y);
    indices.push([i, i + 1, i + 2], [i, i + 2, i + 3]);
  };
  quad([-W / 2, wb], [-R, wb], [-R, top], [-W / 2, top]);
  quad([R, wb], [W / 2, wb], [W / 2, top], [R, top]);
  for (let k = 0; k < N_ARCO; k++) {
    const t0 = Math.PI * k / N_ARCO, t1 = Math.PI * (k + 1) / N_ARCO;
    const x0 = -R * Math.cos(t0), x1 = -R * Math.cos(t1);
    const y0 = S + R * Math.sin(t0), y1 = S + R * Math.sin(t1);
    quad([x0, y0], [x1, y1], [x1, top], [x0, top]);
  }
  return { filename: card.filename, positions, uvs, indices };
}

// Le quattro superfici della nicchia -> [{filename, positions, uvs, indices}]
function buildNicchia(nome, lato, indice, church) {
  // fondo 5 cm davanti al muro di fondo della cappella del modello (vedi reference_photos.py)
  const R = CHAPEL_ARCH_RADIUS_M, S = CHAPEL_ARCH_SPRING_M, d = CHAPEL_PROJECTION_DEPTH_M - 0.05, z0 = NICCHIA_Z0;
  const uc = church.chapelUPositions()[indice];
  const L = (X, Y, Z) => church.localToEnu(uc + lato * X, lato * (WH + Z), Y);
  const parti = [];
  { // fondo: rettangolo fino all'imposta + mezzo cerchio
    const positions = [], uvs = [], indices = [], H = S + R;
    const add = (X, Y, uv) => { positions.push(L(X, Y, d)); uvs.push(uv); return positions.length - 1; };
    const a = add(-R, 0, [0, 0]), b = add(R, 0, [1, 0]), c = add(R, S, [1, S / H]), e = add(-R, S, [0, S / H]);
    indices.push([a, b, c], [a, c, e]);
    const centro = add(0, S, [0.5, S / H]);
    const arco = [];
    for (let k = 0; k <= N_ARCO; k++) {
      const th = Math.PI * k / N_ARCO;
      arco.push(add(-R * Math.cos(th), S + R * Math.sin(th), [(1 - Math.cos(th)) / 2, (S + R * Math.sin(th)) / H]));
    }
    for (let k = 0; k < N_ARCO; k++) indices.push([centro, arco[k + 1], arco[k]]);
    parti.push({ filename: `${nome}_fondo.jpg`, positions, uvs, indices });
  }
  for (const [suff, X] of [["lato_sx", -R], ["lato_dx", R]]) {
    parti.push({
      filename: `${nome}_${suff}.jpg`,
      positions: [L(X, 0, z0), L(X, 0, d), L(X, S, d), L(X, S, z0)],
      uvs: [[0, 0], [1, 0], [1, 1], [0, 1]], indices: [[0, 1, 2], [0, 2, 3]],
    });
  }
  { // volta a botte
    const positions = [], uvs = [], indices = [];
    for (let k = 0; k <= N_ARCO; k++) {
      const th = Math.PI * k / N_ARCO, X = -R * Math.cos(th), Y = S + R * Math.sin(th);
      positions.push(L(X, Y, z0), L(X, Y, d));
      uvs.push([k / N_ARCO, 0], [k / N_ARCO, 1]);
    }
    for (let k = 0; k < N_ARCO; k++) { const i = 2 * k; indices.push([i, i + 2, i + 3], [i, i + 3, i + 1]); }
    parti.push({ filename: `${nome}_volta.jpg`, positions, uvs, indices });
  }
  return parti;
}

// True se il punto locale (u, v, w) del muro della navata cade nell'arco
// d'ingresso di una cappella con nicchia (il muro li' va bucato).
function aperturaCappella(church, u, v, w, margine = 0) {
  for (const [, lato, indice] of NICCHIE) {
    if (v * lato <= 0) continue;
    if (arcoAperto(u - church.chapelUPositions()[indice], w, margine)) return true;
  }
  return false;
}

// Foto reali delle vetrate laterali, una per vetrata (vetrate_laterali_da_foto.py,
// vedi reference_photos.py): Ovest a-d dall'ingresso, Est e-h dall'abside, i sui lati corti dell'abside
const CHAPEL_WINDOW_PHOTOS = {
  "Cappella Notre-Dame-du-Rosaire (Ovest)": "vetrata_laterale_a.jpg",
  "Cappella Saint-Joseph (Ovest)": "vetrata_laterale_b.jpg",
  "Cappella Sacre-Coeur (Ovest)": "vetrata_laterale_c.jpg",
  "Cappella Saint-Louis (Ovest)": "vetrata_laterale_d.jpg",
  "Cappella Sainte-Anne (Est)": "vetrata_laterale_e.jpg",
  "Cappella Saint-Antoine (Est)": "vetrata_laterale_f.jpg",
  "Cappella Coeur-Immacule-de-Marie (Est)": "vetrata_laterale_g.jpg",
  "Cappella Saint-Jean-Baptiste (Est)": "vetrata_laterale_h.jpg",
  "Abside - lato corto Ovest": "vetrata_laterale_i.jpg",
  "Abside - lato corto Est": "vetrata_laterale_i.jpg",
  // Vetrate della facciata viste dall'interno (vetrate_da_video.py, video IMG_9756)
  "Facciata - finestra centrale": "vetrata_facciata_centrale.jpg",
  "Facciata - finestra laterale Ovest": "vetrata_facciata_ovest.jpg",
  "Facciata - finestra laterale Est": "vetrata_facciata_est.jpg",
};

// sviluppo della parete vera dal video IMG_9760 (abside_da_video.py)
const APSE_PHOTO_FILENAME = "abside_interno.jpg";
const APSE_PHOTO_HEIGHT_BOTTOM = 0.5;
// CORRETTO: usava WALL_HEIGHT_M (altezza muro NAVATA), risalente a
// prima che l'abside avesse un'altezza propria distinta - il
// pannello risultava "troppo alto" (segnalato dall'utente).
// L'abside ha ora il suo muro a APSE_EXTERNAL_HEIGHT_M (15.69 m).
const APSE_PHOTO_HEIGHT_TOP = APSE_EXTERNAL_HEIGHT_M - 0.56;

// 4 angoli locali (u,v,w) del pannello: basso-sx, basso-dx, alto-dx, alto-sx
function cardCornersLocal(card) {
  if (card.facing === "down") {
    const hw = card.widthM / 2.0, hh = card.heightM / 2.0;
    return [
      [card.u - hw, card.v - hh, card.wBottom],
      [card.u + hw, card.v - hh, card.wBottom],
      [card.u + hw, card.v + hh, card.wBottom],
      [card.u - hw, card.v + hh, card.wBottom],
    ];
  }
  const halfW = card.widthM / 2.0;
  let left, right;
  if (card.facing === "plus_v" || card.facing === "minus_v") {
    // CORRETTO: segno invertito, le foto laterali erano speculari
    // (vedi reference_photos.py): guardando la parete Ovest (+v)
    // dall'interno la facciata (u piccolo) e' a SINISTRA.
    const sign = card.facing === "plus_v" ? -1.0 : 1.0;
    left = [card.u - sign * halfW, card.v];
    right = [card.u + sign * halfW, card.v];
  } else {
    // NOTA: "plus_u"/"minus_u" non sono simmetrici per riflessione
    // come plus_v/minus_v - il segno corretto e' stato verificato
    // empiricamente confrontando il testo delle meridiane nella foto
    // reale della facciata (era speculare con sign=-1 su minus_u
    // prima di questa correzione - vedi reference_photos.py).
    const sign = card.facing === "plus_u" ? 1.0 : -1.0;
    left = [card.u, card.v - sign * halfW];
    right = [card.u, card.v + sign * halfW];
  }
  return [
    [left[0], left[1], card.wBottom],
    [right[0], right[1], card.wBottom],
    [right[0], right[1], card.wBottom + card.heightM],
    [left[0], left[1], card.wBottom + card.heightM],
  ];
}

// Pannello piatto rettangolare -> {positions:[[x,y,z]x4], uvs:[[u,v]x4], indices:[[0,1,2],[0,2,3]]}
function buildFlatCard(card, church) {
  const corners = cardCornersLocal(card);
  const positions = corners.map(([u, v, w]) => church.localToEnu(u, v, w));
  const uvs = [[0, 0], [1, 0], [1, 1], [0, 1]];
  const indices = [[0, 1, 2], [0, 2, 3]];
  return { filename: card.filename, positions, uvs, indices,
    soloFronte: !!card.soloFronte, frameLoop: card.soloFronte ? null : [0, 1, 2, 3, 0] };
}

// Pannello CURVO dell'abside: striscia di quad che segue i 5 lati del
// pentagono (church.apseVertices()) PIU' i due tratti di raccordo
// verso il muro della navata (da (L,Wh) al primo vertice, e
// dall'ultimo vertice a (L,-Wh)) - senza questi due tratti il
// pannello lasciava un varco visibile vicino alla torre ("non chiude
// verso il basso", segnalato dall'utente). Texture U proporzionale
// alla distanza percorsa lungo il perimetro.
function buildCurvedApsePanel(church, filename = APSE_PHOTO_FILENAME, heightBottom = APSE_PHOTO_HEIGHT_BOTTOM, heightTop = APSE_PHOTO_HEIGHT_TOP) {
  const Wh = church.naveWidthM / 2.0;
  const L = church.naveLengthM;
  let vertsUV = [[L, Wh], ...church.apseVertices(), [L, -Wh]];
  // 10 cm verso l'interno (vedi reference_photos.py)
  const cu = vertsUV.reduce((s, p) => s + p[0], 0) / vertsUV.length;
  vertsUV = vertsUV.map(([u, v]) => { const n = Math.hypot(cu - u, v) || 1; return [u + 0.1 * (cu - u) / n, v - 0.1 * v / n]; });
  const cum = [0.0];
  for (let i = 1; i < vertsUV.length; i++) {
    const d = Math.hypot(vertsUV[i][0] - vertsUV[i - 1][0], vertsUV[i][1] - vertsUV[i - 1][1]);
    cum.push(cum[cum.length - 1] + d);
  }
  const total = cum[cum.length - 1] > 0 ? cum[cum.length - 1] : 1.0;

  const positions = [];
  const uvs = [];
  for (let i = 0; i < vertsUV.length; i++) {
    const [uLoc, vLoc] = vertsUV[i];
    const uTex = cum[i] / total;
    positions.push(church.localToEnu(uLoc, vLoc, heightBottom));
    uvs.push([uTex, 0.0]);
    positions.push(church.localToEnu(uLoc, vLoc, heightTop));
    uvs.push([uTex, 1.0]);
  }

  const n = vertsUV.length;
  const indices = [];
  for (let i = 0; i < n - 1; i++) {
    const i0 = i * 2;
    indices.push([i0, i0 + 2, i0 + 3], [i0, i0 + 3, i0 + 1]);
  }

  const bottomLoop = [];
  const topLoop = [];
  for (let i = 0; i < n; i++) { bottomLoop.push(i * 2); topLoop.push(i * 2 + 1); }

  return { filename, positions, uvs, indices, bottomLoop, topLoop };
}

function windowAlongVector(church, win) {
  const tangentWorldRad = (Math.PI / 180) * (win.wallAzimuthDeg - 90.0);
  return church.enuToLocalUV(Math.sin(tangentWorldRad), Math.cos(tangentWorldRad));
}

function windowOutwardVector(church, win) {
  const th = (Math.PI / 180) * win.wallAzimuthDeg;
  const [du, dv] = church.enuToLocalUV(Math.sin(th), Math.cos(th));
  const mag = Math.hypot(du, dv) || 1.0;
  return [du / mag, dv / mag];
}

// Foto reale sovrapposta su una vetrata (arco incluso), arretrata di
// `inset` verso l'interno per restare davanti alla mesh piena e ai
// pannelli grandi delle pareti laterali.
function buildWindowPhotoOverlay(church, win, filename, inset = 0.03) {  // 1 cm davanti alla faccia interna della vetrata
  const along = windowAlongVector(church, win);
  const outward = windowOutwardVector(church, win);
  const totalH = (win.headM + win.archRiseM) - win.sillM;
  if (totalH <= 0) return null;

  const outline = win.localOutline();
  const positions = [];
  const uvs = [];
  for (const [u, v, w] of outline) {
    const uIn = u - outward[0] * inset;
    const vIn = v - outward[1] * inset;
    positions.push(church.localToEnu(uIn, vIn, w));
    const duP = u - win.wallPointUV[0], dvP = v - win.wallPointUV[1];
    const s = duP * along[0] + dvP * along[1];
    // CORRETTO: era 0.5 + s/width (foto speculari viste dall'interno),
    // vedi reference_photos.py.
    const uTex = 0.5 - s / win.widthM;
    const vTex = (w - win.sillM) / totalH;
    uvs.push([uTex, vTex]);
  }

  const cu = win.wallPointUV[0] - outward[0] * inset;
  const cv = win.wallPointUV[1] - outward[1] * inset;
  const cw = win.sillM + totalH * 0.5;
  positions.push(church.localToEnu(cu, cv, cw));
  uvs.push([0.5, 0.5]);
  const centerIdx = positions.length - 1;

  const n = centerIdx;
  const indices = [];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    indices.push([centerIdx, i, j]);
  }
  return { filename, positions, uvs, indices };
}

function buildAllWindowOverlays(church, mapping = CHAPEL_WINDOW_PHOTOS) {
  const windowsByName = Object.fromEntries(church.windows.map((w) => [w.name, w]));
  const out = [];
  for (const [name, filename] of Object.entries(mapping)) {
    const win = windowsByName[name];
    if (!win) continue;
    const overlay = buildWindowPhotoOverlay(church, win, filename);
    if (overlay) out.push({ windowName: name, ...overlay });
  }
  return out;
}
