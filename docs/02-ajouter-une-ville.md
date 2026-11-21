# 02 — Ajouter une ville

Une ville, c'est **un fichier JSON** dans `blender/themes/`. Tout ce qui n'y figure pas est
pris dans `blender/themes/_commun.json`. Trois lignes suffisent pour obtenir une ville qui
fonctionne ; tout le reste sert à lui donner son caractère.

## Pas à pas

### 1. Créer le fichier du thème

`blender/themes/marseille.json` (le nom du fichier est l'identifiant de la ville : minuscules,
sans espace ni accent) :

```json
{
  "id": "marseille",
  "nom": "Marseille — Le Panier",
  "embleme": "⛵",
  "ordre": 4,
  "graine": 13002
}
```

- `nom` : ce qu'affiche l'accueil. Le tiret long « — » sépare la ville (en gros) du
  quartier (en dessous).
- `embleme` : un émoji qui illustre la ville sur l'accueil (facultatif, 🏙️ par défaut).
- `ordre` : la place sur l'accueil (Paris 0, New York 1, Lille 2, Delhi 3).
- `graine` : n'importe quel nombre. Même graine = même ville ; autre graine = autre ville.

Avec ces seules lignes, la ville ressemble à Paris en plus neutre. On la personnalise
ensuite (étape 3).

### 2. Vérifier le thème (2 secondes, sans Blender)

```bash
python -m unittest discover -s blender/tests -t blender
```

Les tests vérifient **tous** les thèmes présents. Une faute de frappe donne la liste claire
de ce qui ne va pas, par exemple :

```
thème « marseille » invalide :
  - style.toit : « coupole » n'est pas un type de toit (possibles : mansarde, pignon, plat)
  - style.murs : « ocre_clair » n'est pas une couleur de la palette (…)
```

### 3. Donner son caractère à la ville

Exemple complet, commenté plus bas :

```json
{
  "id": "marseille",
  "nom": "Marseille — Le Panier",
  "ordre": 4,
  "graine": 13002,
  "rue": 8,
  "style": {
    "square": "lille",
    "toit": "pignon",
    "part_toit_plat": 0.4,
    "toits": ["tuile"],
    "balcons": "filants",
    "etages": [3, 5],
    "largeur_lot": [5, 8],
    "murs": ["ocre_clair", "rose_pale", "jaune_sable"],
    "volets": ["volet_bleu", "volet_vert"],
    "auvents": ["v_bleu", "v_turquoise"],
    "toit_extras": ["linge", "linge", "pigeons", "chat", "transat"],
    "arbres_modeles": ["Palmier", "Arbre_A", "Arbre_D"],
    "feuillages": ["feuillage", "f_olive"],
    "vehicules": ["voiture", "voiture", "camionnette"],
    "saynetes_rue": ["etal_renverse", "chiens", "musicien", "peintre"],
    "saynetes_place": ["etal_renverse", "pigeons", "mariage", "artiste"],
    "tags": 0.6,
    "foule": 8
  },
  "palette": {
    "ocre_clair": "#E8C496",
    "rose_pale": "#EFC2B3",
    "jaune_sable": "#E9D8B0",
    "volet_bleu": "#5C8FC2",
    "volet_vert": "#4F9A72"
  }
}
```

