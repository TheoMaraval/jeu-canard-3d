# 04 — Étendre le générateur

Quand un thème ne suffit plus (voir la fin de [02](02-ajouter-une-ville.md)), on ajoute une
brique au générateur. Une fois ajoutée, elle devient un mot-clé **utilisable par toutes
les villes**.

Après chaque modification : `python -m unittest discover -s blender/tests -t blender`
(quelques secondes), puis `bash blender/tout_generer.sh` (toutes les villes).

> **Règle importante.** Le générateur est déterministe : une ville est entièrement définie
> par son thème et sa graine. Mais ajouter un tirage au hasard dans du code commun (un
> nouvel objet sur tous les trottoirs, par exemple) décale toute la suite des tirages : **les
> canards de toutes les villes changent de place**. Il faut alors régénérer toutes les
> villes et augmenter `version` dans `_commun.json` (et dans les thèmes qui la redéfinissent).
>
> Même sans changer `version`, modifier la borne basse de `visibilite_canard`, `distance_min` ou
> tout ce qui change la liste des cachettes change l'empreinte : les défis déjà envoyés sont
> alors refusés.

## Où est quoi

| Je veux ajouter… | Fichiers à toucher |
|---|---|
| Un modèle de décor (personnage, véhicule, objet, animal, plante) | `blender/build_kit.py` ou `kit_loufoque.py`, puis `KIT` et un appel dans `blender/citygen/layout.py` |
| Une saynète | `layout.py` (une méthode `s_<nom>`) |
| Une place centrale | `layout.py` (une méthode `square_<nom>`) |
| Un élément de toit | `layout.py` (`extra_toit` et `EXTRAS_TOIT`) |
| Un type de toit ou de balcon | `layout.py` (`immeuble`, `balcons`, `TOITS`, `BALCONS`) |
| Un véhicule | `build_kit.py`, puis `VEHICULES` et `vehicule()` dans `layout.py` |
| Un leurre jaune | `blender/build_assets.py`, `LEURRES` dans `blender/citygen/placement.py`, `leurres_par_lieu` dans les thèmes |

La validation des thèmes (`valider_theme` dans `layout.py`) découvre automatiquement les
saynètes et les places ; pour les toits, balcons, éléments de toit et véhicules, il faut
ajouter le nouveau nom à l'ensemble correspondant (`TOITS`, `BALCONS`, `EXTRAS_TOIT`,
`VEHICULES`).

## Modéliser un objet

Les modèles sont écrits en Python avec la classe `Builder` (`blender/citygen/geo.py`),
qui assemble des formes simples en un seul objet. Conventions :

- l'objet **regarde vers +x** et **repose sur z = 0** ;
- les unités sont des mètres ;
- un matériau `T_<rôle>` (par exemple `T_haut`, `T_caisse`) reçoit une **couleur par
  instance**, choisie par la ville (4 rôles au plus par modèle) ; un matériau `K_<nom>` a
  une couleur fixe. Les couleurs par défaut se déclarent avec `register({...})` en tête
  de fichier.

Les formes disponibles :

| Méthode | Forme |
|---|---|
| `box(mat, (sx, sy, sz), (x, y, z), rot=(0, 0, 0), haut=None)` | Boîte centrée en (x, y, z) ; `haut=(fx, fy)` rétrécit le dessus (toits, pyramides) |
| `rbox(mat, taille, position, rot, bevel=0.05)` | Boîte aux arêtes adoucies : volumes « jouet » (carrosseries, coussins) |
| `cyl(mat, r, hauteur, xf(...), seg)` | Cylindre |
| `cone(mat, r_bas, r_haut, hauteur, xf(...), seg)` | Cône ou tronc de cône |
| `sphere(mat, r, xf(position, échelle), half=False, u, v)` | Sphère, éventuellement aplatie ou en demi-sphère |
| `ico(mat, r, position, échelle, sub=1)` | Boule à facettes régulières : feuillages, nuages, fumée |
| `lathe(mat, [(rayon, z), ...], seg=8)` | Objet de révolution à partir d'un profil : vases, lampadaires, corps, chapeaux |
| `tube(mat, p0, p1, r0, r1)` | Membre allant de p0 à p1 : bras, jambes, pieds de table, branches |

`xf(position, échelle, rotation)` fabrique la transformation attendue par `cyl`, `cone`,
`sphere` et `lathe`.

### Exemple : un banc public en pierre

Dans `blender/kit_loufoque.py` :

```python
def banc_pierre():
    b = Builder("Banc_Pierre")
    b.rbox("K_Gris", (1.6, 0.5, 0.12), (0, 0, 0.45), bevel=0.04)    # assise
    for x in (-0.6, 0.6):
        b.rbox("K_Gris", (0.25, 0.45, 0.4), (x, 0, 0.2), bevel=0.03)  # pieds
    return b
```

Puis :

1. ajouter `banc_pierre` à la liste `ASSETS_LOUFOQUES` en bas du fichier ;
2. ajouter `"Banc_Pierre"` à l'ensemble `KIT` dans `layout.py` (sinon `build_kit.py` refuse
   de terminer, ce qui évite d'oublier) ;
