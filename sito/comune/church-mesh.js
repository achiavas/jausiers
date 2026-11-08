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

// Prisma verticale da 0 a h sul contorno loopUV (senza fondo)
function prisma(loopUV, h, church) {
  return mergeParts([flatPolygon(loopUV, h, church, false), verticalBand(loopUV, 0.0, h, church)]);
}

// Tre gradini davanti all'arco trionfale, larghi quanto l'apertura
// dell'abside, piu' il pavimento rialzato dell'abside (vedi
// quotaPavimento in church-geometry.js).
function buildGradini(church) {
  const L = church.naveLengthM;
  const vh = church.naveWidthM / 2.0 - APSE_RECESS_M;
  const parti = [];
  for (let k = 1; k <= GRADINI_N; k++) {
    const u0 = L - (GRADINI_N - k + 1) * GRADINO_PEDATA_M;
    const u1 = L - (GRADINI_N - k) * GRADINO_PEDATA_M;
    parti.push(prisma([[u0, vh], [u1, vh], [u1, -vh], [u0, -vh]], k * GRADINO_ALZATA_M, church));
  }
  parti.push(prisma(church.apseVertices(), GRADINI_N * GRADINO_ALZATA_M, church));
  // due gradini all'ingresso di ogni cappella e il suo piano rialzato
  const wh = church.naveWidthM / 2.0, a = CAPPELLA_GRADINO_ALZATA_M, p = CAPPELLA_GRADINO_PEDATA_M, R = CHAPEL_ARCH_RADIUS_M;
  const dd = CHAPEL_PROJECTION_DEPTH_M, dw = CHAPEL_PROJECTION_WIDTH_M;
  for (const uc of church.chapelUPositions()) {
    for (const lato of [1.0, -1.0]) {
      for (const [v0, v1, u0, u1, h] of [[wh - p, wh, uc - R, uc + R, a],
        [wh, wh + p, uc - R, uc + R, CAPPELLA_GRADINI_N * a],
        [wh + p, wh + dd, uc - dw / 2, uc + dw / 2, CAPPELLA_GRADINI_N * a]]) {
        const lo = Math.min(lato * v0, lato * v1), hi = Math.max(lato * v0, lato * v1);
        parti.push(prisma([[u0, hi], [u1, hi], [u1, lo], [u0, lo]], h, church));
      }
    }
  }
  return mergeParts(parti);
}

// Solido chiuso: contorno loopUV (stesso verso del pavimento) da w0 a w1
function scatola(loopUV, w0, w1, church) {
  return mergeParts([flatPolygon(loopUV, w1, church, false), flatPolygon(loopUV, w0, church, true),
    verticalBand(loopUV, w0, w1, church)]);
}
function blocco(u0, u1, v0, v1, w0, w1, church) {
  const lo = Math.min(v0, v1), hi = Math.max(v0, v1);
  return scatola([[u0, hi], [u1, hi], [u1, lo], [u0, lo]], w0, w1, church);
}

// Banchi di legno in due file ai lati del corridoio: per ogni banco
// sedile, schienale (verso la facciata: si guarda l'abside) e due
// fianchi. Dal fondo fino a ~1.5 m dal primo gradino.
function buildBanchi(church) {
  return mergeParts(banchiScatole(church).map(([u0, u1, v0, v1, w0, w1]) => blocco(u0, u1, v0, v1, w0, w1, church)));
}

// Balaustra in ferro in cima ai gradini: corrimano, traversa bassa,
// montanti ogni ~1.2 m e sbarre sottili ogni 12 cm, in due tratti ai
// lati del varco centrale.
function buildBalaustra(church) {
  const q = GRADINI_N * GRADINO_ALZATA_M;
  const h = BALAUSTRA_ALTEZZA_M;
  const u = BALAUSTRA_U_M;
  const vh = church.naveWidthM / 2.0 - APSE_RECESS_M;
  const parti = [];
  for (const lato of [1.0, -1.0]) {
    const a = lato * BALAUSTRA_VARCO_M / 2, b = lato * vh;
    parti.push(blocco(u - 0.05, u + 0.05, a, b, q + h - 0.06, q + h, church));    // corrimano
    parti.push(blocco(u - 0.02, u + 0.02, a, b, q + 0.06, q + 0.10, church));     // traversa bassa
    const lung = Math.abs(b - a);
    const nMont = Math.max(1, Math.round(lung / 1.2));
    for (let k = 0; k <= nMont; k++) {
      const v = a + (b - a) * k / nMont;
      parti.push(blocco(u - 0.03, u + 0.03, v - 0.03, v + 0.03, q, q + h, church));
    }
    const nSbarre = Math.floor(lung / 0.12);
    for (let k = 1; k < nSbarre; k++) {
      const v = a + (b - a) * k / nSbarre;
      parti.push(blocco(u - 0.01, u + 0.01, v - 0.01, v + 0.01, q + 0.10, q + h - 0.06, church));
    }
  }
  return mergeParts(parti);
}

// L'altare in cima ai gradini (tavolo con tovaglia bianca): base in
// marmo e tovaglia che ricade sui lati. Ritorna { marmo, tovaglia }.
function buildAltari(church) {
  const q = GRADINI_N * GRADINO_ALZATA_M;
  const h = ALTARE_ALTEZZA_M;
  const u0 = ALTARE_U_CENTRO_M - ALTARE_PROFONDITA_M / 2, u1 = ALTARE_U_CENTRO_M + ALTARE_PROFONDITA_M / 2;
  const hw = ALTARE_LARGHEZZA_M / 2;
  return {
    marmo: blocco(u0 + 0.08, u1 - 0.08, -hw + 0.08, hw - 0.08, q, q + h - 0.02, church),
    tovaglia: blocco(u0, u1, -hw, hw, q + h - 0.30, q + h, church),
  };
}

