# Documentation de « Où sont les canards ? » (jeu-canard-3D)

Le jeu en ligne : **https://theomaraval.github.io/jeu-canard-3d/**

## Par où commencer

| Tu veux… | Lis |
|---|---|
| Comprendre comment le projet est construit | [01 — Comprendre le projet](01-comprendre-le-projet.md) |
| **Créer une nouvelle ville** | [02 — Ajouter une ville](02-ajouter-une-ville.md) |
| Rendre le jeu plus facile ou plus dur | [03 — Régler la difficulté](03-regler-la-difficulte.md) |
| Ajouter un modèle, une saynète, une place, un type de toit, un leurre | [04 — Étendre le générateur](04-etendre-le-generateur.md) |
| Lancer en local, tester dans le navigateur, mettre à jour le site, résoudre un problème | [05 — Publier et dépanner](05-publier-et-depanner.md) |
| Idées pour la suite : niveaux, modes « cacher mes canards », « créer mon monde » | [06 — Pistes d'amélioration](06-pistes-d-amelioration.md) |

## En une minute

- Une **ville** est un fichier de réglages : `blender/themes/<ville>.json`.
- Un **générateur** (Python + Blender) en tire un quartier 3D, y cache 30 canards et
  270 leurres jaunes, et écrit le résultat dans `assets/`.
- L'**application** (`app/`, Three.js) affiche ce résultat dans le navigateur et gère le
  jeu : accueil et choix de la ville, zoom, taps, compteurs, « coin coin » et musique de fin, partage, sauvegarde.
- Chaque envoi sur la branche `main` de GitHub **republie le site automatiquement**.

## Reprendre avec Claude après un « clear »

Ouvre une session dans `C:\Users\TMARAVAL\code\jeu-canard-3D` : Claude lit `CLAUDE.md`, qui
résume le projet et renvoie ici. Pour une tâche précise, cite le bon fichier, par exemple :

> Lis `docs/02-ajouter-une-ville.md` et crée une ville « Marseille, le Panier ».

## Documents historiques

`docs/superpowers/specs/` (la conception, avec son journal des révisions) et
`docs/superpowers/plans/` (les plans d'implémentation exécutés) racontent comment le projet
a été construit. Ils ne sont pas nécessaires pour s'en servir.
