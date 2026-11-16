# jeu-canard-3D

Version 3D de jeuFind (`../jeuFind`, prototype 2D de référence pour la boucle de jeu).

## But du joueur

Trouver les **30 canards en plastique jaunes** cachés dans un quartier urbain dense et
stylisé. Un canard trouvé passe en vert, +1 au compteur. Fin de partie à 30/30
(temps, nombre de taps, précision). Pas de temps limité, pas de vies.

## Règles qui définissent le jeu

- **Camouflage** : canards et leurres (taxi, parasol, plot, borne, boîte aux lettres,
  jardinière, casque) partagent le même matériau jaune et le même gabarit. En vue
  d'ensemble, impossible de les distinguer. Seuls le bec orange, l'œil noir et la
  silhouette trahissent le canard, et seulement en zoomant.
  Si un canard se distingue à zoom moyen, le jeu est cassé.
- **Pas de pénalité** pour un tap raté (leurre ou vide → rien).
- **Un canard par position**, et les 30 couvrent toute la carte.
- **Difficulté** : proportion de leurres (~15 % du décor, à régler au playtest) et zoom
  auquel les détails du canard deviennent lisibles.
- **Progression** sauvegardée localement, par scène.
- **Plateformes** : iPad / tablette (pan, pinch, tap) et navigateur desktop.

## Gabarit des assets

- La partie **jaune** de chaque asset tient dans un cube de **0,50 m** (`GABARIT`).
- Un seul matériau jaune partagé : `MAT_Jaune` (#FFD21E, rugosité 0,45).
- `blender/build_assets.py` construit le canard et 7 leurres, vérifie le gabarit et
  échoue s'il est dépassé. Les valeurs sont un point de départ, pas un réglage mesuré.

## Architecture

Validée le 16/11/2026 : 3D temps réel, Blender → `.glb` → Three.js, caméra orthographique
à angle isométrique fixe (pan + zoom, pas de rotation en v1). Détail dans
`docs/superpowers/specs/2026-11-16-jeu-canard-3d-design.md` (approuvée).

## Arborescence

- `blender/themes/<ville>.json` : tous les réglages d'une ville (taille, îlots, palette,
  nombre de canards et de leurres, plages de visibilité, graine).
- `blender/citygen/` : `layout.py` (plan du quartier) et `placement.py` (choix des
  canards et leurres) en **Python pur, sans bpy** ; `geo.py` (primitives → maillage, bpy).
- `blender/tests/` : tests `unittest` des modules purs.
- `blender/build_assets.py`, `build_quartier.py`, `place_objets.py`, `render_ville.py` :
  les quatre étapes du pipeline. `blender/*.blend` et `blender/scenes/` sont générés.
- `assets/props.glb` : canard (`Canard`, `Canard_Loin`) et 7 leurres, communs aux villes.
- `assets/scenes/<ville>/quartier.glb` + `placements.json` ; `assets/scenes.json` : index.
- `app/` : application Vite + Three.js. `src/partie.js`, `sauvegarde.js`, `picking.js`,
  `vue.js` sont purs et testés (`tests/logique.test.js`) ; `scene.js`, `entrees.js`,
  `hud.js`, `main.js` portent Three.js et le DOM. `assets/` est servi à la racine.
- `.claude/skills/` : 9 skills de `arjun988/blender-skills` (MIT).
- `docs/superpowers/specs/` et `plans/` ; `docs/previews/` : rendus de contrôle.

## Lancer

Blender 5.3 n'est pas dans le PATH : `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`.

```bash
python -m unittest discover -s blender/tests -t blender                                        # 22 tests
blender --background --python blender/build_assets.py                                           # props
blender --background --python blender/build_quartier.py -- --ville paris                        # décor
blender --background blender/scenes/paris.blend --python blender/place_objets.py -- --ville paris   # placements
blender --background blender/scenes/paris.blend --python blender/render_ville.py -- --ville paris   # aperçus
```

Après une modification du plan ou du thème : relancer décor, placements, aperçus, dans cet ordre.

```bash
cd app && npm install
npm run dev     # http://localhost:5173 ; l'adresse « Network » affichée sert pour l'iPad (même Wi-Fi)
npm test        # 21 tests
npm run build
```

Ville au choix : `http://localhost:5173/?ville=<id>` (par défaut la première de `scenes.json`).
Diagnostic dans la console du navigateur : `jeu.stats()`, `jeu.vue()`, `jeu.partie()`.

## Ajouter une ville

Copier `blender/themes/paris.json` sous un nouvel `id`, changer palette, dimensions et
graine, puis lancer `build_quartier`, `place_objets` et `render_ville` avec `--ville <id>`.
Le décor ne doit contenir aucune couleur proche du jaune (un test le vérifie pour Paris).
Un style de bâti vraiment différent (gratte-ciel, maisons) demande d'étendre `layout.py`.

## Repères et caméra

- Blender : Z vers le haut, carte centrée sur l'origine. glTF / app : `(x, z, -y)`.
- Caméra de jeu fixe : azimut 45°, élévation 35,264°, côté `+x, -y` (Blender). Seules les
  façades sud et est, les toits et les trottoirs sud/est sont visibles : une cachette
  ailleurs a une visibilité nulle et est écartée automatiquement.

## Règles ajoutées par la version 3D

- **Révélation** : le bec et l'œil ne sont affichés qu'à partir de 56 px par mètre
  (canard de 28 px). En dessous, le canard est une masse jaune (`Canard_Loin`).
- **Un tap ne trouve un canard que si la vue est révélée.** Sinon il suffirait de tapoter
  la vue d'ensemble. Tolérance : `max(rayon du canard à l'écran, 22 px)`.
- **Orientation** : chaque canard montre son bec et au moins un œil à la caméra.
- **Visibilité** : canard visible à 40–90 %, leurre à 40–100 %.

## État

- Fait : pipeline Blender pour Paris et application jouable (plans dans
  `docs/superpowers/plans/`). 30 canards (10 balcon, 8 sol, 12 toit), 170 leurres.
- Vérifié dans le navigateur de bureau : chargement, zoom, révélation, tap, compteur,
  sauvegarde, canard vert après rechargement. 48 draw calls.
- **Pas encore vérifié** : iPad réel (fluidité, pincement, tolérance du tap) et une partie
  complète jusqu'à l'écran de fin. Tous les réglages sont des valeurs de départ.
- Le serveur MCP `blender` (`localhost:9876`) n'est pas démarré : tout tourne en
  `--background`. Le MCP ne sert que pour travailler dans Blender ouvert.
- Limites connues : immeubles encore uniformes (pas de lucarnes ni de mobilier de toit) ;
  leurres « sol uniquement » (taxi, borne, boîte aux lettres) sous-représentés (25 sur
  170) ; juste sous le seuil de révélation, la silhouette à deux boules du canard peut
  déjà le trahir (à juger au playtest : baisser le seuil ou simplifier `Canard_Loin`) ;
  pas d'écran de choix de ville.

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
