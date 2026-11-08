// orbit-controls-lite.js
// Controlli camera minimali (orbita/zoom/pan) scritti da zero, senza
// dipendenze ES-module, per funzionare come script classico via
// file:// (la versione ufficiale THREE.OrbitControls e' distribuita
// solo come modulo ES, che il browser blocca per CORS quando la
// pagina e' aperta con doppio click invece che via server).
//
// Supporta sia mouse che touch tramite i Pointer Events, tracciando
// tutti i puntatori attivi per ID:
//   - 1 dito/tasto sinistro, trascina  = ruota intorno al target
//   - 2 dita, trascina                 = pan (sposta camera+target)
//   - 2 dita, avvicina/allontana       = pinch-to-zoom
//   - tasto destro del mouse, trascina = pan
//   - rotellina del mouse              = zoom

class OrbitControlsLite {
  constructor(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;
    this.target = new THREE.Vector3(0, 0, 0);
    this.minDistance = 1;
    this.maxDistance = 300;
    this.rotateSpeed = 1.0;
    this.zoomSpeed = 1.0;
    this.panSpeed = 1.0;
    this.dampingFactor = 0.08;
    this.enableDamping = true;

    this._spherical = new THREE.Spherical();
    this._sphericalDelta = new THREE.Spherical();
    this._panOffset = new THREE.Vector3();
    this._scale = 1;

    this._pointers = new Map(); // pointerId -> {x,y}
    this._panning = false; // true quando il gesto attivo e' pan (tasto destro o 2 dita)
    this._lastMidX = 0;
    this._lastMidY = 0;
    this._lastPinchDist = 0;

    this._onPointerDown = this._onPointerDown.bind(this);
    this._onPointerMove = this._onPointerMove.bind(this);
    this._onPointerUp = this._onPointerUp.bind(this);
    this._onWheel = this._onWheel.bind(this);
    this._onContextMenu = (e) => e.preventDefault();

    domElement.addEventListener("pointerdown", this._onPointerDown);
    window.addEventListener("pointermove", this._onPointerMove);
    window.addEventListener("pointerup", this._onPointerUp);
    window.addEventListener("pointercancel", this._onPointerUp);
    domElement.addEventListener("wheel", this._onWheel, { passive: false });
    domElement.addEventListener("contextmenu", this._onContextMenu);
    // impedisce lo scroll/zoom della pagina mentre si interagisce con la scena
    domElement.style.touchAction = "none";
  }

  _midpoint() {
    const pts = [...this._pointers.values()];
    if (pts.length === 1) return pts[0];
    const mx = (pts[0].x + pts[1].x) / 2;
    const my = (pts[0].y + pts[1].y) / 2;
    return { x: mx, y: my };
  }

  _pinchDistance() {
    const pts = [...this._pointers.values()];
    return Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
  }

  _onPointerDown(e) {
    try { this.domElement.setPointerCapture(e.pointerId); } catch (err) { /* ignora: non critico */ }
    this._pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    if (this._pointers.size === 2) {
      this._panning = true;
      const mid = this._midpoint();
      this._lastMidX = mid.x;
      this._lastMidY = mid.y;
      this._lastPinchDist = this._pinchDistance();
    } else if (this._pointers.size === 1) {
      this._panning = e.button === 2; // tasto destro del mouse = pan, altrimenti ruota
      this._lastMidX = e.clientX;
      this._lastMidY = e.clientY;
    }
  }

  _onPointerUp(e) {
    this._pointers.delete(e.pointerId);
    if (this._pointers.size === 1) {
      // resta un solo puntatore: ricomincia da capo come rotazione
      const [p] = [...this._pointers.values()];
      this._lastMidX = p.x;
      this._lastMidY = p.y;
      this._panning = false;
    } else if (this._pointers.size === 0) {
      this._panning = false;
    }
  }

