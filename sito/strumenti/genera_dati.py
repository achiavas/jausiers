#!/usr/bin/env python3
"""
genera_dati.py - porta nel sito i dati che nascono altrove:

  orientatamento_chiese_Ubaye/orientamento_chiese.csv        (chiese.py)
      -> sito/comune/dati/chiese_ubaye.js   window.CHIESE_UBAYE = [...]
  orientatamento_chiese_Ubaye/ricerca_saint_nicolas_jausiers.json  (/chiesa)
      -> sito/comune/dati/ricerca.js        window.RICERCA = {...} | null
  jausiers_sun3d_py/storia_jausiers.json  (cronologia dal diagnostico 2016)
      -> sito/comune/dati/storia_jausiers.js  window.STORIA_JAUSIERS = {...} | null
  jausiers_sun3d_py/ricerca_orientamento_ubaye/mappa_orientamento_ubaye.html
      -> sito/comune/dati/mappa_orientamento_ubaye.html (copia, cartina della pagina storia)

Il sito si apre anche con doppio click (file://), dove il browser non
legge i .json: per questo i dati diventano piccoli file .js.
Il mod jausiers scrive gia' comune/dati/ricerca.js a ogni salva_ricerca; questo
script serve dopo aver rilanciato chiese.py o per rigenerare tutto.

Uso:  python3 sito/strumenti/genera_dati.py
"""
from __future__ import annotations

import csv
import json
import os

import traduzioni_fr

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.normpath(os.path.join(QUI, ".."))
PROGETTO = os.path.normpath(os.path.join(SITO, ".."))
ORIENT = os.path.join(PROGETTO, "orientatamento_chiese_Ubaye")
DATI = os.path.join(SITO, "comune", "dati")

NUMERICI = {"lon", "lat", "area_m2", "elongation", "axis_az", "dev_from_EW",
            "slope_deg", "downhill_az", "axis_vs_fallline"}


def num(x: str):
    if x == "":
        return None
    v = float(x)
    return int(v) if v.is_integer() and "." not in x else v


def chiese() -> list[dict]:
    path = os.path.join(ORIENT, "orientamento_chiese.csv")
    righe, visti = [], set()
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["osm_url"] in visti:  # il CSV puo' contenere righe ripetute
                continue
            visti.add(r["osm_url"])
            righe.append({k: (num(v) if k in NUMERICI else v) for k, v in r.items()})
    # Se c'e' la ricerca di jausiers_sun3d_py, aggiunge verso dell'abside,
    # affidabilita', epoca e protezione (chiese.py conosce l'asse solo modulo 180).
    extra = os.path.join(PROGETTO, "jausiers_sun3d_py", "ricerca_orientamento_ubaye", "storia_fonti.json")
    if os.path.exists(extra):
        with open(extra, encoding="utf-8") as f:
            per_url = {f"https://www.openstreetmap.org/{c['osm']}": c for c in json.load(f)}
        for r in righe:
            c = per_url.get(r["osm_url"])
            if c:
                T = traduzioni_fr
                r.update(apse_az=c["apse_az"], facade_az=c["facade_az"], affidabilita=c["affidabilita"],
                         epoca=T.it(c.get("epoca")), protezione=T.it(c.get("protezione")),
                         storia=[T.it(p) for p in c.get("storia") or []],
                         fonti_storia=[dict(f, t=T.it(f["t"]), url=_web(f.get("url"))) for f in c.get("fonti") or []],
                         epoca_fr=T.fr(c.get("epoca")), protezione_fr=T.fr(c.get("protezione")),
                         storia_fr=[T.fr(p) for p in c.get("storia") or []],
                         fonti_storia_fr=[dict(f, t=T.fr(f["t"]), url=_web(f.get("url"))) for f in c.get("fonti") or []])
    return righe


