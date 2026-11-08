// church-geometry.js
// Porting 1:1 di church_geometry.py — vedi quel file per i commenti
// completi sulla provenienza di ogni quota (misurata / stimata).
// Ogni costante deve restare UGUALE al Python: lo controlla
// strumenti/verifica_sync.py. Unica aggiunta: l'orientamento scelto in
// parametri.js (piantine di default) ruota facciata e abside.

const LATITUDE_DEG = 44.41978;
const LONGITUDE_DEG = 6.73401;
const TIMEZONE_NAME = "Europe/Paris";

// Valore delle piantine (= FACADE_AZIMUTH_DEG di church_geometry.py).
const FACADE_AZIMUTH_PIANTINE_DEG = 160.0;
const ORIENTAMENTO = scegliOrientamento(FACADE_AZIMUTH_PIANTINE_DEG); // parametri.js
const FACADE_AZIMUTH_DEG = ORIENTAMENTO.facciata;

const NAVE_LENGTH_M = 26.52;
const NAVE_WIDTH_M = 13.37;
const N_CHAPELS_PER_SIDE = 4;

const WALL_HEIGHT_M = 16.56;
const CHAPEL_ROOF_HEIGHT_M = 9.64;
const CHAPEL_ROOF_PITCH_RISE_M = 1.31;
const ROOF_RIDGE_RISE_M = 6.57;

const CHAPEL_PROJECTION_DEPTH_M = 2.19;
// Arco d'ingresso delle cappelle, misurato sulle foto raddrizzate (vedi church_geometry.py)
const CHAPEL_ARCH_RADIUS_M = 2.13;
const CHAPEL_ARCH_SPRING_M = 5.39;
// Gradini del presbiterio (vedi church_geometry.py): stimati, da verificare
const GRADINI_N = 3;
const GRADINO_ALZATA_M = 0.16;
const GRADINO_PEDATA_M = 0.32;
// Arredi (vedi church_geometry.py): misure stimate dalle foto
const BANCHI_U_INIZIO_M = 5.0;
const BANCHI_PASSO_M = 0.95;
const BANCHI_V_CORRIDOIO_M = 1.15;
const BANCHI_V_ESTERNO_M = 5.0;
const ALTARE_U_CENTRO_M = NAVE_LENGTH_M + 2.4;
const ALTARE_LARGHEZZA_M = 2.2;
const ALTARE_PROFONDITA_M = 0.9;
const ALTARE_ALTEZZA_M = 0.95;
const BALAUSTRA_U_M = NAVE_LENGTH_M + 0.15;
const BALAUSTRA_ALTEZZA_M = 0.9;
const BALAUSTRA_VARCO_M = 1.2;
const RISCALDAMENTO_U_M = NAVE_LENGTH_M + 0.6;
const RISCALDAMENTO_V_M = 4.6;
const RISCALDAMENTO_LARGHEZZA_M = 1.4;
const RISCALDAMENTO_PROFONDITA_M = 0.6;
const RISCALDAMENTO_ALTEZZA_M = 2.9;
// pulpito in legno fra la 3a e la 4a cappella a sinistra (vedi church_geometry.py)
const PULPITO_FRA_CAPPELLE = [2, 3];
const PULPITO_RAGGIO_M = 0.6;
const PULPITO_PIANO_M = 2.2;
const PULPITO_PARAPETTO_M = 1.1;
const PULPITO_BALDACCHINO_M = 5.0;
const PULPITO_CIMA_M = 6.6;
// consolle dell'organo (vedi church_geometry.py)
const ORGANO_U_M = NAVE_LENGTH_M - GRADINI_N * GRADINO_PEDATA_M - 1.1;
const ORGANO_V_M = 4.3;
const ORGANO_LARGHEZZA_M = 1.4;
const ORGANO_PROFONDITA_M = 0.65;
const ORGANO_ALTEZZA_M = 0.95;
// cornicione interno tutto intorno (vedi church_geometry.py)
const CORNICIONE_BASE_M = 8.9;
const CORNICIONE_CIMA_M = 10.4;
const CORNICIONE_SPORGENZA_M = 0.62;
// volta dell'abside a ombrello (vedi church_geometry.py)
const VOLTA_ABSIDE_CHIAVE_M = 15.0;
const VOLTA_ABSIDE_LUNETTE_M = 14.2;
// chiave sopra il centro dell'abside; suddivisione del bordo e dei meridiani
// (la stessa della texture, volta_da_video.py)
const VOLTA_ABSIDE_NT = 14;
const VOLTA_ABSIDE_NA = 24;
const VOLTA_ABSIDE_NM = 14;
// volta della navata a botte con lunette sopra le finestre alte (stimata)
const VOLTA_NAVATA_CHIAVE_M = 16.3;
const VOLTA_NAVATA_LUNETTE_M = 14.2;
const VOLTA_NAVATA_LUNETTA_LARGA_M = 3.2;
// lampadario di cristallo dell'abside, doppio (vedi church_geometry.py)
const LAMPADARIO_ALTO_M = 12.1;
const LAMPADARIO_BASSO_M = 8.8;
const LAMPADARIO_RAGGIO_BRACCI_M = 0.65;
const LAMPADARIO_RAGGIO_BRACCI_BASSO_M = 0.57;
const LAMPADARIO_N_BRACCI = 12;
// tre lampadari singoli sull'asse della navata (vedi church_geometry.py)
const LAMPADARI_NAVATA_U_M = [7.2, 15.9, 24.6];
const LAMPADARIO_NAVATA_ALTO_M = 13.9;
const LAMPADARIO_NAVATA_BASSO_M = 11.2;
// Controfacciata e lesene fra le cappelle (vedi church_geometry.py), stimate
const BUSSOLA_LARGHEZZA_M = 5.6;
const BUSSOLA_PROFONDITA_M = 1.2;
const BUSSOLA_ALTEZZA_M = 5.5;
const PORTONE_LARGHEZZA_M = 2.6;
const PORTONE_ALTEZZA_M = 4.8;
const LESENA_LARGHEZZA_M = 1.0;
const LESENA_SPORGENZA_M = 0.12;
const LESENA_ZOCCOLO_M = 1.0;
const CROCE_CONSACRAZIONE_M = 3.37;
const CHAPEL_PROJECTION_WIDTH_M = 4.82;
const CHAPEL_ROW_MARGIN_M = 1.10;