// Armadi in legno del riscaldamento ai due lati dell'abside: cassa
// alta, cornice in cima e griglia a lamelle sul fronte (verso la
// navata) nella parte alta.
function buildRiscaldamento(church) {
  const q = GRADINI_N * GRADINO_ALZATA_M;
  const h = RISCALDAMENTO_ALTEZZA_M;
  const du = RISCALDAMENTO_PROFONDITA_M / 2, dv = RISCALDAMENTO_LARGHEZZA_M / 2;
  const u0 = RISCALDAMENTO_U_M - du, u1 = RISCALDAMENTO_U_M + du;
  const parti = [];
  for (const lato of [1.0, -1.0]) {
    const c = lato * RISCALDAMENTO_V_M;
    parti.push(blocco(u0, u1, c - dv, c + dv, q, q + h, church));                                  // cassa
    parti.push(blocco(u0 - 0.04, u1 + 0.04, c - dv - 0.04, c + dv + 0.04, q + h - 0.08, q + h, church));  // cornice
    parti.push(blocco(u0 - 0.03, u1, c - dv - 0.02, c + dv + 0.02, q, q + 0.12, church));           // zoccolo
    for (let k = 0; k < 8; k++) {                                                                    // lamelle
      const w = q + h - 1.25 + k * 0.14;
      parti.push(blocco(u0 - 0.04, u0, c - dv + 0.06, c + dv - 0.06, w, w + 0.05, church));
    }
  }
  return mergeParts(parti);
}

function ottagono(cu, cv, r) {
  const pts = [];
  for (let k = 0; k < 8; k++) {
    const a = Math.PI / 8 + k * Math.PI / 4;
    pts.push([cu + r * Math.cos(a), cv + r * Math.sin(a)]);
  }
  return signedArea(pts) < 0 ? pts : pts.reverse();
}

// Piramide dal contorno loopUV a quota w0 fino a punta = [u, v, w]
function piramide(loopUV, w0, punta, church) {
  const n = loopUV.length;
  const positions = ptsLocalToWorld(church, [...loopUV.map(([u, v]) => [u, v, w0]), punta]);
  const indices = [];
  for (let i = 0; i < n; i++) indices.push([i, (i + 1) % n, n]);
  return mergeParts([{ positions, indices }, flatPolygon(loopUV, w0, church, true)]);
}

// Pulpito in legno sul pilastro fra due cappelle a sinistra entrando
// (v = +Wh): sostegno, cassa ottagonale con cornici, pannello contro il
// pilastro e baldacchino a piramide con un pinnacolo in cima.
function buildPulpito(church) {
  const us = church.chapelUPositions();
  const u = (us[PULPITO_FRA_CAPPELLE[0]] + us[PULPITO_FRA_CAPPELLE[1]]) / 2;
  const wh = church.naveWidthM / 2.0;
  const r = PULPITO_RAGGIO_M;
  const v = wh - 0.15 - r;                                   // centro della cassa, staccata dal pilastro
  const w0 = PULPITO_PIANO_M, w1 = PULPITO_PIANO_M + PULPITO_PARAPETTO_M;
  const parti = [
    blocco(u - 0.25, u + 0.25, v - 0.1, wh, 0.0, w0, church),                       // sostegno
    scatola(ottagono(u, v, r * 0.7), w0 - 0.35, w0, church),                        // fondo rastremato
    scatola(ottagono(u, v, r), w0, w1, church),                                     // cassa
    scatola(ottagono(u, v, r + 0.06), w0, w0 + 0.10, church),                       // cornice bassa
    scatola(ottagono(u, v, r + 0.08), w1 - 0.08, w1, church),                       // cornice alta
    blocco(u - 0.45, u + 0.45, wh - 0.10, wh, w1, PULPITO_BALDACCHINO_M, church),   // pannello sul pilastro
  ];
  const rb = r + 0.25;                                                               // baldacchino
  parti.push(scatola(ottagono(u, v, rb), PULPITO_BALDACCHINO_M, PULPITO_BALDACCHINO_M + 0.20, church));
  parti.push(piramide(ottagono(u, v, rb - 0.05), PULPITO_BALDACCHINO_M + 0.20, [u, v, PULPITO_CIMA_M], church));
  parti.push(blocco(u - 0.06, u + 0.06, v - 0.06, v + 0.06, PULPITO_CIMA_M - 0.2, PULPITO_CIMA_M + 0.35, church));
  return mergeParts(parti);
}

// Consolle dell'organo: cassa in legno chiaro con il leggio in cima
// (verso l'abside: l'organista guarda l'altare) e zoccolo scuro
// rientrato sotto (pedaliera). Ritorna { legno, zoccolo }.
function buildOrgano(church) {
  const du = ORGANO_PROFONDITA_M / 2, dv = ORGANO_LARGHEZZA_M / 2;
  const u = ORGANO_U_M, v = ORGANO_V_M, h = ORGANO_ALTEZZA_M;
  return {
    legno: mergeParts([
      blocco(u - du, u + du, v - dv, v + dv, 0.14, h, church),                          // cassa
      blocco(u + 0.05, u + 0.10, v - dv + 0.2, v + dv - 0.2, h, h + 0.38, church),      // leggio
      blocco(u - du - 0.02, u + du + 0.02, v - dv - 0.02, v + dv + 0.02, h - 0.03, h, church),  // coperchio
    ]),
    zoccolo: blocco(u - du + 0.08, u + du - 0.04, v - dv + 0.06, v + dv - 0.06, 0.0, 0.14, church),
  };
}

