# jeu-canard-3D — « Où sont les canards ? »

Jeu d'observation 3D : trouver 30 canards en plastique jaunes cachés dans un quartier
dessiné, dense et loufoque. Quatre villes : Paris, New York, Lille, Delhi.
Successeur de `../jeuFind` (prototype 2D, référence historique seulement).

- **En ligne** : https://theomaraval.github.io/jeu-canard-3d/ (dépôt `TheoMaraval/jeu-canard-3d`,
  republié à chaque `git push` sur `main` par `.github/workflows/pages.yml`, en 2 à 5 min).
- **Documentation complète** : `docs/README.md`. Lire le fichier qui correspond à la tâche
  avant de commencer :

| Tâche | Fichier |
|---|---|
| Architecture, formats de fichiers (dont `cachettes.json`, lien de défi), sauvegarde, charte de l'interface, son | `docs/01-comprendre-le-projet.md` |
| Créer ou modifier une ville (+ référence de toutes les clés de thème) | `docs/02-ajouter-une-ville.md` |
| Difficulté | `docs/03-regler-la-difficulte.md` |
| Nouveau modèle, saynète, place, toit, véhicule, leurre | `docs/04-etendre-le-generateur.md` |
| Lancer, tester dans le navigateur, publier, dépanner, fluidité | `docs/05-publier-et-depanner.md` |
| Idées et modes futurs (cacher ses canards, créer son monde) | `docs/06-pistes-d-amelioration.md` |

## Architecture en trois lignes

`blender/themes/<ville>.json` → générateur Python pur (`blender/citygen/`) + Blender 5.3 en
ligne de commande (`blender/*.py`) → fichiers dans `assets/` → app Vite + Three.js (`app/`).
Le générateur et l'app ne communiquent que par `assets/` (formats dans `docs/01`).

## L'application (`app/`)

| Fichier | Rôle | Testé |
|---|---|---|
| `index.html` | Structure des écrans (accueil, barre de jeu, chargement, fin) ; icônes SVG et mascotte canard en `<symbol>` | — |
| `src/style.css` | Charte « autocollant de BD » ; variables en tête (`--encre`, `--jaune`…) | — |
| `src/main.js` | Assemble tout : accueil sans `?ville=` (avec « Mes défis »), sinon la partie, un défi reçu (`&defi=`) ou l'écran « Cacher » (`&cacher`) | — |
| `src/scene.js` | Charge les fichiers de `assets/`, rendu toon + traits d'encre, instanciation ; canards fournis (défi), emplacements vides, `placerCanards`, `rebondir` | — |
| `src/entrees.js` | Glisser, pincer, molette, tap | — |
| `src/vue.js` | Position, zoom, seuil de révélation, projection écran | oui |
| `src/picking.js` | Quel canard est sous le doigt | oui |
| `src/partie.js` | Trouvés, taps, temps | oui |
| `src/sauvegarde.js` | Progression et record (meilleur temps) par ville (`localStorage`) | oui |
| `src/hud.js` | Affichage : accueil (mode Cacher, cartes « Mes défis »), compteur, chrono, aide, toasts, fin, confettis, HUD « Cacher », panneau du prénom | formats |
| `src/partage.js` | Textes de score et d'invitation, partage natif ou copie (`partagerAvecRetour`), titres de fin (`sousTitreFin`) | oui |
| `src/defi.js` | Code du lien de défi (encode, décode, vérifie), messages de rejet, textes, liens `&defi=` et `&cacher=` | oui |
| `src/cachettes.js` | Charge `cachettes.json` ; aimant qui pose un canard sur la cachette la plus proche ; `canardsDuDefi` | oui |
| `src/mesdefis.js` | « Mes défis », dernier prénom, clé de progression d'un défi reçu | oui |
| `src/cacher.js` | Écran « Cacher mes canards » : poser, retirer, brouillon automatique, partager | — |
| `src/mesure.js` | Mesure de fluidité, avec `&debug` dans l'adresse (chargé à la demande) | oui |
| `src/son.js` | « coin coin » et musique de fin enregistrés (`assets/sons/`), cri synthétisé en secours, bouton son | oui |

Tests : `app/tests/` (85). Polices Fredoka et Nunito embarquées via `@fontsource`.

## Règles qui définissent le jeu (ne pas casser)

- Canards et 22 leurres partagent le même jaune (`#FFD21E`) et le même gabarit (0,50 m
  modélisé, 0,35 m en jeu). Le seul jaune du décor est la couleur `jaune` (gros leurres :
  taxis, stores, rickshaws). Si un canard se distingue à zoom moyen, le jeu est cassé.