const APSE_RECESS_M = 1.31;
// Valori delle piantine (= APSE_FACET_AZIMUTHS_DEG di church_geometry.py),
// ruotati della stessa differenza della facciata.
const APSE_FACET_AZIMUTHS_PIANTINE_DEG = [250.0, 301.4, 340.9, 17.6, 70.0];
const APSE_FACET_AZIMUTHS_DEG = APSE_FACET_AZIMUTHS_PIANTINE_DEG.map((a) => mod360(a + ORIENTAMENTO.delta));
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
const FACADE_SIDE_WINDOW_OFFSET_M = 1.93;  // dalla foto frontale della facciata (era 1.45, stimata)

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

  // Contorno "nucleo" della navata+abside, SENZA le nicchie sporgenti
  // delle cappelle (lati Ovest/Est semplici, a filo v=+-Wh) - usato
  // per il muro ALTO della navata: le nicchie hanno un proprio muro
  // BASSO separato (vedi buildChapelWallStructures() in church-mesh.js).
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
  // Le vetrate delle cappelle sono finestre di CLERISTORIO sul muro
  // alto della navata (v=Wh), non sulla parete di fondo della
  // nicchia: il loro davanzale (11.18 m) e' interamente SOPRA la
  // gronda del tetto basso delle cappelle (9.64 m) - vedi il commento
  // esteso nella versione Python (church_geometry.py) per il dettaglio.

  for (let i = 0; i < chapelUs.length; i++) {
    const u = chapelUs[i];
    windows.push(new Window({
      name: `Cappella ${neNames[i]} (Ovest)`, group: "cappella",
      wallPointUV: [u, Wh], wallAzimuthDeg: (FACADE_AZIMUTH_DEG + 90.0) % 360.0,
      widthM: CHAPEL_WINDOW_WIDTH_M, sillM: CHAPEL_WINDOW_SILL_M, headM: CHAPEL_WINDOW_HEAD_M,
      archRiseM: CHAPEL_WINDOW_ARCH_RISE_M,
    }));
    windows.push(new Window({
      name: `Cappella ${swNames[i]} (Est)`, group: "cappella",
      wallPointUV: [u, -Wh], wallAzimuthDeg: (FACADE_AZIMUTH_DEG - 90.0 + 360) % 360.0,
      widthM: CHAPEL_WINDOW_WIDTH_M, sillM: CHAPEL_WINDOW_SILL_M, headM: CHAPEL_WINDOW_HEAD_M,
      archRiseM: CHAPEL_WINDOW_ARCH_RISE_M,
    }));
  }

  const churchTmp2 = new ChurchModel();
  const apsePts = churchTmp2.apseVertices();
  const apseNames = [
    "Abside - lato corto Ovest",
    "Abside - pannello smussato Ovest",
    "Abside - pannello di fondo",
    "Abside - pannello smussato Est",
    "Abside - lato corto Est",
  ];
  for (let i = 0; i < 5; i++) {
    const p1 = apsePts[i], p2 = apsePts[i + 1];
    const mid = [(p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0];
    const az = APSE_FACET_AZIMUTHS_DEG[i];
    const isClocherSide = apseNames[i] === "Abside - lato corto Ovest";
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
    name: "Facciata - finestra centrale", group: "facciata",
    wallPointUV: [0.0, 0.0], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_CENTRAL_WINDOW_WIDTH_M, sillM: FACADE_CENTRAL_WINDOW_SILL_M, headM: FACADE_CENTRAL_WINDOW_HEAD_M,
    archRiseM: FACADE_CENTRAL_WINDOW_ARCH_RISE_M,
  }));
  windows.push(new Window({
    name: "Facciata - finestra laterale Ovest", group: "facciata",
    wallPointUV: [0.0, FACADE_SIDE_WINDOW_OFFSET_M], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_SIDE_WINDOW_WIDTH_M, sillM: FACADE_SIDE_WINDOW_SILL_M, headM: FACADE_SIDE_WINDOW_HEAD_M,
    archRiseM: FACADE_SIDE_WINDOW_ARCH_RISE_M,
  }));
  windows.push(new Window({
    name: "Facciata - finestra laterale Est", group: "facciata",
    wallPointUV: [0.0, -FACADE_SIDE_WINDOW_OFFSET_M], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_SIDE_WINDOW_WIDTH_M, sillM: FACADE_SIDE_WINDOW_SILL_M, headM: FACADE_SIDE_WINDOW_HEAD_M,
    archRiseM: FACADE_SIDE_WINDOW_ARCH_RISE_M,
  }));
  windows.push(new Window({
    name: "Facciata - portale d'ingresso", group: "porta",
    wallPointUV: [0.0, 0.0], wallAzimuthDeg: FACADE_AZIMUTH_DEG,
    widthM: FACADE_DOOR_WIDTH_M, sillM: FACADE_DOOR_SILL_M, headM: FACADE_DOOR_HEAD_M,
    archRiseM: FACADE_DOOR_ARCH_RISE_M,
  }));

  return windows;
}

