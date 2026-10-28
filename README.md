# Jausiers — version française, sans Python (HTML/JavaScript)

Version française de l'application (modèle 3D de l'église
Saint-Nicolas-de-Myre avec projection solaire en temps réel),
identique à la version italienne dans son fonctionnement, fonctionnant
dans **n'importe quel navigateur** (Chrome, Edge, Firefox) **sans
installer Python, Node.js ou autre chose**.

## Utilisation

1. Extrayez tous les fichiers dans un dossier (ils doivent rester
   ensemble, dans le même dossier — ne déplacez pas `index.html`
   seul).
2. Double-cliquez sur **`index.html`**. L'application s'ouvre dans le
   navigateur par défaut et démarre immédiatement.

Aucune connexion internet n'est nécessaire : toutes les bibliothèques
(Three.js) et les photos sont incluses dans les fichiers eux-mêmes
(les photos sont intégrées en base64 dans `photos-data.js`, ~1,5 Mo).

## Commandes

- **Glisser (clic gauche)** — fait pivoter la vue
- **Glisser (clic droit)** — déplace la vue (pan)
- **Molette** — zoom
- **Curseurs "Jour de l'année"** et **"Heure locale"** — changent la
  date et l'heure ; la scène se met à jour en temps réel
- **Touches 1 / 2 / 3** — solstice d'hiver / équinoxe / solstice d'été
  (année 2026)
- **Touches N / S / E / O** — vue depuis le Nord / Sud / Est / Ouest
- **Touche T** — vue de dessus (plan)
- **Touche R** — vue axonométrique par défaut
- **Barre d'espace** — démarre/arrête l'animation (fait défiler
  l'heure)
- **Case à cocher "Afficher les photos"** — affiche/masque les
  panneaux photographiques

## Corrections géométriques issues d'un relevé direct (dernière mise à jour)

**VRAI BUG TROUVÉ** : sens d'enroulement (winding) inversé dans
l'éventail du toit — présent depuis la toute première tentative en
pavillon. Les angles des points du contour par rapport au centroïde
n'étaient pas monotones (rompant la condition "en étoile"),
produisant des triangles avec des normales tournées vers l'intérieur
au lieu de l'extérieur. Confirmé en activant le backface culling : la
majorité du toit disparaissait. Construction séparée en éventail-
pentagone (vérifié en étoile valide) + 2 triangles de raccord, avec
le bon sens. Vérifié par calcul direct des normales : les 7 triangles
du toit sont maintenant correctement orientés vers le haut.

**Vrais panneaux rectangulaires pour les pans 1 et 5** (plus de
fines bandes) : confirmé par capture d'écran que le vide près du
clocher était encore visible - les bandes de 10 cm n'étaient pas
suffisantes. Remplacées par de vrais panneaux rectangulaires
couvrant tout le pan 1/5, de la bouche au premier/dernier sommet du
pentagone, du mur (15,69 m) à la hauteur du clocher (19,85 m).
Vérifié visuellement : couverture solide, aucun vide résiduel.

**Correction de la vraie cause du vide dans le toit** : le mur et le
toit étaient des objets séparés fusionnés avec merge(), qui bien que
partageant la même position physique étaient deux points distincts -
avec la transparence réelle de l'app (opacité 0,4) de minuscules
écarts en virgule flottante laissaient un vide visible (on voyait à
travers le toit jusqu'à la photo intérieure). Réécrit comme un seul
objet avec un unique tableau de points partagé. Correspondance
numérique exacte entre Python et JavaScript vérifiée (25 points, 19
bords de frontière).

**Fermeture du vide entre l'abside et le clocher** : signalé par une
capture d'écran près du faîte du toit absidal. Le maillage de
l'abside seul était parfaitement fermé - le problème se situait à la
jonction avec le clocher (structures séparées, à fleur avec une
tolérance minimale et un dénivelé de hauteur). Ajout d'un panneau de
raccord vertical chevauchant (5 cm) aux deux angles de la "bouche",
même stratégie déjà utilisée avec succès pour les niches des
chapelles.

**Toit de l'abside : pavillon symétrique** (confirmé par une photo
réelle de l'église vue de derrière) : les 5 pans convergent vers un
seul faîte central, comme un petit cône — plus la structure
asymétrique d'une tentative précédente (lecture erronée des cotes du
plan). Retour à la construction la plus simple : éventail depuis le
centroïde du pentagone, avant-toit constant à 15,69 m, faîte à
19,85 m. Vérifié par analyse des bords de frontière et comparaison
directe avec la photo.

**Toit de l'abside : pavillon symétrique** (confirmé par une photo
réelle de l'église vue de derrière) : les 5 pans convergent vers un
seul faîte central, comme un petit cône — plus la structure
asymétrique d'une tentative précédente (mauvaise lecture des cotes du
plan). Retour à la construction la plus simple : éventail depuis le
centroïde du pentagone, gouttière constante à 15,69 m, faîte à
19,85 m. Vérifié par analyse des bords de frontière et comparaison
directe avec la photo.

