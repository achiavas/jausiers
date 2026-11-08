// wall-projection.js
// Porting 1:1 di wall_projection.py — vedi quel file per la
// spiegazione completa del principio geometrico (raggio che colpisce
// il pavimento O una parete verticale interna, a seconda di quale
// superficie incontra per prima).

const EDGE_SUBDIVISIONS = 6;

// Altezza REALE del muro interno nel punto (u,v) del perimetro - non
// piu' un'unica WALL_HEIGHT_M uniforme: le nicchie delle cappelle
// hanno un'altezza molto piu' bassa (9.64-10.95 m, tetto inclinato) e
// l'abside ha la sua altezza propria - vedi _wall_height_at_point in
// wall_projection.py per la spiegazione completa (evita macchie di
// luce segmentate/interrotte quando la luce di una vetrata di
// cleristorio passa SOPRA una nicchia bassa).
function wallHeightAtPoint(u, v) {
  const Wh = NAVE_WIDTH_M / 2.0;
  const L = NAVE_LENGTH_M;
  if (u > L - 1e-6) {
    return APSE_EXTERNAL_HEIGHT_M + 4.15;
  }
  if (Math.abs(v) > Wh + 1e-6) {
    let depthFrac = (Math.abs(v) - Wh) / CHAPEL_PROJECTION_DEPTH_M;
    depthFrac = Math.max(0.0, Math.min(1.0, depthFrac));
    return CHAPEL_ROOF_HEIGHT_M + CHAPEL_ROOF_PITCH_RISE_M * (1.0 - depthFrac);
  }
  return WALL_HEIGHT_M;
}

function densifyLoop(points, subdivisions) {
  const n = points.length;
  const dense = [];
  for (let i = 0; i < n; i++) {
    const p0 = points[i], p1 = points[(i + 1) % n];
    for (let k = 0; k < subdivisions; k++) {
      const t = k / subdivisions;
      dense.push([0, 1, 2].map((j) => p0[j] + (p1[j] - p0[j]) * t));
    }
  }
  return dense;
}

function rayVsSegmentXY(p0, direction, segA, segB) {
  const [x1, y1] = p0;
  const [dx, dy] = direction;
  const x2 = x1 + dx, y2 = y1 + dy;
  const [x3, y3] = segA, [x4, y4] = segB;
  const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
  if (Math.abs(denom) < 1e-9) return null;
  const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
  const s = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / denom;
  if (t >= 1e-6 && s >= 0.0 && s <= 1.0) return [t, s];
  return null;
}

// Trova la prima superficie colpita. Ritorna:
//   {kind:"pavimento", u, v}  oppure
//   {kind:"parete", edgeIndex, s, height}  oppure  null
// Le macchie di luce sulle pareti si disegnano staccate dal filo del muro
// di tanto verso l'interno, davanti alle foto appoggiate alle pareti.
const STACCO_PARETE_M = 0.2;

// Il muro della navata davanti a ogni cappella (v = +-Wh, largo quanto la
// nicchia): il raggio lo attraversa solo dentro l'arco d'ingresso.
function schermiCappelle(church) {
  const wh = church.naveWidthM / 2.0, dw = CHAPEL_PROJECTION_WIDTH_M / 2.0, out = [];
  for (const uc of church.chapelUPositions()) for (const lato of [1.0, -1.0]) out.push([[uc - dw, lato * wh], [uc + dw, lato * wh], uc]);
  return out;
}
function dentroArco(u, w, uc) {
  const x = u - uc, R = CHAPEL_ARCH_RADIUS_M, S = CHAPEL_ARCH_SPRING_M;
  return Math.abs(x) < R && (w < S || x * x + (w - S) ** 2 < R * R);
}
function dentroPianta(u, v, perimeter) {
  let dentro = false;
  for (let i = 0, j = perimeter.length - 2; i < perimeter.length - 1; j = i++) {
    const [ui, vi] = perimeter[i], [uj, vj] = perimeter[j];
    if ((vi > v) !== (vj > v) && u < (uj - ui) * (v - vi) / (vj - vi + 1e-12) + ui) dentro = !dentro;
  }
  return dentro;
}

// Sutherland-Hodgman: tiene la parte di poli con p[asse] >= limite
// (sopra=true) o <= limite (sopra=false).
function ritaglia(poli, asse, limite, sopra) {
  const dentro = sopra ? (p) => p[asse] >= limite : (p) => p[asse] <= limite;
  const out = [];
  poli.forEach((cur, i) => {
    const prev = poli[(i - 1 + poli.length) % poli.length];
    if (dentro(cur) !== dentro(prev)) {
      const t = (limite - prev[asse]) / (cur[asse] - prev[asse]);
      out.push(prev.map((a, k) => a + t * (cur[k] - a)));
    }
    if (dentro(cur)) out.push(cur);
  });
  return out;
}

