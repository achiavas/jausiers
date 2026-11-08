import json, csv, math, sys, io, urllib.request, time
from PIL import Image, ImageDraw, ImageFont
P = '/Users/andreew_1/Documents/eglise_jausiers/jausiers_sun3d_py/ricerca_orientamento_ubaye/'
OUT = sys.argv[1]
raw = {f"{e['type']}/{e['id']}": e for e in json.load(open(P+'osm_ubaye_raw.json'))['elements']}
rows = [r for r in csv.DictReader(open(P+'orientamento_chiese_ubaye.csv')) if r['affidabilita'] != 'alta' or 'all' in sys.argv]
def merc(lat, lon):
    return lon*20037508.34/180, math.log(math.tan(math.radians(90+lat)/2))*20037508.34/math.pi
SZ = 420
tiles = []
for i, r in enumerate(rows, 1):
    e = raw[r['osm']]; pts = [(p['lat'], p['lon']) for p in e['geometry']]
    lat, lon = float(r['lat']), float(r['lon']); k = 1/math.cos(math.radians(lat))
    half = max(float(r['L'])*1.3, 14) * k
    cx, cy = merc(lat, lon)
    bbox = (cx-half, cy-half, cx+half, cy+half)
    u = ("https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=ORTHOIMAGERY.ORTHOPHOTOS"
         f"&STYLES=&CRS=EPSG:3857&BBOX={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&WIDTH={SZ}&HEIGHT={SZ}&FORMAT=image/jpeg")
    for a in range(4):
        try:
            img = Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'church-orientation-research'}), timeout=30).read())).convert('RGB'); break
        except Exception as ex:
            time.sleep(2*(a+1)); img = Image.new('RGB', (SZ, SZ), 'gray')
    d = ImageDraw.Draw(img)
    def px(la, lo):
        x, y = merc(la, lo); return ((x-bbox[0])/(2*half)*SZ, (bbox[3]-y)/(2*half)*SZ)
    d.line([px(*p) for p in pts], fill=(255, 255, 0), width=1)
    # arrow from centre toward computed apse, length L/2
    az = math.radians(float(r['apse_az'])); Lpx = float(r['L'])*k/(2*half)*SZ*0.75
    c = (SZ/2, SZ/2); tip = (c[0]+Lpx*math.sin(az), c[1]-Lpx*math.cos(az))
    d.line([c, tip], fill=(255, 0, 0), width=2); d.ellipse([tip[0]-4, tip[1]-4, tip[0]+4, tip[1]+4], fill=(255, 0, 0))
    d.rectangle([0, 0, SZ, 18], fill=(0, 0, 0))
    d.text((3, 3), f"#{i} {r['commune'][:16]} | {r['name'][:30]} | {float(r['apse_az']):.0f}", fill='white')
    d.text((SZ-14, 22), "N", fill=(0, 255, 255))
    tiles.append(img); r['idx'] = i
    print(i, r['osm'], r['name'], flush=True)
for s in range(0, len(tiles), 6):
    sheet = Image.new('RGB', (SZ*3, SZ*2), 'black')
    for j, t in enumerate(tiles[s:s+6]): sheet.paste(t, ((j%3)*SZ, (j//3)*SZ))
    sheet.save(f"{OUT}/sheet_{s//6+1:02d}.jpg", quality=88)
json.dump([{k: r[k] for k in ('idx', 'osm', 'commune', 'name', 'apse_az')} for r in rows], open(OUT+'/index.json', 'w'), ensure_ascii=False, indent=0)