**Correction du vrai bug : le toit était déconnecté du mur** ("il
n'y en avait pas"). Double cause : (1) les pièces du toit étaient
fusionnées avec `merge()`, qui ne dédupliquait pas correctement les
points coïncidents, laissant les pans 1/5 complètement déconnectés ;
(2) le mur reliait directement pentagone[0]-pentagone[1], tandis que
le toit passe par un point intermédiaire à mi-chemin — un
désalignement topologique. Résolu en construisant toute la structure
comme un seul objet avec un unique tableau de points partagé. Vérifié
par analyse des bords de frontière : seuls ceux architecturalement
attendus restent ouverts.

**Toit de l'abside à 5 pans** (plus une pente unique) : l'utilisateur
a précisé la vraie structure — pans 1 et 5 (près du clocher)
triangulaires, descendent abruptement de 19,85 m à 15,69 m sur
seulement 2,31 m ; pans 2,3,4 (corps central) plats de là jusqu'à la
pointe extérieure. Un bug préexistant également trouvé et corrigé :
le mur se refermait toujours sur la "bouche" absidale au lieu de
rester ouvert vers la nef.

**Correction également du toit de l'abside** : même défaut "en
éventail" que le toit de la nef (éventail depuis un seul sommet, au
lieu du vrai plan incliné lisse). Résolu en exploitant la symétrie du
pentagone : le toit est maintenant construit comme des quadrilatères
reliant le côté Ouest du contour au côté Est symétrique, sans aucun
point de convergence. Vérifié visuellement et numériquement.

**Correction du VRAI toit principal** : c'était une pyramide à 4
pans (un éventail depuis un point central vers tous les coins du
rectangle), pas un vrai toit à deux pans. Réécrit avec un vrai
faîte linéaire et seulement deux pans rectangulaires + deux pignons
triangulaires aux extrémités façade/abside, comme le montrent les
plans. Vérifié visuellement (vue du dessus et de face) et
numériquement (limites identiques aux murs, aucun débordement dans
l'abside).

**Correction d'un vrai bug de triangulation** : le toit de l'abside
avait un dernier triangle parasite reliant les deux côtés de la
"bouche" absidale (où elle s'ouvre vers la nef) avec un bouchon plat
à la hauteur maximale (19,85 m) — cause probable de l'aspect "toit
ouvert vers le haut" et de "mur trop haut" signalés par l'utilisateur.
La valeur du mur (15,69 m) a été confirmée correcte par l'utilisateur.
Triangle parasite supprimé — la bouche est maintenant ouverte vers la
nef comme elle doit l'être.

**Correction du vrai coupable des problèmes "trop haut"/"ne ferme
pas" de l'abside** : ce n'était pas le maillage extérieur (déjà
corrigé), mais le **panneau photo courbe intérieur** de l'abside,
avec deux bugs résiduels datant d'avant que l'abside ait sa propre
hauteur — hauteur calculée à partir du mur de la nef au lieu de
celui de l'abside (16,0 m au lieu de 15,13 m), et contour ne
couvrant que le pentagone sans les deux tronçons de raccord vers la
nef (laissant un vide près du clocher). Les deux corrigés — limites
maintenant identiques à la structure solide.

**Affinement final du toit de l'abside** : point haut = faîte du toit
de la nef (23,38 m) − 3,53 m = 19,85 m exacts (était 19,84 m,
dérivation précédente). Montée mise à jour à 4,16 m. Suppression
d'une constante résiduelle inutilisée (faîte plat, remplacé par la
pente unique).

