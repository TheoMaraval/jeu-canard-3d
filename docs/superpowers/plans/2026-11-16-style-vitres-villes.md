# Style dessiné, vitres, quatre villes, difficulté — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Donner au jeu un graphisme de scène dessinée fourmillante, des canards derrière
des vitres, quatre quartiers reconnaissables, et le rendre nettement moins facile.

**Architecture:** Le générateur devient paramétré par un style architectural (thème de
ville fusionné avec un tronc commun). Les façades visibles sont une peau trouée devant un
noyau, ce qui crée de vraies niches vitrées. Le style « dessin » est fait côté app
(matériaux toon, arêtes, coque retournée), pas dans Blender.

**Tech Stack:** inchangé (Blender 5.3 `--background`, Python `unittest`, Three.js, Vitest).

Spec : section 9 de `docs/superpowers/specs/2026-11-16-jeu-canard-3d-design.md`.

---

## Tâches

### Tâche 1 : générateur paramétré et façades à niches
- [x] `themes/_commun.json` + héritage dans `charger_theme`, `villes()`.
- [x] `layout.py` : `facade()` (peau, bandeaux, trumeaux, vitres, vitrine), lieu `vitre`,
      `balcons()` (filants, secours, jharokha), toits (mansarde, plat, pignon à gradins),
      éléments de toit, véhicules, étals, passants, quatre `square_<ville>`.
- [x] `tests/test_layout.py` paramétré sur les quatre villes.

### Tâche 2 : difficulté
- [x] `echelle_objets`, 270 leurres, visibilité 0,3–0,8, gros jaune dans le décor.
- [x] Trois leurres à silhouette de canard dans `build_assets.py` (arrosoir, botte, ballon).
- [x] `place_objets.py` : échelle, vitres retirées pour la mesure de visibilité.
- [x] `placement.py` : plage élargie par paliers pour les cases difficiles, tests.

### Tâche 3 : maillage rapide
- [x] `citygen/maillage.py` (pur) + `tests/test_maillage.py` (volume signé positif).
- [x] `geo.objet_rapide` ; `build_quartier.py` produit `Quartier` et `Vitres`.

### Tâche 4 : rendu « dessin » dans l'app
- [x] `scene.js` : matériaux toon, verre, arêtes, coque, échelle des objets.
- [x] `vue.js` : seuil de révélation et zoom maximal déduits du gabarit ; tests.
- [x] Menu des villes (`hud.js`, `index.html`, `style.css`), message clair si l'index manque.

### Tâche 5 : skills et personnages
- [x] Skills réelles du dépôt installées : `cartoon-style`, `stylized-style`,
      `lowpoly-style`, `character-artist`, `isometric-style`.
- [x] Passants à proportions cartoon (grosse tête, bras, cheveux ou chapeau).

### Tâche 6 : génération et contrôle
- [x] `blender/tout_generer.sh` : tests, props, quatre villes, aperçus.
- [x] Contrôle à l'image des quatre villes dans le navigateur.
- [ ] Playtest sur iPad : fluidité et difficulté. **À faire par l'utilisateur.**

## Commandes

```bash
bash blender/tout_generer.sh            # tout
bash blender/tout_generer.sh delhi      # une ville
cd app && npm test && npm run dev
```
