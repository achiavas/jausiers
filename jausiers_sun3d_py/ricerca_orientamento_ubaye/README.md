# Orientamento delle chiese e cappelle della valle dell'Ubaye

Ricerca del 06/11/2026. Misura dell'asse di **tutte le chiese e cappelle
mappate su OpenStreetMap** nei 14 comuni attuali della valle dell'Ubaye:
Barcelonnette, Enchastrayes, Faucon-de-Barcelonnette, Jausiers,
La Condamine-Châtelard, Le Lauzet-Ubaye, Les Thuiles, Méolans-Revel,
Pontis, Saint-Paul-sur-Ubaye, Saint-Pons, Ubaye-Serre-Ponçon,
Uvernet-Fours, Val d'Oronaye. In totale 75 edifici.

## Metodo

1. Query Overpass (bbox 44.33–44.62 N, 6.28–6.98 E) su
   `amenity=place_of_worship` e `building=church|chapel|cathedral`
   (dati grezzi: `osm_ubaye_raw.json`, © contributori OpenStreetMap, ODbL).
2. Comune assegnato con l'API ufficiale `geo.api.gouv.fr`. Gli edifici
   sul versante italiano (Valle Stura/Maira) sono stati esclusi.
3. **Asse**: lato lungo del rettangolo di area minima che contiene la
   pianta (stesso riferimento del programma: azimut da Nord, in senso orario).
4. **Verso (abside o facciata)**: si confronta la larghezza della pianta
   nell'ultimo 20% di ciascuna estremità. L'estremità più stretta viene
   presa come abside, perché il coro è più stretto della navata con le
   cappelle. `end_ratio` = larghezza lato abside / larghezza lato opposto.
5. Affidabilità:
   - **alta**: allungamento ≥ 1.25 e `end_ratio` ≤ 0.95;
   - **asse sì, verso incerto**: estremità di larghezza quasi uguale
     (abside piatta). L'asse è giusto, ma l'abside potrebbe stare a ±180°;
   - **bassa**: pianta quasi quadrata, asse non significativo.

Script riproducibile: `orientamento_osm.py <osm.json> <out.json>`.

## Taratura con i dati del programma (Jausiers)

Il modello del programma (`church_geometry.py`) per Saint-Nicolas-de-Myre usa
`FACADE_AZIMUTH_DEG = 160°`, quindi abside ≈ 340° (NNW). Questo valore viene
dalla planimetria catastale con freccia nord.
La pianta OSM della stessa chiesa dà **abside 336.3°**, quindi facciata 156°:
**differenza di circa 4°**, coerente con la precisione di un tracciato OSM.
Le cinque facce dell'abside del programma (250°, 301°, 341°, 18°, 70°)
sono simmetriche intorno a ~340°, e questo conferma l'asse.
Il metodo dà quindi un errore tipico di qualche grado sugli edifici
ben tracciati.

Per l'uso nel programma (`solar_position.py`, `church_geometry.py`)
basta mettere in `FACADE_AZIMUTH_DEG` il valore della colonna *facciata*,
insieme a lat/lon presi dal CSV.

## Verifica su ortofoto IGN (06/11/2026)

Ho controllato a vista tutti i 75 edifici sulle ortofoto IGN
(Géoplateforme, layer `ORTHOIMAGERY.ORTHOPHOTOS`), con sopra il contorno
OSM (giallo) e la direzione calcolata dell'abside (freccia rossa).
I fogli sono in `ortofoto/` (`incerte_*` = le 45 righe incerte o a
bassa affidabilità, `alta_*` = le 30 ad affidabilità alta). Si possono
rigenerare con `ortofoto_fogli.py`.

