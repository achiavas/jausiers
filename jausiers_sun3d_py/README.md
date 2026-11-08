# Jausiers — visualizzatore 3D interattivo (Python / PyVista)

Applicazione Python standalone (nessun HTML/JS) che mostra un modello
3D **solido** (volumetrico: mura con spessore reale, tetto, pavimento,
vetrate incassate) della chiesa Saint-Nicolas-de-Myre di Jausiers, con
la proiezione solare calcolata in tempo reale.

## Aggiornamento dell'08/11/2026 — pannello "Storia e fonti" (tasto H)

Nel visualizzatore 3D il tasto **H** mostra o nasconde, in alto a
sinistra della vista 3D, un pannello con la storia di Saint-Nicolas-de-Myre:
epoca (completata verso il 1670, consacrata nel 1686), tutela
(monumento storico dal 1921, Mérimée PA00080407), orientamento del
modello, descrizione e fonti (Wikipedia fr, Mérimée, OpenStreetMap,
planimetria catastale del programma). Il pannello è nascosto all'avvio.

Il testo è generato da `storia_chiesa.py`, che legge la scheda da
`ricerca_orientamento_ubaye/storia_fonti.py`: è la stessa scheda usata
dalla cartina delle chiese dell'Ubaye, quindi una correzione va fatta in
un posto solo. Il pannello riporta anche una discordanza: Wikipedia parla
di «facciata occidentale», mentre planimetria catastale (160°), pianta OSM
(156°) e ortofoto danno una facciata rivolta a SSE.
Anteprima: `ricerca_orientamento_ubaye/viewer_pannello_storia.png`.

## Aggiornamento del 28/08 (parte 4) — TROVATO IL VERO BUG: verso di avvolgimento invertito nel ventaglio del tetto

L'utente ha insistito, correttamente, che il varco era "sempre lì fin
dall'inizio dei calcoli", non dipendeva dalle foto, e corrispondeva a
"due parti" larghe del tetto - indicazioni preziose che hanno permesso
di trovare finalmente la causa reale, presente fin dal primo
tentativo a padiglione.

**Diagnosi**: calcolato l'angolo di ciascun punto del contorno
dell'abside (bocca + pentagono) rispetto al centroide usato per il
ventaglio - la sequenza di angoli NON era monotona (124°, 130°, poi
giù bruscamente a 80°...), rompendo la condizione "a stella" richiesta
per un ventaglio valido: questo produceva triangoli con verso di
avvolgimento (winding) INCOERENTE rispetto al resto della mesh.
Confermato in modo inequivocabile attivando il backface culling: la
MAGGIOR PARTE del tetto spariva (normali rivolte verso l'interno
invece che verso l'esterno) - visibile in modo intermittente/dipendente
dall'angolo con il rendering normale, spiegando "un buco molto largo,
sempre nello stesso punto".

**Soluzione**: separata la costruzione del tetto in (1) un ventaglio
SOLO sui 6 vertici del vero pentagono (verificato a stella valida,
angoli monotoni) con verso ESPLICITAMENTE invertito rispetto al
tentativo precedente, e (2) due triangoli distinti per le sezioni di
raccordo verso la bocca, con verso scelto per essere coerente.
Verificato con calcolo diretto (prodotto vettoriale) della componente
Z della normale per OGNI singolo triangolo del tetto: tutti e 7
risultano ora positivi (rivolti verso l'alto/esterno), consistenti fra
loro. Corrispondenza numerica esatta fra Python e JavaScript.

## Aggiornamento del 28/08 (parte 3) — pannelli rettangolari veri per le falde 1 e 5 (non più sottili strisce)

L'utente ha confermato (con screenshot a foto disattivate) che il
varco vicino al campanile era ancora visibile: le sottili strisce
verticali di raccordo (10 cm di larghezza) del tentativo precedente
non erano sufficienti a coprire realmente l'area, lasciando visibile
lo sfondo nero attraverso un varco a forma di cuneo. Richiesta
esplicita: "riempi con due tetti rettangolari per i pannelli 1 e 5".

Sostituite le strisce con VERI PANNELLI RETTANGOLARI: ciascuno copre
l'intera falda 1 (o 5) - dalla bocca (con 5 cm di sovrapposizione)
fino al primo/ultimo vertice del pentagono, dal filo del muro
(15.69 m) fino all'altezza del campanile (19.85 m). Verificato
visivamente (abside + campanile isolati): il pannello ora copre
solidamente l'intera zona di raccordo, nessun varco residuo.

## Aggiornamento del 28/08 (parte 2) — corretta la vera causa della fessura: punti duplicati fra muro e tetto

L'utente ha segnalato (con screenshot, evidenziando in blu due
pannelli mancanti) che il tetto continuava a mostrare una fessura,
nonostante il pannello di raccordo con il campanile aggiunto in
precedenza. Verificato con Playwright sulla versione web: si vedeva
davvero attraverso il tetto fino alla foto interna.

Causa reale trovata: muro e tetto erano costruiti come oggetti
PolyData SEPARATI, poi uniti con `merge()`/`mergeParts()` - pur
condividendo la STESSA posizione fisica (il bordo superiore del muro,
a wall_height, e il bordo del ventaglio del tetto), erano DUE punti
distinti calcolati attraverso percorsi di codice diversi. Con
rendering OPACO la differenza non si notava, ma con la trasparenza
reale usata dall'app (opacita' 0.4) minuscole discrepanze di virgola
mobile fra i due calcoli lasciavano una fessura visibile.

**Soluzione definitiva**: riscritta la funzione per costruire
l'INTERA struttura (muro + tetto + pannelli di raccordo con il
campanile) come UN UNICO PolyData con un solo array di punti
condiviso - nessun merge(). Verificato con `extract_feature_edges`:
19 bordi di confine residui (tutti architettonicamente attesi).
Corrispondenza numerica esatta fra Python e JavaScript (stesso numero
di punti, stesso numero di bordi di confine) - non piu' soggetta a
differenze di deduplicazione come nei tentativi precedenti.

## Aggiornamento del 28/08 — chiusa la fessura fra abside e campanile

L'utente ha segnalato (con screenshot) una fessura scura visibile
vicino al colmo del tetto dell'abside, verso il campanile. Verificato
con `extract_feature_edges` che la mesh dell'abside da sola e'
perfettamente chiusa (solo il bordo atteso della "bocca" verso la
navata) - il problema era quindi alla giunzione fra due strutture
SEPARATE (abside e campanile): l'angolo della bocca dell'abside e' a
filo del bordo del campanile con una tolleranza numerica minima
(TOWER_U_CENTER-TOWER_WIDTH_U/2 = 26.5 contro il vertice absidale a
u=26.52), e c'e' un dislivello fra l'altezza del bordo del tetto
dell'abside (15.69 m) e l'altezza del corpo del campanile (19.85 m).

Aggiunto un pannello di raccordo verticale extra a entrambi gli
angoli della bocca (Ovest, verso il campanile, ed Est per simmetria/
robustezza), leggermente sovrapposto (5 cm) in u e alto fino a
TOWER_BODY_HEIGHT_M - stessa strategia difensiva gia' usata con
successo per il raccordo fra le nicchie delle cappelle e il muro
nucleo: chiude qualunque fessura residua a prescindere dalla causa
geometrica esatta. Verificato visivamente (abside e campanile
isolati, sovrapposizione visibile, nessuna fessura).

## Aggiornamento del 26/08 — tetto abside: PADIGLIONE SIMMETRICO (confermato da foto reale)

L'utente ha fornito una foto REALE della chiesa vista da dietro
("Elevation Nord - chevet"), risolvendo definitivamente l'ambiguita'
delle sole misure della pianta tecnica: il tetto dell'abside e' un
chiaro **padiglione liscio e simmetrico** - le 5 falde convergono in
un unico colmo centrale, come un piccolo cono/ombrello. La struttura
del tentativo precedente (falde 1 e 5 ripide su 2.31 m, poi 2/3/4
piatte) era una lettura sbagliata delle quote della pianta.

Tornata alla costruzione piu' semplice: un ventaglio di triangoli dal
centroide del pentagono (colmo a wall_height+ridge_rise=19.85 m) a
tutti i vertici del contorno (gronda costante a wall_height=15.69 m).
A differenza del tetto rettangolare della NAVATA (dove un ventaglio
da un punto produceva erroneamente una piramide invece di una
capanna, corretto in un turno precedente), per il pentagono
dell'abside il ventaglio da un punto centrale E' la forma corretta:
essendo il pentagono ragionevolmente regolare, i raggi hanno
lunghezze simili e non si crea l'effetto "a raggiera" visto sul
rettangolo. Verificato con `extract_feature_edges` (solo 11 bordi di
confine residui, tutti architettonicamente attesi: pavimento aperto e
bocca verso la navata) e confronto visivo diretto con la foto reale.

