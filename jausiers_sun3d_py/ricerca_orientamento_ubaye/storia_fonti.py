"""
Storia e fonti delle chiese dell'Ubaye (ricerca dell'08/11/2026).

Per ogni edificio (chiave = id OpenStreetMap) un riassunto in italiano,
scritto a partire dalle fonti elencate. Le fonti sono abbreviate con i
codici di FONTI_COMUNI / FONTI_CHIESA qui sotto; i link a OSM, Wikidata e
Mérimée vengono aggiunti automaticamente da build_mappa.py.

Wikipedia (fr) consultata l'08/11/2026, sezioni "Lieux et monuments" /
"Art religieux" delle voci dei comuni e voci delle singole chiese.
Bibliografia citata da quelle voci: Raymond Collier, "La Haute-Provence
monumentale et artistique", Digne, 1986.
"""

WP = "https://fr.wikipedia.org/wiki/"
FONTI = {
    "wp_jausiers": ("Wikipedia (fr): Jausiers, Art religieux", WP + "Jausiers"),
    "wp_jausiers_ch": ("Wikipedia (fr): Église Saint-Nicolas-de-Myre de Jausiers", WP + "Église_Saint-Nicolas-de-Myre_de_Jausiers"),
    "wp_barcelonnette": ("Wikipedia (fr): Barcelonnette, Art religieux", WP + "Barcelonnette"),
    "wp_stpaul": ("Wikipedia (fr): Saint-Paul-sur-Ubaye, Art religieux", WP + "Saint-Paul-sur-Ubaye"),
    "wp_stpaul_ch": ("Wikipedia (fr): Église Saint-Pierre-et-Saint-Paul de Saint-Paul-sur-Ubaye", WP + "Église_Saint-Pierre-et-Saint-Paul_de_Saint-Paul-sur-Ubaye"),
    "wp_maurin": ("Wikipedia (fr): Église Saint-Antoine-du-Désert de Maurin", WP + "Église_Saint-Antoine-du-Désert_de_Maurin"),
    "wp_meolans": ("Wikipedia (fr): Méolans-Revel, Lieux et monuments", WP + "Méolans-Revel"),
    "wp_stpons": ("Wikipedia (fr): Saint-Pons (Alpes-de-Haute-Provence)", WP + "Saint-Pons_(Alpes-de-Haute-Provence)"),
    "wp_stpons_ch": ("Wikipedia (fr): Église Saint-Pons de Saint-Pons", WP + "Église_Saint-Pons_de_Saint-Pons"),
    "wp_condamine": ("Wikipedia (fr): La Condamine-Châtelard", WP + "La_Condamine-Châtelard"),
    "wp_enchastrayes": ("Wikipedia (fr): Enchastrayes", WP + "Enchastrayes"),
    "wp_faucon": ("Wikipedia (fr): Faucon-de-Barcelonnette", WP + "Faucon-de-Barcelonnette"),
    "wp_lauzet": ("Wikipedia (fr): Le Lauzet-Ubaye", WP + "Le_Lauzet-Ubaye"),
    "wp_thuiles": ("Wikipedia (fr): Les Thuiles", WP + "Les_Thuiles"),
    "wp_uvernet": ("Wikipedia (fr): Uvernet-Fours, Églises et chapelles", WP + "Uvernet-Fours"),
    "wp_pontis": ("Wikipedia (fr): Pontis", WP + "Pontis"),
    "wp_larche": ("Wikipedia (fr): Larche (Alpes-de-Haute-Provence)", WP + "Larche_(Alpes-de-Haute-Provence)"),
    "wp_meyronnes": ("Wikipedia (fr): Meyronnes", WP + "Meyronnes"),
    "wp_breole": ("Wikipedia (fr): La Bréole", WP + "La_Bréole"),
    "wp_stvincent": ("Wikipedia (fr): Saint-Vincent-les-Forts", WP + "Saint-Vincent-les-Forts"),
    "diag2016": ("Diagnostic 2016, M. Trubert (ACMH), synthèse historique pp. 11-29 (archivi comunali, AD Digne, DRAC PACA, Médiathèque du Patrimoine, SHD)", "file:///Users/andreew_1/Documents/eglise_jausiers/Eglsie_StNicolas_Diagnostic_2016.pdf"),
    "atti1668": ("Atti del 4/1/1668 e del 4/9/1689 (trascrizione «Eglise Saint Nicolas_création»)", "file:///Users/andreew_1/Documents/eglise_jausiers/Eglise%20Saint%20Nicolas_cr%C3%A9ation.pdf"),
    "programma": ("Programma jausiers_sun3d_py: church_geometry.py (planimetria catastale con freccia nord)", "../church_geometry.py"),
}

