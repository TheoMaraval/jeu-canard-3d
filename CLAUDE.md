# jeu-canard-3D

Version 3D de jeuFind (`../jeuFind`, prototype 2D de référence pour la boucle de jeu).

## But du joueur

Trouver les **30 canards en plastique jaunes** cachés dans un quartier dessiné, dense et
plein de monde, façon grande scène fourmillante. Quatre quartiers : Paris, New York,
Lille, Delhi. Un canard trouvé passe en vert, +1 au compteur. Fin de partie à 30/30
(temps, nombre de taps, précision). Pas de temps limité, pas de vies.

## Règles qui définissent le jeu

- **Camouflage** : canards et petits leurres (plot, borne, parasol, taxi miniature, boîte
  aux lettres, jardinière, casque, arrosoir, botte, ballon) partagent le même matériau
  jaune et le même gabarit. En vue d'ensemble, impossible de les distinguer. Seuls le bec
  orange, l'œil noir et la silhouette trahissent le canard, et seulement en zoomant.
  Si un canard se distingue à zoom moyen, le jeu est cassé.
- **Le jaune ne suffit pas** : le décor contient de gros objets jaunes (taxis,
  camionnettes, rickshaws, stores) à la teinte exacte des canards. Aucune autre couleur
  du décor n'est jaune (un test le vérifie pour chaque ville).
- **Révélation** : le bec et l'œil ne sont affichés que lorsque le canard fait au moins
  28 px à l'écran. En dessous, c'est une masse jaune (`Canard_Loin`).
