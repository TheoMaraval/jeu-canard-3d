# Pipeline Blender — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** À partir d'un fichier de thème, produire `assets/scenes/<ville>/quartier.glb` et
`placements.json` (30 canards + 170 leurres) vérifiés, plus des aperçus.

**Architecture:** La logique (plan du quartier, choix des placements) est du Python pur,
sans `bpy`, testé avec `unittest` hors de Blender. Blender ne fait que trois choses :
transformer la liste de primitives en maillage, mesurer la visibilité par lancer de
rayons, exporter. Les modules communiquent par des dictionnaires simples.

**Tech Stack:** Blender 5.3 en `--background`, Python 3 (`unittest`), glTF 2.0.

Plan suivant (séparé) : l'application Three.js (`docs/superpowers/plans/` à venir).

---

## Fichiers

| Fichier | Rôle | bpy ? |
|---|---|---|
| `blender/themes/paris.json` | Tous les réglages d'une ville | non |
| `blender/citygen/layout.py` | `make_layout(theme)` → `{prims, slots, lots, blocs}` | non |
| `blender/citygen/placement.py` | `choisir(slots, theme)` → objets ; `valider(objets, theme)` | non |
| `blender/citygen/geo.py` | `Builder` (primitives → maillage), matériaux | oui |
| `blender/build_assets.py` | Canard (près + loin) et leurres → `assets/props.glb` | oui |
| `blender/build_quartier.py` | plan → maillage → `.blend` + `quartier.glb` | oui |
| `blender/place_objets.py` | visibilité + placement → `placements.json`, `scenes.json` | oui |
| `blender/render_ville.py` | aperçus dans `docs/previews/<ville>_*.png` | oui |
| `blender/tests/test_layout.py`, `test_placement.py` | tests des modules purs | non |

## Contrats

**Primitive** (`prims`) : `{"t": "box"|"cyl"|"sph", "mat": str, "pos": [x,y,z] (centre), ...}`
- box : `size [sx,sy,sz]`, `rot` (rad, axe Z), `haut [fx,fy]` optionnel (rétrécit le dessus) ;
- cyl : `r1`, `r2`, `h`, `seg` ; sph : `r`, `scale [sx,sy,sz]`.

**Slot** (cachette candidate) : `{"lieu": "sol"|"balcon"|"toit", "pos": [x,y,z], "rot": rad}`,
puis `"vis"` (0–1) ajouté par `place_objets.py`.

**Objet placé** : `{"id", "type" (nom du nœud dans props.glb), "position" [x,y,z] glTF,
"rotation" (rad, axe Y), "visibilite", "lieu", "zone" ("A1"…"F5")}`.

**Repères** : Blender Z haut, carte centrée sur l'origine. glTF = `(x, z, -y)`.
Caméra de jeu : azimut 45°, élévation 35,264°, placée côté `+x, -y` (Blender).

## Tâches

### Tâche 1 : socle partagé `geo.py` et canard « loin »
- [x] Extraire `Builder`, `material`, `xf` de `build_assets.py` vers `citygen/geo.py`
      (palette enregistrée par `register()`), ajouter `haut` à `box`.
- [x] Ajouter `Canard_Loin` (corps, tête, queue ; ni bec ni yeux) à `build_assets.py`.
- [x] Lancer `build_assets.py` : 9 objets, contrôle de gabarit vert.
- [x] Commit.

### Tâche 2 : thème et plan du quartier (pur)
- [x] Écrire `tests/test_layout.py` : déterminisme, primitives dans la carte, aucune
      couleur de décor proche du jaune, ≥ 1500 slots, ≥ 20 slots par case de la grille,
      aucun slot « sol » dans un immeuble.
- [x] Vérifier l'échec (`python -m unittest discover -s blender/tests -t blender`).
- [x] Écrire `themes/paris.json` et `citygen/layout.py` (îlots bâtis en anneau, îlot
      central en square avec fontaine, trottoirs, arbres, mobilier, voitures, balcons,
      toits mansardés, cheminées).
- [x] Tests verts. Commit.

### Tâche 3 : choix des placements (pur)
- [x] Écrire `tests/test_placement.py` : 30 canards, un par case, 170 leurres, plages de
      visibilité, distances minimales, déterminisme, erreur nommant la case sans candidat,
      type de leurre compatible avec le lieu.
- [x] Vérifier l'échec, écrire `citygen/placement.py`, tests verts. Commit.

### Tâche 4 : maillage et export
- [x] `build_quartier.py -- --ville paris` : plan → un maillage fusionné, un slot par
      matériau → `blender/scenes/paris.blend` + `assets/scenes/paris/quartier.glb`.
- [x] Relever triangles, nombre de matériaux, poids du GLB ; comparer au budget de la spec.
- [x] Commit.

### Tâche 5 : visibilité et placements
- [x] `place_objets.py` : pour chaque slot, recaler au sol par rayon descendant, puis
      27 rayons vers la caméra → `vis`. Appeler `choisir` puis `valider`.
- [x] Écrire `assets/scenes/paris/placements.json` et `assets/scenes.json`.
- [x] Commit.

### Tâche 6 : aperçus et contrôle à l'image
- [x] `render_ville.py` : vue d'ensemble, vue à zoom moyen, gros plan sur un canard.
- [x] Regarder les images : le quartier est-il lisible et dense ? les canards se
      confondent-ils avec les leurres à zoom moyen ? Corriger thème ou plan si besoin.
- [x] Mettre à jour `CLAUDE.md` et la spec (journal). Commit.

## Commandes

```bash
python -m unittest discover -s blender/tests -t blender
blender --background --python blender/build_assets.py
blender --background --python blender/build_quartier.py -- --ville paris
blender --background blender/scenes/paris.blend --python blender/place_objets.py -- --ville paris
blender --background blender/scenes/paris.blend --python blender/render_ville.py -- --ville paris
```