// Sull'altare: due candelieri dorati con candela accesa ai lati, un
// crocifisso dorato al centro (dalla parte dell'abside) e il messale
// rosso sul leggio, dalla parte del celebrante (verso l'abside: l'altare
// e' rivolto alla navata). Ritorna { oro, cera, fiamma, libro }.
function buildOggettiAltare(church) {
  const w = GRADINI_N * GRADINO_ALZATA_M + ALTARE_ALTEZZA_M;     // piano dell'altare
  const u = ALTARE_U_CENTRO_M;
  const ub = u + ALTARE_PROFONDITA_M / 2 - 0.15;                    // verso l'abside
  const oro = [], cera = [], fiamma = [];
  for (const v of [ALTARE_LARGHEZZA_M / 2 - 0.25, -(ALTARE_LARGHEZZA_M / 2 - 0.25)]) {
    oro.push(blocco(ub - 0.07, ub + 0.07, v - 0.07, v + 0.07, w, w + 0.04, church),              // piede
      blocco(ub - 0.015, ub + 0.015, v - 0.015, v + 0.015, w + 0.04, w + 0.34, church),          // fusto
      blocco(ub - 0.045, ub + 0.045, v - 0.045, v + 0.045, w + 0.34, w + 0.36, church));         // piattello
    cera.push(blocco(ub - 0.022, ub + 0.022, v - 0.022, v + 0.022, w + 0.36, w + 0.62, church));
    fiamma.push(blocco(ub - 0.008, ub + 0.008, v - 0.008, v + 0.008, w + 0.63, w + 0.67, church));
  }
  oro.push(blocco(ub - 0.08, ub + 0.08, -0.08, 0.08, w, w + 0.05, church),                        // crocifisso
    blocco(ub - 0.015, ub + 0.015, -0.015, 0.015, w + 0.05, w + 0.62, church),
    blocco(ub - 0.015, ub + 0.015, -0.12, 0.12, w + 0.45, w + 0.48, church));
  const ul = u + 0.05;                                                                              // messale
  const libro = mergeParts([blocco(ul - 0.12, ul + 0.12, 0.30, 0.56, w, w + 0.06, church),
    blocco(ul - 0.14, ul + 0.14, 0.28, 0.58, w + 0.06, w + 0.10, church)]);
  return { oro: mergeParts(oro), cera: mergeParts(cera), fiamma: mergeParts(fiamma), libro };
}

// profilo del cornicione: [da, a, sporgenza] in frazioni dell'altezza e
// della sporgenza totale, dal basso (vedi church_mesh.py)
const PROFILO_CORNICIONE = [[0.00, 0.13, 0.19], [0.13, 0.27, 0.26], [0.27, 0.63, 0.16],
  [0.63, 0.70, 0.40], [0.70, 0.78, 0.52], [0.78, 0.90, 0.60], [0.90, 1.00, 1.00]];

// Cornicione interno lungo i due fianchi della navata (sopra le cappelle)
// e la controfacciata, NON nell'abside: si ferma contro l'arco trionfale.
// Fasce sovrapposte che sporgono sempre di piu' verso l'alto, con le
// mensoline (ogni 0.5 m) sotto la cornice.
function buildCornicione(church) {
  const L = church.naveLengthM, wh = church.naveWidthM / 2.0;
  const muro = [[L, -wh], [0.0, -wh], [0.0, wh], [L, wh]];
  const dentro = (d) => [[L, -(wh - d)], [d, -(wh - d)], [d, wh - d], [L, wh - d]];
  const fascia = (a, b, w) => {
    const positions = ptsLocalToWorld(church, [...a.map(([u, v]) => [u, v, w]), ...b.map(([u, v]) => [u, v, w])]);
    const n = a.length, indices = [];
    for (let k = 0; k < n - 1; k++) indices.push([k, k + 1, n + k + 1], [k, n + k + 1, n + k]);
    return { positions, indices };
  };
  const h0 = CORNICIONE_BASE_M, H = CORNICIONE_CIMA_M - CORNICIONE_BASE_M, D = CORNICIONE_SPORGENZA_M;
  const parti = [];
  for (const [a, b, d] of PROFILO_CORNICIONE) {
    const w0 = h0 + a * H, w1 = h0 + b * H;
    const dd = dentro(d * D);
    parti.push(verticalBand(dd, w0, w1, church, false), fascia(muro, dd, w0), fascia(muro, dd, w1));
    for (const k of [0, muro.length - 1])          // testate contro l'arco trionfale
      parti.push(verticalBand([muro[k], dd[k]], w0, w1, church, false));
  }
  const wm0 = h0 + 0.70 * H, wm1 = h0 + 0.90 * H;
  for (let i = 0; i < muro.length - 1; i++) {
    const p = muro[i], q = muro[i + 1];
    const lung = Math.hypot(q[0] - p[0], q[1] - p[1]);
    const a = [(q[0] - p[0]) / lung, (q[1] - p[1]) / lung];
    const nrm = [a[1], -a[0]];                         // verso l'interno
    const k = Math.floor((lung - 0.5) / 0.5);
    for (let j = 0; j <= k; j++) {
      const t = 0.25 + j * (lung - 0.5) / Math.max(k, 1);
      const c = [p[0] + a[0] * t, p[1] + a[1] * t];
      let pts = [[-0.06, 0], [0.06, 0], [0.06, 0.9 * D], [-0.06, 0.9 * D]].map(([x, y]) =>
        [c[0] + a[0] * x + nrm[0] * y, c[1] + a[1] * x + nrm[1] * y]);
      if (signedArea(pts) > 0) pts = pts.reverse();
      parti.push(scatola(pts, wm0, wm1, church));
    }
  }
  return mergeParts(parti);
}

// Superficie da una griglia di punti locali punti[i][j] = [u, v, w]
function griglia(punti, church) {
  const ni = punti.length, nj = punti[0].length;
  const positions = ptsLocalToWorld(church, punti.flat());
  const indices = [];
  for (let i = 0; i < ni - 1; i++) for (let j = 0; j < nj - 1; j++) {
    const a = i * nj + j;
    indices.push([a, a + 1, a + nj + 1], [a, a + nj + 1, a + nj]);
  }
  return { positions, indices };
}

// Bordo della volta dell'abside (vedi church_mesh.py): i 5 lati del
// pentagono (imposta a lunetta sopra ogni finestra), poi l'arco trionfale.
function bordoVoltaAbside(church) {
  const ap = church.apseVertices();
  const w0 = CORNICIONE_CIMA_M, wc = VOLTA_ABSIDE_CHIAVE_M, wl = VOLTA_ABSIDE_LUNETTE_M;
  const pts = [];
  for (let i = 0; i < ap.length - 1; i++) {
    const p = ap[i], q = ap[i + 1];
    for (let k = 0; k < VOLTA_ABSIDE_NT; k++) {
      const t = k / VOLTA_ABSIDE_NT;
      pts.push([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, w0 + (wl - w0) * Math.sqrt(Math.max(Math.sin(Math.PI * t), 0.0))]);
    }
  }
  const va = ap[0][1], L = church.naveLengthM;
  for (let k = 0; k <= VOLTA_ABSIDE_NA; k++) {
    const f = Math.PI * k / VOLTA_ABSIDE_NA;
    pts.push([L, -va * Math.cos(f), w0 + (wc - w0) * Math.sin(f)]);
  }
  return pts;
}

