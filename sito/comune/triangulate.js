// triangulate.js
// Triangolazione "ear clipping" di un poligono 2D semplice (non
// auto-intersecante), eventualmente non convesso - necessaria per la
// pianta della chiesa (cappelle sporgenti + abside a pentagono).
// Ritorna una lista di terne di indici (nello stesso ordine dei punti
// in input).

function signedArea(pts) {
  let a = 0;
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[(i + 1) % n];
    a += x1 * y2 - x2 * y1;
  }
  return a / 2;
}

function isConvex(a, b, c, ccw) {
  const cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  return ccw ? cross > 1e-12 : cross < -1e-12;
}

function pointInTriangle(p, a, b, c) {
  const d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1]);
  const d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1]);
  const d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1]);
  const hasNeg = d1 < 0 || d2 < 0 || d3 < 0;
  const hasPos = d1 > 0 || d2 > 0 || d3 > 0;
  return !(hasNeg && hasPos);
}

function triangulatePolygon(points) {
  const n = points.length;
  if (n < 3) return [];
  if (n === 3) return [[0, 1, 2]];

  const ccw = signedArea(points) > 0;
  const idx = Array.from({ length: n }, (_, i) => i);
  const tris = [];

  let guard = 0;
  while (idx.length > 3 && guard < 10000) {
    guard++;
    let earFound = false;
    for (let i = 0; i < idx.length; i++) {
      const iPrev = idx[(i - 1 + idx.length) % idx.length];
      const iCur = idx[i];
      const iNext = idx[(i + 1) % idx.length];
      const a = points[iPrev], b = points[iCur], c = points[iNext];
      if (!isConvex(a, b, c, ccw)) continue;

      let containsOther = false;
      for (const j of idx) {
        if (j === iPrev || j === iCur || j === iNext) continue;
        if (pointInTriangle(points[j], a, b, c)) { containsOther = true; break; }
      }
      if (containsOther) continue;

      tris.push([iPrev, iCur, iNext]);
      idx.splice(i, 1);
      earFound = true;
      break;
    }
    if (!earFound) break; // poligono degenere: interrompe senza bloccare
  }
  if (idx.length === 3) tris.push([idx[0], idx[1], idx[2]]);
  return tris;
}