# osm id -> dict(epoca, protezione, storia=[paragrafi], fonti=[codici], orient=nota sull'orientamento dalle fonti)
STORIA = {
 # ---------------- Barcelonnette
 "way/128064002": dict(epoca="Medioevo; ricostruita 1634-1644; chiesa attuale 1923-1927",
   storia=["Chiesa medievale distrutta dal grande incendio del 1628 e ricostruita due volte (1634-1638 e 1643-1644). L'edificio seicentesco fu demolito nel 1926-1927: la chiesa attuale, iniziata nel 1923, lo sostituisce.",
           "Del Seicento resta il campanile, rialzato di un piano nel 1653 per le campane, con bifore, piramidi e doccioni; il campanile in ferro battuto con la Vergine dorata è del 1860."],
   fonti=["wp_barcelonnette"]),
 "way/128062231": dict(storia=["Wikidata la chiama «chapelle Saint-Jacques-et-Saint-Philippe des Allemands». Nelle fonti aperte consultate non ci sono altre notizie."], fonti=[]),
 # ---------------- Enchastrayes
 "way/195326268": dict(epoca="parrocchia dal 1816", storia=["Chiesa del hameau di La Conche, eretta in parrocchia nel 1816 (la voce del comune la chiama anche cappella)."], fonti=["wp_enchastrayes"]),
 "way/195328613": dict(epoca="XIX secolo", storia=["Chiesa del villaggio, del XIX secolo, addossata al municipio.",
   "Conserva il quadro «Le anime del Purgatorio con i santi Pietro e Paolo» (1717), classificato monumento storico come oggetto (1991)."], fonti=["wp_enchastrayes"]),
 "way/600812181": dict(storia=["Wikidata: «chapelle Saint-Jean du Villard». La voce del comune cita una cappella al Villard senza altri dettagli."], fonti=["wp_enchastrayes"]),
 # ---------------- Faucon
 "way/72861887": dict(epoca="XI secolo; ricostruita nel XVII secolo",
   storia=["Prima costruzione nell'XI secolo, ricostruita nel Seicento. Navata con collaterali, archi a tutto sesto, abside a catino (cul-de-four).",
           "Il campanile isolato è il monumento più antico: secondo la DRAC i primi 20 metri sarebbero gallo-romani (secondo Collier è una ricostruzione del XVI secolo). Ha una meridiana del 1878. Nella chiesa c'è un coperchio di sarcofago classificato."],
   fonti=["wp_faucon"]),
 "way/72862315": dict(storia=["Edificio vicino al campanile di Saint-Étienne, senza nome in OSM. Potrebbe essere la cappella dei Penitenti (1690, ex chiesa dei Chalaisiens, oggi sala delle feste), che le fonti collocano accanto al campanile: identificazione da verificare."], fonti=["wp_faucon"]),
 "way/72862068": dict(storia=["La voce del comune non cita una cappella Saint-Jean-de-Matha. Ricorda però il convento dei Trinitari, insediato in Ubaye nel 1666, anno della canonizzazione di san Giovanni de Matha. La pianta OSM comprende più edifici."], fonti=["wp_faucon"]),
 # ---------------- Jausiers
 "way/93932532": dict(epoca="costruita tra il 1668 e il 1689 (atti notarili); campanile dopo il 1860", protezione="Monumento storico, classificata nel 1921 (PA00080407)",
   storia=["Chiesa barocca di stile controriformato, definita «la più grande chiesa barocca dei paesi della Durance». Due atti notarili ne fissano la costruzione tra il 1668 e il 1689. Il 4 gennaio 1668 la cappellania di San Giovanni Battista e i consoli decidono di ricostruire la cappella in rovina al Pasquier, oppure, se lì sorgerà la nuova parrocchiale, di farvi un altare di San Giovanni Battista. Il 4 settembre 1689 la cappellania risulta insediata nella chiesa parrocchiale: da qui il doppio patronato, san Nicola e san Giovanni Battista. Gli atti confermano il XVII secolo (Collier) contro il XVIII della scheda MH; Wikipedia indica una consacrazione nel 1686.",
           "Il 21 aprile 1691 la chiesa, «fraîchement bâtie», fu saccheggiata dalle truppe francesi. Il campanile annesso è posteriore al 1860: quell'anno l'abate Féraud scrive che non esiste. Interventi successivi: altare Cantini (1904), alluvione (1957), copertura in scandole di larice (1973), meridiane rifatte da Gavoty (1993).",
           "Navata di quattro campate alta 18 m, coro con volte a crociera raggiate, capitelli corinzi. Le fonti danno 26 × 18 m (il programma, dalla planimetria catastale, usa una navata di 26,52 m e un'abside a 5 lati)."],
   orient="il diagnostico 2016 lo dice esplicitamente: «L'édifice n'est pas orienté», mentre la chiesa antica, demolita, era orientata. Planimetria catastale (facciata a 160°), pianta OSM (156°) e ortofoto concordano su una facciata a SSE con meridiana sul lato sud; la «facciata occidentale» di Wikipedia è un errore.",
   fonti=["diag2016", "atti1668", "wp_jausiers_ch", "wp_jausiers", "programma"]),
 "way/93928811": dict(epoca="1832", storia=["Chiesa del hameau di Les Sanières, un tempo parrocchiale, costruita nel 1832 e dedicata a san Sebastiano."], fonti=["wp_jausiers"]),
 "way/93927303": dict(storia=["Chiesa del hameau di Lans, un tempo parrocchiale, dedicata all'Annunciazione (Wikidata: «Notre-Dame-del-Bosc de Lans»)."], fonti=["wp_jausiers"]),
 # ---------------- La Condamine-Châtelard
 "way/290959205": dict(epoca="1822", storia=["Chiesa parrocchiale del capoluogo, del 1822, dedicata a santa Caterina d'Alessandria. Sul frontone c'è un occhio di bue a forma di conchiglia largo più di 1,5 m. Conserva una «Presentazione di Gesù al Tempio» di Fidèle Maria Patritti (1862)."], fonti=["wp_condamine"]),
 "way/128081857": dict(epoca="1830", storia=["Chiesa del Châtelard, del 1830. Coro a catino e campanile costruito contro il coro, addossato alla cappella dei Penitenti. Conserva un fonte battesimale carolingio classificato."], orient="Il coro a catino si vede in ortofoto come estremità arrotondata a nord, e la direzione misurata lo conferma.", fonti=["wp_condamine"]),
 "way/128081813": dict(epoca="~1630 (OSM)", storia=["Cappella dei Penitenti del Châtelard, addossata al campanile di Saint-Clément e probabilmente della stessa epoca."], fonti=["wp_condamine"]),
 "way/128082035": dict(epoca="~1870 (OSM)", storia=["Cappella Saint-Roch del Châtelard, citata tra le piccole cappelle ancora in piedi."], fonti=["wp_condamine"]),
 "way/162367074": dict(storia=["Cappella Sainte-Anne, alla confluenza del torrente Berrad con il Parpaillon, al centro di un habitat sparso."], fonti=["wp_condamine"]),
 "way/128082218": dict(storia=["Piccola cappella del comune; nelle fonti aperte consultate non ci sono altre notizie."], fonti=[]),
 # ---------------- Le Lauzet-Ubaye
 "way/128071277": dict(epoca="1715", storia=["Chiesa del 1715 a navata unica di tre campate, coro a chevet piatto, decorazione dipinta neomedievale della metà dell'Ottocento. Campanile a torre quadrata con guglia in pietra e quattro piramidi.",
   "Conserva una «Vergine della Misericordia» di Jacques Bottero (verso il 1700), proveniente dal convento dei Domenicani di Barcelonnette e classificata."], fonti=["wp_lauzet"]),
 "way/128071366": dict(storia=["Cappella Sainte-Anne di Champcontier, citata senza data."], fonti=["wp_lauzet"]),
 "way/128071854": dict(storia=["Cappella Saint-Paul di Costeplane, citata senza data."], fonti=["wp_lauzet"]),
 # ---------------- Les Thuiles
 "way/128068584": dict(epoca="fine XVII-XVIII secolo; campanile e portale sud inizio XVI",
   storia=["Navata alta di tre campate con volte a crociera e cappelle laterali in ogni campata; coro più basso. Del precedente edificio restano il campanile quadrato con guglia e quattro piramidi e il portale sud gotico (inizio del XVI secolo). Meridiana del 1881, restaurata nel 1996."], fonti=["wp_thuiles"]),
 "way/128069346": dict(storia=["Cappella Saint-Jean del hameau des Prats, vicino a un mulino. Conserva l'unico oggetto classificato del comune, una pisside d'argento del XVIII secolo."], fonti=["wp_thuiles"]),
 "way/128069036": dict(storia=["Cappella Saint-Joseph di Miraval, citata senza data."], fonti=["wp_thuiles"]),
 "way/128069160": dict(storia=["Cappella dei Guérins, citata come cappella aperta."], fonti=["wp_thuiles"]),
 "way/128069132": dict(storia=["Wikidata: «chapelle du Clot-Meyrans» (dedicata a san Giuseppe secondo la voce del comune)."], fonti=["wp_thuiles"]),
 # ---------------- Méolans-Revel
 "way/127740276": dict(epoca="fine XV secolo (elementi gotici); cappella nord XVI-XVII",
   storia=["Chiesa parrocchiale di Revel. Sulla facciata c'è una statuetta gotica di san Giacomo della fine del Quattrocento; restano elementi gotici e la cappella nord, voltata a crociera, del passaggio tra Cinquecento e Seicento."], fonti=["wp_meolans"]),
 "way/127740201": dict(epoca="priorato fondato nel 1135; ricostruita nel XVII secolo",
   storia=["Antico priorato di Laverq, dipendente da Volonne e fondato nel 1135, poi passato alle abbazie di Chalais e di Boscodon. Resta un frammento di muro della prima costruzione; la chiesa fu ricostruita nel Seicento e rinnovata nell'Ottocento.",
           "Navata di due campate, cupola sul coro, campanile a torre accanto alla facciata ovest con guglia in pietra a quattro facce."],
   orient="Il campanile sta accanto alla facciata ovest: abside a est, come la misura (82°).", fonti=["wp_meolans"]),
 "way/127740254": dict(epoca="1763", storia=["Notre-Dame-de-la-Visitation, detta Notre-Dame-des-Lumières, a Rioclar: antica parrocchia indipendente, del 1763. Navata di due campate, campanile a torre, un Cristo ligneo del XVI secolo."], fonti=["wp_meolans"]),
 "way/127741573": dict(epoca="XVIII secolo", storia=["Cappella di Chaudon del XVIII secolo: navata di due campate con volte a crociera, porta a sud e campanile a vela sopra la facciata ovest."],
   orient="Il campanile a vela sopra la facciata ovest indica l'abside a est. Il calcolo automatico dava il verso opposto (262°): orientamento corretto a 82°.", fonti=["wp_meolans"]),
 "way/127740308": dict(storia=["Wikidata: «église Saint-Julien de Méolans». La voce del comune ricorda che la chiesa Saint-Julien originale è scomparsa e che ne resta il campanile cinquecentesco isolato su una roccia (sito classificato nel 1944). L'edificio mappato è la chiesa/cappella attuale."], fonti=["wp_meolans"]),
 "way/127740306": dict(storia=["Antica chiesa parrocchiale di Saint-Barthélemy (Wikidata: «église Saint-Julien de Saint-Barthélemy»), citata senza data."], fonti=["wp_meolans"]),
 "way/127740366": dict(storia=["Cappella Saint-Jean di Peynier, una delle cappelle succursali della parrocchia."], fonti=["wp_meolans"]),
 "way/127741231": dict(storia=["Cappella Saint-Antoine-et-Saint-Roch di Rioclar-Bas, citata solo in una didascalia."], fonti=["wp_meolans"]),
 "way/127741555": dict(storia=["Cappella del hameau des Trons, citata solo in una didascalia."], fonti=["wp_meolans"]),
 # ---------------- Pontis
 "way/197385428": dict(epoca="XIX secolo", storia=["Chiesa parrocchiale del XIX secolo, dedicata a san Girolamo con san Pietro patrono (Wikidata la chiama «Saint-Joseph»). Rosone a vetrata e meridiana recente in facciata, campanile con quattro piramidi.",
   "Conserva un piatto da questua in rame del XVI secolo, classificato nel 1995, e due quadri (san Girolamo, 1665; Vergine con Bambino, XVIII secolo) restaurati nel 2013."], fonti=["wp_pontis"]),
 "way/197385437": dict(storia=["Parrocchia secondaria creata all'Adroit de Pontis perché il terreno rendeva difficile raggiungere il capoluogo. Il portale in legno è scolpito a imitazione di teste di chiodo."], fonti=["wp_pontis"]),
 "way/1038844287": dict(storia=["Cappella Saint-Pierre aux Hugues, una delle due cappelle del comune."], fonti=["wp_pontis"]),
 "way/197385465": dict(storia=["Cappella del hameau des Chappas (Wikidata: «chapelle Saint-Martin des Chappas»)."], fonti=["wp_pontis"]),
 # ---------------- Saint-Paul-sur-Ubaye
 "way/128090543": dict(epoca="campanile 1390; coro 1452-1472; volte 1690; fortificata 1696", protezione="Monumento storico, classificata nel 1921 (PA00080475)",
   storia=["Origini tardomedievali: la base del campanile (1390 circa) e parte del coro (1452-1472) sono le parti più antiche. Nel 1591 le truppe di Lesdiguières la distrussero mentre gli abitanti vi si erano trincerati; le volte furono ricostruite solo nel 1690, la chiesa fu fortificata nel 1696 e la copertura rifatta nel 1762.",
           "Il terremoto del 5 aprile 1959 fece crollare una campata: i restauri durarono dal 1963 al 1970. Navata di due campate con volte a ogiva, coro a chevet piatto, cappella a sud, arcatelle lombarde all'esterno. Il portale occidentale è dell'inizio del XVI secolo; affreschi cinquecenteschi di pittori italiani."],
   orient="Portale occidentale e coro opposto: l'abside a ENE (63°) è coerente con le fonti.", fonti=["wp_stpaul_ch", "wp_stpaul"]),
 "way/128086950": dict(epoca="fondazioni XII secolo; parrocchia dal 1431; ricostruita dopo il 1531", protezione="Monumento storico, classificata nel 1920 (PA00080476)",
   storia=["Chiesa di Maurin, in fondo alla valle verso le sorgenti dell'Ubaye. I hameaux isolati (La Barge, Maljasset, Combe-Brémond) ottennero la parrocchia nel 1431: prima gli abitanti dovevano scendere fino a Serenne.",
           "Fondazioni del XII secolo; distrutta da una valanga nel 1531 e ricostruita (un'iscrizione sul timpano lo ricorda). Navata di tre campate e coro romanico, portale in marmo rosa. Retable e quadro della Vergine del Rosario (1654) classificati; anche il cimitero, con i suoi capitelli e la porta, è protetto."],
   fonti=["wp_maurin", "wp_stpaul"]),
 "way/128090494": dict(epoca="XIII secolo", storia=["Chiesa gotica di Tournoux, del XIII secolo, con volte più recenti. Il campanile ha base romanica e piani del XVI-XVII secolo con bifore. Un collaterale nord è stato aggiunto nel XVIII-XIX secolo; il portale ha un architrave su due mensole scolpite (XV-XVI secolo). Conserva una Vergine del Rosario."], fonti=["wp_stpaul"]),
 "way/128090511": dict(epoca="1785", storia=["Chiesa di Mélézen del 1785. Una cappella precedente fu trasformata in presbiterio. Croce processionale del XVII secolo classificata."], fonti=["wp_stpaul"]),
 "way/128091115": dict(epoca="1829 (su edificio precedente)", storia=["Antica parrocchiale di Grande-Serenne (Wikidata: «église de la Transfiguration»), eretta nel 1829 su una costruzione precedente. Pianta a croce latina con cupola. Il terremoto del 1959 tranciò la punta del campanile."], fonti=["wp_stpaul"]),
 "way/128091102": dict(epoca="ricostruita nel 1549", protezione="Monumento storico, iscritta 2016 (PA04000035)", storia=["Chiesa Saint-Jean-Baptiste di Fouillouse, tra Fouillouse e Les Serrets, ricostruita nel 1549, con volta a botte spezzata posteriore e campanile a vela a tre fornici. Il Cristo su trave di gloria e un paliotto in arazzo sono classificati. Fouillouse ebbe la parrocchia nel 1534."], fonti=["wp_stpaul", "wp_maurin"]),
 "way/128090492": dict(storia=["Wikidata: «chapelle Saint-Jean-Baptiste de Saint-Paul-sur-Ubaye»; nelle fonti consultate non ci sono altre notizie."], fonti=[]),
 "way/128090944": dict(storia=["Cappella Saint-Roch della Petite-Serenne."], fonti=["wp_stpaul"]),
 "way/128090724": dict(storia=["Cappella del hameau di Prads (Wikidata: Notre-Dame-des-Sept-Douleurs des Prats). Conserva un altare in legno intagliato del XVIII secolo classificato; dipendeva dalla parrocchia del capoluogo."], fonti=["wp_stpaul"]),
 "way/401080144": dict(epoca="fine XVIII secolo; campanile 1819", storia=["Luogo di pellegrinaggio sulla via dei colli verso il Piemonte, costruita dagli abitanti alla fine del Settecento; campanile aggiunto nel 1819. L'affresco del timpano riproduce una tela di Joseph-André Signoret ed è stato rifatto nel 1992."], fonti=["wp_stpaul"]),
 "way/128091064": dict(epoca="coro inizio XVI secolo; ricostruita nel 1988", storia=["Cappella Saint-Jacques di Gleizolles, dipendente da Tournoux. Negli anni Ottanta ne restava solo il coro voltato a ogiva dell'inizio del Cinquecento; gli abitanti la ricostruirono nel 1988 limitandola all'antico chevet."], fonti=["wp_stpaul"]),
 "way/128090685": dict(epoca="metà XIX secolo", storia=["Cappella del colle di Vars, costruita a metà Ottocento al posto di un ospizio per i viaggiatori."], fonti=["wp_stpaul"]),
 "way/1203781998": dict(storia=["Cappella Notre-Dame all'Estrech, presso Les Bonis, dipendente dalla parrocchia del capoluogo."], fonti=["wp_stpaul"]),
 # ---------------- Saint-Pons
 "way/128066982": dict(epoca="priorato XII secolo; coro XVI; navata XVII", protezione="Monumento storico, classificata il 31/10/1912 (PA00080478)",
   storia=["Antico priorato benedettino del XII secolo, ricostruito nel Cinquecento: il coro è del XVI secolo, la navata di tre campate e la cappella sud del XVII. Conserva rare bande lombarde e un arco trionfale con capitelli figurati.",
           "Campanile a torre con guglia a sei facce e doccioni. Il portale occidentale ha tre archivolti; quello sud ha un architrave con Cristo in maestà e un'iscrizione gotica. Il timpano dipinto con l'Adorazione dei Magi (verso il 1500) fu restaurato nel 1912."],
   orient="Chevet piatto e cieco, coro illuminato solo da sud, portale principale a ovest: l'abside guarda a est. Il calcolo automatico dava il verso opposto (283°): orientamento corretto a 103°.",
   fonti=["wp_stpons", "wp_stpons_ch", "wp_barcelonnette"]),
 # ---------------- Ubaye-Serre-Ponçon
 "way/116097551": dict(epoca="1581; campanile rialzato nel 1890", storia=["Chiesa parrocchiale di La Bréole, del 1581. Nel 1890 un lascito permise di rialzare il campanile da circa 30 a 40 m. Vetrate contemporanee, due delle quali del 2013."], fonti=["wp_breole"]),
 "way/128051204": dict(epoca="XVI secolo", storia=["Chiesa di Saint-Vincent-les-Forts, del XVI secolo, dedicata a san Vincenzo di Saragozza: navata con volta a botte ribassata e doppia abside disassata. Nel 1690 le truppe piemontesi di occupazione vi si installarono."], fonti=["wp_stvincent"]),
 "way/128051016": dict(storia=["Chiesa del Lautaret, già esistente quando divenne parrocchia all'inizio del XIX secolo."], fonti=["wp_stvincent"]),
 "way/116084655": dict(storia=["Chiesa Saint-Marcellin di Costebelle. Conserva un calice d'argento del 1711 classificato (Palissy PM04000852)."], fonti=["wp_breole"]),
 "way/128050703": dict(storia=["Cappella dei Rollands, citata senza data."], fonti=["wp_stvincent"]),
 # ---------------- Uvernet-Fours
 "way/128074117": dict(epoca="1677", storia=["Chiesa parrocchiale del capoluogo, Uvernet, del 1677."], fonti=["wp_uvernet"]),
 "way/128075448": dict(epoca="XVI-XVII secolo", storia=["Antica chiesa parrocchiale dei Agneliers, del XVI-XVII secolo. Conserva tre quadri classificati provenienti dalla cappella di Morjuan (Sepoltura di Cristo, Vergine con Bambino, Dio Padre)."], fonti=["wp_uvernet"]),
 "way/128075398": dict(epoca="1969 (OSM)", storia=["Cappella contemporanea della stazione di Pra-Loup, in stile chalet, opera di Pommer, dedicata a san Francesco d'Assisi."], fonti=["wp_uvernet"]),
 # ---------------- Val d'Oronaye
 "way/96741697": dict(epoca="ricostruita dopo il 1945", storia=["Chiesa di Larche. Il villaggio fu completamente distrutto dai combattimenti della Liberazione nell'aprile 1945 e poi ricostruito: l'edificio attuale appartiene alla ricostruzione (la voce del comune cita chiese del XX secolo dedicate a Notre-Dame-des-Neiges e a Saint-Pierre-ès-Liens)."], fonti=["wp_larche"]),
 "way/96741859": dict(epoca="1956 (OSM)", storia=["Maison-Méane, antica parrocchia indipendente, fu distrutta durante la seconda guerra mondiale e ricostruita più in alto, vicino alla nuova strada: la cappella attuale (1956 secondo OSM) è di quella ricostruzione."], fonti=["wp_larche"]),
 "way/96992129": dict(epoca="XIX secolo", storia=["Chiesa parrocchiale di Meyronnes, del XIX secolo, dedicata a san Donato martire (festa il 7 agosto)."], fonti=["wp_meyronnes"]),
 "way/96992035": dict(epoca="1773; parrocchia dal 1833; ricostruita dopo la guerra", storia=["Chiesa di Saint-Ours (Wikidata: «église Saint-Ours de Saint-Ours»). La prima cappella, a nord del hameau, fu spostata e ricostruita nel 1773 al Plan de Saint-Ours, eretta in parrocchia nel 1833 e ricostruita dopo l'ultima guerra."], fonti=["wp_meyronnes"]),
 "way/96992202": dict(epoca="dal 1860", storia=["Cappella del Vieux-Saint-Ours, a circa 1794 m, sul sito della prima cappella, ricostruita a partire dal 1860. Luogo di pellegrinaggio il 17 giugno."], fonti=["wp_meyronnes"]),
 "way/96741723": dict(storia=["Wikidata: «chapelle Sainte-Madeleine du col de Larche»; nelle fonti consultate non ci sono altre notizie."], fonti=[]),
 "way/96741728": dict(storia=["Wikidata: «chapelle Notre-Dame-des-Lumières du Lauzanier», nel vallone del Lauzanier; nelle fonti consultate non ci sono altre notizie."], fonti=[]),
}

# correzioni di verso ricavate dalle fonti (nuovo azimut dell'abside)
CORREZIONI_DA_FONTI = {"way/128066982": 103.1, "way/127741573": 81.7}
CONFERME_DA_FONTI = {"way/127740201", "way/128090543"}