// Volta a ombrello dell'abside: meridiani dal bordo alla chiave, sopra il
// centro dell'abside; uvs = (posizione lungo il bordo, frazione del meridiano),
// come la texture (volta_da_video.py). Ritorna { vele (con uvs), arco }.
function buildVoltaAbside(church) {
  const L = church.naveLengthM, wh = church.naveWidthM / 2.0;
  const ap = church.apseVertices();
  const w0 = CORNICIONE_CIMA_M, wc = VOLTA_ABSIDE_CHIAVE_M;
  const us = ap.map((p) => p[0]);
  const K = [(Math.min(...us) + Math.max(...us)) / 2, 0.0];
  const bordo = bordoVoltaAbside(church);
  const ths = [];
  for (let m = 0; m <= VOLTA_ABSIDE_NM; m++) ths.push(Math.PI / 2 * m / VOLTA_ABSIDE_NM);
  const vele = griglia(bordo.map((b) => ths.map((th) => [K[0] + (b[0] - K[0]) * Math.cos(th), K[1] + (b[1] - K[1]) * Math.cos(th),
    b[2] + (wc - b[2]) * Math.sin(th)])), church);
  const n = bordo.length;
  vele.uvs = [];
  for (let i = 0; i < n; i++) for (let m = 0; m <= VOLTA_ABSIDE_NM; m++) vele.uvs.push([i / (n - 1), m / VOLTA_ABSIDE_NM]);
  const va = ap[0][1];
  const righe = [];
  for (let k = 0; k <= 40; k++) {
    const v = -wh + 2 * wh * k / 40;
    const basso = Math.abs(v) < va ? w0 + (wc - w0) * Math.sqrt(Math.max(0, 1 - (v / va) ** 2)) : w0;
    righe.push([[L, v, basso], [L, v, WALL_HEIGHT_M]]);
  }
  return { vele, arco: griglia(righe, church) };
}

// Volta a botte della navata (vedi church_mesh.py): quarti d'ellisse dai
// fianchi al colmo, imposta a lunetta sopra ogni finestra alta.
function buildVoltaNavata(church) {
  const L = church.naveLengthM, wh = church.naveWidthM / 2.0;
  const w0 = CORNICIONE_CIMA_M, wc = VOLTA_NAVATA_CHIAVE_M, wl = VOLTA_NAVATA_LUNETTE_M;
  const meta = VOLTA_NAVATA_LUNETTA_LARGA_M / 2, ucs = church.chapelUPositions();
  const set = new Set([0, L]);
  for (const uc of ucs) for (let k = 0; k <= 12; k++) set.add(+(uc - meta + 2 * meta * k / 12).toFixed(6));
  for (let k = 0; k < 40; k++) set.add(+(L * k / 39).toFixed(6));
  const us = [...set].sort((a, b) => a - b);
  const imposta = (u) => {
    for (const uc of ucs) {
      const t = (u - uc + meta) / (2 * meta);
      if (t > 0 && t < 1) return w0 + (wl - w0) * Math.sqrt(Math.sin(Math.PI * t));
    }
    return w0;
  };
  const ths = [];
  for (let m = 0; m <= 12; m++) ths.push(Math.PI / 2 * m / 12);
  return mergeParts([1.0, -1.0].map((lato) => griglia(us.map((u) => ths.map((th) =>
    [u, lato * wh * Math.cos(th), imposta(u) + (wc - imposta(u)) * Math.sin(th)])), church)));
}

// Altare di ogni cappella (vedi church_mesh.py): mensa del colore del
// paliotto, tovaglia bianca, gradino sopra la mensa verso il fondo.
// [{nome, parti: {fronte, tovaglia, gradino}, cf, cg}]
function buildAltariCappelle(church) {
  const wh = church.naveWidthM / 2.0;
  const q = CAPPELLA_GRADINI_N * CAPPELLA_GRADINO_ALZATA_M;
  const hw = ALTARE_CAPPELLA_LARGHEZZA_M / 2, pr = ALTARE_CAPPELLA_PROFONDITA_M, h = ALTARE_CAPPELLA_ALTEZZA_M;
  return ALTARI_CAPPELLE.map(([nome, lato, i, cf, cg]) => {
    const uc = church.chapelUPositions()[i];
    const fondo = wh + CHAPEL_PROJECTION_DEPTH_M - 0.07;
    const v = (x) => lato * x;
    return { nome, cf, cg, parti: {
      fronte: blocco(uc - hw + 0.05, uc + hw - 0.05, v(fondo - pr + 0.05), v(fondo), q, q + h - 0.02, church),
      tovaglia: blocco(uc - hw, uc + hw, v(fondo - pr), v(fondo), q + h - 0.25, q + h, church),
      gradino: blocco(uc - hw + 0.15, uc + hw - 0.15, v(fondo - 0.32), v(fondo), q + h, q + h + 0.32, church),
    } };
  });
}

// Superficie di rivoluzione attorno all'asse verticale (cu, cv):
// profilo = [[quota, raggio]] dall'alto in basso
function tornio(profilo, cu, cv, church, n = 24, angoli = [0, 2 * Math.PI]) {
  const righe = [];
  for (let k = 0; k <= n; k++) {
    const a = angoli[0] + (angoli[1] - angoli[0]) * k / n;
    righe.push(profilo.map(([z, r]) => [cu + r * Math.cos(a), cv + r * Math.sin(a), z]));
  }
  return griglia(righe, church);
}

// Profilo di una coppa di cristalli a n gradini, da z0 (raggio r0) a z1
function coppa(z0, z1, r0, n = 5) {
  const prof = [], dz = (z0 - z1) / n;
  for (let k = 0; k < n; k++) {
    const r = r0 * Math.pow(1 - k / n, 0.8) + 0.06 * k / n;
    prof.push([z0 - k * dz, r], [z0 - (k + 1) * dz + 0.01, r * 0.9]);
  }
  prof.push([z1, 0.04]);
  return prof;
}

