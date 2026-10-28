// church-mesh.js
// Porting 1:1 di church_mesh.py — costruisce le mesh 3D SOLIDE
// (mura con spessore reale, tetto, pavimento, vetrate incassate)
// come THREE.BufferGeometry, a partire dal modello parametrico di
// church-geometry.js.

const WALL_THICKNESS_M = 0.70;
const FLOOR_THICKNESS_M = 0.30;

// ---------------------------------------------------------------
// Geometria di supporto (poligoni in pianta locale u,v)
// ---------------------------------------------------------------

// (signedArea condivisa con triangulate.js, caricato prima)

// Ritorna un anello (u,v) spostato verso l'esterno di `distance` metri
// (giunzione a mitria). loop_uv NON deve avere l'ultimo punto duplicato.
function offsetLoopOutward(loopUV, distance) {
  const n = loopUV.length;
  const sign = signedArea(loopUV) > 0 ? 1.0 : -1.0;

  function norm2(d) { return Math.hypot(d[0], d[1]); }
  function edgeNormal(p1, p2) {
    const d = [p2[0] - p1[0], p2[1] - p1[1]];
    const m = norm2(d);
    const dn = [d[0] / m, d[1] / m];
    return sign > 0 ? [dn[1], -dn[0]] : [-dn[1], dn[0]];
  }

  const out = [];
  for (let i = 0; i < n; i++) {
    const pPrev = loopUV[(i - 1 + n) % n], pCur = loopUV[i], pNext = loopUV[(i + 1) % n];
    const n1 = edgeNormal(pPrev, pCur);
    const n2 = edgeNormal(pCur, pNext);
    let avg = [n1[0] + n2[0], n1[1] + n2[1]];
    const normAvg = norm2(avg);
    const avgDir = normAvg < 1e-9 ? n1 : [avg[0] / normAvg, avg[1] / normAvg];
    const cosHalf = avgDir[0] * n1[0] + avgDir[1] * n1[1];
    const miter = Math.abs(cosHalf) > 1e-3 ? distance / cosHalf : distance;
    out.push([pCur[0] + avgDir[0] * miter, pCur[1] + avgDir[1] * miter]);
  }
  return out;
}

// Direzione (du,dv) unitaria, nel piano locale (u,v), corrispondente
// all'azimut di bussola dato.
function localOutwardDirUV(church, wallAzimuthDeg) {
  const th = (Math.PI / 180) * wallAzimuthDeg;
  const east = Math.sin(th), north = Math.cos(th);
  const [u, v] = church.enuToLocalUV(east, north);
  const mag = Math.hypot(u, v);
  return [u / mag, v / mag];
}

// ---------------------------------------------------------------
// Costruttori di mesh elementari — ciascuno ritorna
// {positions: number[][], indices: number[][]} (indici LOCALI a
// questo pezzo, da fondere con mergeParts)
// ---------------------------------------------------------------

function ptsLocalToWorld(church, ptsUVW) {
  return ptsUVW.map(([u, v, w]) => church.localToEnu(u, v, w));
}

function flatPolygon(loopUV, z, church, reverse = false) {
  const order = reverse ? [...loopUV].reverse() : loopUV;
  const positions = ptsLocalToWorld(church, order.map(([u, v]) => [u, v, z]));
  const tris = triangulatePolygon(order);
  return { positions, indices: tris };
}

function verticalBand(loopUV, z0, z1, church, closed = true) {
  const n = loopUV.length;
  const positions = ptsLocalToWorld(church, [
    ...loopUV.map(([u, v]) => [u, v, z0]),
    ...loopUV.map(([u, v]) => [u, v, z1]),
  ]);
  const indices = [];
  const nEdges = closed ? n : n - 1;
  for (let i = 0; i < nEdges; i++) {
    const j = (i + 1) % n;
    indices.push([i, j, n + j], [i, n + j, n + i]);
  }
  return { positions, indices };
}

function ringCap(innerLoopUV, outerLoopUV, z, church) {
  const n = innerLoopUV.length;
  const positions = ptsLocalToWorld(church, [
    ...innerLoopUV.map(([u, v]) => [u, v, z]),
    ...outerLoopUV.map(([u, v]) => [u, v, z]),
  ]);
  const indices = [];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    indices.push([i, j, n + j], [i, n + j, n + i]);
  }
  return { positions, indices };
}

