# 03 — Régler la difficulté

La difficulté vient de **où** le joueur regarde, pas de combien il zoome. Les leviers se
répartissent en deux familles :

- **dans le thème** (`blender/themes/`) : demandent de régénérer la ville ;
- **dans l'app** (`app/src/`) : il suffit de republier.

Aucun réglage n'a encore été validé par une vraie partie : ce sont des valeurs de départ.
Changer **un levier à la fois** et jouer une partie entre deux changements.

## Leviers du thème (régénération nécessaire)

Ils se placent dans `_commun.json` pour toutes les villes, ou dans le thème d'une ville pour
elle seule.

| Clé | Valeur | Plus difficile si… | Effet |
|---|---|---|---|
| `echelle_objets` | 0,7 | plus petit | Taille des canards et leurres (0,7 → 0,35 m). Plus petit : il faut zoomer davantage, donc on voit moins de ville à la fois |
| `leurres` | 270 | plus grand | Nombre de leurres. Avec 30 canards, 1 objet jaune sur 10 est un canard. Au-delà de 400, risque d'exaspérer |
| `visibilite_canard` | `[0.3, 0.8]` | bornes plus basses | Part du canard visible depuis la caméra. Ne jamais descendre sous 0,15 : le placement le refuse, un canard caché à 90 % est introuvable. Changer la borne basse de `visibilite_canard` ou `distance_min` (ou tout ce qui modifie la liste des cachettes) change l'empreinte et invalide les défis déjà envoyés, même sans changer `version`. |
| `visibilite_leurre` | `[0.3, 1.0]` | plus proche de celle des canards | Si les leurres sont tous bien en vue et les canards tous à moitié cachés, « à moitié caché » devient un indice |
| `distance_min_canards` | 6 | plus petit | Distance minimale entre deux canards (m) |
| `canards` + `grille` | 30, `[6, 5]` | — | Nombre de canards ; `grille` doit avoir exactement autant de cases |
| `style.toile_jaune` | 0,12 | plus grand | Part de stores et parasols jaunes : du « gros jaune » qui attire l'œil pour rien |
| `style.vehicules` | liste | plus de `taxi`, `camionnette`, `bus_scolaire`, `rickshaw` | Plus de véhicules jaunes |
| `style.foule`, `saynete_rue`, `nb_betes` | 7 ; 0,55 ; 2 | plus grand | Plus de bruit visuel et plus de cachettes derrière les gens. Coûte en fluidité sur téléphone |
| `style.tags` | 0,4 | plus grand | Les tags peuvent être jaunes (`tags_couleurs`) |
| `leurres_par_lieu` | listes | mettre les leurres qui ressemblent au canard partout | Les plus traîtres : `Leurre_Smiley` (yeux noirs), `Leurre_Tournesol` (cœur orange), `Leurre_Arrosoir` (bec), `Leurre_Ballon` (rond) |

Où se cachent les canards (sol, balcon, toit, derrière une vitre) dépend des cachettes
qu'offre la ville : plus de balcons, d'étals et de terrasses, plus de variété. Les canards
sont répartis à tour de rôle entre les types de lieux.

## Leviers de l'app (republication suffit)

| Constante | Fichier | Valeur | Effet |
|---|---|---|---|
| `PX_REVELATION` | `app/src/vue.js` | 28 | Taille à l'écran (px) à partir de laquelle bec et œil apparaissent et le tap compte. Plus grand = il faut zoomer plus |
| `PX_MAX` | `app/src/vue.js` | 120 | Taille du canard au zoom maximal |
| `TOLERANCE_PX` | `app/src/picking.js` | 22 | Rayon de tolérance du tap. Ne pas descendre sous ~20 px au doigt |

## Ce que chaque réglage coûte

| Réglage | Risque |
|---|---|
| Objets plus petits | Au-delà d'un certain point, le joueur ratisse la carte case par case au zoom maximal : ennuyeux. C'est exactement ce que la conception veut éviter |
| Plus de leurres | Plus de taps inutiles, plus de frustration |
| Canards plus cachés | Injustice ressentie (« il était invisible ») |
| Plus de foule et de saynètes | Fluidité sur téléphone |

## Idées pour aller plus loin

Niveaux de difficulté au choix du joueur, contre-la-montre, indices, canards qui bougent :
voir [06 — Pistes d'amélioration](06-pistes-d-amelioration.md).