**Toit de l'abside en pente unique** (plus en pavillon) : confirmé
par l'utilisateur en comparant avec le plan technique — monte de
15,69 m (pointe extérieure du pentagone) à 19,84 m (là où il rejoint
la nef), comme un simple prolongement incliné plutôt qu'une structure
en pavillon autonome. Mur à hauteur constante inchangé.

**Remplissages entre les chapelles** : atteignent maintenant le vrai
toit incliné (9,64-10,95 m) et sont transparents comme les murs
(0,28, était 0,9). **Projection de la lumière dans les chapelles/
l'abside corrigée** : utilisait une hauteur de mur uniforme (16,56 m)
partout, causant des taches de lumière segmentées quand un vitrail
de claire-voie projetait au-dessus du vrai toit (plus bas) d'une
niche. La hauteur est maintenant calculée pour chaque point du
périmètre selon la zone réelle - vérifié avec un balayage étendu
(2176 combinaisons, zéro erreur).

**Remplissages entre les chapelles maintenant SAILLANTS** (plus au
nu du mur) : le problème n'était pas un vide dans le maillage, mais
un RETRAIT visible de l'extérieur — le mur noyau, correct mais en
retrait par rapport aux chapelles saillantes, apparaissait comme un
creux. Les remplissages font maintenant saillie à la même profondeur
que les niches (2,19 m), sur les 5 tronçons par côté : tout le flanc
de l'église apparaît comme un seul volume saillant continu — vérifié
visuellement avec des couleurs distinctes.

**Bande solide continue sur toute la longueur** (pas seulement entre
les chapelles) : le vide était encore visible après la version "à
piliers" (limitée aux seuls tronçons vides). Remplacée par une bande
continue sur toute la longueur des deux côtés, volontairement
redondante avec les niches elles-mêmes, qui élimine toute possibilité
de vide par construction - vérifié visuellement avec une couleur
distincte.

**Toit de l'abside en pavillon** (plus une pyramide à pointe unique,
qui paraissait visuellement trop haute/pointue) : deux points de
faîte séparés de 2,31 m, orientés le long de l'axe de la nef.
**Piliers solides** ajoutés entre chaque paire de niches adjacentes
(opacité 0,9), pour garantir que cette zone se lise toujours comme de
la maçonnerie pleine - vérifié visuellement qu'ils remplissent
exactement l'espace indiqué par l'utilisateur comme "vide".

**Chevauchement défensif niches/mur noyau** : le vide signalé par
l'utilisateur s'avérait géométriquement absent dans les tests isolés
(mur noyau continu avec couleurs distinctes) - cause exacte non
confirmée avec certitude (probablement liée aux panneaux photo, qui
commencent à 0,5 m du sol). Un chevauchement réel de 5 cm a été
appliqué entre chaque niche et le mur noyau (au lieu d'une simple
coïncidence de plans), éliminant toute cause possible de z-fighting
indépendamment du mécanisme exact.

**Point ouvert** : de nouvelles cotes trouvées sur une version mise à
jour du plan (bleu 3,53 m, noir 7,85 m) ne sont pas encore
interprétées pour l'abside - la demande de relire toutes les mesures
extérieures de l'abside reste partiellement en suspens.

**Nouveau contrôle "Afficher les vitraux"** : ajout d'une seconde case
à cocher, semblable à "Afficher les photos", qui masque/affiche les
maillages pleins des 17 vitraux (chapelles, abside, façade)
indépendamment des photos et des taches de lumière - utile pour
inspecter la structure du bâtiment.

**Espace visuel entre les chapelles résolu** (bug de z-fighting) :
les panneaux de liaison ajoutés précédemment entre les niches étaient
exactement dans le même plan que le mur noyau de la nef, causant un
z-fighting qui faisait disparaître les deux surfaces sous certains
angles. Le mur noyau couvre déjà seul avec continuité tout l'espace
entre une niche et la suivante — les panneaux étaient redondants,
supprimés.

