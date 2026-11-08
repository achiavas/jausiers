"""
traduzioni_fr.py - i testi delle chiese dell'Ubaye in francese, e le
correzioni della versione italiana.

I dati nascono in italiano in un'altra parte del progetto
(jausiers_sun3d_py/ricerca_orientamento_ubaye/storia_fonti.json e
orientatamento_chiese_Ubaye/ricerca_saint_nicolas_jausiers.json). Qui non si
modificano quei file: genera_dati.py li legge e usa questo modulo per
produrre una versione francese e una italiana separate.

- fr(testo)  -> il testo in francese (dizionario esatto, poi regole per i
               testi ripetitivi). Un testo che manca resta in italiano e
               finisce in MANCANTI: genera_dati.py lo segnala.
- it(testo)  -> il testo italiano senza parole o citazioni francesi
               (i nomi propri francesi restano).
"""
from __future__ import annotations

import re

MANCANTI: list[str] = []

# ---------------------------------------------------------------------------
# Versione italiana: niente francese, salvo i nomi propri
# ---------------------------------------------------------------------------
_IT = [
    ("«fraîchement bâtie»", "«appena costruita»"),
    ("«L'édifice n'est pas orienté»", "«l'edificio non è orientato»"),
    ("«n'est pas orienté»", "«non è orientato»"),
    ("cappellania di San Giovanni Battista", "cappellania Saint-Jean-Baptiste"),
    ("Diagnostic 2016, M. Trubert (ACMH), synthèse historique pp. 11-29",
     "Diagnostico 2016, M. Trubert (ACMH), sintesi storica, pp. 11-29"),
    ("trascrizione «Eglise Saint Nicolas_création»", "trascrizione"),
    (" (cul-de-four)", ""),
    ("coro a chevet piatto", "coro a terminazione piatta"),
    ("Chevet piatto e cieco", "Terminazione del coro piatta e cieca"),
    ("all'antico chevet", "all'antica abside"),
    ("Retable e quadro", "Pala d'altare e quadro"),
    ("habitat sparso", "abitato sparso"),
    ("I hameaux isolati", "Le frazioni isolate"),
    ("a nord del hameau", "a nord della frazione"),
]
_IT_RE = [
    (re.compile(r"del hameau des (\w[\w-]*)"), r"della frazione Les \1"),
    (re.compile(r"del hameau di "), "della frazione di "),
]


def it(s):
    if not isinstance(s, str):
        return s
    for a, b in _IT:
        s = s.replace(a, b)
    for r, b in _IT_RE:
        s = r.sub(b, s)
    return s


# ---------------------------------------------------------------------------
# Versione francese
# ---------------------------------------------------------------------------
_DIR = {"N": "N", "S": "S", "E": "E", "W": "O", "NW": "NO", "NNW": "NNO", "SW": "SO", "ESE": "ESE",
        "ENE": "ENE", "NE": "NE", "SE": "SE", "WNW": "ONO", "WSW": "OSO", "SSW": "SSO", "NNE": "NNE", "SSE": "SSE"}
_FORMA = {
    ("abside", "semicircolare"): "abside semi-circulaire",
    ("abside", "arrotondata"): "abside arrondie",
    ("abside", "poligonale"): "abside polygonale",
    ("testata", "arrotondata"): "extrémité arrondie",
    ("testata", "poligonale"): "extrémité polygonale",
    ("testata", "semicircolare"): "extrémité semi-circulaire",
}
_PENDIO = {
    "quasi lungo il pendio": "presque dans le sens de la pente",
    "quasi di traverso al pendio": "presque en travers de la pente",
    "obliquo al pendio": "en biais par rapport à la pente",
}

