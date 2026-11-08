"""
Costruisce mappa_orientamento_ubaye.html: cartina interattiva con
orientamento, storia e fonti di ogni chiesa.

Uso:  python3 build_mappa.py
Legge: orientamento_chiese_ubaye.csv, osm_ubaye_raw.json, storia_fonti.py,
       mappa_base.json (confini comunali + fiumi), mappa_template.html
Applica anche al CSV le correzioni di verso ricavate dalle fonti storiche.
"""
import csv, json, os
from storia_fonti import FONTI, STORIA, CORREZIONI_DA_FONTI, CONFERME_DA_FONTI

HERE = os.path.dirname(os.path.abspath(__file__))
p = lambda f: os.path.join(HERE, f)
CARD = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
card = lambda a: CARD[int((a % 360) / 22.5 + 0.5) % 16]

rows = list(csv.DictReader(open(p('orientamento_chiese_ubaye.csv'))))
raw = {f"{e['type']}/{e['id']}": e for e in json.load(open(p('osm_ubaye_raw.json')))['elements']}

# --- correzioni / conferme dalle fonti scritte (idempotente)
for r in rows:
    o = r['osm']
    if o in CORREZIONI_DA_FONTI and not r['verifica_ortofoto'].startswith('CORRETTO DA FONTI'):
        old = float(r['apse_az']); new = CORREZIONI_DA_FONTI[o]
        r['apse_az'] = f"{new:.1f}"; r['facade_az'] = f"{(new + 180) % 360:.1f}"; r['dir'] = card(new)
        r['affidabilita'] = 'verificata'
        r['verifica_ortofoto'] = f"CORRETTO DA FONTI (calcolo automatico {old:.0f}°): {STORIA[o]['orient']}"
    elif o in CONFERME_DA_FONTI and r['affidabilita'] != 'verificata':
        r['affidabilita'] = 'verificata'
        r['verifica_ortofoto'] = 'confermato dalle fonti: ' + STORIA[o]['orient']
with open(p('orientamento_chiese_ubaye.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# --- pendenza del terreno da ../../orientatamento_chiese_Ubaye (chiese.py, DEM IGN RGE ALTI)
pend = {}
_pc = p('../../orientatamento_chiese_Ubaye/orientamento_chiese.csv')
if os.path.exists(_pc):
    for q in csv.DictReader(open(_pc, encoding='utf-8')):
        if q['slope_deg']:
            pend[q['osm_url'].rsplit('.org/', 1)[1]] = q

def pendio(o):
    q = pend.get(o)
    if not q:
        return None
    a = float(q['axis_vs_fallline'])
    rel = 'quasi lungo il pendio' if a <= 30 else ('quasi di traverso al pendio' if a >= 60 else 'obliquo al pendio')
    return f"{float(q['slope_deg']):.0f}° verso {float(q['downhill_az']):.0f}°; asse {rel} ({a:.0f}°)"

# --- dati per la mappa
out = []
for r in rows:
    t = raw[r['osm']].get('tags', {})
    s = STORIA.get(r['osm'], {})
    fonti = [{'t': FONTI[k][0], 'url': FONTI[k][1]} for k in s.get('fonti', [])]
    if t.get('ref:mhs'):
        fonti.append({'t': f"Mérimée {t['ref:mhs']} (POP, Ministero della Cultura)", 'url': f"https://pop.culture.gouv.fr/notice/merimee/{t['ref:mhs']}"})
    if t.get('wikidata'):
        fonti.append({'t': f"Wikidata {t['wikidata']}", 'url': f"https://www.wikidata.org/wiki/{t['wikidata']}"})
    fonti.append({'t': f"OpenStreetMap {r['osm']} (pianta)", 'url': f"https://www.openstreetmap.org/{r['osm']}"})
    if r['osm'] in pend:
        fonti.append({'t': "Pendenza: DEM IGN RGE ALTI, calcolata da chiese.py", 'url': "https://geoservices.ign.fr/rgealti"})
    storia = list(s.get('storia', []))
    if s.get('orient'):
        storia.append('Orientamento: ' + s['orient'])
    prot = s.get('protezione') or (f"Monumento storico ({t['ref:mhs']}, dal {t.get('mhs:inscription_date','?')})" if t.get('ref:mhs') else None)
    out.append(dict(osm=r['osm'], name=r['name'], commune=r['commune'], building=r['building'],
        lat=float(r['lat']), lon=float(r['lon']), L=float(r['L']), W=float(r['W']),
        apse_az=float(r['apse_az']), facade_az=float(r['facade_az']),
        affidabilita=r['affidabilita'], verifica_ortofoto=r['verifica_ortofoto'],
        epoca=s.get('epoca') or t.get('start_date'), protezione=prot, pendio=pendio(r['osm']), storia=storia, fonti=fonti))
json.dump(out, open(p('storia_fonti.json'), 'w'), ensure_ascii=False, indent=1)

html = open(p('mappa_template.html')).read()
html = html.replace('/*BASE*/null', open(p('mappa_base.json')).read())
html = html.replace('/*CHURCHES*/[]', json.dumps(out, ensure_ascii=False, separators=(',', ':')))
open(p('mappa_orientamento_ubaye.html'), 'w').write(html)
print(len(out), 'edifici;', sum(1 for c in out if c['storia']), 'con storia;',
      sum(1 for c in out if c['affidabilita'] in ('alta', 'verificata')), 'con verso affidabile')