**Confirmation croisée du toit de l'abside** : confirmé que le vert
(4,15 m) indique la montée du toit de l'abside au-dessus du mur - cela
coïncide presque exactement avec la valeur dérivée précédemment
(19,85−15,69=4,16 m). Les trois mesures indépendantes (total 19,85,
mur 15,69, toit 4,15) se confirment maintenant mutuellement.

**Hauteur de l'abside corrigée** (elle était trop haute) : la valeur
"orange" (19,85 m) n'était pas la hauteur du mur extérieur de
l'abside, mais la hauteur du FAÎTE du toit. La vraie hauteur du mur
est la valeur "cyan" (15,69 m). Corrigé : APSE_EXTERNAL_HEIGHT_M
19,85→15,69 m, APSE_ROOF_RIDGE_RISE_M 2,51→4,16 m (le total reste
19,85 m, mais maintenant correctement proportionné — le mur de
l'abside est juste en dessous de celui de la nef, 16,56 m, au lieu de
le dépasser).

**Photo réelle de la façade extérieure** : remplacement de l'ancienne
photo intérieure de l'entrée par une photo réelle de la façade
EXTÉRIEURE (fond déjà supprimé), fixée à l'extérieur du mur au lieu de
l'intérieur. Dimensions (15,93 × 22,94 m) calculées à partir des
pixels de la photo elle-même, en utilisant comme référence la hauteur
connue du mur/toit dans le modèle. Un bug trouvé et corrigé pendant la
vérification : le texte des cadrans solaires apparaissait en miroir à
cause d'une erreur de signe dans l'orientation "minus_u" des panneaux
photo plats.

**Abside avec sa propre hauteur extérieure** (19,85 m + toiture en
pavillon jusqu'à 22,36 m, au lieu d'hériter des 16,56 m de la nef) et
**mur bas continu entre les niches des chapelles** (comblait un vide
visuel qui apparaissait auparavant entre une niche et la suivante, au
niveau du toit bas).

**Panneaux de liaison entre les niches des chapelles** (mur bas continu
entre une chapelle et la suivante, au lieu du vide visuel précédent)
et **abside avec sa propre hauteur externe** (19,85 m + toit en pavillon
jusqu'à 22,36 m, au lieu d'hériter des 16,56 m de la nef). Note : la
valeur de montée du toit absidal (2,51 m, indiquée par l'utilisateur)
diffère légèrement de ma lecture pixel du document (2,31 m) - la
première a été utilisée, avec la divergence signalée.

**Mur haut vraiment coupé au-dessus des 8 niches des chapelles** : le
toit bas n'était qu'un plan visuel superposé - le mur haut continuait
à monter jusqu'à 16,56 m même là, "perçant" le toit par derrière.
Le mur haut est maintenant construit uniquement sur le "noyau" nef+
abside (sans les niches saillantes), et les 8 niches sont des
structures séparées qui s'arrêtent vraiment à la hauteur du toit bas
(9,64-10,95 m).

**Pente du toit bas des chapelles mesurée** (1,31 m, repérée grâce à
une flèche cyan sur "Elevation Sud" indiquant où le mur extérieur de
la chapelle rencontre le mur haut de la nef) - remplace une estimation
précédente (1,2 m). Le toit monte maintenant de 9,64 m (égout) à
10,95 m.

**Vitraux des chapelles déplacés sur le mur de la nef** (fenêtres de
claire-voie, plus sur la paroi de fond de la niche) : l'appui
(11,18 m) était au-dessus de l'égout du toit bas des chapelles
(9,64 m), et sur la paroi de la niche les vitraux se retrouvaient
coupés par le toit, paraissant trop hauts et déconnectés de
l'architecture. En conséquence, le retrait de 1,31 m introduit
précédemment a aussi été retiré (plus valide à cette position). Le
**portail** utilise maintenant un groupe dédié avec la couleur/
opacité des murs et est exclu du calcul de la lumière solaire (ne
laisse pas passer la lumière).

À partir de quatre plans officiels de l'architecte (Michel Trubert
ACMH, "Diagnostic - Etat des lieux", 09/2016 — plan 1/200, élévations
Sud et Est 1/100), de nombreuses cotes auparavant seulement estimées
ont été corrigées : longueur/largeur de la nef, profondeur réelle des
niches des chapelles (2,19 m, bien plus que l'estimation précédente
de 0,38 m), dimensions et hauteur de tous les vitraux, ajout du
portail d'entrée, du clocher (corps + flèche, ~35,5 m au total), un
toit bas séparé au-dessus des chapelles (égout à 9,64 m, auparavant
défini mais jamais utilisé dans le maillage) et le narthex/vestibule
couvert au-dessus du portail (structure solide qui ne laisse pas
passer la lumière, avec un plafond à profil courbe de 6,58 m à
4,49 m). Voir les commentaires dans `church-geometry.js` pour la
provenance exacte (mesurée/dérivée/estimée) de chaque cote.