// Un lampadario di cristallo (vedi church_mesh.py): catena, corona, anello
// di candele, coppa a gradini, sfera; se doppio, fuso, secondo anello e
// seconda coppa. Ritorna [cristallo, oro, candele] come liste di parti.
function lampadario(cu, cv, aggancio, a, b, R1, R2, doppio, church) {
  const H = a - b;
  let z1, zc, rs;
  if (doppio) { z1 = a - 0.13 * H; zc = z1 - 0.25 * H; rs = 0.04 * H; }
  else { z1 = a - 0.16 * H; zc = b + 0.2 * H; rs = 0.06 * H; }
  const zs = zc - rs;
  const sfera = [];
  for (let k = 0; k <= 8; k++) { const t = Math.PI * k / 8; sfera.push([zs + rs * Math.cos(t), rs * Math.sin(t)]); }
  const cristallo = [tornio([[a, 0.05], [a - 0.06 * H, 0.18], [z1 + 0.02, 0.30]], cu, cv, church),
    tornio(coppa(z1 - 0.02, zc, R1 * 0.92), cu, cv, church), tornio(sfera, cu, cv, church)];
  const anelli = [[z1, R1]];
  if (doppio) {
    const z2 = zs - rs - 0.29 * H;
    cristallo.push(tornio([[zs - rs, 0.05], [z2 + 0.25 * (zs - rs - z2), R2 * 0.45], [z2 + 0.02, R2 * 0.78]], cu, cv, church),
      tornio(coppa(z2 - 0.02, b + 0.03 * H, R2 * 0.92), cu, cv, church),
      tornio([[b + 0.03 * H, 0.04], [b, 0.0]], cu, cv, church));
    anelli.push([z2, R2]);
  } else cristallo.push(tornio([[zs - rs, 0.03], [b, 0.0]], cu, cv, church));
  const oro = [blocco(cu - 0.02, cu + 0.02, cv - 0.02, cv + 0.02, a, aggancio, church),
    tornio([[a + 0.06, 0.06], [a, 0.12], [a - 0.03, 0.10]], cu, cv, church)];
  const candele = [];
  for (const [zr, R] of anelli) {
    oro.push(tornio([[zr + 0.04, R + 0.03], [zr, R + 0.06], [zr - 0.04, R + 0.03], [zr - 0.04, 0.2],
      [zr + 0.04, 0.2], [zr + 0.04, R + 0.03]], cu, cv, church));
    for (let k = 0; k < LAMPADARIO_N_BRACCI; k++) {
      const t = 2 * Math.PI * (k + 0.5) / LAMPADARIO_N_BRACCI;
      const x = cu + R * Math.cos(t), y = cv + R * Math.sin(t);
      oro.push(blocco(x - 0.035, x + 0.035, y - 0.035, y + 0.035, zr + 0.04, zr + 0.09, church));
      candele.push(blocco(x - 0.018, x + 0.018, y - 0.018, y + 0.018, zr + 0.09, zr + 0.27, church));
    }
  }
  return [cristallo, oro, candele];
}

// I lampadari: quello doppio dell'abside e i due singoli della navata
// (vedi church_mesh.py). { cristallo, oro, candele }
function buildLampadario(church) {
  const us = church.apseVertices().map((p) => p[0]);
  const tutti = [lampadario((Math.min(...us) + Math.max(...us)) / 2, 0.0, VOLTA_ABSIDE_CHIAVE_M, LAMPADARIO_ALTO_M,
    LAMPADARIO_BASSO_M, LAMPADARIO_RAGGIO_BRACCI_M, LAMPADARIO_RAGGIO_BRACCI_BASSO_M, true, church)];
  for (const u of LAMPADARI_NAVATA_U_M)
    tutti.push(lampadario(u, 0.0, VOLTA_NAVATA_CHIAVE_M, LAMPADARIO_NAVATA_ALTO_M, LAMPADARIO_NAVATA_BASSO_M,
      LAMPADARIO_RAGGIO_BRACCI_M, LAMPADARIO_RAGGIO_BRACCI_M, false, church));
  const [cristallo, oro, candele] = [0, 1, 2].map((n) => mergeParts(tutti.flatMap((t) => t[n])));
  return { cristallo, oro, candele };
}

// colori (RGB) dalle foto (vedi church_mesh.py)
// (dal video IMG_9758, tolta la dominante calda: stessa famiglia di toni dei muri)
const COLORI_ARREDI = { pietra: 0xe6e1d7, legno: 0x52362b, legno_chiaro: 0x7a5232, rosso: 0xb5221c, giallo: 0xe0b020,
  oro: 0xc9a33a, marmo_scuro: 0x6b625a, bianco: 0xefebe4, croce: 0xb83a26, nero: 0x1e1e1e,
  marmo_giallo: 0xcfbb9b, quadro: 0x6b5038, avorio: 0xe9dcc0, fondo_altare: 0xb3a89c, fonte: 0xae987f,
  pannello: 0xbab5ac, zoccolo: 0xcfc9bd, legno_pannello: 0x6a4634, legno_scuro: 0x3a241b, nicchia: 0x9aa3a6 };

// Lastra verticale (piano v-w a quota u) con l'arco a tutto sesto in cima
function arcoVerticale(u, v0, v1, w0, wImposta, church, n = 20) {
  const r = (v1 - v0) / 2, vc = (v0 + v1) / 2, righe = [];
  for (let k = 0; k <= n; k++) {
    const v = v0 + (v1 - v0) * k / n;
    righe.push([[u, v, w0], [u, v, wImposta + Math.sqrt(Math.max(r * r - (v - vc) ** 2, 0.0))]]);
  }
  return griglia(righe, church);
}

