// i18n.js - testi in italiano e francese, in un solo posto.
//
// I nomi interni delle vetrate restano quelli di church_geometry.py
// (italiano): sono la chiave condivisa con il Python e con i dati di
// riferimento. Qui si traducono solo per la visualizzazione.
"use strict";

// La lingua e' fissata dalla pagina (sito/it/ o sito/fr/, window.LANG_FISSA):
// ogni versione e' in una lingua sola.
const LANG = window.LANG_FISSA === "fr" ? "fr" : "it";
document.documentElement.lang = LANG;

const TESTI = {
  it: {
    nomeChiesa: "Chiesa Saint-Nicolas-de-Myre",
    titoloPagina: "Jausiers - Chiesa Saint-Nicolas-de-Myre - Proiezione solare 3D",
    titoloStoria: "Jausiers - Chiesa Saint-Nicolas-de-Myre - Orientamento e storia",
    nonTradotto: "",
    errore: "Errore durante il caricamento",
    console: "Apri la Console sviluppatore (F12 o Ctrl+Maiusc+K) per il dettaglio completo.",
    lento: "Il caricamento sta impiegando più del previsto",
    lentoCause: "Possibili cause: scheda grafica/driver non supportati da questo browser (prova ad aggiornare il browser o i driver video), oppure un antivirus che rallenta la lettura dei file locali.",
    lentoConsole: "Apri la Console sviluppatore (F12) per vedere se compare un errore.",
    caricamento: "Caricamento modello 3D...",
    giorno: "Giorno dell'anno",
    ora: "Ora locale (Europe/Paris)",
    mostraFoto: "Mostra foto",
    mostraVetrate: "Mostra vetrate",
    vistaInterna: "Viste",
    vistaSinistra: "Sinistra",
    vistaDestra: "Destra",
    vistaAbside: "Abside",
    vistaEsterno: "Esterno",
    vistaFacciataEsterna: "Facciata esterna",
    vistaFacciata: "Facciata",
    vistaNota: "Cappelle numerate dall'ingresso; i lati come li vede chi entra.",
    cappelle: "Cappelle laterali",
    abside: "Abside",
    facciata: "Facciata (ingresso)",
    tasti: "[\u2191][\u2193] avanti/indietro  [\u2190][\u2192] gira\n[Maiusc]+[\u2190][\u2192] passo di lato\n[PagSu][PagGi\u00f9] sali/scendi\n[1][2][3] solstizi/equinozio\n[N][S][E][O] viste laterali\n[T] pianta   [R] reset\n[Spazio] anima giornata\nTrascina (sx) per ruotare\nTrascina (dx) per spostare\nRotellina per zoom",
    mesi: ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    sole: (az, alt) => `Sole: azimut ${az}°\naltezza ${alt}°`,
    soleSotto: "Sole sotto l'orizzonte",
    illuminate: "Vetrate illuminate all'ora scelta:",
    nessuna: "(nessuna)",
    notaLuce: "Per ogni vetrata: da che ora a che ora il sole entra, e per quanto tempo in tutto. Calcolo ogni 10 minuti, con l'orizzonte piatto: le montagne intorno a Jausiers non sono considerate, quindi in realtà il sole arriva più tardi e se ne va prima.",
    luceGiorno: "Luce diretta in questo giorno",
    alba: "alba", tramonto: "tramonto", culmine: "culmine",
    orientamento: "Orientamento",
    fonte_piantine: "Piantine (diagnostico 2016)",
    fonte_online: "Ricerca online",
    fonte_osm: "OpenStreetMap",
    fonte_manuale: "Valore manuale",
    facciataAbside: (f, a) => `Facciata ${f}° · abside ${a}°`,
    rotazione: (d) => `rotazione rispetto alle piantine: ${d}°`,
    asseNonDisponibile: "non disponibile",
    nota: "Le misure vengono dalle piantine cartacee; online e OSM sono solo un confronto.",
    storia: "Orientamento, storia e fonti →",
    sezStoria: "Storia e orientamento",
    testoStoria: "Costruita tra il 1668 e il 1689, monumento storico dal 1921. La facciata guarda a sud-sud-est (160°), l'abside a nord-nord-ovest: la chiesa non è orientata verso est. Cronologia, cartine delle chiese dell'Ubaye e fonti nella pagina dedicata.",
    apriStoria: "Apri storia, orientamento e fonti →",
    sezOrientamento: "Scegli l'orientamento",
    sezData: "Scegli data e ora",
    sezVetrate: "Vetrate illuminate e luce diretta (da verificare)",
    sezMostra: "Mostra",
    tornaModello: "← Modello 3D",
    asseOnline: "Asse trovato dalla ricerca",
    asseAbside: "Abside verso",
    storiaTitolo: "Storia",
    affidabilita: "Affidabilità",
    fonti: "Fonti",
    nessunaRicerca: "Nessuna ricerca ancora salvata (lancia /chiesa nel mod jausiers).",
    aggiornato: "Aggiornato",
    chieseUbaye: "Orientamento delle chiese della valle dell'Ubaye (OpenStreetMap)",
    chieseNota: "Asse lungo dal contorno OSM (rettangolo minimo), noto modulo 180°. devEW: 0 = est-ovest, 90 = nord-sud. Abside: verso del coro, verificato su ortofoto IGN o fonti scritte (ricerca_orientamento_ubaye). Fonte: orientamento_chiese.csv (chiese.py).",
    col: { nome: "Nome originale (OSM)", commune: "Comune", asse: "Asse", devEW: "devEW", pendenza: "Pendenza", vsPendenza: "vs pendenza", osm: "OSM", abside: "Abside", epoca: "Epoca" },
    storiaChiesa: "Storia e fonti",
    cronologia: "Cronologia",
    cartinaChiesa: "La chiesa sulla pianta di OpenStreetMap: asse misurato 156° / 336°",
    cartinaUbaye: "Orientamento delle chiese della valle dell'Ubaye (cartina della ricerca)",
    apriGrande: "Apri a tutta pagina ↗",
    cronologiaNota: "Dagli archivi raccolti nel diagnostico del 2016 (M. Trubert, ACMH) e dalla delibera del 4 gennaio 1668.",
  },
  fr: {
    nomeChiesa: "Église Saint-Nicolas-de-Myre",
    titoloPagina: "Jausiers - Église Saint-Nicolas-de-Myre - Projection solaire 3D",
    titoloStoria: "Jausiers - Église Saint-Nicolas-de-Myre - Orientation et histoire",
    nonTradotto: "Ce texte n'est pas encore disponible en français : relancez la recherche (/chiesa).",
    errore: "Erreur pendant le chargement",
    console: "Ouvrez la Console développeur (F12 ou Ctrl+Maj+K) pour le détail complet.",
    lento: "Le chargement prend plus de temps que prévu",
    lentoCause: "Causes possibles : carte graphique/pilotes non pris en charge par ce navigateur (essayez de mettre à jour le navigateur ou les pilotes graphiques), ou un antivirus qui ralentit la lecture des fichiers locaux.",
    lentoConsole: "Ouvrez la Console développeur (F12) pour voir si une erreur apparaît.",
    caricamento: "Chargement du modèle 3D...",
    giorno: "Jour de l'année",
    ora: "Heure locale (Europe/Paris)",
    mostraFoto: "Afficher les photos",
    mostraVetrate: "Afficher les vitraux",
    vistaInterna: "Vues",
    vistaSinistra: "Gauche",
    vistaDestra: "Droite",
    vistaAbside: "Abside",
    vistaEsterno: "Extérieur",
    vistaFacciataEsterna: "Façade extérieure",
    vistaFacciata: "Façade",
    vistaNota: "Chapelles numérotées depuis l'entrée ; côtés vus en entrant.",
    cappelle: "Chapelles latérales",
    abside: "Abside",
    facciata: "Façade (entrée)",
    tasti: "[\u2191][\u2193] avancer/reculer  [\u2190][\u2192] tourner\n[Maj]+[\u2190][\u2192] pas de côté\n[Pg\u2191][Pg\u2193] monter/descendre\n[1][2][3] solstices/équinoxe\n[N][S][E][O] vues latérales\n[T] plan   [R] réinitialiser\n[Espace] anime la journée\nGlisser (gauche) pour tourner\nGlisser (droite) pour déplacer\nMolette pour zoomer",
    mesi: ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    sole: (az, alt) => `Soleil : azimut ${az}°\nhauteur ${alt}°`,
    soleSotto: "Soleil sous l'horizon",
    illuminate: "Vitraux éclairés à l'heure choisie :",
    nessuna: "(aucun)",
    notaLuce: "Pour chaque vitrail : de quelle heure à quelle heure le soleil entre, et pendant combien de temps au total. Calcul toutes les 10 minutes, avec un horizon plat : les montagnes autour de Jausiers ne sont pas prises en compte, donc en réalité le soleil arrive plus tard et repart plus tôt.",
    luceGiorno: "Lumière directe ce jour-là",
    alba: "lever", tramonto: "coucher", culmine: "culmination",
    orientamento: "Orientation",
    fonte_piantine: "Plans (diagnostic 2016)",
    fonte_online: "Recherche en ligne",
    fonte_osm: "OpenStreetMap",
    fonte_manuale: "Valeur manuelle",
    facciataAbside: (f, a) => `Façade ${f}° · abside ${a}°`,
    rotazione: (d) => `rotation par rapport aux plans : ${d}°`,
    asseNonDisponibile: "non disponible",
    nota: "Les mesures viennent des plans papier ; en ligne et OSM ne servent qu'à comparer.",
    storia: "Orientation, histoire et sources →",
    sezStoria: "Histoire et orientation",
    testoStoria: "Bâtie entre 1668 et 1689, monument historique depuis 1921. La façade regarde vers le sud-sud-est (160°), l'abside vers le nord-nord-ouest : l'église n'est pas orientée vers l'est. Chronologie, cartes des églises de l'Ubaye et sources dans la page dédiée.",
    apriStoria: "Ouvrir histoire, orientation et sources →",
    sezOrientamento: "Choisir l'orientation",
    sezData: "Choisir la date et l'heure",
    sezVetrate: "Vitraux éclairés et lumière directe (à vérifier)",
    sezMostra: "Affichage",
    tornaModello: "← Modèle 3D",
    asseOnline: "Axe trouvé par la recherche",
    asseAbside: "Abside vers",
    storiaTitolo: "Histoire",
    affidabilita: "Fiabilité",
    fonti: "Sources",
    nessunaRicerca: "Aucune recherche enregistrée pour l'instant (lancez /chiesa dans le mod jausiers).",
    aggiornato: "Mis à jour",
    chieseUbaye: "Orientation des églises de la vallée de l'Ubaye (OpenStreetMap)",
    chieseNota: "Axe long d'après le contour OSM (rectangle minimal), connu modulo 180°. devEW : 0 = est-ouest, 90 = nord-sud. Chevet : direction du chœur, vérifiée sur orthophoto IGN ou sources écrites (ricerca_orientamento_ubaye). Source : orientamento_chiese.csv (chiese.py).",
    col: { nome: "Nom", commune: "Commune", asse: "Axe", devEW: "devEW", pendenza: "Pente", vsPendenza: "vs pente", osm: "OSM", abside: "Chevet", epoca: "Époque" },
    storiaChiesa: "Histoire et sources",
    cronologia: "Chronologie",
    cartinaChiesa: "L'église sur le plan OpenStreetMap : axe mesuré 156° / 336°",
    cartinaUbaye: "Orientation des églises de la vallée de l'Ubaye (carte de la recherche)",
    apriGrande: "Ouvrir en pleine page ↗",
    cronologiaNota: "D'après les archives réunies dans le diagnostic de 2016 (M. Trubert, ACMH) et la délibération du 4 janvier 1668.",
  },
};