## Aggiornamento del 25/08 (parte 9) — corretto il vero bug: il tetto era scollegato dal muro ("non c'era")

L'utente ha segnalato "non c'e' tetto per l'abside" dopo la parte 8.
Verificato con `extract_feature_edges` (bordi di confine): il
tentativo precedente creava tri1/tri5 come piccoli pezzi SEPARATI poi
uniti con `merge()`, che non riusciva a deduplicare correttamente i
punti coincidenti con i pannelli adiacenti - le falde 1 e 5
apparivano come due "punte" completamente scollegate dal resto della
struttura (bordi di confine su ENTRAMBI i lati, invece che solo
quelli attesi).

Trovato anche un secondo problema strutturale, piu' sottile: il
contorno del MURO collegava direttamente pentagono[0] a pentagono[1],
mentre il TETTO (gable + falda1 + corpo centrale) tratta quel tratto
come DUE segmenti separati passanti per il punto intermedio p1 (a
u=L+2.31) - un disallineamento topologico che lasciava un varco anche
dopo aver risolto il primo problema.

**Soluzione definitiva**: riscritta la funzione per costruire
l'INTERA struttura (muro + tetto) come un UNICO PolyData con un solo
array di punti condiviso (nessun merge()), e il contorno del muro
ora include esplicitamente p1 e p5 come vertici, garantendo che muro
e tetto condividano esattamente gli stessi edge. Verificato con
`extract_feature_edges`: i bordi di confine residui sono ora solo
quelli architettonicamente attesi (pavimento aperto, bocca aperta
verso la navata, bordi esterni "a gronda" dei due triangoli 1/5, che
non devono collegarsi a nient'altro). La forma stretta e ripida delle
falde 1/5 (base di soli 1.31 m, dislivello di 4.16 m su 2.31 m) e'
confermata essere il risultato geometrico corretto della
specifica dell'utente, non un difetto.

## Aggiornamento del 25/08 (parte 8) — tetto abside a 5 falde (non più falda unica)

L'utente ha specificato con precisione la vera struttura: l'abside è
composta da 5 lati (numerati 1-5 partendo dal campanile). Le falde 1
e 5 (adiacenti alla "bocca") sono TRIANGOLARI e scendono ripidamente
dall'altezza del tetto/muro navata (19,85 m) fino all'altezza base
dell'abside (15,69 m), su una distanza di soli 2,31 m [rosa,
plan3.pdf] - non sull'intera lunghezza del lato pentagonale (5,48 m).
Le falde 2, 3, 4 (corpo centrale) partono da dove finiscono 1 e 5, già
all'altezza base, e restano PIATTE fino alla punta esterna.

Riscritta `build_apse_wall_structure()`: due triangoli (falde 1 e 5)
più un corpo centrale piatto a "zipper" simmetrico (falde 2-3-4),
sostituendo la falda unica continua del tentativo precedente.

**Trovato anche un bug preesistente**: `vertical_band()` chiudeva
sempre il giro completo del contorno, creando un pannello di muro
spurio anche sul lato della "bocca" absidale (dove deve restare
aperta verso la navata) - non correlato al problema del tetto, ma
scoperto durante il debug di un artefatto visivo (due "punte" che
sembravano sporgere dal tetto, poi confermate essere un'illusione
prospettica dovuta alla vista da un'angolazione quasi di taglio sui
triangoli stretti - verificato con vista dall'alto che l'impronta in
pianta è corretta). Aggiunto parametro opzionale `closed` (default
`True`, retrocompatibile) e passato `closed=False` per l'abside.

## Aggiornamento del 25/08 (parte 7) — corretto anche il tetto dell'abside: stesso difetto "a raggiera" del tetto navata

Dopo aver corretto il tetto principale (parte 6), l'utente ha
segnalato che anche il tetto dell'abside andava sistemato. Verificato
visivamente (vista dettagliata sulla giunzione navata/abside): il
tetto dell'abside usava ANCORA un ventaglio da un singolo vertice
(solo con l'ultimo triangolo rimosso, parte 5) - producendo una
struttura "a raggiera" con tutte le linee convergenti verso un unico
angolo, invece del vero piano inclinato liscio ("falda unica")
confermato dall'utente.

Provato prima un approccio con triangolazione vincolata
(`delaunay_2d`), ma la forma allungata del pentagono continuava a
produrre un pattern simile a raggiera (la triangolazione Delaunay
ottimizza la qualita' dei singoli triangoli, non l'assenza di
convergenza). Risolto sfruttando la SIMMETRIA del pentagono rispetto
a v=0: il tetto ora e' costruito come una serie di quadrilateri
("zipper") che collegano il lato Ovest del contorno al lato Est
speculare, creando un vero piano inclinato liscio senza alcun punto
di convergenza. Verificato visivamente (vista ravvicinata sulla
giunzione: linee di piega naturali, nessuna raggiera; vista dall'alto:
copertura pentagonale pulita) e con tutti i test standard.

## Aggiornamento del 25/08 (parte 6) — corretto il VERO tetto principale: era una piramide, non una capanna

L'utente ha fatto notare, giustamente, che i tentativi di correzione
sull'abside non avevano senso se il tetto della NAVATA PRINCIPALE
stesso era sbagliato: "è un tetto rettangolare e non a spiovente".

Trovato: `build_roof()` (usato per la navata) creava un ventaglio di
triangoli da un singolo PUNTO CENTRALE a tutti gli angoli del
rettangolo - questo produce una PIRAMIDE a 4 falde, non un tetto a
CAPANNA (due sole falde rettangolari che si incontrano su un COLMO
LINEARE, con due frontoni triangolari alle estremità facciata/abside)
come mostrato chiaramente in ogni disegno di elevazione e come si
vede nella foto reale della chiesa. Probabilmente questo bug esisteva
gia' da prima (quando il muro navata usava un contorno piu' denso
comprendente le cappelle, il ventaglio approssimava meglio una forma
liscia; dopo la recente semplificazione del contorno a un rettangolo
pulito a 4 punti, il difetto e' diventato visibile: una piramide a 4
spicchi netti).

Riscritta `build_roof()`: ora costruisce esplicitamente 6 punti (4
angoli di gronda + 2 punti di colmo, uno lato facciata e uno lato
abside) e 4 facce (2 falde rettangolari + 2 frontoni triangolari),
invece del ventaglio. Verificato: vista dall'alto mostra le due falde
rettangolari pulite divise esattamente a meta' dal colmo; vista
frontale mostra il classico profilo a capanna con frontone
triangolare, coerente con i disegni. Bounds orizzontali del tetto ora
identici a quelli del muro (nessuno sconfinamento nell'area
absidale). Tutti i test standard ancora OK.

## Aggiornamento del 25/08 (parte 5) — corretto vero bug: tappo piatto spurio nella "bocca" absidale

L'utente ha segnalato "il tetto dell'abside è aperto! va verso
l'alto" e "il muro è troppo alto". Prima di tutto, confermato con
l'utente che il valore del muro (15,69 m, ciano) era corretto -
quindi il problema non era il valore, ma un difetto di rendering.

Trovato: la triangolazione a ventaglio del tetto (da vertice 0)
includeva un ULTIMO triangolo che collegava (L,Wh) - (L,-(Wh-recess))
- (L,-Wh): tre punti che si trovano tutti alla "bocca" absidale
(dove l'abside si apre verso il muro alto della navata, non dove
dovrebbe esserci una superficie di tetto). Questo creava un tappo
piatto spurio all'altezza massima (19,85 m) proprio nel punto che
deve restare aperto/connesso al resto dell'edificio - probabile causa
sia dell'aspetto "tetto aperto verso l'alto" sia dell'impressione di
"muro troppo alto" (la superficie incongrua attraversava l'intera
larghezza della rientranza).

Rimosso l'ultimo triangolo del ventaglio (ora si ferma un'iterazione
prima). Verificato: la mesh ora ha una forma pulita e coerente (fan
roof a falda singola, senza cappe spurie), la bocca risulta aperta
verso la navata. Bounds, chiusura pentagono e tutte le vetrate ancora
OK.

## Aggiornamento del 25/08 (parte 4) — corretto il vero colpevole: il PANNELLO FOTO curvo dell'abside, non la mesh