// Fascia a mezzo anello in un piano v-w (a quota u), centro (vc, wc)
function fasciaArco(u, vc, wc, r0, r1, church, n = 24) {
  const righe = [];
  for (let k = 0; k <= n; k++) {
    const a = Math.PI * k / n;
    righe.push([[u, vc + r0 * Math.cos(a), wc + r0 * Math.sin(a)], [u, vc + r1 * Math.cos(a), wc + r1 * Math.sin(a)]]);
  }
  return griglia(righe, church);
}
// Raggio sottile (largo larg) da r0 a r1 all'angolo a, in un piano v-w
function raggio(u, vc, wc, r0, r1, a, larg, church) {
  const c = Math.cos(a), s = Math.sin(a), t = larg / 2;
  return griglia([r0, r1].map((r) => [[u, vc + r * c - t * s, wc + r * s + t * c], [u, vc + r * c + t * s, wc + r * s - t * c]]), church);
}
// Stendardo in un piano v-w, col bordo basso a punta se punta > 0
function bandiera(u, v0, v1, w0, w1, punta, church, n = 12) {
  const vc = (v0 + v1) / 2, hw = (v1 - v0) / 2, righe = [];
  for (let k = 0; k <= n; k++) { const v = v0 + (v1 - v0) * k / n; righe.push([[u, v, w0 + punta * Math.abs(v - vc) / hw], [u, v, w1]]); }
  return griglia(righe, church);
}
// Lastra in un piano v-w dall'arco a tutto sesto (centro v = 0) fino a wtop: il semicerchio resta aperto
function lastraSopraArco(u, v0, v1, wc, r, wtop, church, n = 24) {
  const righe = [];
  for (let k = 0; k <= n; k++) { const v = v0 + (v1 - v0) * k / n; righe.push([[u, v, wc + Math.sqrt(Math.max(r * r - v * v, 0.0))], [u, v, wtop]]); }
  return griglia(righe, church);
}

// Disco verticale sul muro di un fianco (piano u-w, a quota v)
function discoSuMuro(u, v, w, r, church, n = 24) {
  const righe = [];
  for (let k = 0; k <= n; k++) { const a = 2 * Math.PI * k / n; righe.push([[u, v, w], [u + r * Math.cos(a), v, w + r * Math.sin(a)]]); }
  return griglia(righe, church);
}

