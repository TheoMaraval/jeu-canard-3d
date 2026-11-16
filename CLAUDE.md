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
`docs/superpowers/specs/2026-11-16-jeu-canard-3d-design.md` (en attente de relecture).

## Arborescence

- `blender/` : scripts `bpy` (source de vérité) et `.blend` générés.
- `assets/` : exports `.glb` et données de placement consommés par l'app.
- `app/` : application web (vide pour l'instant).
- `.claude/skills/` : 9 skills de `arjun988/blender-skills` (MIT) — blender-director,
  environment-artist, procedural-modeling, set-dressing, prop-artist, lighting,
  rendering, asset-optimization, export-pipeline.
- `docs/superpowers/specs/` : specs de conception.

## Lancer

```bash
blender --background --python blender/build_assets.py                      # blender/props.blend + assets/props.glb
blender --background blender/props.blend --python blender/render_preview.py # docs/previews/*.png
```

Blender 5.3 : `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe` (pas dans le PATH).

## État

- Fait : arborescence, skills, canard + 7 leurres générés, exportés et contrôlés à l'image
  (`docs/previews/`).
- Le serveur MCP `blender` (`localhost:9876`) n'est pas démarré : les scripts tournent en
  mode `--background`, ce qui suffit. Le MCP ne sert que pour travailler dans Blender ouvert.
- À faire : relecture de la spec, plan d'implémentation, puis quartier, placements et app.

## Pièges connus

- Blender 5 : un matériau créé par script a un arbre de nœuds vide. Créer explicitement
  le Principled BSDF et la sortie (voir `material()` dans `build_assets.py`).
- En mode `--background`, la scène par défaut (cube, caméra) se retrouve dans le `.blend`
  sauvegardé si on ne repart pas d'une scène vide.

- Les scripts Blender doivent être idempotents et ne toucher qu'à leur propre collection.
- Le navigateur intégré de Claude ne fait pas tourner `requestAnimationFrame` : le rendu
  WebGL ne peut pas y être vérifié à l'image. Demander une capture à l'utilisateur.

## Préférences de travail

- Commiter et mettre la doc à jour au fil de l'eau.
- Quand le code contredit la spec, corriger la spec et journaliser l'écart.