_ESATTI = {
    # verifica sull'ortofoto
    "non determinabile da ortofoto": "non déterminable sur l'orthophoto",
    "pianta OSM parziale/sfasata rispetto all'edificio": "plan OSM partiel ou décalé par rapport au bâtiment",
    "pianta OSM che comprende più edifici": "plan OSM englobant plusieurs bâtiments",
    "confermato (planimetria catastale del programma: 340°)": "confirmé (plan cadastral du programme : 340°)",
    "nessun edificio visibile in ortofoto: pianta OSM da verificare": "aucun bâtiment visible sur l'orthophoto : plan OSM à vérifier",
    # epoca
    "Medioevo; ricostruita 1634-1644; chiesa attuale 1923-1927": "Moyen Âge ; reconstruite en 1634-1644 ; église actuelle 1923-1927",
    "parrocchia dal 1816": "paroisse depuis 1816",
    "XIX secolo": "XIXe siècle",
    "XI secolo; ricostruita nel XVII secolo": "XIe siècle ; reconstruite au XVIIe siècle",
    "costruita tra il 1668 e il 1689 (atti notarili); campanile dopo il 1860": "bâtie entre 1668 et 1689 (actes notariés) ; clocher après 1860",
    "fine XVII-XVIII secolo; campanile e portale sud inizio XVI": "fin XVIIe-XVIIIe siècle ; clocher et portail sud début XVIe",
    "priorato fondato nel 1135; ricostruita nel XVII secolo": "prieuré fondé en 1135 ; reconstruite au XVIIe siècle",
    "fine XV secolo (elementi gotici); cappella nord XVI-XVII": "fin XVe siècle (éléments gothiques) ; chapelle nord XVIe-XVIIe",
    "XVIII secolo": "XVIIIe siècle",
    "fondazioni XII secolo; parrocchia dal 1431; ricostruita dopo il 1531": "fondations XIIe siècle ; paroisse depuis 1431 ; reconstruite après 1531",
    "XIII secolo": "XIIIe siècle",
    "1829 (su edificio precedente)": "1829 (sur un édifice antérieur)",
    "fine XVIII secolo; campanile 1819": "fin XVIIIe siècle ; clocher 1819",
    "coro inizio XVI secolo; ricostruita nel 1988": "chœur début XVIe siècle ; reconstruite en 1988",
    "ricostruita nel 1549": "reconstruite en 1549",
    "metà XIX secolo": "milieu du XIXe siècle",
    "campanile 1390; coro 1452-1472; volte 1690; fortificata 1696": "clocher 1390 ; chœur 1452-1472 ; voûtes 1690 ; fortifiée en 1696",
    "priorato XII secolo; coro XVI; navata XVII": "prieuré XIIe siècle ; chœur XVIe ; nef XVIIe",
    "1581; campanile rialzato nel 1890": "1581 ; clocher surélevé en 1890",
    "XVI secolo": "XVIe siècle",
    "XVI-XVII secolo": "XVIe-XVIIe siècle",
    "ricostruita dopo il 1945": "reconstruite après 1945",
    "dal 1860": "depuis 1860",
    "1773; parrocchia dal 1833; ricostruita dopo la guerra": "1773 ; paroisse depuis 1833 ; reconstruite après la guerre",
    # fonti
    "Pendenza: DEM IGN RGE ALTI, calcolata da chiese.py": "Pente : MNT IGN RGE ALTI, calculée par chiese.py",
    "Diagnostic 2016, M. Trubert (ACMH), synthèse historique pp. 11-29 (archivi comunali, AD Digne, DRAC PACA, Médiathèque du Patrimoine, SHD)":
        "Diagnostic 2016, M. Trubert (ACMH), synthèse historique p. 11-29 (archives communales, AD Digne, DRAC PACA, Médiathèque du Patrimoine, SHD)",
    "Atti del 4/1/1668 e del 4/9/1689 (trascrizione «Eglise Saint Nicolas_création»)": "Actes du 4/1/1668 et du 4/9/1689 (transcription)",
    "Programma jausiers_sun3d_py: church_geometry.py (planimetria catastale con freccia nord)":
        "Programme jausiers_sun3d_py : church_geometry.py (plan cadastral avec flèche nord)",
    # scheda della ricerca su Saint-Nicolas (ricerca_saint_nicolas_jausiers.json)
    "Diagnostic 2016, M. Trubert (ACMH), synthèse historique pp. 11-29": "Diagnostic 2016, M. Trubert (ACMH), synthèse historique p. 11-29",
    "Atti del 4/1/1668 e 4/9/1689 (trascrizione)": "Actes du 4/1/1668 et du 4/9/1689 (transcription)",
    "Ortofoto IGN (Géoplateforme)": "Orthophoto IGN (Géoplateforme)",
    "Programma jausiers_sun3d_py, church_geometry.py": "Programme jausiers_sun3d_py, church_geometry.py",
}