// Fonde piu' parti {positions,indices} in una sola, correggendo gli
// indici (equivalente a PyVista .merge())
function mergeParts(parts) {
  const positions = [];
  const indices = [];
  let offset = 0;
  for (const part of parts) {
    for (const p of part.positions) positions.push(p);
    for (const [a, b, c] of part.indices) indices.push([a + offset, b + offset, c + offset]);
    offset += part.positions.length;
  }
  return { positions, indices };
}

function toBufferGeometry(part) {
  const geom = new THREE.BufferGeometry();
  const posArray = new Float32Array(part.positions.length * 3);
  for (let i = 0; i < part.positions.length; i++) {
    posArray[i * 3] = part.positions[i][0];
    posArray[i * 3 + 1] = part.positions[i][1];
    posArray[i * 3 + 2] = part.positions[i][2];
  }
  geom.setAttribute("position", new THREE.BufferAttribute(posArray, 3));
  const idxFlat = new Uint32Array(part.indices.length * 3);
  for (let i = 0; i < part.indices.length; i++) {
    idxFlat[i * 3] = part.indices[i][0];
    idxFlat[i * 3 + 1] = part.indices[i][1];
    idxFlat[i * 3 + 2] = part.indices[i][2];
  }
  geom.setIndex(new THREE.BufferAttribute(idxFlat, 1));
  geom.computeVertexNormals();
  return geom;
}

// ---------------------------------------------------------------
// Componenti principali dell'edificio
// ---------------------------------------------------------------

function buildFloor(innerLoopUV, church, thickness = FLOOR_THICKNESS_M) {
  const top = flatPolygon(innerLoopUV, 0.0, church, false);
  const bottom = flatPolygon(innerLoopUV, -thickness, church, true);
  const side = verticalBand(innerLoopUV, -thickness, 0.0, church);
  return mergeParts([top, bottom, side]);
}

function buildWalls(innerLoopUV, church, thickness = WALL_THICKNESS_M, height = WALL_HEIGHT_M) {
  const outerLoopUV = offsetLoopOutward(innerLoopUV, thickness);
  const outerBand = verticalBand(outerLoopUV, 0.0, height, church);
  const innerBand = verticalBand(innerLoopUV, 0.0, height, church);
  const topRing = ringCap(innerLoopUV, outerLoopUV, height, church);
  const bottomRing = ringCap(innerLoopUV, outerLoopUV, 0.0, church);
  const mesh = mergeParts([outerBand, innerBand, topRing, bottomRing]);
  return { mesh, outerLoopUV };
}

// Tetto a CAPANNA (due falde rettangolari + due frontoni triangolari
// alle estremita'), con un vero COLMO LINEARE lungo l'asse u (a v=0)
// - vedi il commento corrispondente in build_roof() (church_mesh.py)
// per la spiegazione completa (era un ventaglio da un punto centrale,
// che produceva una piramide a 4 falde invece di un tetto a capanna).
function buildRoof(outerLoopUV, church, wallHeight, ridgeRise = ROOF_RIDGE_RISE_M) {
  const uMin = Math.min(...outerLoopUV.map(([u]) => u));
  const uMax = Math.max(...outerLoopUV.map(([u]) => u));
  const vMin = Math.min(...outerLoopUV.map(([, v]) => v));
  const vMax = Math.max(...outerLoopUV.map(([, v]) => v));
  const ridgeH = wallHeight + ridgeRise;

  const eave00 = [uMin, vMax, wallHeight];
  const eave01 = [uMin, vMin, wallHeight];
  const eave10 = [uMax, vMax, wallHeight];
  const eave11 = [uMax, vMin, wallHeight];
  const ridge0 = [uMin, 0.0, ridgeH];
  const ridge1 = [uMax, 0.0, ridgeH];

  const ptsUVW = [eave00, eave01, eave10, eave11, ridge0, ridge1];
  const positions = ptsLocalToWorld(church, ptsUVW);
  // 0=eave00 1=eave01 2=eave10 3=eave11 4=ridge0 5=ridge1
  const indices = [
    [0, 2, 5], [0, 5, 4],   // falda Ovest
    [1, 4, 5], [1, 5, 3],   // falda Est
    [0, 4, 1],              // frontone facciata
    [2, 3, 5],              // frontone abside
  ];
  return { positions, indices };
}

