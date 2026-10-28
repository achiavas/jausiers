// church-geometry.js
// Porting 1:1 di church_geometry.py — vedi quel file per i commenti
// completi sulla provenienza di ogni quota (misurata / stimata).

const LATITUDE_DEG = 44.41978;
const LONGITUDE_DEG = 6.73401;
const TIMEZONE_NAME = "Europe/Paris";

const FACADE_AZIMUTH_DEG = 160.0;

const NAVE_LENGTH_M = 26.52;
const NAVE_WIDTH_M = 13.37;
const N_CHAPELS_PER_SIDE = 4;

const WALL_HEIGHT_M = 16.56;
const CHAPEL_ROOF_HEIGHT_M = 9.64;
const CHAPEL_ROOF_PITCH_RISE_M = 1.31;
const ROOF_RIDGE_RISE_M = 6.57;

const CHAPEL_PROJECTION_DEPTH_M = 2.19;
const CHAPEL_PROJECTION_WIDTH_M = 4.82;
const CHAPEL_ROW_MARGIN_M = 1.10;

const APSE_RECESS_M = 1.31;
const APSE_FACET_AZIMUTHS_DEG = [250.0, 301.4, 340.9, 17.6, 70.0];
const APSE_FACET_LENGTHS_M = [5.48, 4.3912, 3.8396, 4.3912, 5.48];

const CHAPEL_WINDOW_WIDTH_M = 1.10;
const CHAPEL_WINDOW_SILL_M = 11.18;
const CHAPEL_WINDOW_HEAD_M = 12.93;
const CHAPEL_WINDOW_ARCH_RISE_M = 0.55;
const CHAPEL_WINDOW_RECESS_M = 1.31;

const APSE_WINDOW_WIDTH_M = 1.10;
const APSE_WINDOW_SILL_M = 11.18;
const APSE_WINDOW_HEAD_M = 12.93;
const APSE_WINDOW_ARCH_RISE_M = 0.55;

const APSE_WINDOW_CLOCHER_WIDTH_M = 1.29;
const APSE_WINDOW_CLOCHER_SILL_M = 11.18;
const APSE_WINDOW_CLOCHER_HEAD_M = 13.435;
const APSE_WINDOW_CLOCHER_ARCH_RISE_M = 0.645;

const FACADE_CENTRAL_WINDOW_WIDTH_M = 1.53;
const FACADE_CENTRAL_WINDOW_SILL_M = 13.37;
const FACADE_CENTRAL_WINDOW_HEAD_M = 15.235;
const FACADE_CENTRAL_WINDOW_ARCH_RISE_M = 0.765;

const FACADE_SIDE_WINDOW_WIDTH_M = 0.99;
const FACADE_SIDE_WINDOW_SILL_M = 13.37;
const FACADE_SIDE_WINDOW_HEAD_M = 14.625;
const FACADE_SIDE_WINDOW_ARCH_RISE_M = 0.495;
const FACADE_SIDE_WINDOW_OFFSET_M = 1.45;

const FACADE_DOOR_WIDTH_M = 3.30;
const FACADE_DOOR_SILL_M = 0.0;
const FACADE_DOOR_ARCH_RISE_M = 1.65;
const FACADE_DOOR_HEAD_M = 2.73;

const NARTHEX_WIDTH_M = 4.38;
const NARTHEX_DEPTH_M = 2.63;
const NARTHEX_HEIGHT_AT_WALL_M = 6.58;
const NARTHEX_HEIGHT_AT_EDGE_M = 4.49;

const TOWER_U_CENTER_M = 29.2;
const TOWER_V_CENTER_M = 7.7;
const TOWER_WIDTH_U_M = 5.4;
const TOWER_WIDTH_V_M = 4.6;
const TOWER_BODY_HEIGHT_M = 19.85;
const TOWER_SPIRE_HEIGHT_M = 15.69;
const APSE_EXTERNAL_HEIGHT_M = 15.69;
const APSE_ROOF_RIDGE_RISE_M = 4.16;

const RAD = Math.PI / 180;

class Window {
  constructor({ name, group, wallPointUV, wallAzimuthDeg, widthM, sillM, headM, archRiseM = 0.0, nArchPoints = 8 }) {
    this.name = name;
    this.group = group;
    this.wallPointUV = wallPointUV; // [u, v]
    this.wallAzimuthDeg = wallAzimuthDeg;
    this.widthM = widthM;
    this.sillM = sillM;
    this.headM = headM;
    this.archRiseM = archRiseM;
    this.nArchPoints = nArchPoints;
  }