> **Attention au jaune.** Aucune couleur de la palette ne doit être un vrai jaune, sauf
> `jaune` elle-même (c'est ce qui cache les canards). « jaune_sable » ci-dessus passe car
> c'est un beige ; un test refuse les couleurs trop jaunes.

### 4. Générer la ville (quelques minutes)

```bash
bash blender/tout_generer.sh marseille
```

Le script lance les tests, reconstruit les modèles communs, puis génère la ville : bâti,
décor, mesure de visibilité, placement des canards, images de contrôle. Il affiche des
lignes `RESULTAT` ; à surveiller :

- `canards_par_lieu` : idéalement un mélange de `sol`, `toit`, `vitre` (et `balcon`).
- `canards_plage_elargie` : vide de préférence. Une ou deux cases, c'est acceptable.
- `triangles` + `triangles_instances` : au-delà de 600 000 au total, la ville risque d'être
  lente sur téléphone (baisser `foule`, `saynete_rue`, `nb_betes`).

S'il échoue avec `PlacementImpossible: case C3…`, voir « Dépannage » plus bas.

### 5. Regarder le résultat

- Images rapides : `docs/previews/marseille_ensemble.png`, `_moyen.png`, `_pres.png`.
  Elles n'ont pas les traits d'encre ni toutes les couleurs : c'est un contrôle grossier.
- Le vrai rendu : `cd app && npm run dev`, puis `http://localhost:5173/?ville=marseille`.

### 6. Publier

```bash
git add blender/themes/marseille.json assets/ docs/previews/
git commit -m "feat: ville de Marseille"
git push
```

Le site est mis à jour quelques minutes après le `push`.

### Modifier une ville existante

Même chose : modifier son thème, relancer `bash blender/tout_generer.sh <ville>`. Si les
canards changent de place, **augmenter `version`** dans le thème de cette ville (par exemple
`"version": 4`), sinon les joueurs qui avaient commencé verront des canards « trouvés »
au mauvais endroit.

---

## Référence des réglages

### Réglages de la carte (à la racine du thème)

| Clé | Défaut | Effet |
|---|---|---|
| `id`, `nom`, `embleme`, `ordre`, `graine` | — | Voir l'étape 1 |
| `version` | 3 | Version de la scène, pour la sauvegarde |
| `taille` | 120 | Côté de la carte, en mètres |
| `ilots` | 3 | Nombre d'îlots par côté (3 → 9 îlots, dont une place) |
| `rue` | 12 | Largeur des rues, en mètres |
| `trottoir` | 2,5 | Largeur des trottoirs |
| `square` | `[1, 1]` | Quel îlot devient la place (colonne, rangée, à partir de 0) |

La taille d'un îlot vaut `(taille − ilots × rue) / ilots`. Il doit rester au moins
`2 × (trottoir + profondeur) + 4` mètres, sinon les immeubles ne tiennent pas ; la
validation le vérifie. Exemple : Delhi a 4 îlots et des rues de 8 m pour un bâti plus serré.

Les réglages de jeu (`canards`, `leurres`, `grille`, visibilités…) sont décrits dans
[03 — Régler la difficulté](03-regler-la-difficulte.md).

### Architecture (`style`)

| Clé | Défaut | Valeurs possibles |
|---|---|---|
| `square` | `"paris"` | Contenu de la place : `paris` (fontaine, kiosque, terrasse), `new_york` (parc, arche, chariots), `lille` (colonne, beffroi, braderie), `delhi` (porte en grès, banyan, bazar) |
| `toit` | `"plat"` | `mansarde` (zinc, Paris), `plat` (terrasse et muret), `pignon` (deux pentes) |
| `part_toit_plat` | 0 | Avec `pignon` : part de toits plats mélangés |
| `toits` | `["tuile"]` | Couleurs des toits à pignon |
| `gradins` | false | Pignons à gradins flamands (Lille) |
| `toit_extras` | `["cheminee"]` | Ce qu'on trouve sur les toits : `cheminee`, `chateau_eau`, `clim`, `citerne`, `cabanon`, `dome`, `linge`, `transat`, `jardin`, `pigeons`, `chat`, `singe`, `vache`. Répéter un nom le rend plus fréquent |
| `gens_sur_toits` | 0,25 | Probabilité d'un personnage par toit |
| `balcons` | `"aucun"` | `filants` (Paris), `secours` (escaliers de secours, New York), `jharokha` (balcons fermés colorés, Delhi), `aucun` |
| `etages` | `[4, 7]` | Nombre d'étages (minimum, maximum) |
| `etages_tour`, `tours` | `[9, 13]`, 0 | Probabilité et hauteur des tours (îlots du fond seulement) |
| `hauteur_etage`, `rdc` | 3, 4 | Hauteurs en mètres |
| `profondeur` | 8 | Profondeur des immeubles |
| `largeur_lot` | `[8, 12]` | Largeur des immeubles : petit = maisons étroites (Lille), grand = immeubles (Paris) |
| `murs` | pierre, trottoir, pavés | Couleurs des façades |
| `bandeaux` | null | Couleurs des bandeaux entre étages (null = couleur du mur) |
| `volets` | `[]` | Couleurs des volets (vide = pas de volets) |
| `jardinieres_fenetre` | 0,15 | Part de fenêtres fleuries |
| `auvent`, `auvents` | 0,6 | Probabilité d'un store au-dessus des boutiques, et leurs couleurs |
| `toile_jaune` | 0,12 | Part des stores et parasols **jaunes** (gros leurres) |
| `accents` | 3 couleurs | Couleurs des balcons `jharokha` et des dômes |

### Vie de la rue (`style`)

| Clé | Défaut | Effet |
|---|---|---|
| `foule` | 7 | Passants par côté de trottoir |
| `trafic` | 3 | Véhicules en circulation par rue intérieure |
| `vehicules` | `["voiture"]` | `voiture`, `taxi`, `camionnette`, `bus`, `bus_scolaire`, `rickshaw`. Taxis, camionnettes, bus scolaires et capotes de rickshaw sont **jaunes** |
| `arbres` | 0,3 | Probabilité d'un arbre tous les 3,5 m de trottoir |
| `arbres_modeles` | A, B, C, D | `Arbre_A`, `Arbre_B`, `Arbre_C` (conique), `Arbre_D` (branchu), `Palmier` |
| `etals` | 0 | Probabilité d'un étal de marché devant les façades visibles |
| `pots` | 0,25 | Pots de fleurs au pied des façades et sur les balcons |
| `betes`, `nb_betes` | chien, chat, pigeons ; 2 | Animaux en liberté (`Chien`, `Chat`, `Pigeon`, `Poule`, `Singe`), par trottoir (×4 sur la place) |
| `coiffes_folles` | 0,04 | Part de passants avec toque, couronne, heaume, plot sur la tête… |

### Désordre et saynètes (`style`)

| Clé | Défaut | Effet |
|---|---|---|
| `tags` | 0,4 | Probabilité de tags sur une façade |
| `rideaux` | 0,12 | Part de boutiques fermées, rideau de fer tagué |
| `planches` | 0,03 | Part de fenêtres condamnées |
| `lierre`, `fissures` | 0,12 ; 0,1 | Probabilité par façade |
| `saynete_rue` | 0,55 | Probabilité d'une saynète à chacun des 2 emplacements par trottoir visible |
| `saynetes_rue` | 5 saynètes | Celles qu'on peut tirer dans la rue (répéter = plus fréquent) |
| `saynetes_place`, `nb_saynetes_place` | 4 saynètes ; 4 | Celles de la place, et combien |

Les saynètes existantes :

| Saynète | Ce qu'on voit | Où |
|---|---|---|
| `chiens` | Un promeneur et 4 à 6 chiens | rue ou place |
| `fanfare` | Six musiciens en uniforme et une grosse caisse | rue ou place |
| `queue` | Une file d'attente de 5 à 8 personnes | rue ou place |
| `etal_renverse` | Fruits répandus, un marchand, un chien et une poule | rue ou place |
| `musicien` | Un musicien en haut-de-forme et son public | rue ou place |
| `mariage` | Les mariés, des confettis, des invités | rue ou place |
| `ballons` | Un vendeur de ballons (parfois jaunes) et des enfants | rue ou place |
| `ordures` | Sacs, poubelle renversée, cartons, un chat | rue ou place |
| `artiste` | Un peintre à son chevalet et des curieux | rue ou place |
| `pigeons` | Quelqu'un qui nourrit une nuée de pigeons | rue ou place |
| `velos` | Une rangée de vélos garés | rue ou place |
| `elephant` | Un éléphant paré, un cornac couronné, des badauds | rue ou place |
| `geant` | Un géant de procession de plus de 5 m et ses porteurs | rue ou place |
| `peintre` | Un peintre en bâtiment sur son échelle, une flaque de peinture | **rue seulement** |
| `demenagement` | Camionnette, cartons, canapé, piano hissé le long de la façade | **rue seulement** |
| `panne` | Voiture en panne qui fume, conducteur désemparé | **rue seulement** |
| `geyser` | Borne à incendie éventrée, enfants sous le jet | **rue seulement** |
| `chantier` | Trou, barrières, tas de sable, brouette, ouvrier | **rue seulement** |

Les saynètes « rue seulement » ont besoin d'un mur et d'une chaussée ; la validation refuse
de les mettre dans `saynetes_place`.

### Couleurs (`palette`)

- Une couleur se déclare dans `palette` (`"nom": "#RRGGBB"`) et s'utilise ensuite par son
  nom dans `style`.
- Une ville hérite de toutes les couleurs de `_commun.json` (57 couleurs : `v_rouge`,
  `v_bleu`, `v_vert`, `v_violet`, `v_turquoise`, `v_orange`, `v_rose`, `v_marine`, `blanc`,
  `pierre`, `brique`, `tuile`, `ardoise`, `zinc`, `herbe`, `feuillage`, `f_tendre`, `f_rose`,
  `f_automne`, `f_olive`, `peau1` à `peau4`, `ch_noir`, `ch_brun`, `ch_roux`, `ch_gris`…).
- Redéfinir une couleur commune (par exemple `"asphalte": "#807C78"`) ne change que cette ville.
- Les listes de couleurs des personnages se règlent aussi : `vetements`, `pantalons`,
  `peaux`, `cheveux`, `rayures` (marinières), `couleurs` (marchandises), `fleurs`, `linge`,
  `poils`, `tags_couleurs`, `feuillages`, `voitures`, `bus`.

---

## Ce que le thème ne sait pas faire

Il faut alors modifier le générateur (voir [04](04-etendre-le-generateur.md)) :

- une **place** différente des quatre existantes (par exemple un port, un canal) ;
- un **type de toit** ou de **balcon** nouveau (pagode, coupole, moucharabieh) ;
- une forme de ville autre qu'une grille d'îlots carrés (canaux de Venise, ruelles
  tortueuses, front de mer) ;
- de **nouveaux modèles** (gondole, tuk-tuk, cerisier en fleurs, lanternes).

## Dépannage

| Message | Cause probable | Que faire |
|---|---|---|
| `thème « x » invalide : …` | Faute de frappe, valeur inconnue | Le message liste les valeurs possibles |
| `PlacementImpossible: case C3 : aucune cachette…` | Une case de la carte n'a aucun endroit à moitié visible (souvent derrière une tour) | Changer de `graine`, baisser `tours` ou `etages`, ou ajouter du décor qui cache à moitié (`arbres`, `etals`, `pots`) |
| `seulement N leurres placés sur 270` | Pas assez de place libre | Baisser `leurres`, ou augmenter `taille` |
| L'app affiche « Impossible de lancer le jeu : …scenes.json… » | `assets/scenes.json` a été supprimé | Le régénérer : `bash blender/tout_generer.sh` |
| La ville n'apparaît pas dans le menu | `place_objets.py` n'est pas allé au bout | Relire la sortie de `tout_generer.sh` |
| Blender introuvable | Blender n'est pas à l'emplacement prévu | `BLENDER="chemin/vers/blender.exe" bash blender/tout_generer.sh marseille` |
