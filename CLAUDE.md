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

**Pas encore validée.** Proposition en cours : 3D temps réel, Blender → `.glb` → Three.js,
caméra orthographique. Rien n'est à coder dans `app/` avant validation.

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
blender --background --python blender/build_assets.py   # écrit blender/props.blend et assets/props.glb
```

## État

- Fait : arborescence, skills, script des assets de base.
- **Bloqué** : Blender n'est pas installé sur la machine (16/11/2026), le serveur MCP
  `blender` ne répond pas sur `localhost:9876`. Le script n'a **jamais été exécuté**.
- À faire : installer Blender + add-on MCP, exécuter et contrôler les assets à l'image,
  valider l'architecture, écrire la spec, puis générer le quartier.

## Pièges connus

- Les scripts Blender doivent être idempotents et ne toucher qu'à leur propre collection.
- Le navigateur intégré de Claude ne fait pas tourner `requestAnimationFrame` : le rendu
  WebGL ne peut pas y être vérifié à l'image. Demander une capture à l'utilisateur.

## Préférences de travail

- Commiter et mettre la doc à jour au fil de l'eau.
- Quand le code contredit la spec, corriger la spec et journaliser l'écart.