3. le poser quelque part dans `layout.py`, par exemple dans une place :
   `self.poser("Banc_Pierre", (x, y), z, rot, r=0.8)`.

L'app n'a rien à savoir : elle dessine tout ce que liste `decor.json`.

**Budget** : un passant fait 360 triangles et il y en a 400 à 600 par ville. Un objet
répété des centaines de fois doit rester sous quelques centaines de triangles ; un objet
unique (éléphant, beffroi) peut en avoir davantage.

**Pour vérifier un modèle** : `blender/kit.blend` contient tous les modèles alignés,
ouvrable dans Blender.

## Écrire une saynète

Une saynète est une petite scène posée sur un trottoir ou sur la place. Dans `layout.py`,
classe `Plan` :

```python
def s_pique_nique(self, P, ra, rd, z, m):
    """Une nappe, trois personnes assises, un chien qui guette."""
    x, y = P(0, 0.3)
    self.box("v_rouge", (1.4, 1.0, 0.01), (x, y, z + 0.005))         # nappe
    for a in (-0.5, 0.0, 0.5):
        self.figurant(P(a, -0.2), z, rd + math.pi, "Perso_Assis")
    self.poser("Chien", P(1.2, 0.5), z, ra + math.pi, r=0.2, poil=self.choix("poils"))
```

- `P(a, b)` : le point à `a` mètres le long du trottoir et `b` mètres vers la chaussée,
  depuis le centre de la saynète.
- `ra` : l'angle « le long du trottoir » ; `rd` : l'angle « vers la chaussée ». Un
  personnage tourné vers `rd + math.pi` regarde la façade.
- `z` : la hauteur du sol.
- `m` : la distance au mur (sur une place, `m` vaut `None` : si la saynète a besoin d'un
  mur ou de la chaussée, ajouter son nom à `SAYNETES_RUE_SEULEMENT`).
- `figurant(position, z, angle, modèle, …)` pose un personnage **s'il y a la place** ;
  `poser(modèle, position, z, angle, r=rayon, **couleurs)` fait de même pour un objet.
- Des cachettes sont ajoutées automatiquement derrière chaque saynète.

Ensuite, citer `"pique_nique"` dans `saynetes_rue` ou `saynetes_place` d'un thème.

## Écrire une place centrale

```python
def square_venise(self, bx, by, bloc):
    cx, cy, z = self._place(bx, by, bloc, "paves")       # dalle, renvoie le centre
    ...                                                   # monuments, mobilier
    self._animer_place(bx, by, bloc, cx, cy, z, arbres=4, gens=80)
```

- `bx, by` : le coin sud-ouest de l'îlot ; `bloc` : son côté.
- `_animer_place` ajoute arbres, passants, saynètes, buissons, animaux et cachettes.
- Mettre les éléments **hauts** au nord (`by + bloc`) et à l'ouest (`bx`) : ailleurs, ils
  masqueraient le reste de la ville pour la caméra.

S'inspirer de `square_lille` (beffroi au nord-ouest, braderie) ou `square_delhi`.

## Ajouter un élément de toit

Dans `extra_toit()`, une branche qui dessine l'objet et renvoie
`(demi-largeur, hauteur)` : ces deux nombres servent à créer des cachettes **derrière**
l'objet, à moitié masquées. Puis ajouter le nom à `EXTRAS_TOIT`.

## Ajouter un leurre jaune

Dans `blender/build_assets.py`, sur le modèle de `banane()` ou `seau()` :

- nom `Leurre_<Nom>` ;
- la partie jaune en matériau `J` (le jaune des canards), dans un cube de 0,50 m (le
  script vérifie et échoue sinon) ;
- éventuellement des détails d'autres couleurs (`N` noir, `O` orange, `G` gris…). Un œil
  noir **ou** de l'orange rend le leurre plus traître ; jamais les deux sur une forme de
  canard, sinon le joueur ne peut plus faire la différence.

Puis : l'ajouter à `ASSETS`, à `LEURRES` dans `blender/citygen/placement.py` (sinon
`build_assets.py` refuse de terminer), et aux listes `leurres_par_lieu` voulues dans les
thèmes (`sol`, `balcon`, `toit`, `vitre`).

## Ajouter un véhicule

1. Le modéliser dans `build_kit.py` (voir `voiture()` ou `rickshaw()`), regardant vers +x.
2. Dans `layout.py` : l'ajouter à `VEHICULES` (`"tuk_tuk": ("TukTuk", longueur, largeur, hauteur)`)
   et ses couleurs dans le dictionnaire `couleurs` de la méthode `vehicule()`.
3. Le citer dans `style.vehicules` d'un thème.

## Les fiches de conseils Blender

`.claude/skills/` contient 19 fiches (style cartoon, proportions « chibi », véhicules,
végétation, éclairage, export…). Ce sont des conseils de direction artistique et de
méthode, sans modèle ni script. Claude les consulte quand on lui demande de modéliser.