const STACCO_BANCO_M = 0.012;   // la luce sui banchi poco sopra il legno

// La macchia sul pavimento rimandata indietro lungo i raggi del sole sulle
// facce dei banchi rivolte al sole (sedili, schienali, fianchi): il fascio
// di luce le attraversa prima di arrivare a terra. Proiezione parallela =
// affine, quindi basta proiettare il poligono e ritagliarlo sul rettangolo
// della faccia. Restituisce poligoni [u, v, w] locali.
function luceSuiBanchi(church, pavimentoUvw, versoSole) {
  const s = versoSole, out = [];
  for (const [u0, u1, v0, v1, w0, w1] of banchiScatole(church)) {
    const lim = [[u0, u1], [v0, v1], [w0, w1]];
    // facce: [asse della normale, valore, segno]; il fondo non si vede
    for (const [asse, val, segno] of [[2, w1, 1], [0, u0, -1], [0, u1, 1], [1, v0, -1], [1, v1, 1]]) {
      if (s[asse] * segno <= 1e-6) continue;          // faccia non rivolta al sole
      let poli = pavimentoUvw.map((p) => { const t = (val - p[asse]) / s[asse]; return [0, 1, 2].map((k) => p[k] + t * s[k]); });
      for (const k of [0, 1, 2]) {
        if (k === asse) continue;
        if (Math.max(...poli.map((q) => q[k])) < lim[k][0] || Math.min(...poli.map((q) => q[k])) > lim[k][1]) { poli = []; break; }
        poli = ritaglia(poli, k, lim[k][0], true);
        if (!poli.length) break;
        poli = ritaglia(poli, k, lim[k][1], false);
        if (!poli.length) break;
      }
      if (poli.length >= 3) {
        const d = [0, 0, 0]; d[asse] = segno * STACCO_BANCO_M;
        out.push(poli.map((q) => [q[0] + d[0], q[1] + d[1], q[2] + d[2]]));
      }
    }
  }
  return out;
}

function firstHit(u0, v0, w0, pu, pv, pw, perimeter, wallHeight, schermi = []) {
  let tFloor = pw < 0 ? -w0 / pw : Infinity;
  // gradini e abside rialzata: il raggio si ferma alla quota vera
  for (let k = 0; k < 3 && Number.isFinite(tFloor); k++) {
    const q = quotaPavimento(u0 + pu * tFloor, v0 + pv * tFloor);
    if (q >= w0) break;
    tFloor = (q - w0) / pw;
  }

  let bestT = tFloor;
  let best = Number.isFinite(tFloor) ? { kind: "pavimento", u: u0 + pu * tFloor, v: v0 + pv * tFloor } : null;
  // fuori dalla pianta non c'e' pavimento della chiesa (raggio uscito)
  if (best && !dentroPianta(best.u, best.v, perimeter)) { best = null; bestT = Infinity; }

  for (let i = 0; i < perimeter.length - 1; i++) {
    const segA = perimeter[i], segB = perimeter[i + 1];
    const hit = rayVsSegmentXY([u0, v0], [pu, pv], segA, segB);
    if (hit === null) continue;
    const [t, s] = hit;
    const height = w0 + pw * t;
    const hA = wallHeightAtPoint(segA[0], segA[1]);
    const hB = wallHeightAtPoint(segB[0], segB[1]);
    const localWallHeight = hA + s * (hB - hA);
    if (height >= 0.0 && height <= localWallHeight && t < bestT) {
      bestT = t;
      best = { kind: "parete", edgeIndex: i, s, height };
    }
  }
  // muro della navata davanti alle cappelle: ferma il raggio fuori dall'arco
  schermi.forEach(([a, b, uc], k) => {
    const hit = rayVsSegmentXY([u0, v0], [pu, pv], a, b);
    if (hit === null) return;
    const [t, s] = hit;
    const height = w0 + pw * t;
    const u = a[0] + s * (b[0] - a[0]);
    if (height >= 0.0 && height <= WALL_HEIGHT_M && t < bestT && !dentroArco(u, height, uc)) {
      bestT = t;
      best = { kind: "parete", edgeIndex: perimeter.length - 1 + k, s, height };
    }
  });
  return best;
}

