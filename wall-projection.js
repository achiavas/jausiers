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
function firstHit(u0, v0, w0, pu, pv, pw, perimeter, wallHeight) {
  const tFloor = pw < 0 ? -w0 / pw : Infinity;

  let bestT = tFloor;
  let best = Number.isFinite(tFloor) ? { kind: "pavimento", u: u0 + pu * tFloor, v: v0 + pv * tFloor } : null;

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
  return best;
}

// Proietta il contorno di una vetrata (locale u,v,w) lungo la
// direzione del sole. Ritorna una lista di {surface, pointsWorld}
// (surface: "pavimento" | "parete"), eventualmente vuota.
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

  const hits = dense.map(([u, v, w]) => firstHit(u, v, w, pu, pv, pw, perimeter, wallHeight));
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

  function toWorld(h) {
    if (h.kind === "pavimento") {
      return church.localToEnu(h.u, h.v, 0.02);
    }
    const segA = perimeter[h.edgeIndex], segB = perimeter[h.edgeIndex + 1];
    const u = segA[0] + h.s * (segB[0] - segA[0]);
    const v = segA[1] + h.s * (segB[1] - segA[1]);
    return church.localToEnu(u, v, h.height);
  }

  const patches = [];
  for (let gi = 0; gi < groups.length; gi++) {
    const group = groups[gi];
    if (group.length < 3) continue;
    const kind = hits[originalFirst[gi]].kind;
    const pts = group.map((idx) => hits[idx]).filter((h) => h !== null).map(toWorld);
    if (pts.length >= 3) patches.push({ surface: kind, pointsWorld: pts });
  }
  return patches;
}