def ricerca():
    """La scheda della ricerca su Saint-Nicolas. I campi italiani passano da
    traduzioni_fr.it (niente citazioni francesi), i titoli delle fonti hanno
    anche la versione francese (titolo_fr). Le fonti locali (file://) restano
    senza indirizzo: nel sito pubblicato non porterebbero da nessuna parte."""
    path = os.path.join(ORIENT, "ricerca_saint_nicolas_jausiers.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    T = traduzioni_fr
    for k in ("orientamento", "storia", "affidabilita"):
        r[k] = T.it(r.get(k))
    fonti = []
    for f in r.get("fonti") or []:
        f = dict(f, titolo=T.it(f.get("titolo")), titolo_fr=T.fr(f.get("titolo")), nota=T.it(f.get("nota")))
        if not str(f.get("url") or "").startswith("http"):
            f["url"] = None
        fonti.append(f)
    r["fonti"] = fonti
    r.pop("file", None)
    return r


def storia_jausiers():
    """Cronologia di Saint-Nicolas dal diagnostico 2016 e dalla delibera del
    1668 (jausiers_sun3d_py/storia_jausiers.json, scritto a mano)."""
    path = os.path.join(PROGETTO, "jausiers_sun3d_py", "storia_jausiers.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# Testi dell'interfaccia della cartina (mappa_template.html) in francese.
MAPPA_FR = [
    ("<title>Chiese dell'Ubaye, orientamento</title>", "<title>Églises de l'Ubaye, orientation</title>"),
    ("<h1>Chiese dell'Ubaye</h1>", "<h1>Églises de l'Ubaye</h1>"),
    ("La freccia indica la direzione dell'abside. Azimut da Nord, in senso orario.",
     "La flèche indique la direction de l'abside. Azimut compté depuis le nord, dans le sens horaire."),
    ("Cartina dei 14 comuni della valle dell'Ubaye con l'orientamento di 75 chiese e cappelle",
     "Carte des 14 communes de la vallée de l'Ubaye avec l'orientation de 75 églises et chapelles"),
    ('aria-label="Ingrandisci"', 'aria-label="Agrandir"'),
    ('aria-label="Riduci"', 'aria-label="Réduire"'),
    ('aria-label="Vista intera"', 'aria-label="Vue d\'ensemble"'),
    ("<b>Affidabilità del verso</b>", "<b>Fiabilité du sens</b>"),
    ("Rosa delle direzioni delle absidi", "Rose des directions des absides"),
    ("Scegli un edificio", "Choisir un édifice"),
    ("Orientamento misurato sulle piante OpenStreetMap e verificato a vista sulle ortofoto IGN; Jausiers tarato sulla planimetria catastale del programma",
     "Orientation mesurée sur les plans OpenStreetMap et vérifiée à l'œil sur les orthophotos IGN ; Jausiers calé sur le plan cadastral du programme"),
    ("Storia riassunta da Wikipedia (fr) e Wikidata; protezioni da Mérimée. Confini comunali: geo.api.gouv.fr. Fiumi e piante: © contributori OpenStreetMap (ODbL).",
     "Histoire résumée d'après Wikipédia et Wikidata ; protections d'après Mérimée. Limites communales : geo.api.gouv.fr. Rivières et plans : © contributeurs OpenStreetMap (ODbL)."),
    ("verificata:'Verificata (ortofoto o fonti)', alta:'Alta (calcolo)', 'asse sì, verso incerto':'Asse certo, verso incerto', 'bassa (pianta quasi quadrata)':'Bassa: pianta quasi quadrata', 'pianta OSM dubbia':'Pianta OSM dubbia'",
     "verificata:'Vérifiée (orthophoto ou sources)', alta:'Élevée (calcul)', 'asse sì, verso incerto':'Axe sûr, sens incertain', 'bassa (pianta quasi quadrata)':'Faible : plan presque carré', 'pianta OSM dubbia':'Plan OSM douteux'"),
    ("${d.name||'edificio senza nome'}, ${d.commune}, abside ${Math.round(d.apse_az)} gradi",
     "${d.name||'édifice sans nom'}, ${d.commune}, abside ${Math.round(d.apse_az)} degrés"),
    ("${d.name||'(senza nome)'} · ${d.commune}", "${d.name||'(sans nom)'} · ${d.commune}"),
    ("absidi affidabili.</b> ${east} guardano tra NE ed E, ${west} tra SO e NO. Nell'Ubaye l'abside a est non è la regola.",
     "absides fiables.</b> ${east} regardent entre le NE et l'E, ${west} entre le SO et le NO. Dans l'Ubaye, l'abside à l'est n'est pas la règle."),
    ("['Facciata',", "['Façade',"),
    ("['Pianta',", "['Plan',"),
    ("['Epoca',", "['Époque',"),
    ("['Protezione',", "['Protection',"),
    ("['Pendio',", "['Pente',"),
    ("['Coordinate',", "['Coordonnées',"),
    ("Nessuna notizia storica trovata nelle fonti aperte consultate.", "Aucune information historique trouvée dans les sources ouvertes consultées."),
    ("c.name||'Edificio senza nome in OSM'", "c.name||'Édifice sans nom dans OSM'"),
    ('style="margin-top:16px">Storia</div>', 'style="margin-top:16px">Histoire</div>'),
    ('style="margin-top:10px">Fonti</div>', 'style="margin-top:10px">Sources</div>'),
    ("${c.name||'(senza nome)'} · ${Math.round(c.apse_az)}°", "${c.name||'(sans nom)'} · ${Math.round(c.apse_az)}°"),
]
CAMPI_MAPPA = ("verifica_ortofoto", "epoca", "protezione", "pendio")


def _testi(c: dict, tradurre) -> dict:
    """Copia di una scheda della cartina con i testi passati da tradurre()."""
    c = dict(c)
    for k in CAMPI_MAPPA:
        c[k] = tradurre(c.get(k))
    c["storia"] = [tradurre(p) for p in c.get("storia") or []]
    c["fonti"] = [dict(f, t=tradurre(f["t"]), url=_web(f.get("url"))) for f in c.get("fonti") or []]
    return c


def _web(url):
    """Solo gli indirizzi web: un file del computer (file://...) non serve nel sito."""
    return url if str(url or "").startswith("http") else None


def copia_mappa() -> bool:
    """La cartina dell'orientamento delle chiese dell'Ubaye, in due lingue:
    mappa_orientamento_ubaye.html (italiano) e mappa_orientamento_ubaye_fr.html.
    Si ricostruisce come build_mappa.py (mappa_template.html + mappa_base.json
    + storia_fonti.json) passando i testi da traduzioni_fr."""
    cartella = os.path.join(PROGETTO, "jausiers_sun3d_py", "ricerca_orientamento_ubaye")
    file = {n: os.path.join(cartella, n) for n in ("mappa_template.html", "mappa_base.json", "storia_fonti.json")}
    if not all(os.path.exists(f) for f in file.values()):
        return False
    with open(file["mappa_template.html"], encoding="utf-8") as f:
        modello = f.read()
    with open(file["mappa_base.json"], encoding="utf-8") as f:
        base = f.read()
    with open(file["storia_fonti.json"], encoding="utf-8") as f:
        schede = json.load(f)
    for lingua, tradurre in (("it", traduzioni_fr.it), ("fr", traduzioni_fr.fr)):
        html = modello
        if lingua == "fr":
            for a, b in MAPPA_FR:
                if a not in html:
                    print(f"ATTENZIONE: testo della cartina non trovato (francese da aggiornare): {a[:60]}")
                html = html.replace(a, b)
        html = html.replace("<head>", f'<head>\n<meta http-equiv="content-language" content="{lingua}">', 1)
        html = html.replace("/*BASE*/null", base)
        html = html.replace("/*CHURCHES*/[]", json.dumps([_testi(c, tradurre) for c in schede], ensure_ascii=False, separators=(",", ":")))
        html = f'<!-- Generato da sito/strumenti/genera_dati.py ({lingua}): non modificare a mano. -->\n' + html
        nome = "mappa_orientamento_ubaye.html" if lingua == "it" else "mappa_orientamento_ubaye_fr.html"
        with open(os.path.join(DATI, nome), "w", encoding="utf-8") as f:
            f.write(html)
    return True


def scrivi(nome: str, variabile: str, valore) -> None:
    os.makedirs(DATI, exist_ok=True)
    testo = (f"// Generato da strumenti/genera_dati.py: non modificare a mano.\n"
             f"window.{variabile} = {json.dumps(valore, ensure_ascii=False, indent=1)};\n")
    with open(os.path.join(DATI, nome), "w", encoding="utf-8") as f:
        f.write(testo)
    print(f"scritto dati/{nome}")


def main() -> None:
    sf = os.path.join(PROGETTO, "jausiers_sun3d_py", "ricerca_orientamento_ubaye", "storia_fonti.json")
    if os.path.exists(sf):
        with open(sf, encoding="utf-8") as f:
            paragrafi = list(dict.fromkeys(p for c in json.load(f) for p in c.get("storia") or []))
        for p in traduzioni_fr.abbina_storia(paragrafi):
            print("ATTENZIONE: paragrafo nuovo o cambiato, manca il francese:", p[:80])
    c = chiese()
    scrivi("chiese_ubaye.js", "CHIESE_UBAYE", c)
    r = ricerca()
    scrivi("ricerca.js", "RICERCA", r)
    scrivi("storia_jausiers.js", "STORIA_JAUSIERS", storia_jausiers())
    print("cartina dell'Ubaye: " + ("scritta in italiano e francese" if copia_mappa() else "assente"))
    if traduzioni_fr.MANCANTI:
        print(f"ATTENZIONE: {len(set(traduzioni_fr.MANCANTI))} testi senza traduzione francese (restano in italiano):")
        for t in sorted(set(traduzioni_fr.MANCANTI)):
            print("  -", t[:100])
    print(f"{len(c)} chiese; ricerca: {'presente' if r else 'assente (lancia /chiesa)'}")


if __name__ == "__main__":
    main()