  // direzione "lungo la parete" nel sistema locale (u,v) — stessa
  // identica formula di Window.local_outline() in church_geometry.py
  _along() {
    const tangentWorldRad = RAD * (this.wallAzimuthDeg - 90.0);
    const azU = RAD * (((FACADE_AZIMUTH_DEG + 180.0) % 360.0));
    const azV = RAD * (((FACADE_AZIMUTH_DEG + 90.0) % 360.0));
    const uHat = [Math.sin(azU), Math.cos(azU)];
    const vHat = [Math.sin(azV), Math.cos(azV)];
    const east = Math.sin(tangentWorldRad);
    const north = Math.cos(tangentWorldRad);
    return [east * uHat[0] + north * uHat[1], east * vHat[0] + north * vHat[1]];
  }

  // Ritorna i punti (u,v,w) del contorno (rettangolo + arco)
  localOutline() {
    const [u0, v0] = this.wallPointUV;
    const half = this.widthM / 2.0;
    const along = this._along();

    const pts = [];
    const left = [u0 - along[0] * half, v0 - along[1] * half];
    const right = [u0 + along[0] * half, v0 + along[1] * half];

    pts.push([left[0], left[1], this.sillM]);
    pts.push([right[0], right[1], this.sillM]);
    pts.push([right[0], right[1], this.headM]);

    if (this.archRiseM > 0) {
      for (let i = 1; i < this.nArchPoints; i++) {
        const t = Math.PI * i / this.nArchPoints;
        const x = Math.cos(t) * half;
        const y = Math.sin(t) * this.archRiseM;
        const pu = u0 + along[0] * x;
        const pv = v0 + along[1] * x;
        pts.push([pu, pv, this.headM + y]);
      }
    }
    pts.push([left[0], left[1], this.headM]);
    return pts;
  }

  // Come localOutline() ma con coordinate texture (u_tex,v_tex) in [0,1]
  localOutlineWithUV() {
    const outline = this.localOutline();
    const top = this.headM + this.archRiseM;
    const half = this.widthM / 2.0;
    const [u0, v0] = this.wallPointUV;
    const along = this._along();
    const mag = Math.hypot(along[0], along[1]) || 1.0;

    return outline.map(([pu, pv, pw]) => {
      const xAlong = ((pu - u0) * along[0] + (pv - v0) * along[1]) / (mag * mag);
      const uTex = half > 0 ? (xAlong + half) / (2 * half) : 0.5;
      const vTex = top > this.sillM ? (pw - this.sillM) / (top - this.sillM) : 0.0;
      return { point: [pu, pv, pw], uv: [uTex, vTex] };
    });
  }
}

class ChurchModel {
  constructor({ facadeAzimuthDeg = FACADE_AZIMUTH_DEG, naveLengthM = NAVE_LENGTH_M, naveWidthM = NAVE_WIDTH_M, windows = [] } = {}) {
    this.facadeAzimuthDeg = facadeAzimuthDeg;
    this.naveLengthM = naveLengthM;
    this.naveWidthM = naveWidthM;
    this.windows = windows;
  }

  localToEnu(u, v, w) {
    const azU = RAD * (((this.facadeAzimuthDeg + 180.0) % 360.0));
    const azV = RAD * (((this.facadeAzimuthDeg + 90.0) % 360.0));
    const uHat = [Math.sin(azU), Math.cos(azU)];
    const vHat = [Math.sin(azV), Math.cos(azV)];
    const east = u * uHat[0] + v * vHat[0];
    const north = u * uHat[1] + v * vHat[1];
    return [east, north, w];
  }

  windowEnuOutline(win) {
    return win.localOutline().map(([u, v, w]) => this.localToEnu(u, v, w));
  }

  enuToLocalUV(east, north) {
    const azU = RAD * (((this.facadeAzimuthDeg + 180.0) % 360.0));
    const azV = RAD * (((this.facadeAzimuthDeg + 90.0) % 360.0));
    const uHat = [Math.sin(azU), Math.cos(azU)];
    const vHat = [Math.sin(azV), Math.cos(azV)];
    const u = east * uHat[0] + north * uHat[1];
    const v = east * vHat[0] + north * vHat[1];
    return [u, v];
  }

  chapelUPositions() {
    const n = N_CHAPELS_PER_SIDE;
    const margin = CHAPEL_ROW_MARGIN_M;
    const usable = this.naveLengthM - 2 * margin;
    const out = [];
    for (let i = 0; i < n; i++) out.push(margin + usable * (i + 0.5) / n);
    return out;
  }

