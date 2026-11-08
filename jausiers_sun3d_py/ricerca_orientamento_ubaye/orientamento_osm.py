import json, math, sys, urllib.request, time
d = json.load(open(sys.argv[1]))
R = 6371000.0
def ring_of(e):
    if e['type'] == 'way': return [(p['lat'], p['lon']) for p in e['geometry']]
    if e['type'] == 'relation':
        outs = [m for m in e.get('members', []) if m.get('role') == 'outer' and 'geometry' in m]
        if not outs: return None
        m = max(outs, key=lambda m: len(m['geometry']))
        return [(p['lat'], p['lon']) for p in m['geometry']]
    return None
def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];up=[]
    for p in pts:
        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
def width_at(xy, s, ax):  # extent across axis of polygon slice near projection s
    ux, uy = math.sin(ax), math.cos(ax); vx, vy = uy, -ux
    vals = []
    n = len(xy)
    for i in range(n):
        (x1,y1),(x2,y2) = xy[i], xy[(i+1)%n]
        a1 = x1*ux+y1*uy; a2 = x2*ux+y2*uy
        if (a1-s)*(a2-s) <= 0 and a1 != a2:
            t = (s-a1)/(a2-a1); x = x1+t*(x2-x1); y = y1+t*(y2-y1)
            vals.append(x*vx+y*vy)
    return (max(vals)-min(vals)) if len(vals) >= 2 else 0.0
def commune(lat, lon):
    try:
        u = f"https://geo.api.gouv.fr/communes?lat={lat:.6f}&lon={lon:.6f}&fields=nom,code"
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'church-orientation-research'}), timeout=20) as r:
            j = json.load(r); return (j[0]['nom'], j[0]['code']) if j else ('?', '')
    except Exception as ex: return ('?', '')
rows = []
for e in d['elements']:
    t = e.get('tags', {})
    ring = ring_of(e)
    if not ring or len(ring) < 4: continue
    if ring[0] == ring[-1]: ring = ring[:-1]
    lat0 = sum(p[0] for p in ring)/len(ring); lon0 = sum(p[1] for p in ring)/len(ring)
    k = math.cos(math.radians(lat0))
    xy = [(math.radians(lo-lon0)*R*k, math.radians(la-lat0)*R) for la,lo in ring]  # x=E, y=N
    h = hull(xy)
    best = None
    for i in range(len(h)):
        (x1,y1),(x2,y2) = h[i], h[(i+1)%len(h)]
        ang = math.atan2(x2-x1, y2-y1)  # azimuth from N
        ux, uy = math.sin(ang), math.cos(ang); vx, vy = uy, -ux
        a = [p[0]*ux+p[1]*uy for p in h]; b = [p[0]*vx+p[1]*vy for p in h]
        L, W = max(a)-min(a), max(b)-min(b)
        if L < W: L, W, ang = W, L, ang + math.pi/2
        if best is None or L*W < best[0]: best = (L*W, L, W, ang)
    _, L, W, ax = best
    ux, uy = math.sin(ax), math.cos(ax)
    proj = [p[0]*ux+p[1]*uy for p in xy]; smin, smax = min(proj), max(proj)
    # mean width over the last 20% at each end
    def endw(frac_from, frac_to):
        ws = [width_at(xy, smin+(smax-smin)*f, ax) for f in [frac_from+(frac_to-frac_from)*j/6 for j in range(1,6)]]
        return sum(ws)/len(ws)
    wplus = endw(0.80, 0.97); wminus = endw(0.03, 0.20)
    az = math.degrees(ax) % 360
    if wplus < wminus: apse = az; ratio = wplus/wminus if wminus else 1
    else: apse = (az+180) % 360; ratio = wminus/wplus if wplus else 1
    rows.append(dict(osm=f"{e['type']}/{e['id']}", name=t.get('name',''), building=t.get('building',''),
        lat=round(lat0,5), lon=round(lon0,5), L=round(L,1), W=round(W,1), elong=round(L/W,2) if W else 0,
        axis=round(min(az%180, az%180),1), apse_az=round(apse,1), end_ratio=round(ratio,2)))
for r in rows:
    r['commune'], r['insee'] = commune(r['lat'], r['lon']); time.sleep(0.05)
json.dump(rows, open(sys.argv[2],'w'), ensure_ascii=False, indent=1)
print(len(rows))