Risultati:
- **6 confermate**, con abside arrotondata o poligonale ben visibile:
  Jausiers Saint-Nicolas, Jausiers Saint-Sébastien (prima "verso
  incerto"), la cappella senza nome di Jausiers a S, La Condamine
  Saint-Clément, la cappella dei Pénitents Blancs e Saint-Pierre di
  Ubaye-Serre-Ponçon (prima "verso incerto").
- **3 corrette** (il calcolo automatico dava il verso opposto):
  - Méolans-Revel, Saint-Julien (way/127740306): da 138° a **318° NW**
  - Saint-Paul, chapelle Sainte-Marie-Madeleine: da 130° a **310° NW**
  - Val d'Oronaye, chapelle Sainte-Marie-Madeleine: da 98° a **278° W**
- **3 piante OSM dubbie**: un edificio non visibile in ortofoto
  (way/128050603), un contorno che comprende più edifici (Faucon,
  Saint-Jean-de-Matha) e un contorno parziale o sfasato (Enchastrayes,
  Saint-Pierre-et-Saint-Paul, che è uscita dal gruppo "alta").
- **Tutte le altre** non sono determinabili dall'alto: sono piccole
  cappelle col tetto a due falde e la testata piatta, e alla risoluzione
  dell'ortofoto (~20 cm) non si vede da che lato sta il coro. Per queste
  l'asse vale, il verso no. Servono foto da terra, la planimetria
  catastale o l'inventario del patrimonio (POP/Mérimée).

Tra le 30 chiese "alta", nessuna di quelle verificabili a vista
contraddice il calcolo automatico. Le 3 correzioni riguardano tutte
righe che avevo già segnato come incerte o a bassa affidabilità.

## Storia e fonti (08/11/2026)

Ogni edificio ha una scheda storica in italiano (67 su 75) con le fonti.
Le schede sono in `storia_fonti.py` (testo e codici delle fonti) e in
`storia_fonti.json` (dati completi usati dalla cartina).
Le fonti sono:
- **Wikipedia (fr)**: voci delle singole chiese (Jausiers, Saint-Paul,
  Maurin, Saint-Pons) e sezioni "Lieux et monuments" / "Art religieux"
  delle voci dei comuni, che a loro volta citano soprattutto
  R. Collier, *La Haute-Provence monumentale et artistique* (1986);
- **Wikidata**: nome esatto del hameau e codice Mérimée;
- **Mérimée / POP** (Ministero della Cultura) per i 5 monumenti protetti:
  Jausiers PA00080407, Saint-Paul PA00080475, Maurin PA00080476,
  Saint-Pons PA00080478, Fouillouse PA04000035;
- **OpenStreetMap** per la pianta, `start_date` e i tag di protezione.

Le fonti scritte hanno permesso un terzo controllo sull'orientamento:
- **corrette** 2 chiese: Saint-Pons (portale principale a ovest e chevet
  piatto, quindi abside a **103°** e non 283°) e la cappella di Chaudon a
  Méolans-Revel (campanile a vela sulla facciata ovest, quindi **82°** e
  non 262°). Chaudon era classificata "alta": la regola automatica può
  sbagliare anche lì;
- **confermate** 2 chiese: Saint-Paul (portale occidentale, abside 63°) e
  Laverq (campanile accanto alla facciata ovest, abside 82°);
- **discordanza** a Jausiers: Wikipedia parla di «facciata occidentale»,
  mentre planimetria catastale, OSM e ortofoto danno una facciata a SSE
  (156–160°). Tengo i dati misurati.

## Cartina interattiva

`mappa_orientamento_ubaye.html` (si apre in qualsiasi browser) mostra i
comuni e il corso dell'Ubaye. Ogni chiesa ha una freccia nella direzione
dell'abside, colorata per affidabilità. Cliccando su una chiesa si apre
la scheda con azimut, epoca, protezione, storia e fonti.
Si rigenera con `python3 build_mappa.py`, dopo aver modificato
`storia_fonti.py` o il CSV.

## Scambio con mod, sito e chiese.py (08/11/2026)

- **Pendenza**: da `../../orientatamento_chiese_Ubaye/orientamento_chiese.csv`
  (chiese.py, DEM IGN RGE ALTI) la cartina mostra il pendio per le 29
  chiese presenti in entrambe le analisi. Tra quelle su pendio ≥ 5°,
  13 hanno l'asse quasi di traverso al pendio (≥ 60°) e 4 quasi lungo il
  pendio (≤ 30°): le chiese tendono a seguire le curve di livello.
- **Mod jausiers e sito**: la ricerca su Saint-Nicolas (orientamento,
  storia e fonti, in italiano e francese) è salvata in
  `orientatamento_chiese_Ubaye/ricerca_saint_nicolas_jausiers.json` e `.md`,
  nel formato di `salva_ricerca`, e copiata nel sito
  (`sito/comune/dati/ricerca.js`) con `sito/strumenti/genera_dati.py`.

## Quadro d'insieme

Le 35 chiese con verso affidabile (22 "alta" + 13 "verificata"), per
ottante dell'abside: E 10, W 8, N 5, NW 4, NE 4, S 2, SE 2.

**Nell'Ubaye l'orientamento canonico verso est non è la regola.** Solo
14 absidi su 35 (40%) guardano tra NE ed E. Altre 12 guardano tra W e NW
(Les Thuiles, Saint-Vincent, Notre-Dame de Lumière, Saint-Julien di
Saint-Barthélemy) e diverse a nord/NNW (Barcelonnette, Jausiers,
Enchastrayes, La Condamine, Pontis). L'orientamento sembra dettato
soprattutto dal sito: asse della valle, pendio, piazza del villaggio.
È un'ipotesi da verificare caso per caso.

## Tabella completa

Azimut da Nord in senso orario. "Abside" = direzione verso cui guarda il coro.
"Facciata" = normale uscente dell'ingresso (abside + 180°).

| Comune | Edificio | tipo OSM | L×W (m) | Abside | Facciata | Affidabilità | Verifica | OSM |
|---|---|---|---|---|---|---|---|---|
| Barcelonnette | Église Saint-Pierre-ès-liens | church | 45.9×26.4 | **352° N** | 172° | alta | non determinabile da ortofoto | [way/128064002](https://www.openstreetmap.org/way/128064002) |
| Barcelonnette | Chapelle Saint-Jacques et Saint-Philippe | chapel | 7.0×3.9 | **341° NNW** | 161° | asse sì, verso incerto | non determinabile da ortofoto | [way/128062231](https://www.openstreetmap.org/way/128062231) |
| Enchastrayes | Église Notre-Dame-des-Neiges | church | 18.7×11.1 | **340° NNW** | 160° | alta | non determinabile da ortofoto | [way/195326268](https://www.openstreetmap.org/way/195326268) |
| Enchastrayes | Église Saint-Pierre-et-Saint-Paul | church | 19.6×12.8 | **244° WSW** | 64° | pianta OSM dubbia | pianta OSM parziale/sfasata rispetto all'edificio | [way/195328613](https://www.openstreetmap.org/way/195328613) |
| Enchastrayes | Chapelle Saint-Jean | yes | 9.2×7.6 | **224° SW** | 44° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/600812181](https://www.openstreetmap.org/way/600812181) |
| Faucon-de-Barcelonnette | Chapelle Saint-Jean-de-Matha | church | 17.8×17.0 | **89° E** | 269° | pianta OSM dubbia | pianta OSM che comprende più edifici | [way/72862068](https://www.openstreetmap.org/way/72862068) |
| Faucon-de-Barcelonnette | Église Saint-Étienne | church | 27.0×16.3 | **82° E** | 262° | alta | non determinabile da ortofoto | [way/72861887](https://www.openstreetmap.org/way/72861887) |
| Faucon-de-Barcelonnette | (senza nome in OSM) | yes | 20.3×7.9 | **90° E** | 270° | alta | non determinabile da ortofoto | [way/72862315](https://www.openstreetmap.org/way/72862315) |
| Jausiers | Église Notre-Dame-del-Bosc | church | 30.1×13.4 | **69° ENE** | 249° | alta | non determinabile da ortofoto | [way/93927303](https://www.openstreetmap.org/way/93927303) |
| Jausiers | Église Saint-Nicolas-de-Myre | church | 37.5×20.9 | **336° NNW** | 156° | verificata | confermato (planimetria catastale del programma: 340°) | [way/93932532](https://www.openstreetmap.org/way/93932532) |
| Jausiers | Église Saint-Sébastien | church | 24.6×15.0 | **336° NNW** | 156° | verificata | confermato: abside semicircolare a NNW | [way/93928811](https://www.openstreetmap.org/way/93928811) |
| Jausiers | (senza nome in OSM) | chapel | 19.0×8.5 | **169° S** | 349° | verificata | confermato: abside semicircolare a S | [way/93927366](https://www.openstreetmap.org/way/93927366) |
| Jausiers | (senza nome in OSM) | chapel | 14.9×7.9 | **149° SSE** | 329° | alta | non determinabile da ortofoto | [way/93929250](https://www.openstreetmap.org/way/93929250) |
| Jausiers | (senza nome in OSM) | yes | 5.4×5.1 | **327° NNW** | 147° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/93929830](https://www.openstreetmap.org/way/93929830) |
| La Condamine-Châtelard | Église Saint-Clément | church | 18.6×13.5 | **0° N** | 180° | verificata | confermato: abside arrotondata a N | [way/128081857](https://www.openstreetmap.org/way/128081857) |
| La Condamine-Châtelard | Église Sainte-Catherine | church | 25.0×12.6 | **15° NNE** | 195° | alta | non determinabile da ortofoto | [way/290959205](https://www.openstreetmap.org/way/290959205) |
| La Condamine-Châtelard | Chapelle Saint-Baptiste | chapel | 8.0×5.2 | **268° W** | 88° | asse sì, verso incerto | non determinabile da ortofoto | [way/128082218](https://www.openstreetmap.org/way/128082218) |
| La Condamine-Châtelard | Chapelle Saint-Roch | chapel | 6.2×5.3 | **275° W** | 95° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128082035](https://www.openstreetmap.org/way/128082035) |
| La Condamine-Châtelard | Chapelle Sainte-Anne | chapel | 7.4×5.9 | **57° ENE** | 237° | asse sì, verso incerto | non determinabile da ortofoto | [way/162367074](https://www.openstreetmap.org/way/162367074) |
| La Condamine-Châtelard | Chapelle des Pénitents Blancs | chapel | 11.2×6.6 | **112° ESE** | 292° | verificata | confermato: abside arrotondata a ESE | [way/128081813](https://www.openstreetmap.org/way/128081813) |
| Le Lauzet-Ubaye | Église Saint-Laurent | church | 28.8×18.2 | **62° ENE** | 242° | alta | non determinabile da ortofoto | [way/128071277](https://www.openstreetmap.org/way/128071277) |
| Le Lauzet-Ubaye | Chapelle Sainte-Anne | chapel | 6.7×4.9 | **126° SE** | 306° | asse sì, verso incerto | non determinabile da ortofoto | [way/128071366](https://www.openstreetmap.org/way/128071366) |
| Le Lauzet-Ubaye | Chapelle de Costeplane | chapel | 6.1×5.9 | **307° NW** | 127° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128071854](https://www.openstreetmap.org/way/128071854) |
| Le Lauzet-Ubaye | (senza nome in OSM) | chapel | 7.0×5.7 | **98° E** | 278° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128071888](https://www.openstreetmap.org/way/128071888) |
| Les Thuiles | Église Saint-Martin de Tours | church | 22.3×14.6 | **271° W** | 91° | alta | non determinabile da ortofoto | [way/128068584](https://www.openstreetmap.org/way/128068584) |
| Les Thuiles | Chapelle Saint-Jean | chapel | 15.7×7.0 | **217° SW** | 37° | asse sì, verso incerto | non determinabile da ortofoto | [way/128069346](https://www.openstreetmap.org/way/128069346) |
| Les Thuiles | Chapelle Saint-Joseph | chapel | 19.6×9.8 | **273° W** | 93° | alta | non determinabile da ortofoto | [way/128069036](https://www.openstreetmap.org/way/128069036) |
| Les Thuiles | Chapelle ouverte des Guérins | yes | 6.8×5.7 | **272° W** | 92° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128069160](https://www.openstreetmap.org/way/128069160) |
| Les Thuiles | (senza nome in OSM) | yes | 21.8×8.6 | **117° ESE** | 297° | asse sì, verso incerto | non determinabile da ortofoto | [way/128069132](https://www.openstreetmap.org/way/128069132) |
| Méolans-Revel | Chapelle Saint-Jean | church | 7.5×6.6 | **49° NE** | 229° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/127740366](https://www.openstreetmap.org/way/127740366) |
| Méolans-Revel | Église Notre-Dame de Lumière | church | 29.9×11.2 | **272° W** | 92° | alta | non determinabile da ortofoto | [way/127740254](https://www.openstreetmap.org/way/127740254) |
| Méolans-Revel | Église Saint-Antoine | church | 18.0×13.5 | **82° E** | 262° | verificata | confermato dalle fonti: Il campanile sta accanto alla facciata ovest: abside a est, come la misura (82°). | [way/127740201](https://www.openstreetmap.org/way/127740201) |
| Méolans-Revel | Église Saint-Jaques-le-Majeur | church | 26.6×15.1 | **52° NE** | 232° | alta | non determinabile da ortofoto | [way/127740276](https://www.openstreetmap.org/way/127740276) |
| Méolans-Revel | Église Saint-Julien | church | 17.5×14.7 | **318° NW** | 138° | verificata | CORRETTO (calcolo automatico 138°): abside semicircolare a NW | [way/127740306](https://www.openstreetmap.org/way/127740306) |
| Méolans-Revel | Église Saint-Julien | church | 21.2×13.6 | **250° WSW** | 70° | alta | non determinabile da ortofoto | [way/127740308](https://www.openstreetmap.org/way/127740308) |
| Méolans-Revel | Chapelle | yes | 4.6×3.8 | **358° N** | 178° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/1409518781](https://www.openstreetmap.org/way/1409518781) |
| Méolans-Revel | Chapelle Notre-Dame de la Salette | chapel | 8.6×4.9 | **82° E** | 262° | verificata | CORRETTO DA FONTI (calcolo automatico 262°): Il campanile a vela sopra la facciata ovest indica l'abside a est. Il calcolo automatico dava il verso opposto (262°): orientamento corretto a 82°. | [way/127741573](https://www.openstreetmap.org/way/127741573) |
| Méolans-Revel | Chapelle Saint-Antoine et Saint-Roch | chapel | 6.1×4.0 | **246° WSW** | 66° | asse sì, verso incerto | non determinabile da ortofoto | [way/127741231](https://www.openstreetmap.org/way/127741231) |
| Méolans-Revel | Chapelle des Trons | yes | 9.0×6.1 | **347° NNW** | 167° | asse sì, verso incerto | non determinabile da ortofoto | [way/127741555](https://www.openstreetmap.org/way/127741555) |
| Méolans-Revel | (senza nome in OSM) | yes | 11.9×6.0 | **26° NNE** | 206° | asse sì, verso incerto | non determinabile da ortofoto | [way/127740889](https://www.openstreetmap.org/way/127740889) |
| Pontis | Église Saint-Claude | church | 14.0×12.3 | **134° SE** | 314° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/197385437](https://www.openstreetmap.org/way/197385437) |
| Pontis | Chapelle Saint-Martin | chapel | 8.2×5.4 | **99° E** | 279° | asse sì, verso incerto | non determinabile da ortofoto | [way/197385465](https://www.openstreetmap.org/way/197385465) |
| Pontis | Chapelle Saint-Pierre | chapel | 6.6×5.6 | **1° N** | 181° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/1038844287](https://www.openstreetmap.org/way/1038844287) |
| Pontis | Église Saint-Jérôme | yes | 25.4×11.7 | **0° N** | 180° | alta | non determinabile da ortofoto | [way/197385428](https://www.openstreetmap.org/way/197385428) |
| Saint-Paul-sur-Ubaye | Église Saint-Antoine-du-Désert de Maurin | church | 22.2×15.8 | **272° W** | 92° | alta | non determinabile da ortofoto | [way/128086950](https://www.openstreetmap.org/way/128086950) |
| Saint-Paul-sur-Ubaye | Église Saint-Sébastien | church | 18.6×9.5 | **96° E** | 276° | alta | non determinabile da ortofoto | [way/128090511](https://www.openstreetmap.org/way/128090511) |
| Saint-Paul-sur-Ubaye | Église Saint-Thomas | church | 18.4×13.4 | **291° WNW** | 111° | alta | non determinabile da ortofoto | [way/128090494](https://www.openstreetmap.org/way/128090494) |
| Saint-Paul-sur-Ubaye | (senza nome in OSM) | church | 16.4×16.1 | **141° SE** | 321° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128091115](https://www.openstreetmap.org/way/128091115) |
| Saint-Paul-sur-Ubaye | Chapelle Notre-Dame-des-Sept-Douleurs | chapel | 8.1×4.4 | **349° N** | 169° | asse sì, verso incerto | non determinabile da ortofoto | [way/128090724](https://www.openstreetmap.org/way/128090724) |
| Saint-Paul-sur-Ubaye | Chapelle Saint-Antoine | chapel | 6.4×4.6 | **314° NW** | 134° | asse sì, verso incerto | non determinabile da ortofoto | [way/401080144](https://www.openstreetmap.org/way/401080144) |
| Saint-Paul-sur-Ubaye | Chapelle Saint-Jacques | chapel | 5.1×4.8 | **203° SSW** | 23° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128091064](https://www.openstreetmap.org/way/128091064) |
| Saint-Paul-sur-Ubaye | Chapelle Saint-Jean-Baptiste | yes | 17.9×12.4 | **63° ENE** | 243° | alta | non determinabile da ortofoto | [way/128090492](https://www.openstreetmap.org/way/128090492) |
| Saint-Paul-sur-Ubaye | Chapelle Saint-Jean-Baptiste | chapel | 17.8×6.8 | **98° E** | 278° | alta | non determinabile da ortofoto | [way/128091102](https://www.openstreetmap.org/way/128091102) |
| Saint-Paul-sur-Ubaye | Chapelle Saint-Roch | chapel | 16.6×8.3 | **46° NE** | 226° | asse sì, verso incerto | non determinabile da ortofoto | [way/128090944](https://www.openstreetmap.org/way/128090944) |
| Saint-Paul-sur-Ubaye | Chapelle Sainte-Marie-Madeleine | chapel | 7.5×4.7 | **310° NW** | 130° | verificata | CORRETTO (calcolo automatico 130°): testata arrotondata a NW | [way/128090685](https://www.openstreetmap.org/way/128090685) |
| Saint-Paul-sur-Ubaye | Notre-Dame-de-l'Annonciation | chapel | 10.2×5.6 | **136° SE** | 316° | asse sì, verso incerto | non determinabile da ortofoto | [way/1203781998](https://www.openstreetmap.org/way/1203781998) |
| Saint-Paul-sur-Ubaye | Église Saints-Pierre-et-Paul | yes | 30.3×17.2 | **63° ENE** | 243° | verificata | confermato dalle fonti: Portale occidentale e coro opposto: l'abside a ENE (63°) è coerente con le fonti. | [way/128090543](https://www.openstreetmap.org/way/128090543) |
| Saint-Pons | Église Saint-Pons | church | 33.0×17.5 | **103° ESE** | 283° | verificata | CORRETTO DA FONTI (calcolo automatico 283°): Chevet piatto e cieco, coro illuminato solo da sud, portale principale a ovest: l'abside guarda a est. Il calcolo automatico dava il verso opposto (283°): orientamento corretto a 103°. | [way/128066982](https://www.openstreetmap.org/way/128066982) |
| Saint-Pons | (senza nome in OSM) | yes | 6.0×4.9 | **279° W** | 99° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128067661](https://www.openstreetmap.org/way/128067661) |
| Ubaye-Serre-Ponçon | Église Notre-Dame-de-l'Assomption | church | 15.8×12.0 | **1° N** | 181° | asse sì, verso incerto | non determinabile da ortofoto | [way/128051016](https://www.openstreetmap.org/way/128051016) |
| Ubaye-Serre-Ponçon | Église Saint-Pierre | church | 25.3×17.0 | **96° E** | 276° | verificata | confermato: abside semicircolare a E | [way/116097551](https://www.openstreetmap.org/way/116097551) |
| Ubaye-Serre-Ponçon | Église Saint-Vincent | church | 24.4×16.1 | **284° WNW** | 104° | asse sì, verso incerto | non determinabile da ortofoto | [way/128051204](https://www.openstreetmap.org/way/128051204) |
| Ubaye-Serre-Ponçon | Église de Costebelle | church | 18.7×16.1 | **142° SE** | 322° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/116084655](https://www.openstreetmap.org/way/116084655) |
| Ubaye-Serre-Ponçon | Chapelle Saint-Antoine | chapel | 8.0×6.1 | **218° SW** | 38° | asse sì, verso incerto | non determinabile da ortofoto | [way/128050703](https://www.openstreetmap.org/way/128050703) |
| Ubaye-Serre-Ponçon | (senza nome in OSM) | chapel | 9.3×6.5 | **19° NNE** | 199° | pianta OSM dubbia | nessun edificio visibile in ortofoto: pianta OSM da verificare | [way/128050603](https://www.openstreetmap.org/way/128050603) |
| Uvernet-Fours | Église Saint-André | church | 22.1×9.8 | **159° SSE** | 339° | alta | non determinabile da ortofoto | [way/128074117](https://www.openstreetmap.org/way/128074117) |
| Uvernet-Fours | Chapelle Saint-François d'Assise | chapel | 21.4×20.0 | **43° NE** | 223° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/128075398](https://www.openstreetmap.org/way/128075398) |
| Uvernet-Fours | Saint-Jean des Agneliers | yes | 17.3×9.9 | **83° E** | 263° | asse sì, verso incerto | non determinabile da ortofoto | [way/128075448](https://www.openstreetmap.org/way/128075448) |
| Val d'Oronaye | Chapelle Sainte-Marie-Madeleine | church | 12.0×10.2 | **278° W** | 98° | verificata | CORRETTO (calcolo automatico 98°): testata poligonale a W | [way/96741859](https://www.openstreetmap.org/way/96741859) |
| Val d'Oronaye | Église Notre-Dame-du-Mont-Carmel | church | 19.4×14.3 | **129° SE** | 309° | alta | non determinabile da ortofoto | [way/96741697](https://www.openstreetmap.org/way/96741697) |
| Val d'Oronaye | Église Saint-Donat | church | 20.2×19.5 | **57° ENE** | 237° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/96992129](https://www.openstreetmap.org/way/96992129) |
| Val d'Oronaye | Chapelle Saint-Ours | chapel | 6.7×4.0 | **43° NE** | 223° | asse sì, verso incerto | non determinabile da ortofoto | [way/96992202](https://www.openstreetmap.org/way/96992202) |
| Val d'Oronaye | Chapelle de la Madeleine |  | 4.3×3.6 | **224° SW** | 44° | bassa (pianta quasi quadrata) | non determinabile da ortofoto | [way/96741723](https://www.openstreetmap.org/way/96741723) |
| Val d'Oronaye | Chapelle du Lauzanier, Notre-Dame des Lumières | chapel | 5.6×3.9 | **170° S** | 350° | asse sì, verso incerto | non determinabile da ortofoto | [way/96741728](https://www.openstreetmap.org/way/96741728) |
| Val d'Oronaye | (senza nome in OSM) | yes | 15.3×10.6 | **252° WSW** | 72° | alta | non determinabile da ortofoto | [way/96992035](https://www.openstreetmap.org/way/96992035) |

## Limiti

- Il risultato dipende da quanto è stato tracciato bene l'edificio in
  OSM. Alcune piante includono campanile, sacrestia o case addossate
  (per esempio Barcelonnette Saint-Pierre, 46×26 m), e questo può
  spostare l'asse di qualche grado o falsare il verso.
- Il verso automatico sbaglia se il campanile o un portico allargano
  il lato del coro. Va controllato a vista soprattutto per le righe
  "verso incerto" e "bassa".
- Restano fuori le chiese non mappate in OSM e le cappelle registrate
  solo come punto, senza pianta.
- Prossimo passo consigliato: per le righe "non determinabile da
  ortofoto" serve la planimetria catastale (cadastre.gouv.fr), come
  già fatto per Jausiers, oppure le schede POP/Mérimée e foto da terra.