// Tetto basso (a falda unica) sopra le nicchie delle cappelle, su
// entrambi i lati - separato dal tetto principale della navata.
// Gronda (bordo esterno) a eaveHeight [magenta, Elevation Sud,
// 9.64 m]; leggermente piu' alto (+pitchRise, stimato) sul bordo
// interno dove incontra il muro alto della navata.
// Muro BASSO + tetto delle nicchie delle cappelle (8 strutture
// separate, una per nicchia), che sostituiscono la porzione di muro
// ALTO in quelle zone: il "nucleo" navata+abside (vedi
// ChurchModel.coreOutlineLocal()) e' costruito senza le nicchie
// sporgenti, e per ciascuna delle 8 nicchie si costruisce qui una
// struttura a se' stante che si ferma all'altezza del tetto basso
// delle cappelle, invece di proseguire fino a WALL_HEIGHT_M.
function buildChapelWallStructures(church, eaveHeight = CHAPEL_ROOF_HEIGHT_M, pitchRise = CHAPEL_ROOF_PITCH_RISE_M) {
  const dw = CHAPEL_PROJECTION_WIDTH_M / 2.0;
  const dd = CHAPEL_PROJECTION_DEPTH_M;
  const Wh = church.naveWidthM / 2.0;
  const chapelUs = church.chapelUPositions();
  const hInner = eaveHeight + pitchRise;
  const hOuter = eaveHeight;

  function oneNiche(uCenter, vWall, vFar, mirror) {
    // Il muro nucleo ha spessore reale e si estende da vWall verso
    // l'ESTERNO - per sovrapporsi davvero al suo volume solido
    // (elimina ogni possibile z-fighting/varco visivo) l'estensione
    // va nella STESSA direzione, non solo a toccare il bordo.
    const OVERLAP_M = 0.05;
    const vWallExt = !mirror ? vWall + OVERLAP_M : vWall - OVERLAP_M;
    const loop = [
      [uCenter - dw, vWallExt], [uCenter - dw, vFar],
      [uCenter + dw, vFar], [uCenter + dw, vWallExt],
    ];
    const heights = [hInner, hOuter, hOuter, hInner];
    const n = loop.length;
    const ptsUVW = [
      ...loop.map(([u, v]) => [u, v, 0.0]),
      ...loop.map(([u, v], i) => [u, v, heights[i]]),
    ];
    const positions = ptsLocalToWorld(church, ptsUVW);
    const indices = [];
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      const quad = !mirror ? [i, j, n + j, n + i] : [n + i, n + j, j, i];
      indices.push([quad[0], quad[1], quad[2]], [quad[0], quad[2], quad[3]]);
    }
    if (!mirror) {
      indices.push([n, n + 1, n + 2], [n, n + 2, n + 3]);
    } else {
      indices.push([n + 3, n + 2, n + 1], [n + 3, n + 1, n]);
    }
    return { positions, indices };
  }

  const parts = [];
  for (const u of chapelUs) {
    parts.push(oneNiche(u, Wh, Wh + dd, false));       // Ovest
    parts.push(oneNiche(u, -Wh, -Wh - dd, true));       // Est
  }

  // NOTA: fra una nicchia e la successiva NON serve un pannello di
  // collegamento aggiuntivo: il muro "nucleo" della navata
  // (church.naveOnlyOutlineLocal(), un semplice rettangolo continuo
  // da u=0 a u=naveLengthM a v=+-Wh, altezza piena) copre gia' con
  // continuita' tutto lo spazio fra una nicchia e l'altra - un
  // pannello aggiuntivo nello stesso identico piano (v=Wh) causava
  // z-fighting col muro nucleo, che a certi angoli di vista faceva
  // sparire ENTRAMBE le superfici, mostrando un varco visivo (bug
  // segnalato dall'utente e verificato).

  return mergeParts(parts);
}