L'utente ha segnalato ancora una volta "troppo alto" e "non chiude
verso il basso" per l'abside, con uno screenshot annotato. Indagando,
la struttura esterna dell'abside (`apse_structure`, gia' corretta nei
turni precedenti) risultava numericamente corretta - il vero
colpevole era un elemento COMPLETAMENTE DIVERSO: il pannello
fotografico curvo interno dell'abside (`build_curved_apse_panel` in
reference_photos.py, foto "abside_altare_frontale.jpg"), che aveva
DUE bug distinti risalenti a prima che l'abside avesse un'altezza
propria:

1. **"Troppo alto"**: `APSE_PHOTO_HEIGHT_TOP` era calcolato da
   `WALL_HEIGHT_M` (altezza muro NAVATA, 16,56 m) invece
   dell'altezza propria dell'abside (`APSE_EXTERNAL_HEIGHT_M`,
   15,69 m) - risultava a 16,0 m invece di 15,13 m.
2. **"Non chiude verso il basso"**: il pannello copriva solo i 5 lati
   del pentagono absidale (`church.apse_vertices()`), SENZA i due
   tratti di raccordo verso il muro della navata - lasciava un varco
   visibile proprio vicino alla torre, esattamente dove l'utente ha
   indicato con la freccia.

Corretti entrambi: l'altezza ora usa `APSE_EXTERNAL_HEIGHT_M`, e il
contorno del pannello include i due punti di raccordo `(L,Wh)` e
`(L,-Wh)`, esattamente come fa gia' `apse_wall_structure()` per la
mesh solida. Verificato numericamente: bounds orizzontali del
pannello ora IDENTICI a quelli di `apse_structure` (prima erano
diversi, confermando il varco), altezza ridotta da 16,0 a 15,13 m.

## Aggiornamento del 25/08 (parte 3) — affinamento finale altezza tetto abside

L'utente ha fornito una derivazione precisa e diretta: il punto alto
del tetto dell'abside (dove incontra il muro alto della navata) e'
3,53 m piu' basso del colmo del tetto della navata principale
(23,38 m dalla figura) = 19,85 m esatti. Aggiornato
APSE_ROOF_RIDGE_RISE_M da 4,15 a 4,16 m (= 19,85-15,69), coerente
entro 1 cm con la stima precedente. Rimossa anche la costante
APSE_ROOF_FLAT_RIDGE_M, residuo inutilizzato dalla precedente forma a
padiglione (sostituita dalla falda unica nel turno precedente).
Verificato: bounds esatti (0-19,85 m), corrispondenza numerica exacta
Python/JavaScript, tutti i test standard OK.

## Aggiornamento del 25/08 (parte 2) — corretti tre bug critici dei tasti (solo versione Python)

L'utente ha segnalato tre problemi concreti con i comandi da
tastiera, tutti confermati e risolti:

1. **Spazio avvia l'animazione ma non la ferma mai**: bug reale nel
   codice - `_toggle_play()` creava un timer all'avvio ma non lo
   distruggeva mai alla fermata (mancava la chiamata a
   `destroy_timer()`). Corretto.
2. **"E" (Est) chiude il programma**: NON era un bug di questa
   applicazione, ma una collisione con una scorciatoia RISERVATA di
   VTK/PyVista - "e" è il tasto di uscita di default dell'interactor
   (confermato con test mirati: la rappresentazione grafica e la
   "vita" dell'app cambiano in risposta al tasto anche PRIMA che il
   mio codice venga eseguito, a livello di CharEvent gestito in C++,
   non rimovibile in modo affidabile da Python).
3. **"W" (Ovest) rende tutto trasparente**: stessa causa - "w" è la
   scorciatoia riservata di VTK per la modalità wireframe.
4. **Trovato anche un quarto problema non segnalato ma verificato**:
   "3" (21 giugno) attiva il rendering STEREO di VTK (da 0 a 1),
   spiegando l'effetto "tutto viola" - stessa causa (scorciatoia
   riservata).

**Soluzione**: dato che le scorciatoie riservate di VTK sono gestite
a livello di classe base C++ (non tramite observer rimovibili da
Python - verificato con più tentativi, inclusi `RemoveObservers` e
monkey-patching, entrambi inefficaci), i tasti in conflitto sono
stati sostituiti con alternative testate empiricamente una per una
(nessun cambiamento di rappresentazione grafica, nessuna uscita
dall'app, nessuna attivazione dello stereo):

- Est: `E` → `K`
- Ovest: `W` → `O`
- 21 giugno: `3` → `4`

Gli hint a schermo sono stati aggiornati di conseguenza. Verificato
che l'app resti viva e funzionante anche se l'utente preme per
abitudine i vecchi tasti (non più collegati a nessuna funzione, ma
non più pericolosi). **La versione web (JavaScript) non è affetta da
nessuno di questi problemi**: usa i normali eventi `keydown` del
browser, completamente indipendenti dal sistema di scorciatoie di
VTK, e il suo `togglePlay()` già chiamava correttamente
`clearInterval()` alla fermata - nessuna modifica necessaria li'.

## Aggiornamento del 25/08 — tetto abside a FALDA UNICA (non più a padiglione)

L'utente ha confermato (dopo un confronto diretto con "Elevation Est"
e con uno screenshot del modello lato Ovest) che il tetto dell'abside
non e' un padiglione simmetrico con colmo centrale, ma una **falda
unica inclinata**: alta dove l'abside incontra la navata/muro alto,
bassa verso la punta esterna del pentagono - come una semplice
prosecuzione della pendenza, non una struttura autonoma a padiglione.

Riscritta `build_apse_wall_structure()`:
- Muro: altezza COSTANTE (15,69 m) intorno a tutto il pentagono
  (invariato)
- Tetto: un'unica superficie piana inclinata, altezza interpolata
  linearmente in base alla sola coordinata u (distanza dalla navata) -
  da 15,69 m alla punta esterna (u massimo del pentagono) a 19,84 m
  dove incontra il muro alto della navata (u=L)

Rimossa la costante APSE_ROOF_FLAT_RIDGE_M (colmo piatto, 2,31 m) -
non piu' applicabile a questa forma. Verificato: bounds corretti
(z da 0 a 19,84 m), corrispondenza numerica esatta fra Python e
JavaScript, chiusura pentagono e tutte le 17 vetrate ancora OK.

## Aggiornamento del 24/08 (parte 10) — riempimenti fino al tetto e trasparenti, luce non piu' segmentata

Due correzioni su richiesta dell'utente:

