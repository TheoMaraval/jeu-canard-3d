# 01 — Comprendre le projet

## Le jeu en bref

L'arrivée sur le site ouvre un **écran d'accueil** : une carte par ville, avec sa
progression (« Nouvelle partie », « 12 / 30 trouvés », « Terminée en 12:34 »). Un lien
du type `…/?ville=lille` ouvre directement la ville ; c'est ce que contiennent les liens
partagés. Pendant la partie, le bouton « Villes » ramène à l'accueil et le bouton
« Partager » envoie sa progression ; à la fin, « Partager mon score ». Sur téléphone, le
partage ouvre le menu natif (SMS, messageries) ; sur ordinateur, le message et le lien
sont copiés.

Le joueur cherche **30 canards en plastique jaunes** cachés dans un quartier dessiné, dense,
plein de passants et de situations loufoques. Quatre villes : Paris, New York, Lille, Delhi.

**Mode « Cacher mes canards »** : un joueur cache lui-même de 1 à 30 canards, puis envoie
un lien de défi ; son ami les retrouve. Voir « Le mode défi » plus bas.

La boucle de jeu :

1. **Balayer** la ville à zoom moyen : elle est parsemée de petits objets jaunes.
2. **Repérer** un point jaune qui pourrait être un canard.
3. **Zoomer** : à partir d'une certaine taille à l'écran, le canard montre son bec orange et
   son œil noir. Les leurres, eux, restent des objets ordinaires.
4. **Taper** dessus : il passe au vert, +1 au compteur. Un tap raté ne coûte rien.
5. À 30/30 : écran de fin avec le temps, le nombre de taps et la précision.

## Les règles qui font le jeu

Ces règles sont garanties par le code. Si l'une casse, le jeu devient trop facile ou injuste.