// Pilastri SOLIDI e OPACHI fra le nicchie delle cappelle adiacenti (sul
// filo del muro nucleo), dal pavimento fino all'altezza di gronda - vedi
// build_chapel_piers() in church_mesh.py per la spiegazione completa
// (garantiscono che la fascia si legga sempre come muratura solida,
// indipendentemente dal meccanismo esatto di eventuale trasparenza
// multipla che faceva apparire un varco a certi angoli di vista).
// Fascia SOLIDA e OPACA continua su TUTTA la lunghezza della navata
// (non solo negli spazi fra una nicchia e la successiva), sul filo
// del muro nucleo - vedi build_chapel_piers() in church_mesh.py per
// la spiegazione completa (volutamente ridondante con le nicchie
// stesse per eliminare qualsiasi possibilita' di varco visivo).
// Riempimenti SOLIDI negli spazi fra una nicchia di cappella e la
// successiva (e prima della prima/dopo l'ultima) - SPORGONO alla
// STESSA profondita' delle nicchie (fino a v=Wh+CHAPEL_PROJECTION_DEPTH_M),
// non restano sul filo del muro nucleo: l'utente ha chiarito che il
// problema era una RIENTRANZA visibile dall'esterno, non un varco
// nella mesh - vedi build_chapel_piers() in church_mesh.py.
function buildChapelPiers(church, eaveHeight = CHAPEL_ROOF_HEIGHT_M, pitchRise = CHAPEL_ROOF_PITCH_RISE_M) {
  const L = church.naveLengthM;
  const Wh = church.naveWidthM / 2.0;
  const dd = CHAPEL_PROJECTION_DEPTH_M;
  const margin = CHAPEL_ROW_MARGIN_M;
  const chapelUs = church.chapelUPositions();
  const dw = CHAPEL_PROJECTION_WIDTH_M / 2.0;
  const hInner = eaveHeight + pitchRise;
  const hOuter = eaveHeight;

  const edges = [margin];
  for (const u of chapelUs) { edges.push(u - dw); edges.push(u + dw); }
  edges.push(L - margin);
  const segments = [];
  for (let i = 0; i < edges.length - 1; i += 2) segments.push([edges[i], edges[i + 1]]);

  function fillBox(u0, u1, vNear, vFar, hNear, hFar) {
    const loop = [[u0, vNear], [u0, vFar], [u1, vFar], [u1, vNear]];
    const heights = [hNear, hFar, hFar, hNear];
    const n = loop.length;
    const ptsUVW = [...loop.map(([u, v]) => [u, v, 0.0]), ...loop.map(([u, v], i) => [u, v, heights[i]])];
    const positions = ptsLocalToWorld(church, ptsUVW);
    const indices = [];
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      indices.push([i, j, n + j], [i, n + j, n + i]);
    }
    indices.push([n, n + 1, n + 2], [n, n + 2, n + 3]); // tappo superiore (inclinato)
    return { positions, indices };
  }

  const parts = [];
  for (const [u0, u1] of segments) {
    parts.push(fillBox(u0, u1, Wh, Wh + dd, hInner, hOuter));
    parts.push(fillBox(u0, u1, -Wh, -Wh - dd, hInner, hOuter));
  }
  return mergeParts(parts);
}