// Proietta il contorno di una vetrata (locale u,v,w) lungo la
// direzione del sole. Ritorna una lista di {surface, pointsWorld}
// (surface: "pavimento" | "parete" | "banco"), eventualmente vuota.
function projectWindowWithWalls(church, outlineLocalUVW, wallAzimuthDeg, sun, wallHeight) {
  if (!sun.isUp) return [];

  const diff = (((sun.azimuthDeg - wallAzimuthDeg + 180.0) % 360.0) + 360.0) % 360.0 - 180.0;
  if (Math.abs(diff) >= 90.0) return [];

  const [dE, dN, dU] = sunVectorEnu(sun);
  const [du, dv] = church.enuToLocalUV(dE, dN);
  const pu = -du, pv = -dv, pw = -dU;
  if (pw >= 0) return [];

  const perimeter = church.floorOutlineLocal(); // anello chiuso: ultimo punto = primo
  const dense = densifyLoop(outlineLocalUVW, EDGE_SUBDIVISIONS);

  const schermi = schermiCappelle(church);
  // tutti i tratti di parete: il perimetro della pianta, poi i muri davanti alle cappelle
  const segmenti = [];
  for (let i = 0; i < perimeter.length - 1; i++) segmenti.push([perimeter[i], perimeter[i + 1]]);
  for (const [a, b] of schermi) segmenti.push([a, b]);
  const hits = dense.map(([u, v, w]) => firstHit(u, v, w, pu, pv, pw, perimeter, wallHeight, schermi));
  if (hits.every((h) => h === null)) return [];

  function surfKey(h) {
    if (h === null) return null;
    return h.kind === "pavimento" ? "pavimento" : `parete_${h.edgeIndex}`;
  }

  const n = hits.length;
  let start = 0;
  for (let i = 0; i < n; i++) {
    if (surfKey(hits[i]) !== surfKey(hits[(i - 1 + n) % n])) { start = i; break; }
  }
  const order = Array.from({ length: n }, (_, i) => (start + i) % n);

  const groups = [];
  for (const idx of order) {
    if (hits[idx] === null) continue;
    if (groups.length > 0 && surfKey(hits[idx]) === surfKey(hits[groups[groups.length - 1][groups[groups.length - 1].length - 1]])) {
      groups[groups.length - 1].push(idx);
    } else {
      groups.push([idx]);
    }
  }
  if (groups.length > 1) {
    const first = groups[0], last = groups[groups.length - 1];
    if (surfKey(hits[first[0]]) === surfKey(hits[last[last.length - 1]])) {
      groups[0] = [...last, ...first];
      groups.pop();
    }
  }

  // punto di cucitura condiviso fra gruppi adiacenti
  const originalFirst = groups.map((g) => g[0]);
  for (let gi = 0; gi < groups.length; gi++) {
    const prevGroup = groups[(gi - 1 + groups.length) % groups.length];
    groups[gi] = [prevGroup[prevGroup.length - 1], ...groups[gi]];
  }

  // verso del perimetro (< 0: senso orario, interno a destra)
  let a2 = 0;
  for (let i = 0; i < perimeter.length - 1; i++) a2 += perimeter[i][0] * perimeter[i + 1][1] - perimeter[i + 1][0] * perimeter[i][1];
  function toWorld(h) {
    if (h.kind === "pavimento") {
      return church.localToEnu(h.u, h.v, quotaPavimento(h.u, h.v) + 0.02);
    }
    const [segA, segB] = segmenti[h.edgeIndex];
    const u = segA[0] + h.s * (segB[0] - segA[0]);
    const v = segA[1] + h.s * (segB[1] - segA[1]);
    // STACCO_PARETE_M verso l'interno: sul filo del muro le foto (pannelli
    // delle cappelle, fondi delle nicchie, pannello dell'abside) la coprirebbero
    const du = segB[0] - segA[0], dv = segB[1] - segA[1], n = Math.hypot(du, dv) || 1;
    let [iu, iv] = a2 < 0 ? [dv / n, -du / n] : [-dv / n, du / n];
    if (h.edgeIndex >= perimeter.length - 1) { iu = 0; iv = -Math.sign(v); }   // muro davanti a una cappella: verso la navata
    return church.localToEnu(u + STACCO_PARETE_M * iu, v + STACCO_PARETE_M * iv, h.height);
  }

  const patches = [];
  for (let gi = 0; gi < groups.length; gi++) {
    const group = groups[gi];
    if (group.length < 3) continue;
    const kind = hits[originalFirst[gi]].kind;
    const pts = group.map((idx) => hits[idx]).filter((h) => h !== null).map(toWorld);
    if (pts.length >= 3) patches.push({ surface: kind, pointsWorld: pts });
    if (kind === "pavimento") {
      // la stessa luce, prima di toccare terra, cade sui banchi
      const pav = group.map((idx) => hits[idx]).filter((h) => h !== null && h.kind === "pavimento").map((h) => [h.u, h.v, quotaPavimento(h.u, h.v)]);
      if (pav.length >= 3) {
        for (const poli of luceSuiBanchi(church, pav, [-pu, -pv, -pw])) patches.push({ surface: "banco", pointsWorld: poli.map((q) => church.localToEnu(...q)) });
      }
    }
  }
  return patches;
}