La position du clocher (côté "Ouest" du modèle, adjacent à "Chapelle
Notre-Dame-du-Rosaire") a été corrigée par l'utilisateur après une
erreur de lecture initiale du plan.

## Version pour téléphone/tablette

L'application s'adapte automatiquement aux écrans étroits (téléphones,
tablettes en portrait) :

- Le panneau latéral devient un **tiroir escamotable** : touchez
  l'icône &#9776; en haut à gauche pour l'ouvrir, touchez en dehors
  pour le fermer. La scène 3D reste toujours en plein écran.
- **Contrôles tactiles complets** : un doigt pour tourner, deux
  doigts pour déplacer la vue (pan) ou zoomer avec le geste de
  pincement (pinch-to-zoom) — même comportement que la souris
  (gauche=tourner, droit=pan, molette=zoom), vérifié avec de vrais
  gestes multi-touch simulés.
- **Photos recompressées pour une consommation mémoire bien plus
  faible** : 800px de côté maximum, qualité réduite. Le fichier qui
  les contient toutes est passé de 1,57 Mo à environ 320 Ko, et la
  mémoire vidéo réellement utilisée (qui dépend des pixels décodés,
  pas du poids du fichier compressé) est passée d'environ 11 Mo à
  environ 6 Mo.
- **Résolution d'écran limitée** (`devicePixelRatio` maximum 2) et
  **antialiasing désactivé sur les appareils tactiles** : les deux
  réduisent la charge sur la carte graphique, utile sur téléphones et
  ordinateurs moins récents.

## Construction et vérification

Chaque module Python a été reporté 1:1 en JavaScript et **vérifié
numériquement par rapport à la sortie Python originale** avant d'être
intégré : position solaire, géométrie de l'église, maillage 3D,
projection de la lumière sur sol/murs — correspondance exacte ou à la
précision des nombres flottants près sur tous les cas testés, y
compris 1024 combinaisons date/heure/fenêtre.

**Note sur les noms des vitraux** : les noms utilisés dans la liste
"Vitraux éclairés" (`Chapelle X (Ouest/Est)`, `Abside - ...`,
`Façade - ...`) sont aussi utilisés en interne comme clés pour associer
chaque vitrail à sa photo réelle — ils ont été traduits de façon
cohérente dans `church-geometry.js` ET `reference-photos.js`
simultanément et revérifiés (16 vitraux, 8 superpositions photo)
pour garantir qu'aucune correspondance ne se perde dans la
traduction.

**Note sur les contrôles de caméra** : la bibliothèque officielle
`THREE.OrbitControls` n'est distribuée qu'en module ES, que Chrome/
Edge bloquent par sécurité (CORS) quand une page est ouverte par
double-clic plutôt que via un serveur web. Les contrôles de rotation/
zoom/déplacement ont donc été réécrits dans `orbit-controls-lite.js`.
Un bug d'amplification du déplacement (pan, environ 12x) a été
détecté pendant les tests de la version originale et corrigé dans
cette version également.

## Limites connues

- Le rendu (WebGL via Three.js) est visuellement très proche de celui
  de PyVista/VTK (version Python) mais pas identique pixel par pixel.

## En cas de problème

Si `index.html` reste vide ou bloqué sur "Chargement du modèle
3D..." :
- Vérifiez que TOUS les fichiers sont dans le MÊME dossier (en
  particulier `three.min.js`, `photos-data.js` et tous les fichiers
  `.js` à côté de `index.html`).
- Essayez un autre navigateur (Chrome ou Edge à jour recommandés).
- Ouvrez la Console développeur (F12) pour voir d'éventuelles erreurs.