// CORRETTO definitivamente sulla base di una FOTO REALE del tetto
// dell'abside vista da dietro la chiesa (Elevation Nord - chevet,
// fornita dall'utente): e' un classico tetto a PADIGLIONE SIMMETRICO
// ("cono"/piramide a base pentagonale) - tutte e 5 le falde salgono
// con la STESSA pendenza da un muro perimetrale ad altezza COSTANTE
// fino a un UNICO colmo centrale. Non e' ne' una falda unica
// asimmetrica ne' una struttura a 5 falde con due triangoli ripidi
// (entrambi tentativi precedenti, basati su un'interpretazione
// errata delle quote colorate sull'elevazione tecnica invece che
// sulla forma reale fotografata).
// CORRETTO sulla base di una FOTO REALE del tetto dell'abside vista
// da dietro la chiesa (Elevation Nord - chevet): tetto a PADIGLIONE
// SIMMETRICO ("cono"/piramide a base pentagonale) - tutte e 5 le
// falde salgono con la STESSA pendenza da un muro perimetrale ad
// altezza COSTANTE fino a un UNICO colmo centrale.
//
// Costruito come UN UNICO oggetto con un solo array di punti
// condiviso fra muro e tetto (non piu' pezzi separati uniti con
// mergeParts()): un tentativo precedente teneva muro e tetto come
// oggetti distinti con punti duplicati alla stessa posizione fisica -
// con la trasparenza reale usata dall'app (opacita' 0.4) minuscole
// discrepanze di virgola mobile fra i due calcoli separati
// lasciavano una fessura visibile (segnalata dall'utente con
// screenshot: si vedeva attraverso il tetto fino alla foto interna).
// Include anche i pannelli di raccordo verticali ai due angoli della
// "bocca" (dove l'abside tocca il campanile).
// CORRETTO sulla base di una FOTO REALE del tetto dell'abside vista
// da dietro la chiesa (Elevation Nord - chevet): tetto a PADIGLIONE
// SIMMETRICO ("cono"/piramide a base pentagonale) - tutte e 5 le
// falde salgono con la STESSA pendenza da un muro perimetrale ad
// altezza COSTANTE fino a un UNICO colmo centrale.
//
// Costruito come UN UNICO oggetto con un solo array di punti
// condiviso fra muro e tetto (non pezzi separati uniti con
// mergeParts()). Include due PANNELLI RETTANGOLARI (falde 1 e 5, i
// due lati del pentagono adiacenti al campanile) che collegano il
// campanile al resto del tetto - sostituiscono sottili strisce
// verticali di un tentativo precedente, rivelatesi insufficienti a
// coprire il varco (segnalato dall'utente con screenshot: "riempi
// con due tetti rettangolari per i pannelli 1 e 5").
function buildApseWallStructure(church, wallHeight = APSE_EXTERNAL_HEIGHT_M, ridgeRise = APSE_ROOF_RIDGE_RISE_M) {
  const apseLoop = church.apseVertices();
  const Wh = church.naveWidthM / 2.0;
  const L = church.naveLengthM;
  const loop = [[L, Wh], ...apseLoop, [L, -Wh]];
  const n = loop.length;

  let cu = 0, cv = 0;
  for (const [u, v] of apseLoop) { cu += u; cv += v; }
  cu /= apseLoop.length; cv /= apseLoop.length;
  const ridgeH = wallHeight + ridgeRise;

  const OVERLAP_M = 0.05;
  const fillH = TOWER_BODY_HEIGHT_M;
  const [mouthWU, mouthWV] = loop[0];
  const [mouthEU, mouthEV] = loop[loop.length - 1];
  const [pent0U, pent0V] = apseLoop[0];
  const [pent5U, pent5V] = apseLoop[5];

  const allPtsUVW = [
    ...loop.map(([u, v]) => [u, v, 0.0]),
    ...loop.map(([u, v]) => [u, v, wallHeight]),
    [cu, cv, ridgeH],
    // pannello Ovest (falda 1): rettangolo dalla bocca al primo
    // vertice del pentagono, dal filo del muro fino all'altezza del
    // campanile - sovrapposto di 5 cm oltre la bocca.
    [mouthWU - OVERLAP_M, mouthWV, wallHeight], [pent0U, pent0V, wallHeight],
    [pent0U, pent0V, fillH], [mouthWU - OVERLAP_M, mouthWV, fillH],
    // pannello Est (falda 5), speculare
    [mouthEU - OVERLAP_M, mouthEV, wallHeight], [pent5U, pent5V, wallHeight],
    [pent5U, pent5V, fillH], [mouthEU - OVERLAP_M, mouthEV, fillH],
  ];
  const positions = ptsLocalToWorld(church, allPtsUVW);
  const IDX_RIDGE = 2 * n;
  const IDX_FW0 = 2 * n + 1, IDX_FW1 = 2 * n + 2, IDX_FW2 = 2 * n + 3, IDX_FW3 = 2 * n + 4;
  const IDX_FE0 = 2 * n + 5, IDX_FE1 = 2 * n + 6, IDX_FE2 = 2 * n + 7, IDX_FE3 = 2 * n + 8;

  const indices = [];
  // muro (aperto verso la bocca: non chiude l'ultimo lato)
  for (let i = 0; i < n - 1; i++) {
    const j = i + 1;
    indices.push([i, j, n + j], [i, n + j, n + i]);
  }
  // tetto: SEPARATO in due parti (bug reale trovato: il verso di
  // avvolgimento del ventaglio unico su tutti gli 8 punti del loop
  // era invertito - normali rivolte verso l'interno invece che verso
  // l'esterno, causa del varco "sempre li', molto largo, due parti"
  // segnalato dall'utente - confermato con calcolo diretto delle
  // normali via prodotto vettoriale). 1) ventaglio SOLO sui 6
  // vertici del vero pentagono (verificato a stella valida).
  for (let i = 1; i < n - 2; i++) {
    const j = i + 1;
    indices.push([IDX_RIDGE, n + j, n + i]);
  }
  // 2) due triangoli espliciti per le sezioni di ritorno (bocca ->
  //    primo/ultimo vertice pentagono), stesso verso corretto.
  indices.push([IDX_RIDGE, n + 0, n + 1]);
  indices.push([IDX_RIDGE, n + (n - 2), n + (n - 1)]);
  // pannelli RETTANGOLARI (falde 1 e 5) verso il campanile
  indices.push([IDX_FW3, IDX_FW2, IDX_FW1], [IDX_FW3, IDX_FW1, IDX_FW0]);
  indices.push([IDX_FE3, IDX_FE2, IDX_FE1], [IDX_FE3, IDX_FE1, IDX_FE0]);

  return { positions, indices };
}