const T = TESTI[LANG];

// Nomi delle vetrate: chiave = nome del Python (church_geometry.py).
// Le dedicazioni delle cappelle sono nomi propri: restano in francese
// anche nella versione italiana (con gli accenti giusti).
const SANTI_FR = { "Sacre-Coeur": "Sacré-Cœur", "Coeur-Immacule-de-Marie": "Cœur-Immaculé-de-Marie" };
const NOMI_FR = {
  "Abside - lato corto Ovest": "Abside - côté court Ouest",
  "Abside - pannello smussato Ovest": "Abside - pan coupé Ouest",
  "Abside - pannello di fondo": "Abside - pan de fond",
  "Abside - pannello smussato Est": "Abside - pan coupé Est",
  "Abside - lato corto Est": "Abside - côté court Est",
  "Facciata - finestra centrale": "Façade - fenêtre centrale",
  "Facciata - finestra laterale Ovest": "Façade - fenêtre latérale Ouest",
  "Facciata - finestra laterale Est": "Façade - fenêtre latérale Est",
  "Facciata - portale d'ingresso": "Façade - portail d'entrée",
};

function nome(it) {
  const m = /^Cappella (.+) \((Ovest|Est)\)$/.exec(it);
  if (LANG === "it") return m ? `Cappella ${SANTI_FR[m[1]] || m[1]} (${m[2]})` : it;
  if (m) return `Chapelle ${SANTI_FR[m[1]] || m[1]} (${m[2] === "Ovest" ? "Ouest" : "Est"})`;
  return NOMI_FR[it] || it;
}

// Nomi delle chiese OSM (orientamento_chiese.csv): sono nomi propri e
// restano originali; in francese si traducono i segnaposto italiani
// che chiese.py scrive per gli edifici senza nome.
function nomeOsm(n) {
  if (LANG === "it") return n;
  return n
    .replace(/^Edificio di culto senza nome/, "Édifice de culte sans nom")
    .replace(/^Cappella senza nome/, "Chapelle sans nom")
    .replace(/^Chiesa senza nome/, "Église sans nom")
    .replace(/^Cattedrale senza nome/, "Cathédrale sans nom");
}

// Testi della ricerca nella lingua della pagina (campi *_fr per il francese).
function testoRicerca(r, campo) {
  if (!r) return "";
  return LANG === "fr" ? r[campo + "_fr"] || "" : r[campo] || "";
}