// Controfacciata e lesene fra le cappelle (vedi church_mesh.py): [{part, color}]
function buildArrediMuri(church) {
  const out = [];
  const add = (part, c) => out.push({ part, color: COLORI_ARREDI[c] });
  const wh = church.naveWidthM / 2.0;
  const bw = BUSSOLA_LARGHEZZA_M / 2, bd = BUSSOLA_PROFONDITA_M, bh = BUSSOLA_ALTEZZA_M;
  const pw = PORTONE_LARGHEZZA_M / 2, ph = PORTONE_ALTEZZA_M;
  const wi = ph - pw, we = bh - 0.6, pil = pw + 0.35;
  const or2 = (a, b) => [Math.min(a, b), Math.max(a, b)];
  // bussola: pilastri, riquadri ad arco, archivolto, trabeazione
  for (const s_ of [-1, 1]) {
    const [v0, v1] = or2(s_ * pil, s_ * bw);
    add(blocco(0.0, bd, v0, v1, 0.0, we, church), "pietra");
    add(blocco(bd, bd + 0.05, v0 - 0.03, v1 + 0.03, 0.0, 0.5, church), "zoccolo");
    const vc = s_ * (pil + bw) / 2;
    add(arcoVerticale(bd + 0.01, vc - 0.3, vc + 0.3, 0.8, 3.9, church), "pannello");
    add(blocco(bd, bd + 0.08, ...or2(s_ * (pw + 0.05), s_ * (pil + 0.05)), wi - 0.18, wi, church), "pietra");
  }
  add(lastraSopraArco(bd, -pil, pil, wi, pw, we, church), "pietra");
  add(fasciaArco(bd + 0.03, 0.0, wi, pw + 0.02, pw + 0.32, church), "bianco");
  for (const s_ of [-1, 1])
    add(blocco(bd + 0.01, bd + 0.02, ...or2(s_ * (pw + 0.45), s_ * (pil - 0.08)), ph - 0.2, we - 0.15, church), "pannello");
  for (const [w0, w1, d] of [[we, we + 0.2, 0.05], [we + 0.2, we + 0.4, 0.02], [we + 0.4, bh, 0.15]])
    add(blocco(0.0, bd + d, -bw - d, bw + d, w0, w1, church), d !== 0.02 ? "pietra" : "pannello");
  for (const s_ of [-1, 1]) {
    const vc = s_ * (bw - 0.3);
    add(blocco(bd - 0.6, bd, vc - 0.3, vc + 0.3, bh, bh + 0.5, church), "pietra");
    add(blocco(bd, bd + 0.01, vc - 0.18, vc + 0.18, bh + 0.1, bh + 0.4, church), "pannello");
    add(tornio([[bh + 1.85, 0.0], [bh + 0.5, 0.36]], bd - 0.3, vc, church, 4, [Math.PI / 4, Math.PI / 4 + 2 * Math.PI]), "pietra");
    add(tornio([[bh + 2.03, 0.0], [bh + 1.97, 0.07], [bh + 1.91, 0.0]], bd - 0.3, vc, church, 12), "pietra");
  }
  add(tornio([[bh + 1.9, 0.0], [bh + 1.6, 0.25], [bh + 1.2, 0.95], [bh + 0.6, 1.45], [bh, 1.6]],
    0.02, 0.0, church, 24, [-Math.PI / 2, Math.PI / 2]), "pietra");
  // portone: ante a riquadri, sguanci, battuta, traversa, lunetta a raggiera
  add(arcoVerticale(bd - 0.12, -pw, pw, 0.0, wi, church), "legno");
  for (const s_ of [-1, 1]) {
    add(blocco(bd - 0.12, bd, ...or2(s_ * pw, s_ * (pw + 0.02)), 0.0, wi, church), "pietra");
    for (const [w0, w1] of [[0.3, 1.6], [1.8, wi - 0.25]])
      add(blocco(bd - 0.12, bd - 0.09, ...or2(s_ * 0.12, s_ * (pw - 0.12)), w0, w1, church), "legno_pannello");
  }
  add(blocco(bd - 0.12, bd - 0.08, -0.03, 0.03, 0.0, wi, church), "legno_scuro");
  add(blocco(bd - 0.12, bd - 0.06, -pw, pw, wi - 0.12, wi, church), "legno_pannello");
  for (let k = 0; k < 9; k++) add(raggio(bd - 0.11, 0.0, wi, 0.25, pw - 0.05, Math.PI * (k + 0.5) / 9, 0.035, church), "legno_scuro");
  add(fasciaArco(bd - 0.11, 0.0, wi, 0.0, 0.25, church), "legno_pannello");
  // stendardi su un'asta: rosso con croci dorate e icona, giallo a punta
  for (const [vc, col, punta] of [[-2.36, "rosso", false], [2.40, "giallo", true]]) {
    const u0 = bd + 0.12;
    add(blocco(u0 - 0.02, u0 + 0.02, vc - 0.62, vc + 0.62, 4.12, 4.16, church), "oro");
    for (const e of [-0.64, 0.64]) add(tornio([[4.2, 0.0], [4.14, 0.045], [4.08, 0.0]], u0, vc + e, church, 8), "oro");
    add(bandiera(u0, vc - 0.5, vc + 0.5, 1.0, 4.1, punta ? 0.35 : 0.0, church), col);
    add(blocco(u0 + 0.005, u0 + 0.015, vc - 0.24, vc + 0.24, 2.95, 3.65, church), "oro");
    add(blocco(u0 + 0.015, u0 + 0.02, vc - 0.19, vc + 0.19, 3.0, 3.6, church), "quadro");
    if (!punta) for (const [cv_, cw] of [[-0.3, 3.85], [0.3, 3.85], [-0.3, 2.5], [0.3, 2.5], [-0.3, 1.8], [0.3, 1.8], [0.0, 1.3]]) {
      add(blocco(u0 + 0.005, u0 + 0.012, vc + cv_ - 0.07, vc + cv_ + 0.07, cw - 0.015, cw + 0.015, church), "oro");
      add(blocco(u0 + 0.005, u0 + 0.012, vc + cv_ - 0.015, vc + cv_ + 0.015, cw - 0.07, cw + 0.07, church), "oro");
    }
  }
  // battistero (Est): colonne a coppie, trabeazione, nicchie, fonte
  const vb = -5.1;
  add(blocco(0.0, 0.3, vb - 1.35, vb + 1.35, 0.0, 4.6, church), "fondo_altare");
  add(arcoVerticale(0.31, vb - 0.5, vb + 0.5, 2.1, 3.4, church), "nicchia");
  add(tornio([[2.35, 0.32], [2.15, 0.25], [2.0, 0.08]], 0.45, vb, church, 16), "marmo_giallo");
  add(tornio([[3.55, 0.06], [3.4, 0.16], [3.0, 0.24], [2.6, 0.27], [2.35, 0.25]], 0.45, vb, church, 16), "avorio");
  add(arcoVerticale(0.31, vb - 0.42, vb + 0.42, 0.0, 1.4, church), "marmo_scuro");
  add(tornio([[1.0, 0.45], [0.92, 0.45], [0.82, 0.34], [0.72, 0.12], [0.25, 0.1], [0.1, 0.22], [0.0, 0.22]], 0.72, vb, church, 20), "fonte");
  add(tornio([[1.42, 0.06], [1.3, 0.2], [1.1, 0.4], [1.0, 0.44]], 0.72, vb, church, 20), "fonte");
  add(blocco(0.70, 0.74, vb - 0.02, vb + 0.02, 1.42, 1.75, church), "oro");
  add(blocco(0.70, 0.74, vb - 0.1, vb + 0.1, 1.6, 1.64, church), "oro");
  for (const v of [vb - 1.05, vb - 0.7, vb + 0.7, vb + 1.05]) {
    add(blocco(0.3, 0.66, v - 0.18, v + 0.18, 0.0, 1.0, church), "marmo_scuro");
    add(blocco(0.28, 0.68, v - 0.2, v + 0.2, 0.95, 1.05, church), "marmo_scuro");
    add(tornio([[3.85, 0.12], [2.4, 0.145], [1.05, 0.15]], 0.48, v, church, 14), "marmo_giallo");
    add(blocco(0.32, 0.64, v - 0.17, v + 0.17, 3.85, 4.05, church), "marmo_giallo");
  }
  add(blocco(0.0, 0.7, vb - 1.3, vb + 1.3, 4.05, 4.2, church), "marmo_giallo");
  add(blocco(0.0, 0.66, vb - 1.25, vb + 1.25, 4.2, 4.42, church), "nicchia");
  add(blocco(0.0, 0.8, vb - 1.4, vb + 1.4, 4.42, 4.6, church), "marmo_giallo");
  add(blocco(0.1, 0.35, vb - 0.45, vb + 0.45, 4.6, 5.1, church), "marmo_giallo");
  add(blocco(0.2, 0.26, vb - 0.04, vb + 0.04, 5.1, 5.8, church), "marmo_giallo");
  add(blocco(0.2, 0.26, vb - 0.2, vb + 0.2, 5.5, 5.58, church), "marmo_giallo");
  for (let k = 0; k <= 8; k++) { const v = vb - 1.3 + 2.6 * k / 8; add(blocco(1.2, 1.23, v - 0.015, v + 0.015, 0.0, 0.85, church), "nero"); }
  for (const w of [0.1, 0.82]) add(blocco(1.19, 1.24, vb - 1.32, vb + 1.32, w, w + 0.04, church), "nero");
  // armadio a due ante con cornice (Ovest)
  add(blocco(0.0, 0.7, 2.95, 4.85, 0.0, 3.6, church), "legno");
  add(blocco(0.0, 0.78, 2.9, 4.9, 3.6, 3.75, church), "legno_scuro");
  for (const [v0, v1] of [[3.05, 3.85], [3.95, 4.75]])
    for (const [w0, w1] of [[0.2, 1.6], [1.8, 3.4]]) add(blocco(0.7, 0.73, v0, v1, w0, w1, church), "legno_pannello");
  // confessionale: corpo centrale col frontone curvo e la grata, due ali
  add(blocco(0.0, 0.9, 5.35, 6.2, 0.0, 2.6, church), "legno_chiaro");
  add(arcoVerticale(0.9, 5.35, 6.2, 2.6, 2.6, church), "legno_chiaro");
  add(blocco(0.0, 0.9, 5.4, 6.15, 2.6, 2.75, church), "legno_chiaro");
  add(blocco(0.9, 0.93, 5.5, 6.05, 1.3, 2.25, church), "nero");
  for (let k = 0; k < 5; k++) { const v = 5.5 + 0.55 * (k + 0.5) / 5; add(blocco(0.93, 0.95, v - 0.01, v + 0.01, 1.3, 2.25, church), "legno_chiaro"); }
  for (const [v0, v1] of [[4.95, 5.35], [6.2, 6.6]]) {
    add(blocco(0.0, 0.8, v0, v1, 0.0, 2.2, church), "legno");
    add(blocco(0.0, 0.85, v0, v1, 2.2, 2.3, church), "legno_scuro");
  }
  add(blocco(0.42, 0.48, 5.745, 5.805, 3.05, 3.5, church), "legno_chiaro");
  add(blocco(0.42, 0.48, 5.65, 5.9, 3.3, 3.35, church), "legno_chiaro");
  const lw = LESENA_LARGHEZZA_M / 2, sp = LESENA_SPORGENZA_M, z = LESENA_ZOCCOLO_M, cb = CORNICIONE_BASE_M;
  const us = church.chapelUPositions(), campata = us[1] - us[0];
  const pilastri = [us[0] - campata / 2, ...us.map((u) => u + campata / 2)];
  const ord = (a, b) => [Math.min(a, b), Math.max(a, b)];
  let stazione = 0;
  pilastri.forEach((up, k) => {
    for (const lato of [1.0, -1.0]) {
      const muro = lato * (wh - 0.16);
      const dentro = (d) => lato * (wh - 0.16 - d);
      add(blocco(up - lw - 0.08, up + lw + 0.08, ...ord(muro, dentro(sp + 0.08)), 0.0, z, church), "marmo_scuro");
      add(blocco(up - lw, up + lw, ...ord(muro, dentro(sp)), z, cb - 0.35, church), "bianco");
      add(blocco(up - lw - 0.1, up + lw + 0.1, ...ord(muro, dentro(sp + 0.1)), cb - 0.35, cb, church), "bianco");
      add(discoSuMuro(up, dentro(sp + 0.01), CROCE_CONSACRAZIONE_M, 0.27, church), "croce");
      const vc = dentro(sp + 0.02), c = CROCE_CONSACRAZIONE_M;
      add(blocco(up - 0.03, up + 0.03, ...ord(vc, dentro(sp + 0.03)), c - 0.2, c + 0.2, church), "nero");
      add(blocco(up - 0.2, up + 0.2, ...ord(vc, dentro(sp + 0.03)), c - 0.03, c + 0.03, church), "nero");
      if (stazione < 14) {
        add(blocco(up - 0.19, up + 0.19, ...ord(dentro(sp), dentro(sp + 0.04)), 1.75, 2.25, church), "legno");
        add(blocco(up - 0.15, up + 0.15, ...ord(dentro(sp + 0.04), dentro(sp + 0.05)), 1.8, 2.2, church), "quadro");
        stazione++;
      }
      if (lato < 0 && k === 1) {
        add(blocco(up - 0.06, up + 0.06, ...ord(dentro(sp), dentro(sp + 0.1)), 5.8, 8.2, church), "legno");
        add(blocco(up - 0.6, up + 0.6, ...ord(dentro(sp), dentro(sp + 0.1)), 7.45, 7.57, church), "legno");
        add(blocco(up - 0.1, up + 0.1, ...ord(dentro(sp + 0.1), dentro(sp + 0.22)), 6.3, 7.5, church), "avorio");
        add(blocco(up - 0.55, up + 0.55, ...ord(dentro(sp + 0.1), dentro(sp + 0.18)), 7.38, 7.5, church), "avorio");
      }
    }
  });
  return out;
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

// Faccia col contorno della vetrata a distanza d verso l'esterno dal filo
// interno del muro, con la normale verso `verso` (+1 fuori, -1 dentro)
function facciaVetrata(outline, du, dv, d, verso, church) {
  let P = ptsLocalToWorld(church, outline.map(([u, v, w]) => [u + du * d, v + dv * d, w]));
  const e1 = [0, 1, 2].map((k) => P[1][k] - P[0][k]), e2 = [0, 1, 2].map((k) => P[2][k] - P[0][k]);
  const n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
  const o = church.localToEnu(du, dv, 0.0), z = church.localToEnu(0.0, 0.0, 0.0);
  if ((n[0] * (o[0] - z[0]) + n[1] * (o[1] - z[1]) + n[2] * (o[2] - z[2])) * verso < 0) P = P.reverse();
  const indices = [];
  for (let i = 1; i < P.length - 1; i++) indices.push([0, i, i + 1]);
  return { positions: P, indices };
}

// Vetrata (vedi church_mesh.py): due facce sottili, una appena dentro il filo
// interno rivolta verso l'interno, una sul filo esterno rivolta verso
// l'esterno; ciascuna si disegna solo dal davanti, cosi' da dentro si vede
// solo quella interna, coperta esattamente dalla foto della vetrata.
function buildWindowSolid(win, church, wallThickness = WALL_THICKNESS_M, recessFromExterior = 0.0) {
  const outline = win.localOutline();
  const [du, dv] = localOutwardDirUV(church, win.wallAzimuthDeg);
  const r = recessFromExterior;
  return mergeParts([facciaVetrata(outline, du, dv, -0.02 - r, -1, church),
    facciaVetrata(outline, du, dv, wallThickness + 0.02 - r, 1, church)]);
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

  const floor = mergeParts([buildFloor(innerLoopFull, church), buildGradini(church)]);
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

  const altari = buildAltari(church);
  const organo = buildOrgano(church);
  const oggetti = buildOggettiAltare(church);
  return { banchi: buildBanchi(church), balaustra: buildBalaustra(church), riscaldamento: buildRiscaldamento(church), pulpito: buildPulpito(church), altareOro: oggetti.oro, altareCera: oggetti.cera, altareFiamma: oggetti.fiamma, altareLibro: oggetti.libro,
    cornicione: buildCornicione(church), altariCappelle: buildAltariCappelle(church), voltaAbside: buildVoltaAbside(church), voltaNavata: buildVoltaNavata(church), arrediMuri: buildArrediMuri(church), lampadario: buildLampadario(church),
    organoLegno: organo.legno, organoZoccolo: organo.zoccolo, altariMarmo: altari.marmo, altariTovaglia: altari.tovaglia,
    floor, walls, roof, chapelWalls, chapelPiers, apseStructure, tower, narthex, windows };
}