  segmentOutwardAzimuth(p1uv, p2uv) {
    const mx = (p1uv[0] + p2uv[0]) / 2.0, my = (p1uv[1] + p2uv[1]) / 2.0;
    let dx = p2uv[0] - p1uv[0], dy = p2uv[1] - p1uv[1];
    const norm = Math.hypot(dx, dy);
    dx /= norm; dy /= norm;
    let perp = [-dy, dx];
    const center = [this.naveLengthM / 2.0, 0.0];
    const toCenter = [center[0] - mx, center[1] - my];
    if (perp[0] * toCenter[0] + perp[1] * toCenter[1] > 0) perp = [-perp[0], -perp[1]];
    const pa = this.localToEnu(mx, my, 0.0);
    const pb = this.localToEnu(mx + perp[0], my + perp[1], 0.0);
    return ((Math.atan2(pb[0] - pa[0], pb[1] - pa[1]) / RAD) + 360.0) % 360.0;
  }

  // Vertici del pentagono absidale (5 lati, CON rientranza)
  apseVertices() {
    const L = this.naveLengthM;
    const Wh = this.naveWidthM / 2.0;
    let u = L, v = Wh - APSE_RECESS_M;
    const pts = [[u, v]];
    for (let i = 0; i < APSE_FACET_AZIMUTHS_DEG.length; i++) {
      const az = APSE_FACET_AZIMUTHS_DEG[i];
      const length = APSE_FACET_LENGTHS_M[i];
      const tangentAz = RAD * (az + 90.0);
      const along = this.enuToLocalUV(Math.sin(tangentAz), Math.cos(tangentAz));
      u += along[0] * length;
      v += along[1] * length;
      pts.push([u, v]);
    }
    return pts;
  }

  // Contorno reale della pianta (navata + 8 nicchie cappelle + abside)
  floorOutlineLocal() {
    const L = this.naveLengthM;
    const Wh = this.naveWidthM / 2.0;
    const dw = CHAPEL_PROJECTION_WIDTH_M / 2.0;
    const dd = CHAPEL_PROJECTION_DEPTH_M;
    const chapelUs = this.chapelUPositions();

    const neSide = [[0.0, Wh]];
    for (const u of chapelUs) {
      neSide.push([u - dw, Wh]);
      neSide.push([u - dw, Wh + dd]);
      neSide.push([u + dw, Wh + dd]);
      neSide.push([u + dw, Wh]);
    }
    neSide.push([L, Wh]);

    const apse = this.apseVertices();

    const swSide = [[L, -Wh]];
    for (const u of [...chapelUs].reverse()) {
      swSide.push([u + dw, -Wh]);
      swSide.push([u + dw, -Wh - dd]);
      swSide.push([u - dw, -Wh - dd]);
      swSide.push([u - dw, -Wh]);
    }
    swSide.push([0.0, -Wh]);

    const outline = [...neSide, ...apse, ...swSide];
    outline.push(outline[0]);
    return outline;
  }

  coreOutlineLocal() {
    const L = this.naveLengthM;
    const Wh = this.naveWidthM / 2.0;
    const apse = this.apseVertices();
    const outline = [[0.0, Wh], [L, Wh], ...apse, [L, -Wh], [0.0, -Wh]];
    outline.push(outline[0]);
    return outline;
  }

  naveOnlyOutlineLocal() {
    const L = this.naveLengthM;
    const Wh = this.naveWidthM / 2.0;
    const outline = [[0.0, Wh], [L, Wh], [L, -Wh], [0.0, -Wh]];
    outline.push(outline[0]);
    return outline;
  }

  floorOutlineEnu() {
    return this.floorOutlineLocal().map(([u, v]) => {
      const [e, n] = this.localToEnu(u, v, 0.0);
      return [e, n];
    });
  }
}

