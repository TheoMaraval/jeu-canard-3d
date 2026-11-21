# jeu-canard-3D

Jeu d'observation 3D : trouver 30 canards en plastique jaunes cachés dans un quartier
dessiné, dense et loufoque. Quatre villes : Paris, New York, Lille, Delhi.
Successeur de `../jeuFind` (prototype 2D, référence historique seulement).

- **En ligne** : https://theomaraval.github.io/jeu-canard-3d/ (dépôt `TheoMaraval/jeu-canard-3d`,
  republié à chaque `git push` sur `main` par `.github/workflows/pages.yml`).
- **Documentation complète** : `docs/README.md`. Lire le fichier qui correspond à la tâche
  avant de commencer :

| Tâche | Fichier |
|---|---|
| Architecture, formats de fichiers, sauvegarde | `docs/01-comprendre-le-projet.md` |
| Créer ou modifier une ville (+ référence de toutes les clés de thème) | `docs/02-ajouter-une-ville.md` |
| Difficulté | `docs/03-regler-la-difficulte.md` |
| Nouveau modèle, saynète, place, toit, véhicule, leurre | `docs/04-etendre-le-generateur.md` |
| Lancer, publier, dépanner, fluidité | `docs/05-publier-et-depanner.md` |
| Idées et modes futurs (cacher ses canards, créer son monde) | `docs/06-pistes-d-amelioration.md` |

## Architecture en trois lignes

`blender/themes/<ville>.json` → générateur Python pur (`blender/citygen/`) + Blender 5.3 en
ligne de commande (`blender/*.py`) → fichiers dans `assets/` → app Vite + Three.js (`app/`).
Le générateur et l'app ne communiquent que par `assets/` (formats dans `docs/01`).

## Règles qui définissent le jeu (ne pas casser)

- Canards et 22 leurres partagent le même jaune (`#FFD21E`) et le même gabarit (0,50 m
  modélisé, 0,35 m en jeu). Le seul jaune du décor est la couleur `jaune` (gros leurres :
  taxis, stores, rickshaws). Si un canard se distingue à zoom moyen, le jeu est cassé.
- Bec et œil visibles seulement à partir de 28 px à l'écran ; un tap ne trouve un canard
  qu'à partir de ce zoom.
- Un canard par case d'une grille 6 × 5 ; visibilité 30–80 % (jamais < 15 %), bec et un
  œil tournés vers la caméra ; « derrière une vitre » vérifié par lancer de rayons.
- Pas de pénalité pour un tap raté. Temps, taps et précision affichés en direct.
- Sans `?ville=` dans l'adresse (ou avec une ville inconnue) : écran d'accueil. Changer de
  ville recharge la page : une seule scène 3D par page.
- Sauvegarde par ville et par `version` : augmenter la `version` d'une ville quand ses
  canards changent de place.

## Commandes

Blender n'est pas dans le PATH : `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`
(trouvé tout seul par `tout_generer.sh`).

```bash
python -m unittest discover -s blender/tests -t blender   # 41 tests, sans Blender, quelques secondes
bash blender/tout_generer.sh                              # tout régénérer (moins de 10 min)
bash blender/tout_generer.sh lille                        # une ville
cd app && npm run dev                                     # http://localhost:5173/?ville=lille
cd app && npm test                                        # 38 tests
```

Dans une session ouverte depuis `jeuFind`, le serveur de dev se lance avec la configuration
`canard-3d` de `jeuFind/.claude/launch.json`.

## État (21/11/2026)

- Fait : quatre villes publiées ; style dessiné (toon + traits d'encre) ; vitres ; kit de
  81 modèles (passants, véhicules, animaux, tags, végétation, saynètes) ; 18 saynètes ;
  22 leurres ; menu des villes ; compteurs en direct ; « Rejouer » corrigé ; validation
  des thèmes avec messages clairs ; ville minimale (id, nom, graine) garantie par un test ;
  écran d'accueil (choix de la ville, progression) ; partage du score et invitation
  (`app/src/partage.js` : partage natif sur téléphone, copie sinon) ; interface en style
  « autocollant de BD » (charte dans `docs/01`, section « L'interface ») ; « coinnn »
  synthétisé quand on trouve un canard, avec bouton pour couper le son (`app/src/son.js`).
- **Jamais mesuré** : fluidité sur téléphone (400 000 à 570 000 triangles de décor, au-dessus
  de la cible de 500 000), et aucune partie complète jouée pour régler la difficulté.
- Prochaine étape conseillée : mesurer la fluidité sur téléphone, puis le mode « Cacher mes
  canards » (conception dans `docs/06`).

## Pièges pour Claude

- **Ne jamais supprimer `assets/scenes.json`** : l'app ne démarre plus. `place_objets.py`
  met à jour la ligne de sa ville.
- `location.reload()` déclenche `pagehide`, donc une sauvegarde : « Rejouer » coupe les
  sauvegardes (`rejoue = true` dans `main.js`). Pour tester un état sauvegardé, l'injecter
  depuis une page sans jeu (`/scenes.json`), pas depuis le jeu.
- Ajouter un tirage aléatoire dans du code commun du générateur déplace les canards de
  **toutes** les villes : régénérer tout et augmenter `version`.
- Décor : ne pas utiliser `bmesh` (plus de 7 min par ville) ; passer par `citygen/maillage.py`.
- Blender 5 : matériaux et monde créés par script ont un arbre de nœuds vide ; créer les
  nœuds explicitement (`material()` dans `blender/citygen/geo.py`).
- Git Bash : un heredoc contenant `\n`, des apostrophes ou `\U` se casse. Écrire le script
  dans un fichier, ou utiliser l'outil d'édition.
- Navigateur intégré de Claude : volet masqué = page de taille nulle (fixer une taille avec
  `resize_window`, la remettre ensuite) ; zoomer avec des `WheelEvent` synthétiques ;
  les `PointerEvent` synthétiques échouent, faire de vrais clics.
- Vite renvoie `index.html` pour un fichier absent : un JSON « illisible » = fichier manquant.
- Les fiches de `.claude/skills/` (dépôt `arjun988/blender-skills`) sont des conseils, pas
  des modèles. Ne pas citer de noms de skills sans avoir listé le dépôt.
- Le serveur MCP `blender` n'est pas utilisé : tout tourne en `blender --background`.
- Les générations Blender des quatre villes sont longues : demander avant de les relancer
  toutes si ce n'est pas nécessaire.

## Préférences de travail

- Commiter et mettre la doc à jour au fil de l'eau (`docs/` d'abord, puis ce fichier s'il
  change de l'état ou des pièges).
- Quand le code contredit la spec (`docs/superpowers/specs/`), corriger la spec et
  journaliser l'écart dans son journal des révisions.
- Répondre en français.