function defaultChurch() {
  return new ChurchModel({ windows: buildDefaultWindows() });
}

// Due gradini all'ingresso di ogni cappella (vedi church_geometry.py): misure stimate
const CAPPELLA_GRADINI_N = 2;
const CAPPELLA_GRADINO_ALZATA_M = 0.15;
const CAPPELLA_GRADINO_PEDATA_M = 0.30;
// Altari delle cappelle (vedi church_geometry.py): [nome, lato, indice, colore davanti, colore gradino]
const ALTARE_CAPPELLA_LARGHEZZA_M = 2.0;
const ALTARE_CAPPELLA_PROFONDITA_M = 0.75;
const ALTARE_CAPPELLA_ALTEZZA_M = 0.95;
const ALTARI_CAPPELLE = [
  ["cappella_ovest_1", +1, 0, 0xe8e4dc, 0xa79c91],   // bianco: la tovaglia scende fino a terra; gradino di marmo chiaro
  ["cappella_ovest_2", +1, 1, 0x8c6f52, 0xa07838],   // Sant'Antonio: paliotto a piastrelle sotto il pizzo; gradino di legno dorato
  ["cappella_ovest_3", +1, 2, 0x466e78, 0xaf9150],   // paliotto verde-azzurro; gradino dorato
  ["cappella_ovest_4", +1, 3, 0x867f71, 0x867f71],   // altare non visibile nelle foto (banchi): pietra grigia
  ["cappella_est_1", -1, 0, 0xa58c5a, 0x8a8270],   // marmo giallo e grigio come la pala
  ["cappella_est_2", -1, 1, 0x344e8c, 0x966e46],   // paliotto blu (I M J); gradino di marmo rosso e oro
  ["cappella_est_3", -1, 2, 0x28231e, 0xaa8c50],   // paliotto nero e oro (REQUIESCANT IN PACE); gradino dorato
  ["cappella_est_4", -1, 3, 0x464b41, 0xb4965a],   // paliotto di marmo verde scuro; gradino dorato
];