function buildDefaultWindows() {
  const windows = [];
  const neNames = ["Notre-Dame-du-Rosaire", "Saint-Joseph", "Sacre-Coeur", "Saint-Louis"];
  const swNames = ["Saint-Jean-Baptiste", "Coeur-Immacule-de-Marie", "Saint-Antoine", "Sainte-Anne"];

  const churchTmp = new ChurchModel();
  const chapelUs = churchTmp.chapelUPositions();
  const Wh = NAVE_WIDTH_M / 2.0;
  // Les vitraux des chapelles sont des fenêtres de CLAIRE-VOIE sur le
  // mur haut de la nef (v=Wh), pas sur la paroi de fond de la niche :
  // leur appui (11.18 m) est entièrement AU-DESSUS de l'égout du toit
  // bas des chapelles (9.64 m) - voir le commentaire détaillé dans la
  // version Python (church_geometry.py).

  for (let i = 0; i < chapelUs.length; i++) {
    const u = chapelUs[i];
    windows.push(new Window({
      name: `Chapelle ${neNames[i]} (Ouest)`, group: "cappella",
      wallPointUV: [u, Wh], wallAzimuthDeg: (FACADE_AZIMUTH_DEG + 90.0) % 360.0,
      widthM: CHAPEL_WINDOW_WIDTH_M, sillM: CHAPEL_WINDOW_SILL_M, headM: CHAPEL_WINDOW_HEAD_M,
      archRiseM: CHAPEL_WINDOW_ARCH_RISE_M,
    }));
    windows.push(new Window({
      name: `Chapelle ${swNames[i]} (Est)`, group: "cappella",
      wallPointUV: [u, -Wh], wallAzimuthDeg: (FACADE_AZIMUTH_DEG - 90.0 + 360) % 360.0,
      widthM: CHAPEL_WINDOW_WIDTH_M, sillM: CHAPEL_WINDOW_SILL_M, headM: CHAPEL_WINDOW_HEAD_M,
      archRiseM: CHAPEL_WINDOW_ARCH_RISE_M,
    }));
  }

  const churchTmp2 = new ChurchModel();
  const apsePts = churchTmp2.apseVertices();
  const apseNames = [
    "Abside - côté court Ouest",
    "Abside - pan coupé Ouest",
    "Abside - pan de fond",
    "Abside - pan coupé Est",
    "Abside - côté court Est",
  ];
  for (let i = 0; i < 5; i++) {
    const p1 = apsePts[i], p2 = apsePts[i + 1];
    const mid = [(p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0];
    const az = APSE_FACET_AZIMUTHS_DEG[i];
    const isClocherSide = apseNames[i] === "Abside - côté court Ouest";
    windows.push(new Window({
      name: apseNames[i], group: "abside",
      wallPointUV: mid, wallAzimuthDeg: az,
      widthM: isClocherSide ? APSE_WINDOW_CLOCHER_WIDTH_M : APSE_WINDOW_WIDTH_M,
      sillM: isClocherSide ? APSE_WINDOW_CLOCHER_SILL_M : APSE_WINDOW_SILL_M,
      headM: isClocherSide ? APSE_WINDOW_CLOCHER_HEAD_M : APSE_WINDOW_HEAD_M,
      archRiseM: isClocherSide ? APSE_WINDOW_CLOCHER_ARCH_RISE_M : APSE_WINDOW_ARCH_RISE_M,
    }));
  }

  windows.push(new Window({
    name: "Façade - fenêtre centrale", group: "facciata",
    wallPointUV: [0.0, 0.0], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_CENTRAL_WINDOW_WIDTH_M, sillM: FACADE_CENTRAL_WINDOW_SILL_M, headM: FACADE_CENTRAL_WINDOW_HEAD_M,
    archRiseM: FACADE_CENTRAL_WINDOW_ARCH_RISE_M,
  }));
  windows.push(new Window({
    name: "Façade - fenêtre latérale Ouest", group: "facciata",
    wallPointUV: [0.0, FACADE_SIDE_WINDOW_OFFSET_M], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_SIDE_WINDOW_WIDTH_M, sillM: FACADE_SIDE_WINDOW_SILL_M, headM: FACADE_SIDE_WINDOW_HEAD_M,
    archRiseM: FACADE_SIDE_WINDOW_ARCH_RISE_M,
  }));
  windows.push(new Window({
    name: "Façade - fenêtre latérale Est", group: "facciata",
    wallPointUV: [0.0, -FACADE_SIDE_WINDOW_OFFSET_M], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_SIDE_WINDOW_WIDTH_M, sillM: FACADE_SIDE_WINDOW_SILL_M, headM: FACADE_SIDE_WINDOW_HEAD_M,
    archRiseM: FACADE_SIDE_WINDOW_ARCH_RISE_M,
  }));
  windows.push(new Window({
    name: "Façade - portail d'entrée", group: "porta",
    wallPointUV: [0.0, 0.0], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_DOOR_WIDTH_M, sillM: FACADE_DOOR_SILL_M, headM: FACADE_DOOR_HEAD_M,
    archRiseM: FACADE_DOOR_ARCH_RISE_M,
  }));

  return windows;
}

function defaultChurch() {
  return new ChurchModel({ windows: buildDefaultWindows() });
}