function buildWindowSolid(win, church, wallThickness = WALL_THICKNESS_M, recessFromExterior = 0.0) {
  const outlineInner = win.localOutline();
  const [du, dv] = localOutwardDirUV(church, win.wallAzimuthDeg);
  const inset = -0.03 - recessFromExterior, outset = wallThickness + 0.03 - recessFromExterior;
  const innerPts = outlineInner.map(([u, v, w]) => [u + du * inset, v + dv * inset, w]);
  const outerPts = outlineInner.map(([u, v, w]) => [u + du * outset, v + dv * outset, w]);
  const n = innerPts.length;
  const positions = ptsLocalToWorld(church, [...innerPts, ...outerPts]);
  const indices = [];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    indices.push([i, j, n + j], [i, n + j, n + i]);
  }
  // tappi (poligono convesso: fan dal primo vertice va bene)
  for (let i = 1; i < n - 1; i++) indices.push([0, i, i + 1]);
  for (let i = 1; i < n - 1; i++) indices.push([n, n + i + 1, n + i]);
  return { positions, indices };
}

function buildTower(
  church,
  uCenter = TOWER_U_CENTER_M,
  vCenter = TOWER_V_CENTER_M,
  widthU = TOWER_WIDTH_U_M,
  widthV = TOWER_WIDTH_V_M,
  bodyHeight = TOWER_BODY_HEIGHT_M,
  spireHeight = TOWER_SPIRE_HEIGHT_M,
) {
  const hu = widthU / 2.0, hv = widthV / 2.0;
  const footprint = [
    [uCenter - hu, vCenter - hv],
    [uCenter + hu, vCenter - hv],
    [uCenter + hu, vCenter + hv],
    [uCenter - hu, vCenter + hv],
  ];

  const outerBand = verticalBand(footprint, 0.0, bodyHeight, church);
  const bottomCap = flatPolygon(footprint, 0.0, church, true);
  const topCapBody = flatPolygon(footprint, bodyHeight, church, false);

  // guglia: piramide a base rettangolare, apice sopra il centro
  const apexWorld = church.localToEnu(uCenter, vCenter, bodyHeight + spireHeight);
  const baseWorld = ptsLocalToWorld(church, footprint.map(([u, v]) => [u, v, bodyHeight]));
  const n = footprint.length;
  const spirePositions = [apexWorld, ...baseWorld];
  const spireIndices = [];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    spireIndices.push([0, 1 + i, 1 + j]);
  }
  const spire = { positions: spirePositions, indices: spireIndices };

  return mergeParts([outerBand, bottomCap, topCapBody, spire]);
}

