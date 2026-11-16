# Application Three.js — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rendre jouable dans le navigateur (iPad et desktop) la ville produite par le
pipeline Blender : explorer, zoomer, taper les 30 canards, reprendre sa partie.

**Architecture:** La logique de jeu est en fonctions pures testées avec Vitest ; Three.js
et le DOM sont confinés à `scene.js`, `entrees.js`, `hud.js` et `main.js`. L'app ne
connaît le pipeline que par les fichiers de `assets/`, servis à la racine par Vite.

**Tech Stack:** Vite 8, Three.js 0.187, Vitest 5, JavaScript (modules ES), sans framework.

---

## Fichiers

| Fichier | Rôle | Pur ? |
|---|---|---|
| `app/src/partie.js` | État : trouvés, taps, temps. `creerPartie`, `taper`, `terminee`, `precision` | oui |
| `app/src/sauvegarde.js` | `charger` / `enregistrer` / `effacer`, clé `jeu-canard-3d:<ville>:v<version>` | oui |
| `app/src/picking.js` | `choisirCanard(tap, canardsÀLÉcran, {revele})` | oui |
| `app/src/vue.js` | Vue `{u, v, ppm}` : `deplacer`, `zoomer`, `borner`, `projeter`, `estRevele` | oui |
| `app/src/scene.js` | Chargement GLB, instances, caméra orthographique, lumière, rendu à la demande | non |
| `app/src/entrees.js` | Pointeurs et molette → `deplacer`, `zoomer`, `taper` | non |
| `app/src/hud.js` | Compteur, aide, message, écran de fin | non |
| `app/src/main.js` | Assemblage | non |
| `app/tests/logique.test.js` | 21 tests des quatre modules purs | — |

## Contrats

- **Vue** : `u`, `v` = centre de l'écran dans le plan de la caméra (m) ; `ppm` = pixels par
  mètre. Révélation à `ppm ≥ 56` (canard de 28 px). Zoom maxi `ppm = 240` (canard de 120 px).
- **Tap** : ne trouve un canard que si la vue est révélée, dans un rayon de
  `max(rayon du canard à l'écran, 22 px)`. Sinon rien, sans pénalité.
- **Sauvegarde** : `{trouves: string[], taps: number, ecouleMs: number}`.

## Tâches

### Tâche 1 : logique pure
- [x] Écrire `tests/logique.test.js` (partie, sauvegarde, picking, vue).
- [x] Écrire les quatre modules. `npm test` : 21 tests verts.

### Tâche 2 : rendu
- [x] `scene.js` : `quartier.glb` + `props.glb`, un `InstancedMesh` par primitive et par
      type, canards en deux jeux (près / loin) basculés selon la révélation, jaune
      recolorable par instance (vert une fois trouvé), ombre calculée une fois.
- [x] `vite.config.js` : `publicDir: '../assets'`.

### Tâche 3 : gestes et interface
- [x] `entrees.js` : glisser, pincer (zoom centré entre les doigts), molette, tap
      (moins de 10 px et de 500 ms, un seul doigt).
- [x] `hud.js`, `index.html`, `style.css` : compteur, aide, écran de fin, zones sûres iOS.
- [x] `main.js` : chronomètre en pause quand la page est cachée, sauvegarde à chaque tap.

### Tâche 4 : vérification
- [x] `npm run build` sans erreur.
- [x] Dans le navigateur : chargement sans erreur console, zoom jusqu'à la révélation,
      tap raté sans effet, canard trouvé en vert, reprise après rechargement.
- [ ] Sur iPad réel : fluidité, pincement, tolérance du tap. **À faire par l'utilisateur.**

## Commandes

```bash
cd app && npm install
npm run dev        # http://localhost:5173 (et l'adresse réseau pour l'iPad)
npm test
npm run build
```