# I paragrafi di storia, nell'ordine di storia_fonti.json (vedi STORIA_IT_INIZIO
# per controllare che l'abbinamento sia giusto).
_STORIA_FR = [
    "Église médiévale détruite par le grand incendie de 1628 et reconstruite deux fois (1634-1638 et 1643-1644). L'édifice du XVIIe siècle fut démoli en 1926-1927 : l'église actuelle, commencée en 1923, le remplace.",
    "Du XVIIe siècle subsiste le clocher, surélevé d'un étage en 1653 pour les cloches, avec baies géminées, pyramides et gargouilles ; le campanile en fer forgé avec la Vierge dorée date de 1860.",
    "Wikidata l'appelle « chapelle Saint-Jacques-et-Saint-Philippe des Allemands ». Les sources ouvertes consultées ne donnent pas d'autres informations.",
    "Église du hameau de La Conche, érigée en paroisse en 1816 (l'article de la commune l'appelle aussi chapelle).",
    "Église du village, du XIXe siècle, adossée à la mairie.",
    "Elle conserve le tableau « Les âmes du Purgatoire avec saint Pierre et saint Paul » (1717), classé monument historique au titre objet (1991).",
    "Wikidata : « chapelle Saint-Jean du Villard ». L'article de la commune mentionne une chapelle au Villard sans autre détail.",
    "L'article de la commune ne mentionne pas de chapelle Saint-Jean-de-Matha. Il rappelle en revanche le couvent des Trinitaires, installé en Ubaye en 1666, année de la canonisation de saint Jean de Matha. Le plan OSM englobe plusieurs bâtiments.",
    "Première construction au XIe siècle, reconstruite au XVIIe. Nef avec collatéraux, arcs en plein cintre, abside en cul-de-four.",
    "Le clocher isolé est le monument le plus ancien : selon la DRAC, ses 20 premiers mètres seraient gallo-romains (selon Collier, il s'agit d'une reconstruction du XVIe siècle). Il porte un cadran solaire de 1878. L'église abrite un couvercle de sarcophage classé.",
    "Bâtiment proche du clocher de Saint-Étienne, sans nom dans OSM. Il pourrait s'agir de la chapelle des Pénitents (1690, ancienne église des Chalaisiens, aujourd'hui salle des fêtes), que les sources placent à côté du clocher : identification à vérifier.",
    "Église du hameau de Lans, autrefois paroissiale, dédiée à l'Annonciation (Wikidata : « Notre-Dame-del-Bosc de Lans »).",
    "Église baroque de style Contre-Réforme, qualifiée de « plus grande église baroque des pays de Durance ». Deux actes notariés en fixent la construction entre 1668 et 1689. Le 4 janvier 1668, la chapellenie Saint-Jean-Baptiste et les consuls décident de reconstruire la chapelle en ruine au Pasquier ou, si la nouvelle paroissiale doit s'y élever, d'y faire un autel de saint Jean-Baptiste. Le 4 septembre 1689, la chapellenie est installée dans l'église paroissiale : d'où le double patronage, saint Nicolas et saint Jean-Baptiste. Les actes confirment le XVIIe siècle (Collier) contre le XVIIIe de la notice MH ; Wikipédia indique une consécration en 1686.",
    "Le 21 avril 1691, l'église, « fraîchement bâtie », fut pillée par les troupes françaises. Le clocher attenant est postérieur à 1860 : cette année-là, l'abbé Féraud écrit qu'il n'existe pas. Interventions suivantes : autel Cantini (1904), crue (1957), couverture en bardeaux de mélèze (1973), cadrans solaires refaits par Gavoty (1993).",
    "Nef de quatre travées haute de 18 m, chœur aux voûtes d'arêtes rayonnantes, chapiteaux corinthiens. Les sources donnent 26 × 18 m (le programme, d'après le plan cadastral, utilise une nef de 26,52 m et une abside à 5 pans).",
    "Orientation : le diagnostic 2016 le dit explicitement : « L'édifice n'est pas orienté », alors que l'ancienne église, démolie, l'était. Plan cadastral (façade à 160°), plan OSM (156°) et orthophoto s'accordent sur une façade au SSE avec un cadran solaire au sud ; la « façade occidentale » de Wikipédia est une erreur.",
    "Église du hameau des Sanières, autrefois paroissiale, bâtie en 1832 et dédiée à saint Sébastien.",
    "Église du Châtelard, de 1830. Chœur en cul-de-four et clocher construit contre le chœur, adossé à la chapelle des Pénitents. Elle conserve des fonts baptismaux carolingiens classés.",
    "Orientation : le chœur en cul-de-four se voit sur l'orthophoto comme une extrémité arrondie au nord, et la direction mesurée le confirme.",
    "Église paroissiale du chef-lieu, de 1822, dédiée à sainte Catherine d'Alexandrie. Le fronton porte un oculus en forme de coquille de plus de 1,5 m de large. Elle conserve une « Présentation de Jésus au Temple » de Fidèle Maria Patritti (1862).",
    "Petite chapelle de la commune ; les sources ouvertes consultées ne donnent pas d'autres informations.",
    "Chapelle Saint-Roch du Châtelard, citée parmi les petites chapelles encore debout.",
    "Chapelle Sainte-Anne, au confluent du torrent du Berrad et du Parpaillon, au centre d'un habitat dispersé.",
    "Chapelle des Pénitents du Châtelard, adossée au clocher de Saint-Clément et probablement de la même époque.",
    "Église de 1715 à nef unique de trois travées, chœur à chevet plat, décor peint néo-médiéval du milieu du XIXe siècle. Clocher-tour carré avec flèche de pierre et quatre pyramides.",
    "Elle conserve une « Vierge de Miséricorde » de Jacques Bottero (vers 1700), provenant du couvent des Dominicains de Barcelonnette, classée.",
    "Chapelle Sainte-Anne de Champcontier, citée sans date.",
    "Chapelle Saint-Paul de Costeplane, citée sans date.",
    "Nef haute de trois travées voûtées d'arêtes, avec une chapelle latérale à chaque travée ; chœur plus bas. De l'édifice précédent subsistent le clocher carré à flèche et quatre pyramides et le portail sud gothique (début du XVIe siècle). Cadran solaire de 1881, restauré en 1996.",
    "Chapelle Saint-Jean du hameau des Prats, près d'un moulin. Elle conserve le seul objet classé de la commune, un ciboire en argent du XVIIIe siècle.",
    "Chapelle Saint-Joseph de Miraval, citée sans date.",
    "Chapelle des Guérins, citée comme chapelle ouverte.",
    "Wikidata : « chapelle du Clot-Meyrans » (dédiée à saint Joseph selon l'article de la commune).",
    "Chapelle Saint-Jean de Peynier, l'une des chapelles succursales de la paroisse.",
    "Notre-Dame-de-la-Visitation, dite Notre-Dame-des-Lumières, à Rioclar : ancienne paroisse indépendante, de 1763. Nef de deux travées, clocher-tour, un Christ en bois du XVIe siècle.",
    "Ancien prieuré du Laverq, dépendant de Volonne et fondé en 1135, passé ensuite aux abbayes de Chalais et de Boscodon. Il reste un fragment de mur de la première construction ; l'église fut reconstruite au XVIIe siècle et rénovée au XIXe.",
    "Nef de deux travées, coupole sur le chœur, clocher-tour accolé à la façade ouest avec flèche de pierre à quatre pans.",
    "Orientation : le clocher est accolé à la façade ouest : abside à l'est, comme la mesure (82°).",
    "Église paroissiale de Revel. La façade porte une statuette gothique de saint Jacques de la fin du XVe siècle ; il reste des éléments gothiques et la chapelle nord, voûtée d'arêtes, du tournant des XVIe et XVIIe siècles.",
    "Ancienne église paroissiale de Saint-Barthélemy (Wikidata : « église Saint-Julien de Saint-Barthélemy »), citée sans date.",
    "Wikidata : « église Saint-Julien de Méolans ». L'article de la commune rappelle que l'église Saint-Julien d'origine a disparu et qu'il en reste le clocher du XVIe siècle, isolé sur un rocher (site classé en 1944). Le bâtiment cartographié est l'église ou chapelle actuelle.",
    "Chapelle de Chaudon du XVIIIe siècle : nef de deux travées voûtées d'arêtes, porte au sud et clocher-mur au-dessus de la façade ouest.",
    "Orientation : le clocher-mur au-dessus de la façade ouest indique l'abside à l'est. Le calcul automatique donnait le sens opposé (262°) : orientation corrigée à 82°.",
    "Chapelle Saint-Antoine-et-Saint-Roch de Rioclar-Bas, citée seulement dans une légende.",
    "Chapelle du hameau des Trons, citée seulement dans une légende.",
    "Paroisse secondaire créée à l'Adroit de Pontis parce que le relief rendait difficile l'accès au chef-lieu. Le portail en bois est sculpté à l'imitation de têtes de clous.",
    "Chapelle du hameau des Chappas (Wikidata : « chapelle Saint-Martin des Chappas »).",
    "Chapelle Saint-Pierre aux Hugues, l'une des deux chapelles de la commune.",
    "Église paroissiale du XIXe siècle, dédiée à saint Jérôme avec saint Pierre pour patron (Wikidata l'appelle « Saint-Joseph »). Rosace vitrée et cadran solaire récent en façade, clocher à quatre pyramides.",
    "Elle conserve un plat de quête en cuivre du XVIe siècle, classé en 1995, et deux tableaux (saint Jérôme, 1665 ; Vierge à l'Enfant, XVIIIe siècle) restaurés en 2013.",
    "Église de Maurin, au fond de la vallée vers les sources de l'Ubaye. Les hameaux isolés (La Barge, Maljasset, Combe-Brémond) obtinrent la paroisse en 1431 : auparavant, les habitants devaient descendre jusqu'à Serenne.",
    "Fondations du XIIe siècle ; détruite par une avalanche en 1531 et reconstruite (une inscription sur le tympan le rappelle). Nef de trois travées et chœur roman, portail en marbre rose. Retable et tableau de la Vierge du Rosaire (1654) classés ; le cimetière, avec ses chapiteaux et sa porte, est lui aussi protégé.",
    "Église de Mélézen de 1785. Une chapelle antérieure fut transformée en presbytère. Croix de procession du XVIIe siècle classée.",
    "Église gothique de Tournoux, du XIIIe siècle, aux voûtes plus récentes. Le clocher a une base romane et des étages des XVIe-XVIIe siècles à baies géminées. Un collatéral nord a été ajouté aux XVIIIe-XIXe siècles ; le portail a un linteau sur deux consoles sculptées (XVe-XVIe siècle). Elle conserve une Vierge du Rosaire.",
    "Ancienne paroissiale de Grande-Serenne (Wikidata : « église de la Transfiguration »), érigée en 1829 sur une construction antérieure. Plan en croix latine avec coupole. Le séisme de 1959 a tranché la pointe du clocher.",
    "Chapelle du hameau de Prads (Wikidata : Notre-Dame-des-Sept-Douleurs des Prats). Elle conserve un autel en bois sculpté du XVIIIe siècle classé ; elle dépendait de la paroisse du chef-lieu.",
    "Lieu de pèlerinage sur la route des cols vers le Piémont, bâti par les habitants à la fin du XVIIIe siècle ; clocher ajouté en 1819. La fresque du tympan reproduit une toile de Joseph-André Signoret et a été refaite en 1992.",
    "Chapelle Saint-Jacques de Gleizolles, dépendant de Tournoux. Dans les années 1980, il n'en restait que le chœur voûté d'ogives du début du XVIe siècle ; les habitants la reconstruisirent en 1988 en la limitant à l'ancien chevet.",
    "Wikidata : « chapelle Saint-Jean-Baptiste de Saint-Paul-sur-Ubaye » ; les sources consultées ne donnent pas d'autres informations.",
    "Église Saint-Jean-Baptiste de Fouillouse, entre Fouillouse et Les Serrets, reconstruite en 1549, avec une voûte en berceau brisé postérieure et un clocher-mur à trois baies. Le Christ sur poutre de gloire et un antependium en tapisserie sont classés. Fouillouse obtint la paroisse en 1534.",
    "Chapelle Saint-Roch de la Petite-Serenne.",
    "Chapelle du col de Vars, bâtie au milieu du XIXe siècle à la place d'un hospice pour les voyageurs.",
    "Chapelle Notre-Dame à l'Estrech, près des Bonis, dépendant de la paroisse du chef-lieu.",
    "Origines de la fin du Moyen Âge : la base du clocher (vers 1390) et une partie du chœur (1452-1472) sont les parties les plus anciennes. En 1591, les troupes de Lesdiguières la détruisirent alors que les habitants s'y étaient retranchés ; les voûtes ne furent reconstruites qu'en 1690, l'église fut fortifiée en 1696 et la toiture refaite en 1762.",
    "Le séisme du 5 avril 1959 fit s'effondrer une travée : les restaurations durèrent de 1963 à 1970. Nef de deux travées voûtées d'ogives, chœur à chevet plat, chapelle au sud, arcatures lombardes à l'extérieur. Le portail occidental date du début du XVIe siècle ; fresques du XVIe siècle par des peintres italiens.",
    "Orientation : portail occidental et chœur opposé : l'abside à l'ENE (63°) est cohérente avec les sources.",
    "Ancien prieuré bénédictin du XIIe siècle, reconstruit au XVIe : le chœur date du XVIe siècle, la nef de trois travées et la chapelle sud du XVIIe. Il conserve de rares bandes lombardes et un arc triomphal à chapiteaux historiés.",
    "Clocher-tour à flèche à six pans et gargouilles. Le portail occidental a trois voussures ; le portail sud a un linteau avec un Christ en majesté et une inscription gothique. Le tympan peint de l'Adoration des Mages (vers 1500) fut restauré en 1912.",
    "Orientation : chevet plat et aveugle, chœur éclairé seulement par le sud, portail principal à l'ouest : l'abside regarde vers l'est. Le calcul automatique donnait le sens opposé (283°) : orientation corrigée à 103°.",
    "Église du Lautaret, qui existait déjà quand elle devint paroisse au début du XIXe siècle.",
    "Église paroissiale de La Bréole, de 1581. En 1890, un legs permit de surélever le clocher d'environ 30 à 40 m. Vitraux contemporains, dont deux de 2013.",
    "Église de Saint-Vincent-les-Forts, du XVIe siècle, dédiée à saint Vincent de Saragosse : nef voûtée en berceau surbaissé et double abside désaxée. En 1690, les troupes piémontaises d'occupation s'y installèrent.",
    "Église Saint-Marcellin de Costebelle. Elle conserve un calice en argent de 1711 classé (Palissy PM04000852).",
    "Chapelle des Rollands, citée sans date.",
    "Église paroissiale du chef-lieu, Uvernet, de 1677.",
    "Chapelle contemporaine de la station de Pra-Loup, de style chalet, œuvre de Pommer, dédiée à saint François d'Assise.",
    "Ancienne église paroissiale des Agneliers, des XVIe-XVIIe siècles. Elle conserve trois tableaux classés provenant de la chapelle de Morjuan (Mise au tombeau, Vierge à l'Enfant, Dieu le Père).",
    "Maison-Méane, ancienne paroisse indépendante, fut détruite pendant la Seconde Guerre mondiale et reconstruite plus haut, près de la nouvelle route : la chapelle actuelle (1956 selon OSM) date de cette reconstruction.",
    "Église de Larche. Le village fut entièrement détruit par les combats de la Libération en avril 1945 puis reconstruit : l'édifice actuel appartient à la reconstruction (l'article de la commune cite des églises du XXe siècle dédiées à Notre-Dame-des-Neiges et à Saint-Pierre-ès-Liens).",
    "Église paroissiale de Meyronnes, du XIXe siècle, dédiée à saint Donat martyr (fête le 7 août).",
    "Chapelle du Vieux-Saint-Ours, à environ 1794 m, sur le site de la première chapelle, reconstruite à partir de 1860. Lieu de pèlerinage le 17 juin.",
    "Wikidata : « chapelle Sainte-Madeleine du col de Larche » ; les sources consultées ne donnent pas d'autres informations.",
    "Wikidata : « chapelle Notre-Dame-des-Lumières du Lauzanier », dans le vallon du Lauzanier ; les sources consultées ne donnent pas d'autres informations.",
    "Église de Saint-Ours (Wikidata : « église Saint-Ours de Saint-Ours »). La première chapelle, au nord du hameau, fut déplacée et reconstruite en 1773 au Plan de Saint-Ours, érigée en paroisse en 1833 et reconstruite après la dernière guerre.",
]
# inizio dei paragrafi italiani corrispondenti: genera_dati.py controlla
# l'abbinamento e segnala se i dati italiani sono cambiati
STORIA_IT_INIZIO = [
    "Chiesa medievale distrutta", "Del Seicento resta", "Wikidata la chiama", "Chiesa del hameau di La Conche",
    "Chiesa del villaggio", "Conserva il quadro", "Wikidata: «chapelle Saint-Jean du Villard»", "La voce del comune non cita",
    "Prima costruzione nell'XI", "Il campanile isolato", "Edificio vicino al campanile", "Chiesa del hameau di Lans",
    "Chiesa barocca di stile", "Il 21 aprile 1691", "Navata di quattro campate", "Orientamento: il diagnostico 2016",
    "Chiesa del hameau di Les Sanières", "Chiesa del Châtelard", "Orientamento: Il coro a catino", "Chiesa parrocchiale del capoluogo, del 1822",
    "Piccola cappella del comune", "Cappella Saint-Roch del Châtelard", "Cappella Sainte-Anne, alla confluenza", "Cappella dei Penitenti del Châtelard",
    "Chiesa del 1715", "Conserva una «Vergine della Misericordia»", "Cappella Sainte-Anne di Champcontier", "Cappella Saint-Paul di Costeplane",
    "Navata alta di tre campate", "Cappella Saint-Jean del hameau des Prats", "Cappella Saint-Joseph di Miraval", "Cappella dei Guérins",
    "Wikidata: «chapelle du Clot-Meyrans»", "Cappella Saint-Jean di Peynier", "Notre-Dame-de-la-Visitation", "Antico priorato di Laverq",
    "Navata di due campate, cupola", "Orientamento: Il campanile sta accanto", "Chiesa parrocchiale di Revel", "Antica chiesa parrocchiale di Saint-Barthélemy",
    "Wikidata: «église Saint-Julien de Méolans»", "Cappella di Chaudon", "Orientamento: Il campanile a vela", "Cappella Saint-Antoine-et-Saint-Roch",
    "Cappella del hameau des Trons", "Parrocchia secondaria", "Cappella del hameau des Chappas", "Cappella Saint-Pierre aux Hugues",
    "Chiesa parrocchiale del XIX secolo, dedicata a san Girolamo", "Conserva un piatto da questua", "Chiesa di Maurin", "Fondazioni del XII secolo",
    "Chiesa di Mélézen", "Chiesa gotica di Tournoux", "Antica parrocchiale di Grande-Serenne", "Cappella del hameau di Prads",
    "Luogo di pellegrinaggio", "Cappella Saint-Jacques di Gleizolles", "Wikidata: «chapelle Saint-Jean-Baptiste de Saint-Paul", "Chiesa Saint-Jean-Baptiste di Fouillouse",
    "Cappella Saint-Roch della Petite-Serenne", "Cappella del colle di Vars", "Cappella Notre-Dame all'Estrech", "Origini tardomedievali",
    "Il terremoto del 5 aprile 1959", "Orientamento: Portale occidentale", "Antico priorato benedettino", "Campanile a torre con guglia a sei facce",
    "Orientamento: Chevet piatto", "Chiesa del Lautaret", "Chiesa parrocchiale di La Bréole", "Chiesa di Saint-Vincent-les-Forts",
    "Chiesa Saint-Marcellin di Costebelle", "Cappella dei Rollands", "Chiesa parrocchiale del capoluogo, Uvernet", "Cappella contemporanea",
    "Antica chiesa parrocchiale dei Agneliers", "Maison-Méane", "Chiesa di Larche", "Chiesa parrocchiale di Meyronnes",
    "Cappella del Vieux-Saint-Ours", "Wikidata: «chapelle Sainte-Madeleine", "Wikidata: «chapelle Notre-Dame-des-Lumières", "Chiesa di Saint-Ours",
]
assert len(_STORIA_FR) == len(STORIA_IT_INIZIO) == 84