1. **Riempimenti fra le cappelle**: ora arrivano fino al VERO tetto
   della cappella (profilo inclinato, da 9,64 m sul filo esterno a
   10,95 m sul filo interno - non piu' un tappo piatto alla gronda) e
   sono TRASPARENTI come i muri della chiesa (opacita' 0,28, era 0,9).
2. **Proiezione della luce segmentata/discontinua nelle cappelle e
   nell'abside**: causa trovata in `wall_projection.py` - la funzione
   che calcola dove un raggio di sole colpisce una parete usava
   un'unica altezza uniforme (WALL_HEIGHT_M=16,56 m) per TUTTO il
   perimetro, ma le nicchie delle cappelle e l'abside hanno altezze
   reali molto diverse (9,64-10,95 m per le nicchie, ~19,84 m per
   l'abside). Una vetrata di cleristorio (11-13 m, sopra il vero
   tetto della nicchia) veniva quindi erroneamente "fermata" da un
   muro che a quell'altezza non esiste piu' nella nicchia, spezzando
   la macchia di luce. Aggiunta `_wall_height_at_point()`: altezza
   REALE per ciascun punto del perimetro, in base alla zona (nucleo
   navata, nicchia cappella con profilo inclinato, abside) - usata
   ora per interpolare l'altezza locale di ciascun segmento di parete
   invece del valore uniforme. Verificato con sweep esteso (2176
   combinazioni, zero errori) e vista interna con luce radente.

## Aggiornamento del 24/08 (parte 9) — riempimenti fra le cappelle SPORGENTI (non più sul filo muro)

L'utente ha finalmente chiarito il problema con precisione, usando la
mia stessa immagine di verifica con colore distintivo: NON era un
varco/buco nella mesh (verificato piu' volte come assente), ma una
RIENTRANZA visibile dall'esterno. Il muro nucleo, corretto ma
arretrato rispetto alle cappelle sporgenti (che proiettano
CHAPEL_PROJECTION_DEPTH_M=2.19 m in avanti), appariva come un incavo
fra una cappella e l'altra quando osservato dall'esterno - anche se
"riempito" (fasce/pilastri dei tentativi precedenti restavano
comunque sul filo del muro, v=Wh, non sporgenti).

Corretto: `build_chapel_piers()` ora costruisce dei RIEMPIMENTI SOLIDI
(non piu' fasce piatte) che sporgono alla STESSA profondita' delle
nicchie (da v=Wh a v=Wh+2.19 m), in tutti i tratti fra una cappella e
la successiva (e prima della prima/dopo l'ultima, verso la
rientranza absidale - 5 tratti per lato). Il risultato: l'intero
fianco della chiesa appare come un unico volume sporgente continuo,
con le sole vetrate ad arco delle cappelle a distinguersi in cima,
invece di alternare cappelle sporgenti e tratti rientrati. Verificato
visivamente con colori distintivi: riempimenti (verde) e nicchie
(rosso) sporgono ora esattamente alla stessa profondita', senza
soluzione di continuita'.

## Aggiornamento del 24/08 (parte 8) — fascia solida continua su tutta la lunghezza (non solo fra le cappelle)

L'utente ha confermato che il varco era ANCORA visibile dopo
l'aggiunta dei pilastri (limitati ai soli tratti fra una nicchia e la
successiva). Verificato che il file plan3.pdf fosse effettivamente
quello corrente (stesso hash MD5 di prima - non era un problema di
cache) e che le frecce grigie "Varchi che devono essere riempiti" non
portassero nuove quote numeriche applicabili (sono un'indicazione
visiva, non una misura). Individuato anche, per completezza, che nero
(7,85 m) e blu (3,53 m) si riferiscono al raccordo di tetto fra
navata e abside vicino al campanile, non alle cappelle laterali - non
rilevanti per questo problema.

Sostituita la fascia "a pilastri" (solo negli spazi vuoti) con una
fascia SOLIDA CONTINUA su TUTTA la lunghezza della navata (sia dove
ci sono le nicchie sia dove non ci sono), volutamente ridondante con
le nicchie stesse: elimina ogni possibilita' di varco per
costruzione, qualunque fosse la causa esatta del problema visivo
originale. Verificato visivamente con colore distintivo: la fascia
(verde) risulta continua su tutta la lunghezza di entrambi i lati,
senza interruzioni.

## Aggiornamento del 24/08 (parte 7) — tetto abside a padiglione, pilastri solidi fra le cappelle

L'utente ha inviato uno screenshot chiaro con frecce che indicano
esattamente i due problemi residui:

1. **Tetto abside sbagliato/troppo alto**: era una piramide a punta
   singola, che appare visivamente troppo alta e appuntita su una
   base pentagonale larga anche con l'altezza numerica corretta.
   Sostituita con un vero tetto a padiglione: due punti di colmo
   separati da 2,31 m [magenta, APSE_ROOF_FLAT_RIDGE_M - non ancora
   usato in precedenza], orientati lungo l'asse navata e centrati sul
   pentagono, con raccordo esplicito per evitare varchi nella mesh del
   tetto stesso.
2. **Varchi fra le cappelle ancora visibili**: nonostante i test
   isolati confermassero il muro nucleo geometricamente continuo,
   l'utente confermava il problema persistente da una vista esterna
   reale. Aggiunta una struttura DEDICATA e molto piu' opaca (0,9
   invece di 0,28) - pilastri solidi esattamente nello spazio fra ogni
   coppia di nicchie adiacenti, dal pavimento all'altezza di gronda
   (9,64 m) - che garantisce una lettura visiva di muratura piena a
   prescindere dal meccanismo esatto di trasparenza multipla che
   causava l'aspetto di varco.

Verificato visivamente con colori distintivi (i pilastri riempiono
esattamente lo spazio indicato dalle frecce dell'utente) e
numericamente (distanza fra i due punti di colmo = 2,31 m esatti).

## Aggiornamento del 24/08 (parte 6) — sovrapposizione difensiva nicchie/muro nucleo

L'utente ha segnalato che il varco fra le cappelle era ancora visibile
nonostante la correzione precedente (rimozione dei pannelli di
collegamento ridondanti). Il muro nucleo, isolato con colori
distintivi, risultava geometricamente continuo senza varchi - quindi
la causa esatta del varco visibile a schermo (probabilmente legato ai
pannelli fotografici sovrapposti, che iniziano a 0,5 m da terra
lasciando visibile la geometria grezza sotto, o a un effetto di
z-fighting non riprodotto nei miei test isolati) resta non confermata
con certezza al 100%.

Applicata comunque una correzione DIFENSIVA e robusta: il muro di
"ritorno" di ciascuna delle 8 nicchie ora si estende 5 cm OLTRE il
filo del muro nucleo (nella stessa direzione dello spessore del muro,
non solo a toccarne il bordo), garantendo una vera sovrapposizione
geometrica invece di una semplice coincidenza di piani - elimina
qualsiasi possibile causa di z-fighting indipendentemente
dall'esatto meccanismo. Verificato che tutto si costruisca
correttamente e che i test geometrici standard continuino a passare.

**Nuove quote trovate su una versione aggiornata di "Elevation Est"**
(blu 3,53 m, nero 7,85 m, quest'ultimo su un tratto diagonale) - non
ancora pienamente interpretate/applicate al modello absidale: la
richiesta di "rileggere tutte le misure per l'esterno" dell'abside
resta parzialmente inevasa, per evitare di introdurre un'altra
correzione probabilmente errata senza una lettura più sicura.

## Aggiornamento del 24/08 (parte 5) — nuovo controllo per mostrare/nascondere le vetrate

Aggiunto un secondo controllo (checkbox + tasto `V`), analogo a quello
già esistente per le foto ("Mostra foto"): "Mostra vetrate" nasconde/
mostra le mesh piene delle 17 vetrate (cappelle, abside, facciata),
indipendentemente dalle foto sovrapposte e dalle macchie di luce.
Utile per ispezionare la struttura dell'edificio senza gli inserti
colorati delle vetrate. Verificata anche l'assenza di ogni varco
residuo fra le nicchie delle cappelle (vedi parte 4) con colori
distintivi: il muro nucleo copre con continuità tutto lo spazio.

## Aggiornamento del 24/08 (parte 4) — risolto varco visivo fra le cappelle (bug di z-fighting)

L'utente ha segnalato dei varchi visibili fra le 4 cappelle laterali
(su entrambi i lati) in una schermata dell'app web. Diagnosticato:
NON era un'assenza di geometria - il muro "nucleo" della navata
copriva gia' con continuita' tutto lo spazio fra una nicchia e
l'altra, verificato rimuovendo del tutto le nicchie e controllando
che il muro da solo risultasse perfettamente continuo (nessun varco).

La vera causa: i "pannelli di collegamento" aggiunti in una sessione
precedente (per riempire quello che sembrava un vuoto) erano posti
esattamente nello STESSO PIANO del muro nucleo (v=Wh) - due superfici
perfettamente coincidenti causano z-fighting, che a certi angoli di
vista faceva sparire ENTRAMBE, mostrando un varco. Risolto rimuovendo
del tutto i pannelli di collegamento (ridondanti, dato che il muro
nucleo copre gia' quello spazio da solo). Verificato visivamente con
colori distintivi: nessun varco residuo.

## Aggiornamento del 24/08 (parte 3) — conferma incrociata tetto abside

L'utente ha confermato che il valore verde (4,15 m) indica
specificamente la risalita del tetto dell'abside sopra il muro -
coincide quasi esattamente con il valore calcolato indirettamente
nella correzione precedente (colmo - muro = 19,85 - 15,69 = 4,16 m).
Aggiornato APSE_ROOF_RIDGE_RISE_M a 4,15 m (valore diretto invece di
derivato). Le tre misure indipendenti (arancione=19,85 totale,
ciano=15,69 muro, verde=4,15 tetto) ora si confermano reciprocamente:
15,69+4,15=19,84 ≈ 19,85.

## Aggiornamento del 24/08 (parte 2) — altezza abside corretta (era troppo alta)

Trovato un errore: il valore "arancione" (19,85 m) usato come altezza
del muro esterno dell'abside NON era l'altezza del muro, ma l'altezza
del COLMO del tetto (base -> sommita'). L'altezza vera del muro
(gronda, dove il tetto comincia) e' il valore "ciano" (15,69 m).
Corretto:

- APSE_EXTERNAL_HEIGHT_M: 19,85 -> 15,69 m (altezza muro, ciano)
- APSE_ROOF_RIDGE_RISE_M: 2,51 -> 4,16 m (= colmo - muro =
  19,85 - 15,69, che corrisponde quasi esattamente al valore "verde"
  letto separatamente, 4,15 m - conferma incrociata)

Totale (muro + tetto) resta 19,85 m come prima, ma ora l'abside e'
proporzionata correttamente: il muro (15,69 m) e' appena sotto quello
della navata (16,56 m), invece di superarlo come accadeva con il
valore errato.

**Non ancora modellato**: un piccolo tratto piatto in cima al tetto
(magenta, 2,31 m - probabilmente la lunghezza del breve colmo piatto
anziche' un vero e proprio picco a punta) - il tetto resta una
piramide semplice a punta singola.

## Aggiornamento del 24/08 — foto reale della facciata esterna

Sostituita la vecchia foto interna dell'ingresso
(`navata_centrale_ingresso.jpg`, vista dall'interno verso l'abside)
con una foto reale della facciata ESTERNA (fornita dall'utente, sfondo
gia' rimosso), agganciata all'esterno del muro di facciata invece che
all'interno.

Dimensioni del pannello calcolate dai pixel della foto: le due stime
di scala basate sull'altezza (gronda del muro a 16,56 m e colmo del
tetto a 23,13 m nel modello) concordano fra loro al 2% - piu'
affidabili della larghezza, che risente di una leggera prospettiva
della foto. Il pannello e' quindi leggermente piu' largo (15,93 m) del
muro reale (13,37 m), per garantire la copertura completa richiesta.

**Bug trovato e corretto durante la verifica visiva**: il testo delle
meridiane sulla facciata appariva speculare (specchiato) nella nuova
foto - la convenzione di segno per l'orientamento "minus_u" dei
pannelli fotografici piatti (`_card_corners_local()` in
`reference_photos.py`) era invertita. Corretta e verificata (il testo
"D.O.M." ora si legge correttamente).

## Aggiornamento del 23/08 (parte 5) — muro basso continuo fra le nicchie, abside con altezza propria

Due correzioni:

1. **Pannelli di collegamento fra le nicchie delle cappelle**: prima,
   fra una nicchia e la successiva, il muro esterno "spariva" fino al
   filo del muro alto della navata, lasciando un vuoto visivo al
   livello del tetto basso. Aggiunti pannelli di muro basso (altezza
   costante = bordo interno delle nicchie, 10,95 m) che riempiono lo
   spazio fra le cappelle consecutive, su entrambi i lati.
2. **Abside con altezza esterna propria** (19,85 m, "arancione" su
   Elevation Est, con tetto a padiglione che sale di altri 2,51 m fino
   al colmo, 22,36 m totali) - prima l'abside ereditava la stessa
   altezza della navata (16,56 m). Ora ha una struttura dedicata
   separata (`build_apse_wall_structure()`), analoga a quella gia'
   usata per campanile e cappelle. **Nota**: la mia lettura pixel del
   documento dava 2,31 m per questo valore, non 2,51 m - uso il valore
   indicato dall'utente (accesso diretto al PDF), segnalando la
   piccola discrepanza.

Verificato numericamente (muro navata: 16,56 m; struttura absidale:
22,36 m) e visivamente con colori distintivi.

## Aggiornamento del 23/08 (parte 4) — muro alto tagliato davvero sopra le 8 nicchie

Il tetto basso delle cappelle (parte 2/3) era solo un piano visivo
sovrapposto: il muro alto della navata continuava a salire fino a
16,56 m ANCHE nella zona delle nicchie, "bucando" il tetto basso da
dietro. Corretto costruendo il muro alto solo sul "nucleo"
navata+abside (`ChurchModel.core_outline_local()`, SENZA le nicchie
sporgenti), e le 8 nicchie delle cappelle come strutture separate
(`build_chapel_wall_structures()`) che si fermano davvero all'altezza
del tetto basso (9,64-10,95 m) invece di proseguire fino a
WALL_HEIGHT_M. Verificato numericamente (muro alto: z fino a 16,56 m;
nicchie: z fino a 10,95 m) e visivamente con colori distintivi.

## Aggiornamento del 23/08 (parte 3) — pendenza tetto cappelle misurata

La pendenza del tetto basso delle cappelle (da dove la gronda esterna
incontra il muro alto della navata) era stimata (1,2 m). Individuata
sulla pianta "Elevation Sud" una freccia ciano che indica esattamente
questo punto - il valore misurato e' 1,31 m (arancione). Sostituita la
stima con la quota misurata (CHAPEL_ROOF_PITCH_RISE_M): il tetto basso
ora sale da 9,64 m (gronda) a 10,95 m (dove incontra il muro navata),
invece di 10,84 m stimato.

## Aggiornamento del 23/08 (parte 2) — vetrate cappelle come cleristorio, porta come muro

Due correzioni:

1. **Vetrate delle cappelle spostate sul muro navata** (v=Wh, non più
   sulla parete di fondo della nicchia). Il davanzale (11,18 m) era
   interamente SOPRA la gronda del tetto basso delle cappelle
   (9,64 m, aggiunto nella sessione precedente) - posizionate sulla
   parete della nicchia, le vetrate risultavano tagliate fuori dal
   tetto e apparivano "troppo alte", scollegate dall'architettura. Sul
   muro navata diventano vere finestre di **cleristorio**, visibili
   sopra il tetto basso, coerenti con l'altezza muro (16,55/16,56 m,
   Elevation Sud). Di conseguenza rimosso anche l'arretramento di
   1,31 m (CHAPEL_WINDOW_RECESS_M) introdotto in precedenza: non ha
   più senso fisico in questa posizione (spessore muro solo 0,7 m, non
   i 2,19 m della nicchia) - spingerebbe la vetrata dentro lo spazio
   aperto della navata
2. **Portale trattato come muro**: nuovo gruppo dedicato `"porta"`
   (invece di `"facciata"`), stesso colore/opacità dei muri, **escluso
   dal calcolo della luce solare** (non compare mai nella lista
   vetrate illuminate, la sua opacità non cambia mai)

Verificato: chiusura pentagono ancora esatta, tutte le 17 vetrate
orientate correttamente (distanza di test aumentata a 3 m per tenere
conto della profondità della nicchia davanti alle vetrate cappella),
verifica visiva con colori distintivi che conferma la vetrata emergere
sopra il tetto basso.

## Aggiornamento del 22-23/08 — correzioni geometriche da rilievo diretto, portale, campanile, nartece

A partire da quattro piani ufficiali dell'architetto (Michel Trubert
ACMH, "Diagnostic - Etat des lieux", 09/2016 — pianta 1/200, elevazioni
Sud e Est 1/100), corrette numerose quote prima solo stimate:

- Lunghezza/larghezza navata: 26,52 x 13,37 m (misurate)
- Profondità reale delle nicchie delle cappelle: 2,19 m (era stimata
  0,38 m — correzione enorme). Le vetrate delle cappelle sono state
  riposizionate dalla soglia della nicchia alla vera parete di fondo
- Pentagono absidale: rientranza (1,31 m), lunghezze dei 5 lati e
  larghezza navata ora tutte misurate direttamente; risolta la
  chiusura geometrica esatta del pentagono (sistema lineare 2x2, uno
  scarto di chiusura di 2,72 m usando le misure alla lettera e' stato
  ridotto a <0.05 mm - vedi i commenti in `church_geometry.py` per il
  dettaglio, incluso un adattamento del 42% sul pannello di fondo
  dell'abside da verificare)
- Tutte le 17 vetrate (8 cappelle, 5 abside con una dimensione diversa
  lato campanile, 3 facciata) ridimensionate e riposizionate da quota
  misurata
- Aggiunto il **portale d'ingresso** (3,30 x 4,38 m, modellato come le
  vetrate, senza texture)
- Aggiunto il **campanile** (corpo 19,85 m + guglia 15,69 m = 35,54 m
  totali), lato "Ovest" del modello (adiacente a "Cappella
  Notre-Dame-du-Rosaire") - posizione corretta dall'utente dopo un
  errore di lettura iniziale della pianta
- Aggiunto un **tetto basso separato sopra le cappelle** (gronda a
  9,64 m su entrambi i lati) - la quota era gia' definita in una
  sessione precedente ma non era mai stata usata nella mesh 3D
- Aggiunto il **nartece/vestibolo coperto** sopra il portale:
  struttura solida e opaca (non lascia passare luce), con soffitto a
  profilo curvo che va da 6,58 m (al muro) a 4,49 m (a 2,63 m di
  distanza dal muro), largo 4,38 m

Verificato: chiusura pentagono a precisione di macchina, tutte le 17
vetrate orientate correttamente (test geometrico indipendente), sweep
esteso della proiezione solare (2176 combinazioni, zero errori),
bounding box del nartece esatto (z da 0 a 6,58 m).

**Nota tecnica**: il nartece e' modellato come solido opaco visibile
nella scena 3D, ma il suo effetto di "blocco della luce" non e' stato
integrato nel motore di simulazione (`wall_projection.py`) - le
macchie di luce sul pavimento/pareti sono ancora calcolate come se il
nartece non ci fosse. Da valutare se necessario.

## Aggiornamento del 20/08 (parte 8) — vetrate reali, foto ingresso a filo muro, fix z-fighting

Tre richieste:

1. **Foto d'ingresso attaccata al muro**: spostata da u=2.2 a u=0.18,
   praticamente a filo con la parete della facciata (invece di
   fluttuare a meta' navata).

2. **Vetrate reali sulle 8 finestre delle cappelle**: ritagliate due
   finestre pulite e ben illuminate da `im1.jpg` (lato Ovest) e
   `im2.jpg` (lato Est) — le altre finestre visibili nelle due foto
   erano troppo in ombra o tagliate ai bordi per un ritaglio
   leggibile, quindi la stessa foto per lato viene applicata a tutte
   e 4 le vetrate di quel lato. Nuovo metodo
   `Window.local_outline_with_uv()` in `church_geometry.py`: calcola
   le coordinate texture (u_tex,v_tex) per ciascun punto del vero
   contorno della vetrata (rettangolo + arco), non un rettangolo
   approssimato. La foto e' sagomata esattamente come l'arco reale.

3. **Corretto un problema di sovrapposizione** (z-fighting) trovato
   *durante la verifica visiva*: i grandi pannelli panoramici delle
   pareti laterali (spostati leggermente in avanti, v=Wh-0.1, per non
   sovrapporsi al filo muro dove si disegnano le macchie di luce)
   erano PIU' vicini all'osservatore delle texture delle vetrate
   (inset 0.04 m), quindi le nascondevano completamente. Portato
   l'inset delle vetrate a 0.16 m (piu' delle pareti laterali) cosi'
   restano visibili davanti al pannello grande. Verificato con
   screenshot ravvicinati prima e dopo la correzione.

Verificato come sempre: tutte le 16 vetrate corrette, 17 attori
fotografici totali (6 pannelli piatti con cornice + 3 pannello curvo
abside + 8 overlay vetrate), coordinate UV di tutte le vetrate in
range [0,1] (a meno di errori di arrotondamento floating-point
dell'ordine di 1e-16, irrilevanti).

## Aggiornamento del 20/08 (parte 7) — checkbox foto, abside curva, nuove foto laterali

Tre richieste in un colpo solo:

1. **Checkbox visibile** "Mostra foto" nella sidebar (sopra la
   legenda colori), oltre al tasto **P** gia' esistente — i due
   restano sincronizzati fra loro.

2. **Pannello dell'abside non piu' piatto**: nuova funzione
   `build_curved_apse_panel()` in `reference_photos.py` che costruisce
   una striscia di quadrilateri seguendo i 5 lati reali del pentagono
   absidale (`ChurchModel.apse_vertices()`), invece di un singolo
   rettangolo. La coordinata U della texture e' proporzionale alla
   distanza percorsa lungo il perimetro (proiezione panoramica
   semplificata) — la stessa foto di prima (`abside_altare_frontale.jpg`)
   ora "avvolge" la vera forma a pentagono, con le finestre della foto
   che cadono in corrispondenza approssimativa dei 5 lati reali.

3. **Nuove foto per le pareti laterali**: `im1.jpg` (navata Ovest) e
   `im2.jpg` (navata Est), fornite dall'utente con questi nomi
   esatti. Dimensionate come le precedenti "bas-côté": larghezza
   allineata all'estensione utile della navata (`_BC_SPAN`, ~23.6 m),
   altezza dall'aspect ratio reale del file — cosi' le finestre
   visibili nella foto cadono vicino alle vetrate di cleristorio
   reali del modello.

Verificato come sempre: tutte le 16 vetrate corrette, 9 attori
fotografici creati (2 pannelli piatti laterali + 1 pannello piatto
ingresso, ciascuno con cornice = 6, piu' il pannello curvo abside con
2 cornici = 3), toggle foto testato sia via tasto che via checkbox.

## Aggiornamento del 20/08 (parte 6) — foto grandi quanto le pareti

I 4 pannelli fotografici ora occupano quasi l'intera altezza dei muri
(altezza pannello 15.5 m su 16.56 m di `WALL_HEIGHT_M`, con margine
minimo sopra/sotto), invece di coprire solo una porzione centrale.
La larghezza si adatta di conseguenza mantenendo l'aspect ratio reale
della foto (calcolato dal file immagine stesso, non stimato): 11.6 m
per le tre foto in formato verticale (0.75), 20.7 m per quella in
formato orizzontale (1.333, "Bas-côté Est"). Effetto molto piu'
immersivo, verificato via screenshot dall'alto e dall'interno.

## Aggiornamento del 20/08 (parte 5) — nuove quote fornite dall'utente

L'utente ha fornito un nuovo set di misure (sostituendo le stime
precedenti in `church_geometry.py`):

| Quota | Valore precedente | Nuovo valore |
|---|---|---|
| Larghezza navata (NAVE_WIDTH_M) | 14.52 m | **13.8 m** |
| Altezza muro (WALL_HEIGHT_M) | 12.10 m | **16.56 m** |
| Gronda tetto basso cappelle | 4.80 m | **8.0 m** |
| Colmo tetto sopra WALL_HEIGHT_M | 5.5 m | **7.0 m** |
| Sporgenza nicchia cappella | 0.75 m | **0.38 m** |
| Larghezza nicchia cappella | 3.20 m | **4.44 m** |
| Davanzale vetrate cappelle | 6.30 m | **10.49 m** |
| Imposta arco vetrate cappelle | 8.50 m | **13.00 m** |
| Davanzale vetrate abside/facciata | 6.50 m | **10.69 m** |
| Imposta arco vetrate abside/facciata | 8.80 m | **13.20 m** |

L'edificio e' quindi significativamente piu' alto e con vetrate di
cleristorio molto piu' in quota di quanto modellato prima.

**Ricalcolato** `APSE_FACET_LENGTHS_M` (da `[1.0,3.6,3.6,3.6,1.0]` a
`[1.0,3.35,3.35,3.35,1.0]`): la chiusura simmetrica del pentagono
absidale dipende da `NAVE_WIDTH_M` (tramite `APSE_RECESS_M` applicato
alla nuova semi-larghezza), quindi le lunghezze dei lati vanno
riverificate quando cambia la larghezza navata. Scarto di chiusura
residuo dopo la correzione: ~2 cm (trascurabile).

**Ridimensionati** i 4 pannelli fotografici (vedi sotto) di un
fattore ~1.37, proporzionalmente all'aumento di `WALL_HEIGHT_M`, cosi'
da occupare ancora una porzione equilibrata delle pareti ora piu'
alte.

Riverificate tutte le 16 vetrate con lo stesso test geometrico
indipendente delle correzioni precedenti: tutte corrette.

## Aggiornamento del 20/08 (parte 4) — solo 4 foto, su richiesta dell'utente

Rimosse tutte le foto tranne le ultime 4 fornite dall'utente (anche i
file, non solo i riferimenti nel codice — la cartella `photos/` ora
contiene solo queste 4 immagini). Niente piu' foto dal PDF diagnostico
ne' quella del tetto (il tetto e' gia' semi-trasparente nel modello,
una foto del soffitto non serviva).

- `abside_altare_frontale.jpg` → **abside**
- `navata_centrale_ingresso.jpg` → **entrata della navata** (centrata
  sull'asse, v=0)
- `navata_verso_ingresso.jpg` → **parete laterale Ovest**, vista
  dall'interno
- `cappelle_laterali_vista2.jpg` → **parete laterale Est**, vista
  dall'interno

Le due pareti laterali sono montate esattamente sul filo del muro
(`v = ±NAVE_WIDTH_M/2`, calcolato dal modello, non un valore a mano) e
ingrandite (5.4×7.2 m e 7.2×5.4 m) per occupare una porzione piu'
sostanziale della parete, dato che ora sono le uniche foto laterali
rimaste (prima le affiancavano le panoramiche "bas-côté", ora
rimosse).

## Aggiornamento del 20/08 (parte 3) — foto panoramiche allineate alla navata reale

Le due foto panoramiche "bas-côté" (che inquadrano tutte e 4 le
cappelle di un lato in un solo scatto) erano larghe solo 9 m — troppo
strette, coprivano si' e no 2 cappelle invece di tutte e 4,
disallineandole vistosamente dalle vetrate reali del modello.
Corretto: la larghezza del pannello ora e' calcolata dalla stessa
formula geometrica usata da `ChurchModel.chapel_u_positions()` per
posizionare le 4 cappelle (`NAVE_LENGTH_M` meno i margini iniziale e
finale, ~23.6 m), non piu' un valore arbitrario — cosi' il pannello
copre esattamente l'estensione utile della navata, da margine a
margine, e le arcate visibili nella foto si allineano con le vetrate
3D reali (entro i limiti di un pannello piatto rispetto a una foto
scattata in prospettiva).

## Aggiornamento del 20/08 (parte 2) — altre 5 foto reali (facciate, pavimento, tetto)

Aggiunte 5 foto fornite dall'utente, distribuite per completare la
copertura fotografica del modello:

- `abside_altare_frontale.jpg` — vista frontale di abside e altare
  maggiore, montata vicino al fondo dell'abside
- `navata_verso_ingresso.jpg` e `cappelle_laterali_vista2.jpg` — viste
  aggiuntive delle cappelle laterali da diverse angolazioni/campate,
  su entrambi i lati della navata
- `navata_centrale_ingresso.jpg` — corsia centrale verso l'abside
  (foto con maggior campo di pavimento visibile), vicino all'ingresso
- `volta_vista_dal_basso.jpg` — la volta della navata vista dal
  basso, per il tetto/soffitto

Per quest'ultima e' stato aggiunto un nuovo tipo di pannello,
`facing="down"`: **orizzontale** invece che verticale (largo lungo
u, profondo lungo v, montato in quota vicino alla volta) — visibile
guardando verso l'alto, a differenza degli altri pannelli che sono
tutti verticali. Vedi `_card_corners_local()` in
`reference_photos.py`.

Totale ora: **14 pannelli fotografici** nel modello. Nessuna
correzione geometrica in questo aggiornamento (solo foto aggiuntive).

## Aggiornamento del 20/08 — abside corretta: vero pentagono a 5 lati con rientranza

**Segnalazione dell'utente** (con annotazioni dirette su una pianta):
l'abside ha davvero **5 lati, ciascuno con una finestra**, e **arretra
rispetto al filo della navata** prima di aprirsi nel pentagono. La
versione precedente (esagono con parete di fondo piatta, vedi
changelog del 19/08 sotto) era anch'essa sbagliata — nata da
un'interpretazione errata dello stesso disegno.

**Misurato programmaticamente** (non a occhio) sulle annotazioni
dell'utente, tramite analisi automatica dei pixel dell'immagine:

- **Rientranza**: isolata la macchia verde per densita' di colore,
  misurata la sua estensione con la scala del disegno (dedotta dalla
  quota "4.00m" disegnata sulla sacrestia, ~95 px/m in quella
  scansione) → **2.6 m** per lato.
- **Azimut delle 5 pareti absidali**: isolate le 5 macchie rosse per
  componenti connesse, calcolato l'orientamento di ciascuna con una
  regressione PCA sui suoi pixel, poi calibrato sull'azimut gia' noto
  e verificato delle pareti di cappella (250°/70°) per risolvere
  l'ambiguita' di verso → **250.0° / 301.4° / 340.9° / 17.6° / 70.0°**
  (rispettivamente: lato corto Ovest, smussato Ovest, fondo, smussato
  Est, lato corto Est).

Il pentagono e' ora costruito "camminando" lungo questi 5 lati
(`ChurchModel.apse_vertices()` in `church_geometry.py`) usando gli
azimut misurati (certi) e lunghezze stimate (`APSE_FACET_LENGTHS_M`,
non misurabili con la stessa precisione — l'evidenziazione dell'utente
segna la posizione della finestra, non l'estensione del muro), scelte
in modo da chiudere il pentagono simmetricamente (verificato: il
punto di arrivo calcolato si scosta da quello atteso di soli ~5 cm).

Le 5 vetrate absidali sono state rinominate coerentemente: "Abside -
lato corto Ovest/Est", "pannello smussato Ovest/Est", "pannello di
fondo". Verificate tutte e 16 le vetrate del modello (8 cappelle + 5
abside + 3 facciata) con lo stesso test geometrico indipendente delle
correzioni precedenti: tutte corrette.

## Aggiornamento del 19/08 — 3 correzioni importanti

1. **Bug geometrico corretto**: le vetrate laterali (cappelle) non
   proiettavano mai luce, solo quella centrale della facciata. Causa:
   `Window.local_outline()` calcolava la direzione "lungo il muro"
   applicando seno/coseno direttamente all'azimut di bussola, come se
   fosse gia' un angolo nel sistema di coordinate locale
   dell'edificio — funzionava solo per la facciata per coincidenza
   geometrica. Corretto in `church_geometry.py` proiettando
   correttamente la direzione sugli assi locali dell'edificio (stessa
   trasformazione usata altrove nel modello). Verificato: prima 0
   proiezioni valide su centinaia di combinazioni data/ora per le
   vetrate laterali, ora funzionano regolarmente.

2. **Pianta non piu' rettangolare**: dal nuovo documento allegato
   (pianta "Relevé de désordres" 1/100) si vede che le 8 cappelle sono
   NICCHIE SPORGENTI reali, non finestre su una parete piatta.
   `floor_outline_local()` ora traccia questi risalti (stimati:
   sporgenza 1.10 m, larghezza 2.60 m — nessuna quota diretta trovata
   nel documento per la profondita' esatta delle nicchie, ma la loro
   ESISTENZA come sporgenza e' certa dalla pianta).

3. **Altezze reali misurate** sulla tavola "ELEVATION OUEST" (scala
   1/100, con righello grafico nel disegno): l'edificio e' molto piu'
   alto di quanto stimato prima, e le vetrate delle cappelle sono in
   realta' finestre di CLERISTORIO alte (sopra il tetto basso delle
   nicchie), non finestre basse nella nicchia stessa. Vedi tabella
   sotto.

| Quota | Valore precedente (stima) | Valore nuovo (misurato) |
|---|---|---|
| Altezza muro (gronda navata) | 9.0 m | **12.1 m** |
| Davanzale vetrate cappelle | 2.4 m | **6.3 m** |
| Imposta arco vetrate cappelle | 5.2 m | **8.5 m** |
| Larghezza vetrate cappelle | 1.1 m | **1.3 m** |
| Gronda tetto basso cappelle | — | **4.8 m** (nuovo) |

Conseguenza fisica interessante: essendo ora molto piu' alte, le
vetrate di cleristorio proiettano macchie di luce sul pavimento solo
quando il sole e' sufficientemente alto ED ben allineato con la
parete (altrimenti il raggio, molto radente, uscirebbe lateralmente
dall'edificio prima di toccare il pavimento) — comportamento
realistico, non un difetto.

## Installazione

```bash
pip install -r requirements.txt --break-system-packages
# oppure singolarmente:
pip install numpy pyvista shapely --break-system-packages
```

Nota: `zoneinfo` fa parte della libreria standard di Python (3.9+) —
se l'errore "No module named 'zoneinfo'" compare, e' segno di Python
< 3.9: aggiornare Python, oppure installare il backport con
`pip install tzdata backports.zoneinfo --break-system-packages` e
sostituire `from zoneinfo import ZoneInfo` con
`from backports.zoneinfo import ZoneInfo` in `viewer_3d.py`.

## Avvio

```bash
python3 viewer_3d.py
```

Si apre una finestra 3D interattiva.

## Controlli

- **Trascina** (tasto sinistro) — ruota il punto di vista liberamente
- **Rotellina** — zoom
- **Tasto destro / shift+trascina** — pan
- **Slider "Giorno dell'anno"** e **"Ora locale"** in alto a sinistra —
  cambiano data e ora; la scena (vetrate illuminate, macchie di luce
  sul pavimento) si aggiorna in tempo reale mentre trascini
- **Tasti 1 / 2 / 3** — salta a solstizio d'inverno / equinozio /
  solstizio d'estate (anno 2026)
- **Tasti n / s / e / w** — vista precostituita dal lato Nord / Sud /
  Est / Ovest
- **Tasto t** — vista dall'alto (pianta)
- **Tasto r** — vista assonometrica di default
- **Tasto p** — mostra/nasconde i pannelli con le foto reali (vedi sotto)
- **Barra spaziatrice** — avvia/ferma un'animazione che fa scorrere
  l'ora automaticamente

Il pannello in alto a destra mostra data/ora correnti, azimut e
altezza del sole, e l'elenco delle vetrate illuminate in quel momento.

## Aggiornamento del 19/08 (parte 4) — foto reali nel modello 3D

Sei foto (5 estratte dal diagnostico PDF + una fornita dall'utente)
sono ora inserite nel modello come pannelli testurizzati, posizionati
vicino al punto a cui si riferiscono:

- Foto dell'utente (navata verso l'abside) — vicino all'ingresso
- Volta con lampadari e vetrate di cleristorio — in alto, centrale
- 2 dettagli ravvicinati di una vetrata — vicino alla prima cappella
- Portale, lato interno ed esterno — vicino alla facciata

Non sono texture "incollate" sulle superfici del modello (nessuna
proiezione fotogrammetrica: la geometria resta quella schematica
descritta sopra) - sono piccoli pannelli verticali con cornice,
pensati come riferimento visivo mentre si esplora il modello, non
come rivestimento fotorealistico. Premi **P** per nasconderli se
disturbano la lettura delle proiezioni solari.

Nuovo file: `reference_photos.py` (definisce posizione, dimensioni e
orientamento di ciascun pannello — facilmente modificabile) e la
cartella `photos/` con le immagini. Nota tecnica per chi aggiunge foto
proprie: se il file ha un tag EXIF di rotazione (tipico delle foto da
smartphone) va normalizzato con `PIL.ImageOps.exif_transpose()` prima
di salvarlo, altrimenti la texture appare ruotata di 90° pur essendo
il pannello geometricamente corretto (mi e' capitato con la foto
fornita durante lo sviluppo).

## Struttura del codice

- `solar_position.py` — posizione solare (algoritmo NOAA/Meeus),
  invariato e validato rispetto alle versioni precedenti del progetto
- `church_geometry.py` — modello parametrico 2.5D della chiesa
  (impronta in pianta CON sporgenze delle cappelle, 14 vetrate con
  posizione/dimensioni/azimut) — vedi le 3 correzioni sopra
- `church_mesh.py` — costruisce le mesh 3D SOLIDE con PyVista a
  partire dal modello 2.5D — mura con vero spessore
  (`WALL_THICKNESS_M`, stimato 0.70 m), tetto a padiglione, soletta di
  pavimento, vetrate come inserti vetrati solidi incassati nello
  spessore del muro. Usa ora `WALL_HEIGHT_M` da `church_geometry.py`
  (12.1 m, misurato) invece del valore stimato precedente.
- `light_projection.py` — proiezione del raggio solare fino al
  pavimento soltanto (usato solo internamente da `wall_projection.py`
  per il calcolo del vettore solare; il ritaglio contro il perimetro
  non e' piu' usato direttamente da `viewer_3d.py`, vedi sotto)
- `wall_projection.py` — **nuovo**: come sopra, ma se il raggio non
  raggiunge il pavimento entro il perimetro (incidenza troppo
  radente) la macchia di luce viene disegnata sulla PARETE VERTICALE
  interna che il raggio incontra per primo, invece di sparire. Gestisce
  anche il caso "misto" (una vetrata la cui macchia cade in parte sul
  pavimento e in parte su una parete, es. verso l'alba/tramonto),
  infittendo il contorno della vetrata e raggruppando i punti per
  superficie colpita, condividendo i punti di passaggio così i
  poligoni pavimento/parete si accostano senza vuoti visibili.
- `reference_photos.py` — posiziona foto reali come pannelli
  testurizzati nel modello 3D (vedi "Aggiornamento parte 4" sotto)
- `viewer_3d.py` — l'applicazione interattiva: due pannelli VTK
  separati (sidebar controlli a sinistra, vista 3D a destra — non si
  sovrappongono mai), slider, tasti di scelta rapida

## Aggiornamento del 19/08 (parte 3) — proiezione anche sulle pareti

Prima le vetrate con incidenza molto radente (raggio quasi parallelo
al pavimento) semplicemente non mostravano alcuna macchia di luce,
anche se la vetrata era "rivolta" al sole: il raggio, geometricamente,
avrebbe attraversato una parete prima di raggiungere il pavimento
visibile, e quel caso veniva scartato. Ora `wall_projection.py`
verifica per ogni punto del contorno della vetrata quale superficie
(pavimento o una delle pareti interne) il raggio incontra per primo, e
disegna la macchia li'. Verificato su 4032 combinazioni data/ora/
vetrata (nessun errore, 2005 macchie generate contro le poche
centinaia di prima) e su un caso "mite" con macchia che scavalca
visibilmente lo spigolo pavimento-parete senza soluzione di
continuita'.

## Aggiornamento del 19/08 (parte 2) — layout interfaccia, abside e cappelle

**1. Layout dell'interfaccia.** La finestra ora usa due renderer VTK
SEPARATI (non piu' un overlay sulla vista 3D): un pannello laterale
fisso a sinistra con tutti i controlli, la vista 3D a destra. Non si
sovrappongono mai, indipendentemente da come viene ridimensionata la
finestra. Data e ora sono mostrate in grande (26-30pt) sopra ai
rispettivi slider.

**2. Abside corretta: non e' un pentagono a punta.** Misurando
`pianta2.pdf` (pianta "Relevé de désordres" 1/100, usando come
riferimento di scala la quota "4.00m" disegnata sulla sacrestia,
~64.5 px/m) e' emerso che l'abside ha in realta' una **parete di
fondo PIATTA** con i due angoli tagliati in diagonale ("abside a pan
coupé" — un esagono, non un pentagono). Il punto dove convergevano
le nervature nel disegno precedente (etichettato "Fig.12" nella
pianta) era il colmo della volta a raggiera, NON un vertice del
muro — un errore di lettura della pianta commesso nella versione
precedente. Ora l'azimut dei due pannelli smussati e' calcolato
geometricamente da `ChurchModel.segment_outward_azimuth()` invece di
essere stimato a mano con un angolo arbitrario. Anche le nicchie
delle cappelle sono state ri-misurate sulla stessa pianta: risultano
piu' larghe (3.20 m, prima 2.60 m) e meno sporgenti (0.75 m, prima
1.10 m).

**3. Secondo bug di orientamento (cappelle).** Verificando la nuova
pianta e' emerso un bug indipendente dal primo (gia' corretto in
precedenza): le 8 vetrate delle cappelle avevano l'azimut
INVERTITO — la direzione dichiarata come "verso l'esterno" portava
in realta' piu' dentro la chiesa. Scoperto con un test
indipendente e non circolare (spostarsi di qualche metro nella
direzione dichiarata "esterna" e controllare se ci si trova
davvero fuori dall'edificio) su tutte e 14 le vetrate. Corretto, e
le etichette dei lati sono state rinominate da (NE)/(SW) — fuorvianti
e all'origine della confusione — a (Ovest)/(Est), coerenti sia con
l'azimut reale sia con la nomenclatura "ELEVATION OUEST/EST" del
documento originale.

## Note tecniche / limiti residui

- Lo spessore dei muri (0.70 m) e lo spessore della soletta (0.30 m)
  restano stime ragionevoli, non misure dirette — modificabili
  in cima a `church_mesh.py` e `church_geometry.py`.
- Le nicchie delle cappelle sono modellate alla STESSA altezza del
  muro principale (12.1 m) per semplicita', anche se in realta' hanno
  probabilmente un tetto basso indipendente (gronda ~4.8 m, misurata)
  con una propria falda che si raccorda al muro alto del cleristorio.
  Modellare questo secondo livello di tetto e' un possibile
  miglioramento futuro, non ancora implementato.
- Il tetto principale e' semplificato come un unico padiglione
  piramidale (visivamente plausibile, non replica esattamente la
  falda a due spioventi + padiglione dell'abside visibile nelle
  foto reali).
- La proiezione della luce ora considera sia il **pavimento** sia le
  **pareti verticali interne** (vedi "Aggiornamento parte 3" sopra).
  Non modellati: il soffitto/volta (un raggio che risalirebbe oltre
  l'altezza dei muri non e' rappresentato) e le pareti ESTERNE oltre
  lo spessore del muro.
- Le dimensioni delle vetrate dell'abside e della facciata restano
  stimate per coerenza proporzionale (nessuna elevazione dedicata
  trovata nel documento per queste due parti).