  _onPointerMove(e) {
    if (!this._pointers.has(e.pointerId)) return;
    this._pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    const el = this.domElement;

    if (this._pointers.size >= 2) {
      // due dita: pan dal movimento del punto medio + pinch-zoom dalla distanza
      const mid = this._midpoint();
      const dx = mid.x - this._lastMidX;
      const dy = mid.y - this._lastMidY;
      this._lastMidX = mid.x;
      this._lastMidY = mid.y;
      this._applyPan(dx, dy);

      const dist = this._pinchDistance();
      if (this._lastPinchDist > 0) {
        const pinchRatio = this._lastPinchDist / dist;
        this._scale *= pinchRatio;
      }
      this._lastPinchDist = dist;
      return;
    }

    if (this._pointers.size !== 1) return;
    const dx = e.clientX - this._lastMidX;
    const dy = e.clientY - this._lastMidY;
    this._lastMidX = e.clientX;
    this._lastMidY = e.clientY;

    if (this._panning) {
      this._applyPan(dx, dy);
    } else {
      const angleX = 2 * Math.PI * dx / el.clientHeight * this.rotateSpeed;
      const angleY = 2 * Math.PI * dy / el.clientHeight * this.rotateSpeed;
      this._sphericalDelta.theta -= angleX;
      this._sphericalDelta.phi -= angleY;
    }
  }

  _applyPan(dx, dy) {
    const el = this.domElement;
    const offset = new THREE.Vector3().copy(this.camera.position).sub(this.target);
    let targetDistance = offset.length();
    targetDistance *= Math.tan((this.camera.fov / 2) * Math.PI / 180);
    const panX = (2 * dx * targetDistance / el.clientHeight) * this.panSpeed;
    const panY = (2 * dy * targetDistance / el.clientHeight) * this.panSpeed;

    const xDir = new THREE.Vector3();
    const yDir = new THREE.Vector3();
    const zDir = new THREE.Vector3();
    zDir.copy(this.camera.position).sub(this.target).normalize();
    xDir.crossVectors(this.camera.up, zDir).normalize();
    yDir.crossVectors(zDir, xDir).normalize();

    this._panOffset.addScaledVector(xDir, -panX);
    this._panOffset.addScaledVector(yDir, panY);
  }

  _onWheel(e) {
    e.preventDefault();
    const factor = Math.pow(0.95, this.zoomSpeed);
    if (e.deltaY < 0) this._scale *= factor;
    else this._scale /= factor;
  }

  update() {
    const offset = new THREE.Vector3().copy(this.camera.position).sub(this.target);
    this._spherical.setFromVector3(offset);

    if (this.enableDamping) {
      this._spherical.theta += this._sphericalDelta.theta * this.dampingFactor;
      this._spherical.phi += this._sphericalDelta.phi * this.dampingFactor;
    } else {
      this._spherical.theta += this._sphericalDelta.theta;
      this._spherical.phi += this._sphericalDelta.phi;
    }
    this._spherical.phi = Math.max(0.02, Math.min(Math.PI - 0.02, this._spherical.phi));
    this._spherical.radius *= this._scale;
    this._spherical.radius = Math.max(this.minDistance, Math.min(this.maxDistance, this._spherical.radius));

    if (this.enableDamping) {
      this.target.addScaledVector(this._panOffset, this.dampingFactor);
    } else {
      this.target.add(this._panOffset);
    }

    offset.setFromSpherical(this._spherical);
    this.camera.position.copy(this.target).add(offset);
    this.camera.lookAt(this.target);

    if (this.enableDamping) {
      this._sphericalDelta.theta *= (1 - this.dampingFactor);
      this._sphericalDelta.phi *= (1 - this.dampingFactor);
      this._panOffset.multiplyScalar(1 - this.dampingFactor);
    } else {
      this._sphericalDelta.set(0, 0, 0);
      this._panOffset.set(0, 0, 0);
    }
    this._scale = 1;
  }
}