- **Un tap ne trouve un canard que si la vue est révélée.** Sinon il suffirait de tapoter
  la vue d'ensemble. Tolérance : `max(rayon du canard à l'écran, 22 px)`.
- **Pas de pénalité** pour un tap raté (leurre ou vide → rien).
- **Un canard par case** d'une grille 6 × 5 : les 30 couvrent toute la carte.
- **Cachettes** : sol, balcon, toit, et **derrière une vitre** (fenêtre ou vitrine).
  Canard visible à 30–80 %, bec et un œil toujours tournés vers la caméra.
- **Progression** sauvegardée localement, par ville et par version de scène.
- **Plateformes** : iPad / tablette (pan, pinch, tap) et navigateur desktop.

## Réglages de difficulté (`blender/themes/_commun.json`, surchargeables par ville)

| Clé | Valeur | Effet |
|---|---|---|
| `echelle_objets` | 0,7 | canards et leurres de 0,35 m ; plus petit = plus de zoom nécessaire |
| `leurres` | 270 | 1 objet jaune sur 10 est un canard |
| `visibilite_canard` | 0,3–0,8 | part du canard visible depuis la caméra |
| `style.toile_jaune` | 0,12 | part des stores et parasols jaunes |
| `style.vehicules` | liste | plus de `taxi` / `camionnette` / `rickshaw` = plus de gros jaune |
| `style.foule` | 7 à 11 | passants par trottoir ; plus de monde = plus de bruit et de cachettes |

Tout est une valeur de départ : rien n'a été réglé par un vrai playtest.

## Gabarit des assets

- La partie **jaune** de chaque modèle tient dans un cube de **0,50 m** (`GABARIT` dans
  `build_assets.py`, qui échoue sinon) ; l'échelle de jeu est appliquée au placement.
- Un seul matériau jaune partagé : `MAT_Jaune` (#FFD21E), identique au `jaune` du décor.

## Architecture

Validée le 16/11/2026 : 3D temps réel, Blender → `.glb` → Three.js, caméra orthographique
à angle isométrique fixe (pan + zoom, pas de rotation en v1). Détail dans
`docs/superpowers/specs/2026-11-16-jeu-canard-3d-design.md` (approuvée).

## Arborescence

- `blender/themes/_commun.json` + `<ville>.json` : réglages partagés et propres à chaque
  ville (palette, style architectural, difficulté, graine).
- `blender/citygen/`, en **Python pur, sans bpy**, testé hors de Blender :
  `layout.py` (plan du quartier → primitives du bâti, instances du kit, cachettes),
  `placement.py` (choix des canards et leurres), `maillage.py` (primitives → sommets et
  faces). `geo.py` est le seul module qui touche à bpy.
- `blender/tests/` : 36 tests `unittest`.
- Étapes du pipeline, enchaînées par `tout_generer.sh` :
  `build_assets.py` (canard et leurres) → `build_kit.py` (personnages, véhicules, arbres,
  mobilier) → `build_quartier.py` → `place_objets.py` → `render_ville.py`.
  `blender/*.blend` et `blender/scenes/` sont générés.
- `assets/props.glb` : `Canard`, `Canard_Loin` et 10 leurres. `assets/kit.glb` : 28 modèles
  instanciés. Les deux sont communs aux villes.
- `assets/scenes/<ville>/` : `quartier.glb` (objets `Quartier` et `Vitres` : le bâti),
  `decor.json` (instances du kit : type, position, rotation, échelle, teintes),
  `placements.json` (canards et leurres). `assets/scenes.json` : index lu par l'app.
- `app/` : application Vite + Three.js. `src/partie.js`, `sauvegarde.js`, `picking.js`,
  `vue.js` sont purs et testés (`tests/logique.test.js`, 22 tests) ; `scene.js` (rendu
  « dessin »), `entrees.js`, `hud.js`, `main.js` portent Three.js et le DOM.
- `.claude/skills/` : 19 skills de `arjun988/blender-skills` (MIT). Ce sont des **fiches
  de conseils**, pas des modèles ni des scripts : le dépôt ne contient aucun asset.
- `docs/superpowers/specs/` et `plans/` ; `docs/previews/` : rendus Blender de contrôle
  (sans traits d'encre ni teintes d'instance : le style final ne se voit que dans l'app).

## Le kit de modèles (`blender/build_kit.py`)

- Modèles tournés vers +x, posés à z = 0, construits avec `Builder` : `lathe` (révolution),
  `tube` (membres), `rbox` (boîte chanfreinée), `ico`, `sphere`.
- Matériaux `T_<rôle>` : teinte propre à chaque instance (4 rôles au plus par modèle) ;
  `K_<nom>` : couleur fixe.
- Personnages : 7 poses (debout, marche, salue, robe, marinière, assis, buste) × 5 coiffes
  × teintes de haut, bas, peau et cheveux ; un sur huit est un enfant (échelle 0,68).
- `layout.py` choisit les instances (`self.inst(type, x, y, z, rot, k, rôle=couleur)`) ;
  l'ensemble `KIT` y liste les noms attendus et `build_kit.py` échoue s'il en manque un.
- Ajouter un modèle : une fonction dans `build_kit.py`, son nom dans `KIT`, un appel à
  `self.inst` dans `layout.py`. L'app n'a rien à savoir : elle instancie ce que liste
  `decor.json`.

## Lancer

Blender 5.3 n'est pas dans le PATH : `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`.

```bash
python -m unittest discover -s blender/tests -t blender                                        # 36 tests
bash blender/tout_generer.sh                 # tout : tests, props, les 4 villes, aperçus
bash blender/tout_generer.sh lille           # une seule ville
# ou étape par étape :
blender --background --python blender/build_assets.py                                           # props
blender --background --python blender/build_kit.py                                              # kit de modèles
blender --background --python blender/build_quartier.py -- --ville paris                        # bâti + decor.json
blender --background blender/scenes/paris.blend --python blender/place_objets.py -- --ville paris   # placements
blender --background blender/scenes/paris.blend --python blender/render_ville.py -- --ville paris   # aperçus
```

Après une modification du plan ou du thème : relancer décor, placements, aperçus, dans cet ordre.

```bash
cd app && npm install
npm run dev     # http://localhost:5173 ; l'adresse « Network » affichée sert pour l'iPad (même Wi-Fi)
npm test        # 22 tests
npm run build
```

Ville au choix : `http://localhost:5173/?ville=<id>` (par défaut la première de `scenes.json`).
Diagnostic dans la console du navigateur : `jeu.stats()`, `jeu.vue()`, `jeu.partie()`.

## Ajouter ou modifier une ville

- Une ville = `blender/themes/<id>.json`, fusionné avec `_commun.json` (palette et style
  hérités, la ville ne redéfinit que ce qui change).
- L'architecture se règle dans `style` : `toit` (`mansarde` | `plat` | `pignon`),
  `balcons` (`filants` | `secours` | `jharokha` | `aucun`), `gradins`, `toit_extras`
  (`cheminee`, `chateau_eau`, `clim`, `citerne`, `cabanon`, `dome`, `linge`), `etages`,
  `largeur_lot`, `tours`, `etals`, `vehicules`, `murs`, `bandeaux`, `volets`…
- La place centrale est la seule partie codée par ville : `square_<nom>` dans `layout.py`.
- Un élément nouveau (autre type de toit, autre véhicule) s'ajoute dans `layout.py` et
  devient un mot-clé utilisable par toutes les villes.
- Garder les éléments hauts au nord et à l'ouest (`fond=True`) : ailleurs ils masquent
  tout ce qui est derrière eux pour la caméra.
- Puis : `bash blender/tout_generer.sh <id>` et regarder `docs/previews/<id>_*.png`.

## Repères et caméra

- Blender : Z vers le haut, carte centrée sur l'origine. glTF / app : `(x, z, -y)`.
- Caméra de jeu fixe : azimut 45°, élévation 35,264°, côté `+x, -y` (Blender). Seules les
  façades sud et est, les toits et les trottoirs sud/est sont visibles : une cachette
  ailleurs a une visibilité nulle et est écartée automatiquement.

## Rendu « dessin » (app/src/scene.js)

- Matériaux toon à trois paliers, forte lumière d'ambiance, ombre portée à 40 %, fond papier.
- Bâti : traits d'encre sur les arêtes vives (`EdgesGeometry`, 50°), pas de coque.
- Modèles instanciés (kit, canards, leurres) : un seul maillage par modèle, teintes
  d'instance par rôle (attributs `role` et `tint1..4`), et une coque noire retournée
  d'épaisseur constante à l'écran, masquée sous 12 px/m.
- Vitres : matériau `verre` translucide, rendu après les objets opaques.
- Sur le bâti, pour éviter des traits parasites : cylindres ≥ 8 segments, sphères 8 × 5.

## État

- Fait : quatre villes jouables (Paris, New York, Lille, Delhi), style dessiné, vitres,
  kit de modèles (personnages chibi avec visage, véhicules détaillés, arbres, mobilier),
  menu des villes.
- Par ville : 30 canards (dont 6 à 9 **vérifiés derrière une vitre**) et 270 leurres ;
  canards visibles à 51–56 % en moyenne. Quatre cases en plage de visibilité élargie
  (New York A2 et E2, Lille E3 et E5), signalées par `assoupli` dans `placements.json`.
- « Derrière une vitre » est garanti par construction : `place_objets.py` rejette une
  cachette `vitre` si un seul des rayons qui en sortent (bec et yeux compris) atteint la
  caméra sans traverser l'objet `Vitres`.
- Vérifié dans le navigateur de bureau : les quatre villes se chargent sans erreur ;
  canard en vitrine teinté par la vitre ; teintes et coiffes des passants ; menu.
- Triangles par ville (bâti / instances du kit) : Paris 80 000 / 246 000, New York
  58 000 / 239 000, Lille 73 000 / 293 000, Delhi 68 000 / 356 000, plus ~90 000 pour
  canards et leurres. Les coques doublent les instances au-delà de 12 px/m : Delhi peut
  approcher le million de triangles par image, **au-dessus de la cible de 500 000**.
- **Pas encore vérifié** : iPad réel (fluidité avec ces volumes, pincement, tolérance du
  tap) et une partie complète jusqu'à l'écran de fin. La difficulté n'a pas été jouée.
- Si l'iPad peine, dans l'ordre : relever `SEUIL_CONTOURS_PPM` (scene.js), baisser
  `style.foule`, alléger les personnages (360 triangles chacun) dans `build_kit.py`.
- Le serveur MCP `blender` n'est pas utilisé : tout tourne en `--background`.
- Limites connues : canards et leurres jaunes gardent leur modélisation d'origine, plus
  simple que le kit ; leurres « sol uniquement » rares ; aperçus Blender non représentatifs.

## Pièges connus

- Blender 5 : un matériau créé par script a un arbre de nœuds vide. Créer explicitement
  le Principled BSDF et la sortie (voir `material()` dans `build_assets.py`).
- Blender 5 : même chose pour le monde. Sans nœud Background, pas de lumière d'ambiance
  et les ombres sont noires.
- Visibilité des cachettes : sans obstacle bas (garde-corps, acrotère, haie), elle vaut
  0 ou 1 et presque aucune cachette n'est « à moitié cachée ». Ajouter du décor qui
  masque partiellement avant de toucher aux plages du thème.
- Git Bash : les heredocs contenant des apostrophes ou des `\U` cassent. Écrire le script
  dans un fichier puis le lancer.
- **Ne jamais supprimer `assets/scenes.json`** pendant une régénération : l'app affiche
  « Impossible de lancer le jeu ». `place_objets.py` met à jour la ligne de sa ville.
- `bmesh` ralentit à mesure que le maillage grossit (plus de 7 min pour Paris). Le décor
  passe par `maillage.py` + `from_pydata` (8 s). `Builder` (bmesh) ne sert qu'aux props.
- Vite renvoie `index.html` (code 200) pour un fichier absent : un JSON « illisible »
  veut dire fichier manquant.
- Des noms de skills cités de mémoire par un autre assistant (`toon-shading`,
  `stylized-character`, `npr-shader`…) n'existent pas dans le dépôt : lister le dépôt.
- Volet Navigateur de Claude masqué : la page a une taille nulle (canvas 0 × 0, zoom
  non fini). Fixer une taille avec `resize_window` avant de tester, la remettre ensuite.
- En mode `--background`, la scène par défaut (cube, caméra) se retrouve dans le `.blend`
  sauvegardé si on ne repart pas d'une scène vide.

- Les scripts Blender doivent être idempotents et ne toucher qu'à leur propre collection.
- Le navigateur intégré de Claude affiche bien le rendu Three.js de ce projet (contrairement
  à MapLibre dans jeuFind). Pour y zoomer, envoyer des `WheelEvent` synthétiques ; les
  `PointerEvent` synthétiques échouent sur `setPointerCapture`, utiliser de vrais clics.
- Le serveur de dev se lance depuis la session jeuFind par la configuration `canard-3d`
  de `jeuFind/.claude/launch.json`.

## Préférences de travail

- Commiter et mettre la doc à jour au fil de l'eau.
- Quand le code contredit la spec, corriger la spec et journaliser l'écart.