// Quota se (u, v) e' sui gradini o dentro una cappella, altrimenti null
function quotaCappella(u, v) {
  const wh = NAVE_WIDTH_M / 2.0, av = Math.abs(v);
  if (av < wh - CAPPELLA_GRADINO_PEDATA_M || av > wh + CHAPEL_PROJECTION_DEPTH_M) return null;
  const campata = (NAVE_LENGTH_M - 2 * CHAPEL_ROW_MARGIN_M) / N_CHAPELS_PER_SIDE;
  for (let i = 0; i < N_CHAPELS_PER_SIDE; i++) {
    const du = Math.abs(u - (CHAPEL_ROW_MARGIN_M + (i + 0.5) * campata));
    const piano = CAPPELLA_GRADINI_N * CAPPELLA_GRADINO_ALZATA_M;
    if (av >= wh + CAPPELLA_GRADINO_PEDATA_M && du <= CHAPEL_PROJECTION_WIDTH_M / 2) return piano;
    if (du <= CHAPEL_ARCH_RADIUS_M) return av >= wh ? piano : CAPPELLA_GRADINO_ALZATA_M;
  }
  return null;
}

// Quota del pavimento in (u, v): 0 in navata, i gradini davanti
// all'arco trionfale, GRADINI_N * GRADINO_ALZATA_M nell'abside, i
// gradini e il piano delle cappelle.
// Le scatole [u0, u1, v0, v1, w0, w1] dei banchi: sedile, schienale (verso
// la facciata: si guarda l'abside), mensola sotto e due fianchi. Dal fondo
// fino a ~1.5 m dal primo gradino. Servono alla mesh e alla luce delle
// vetrate che cade sui banchi.
function banchiScatole(church) {
  const uFine = church.naveLengthM - GRADINI_N * GRADINO_PEDATA_M - 1.5;
  const out = [];
  for (let u = BANCHI_U_INIZIO_M; u + 0.45 <= uFine; u += BANCHI_PASSO_M) {
    for (const lato of [1.0, -1.0]) {
      const [a, b] = [lato * BANCHI_V_CORRIDOIO_M, lato * BANCHI_V_ESTERNO_M].sort((x, y) => x - y);
      out.push([u, u + 0.40, a, b, 0.42, 0.46]);             // sedile
      out.push([u - 0.04, u, a, b, 0.46, 0.92]);             // schienale
      out.push([u + 0.10, u + 0.40, a, b, 0.10, 0.14]);      // mensola sotto
      for (const v of [a, b]) out.push([u - 0.06, u + 0.45, v - 0.03, v + 0.03, 0.0, 0.95]);  // fianchi
    }
  }
  return out;
}

function quotaPavimento(u, v) {
  const qc = quotaCappella(u, v);
  if (qc !== null) return qc;
  if (Math.abs(v) > NAVE_WIDTH_M / 2.0 - APSE_RECESS_M) return 0.0;
  const u0 = NAVE_LENGTH_M - GRADINI_N * GRADINO_PEDATA_M;
  if (u < u0) return 0.0;
  if (u >= NAVE_LENGTH_M) return GRADINI_N * GRADINO_ALZATA_M;
  return (Math.floor((u - u0) / GRADINO_PEDATA_M) + 1) * GRADINO_ALZATA_M;
}
