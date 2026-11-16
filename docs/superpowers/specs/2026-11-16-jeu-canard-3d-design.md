# jeu-canard-3D — conception

Date : 2026-11-16. Statut : **approuvée**.

## 1. Objectif

Jeu d'observation : trouver 30 canards jaunes cachés dans un quartier urbain 3D stylisé,
sur iPad et navigateur desktop. Les règles de jeu sont celles de `CLAUDE.md` ; ce document
fixe comment on les réalise en 3D.

## 2. Décisions validées

- **3D temps réel** : Blender → `.glb` → Three.js (Vite, JavaScript sans framework d'UI).
- **Caméra orthographique à angle isométrique fixe** (élévation ~35°, azimut 45°).
  Pan et zoom continu seulement. Pas de rotation en v1.
- Repli si l'iPad ne tient pas la charge : rendu Blender en tuiles 2D (hors périmètre ici).

## 3. Décisions de game design (prises pour le fun, à régler au playtest)

| Réglage | Valeur de départ | Pourquoi |
|---|---|---|
| Gabarit jaune | cube de 0,50 m | Assez gros pour être tapé au doigt, assez petit pour se perdre dans le décor |
| Quartier | 120 × 120 m, 8 îlots bâtis + 1 square, style parisien | La boîte aux lettres jaune y est naturelle ; ~15 objets jaunes par écran à zoom moyen |
| Canards | 30, un par case d'une grille 6 × 5 | Garantit la répartition sur toute la carte |
| Objets jaunes | 200 (30 canards + 170 leurres) | 15 % des points jaunes sont des canards : 1 candidat sur 7 paie |
| Seuil de révélation | canard ≥ 28 px à l'écran | En dessous, bec et œil ne sont pas affichés |
| Zoom mini / maxi | quartier entier / canard ≈ 120 px | Au seuil de révélation, l'écran ne montre qu'~1/60 de la carte : ratisser est long |
| Visibilité des cachettes | canard : 40 à 90 % visible ; leurre : 40 à 100 % | Jamais invisible, rarement offert |
| Orientation du canard | bec et au moins un œil visibles de la caméra | Un canard vu de dos serait indiscernable même de près |
| Tap | seulement quand la vue est révélée ; rayon `max(canard à l'écran, 22 px)` | Confort tactile sans permettre de tapoter la vue d'ensemble ; aucun retour sur un tap raté |

Les 15 % du cahier des charges sont interprétés comme la part de canards parmi les objets
jaunes. Écart à journaliser si le playtest impose une autre lecture.

### Camouflage garanti par le code

Le canard a deux niveaux de détail : **loin** (masse jaune seule) et **près** (avec bec
orange et yeux noirs). Le passage se fait au seuil de révélation. Les leurres n'ont qu'un
niveau. Un canard trouvé devient vert aux deux niveaux, avec un petit rebond.

### Cachettes

Les canards ne sont pas posés au hasard sur le trottoir. Le générateur propose des
emplacements typés (balcon, toit, auvent, terrasse, derrière un kiosque, fontaine, benne)
et ne garde que ceux dont la visibilité depuis la caméra fixe est dans la plage voulue,
mesurée par lancer de rayons dans Blender (27 points du volume du canard). Les leurres
occupent les mêmes types d'emplacements, sinon le lieu trahirait le canard. Les canards
sont répartis à tour de rôle entre sol, balcon et toit.

Ce qui cache à moitié : garde-corps des balcons, acrotères des toits, cheminées, troncs
et feuillages, voitures, bancs, haies du square, claustras de terrasse, kiosque.

## 4. Composants

1. **`blender/build_assets.py`** (fait) — canard + 7 leurres, vérifie gabarit et matériau
   jaune unique. Sortie : `assets/props.glb`. À compléter : niveau « loin » du canard.
2. **`blender/build_quartier.py`** — génère le quartier à partir d'une graine : îlots,
   immeubles haussmanniens simplifiés, rues, mobilier, végétation. Un seul maillage,
   un matériau uni par couleur de palette (31 pour Paris), sans texture.
   Sortie : `assets/scenes/<ville>/quartier.glb`.
3. **`blender/place_objets.py`** — mesure la visibilité de chaque cachette, choisit les
   30 canards et les 170 leurres, contrôle les règles. Sortie :
   `assets/scenes/<ville>/placements.json` (`{id, type, position, rotation, visibilite,
   lieu, zone}`, repère glTF) et `assets/scenes.json`.

La logique (plan du quartier, choix des placements) vit dans `blender/citygen/` en Python
pur, testée hors de Blender (`blender/tests/`).
4. **`app/`** — modules indépendants :
   - `scene` : charge les GLB, crée les instances (`InstancedMesh`) à partir des placements ;
   - `vue` : position et zoom, bornes, projection écran, seuil de révélation (pur) ;
   - `entrees` : pan, pinch, molette, tap ;
   - `picking` : tap → canard le plus proche dans la tolérance, ou rien ;
   - `partie` : état pur (trouvés, taps, temps), sans dépendance à Three.js ;
   - `sauvegarde` : `localStorage`, par scène ;
   - `hud` : compteur, écran de fin.

Les scripts Blender ne communiquent avec l'app que par les trois fichiers de `assets/`.

### Plusieurs villes

Une ville = un **thème** + une **graine**. Rien de propre à Paris n'est codé en dur.

- `blender/themes/<ville>.json` : dimensions, taille des îlots, hauteurs et palette des
  immeubles, forme des toits, mobilier, mélange de leurres, graine.
- `build_quartier.py` et `place_objets.py` prennent `--ville <id>` et écrivent dans
  `assets/scenes/<id>/` (`quartier.glb`, `placements.json`).
- `assets/scenes.json` liste les villes disponibles (id, nom, version). L'app charge la
  ville demandée (`?ville=<id>`, sinon la première) ; la sauvegarde est indexée par
  `id` + `version`.
- `props.glb` (canard et leurres) est commun à toutes les villes.

v1 livre une seule ville (`paris`). Ajouter une ville = écrire un fichier de thème et
relancer deux scripts ; l'écran de choix de ville reste hors périmètre v1.

## 5. Budget de performance (cible iPad, à mesurer)

- 60 images/s, < 150 draw calls, < 500 000 triangles, GLB total < 10 Mo.
- Scène statique : une lumière directionnelle dont l'ombre est calculée **une seule fois**
  au chargement, plus une lumière d'ambiance. Pas d'occlusion cuite en v1.
- Rendu à la demande (uniquement quand la caméra ou l'état change) pour la batterie.

## 6. Erreurs

- GLB ou placements introuvables : message à l'écran, pas d'écran noir.
- Sauvegarde illisible ou d'une autre version de scène : ignorée, partie neuve.
- WebGL indisponible : message explicite.

## 7. Tests

- **Blender** : assertions dans les scripts (gabarit, 30 canards, une cachette par case,
  plage de visibilité, distance minimale entre canards). Un script qui échoue n'exporte rien.
- **App** : Vitest sur `partie`, `sauvegarde`, `picking` (géométrie écran) et `lod` (seuil).
- **À l'image** : aperçus Blender dans `docs/previews/` ; le rendu WebGL et la fluidité
  iPad sont vérifiés par l'utilisateur (Claude ne voit pas le rendu WebGL).

## 8. Hors périmètre v1

Rotation de caméra, indices, temps limité, classement, plusieurs scènes, sons, curation
manuelle des cachettes, export Godot.

## Journal des révisions

- 2026-11-16 : première version.
- 2026-11-16 : approuvée par l'utilisateur. Ajout de « Plusieurs villes » (thème + graine,
  `assets/scenes/<id>/`) : la structure multi-villes entre dans la v1, l'écran de choix non.
- 2026-11-16 : après génération du premier quartier. Écarts journalisés :
  - carte de 120 m au lieu de 160 m (densité d'objets jaunes par écran) ;
  - pas d'occlusion ambiante cuite : matériaux unis par couleur, ombre calculée une fois
    côté app (plus simple, un seul maillage) ;
  - ajout de la règle d'orientation du canard (bec et œil vers la caméra), constatée
    nécessaire sur le premier gros plan ;
  - leurres acceptés jusqu'à 100 % de visibilité (un plot en plein trottoir est naturel) ;
    92 leurres sur 170 sont dans la même plage de visibilité que les canards.
  - Mesuré pour Paris : 53 282 triangles, 31 matériaux, `quartier.glb` 2,2 Mo.
- 2026-11-16 : après la première version jouable de l'app. Écarts journalisés :
  - `camera` et `lod` fusionnés en `vue.js` (le zoom d'une caméra orthographique est
    global : la révélation dépend d'un seul nombre) ; gestes dans `entrees.js` ;
  - pas d'inertie sur le déplacement en v1 ;
  - un tap sous le seuil de révélation ne trouve rien (anti-tapotage) ;
  - mesuré sur desktop : 48 draw calls. Fluidité iPad non mesurée.