- Bec et œil visibles seulement à partir de 28 px à l'écran ; un tap ne trouve un canard
  qu'à partir de ce zoom.
- Un canard par case d'une grille 6 × 5 ; visibilité 30–80 % (jamais < 15 %), bec et un
  œil tournés vers la caméra ; « derrière une vitre » vérifié par lancer de rayons.
- Mode défi : un canard de défi n'est posé que sur une cachette de `cachettes.json`
  (garantie visible, mêmes règles que les 30 canards) ; son numéro est sa position dans la
  liste, ne jamais réordonner ce fichier.
- Pas de pénalité pour un tap raté. Temps, taps et précision affichés en direct.
- Sans `?ville=` dans l'adresse (ou avec une ville inconnue) : écran d'accueil. Changer de
  ville recharge la page : une seule scène 3D par page.
- Sauvegarde par ville et par `version` : augmenter la `version` d'une ville quand ses
  canards changent de place (les records de cette ville repartent alors de zéro).

## Commandes

Blender n'est pas dans le PATH : `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`
(trouvé tout seul par `tout_generer.sh`).

```bash
python -m unittest discover -s blender/tests -t blender   # 47 tests, sans Blender, quelques secondes
bash blender/tout_generer.sh                              # tout régénérer (moins de 10 min)
bash blender/tout_generer.sh lille                        # une ville
cd app && npm run dev                                     # http://localhost:5173 (accueil) ou /?ville=lille
cd app && npm test                                        # 85 tests
cd app && npm run lint                                    # no-undef : bloque la publication si un nom n'est pas déclaré
```