_STORIA: dict[str, str] = {}   # testo italiano completo -> francese, riempito da abbina_storia()


def abbina_storia(paragrafi_it: list[str]) -> list[str]:
    """Abbina i paragrafi italiani (ordine di storia_fonti.json) ai francesi;
    restituisce l'elenco dei paragrafi che non trovano una traduzione."""
    senza = []
    for p in paragrafi_it:
        for inizio, fr_ in zip(STORIA_IT_INIZIO, _STORIA_FR):
            if p.startswith(inizio):
                _STORIA[p] = fr_
                break
        else:
            senza.append(p)
    return senza


_RE = [
    # Monumento storico, classificata nel 1921 (PA00080407) / iscritta 2016 / classificata il 31/10/1912
    (re.compile(r"^Monumento storico, classificata nel (\d{4}) \((\w+)\)$"), lambda m: f"Monument historique, classé en {m[1]} ({m[2]})"),
    (re.compile(r"^Monumento storico, iscritta (\d{4}) \((\w+)\)$"), lambda m: f"Monument historique, inscrit en {m[1]} ({m[2]})"),
    (re.compile(r"^Monumento storico, classificata il ([\d/]+) \((\w+)\)$"), lambda m: f"Monument historique, classé le {m[1]} ({m[2]})"),
    # pendio: 3° verso 179°; asse quasi lungo il pendio (8°)
    (re.compile(r"^(\d+)° verso (\d+)°; asse (quasi lungo il pendio|quasi di traverso al pendio|obliquo al pendio) \((\d+)°\)$"),
     lambda m: f"{m[1]}° vers {m[2]}° ; axe {_PENDIO[m[3]]} ({m[4]}°)"),
    # ~1870 (OSM), 1969 (OSM)
    (re.compile(r"^(~?\d{4}) \(OSM\)$"), lambda m: f"{m[1]} (OSM)"),
    (re.compile(r"^\d{4}$"), lambda m: m[0]),
    # verifica: confermato: abside semicircolare a NNW
    (re.compile(r"^confermato: (abside|testata) (semicircolare|arrotondata|poligonale) a (\w+)$"),
     lambda m: f"confirmé : {_FORMA[(m[1], m[2])]} vers le {_DIR.get(m[3], m[3])}"),
    (re.compile(r"^CORRETTO \(calcolo automatico (\d+)°\): (abside|testata) (semicircolare|arrotondata|poligonale) a (\w+)$"),
     lambda m: f"CORRIGÉ (calcul automatique {m[1]}°) : {_FORMA[(m[2], m[3])]} vers le {_DIR.get(m[4], m[4])}"),
    (re.compile(r"^confermato dalle fonti: (.+)$"), lambda m: "confirmé par les sources : " + _orient(m[1])),
    (re.compile(r"^CORRETTO DA FONTI \(calcolo automatico (\d+)°\): (.+)$"),
     lambda m: f"CORRIGÉ PAR LES SOURCES (calcul automatique {m[1]}°) : " + _orient(m[2])),
    # fonti
    (re.compile(r"^OpenStreetMap (way/\d+) \(pianta\)$"), lambda m: f"OpenStreetMap {m[1]} (plan)"),
    (re.compile(r"^Mérimée (\w+) \(POP, Ministero della Cultura\)$"), lambda m: f"Mérimée {m[1]} (POP, ministère de la Culture)"),
    (re.compile(r"^(Wikipedia \(fr\):|Wikidata) .*$"), lambda m: m[0]),
    (re.compile(r"^OpenStreetMap way \d+$"), lambda m: m[0]),
]


def _orient(testo_it: str) -> str:
    """La parte dopo «confermato dalle fonti:» e' il paragrafo «Orientamento: ...»."""
    t = _STORIA.get("Orientamento: " + testo_it)
    if t:
        return t.split(" : ", 1)[1] if t.startswith("Orientation : ") else t
    MANCANTI.append(testo_it)
    return testo_it


def fr(s):
    if not isinstance(s, str) or not s:
        return s
    if s in _STORIA:
        return _STORIA[s]
    if s in _ESATTI:
        return _ESATTI[s]
    for r, f in _RE:
        m = r.match(s)
        if m:
            return f(m)
    MANCANTI.append(s)
    return s