| Règle | Ce qui la garantit |
|---|---|
| Canards et leurres ont **le même jaune et la même taille** | Un seul matériau `MAT_Jaune` (#FFD21E) ; `build_assets.py` refuse tout modèle dont la partie jaune dépasse 0,50 m |
| **Le jaune seul ne suffit pas** : le décor a de gros objets jaunes (taxis, stores, rickshaws) | Le seul jaune autorisé dans une palette est la couleur `jaune` ; un test le vérifie pour chaque ville |
| **Le bec et l'œil n'apparaissent qu'en zoomant** | L'app affiche un canard sans bec ni œil (`Canard_Loin`) tant qu'il fait moins de 28 px à l'écran |
| **Un tap ne trouve rien en vue d'ensemble** | Le tap n'est testé que si les canards sont « révélés » (≥ 28 px) |
| **Les 30 canards couvrent toute la carte** | Grille 6 × 5 : un canard par case |
| **Un canard est toujours trouvable** | Visible à 30–80 % depuis la caméra (jamais moins de 15 %), bec et un œil tournés vers la caméra |
| **« Derrière une vitre » est vrai** | Une cachette `vitre` est refusée si une seule partie visible ne passe pas à travers la vitre |
| **Pas de pénalité** | Un tap raté compte dans les statistiques, sans autre effet |

## Comment le projet est construit

```
 blender/themes/<ville>.json          réglages d'une ville (+ _commun.json pour les valeurs par défaut)
            │
            ▼
 ┌──────── générateur (Python pur, testé sans Blender) ───────────────────────────┐
 │  citygen/layout.py     plan du quartier : bâti, décor, cachettes candidates    │
 │  citygen/placement.py  choix des 30 canards et des 270 leurres                 │
 │  citygen/cachettes.py  cachettes du mode défi : filtre, empreinte (CRC32)      │
 │  citygen/maillage.py   primitives → triangles                                  │
 └─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
 ┌──────── Blender 5.3, en ligne de commande ─────────────────────────────────────┐
 │  build_assets.py    canard + 22 leurres jaunes          → assets/props.glb     │
 │  build_kit.py       81 modèles de décor (passants,      → assets/kit.glb       │
 │  (+ kit_loufoque)   véhicules, animaux, tags, arbres…)                         │
 │  build_quartier.py  bâti de la ville + liste du décor   → quartier.glb,        │
 │                                                           decor.json           │
 │  place_objets.py    mesure ce qui est visible (rayons)  → placements.json,     │
 │                     et place canards et leurres           cachettes.json,      │
 │                                                           scenes.json          │
 │  render_ville.py    images de contrôle                  → docs/previews/       │
 └─────────────────────────────────────────────────────────────────────────────────┘
            │  fichiers dans assets/
            ▼
 ┌──────── application web (app/, Vite + Three.js) ───────────────────────────────┐
 │  scene.js     charge les fichiers, dessine (style « dessin » : traits d'encre)  │
 │  vue.js       position, zoom, seuil de révélation          (pur, testé)        │
 │  entrees.js   doigts, souris, molette                                          │
 │  picking.js   quel canard est sous le doigt                (pur, testé)        │
 │  partie.js    trouvés, taps, temps                         (pur, testé)        │
 │  sauvegarde.js progression et record par ville             (pur, testé)        │
 │  hud.js       accueil, compteur, chrono, précision, écran de fin, mode Cacher  │
 │  partage.js   messages de score et d'invitation, partage   (pur, testé)        │
 │  defi.js      code du lien de défi, rejets, textes         (pur, testé)        │
 │  cachettes.js chargement de cachettes.json, aimant         (pur, testé)        │
 │  mesdefis.js  « Mes défis », dernier prénom                (pur, testé)        │
 │  cacher.js    écran « Cacher mes canards »                                     │
 │  son.js       « coin coin » et musique de fin, bouton son  (testé)             │
 │  mesure.js    mesure de fluidité (&debug dans l'adresse)   (testé)             │
 └─────────────────────────────────────────────────────────────────────────────────┘
            │  GitHub Actions à chaque envoi sur main
            ▼
     https://theomaraval.github.io/jeu-canard-3d/
```

Le générateur et l'app ne se parlent **que par les fichiers de `assets/`**. On peut donc
changer l'un sans toucher à l'autre, tant que les formats ci-dessous sont respectés.

## Les dossiers

| Dossier | Contenu |
|---|---|
| `blender/themes/` | Une ville par fichier, plus `_commun.json` (valeurs par défaut) |
| `blender/citygen/` | Le générateur, en Python pur (sauf `geo.py`, seul à utiliser Blender) |
| `blender/tests/` | 55 tests du générateur, lancés sans Blender |
| `blender/*.py` | Les étapes Blender ; `tout_generer.sh` les enchaîne |
| `blender/*.blend`, `blender/scenes/` | Fichiers Blender générés (utiles pour inspecter, régénérables) |
| `assets/` | **Ce que l'app charge** : `props.glb`, `kit.glb`, `scenes.json`, `scenes/<ville>/`, et `sons/` (seul dossier écrit à la main, pas par le générateur) |
| `app/` | L'application ; `app/tests/` : 90 tests |
| `.github/workflows/pages.yml` | La publication automatique |
| `.claude/skills/` | Fiches de conseils Blender (dépôt `arjun988/blender-skills`, licence MIT) |
| `docs/previews/` | Rendus Blender de contrôle (sans traits d'encre : le vrai rendu est dans l'app) |

## L'interface

Style « autocollant de BD », assorti au rendu de la ville : contours d'encre épais, ombres
décalées nettes, boutons qui s'enfoncent à l'appui, fond papier tramé. Tout est dans
`app/src/style.css`, réglé par des variables en tête de fichier (`--encre`, `--jaune`,
`--orange`, `--papier`…).

- Polices : Fredoka (titres) et Nunito (texte), **embarquées dans le site** (paquets
  `@fontsource`), pas chargées chez Google : aucune adresse de joueur n'est transmise.
- Icônes : tracés SVG dans `index.html` (`<symbol id="i-…">`), réutilisés avec `<use>`.
  Les émojis ne servent qu'aux emblèmes des villes.
- Mascotte : un canard dessiné en SVG (`<symbol id="canard">`), sur l'accueil, le
  chargement, l'écran de fin et le compteur.
- Retours de jeu : le compteur saute, un « +1 » jaillit, le téléphone vibre et un canard
  fait « coin coin » quand on en trouve un ; une petite musique, confettis, étoiles et titre selon la précision à la fin
  (`titreFin` : 70 % et plus « Œil de lynx », 40 % « Fin limier », sinon « Chasseur tenace »).
- Son (`app/src/son.js`) : deux **enregistrements** faits à la voix par l'auteur du jeu,
  dans `assets/sons/`, joués avec Web Audio :
  - `coin.mp3` (1,25 s, 16 Ko, deux « coin ») quand on trouve un canard ; chaque cri est
    joué un peu plus vite ou plus lentement (±6 %, `vitesseCri()`) pour varier ;
  - `fin.mp3` (1,8 s, 22 Ko) quand on trouve le dernier canard, une seconde après son
    « coin coin » (`fanfare(1)` dans `main.js`). Pas de musique en rouvrant une partie
    déjà finie.

  Les fichiers sont téléchargés au lancement de la partie et décodés au premier contact.
  Tant que le « coin coin » n'est pas prêt, ou s'il manque, un cri **synthétisé** le
  remplace (`parametresCoin()`) ; la musique, elle, n'a pas de remplaçant.
  Le bouton haut-parleur coupe tout, et le choix est gardé sur l'appareil. Sur iPhone, le
  son est débloqué au premier contact avec la ville ; le bouton silencieux du téléphone
  le coupe aussi. Pour changer un son, remplacer le fichier (voir [05](05-publier-et-depanner.md)).
- Aide en bas de l'écran : « Zoome sur un point jaune… » en vue d'ensemble, « Touche le
  canard… » une fois zoomé. Chaque message reste 5 s (`DUREE_AIDE_MS` dans `hud.js`) et
  ne revient que lorsqu'on franchit le zoom de révélation.
- Accessibilité : cibles tactiles de 44 px au moins, contour orange au clavier, animations
  coupées si le système demande moins de mouvement.

## Repères et caméra

- **Blender** : Z vers le haut, carte centrée sur l'origine, en mètres.
- **Fichiers JSON et app** : repère glTF, Y vers le haut. Conversion : `(x, y, z)` Blender
  devient `(x, z, -y)`.
- **Caméra de jeu** : orthographique, fixe, vue isométrique (azimut 45°, élévation
  35,264°), placée côté sud-est. Le joueur ne peut ni la tourner ni l'incliner.
- Conséquence : seules les **façades sud et est** sont visibles. Le générateur ne détaille
  qu'elles, et une cachette sur une façade nord ou ouest a une visibilité nulle et n'est
  jamais retenue. Les éléments hauts (tours, beffroi, porte monumentale) sont placés au
  nord-ouest pour ne rien masquer.

## Les fichiers échangés

### `assets/scenes.json` — la liste des villes

```json
[ { "id": "paris", "nom": "Paris — Grands Boulevards", "version": 3, "ordre": 0,
    "embleme": "🥐", "couleur": "#3F6FD8", "canards": 30, "empreinte": "aegt" }, … ]
```

`ordre` fixe la place sur l'écran d'accueil, `embleme` l'icône de la ville, `couleur` le
bandeau de sa carte, `canards` le
total affiché dans la progression ; `version` sert à la sauvegarde (voir plus bas).
`empreinte` (4 caractères base 36) est celle de `cachettes.json` : l'accueil sait ainsi, sans
charger ce fichier, si un défi de « Mes défis » vaut encore (voir plus bas).
Le nom est découpé au tiret long « — » : « Paris » en titre, « Grands Boulevards » dessous.

### `assets/scenes/<ville>/placements.json` — canards et leurres

```json
{ "ville": "paris", "version": 3, "taille": 120, "echelle": 0.7, "gabarit": 0.35,
  "camera": { "azimut": 45.0, "elevation": 35.264, "vers_camera": [0.577, 0.577, 0.577] },
  "objets": [
    { "id": "canard-01", "type": "Canard", "position": [-49.4, 19.15, 51.95],
      "rotation": 0.436, "visibilite": 0.556, "lieu": "balcon", "zone": "A1" },
    { "id": "leurre-011", "type": "Leurre_Jardiniere", … } ] }
```

- `lieu` : `sol`, `balcon`, `toit` ou `vitre`.
- `zone` : la case de la grille 6 × 5, de `A1` (coin sud-ouest de la carte) à `F5` (coin nord-est). Les lettres vont d'ouest en
  est, les chiffres du sud au nord.
- `assoupli` (rare) : la case n'offrait aucune cachette à moitié visible, la plage de
  visibilité a été élargie pour ce canard.

### `assets/scenes/<ville>/cachettes.json` — où un canard de défi peut se cacher

```json
{"ville": "lille", "version": 3, "empreinte": "cccn", "echelle": 0.7, "gabarit": 0.35,
 "distance_min_canards": 6.0, "cachettes": [
[16.22, 0.0, -31.825, 5.061, 0.556, "sol"],
[-50.876, 16.132, 48.318, 0.436, 1.0, "toit"],
… ]}
```

- **Une cachette par ligne** : `[x, y, z, rotation, visibilite, "lieu"]`, repère glTF comme
  `placements.json`. Son **numéro est sa position dans la liste** (0 pour la première) : c'est
  ce numéro que le lien de défi transporte. Ne jamais trier ni filtrer ce fichier à la main.
- D'où viennent les cachettes : d'abord les `slots` du plan (ceux d'où sont tirés les canards
  du jeu), puis les **cachettes denses** de `make_layout(theme)["cachettes_denses"]` : chaque
  fenêtre non condamnée (3 places à l'appui), les vitrines (tous les 0,6 m), les balcons
  (0,8 m), une grille de 1,2 m sur les toits plats et les plateaux de mansarde, une grille de
  1 m sur trottoirs et places (2 m sur la chaussée). `layout.py` les pose **sans aucun tirage
  au sort** et `place_objets.py` les mesure **après** avoir choisi canards et leurres : la
  partie normale ne change pas (`placements.json` identique, même `version`). Détails :
  `docs/04-etendre-le-generateur.md`, « Cachettes denses ».
- Une cachette est gardée si sa visibilité est ≥ 0,3, si une orientation montre le bec et un
  œil, et si elle est à `distance_min` (1 m, `_commun.json`) au moins de chaque leurre. Une
  cachette à moins de 0,35 m d'une cachette déjà gardée est retirée (`dedoublonner`).
- `echelle` sert à calculer le centre du canard à l'écran ; `distance_min_canards` est
  l'écart minimal entre deux canards d'un même défi.
- **`empreinte`** : CRC32 du contenu de `cachettes`, en 4 caractères base 36. Relancer
  `place_objets.py` réécrit `cachettes.json` **et** l'empreinte (dans le fichier et dans
  `scenes.json`). Si l'empreinte change, les défis déjà envoyés pour cette ville sont
  refusés par le jeu (« créé pour une ancienne version »).
- Nombre de cachettes (22/11/2026, avec les cachettes denses) :

  | Ville | Total | sol | vitre | toit | balcon | Avant les denses |
  |---|---|---|---|---|---|---|
  | Paris | 4654 | 1367 | 1353 | 1353 | 581 | 1123 |
  | New York | 4783 | 1611 | 1140 | 1484 | 548 | 1038 |
  | Lille | 2659 | 1277 | 864 | 518 | — | 408 |
  | Delhi | 3379 | 890 | 869 | 1620 | — | 827 |

  Lille a peu de toits plats (pignons) ; Delhi n'a pas de balcon ouvert (jharokhas fermés).
  Beaucoup de candidates au sol sont écartées parce que cachées par les immeubles (vues
  depuis la caméra, au nord-ouest de chaque îlot).
- Chargé seulement en mode défi (cacher ou jouer un défi), 117 à 215 Ko selon la ville
  (16 à 29 Ko compressé, comme le sert GitHub Pages).
- Absent : le jeu dit que le mode défi n'est pas prêt pour la ville.
- Produit par `citygen/cachettes.py` (pur, testé), appelé par `place_objets.py`.

### `assets/scenes/<ville>/decor.json` — passants, véhicules, animaux, objets

```json
{ "instances": [ { "type": "Voiture", "p": [43.7, 0.0, -22.4], "r": 0.0, "s": 1.0,
                   "c": { "caisse": "#FAF6EC" } }, … ] }
```

`type` est un modèle de `kit.glb` ; `c` donne la couleur de chaque partie teintable du
modèle (son « rôle » : `haut`, `bas`, `peau`, `caisse`, `toile`…).

### `assets/scenes/<ville>/quartier.glb` — le bâti

Deux objets : `Quartier` (sol, rues, immeubles, toits, façades) et `Vitres` (translucides).

## Le mode défi (« Cacher mes canards »)

Pas de serveur : tout tient dans le lien. Le joueur pose ses canards sur des cachettes
garanties visibles ; l'ami ouvre le lien et joue une partie normale avec ces canards à la
place des 30 habituels (compteur 0 / n, mêmes règles de zoom et de tap).

| Module | Rôle |
|---|---|
| `src/defi.js` | Encode, décode et vérifie le code du lien ; messages de rejet ; textes d'invitation, de fin et de temps renvoyé ; liens `?ville=…&defi=…` et `?ville=…&cacher=<id>` |
| `src/cachettes.js` | Charge `cachettes.json` ; `aimanter` (tap + cachettes projetées + canards posés : numéro ou raison de refus) ; `canardsDuDefi` |
| `src/mesdefis.js` | « Mes défis », dernier prénom, clé de progression d'un défi reçu |
| `src/cacher.js` | Écran « Cacher » (pas de test unitaire : vérifié dans le navigateur) |

Les autres modules ont gagné : `partage.js` (`partagerAvecRetour`, `sousTitreFin`),
`scene.js` (canards fournis, emplacements vides, `placerCanards`, `rebondir`), `hud.js`
(HUD du mode Cacher, panneau du prénom, cartes « Mes défis », mode Cacher de l'accueil) et
`main.js` (aiguillage : accueil, partie, défi reçu, écran « Cacher »).

### Le lien de défi

`…/?ville=lille&defi=<code>`. Le code est en base64url (sans `=`) sur des octets
(`FORMAT` = 1 dans `defi.js`) :

| Octets | Contenu |
|---|---|
| 1 | Format (`1`) |
| 1 | `version` de la ville |
| 3 | `empreinte` des cachettes (4 caractères base 36) |
| 1 | Nombre de canards *n* (1 à 30) |
| 2 × *n* | Numéros des cachettes (0 à 65 535), 2 octets chacun |
| reste | Prénom en UTF-8, 20 caractères au plus (vide = anonyme) |

Le prénom est nettoyé (`nettoyerPrenom` : sans caractères de contrôle ni inversions de
sens). `ville` reste un paramètre à part. Rejets (`decoderDefi`, `verifierDefi`), suivis
d'un message et d'un retour à l'accueil :

| Raison | Cas | Message |
|---|---|---|
| `abime` | Code illisible, numéro hors liste, doublon, *n* hors 1–30 | « Ce lien de défi est abîmé. » |
| `format` | Premier octet inconnu | « …version plus récente du jeu : recharge la page. » |
| `version` / `empreinte` | La ville a changé depuis la création du défi | « …créé pour une ancienne version de Lille : demande à Camille d'en refaire un. » |
| `pas-pret` | `cachettes.json` absent | « Le mode défi n'est pas encore prêt pour Lille. » |

### Comportement de l'écran « Cacher »

- Le canard se pose par **aimant** : tap au zoom de révélation, sur la cachette libre la plus
  proche à 40 px au plus qui respecte l'écart minimal. Raisons de refus : `zoom`, `aucune`,
  `trop-pres`, `plein` (30 canards). Taper un canard posé le retire.
- Le brouillon est enregistré dans « Mes défis » à **chaque canard posé ou retiré** ; un
  brouillon vidé de ses canards est supprimé. Son identifiant est mis dans l'adresse
  (`history.replaceState`) : un rechargement rouvre le même brouillon.
- Un brouillon périmé (version ou empreinte changée) ouvert par `cacher=<id>` : un nouveau
  défi est commencé, avec un message.
- Accueil : « Cacher mes canards » transforme les tickets en « Où cacher tes canards ? »
  (le bouton devient « Annuler »). Cartes « Mes défis » : **Envoyer**, **Modifier**,
  **Supprimer** (avec confirmation). Un défi périmé (version ou empreinte changée, ou ville
  disparue) est grisé et ne peut plus qu'être supprimé. `pageshow` redessine l'accueil
  après un retour arrière.

## La sauvegarde

La progression est gardée dans le navigateur du joueur (`localStorage`), sous la clé
`jeu-canard-3d:<ville>:v<version>`. Quand une ville est régénérée et que ses canards
changent de place, **augmenter sa `version`** (dans son thème) : les anciennes sauvegardes,
devenues fausses, seront ignorées au lieu d'afficher des canards « trouvés » ailleurs.

**Le record** (meilleur résultat d'une ville terminée) est gardé à part, sous
`jeu-canard-3d:<ville>:v<version>:record` (`{ ecouleMs, taps }`) :

- le meilleur est le **plus rapide** ; à temps égal, celui qui a **le moins de taps**
  (`meilleur()` dans `sauvegarde.js`) ;
- il est noté à chaque fin de partie (`retenirRecord()`), et « Rejouer » n'efface que la
  partie, jamais le record ;
- l'écran de fin compare la partie au record d'avant : « Nouveau record ! L'ancien : 12:34 »
  (pastille jaune) ou « Ton record : 8:12 » ; rien à la première partie finie
  (`texteRecord()` dans `partage.js`) ;
- l'accueil affiche le record en pastille ★ dans le bandeau du ticket de la ville. Une
  partie finie avant l'arrivée des records compte comme record ;
- augmenter la `version` d'une ville efface aussi ses records : ses canards ont changé,
  les anciens temps ne se comparent plus.

**Mode défi** : deux clés et une famille de clés de plus (`mesdefis.js`) :

| Clé | Contenu |
|---|---|
| `jeu-canard-3d:mes-defis` | Liste des défis créés ici : `{id, ville, version, empreinte, prenom, numeros, cree}` |
| `jeu-canard-3d:prenom` | Dernier prénom saisi, proposé d'office au défi suivant |
| `jeu-canard-3d:defi:<code>` | Progression d'un défi **reçu** (même forme qu'une partie : `{trouves, taps, ecouleMs}`) ; la partie normale et le record de la ville ne sont pas touchés |

## Ce qui est vérifié, ce qui ne l'est pas

- Les 55 tests du générateur et les 93 de l'app passent. GitHub relance à chaque publication
  ceux de l'app, précédés de `npm run lint` (ESLint `no-undef` : un nom non déclaré, par
  exemple un import retiré par erreur, bloque la publication).
- Le mode défi a été vérifié dans le navigateur à 390 px (cacher, partager, ouvrir le lien,
  trouver, « Mes défis ») ; l'écran « Cacher » n'a pas de test automatique. Pas encore essayé
  sur un vrai téléphone.
- Les quatre villes ont été contrôlées à l'image dans un navigateur d'ordinateur.
- **Fluidité** : mesurée sur un iPhone récent (Delhi, la ville la plus lourde) : 59 images/s
  sans saccade, 4 à 7 ms par image, malgré 590 000 à 810 000 triangles. Vérifiée aussi par
  l'utilisateur sur un téléphone modeste : fluide (chiffres non relevés). Outil : `&debug`
  dans l'adresse, voir [05](05-publier-et-depanner.md).
- **Sons** : écoutés sur téléphone par l'utilisateur.
- **Difficulté** : une partie complète jouée sur téléphone (22/11/2026). Verdict : bien
  réglée, mais parfois assez facile. Pas encore modifiée à la suite de ce retour (pistes :
  [03](03-regler-la-difficulte.md), et les niveaux de difficulté de
  [06](06-pistes-d-amelioration.md)).
