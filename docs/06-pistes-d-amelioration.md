# 06 — Pistes d'amélioration

Les idées sont classées par thème, avec une estimation de l'effort :

- **S** : quelques heures, une ou deux fonctions ;
- **M** : une à deux journées, plusieurs fichiers ;
- **L** : plusieurs jours, nouvelle partie de l'app ;
- **XL** : un projet en soi.

Ces estimations supposent le code actuel ; elles n'ont pas été vérifiées en le faisant.

**Ordre conseillé** : d'abord mesurer la fluidité sur téléphone (sans ça, tout ajout de
contenu est un pari), puis le mode « Cacher mes canards » (le meilleur rapport plaisir /
effort, il réutilise presque tout), puis les niveaux de difficulté.

---

## 1. Mode « Cacher mes canards » (défi entre amis)

**L'idée** : un joueur cache lui-même ses canards dans une ville, puis envoie un lien ; son
ami doit les retrouver.

**La règle d'or** : les canards cachés doivent **toujours rester trouvables**. Le joueur
qui cache ne doit pas pouvoir les rendre invisibles, sinon le défi devient injuste et le jeu
perd son sens.

### Comment garantir que les canards restent visibles

Le générateur le sait déjà. Pour chaque ville, `place_objets.py` mesure entre 2 000 et
3 500 cachettes possibles, chacune avec :

- sa **visibilité** (part du canard que la caméra voit, de 0 à 1) ;
- une **orientation** qui montre le bec et un œil à la caméra, ou rien si c'est impossible ;
- son lieu (`sol`, `balcon`, `toit`, `vitre`) et sa case de la grille.

Aujourd'hui, il n'en garde que 300 (30 canards et 270 leurres). Il suffit d'écrire **toutes
les cachettes valables** dans un fichier `cachettes.json`. Le mode « Cacher » ne propose
alors que celles-là : on ne peut poser un canard que là où il est garanti visible.

Règles proposées pour qu'une cachette soit autorisée :

| Règle | Pourquoi |
|---|---|
| Visibilité ≥ 0,3 | Assez de canard à l'écran pour le repérer |
| Bec et un œil visibles (orientation trouvée) | Sinon on ne peut pas le distinguer d'un leurre, même de près |
| À plus de 2 m d'un autre canard caché | Deux canards collés se trouvent ensemble |
| Pas à moins de 1 m d'un leurre | Éviter deux objets jaunes qui se chevauchent (le leurre gênant est retiré) |

Le joueur choisit combien de canards cacher (par exemple 5, 10 ou 30).

### Déroulé côté joueur

1. Menu → « Cacher mes canards » → choix de la ville et du nombre de canards.
2. La ville s'affiche ; en zoomant, des repères discrets montrent les cachettes possibles
   (ou bien : le joueur tape où il veut, et le jeu « aimante » le canard sur la cachette
   valable la plus proche, en expliquant sinon : « trop caché ici », « on ne verrait pas
   sa tête »).
3. Chaque canard posé apparaît ; on peut le retirer d'un tap.
4. « Partager » produit un lien du type
   `…/jeu-canard-3d/#defi=paris.3.AAEC…`, à envoyer par message.
5. L'ami ouvre le lien : c'est une partie normale, avec les canards de son ami à la place
   des 30 canards habituels, et à la fin « Défi de Camille réussi en 4:12 ».

### Pourquoi c'est faisable rapidement

- Le lien est court : la ville, sa version, et les **numéros** des cachettes choisies
  (2 octets par canard : 30 canards tiennent en environ 80 caractères).
- La `version` dans le lien protège contre une ville régénérée entre-temps : si les
  numéros ne correspondent plus, le jeu le dit au lieu de cacher des canards n'importe où.
- Pas de serveur : tout tient dans le lien.
- Le reste de la partie (zoom, révélation, tap, chrono, écran de fin) est déjà là.

| Morceau | Effort |
|---|---|
| Écrire `cachettes.json` dans `place_objets.py` (~150 Ko par ville) | S |
| Encoder et décoder le lien de défi, tests | S |
| Charger un défi au lieu des canards habituels | S |
| Écran « Cacher » : poser, retirer, compteur, bouton partager | M |
| **Total** | **M à L** |

### Variante plus libre (plus tard)

Laisser poser un canard **n'importe où**, en mesurant la visibilité directement dans le
navigateur (les mêmes 27 rayons qu'aujourd'hui dans Blender, avec Three.js et la
bibliothèque `three-mesh-bvh` pour que ce soit rapide). Plus libre, mais plus lourd (**L**)
et plus risqué : les règles ci-dessus restent obligatoires.

---

## 2. Mode « Créer mon monde »

Trois niveaux d'ambition, du plus simple au plus libre.

### Niveau 1 — Configurateur de ville (M)

Une page de l'app avec des curseurs et des listes (taille, étages, toits, couleurs, foule,
saynètes, graine…) qui fabrique le fichier de thème et montre en direct les erreurs de
validation. Le fichier est ensuite téléchargé, puis généré **sur l'ordinateur** avec
Blender comme aujourd'hui.

- Avantage : rapide, sans risque, rend la création de villes accessible sans éditer de JSON.
- Limite : il faut toujours Blender et une publication pour jouer la ville.

### Niveau 2 — Génération dans le navigateur (L à XL)

Le joueur règle sa ville et **joue immédiatement**, sur téléphone, sans Blender.

C'est possible parce que le générateur est déjà en Python pur, sans Blender (`layout.py`,
`placement.py`, `maillage.py`, environ 1 300 lignes) et que tous les modèles sont déjà
dans `kit.glb` et `props.glb`. Il faut :

