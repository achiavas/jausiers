// reference-photos.js
// Porting 1:1 di reference_photos.py — vedi quel file per la
// spiegazione completa. Qui le funzioni ritornano descrittori di
// geometria "grezzi" ({positions, uvs, indices, filename}) pronti da
// convertire in THREE.Mesh nel file principale (index.html), non
// oggetti Three.js direttamente, per restare testabili in Node senza
// bisogno di un contesto WebGL.

const NAVE_U_CENTER = NAVE_LENGTH_M / 2.0;
const WH = NAVE_WIDTH_M / 2.0;
const BC_MARGIN = NAVE_LENGTH_M * 0.06;
const BC_SPAN = NAVE_LENGTH_M - 2 * BC_MARGIN;

const PHOTO_CARDS = [
  {
    filename: "facciata_esterna.jpg",
    caption: "Façade extérieure (photo réelle)",
    u: -0.15, v: 0.0, wBottom: 0.0, widthM: 15.93, heightM: 22.94,
    facing: "minus_u",
  },
  {
    filename: "im1.jpg",
    caption: "Nef latérale Ouest, vue de l'intérieur",
    u: NAVE_U_CENTER, v: WH - 0.1, wBottom: 0.5, widthM: BC_SPAN, heightM: BC_SPAN / 1.599,
    facing: "minus_v",
  },
  {
    filename: "im2.jpg",
    caption: "Nef latérale Est, vue de l'intérieur",
    u: NAVE_U_CENTER, v: -WH + 0.1, wBottom: 0.5, widthM: BC_SPAN, heightM: BC_SPAN / 1.799,
    facing: "plus_v",
  },
];

const CHAPEL_WINDOW_PHOTOS = {
  "Chapelle Notre-Dame-du-Rosaire (Ouest)": "vetrata_ovest_reale.jpg",
  "Chapelle Saint-Joseph (Ouest)": "vetrata_ovest_reale.jpg",
  "Chapelle Sacre-Coeur (Ouest)": "vetrata_ovest_reale.jpg",
  "Chapelle Saint-Louis (Ouest)": "vetrata_ovest_reale.jpg",
  "Chapelle Saint-Jean-Baptiste (Est)": "vetrata_est_reale.jpg",
  "Chapelle Coeur-Immacule-de-Marie (Est)": "vetrata_est_reale.jpg",
  "Chapelle Saint-Antoine (Est)": "vetrata_est_reale.jpg",
  "Chapelle Sainte-Anne (Est)": "vetrata_est_reale.jpg",
};

const APSE_PHOTO_FILENAME = "abside_altare_frontale.jpg";
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
    const sign = card.facing === "plus_v" ? 1.0 : -1.0;
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
  return { filename: card.filename, positions, uvs, indices, frameLoop: [0, 1, 2, 3, 0] };
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
  const vertsUV = [[L, Wh], ...church.apseVertices(), [L, -Wh]];
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
function buildWindowPhotoOverlay(church, win, filename, inset = 0.16) {
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
    const uTex = 0.5 + s / win.widthM;
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