Le serveur de dev se lance avec la configuration `canard-3d` de `.claude/launch.json`. Si le
port 5173 est déjà pris, c'est en général ce même serveur, déjà lancé par l'utilisateur :
ouvrir directement `http://localhost:5173`. Recettes pour tester dans le navigateur intégré
(taille d'écran, sauvegarde et record injectés, zoom sur un canard, sons neutralisés) :
`docs/05`, section « Tester dans le navigateur ».

## État (22/11/2026)

- **Générateur** : quatre villes publiées ; style dessiné (toon + traits d'encre) ; vitres ;
  kit de 81 modèles (passants, véhicules, animaux, tags, végétation) ; 18 saynètes ;
  22 leurres ; validation des thèmes avec messages clairs ; une ville minimale (id, nom,
  graine) se génère, garanti par un test.
- **App** :
  - écran d'accueil (tickets de ville avec progression et pastille ★ du record) ;
  - temps, taps et précision en direct ; aide en bas de l'écran qui s'efface après 5 s ;
  - partage du score et invitation ; interface « autocollant de BD » ;
  - sons enregistrés à la voix par l'utilisateur : « coin coin » à chaque canard trouvé,
    musique de fin après le dernier ; cri synthétisé en secours ; bouton pour couper le son ;
  - record (meilleur temps, puis moins de taps) par ville, gardé quand on rejoue ; écran de
    fin « Nouveau record ! » ou « Ton record » ;
  - panneau de mesure de fluidité avec `&debug` dans l'adresse.
- **Mesuré** : fluidité sur un iPhone récent, Delhi (la plus lourde) : 59 images/s sans
  saccade, 4 à 7 ms par image, 590 000 à 810 000 triangles. Le jeu y tourne bien.
- **Vérifié par l'utilisateur sur téléphone (22/11/2026)** : une partie complète jouée,
  difficulté « bien réglée mais parfois assez facile » ; fluide sur un téléphone modeste
  (chiffres de `&debug` non relevés) ; « coin coin » et musique de fin écoutés.
- **Mode « Cacher mes canards » : fait (22/11/2026)**. On cache de 1 à 30 canards sur des
  cachettes garanties visibles (`cachettes.json`, 408 à 1123 par ville), on envoie un lien
  `?ville=…&defi=<code>`, l'ami les retrouve (progression gardée à part, record de la ville
  intact). « Mes défis » sur l'accueil : envoyer, modifier, supprimer. Spec
  `docs/superpowers/specs/2026-11-22-cacher-mes-canards-design.md`, plan
  `docs/superpowers/plans/2026-11-22-cacher-mes-canards.md`. Vérifié dans le navigateur à
  390 px ; pas encore sur un vrai téléphone.
- **Ensuite** : un niveau « expert » répondrait au « parfois assez facile » ; puis les
  restes du mode défi (liste dans `docs/06`, « Restes du mode défi »).

## Pièges pour Claude

- **Ne jamais supprimer `assets/scenes.json`** : l'app ne démarre plus. `place_objets.py`
  met à jour la ligne de sa ville (avec `embleme`, `couleur`, `ordre`, `canards`).
- `location.reload()` et tout départ de page déclenchent `pagehide`, donc une sauvegarde :
  « Rejouer » coupe les sauvegardes (`rejoue = true` dans `main.js`). Pour injecter ou
  effacer une sauvegarde de test, le faire depuis une page sans jeu (`/scenes.json`).
- Augmenter la `version` d'une ville, ou régénérer son placement, change son `empreinte` :
  les défis déjà envoyés pour cette ville deviennent invalides (le jeu le dit au joueur).
- Publication : l'étape `deploy-pages` échoue parfois pour une raison passagère de GitHub
  (build et tests verts). Republier (`git commit --allow-empty -m "ci: republier"`, push,
  pushs espacés de 2 min) ; vérifier le site avec `?v=<sha>` (cache Pages ~10 min). Détails :
  `docs/05`.
- Ajouter un tirage aléatoire dans du code commun du générateur déplace les canards de
  **toutes** les villes : régénérer tout et augmenter `version`.
- Décor : ne pas utiliser `bmesh` (plus de 7 min par ville) ; passer par `citygen/maillage.py`.
- Blender 5 : matériaux et monde créés par script ont un arbre de nœuds vide ; créer les
  nœuds explicitement (`material()` dans `blender/citygen/geo.py`).
- Git Bash : un heredoc contenant `\n`, des apostrophes ou `\U` se casse. Écrire le script
  dans un fichier, ou utiliser l'outil d'édition.
- Python sous Windows : afficher un émoji (thèmes, `scenes.json`) plante avec
  `UnicodeEncodeError` ; préfixer `PYTHONIOENCODING=utf8`.
- Navigateur intégré de Claude :
  - volet masqué = page de taille nulle (fixer une taille avec `resize_window`, la remettre
    ensuite) et `requestAnimationFrame` presque arrêté : les images/s de `&debug` y sont
    fausses, seul « image calculée » est fiable ;
  - zoomer avec des `WheelEvent` synthétiques ; les `PointerEvent` synthétiques échouent,
    faire de vrais clics (capture d'écran d'abord pour avoir le repère des coordonnées) ;
  - pas de `navigator.share` : le partage passe par la copie, qui écrit dans le
    presse-papiers de l'utilisateur : neutraliser `navigator.clipboard.writeText` d'abord ;
    `window.confirm` (suppression d'un défi) bloque le navigateur : `window.confirm = () => true` ;
  - modifier un fichier source recharge la partie ouverte (Vite) : la sauvegarde de
    `pagehide` réécrit alors l'état en mémoire (et peut noter un record). Remettre les
    sauvegardes de test à zéro depuis `/scenes.json` à la fin.
- Ne pas déclencher le son dans le vrai navigateur pendant les tests (rallumer le son joue
  un cri) : analyser les sons avec un `OfflineAudioContext`, ou neutraliser `start` **et**
  `stop` de `AudioScheduledSourceNode` avant de jouer (recettes dans `docs/05`).
- Un son ne doit jamais bloquer la partie : `coin()` et `fanfare()` avalent toute erreur
  audio. Garder ce `try/catch` (sans lui, une erreur empêchait l'écran de fin).
- `assets/sons/` est le seul dossier de `assets/` écrit à la main (pas par le générateur) :
  sons découpés et convertis en MP3 avec ffmpeg (recette dans `docs/05`). Ne jamais
  récupérer un son sur YouTube ; un son d'Internet doit avoir une licence claire.
- Vite renvoie `index.html` pour un fichier absent : un JSON « illisible » = fichier manquant.
- Les fiches de `.claude/skills/` (dépôt `arjun988/blender-skills`) sont des conseils, pas
  des modèles. Ne pas citer de noms de skills sans avoir listé le dépôt.
- Le serveur MCP `blender` n'est pas utilisé : tout tourne en `blender --background`.
- Les générations Blender des quatre villes sont longues : demander avant de les relancer
  toutes si ce n'est pas nécessaire.

## Préférences de travail

- Commiter et pousser au fil de l'eau ; mettre la doc à jour à chaque changement
  (`docs/` d'abord, puis ce fichier s'il change l'état, les fichiers ou les pièges).
- Quand le code contredit la spec (`docs/superpowers/specs/`), corriger la spec et
  journaliser l'écart dans son journal des révisions.
- Vérifier dans le navigateur ce qui se voit (captures à taille de téléphone, 390 px) avant
  d'annoncer qu'une modification d'interface est faite.
- Répondre en français.