1. faire tourner le générateur dans le navigateur, soit en le **traduisant en JavaScript**,
   soit avec **Pyodide** (Python dans le navigateur, environ 10 Mo à télécharger en plus,
   mais le code reste tel quel) ;
2. refaire la **mesure de visibilité** (aujourd'hui des rayons dans Blender) avec
   Three.js et `three-mesh-bvh` ;
3. construire le bâti directement dans Three.js à partir des primitives.

Bonus : une ville se partage alors par un lien très court (le thème modifié et la graine),
et un **« défi du jour »** devient possible (une graine par date, la même pour tout le monde).

### Niveau 3 — Éditeur libre (XL)

Poser soi-même immeubles, arbres, véhicules, passants et saynètes sur une grille, à la
souris ou au doigt, avec annuler/refaire, puis cacher ses canards (mode 1).

- Le format existe presque : `decor.json` est déjà une liste d'objets posés (type,
  position, angle, couleurs). Il manque un format équivalent pour le bâti (immeubles
  paramétrés plutôt que primitives).
- La difficulté est surtout l'ergonomie tactile (sélectionner, déplacer, tourner un objet
  sur un téléphone) et le stockage : une ville éditée ne tient pas dans un lien, il faut
  la sauvegarder sur l'appareil ou l'exporter en fichier.
- Garde-fou indispensable : la vérification de visibilité du mode 1 s'applique aux
  canards, quel que soit le décor construit.

**Conseil** : faire le niveau 1, puis le mode « Cacher mes canards » ; n'attaquer les
niveaux 2 et 3 qu'une fois le jeu validé par des joueurs.

---

## 3. Augmenter la complexité et la rejouabilité

| Idée | Comment | Effort |
|---|---|---|
| **Niveaux de difficulté** (facile, normal, expert) | Côté app : seuil de révélation `PX_REVELATION`, nombre de canards à trouver (15 / 30), tolérance du tap. Côté génération : une variante par niveau (taille des objets, nombre de leurres, visibilité) | S (app) à M (génération) |
| **Contre-la-montre** | Temps limité affiché à rebours ; fin de partie au temps écoulé | S |
| **Taps limités** | Un nombre de taps maximal : chaque tap raté compte vraiment | S |
| **Meilleurs temps** | Record par ville gardé sur l'appareil, affiché sur l'écran de fin et sur l'accueil | S |
| **Image de partage** | Une vignette de la ville dans les aperçus de lien (balises Open Graph) et une image du score à partager | S à M |
| **Indices** | Après un certain temps, montrer la case de la grille où reste un canard (`zone` est déjà dans `placements.json`) | S |
| **Canard doré** | Un canard rare et très bien caché, qui donne un bonus | S à M |
| **Faux canards** | Leurre en forme de canard sans bec (ou un canard d'une autre couleur) : il faut vraiment regarder le bec | S |
| **Canards qui bougent** | Un canard sur la tête d'un passant qui marche, sur un bus qui roule | L : il faut animer des objets, aujourd'hui tout est immobile |
| **Nuit** | Ville sombre, lampadaires et fenêtres allumés, canards cachés dans les zones d'ombre | M |
| **Météo et saisons** | Neige sur les toits, parapluies jaunes partout, feuilles d'automne | M |
| **Caméra orientable** (4 angles) | Les canards cachés d'un côté ne se voient que d'un autre angle | XL : il faut détailler les quatre façades et mesurer la visibilité pour chaque angle |
| **Plus de villes** | Tokyo, Rio, Marrakech : un thème suffit si le bâti est proche des styles existants. Venise (canaux) ou un front de mer demandent une nouvelle forme de carte | S par ville simple ; L pour une nouvelle forme |
| **Classement en ligne** | Partager son temps avec d'autres joueurs | L : il faut un serveur |

---

## 4. Qualité, confort et technique

| Idée | Pourquoi | Effort |
|---|---|---|
| **Mesurer la fluidité sur téléphone** | Jamais fait ; tout le reste en dépend. Ajouter un affichage des images par seconde avec `?debug` dans l'adresse | S |
| **Compresser les modèles** (Meshopt ou Draco) | Le site pèse environ 16 Mo : long en 4G | S à M |
| **Niveaux de détail** | Passants et arbres simplifiés en vue d'ensemble | M |
| **Application installable, hors ligne** (PWA) | Icône sur l'écran d'accueil, jeu sans réseau | S |
| **Plus de sons** | Le « coinnn » et la vibration existent ; manquent une ambiance de ville, un son de tap raté, une fanfare de fin. Ou remplacer le cri synthétisé par un enregistrement libre de droits | S |
| **Daltonisme** | Un canard trouvé passe au vert : ajouter aussi un signe (coche) | S |
| **Test de bout en bout** | Aujourd'hui, l'affichage et les gestes ne sont testés qu'à la main ; un test automatique (Playwright) pourrait jouer une partie à chaque publication | M |
| **Bundle plus léger** | Le code de l'app fait 630 Ko (Three.js surtout) ; découpage possible | S |

---

## Limites connues aujourd'hui

- Fluidité sur téléphone et tablette jamais mesurée.
- Aucune partie complète jouée pour régler la difficulté.
- Les images de `docs/previews/` n'ont ni traits d'encre ni toutes les couleurs.
- Les tags ne vont que sur les bandeaux entre étages et sur les rideaux de fer.
- Les saynètes de rue sont à l'étroit (trottoirs de 2 à 2,5 m).
- Rien ne bouge : passants, animaux et véhicules sont immobiles.
- Une ou deux cases par ville ont parfois un canard plus visible que la règle
  (`assoupli` dans `placements.json`).