// Nartece/vestibolo coperto all'ingresso: struttura SOLIDA e OPACA
// (non lascia passare luce) attaccata all'interno del muro di
// facciata, sopra il portale. Soffitto a profilo curvo (quarto di
// coseno fra i due punti quotati), largo `width` (centrato
// sull'asse), profondo `depth` dal muro. Chiuso anche sui due fianchi
// e sul fondo per essere un solido vero e proprio.
function buildNarthexVault(
  church,
  width = NARTHEX_WIDTH_M,
  depth = NARTHEX_DEPTH_M,
  heightAtWall = NARTHEX_HEIGHT_AT_WALL_M,
  heightAtEdge = NARTHEX_HEIGHT_AT_EDGE_M,
  nSegments = 10,
) {
  const hv = width / 2.0;
  const deltaH = heightAtWall - heightAtEdge;

  const profile = [];
  for (let i = 0; i <= nSegments; i++) {
    const t = i / nSegments;
    const u = depth * t;
    const w = heightAtEdge + deltaH * Math.cos(Math.PI / 2.0 * t);
    profile.push([u, w]);
  }
  const n = profile.length;

  // soffitto: superficie rigata fra i due fianchi, seguendo il profilo
  const ceilingUVW = [
    ...profile.map(([u, w]) => [u, hv, w]),
    ...profile.map(([u, w]) => [u, -hv, w]),
  ];
  const ceilingPositions = ptsLocalToWorld(church, ceilingUVW);
  const ceilingIndices = [];
  for (let i = 0; i < n - 1; i++) {
    const j = i + 1;
    ceilingIndices.push([i, j, n + j], [i, n + j, n + i]);
  }
  const ceiling = { positions: ceilingPositions, indices: ceilingIndices };

  // fianchi: riempiono il profilo curvo fino al pavimento
  function sideWall(v, reverse) {
    const ptsUVW = [...profile.map(([u]) => [u, v, 0.0]), ...profile.map(([u, w]) => [u, v, w])];
    const positions = ptsLocalToWorld(church, ptsUVW);
    const indices = [];
    for (let i = 0; i < n - 1; i++) {
      const j = i + 1;
      const quad = reverse ? [n + i, n + j, j, i] : [i, j, n + j, n + i];
      indices.push([quad[0], quad[1], quad[2]], [quad[0], quad[2], quad[3]]);
    }
    return { positions, indices };
  }
  const sidePos = sideWall(hv, false);
  const sideNeg = sideWall(-hv, true);

  // parete di fondo (al bordo esterno): chiude il solido verso la navata
  const [uFar, wFar] = profile[profile.length - 1];
  const backPositions = ptsLocalToWorld(church, [
    [uFar, hv, 0.0], [uFar, -hv, 0.0], [uFar, -hv, wFar], [uFar, hv, wFar],
  ]);
  const backWall = { positions: backPositions, indices: [[0, 1, 2], [0, 2, 3]] };

  return mergeParts([ceiling, sidePos, sideNeg, backWall]);
}

// Costruisce tutte le mesh solide dell'edificio. Ritorna
// { floor, walls, roof, tower, windows } — ciascuna {positions,indices},
// pronte per toBufferGeometry().
function buildAll(church, wallHeight = WALL_HEIGHT_M) {
  const innerLoopFull = church.floorOutlineLocal().slice(0, -1);
  const innerLoopNave = church.naveOnlyOutlineLocal().slice(0, -1);

  const floor = buildFloor(innerLoopFull, church);
  const { mesh: walls, outerLoopUV } = buildWalls(innerLoopNave, church, WALL_THICKNESS_M, wallHeight);
  const roof = buildRoof(outerLoopUV, church, wallHeight);
  const chapelWalls = buildChapelWallStructures(church);
  const chapelPiers = buildChapelPiers(church);
  const apseStructure = buildApseWallStructure(church);
  const windows = {};
  // NOTA: CHAPEL_WINDOW_RECESS_M (1.31 m) non e' piu' applicato: le
  // vetrate delle cappelle sono tornate sul muro navata (v=Wh) per
  // risolvere il conflitto con l'altezza del tetto basso delle
  // cappelle - vedi il commento in church-geometry.js.
  for (const w of church.windows) windows[w.name] = buildWindowSolid(w, church);
  const tower = buildTower(church);
  const narthex = buildNarthexVault(church);

  return { floor, walls, roof, chapelWalls, chapelPiers, apseStructure, tower, narthex, windows };
}
