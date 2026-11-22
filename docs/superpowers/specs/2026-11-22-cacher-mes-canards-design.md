# Mode « Cacher mes canards » — conception

Date : 2026-11-22. Statut : **approuvée** (conception validée section par section avec
l'utilisateur).

## 1. Objectif

Un joueur cache lui-même ses canards dans une ville, puis envoie un lien ; son ami doit les
retrouver. Point de départ : `docs/06-pistes-d-amelioration.md`, section 1.

**Règle d'or** : un canard caché reste **toujours trouvable**. Celui qui cache ne peut le
poser que sur une cachette mesurée par le générateur, avec les mêmes garanties que les 30
canards habituels (part visible, bec et œil tournés vers la caméra).

## 2. Décisions validées

| Question | Décision |
|---|---|
| Comment on pose | **Tap libre + aimant** : le canard saute sur la cachette valable la plus proche ; rien ne montre les cachettes à l'avance |
| Combien de canards | **Libre, de 1 à 30** ; « Partager » dès le premier |
| Prénom | **Facultatif**, dans le lien ; proposé d'office d'après le dernier défi |
| Garder ses défis | **Liste « Mes défis »** sur le téléphone : renvoyer, modifier, supprimer |
| D'où viennent les cachettes | **Calculées à l'avance par Blender** (`cachettes.json`), pas dans le navigateur |
| Évolution | Le lien porte un **numéro de format** : une future version « pose libre » (visibilité calculée dans le navigateur) restera compatible |

## 3. Les cachettes (générateur)

`place_objets.py` écrit `assets/scenes/<ville>/cachettes.json` à partir des cachettes qu'il
mesure déjà (2 000 à 3 500 par ville). Le filtre est une fonction pure,
`blender/citygen/cachettes.py`, testée sans Blender.

Une cachette est gardée si :

| Règle | Pourquoi |
|---|---|
| Visibilité ≥ 0,3 (borne basse de `visibilite_canard`) | Assez de canard à l'écran pour le repérer |
| `rot_canard` trouvée (bec et un œil visibles) | Sinon on ne le distingue pas d'un leurre, même de près |
| À au moins `distance_min` de chaque leurre de la ville | Pas deux objets jaunes l'un dans l'autre ; les leurres ne bougent jamais, donc l'app n'a rien à retirer |

Pas de borne haute : un canard très visible rend le défi facile, c'est le choix de celui qui
cache.

Format (repère glTF, comme `placements.json`), numéroté par la position dans la liste :

```json
{
  "ville": "lille", "version": 3, "empreinte": "k7f2",
  "echelle": 0.7, "gabarit": 0.35, "distance_min_canards": 6.0,
  "cachettes": [[x, y, z, rotation, visibilite, "lieu"], …]
}
```

- Environ 100 Ko par ville ; chargé seulement en mode défi (cacher ou jouer un défi).
- **`empreinte`** : 4 caractères (base 36) tirés d'un CRC32 du contenu de `cachettes`.
  Si une ville est régénérée sans changer de `version`, les numéros ne correspondent plus :
  l'empreinte le détecte et le jeu refuse le défi au lieu de cacher des canards ailleurs.
- **Aucun tirage aléatoire ajouté** : canards et leurres actuels inchangés, pas de `version`
  à augmenter. Seule l'étape de placement des quatre villes est relancée (les `.blend` sont
  déjà dans `blender/scenes/`).
- `place_objets.py` ajoute aussi `"empreinte"` à la ligne de la ville dans `scenes.json` :
  l'accueil sait ainsi, sans charger `cachettes.json`, si un défi de « Mes défis » vaut encore.
- Écart entre deux canards d'un défi : `distance_min_canards` du thème (6 m aujourd'hui),
  la même règle que le générateur. Valeur à régler au playtest si elle gêne celui qui cache.

## 4. Le lien de défi

`…/jeu-canard-3d/?ville=lille&defi=<code>`

`<code>` est en base64url (sans `=`), sur des octets :

| Octets | Contenu |
|---|---|
| 1 | Format (`1`) |
| 2 | `version` de la ville |
| 3 | `empreinte` des cachettes (les 4 caractères base 36 tiennent dans 3 octets) |
| 1 | Nombre de canards *n* (1 à 30) |
| 2 × *n* | Numéros des cachettes (0 à 65 535) |
| reste | Prénom en UTF-8, 20 caractères au plus (vide = anonyme) |

30 canards et un prénom court : environ 100 caractères. `ville` reste un paramètre à part,
pour que l'aiguillage actuel (`?ville=`) ne change pas.

**Rejets**, avec une raison et un message clair, puis retour à l'accueil :

| Raison | Message (exemple) |
|---|---|
| `abime` (code illisible, numéro hors liste, doublon, *n* hors 1–30) | « Ce lien de défi est abîmé. » |
| `format` (format inconnu) | « Ce défi vient d'une version plus récente du jeu : recharge la page. » |
| `version` ou `empreinte` | « Ce défi a été créé pour une ancienne version de Lille : demande à Camille d'en refaire un. » |

## 5. Ce qui est gardé sur le téléphone

- **« Mes défis »** (`localStorage`) : pour chacun, un identifiant, `ville`, `version`,
  `empreinte`, prénom, numéros de cachettes, date de création. Enregistré **automatiquement**
  à chaque canard posé ou retiré. Un défi dont la ville a changé de version ou d'empreinte
  est grisé « plus valable » et ne peut plus qu'être supprimé.
- **Dernier prénom** : celui du dernier défi partagé, proposé d'office au suivant.
- **Défi reçu** : la progression est gardée par défi (clé tirée du code), pour quitter et
  reprendre. Ni la partie normale ni le record de la ville ne sont touchés. Pas de record
  par défi.
- `localStorage` bloqué (navigation privée) : on peut cacher, partager et jouer ; seule la
  mémoire (« Mes défis », progression) manque.

## 6. Écrans

### Accueil

- Bouton **« Cacher mes canards »** sous les tickets de ville (style autocollant).
- Section **« Mes défis »** si la liste n'est pas vide : une carte par défi (emblème,
  « Lille · 7 canards · 21/11 ») avec **Envoyer**, **Modifier**, **Supprimer** (avec
  confirmation).

### Cacher ses canards (`?ville=<id>&cacher`, ou `&cacher=<identifiant>` pour modifier)

1. « Cacher mes canards » → choix de la ville (mêmes tickets) → rechargement de la page.
2. La ville **sans les 30 canards habituels**, avec tous les leurres. En haut : « 7 / 30
   canards cachés », **Partager** (actif dès 1 canard), menu. En bas, aide : « Zoome, puis
   tape là où cacher un canard ».
3. **Poser** : seulement au zoom de révélation (canard ≥ 28 px), comme pour trouver. Le tap
   est aimanté sur la cachette libre la plus proche à l'écran, à 40 px au plus du doigt ;
   petit rebond. Sinon, un message bref :
   - `zoom` : « Zoome davantage pour cacher un canard » ;
   - `aucune` : « Pas de cachette ici : essaie un rebord, un balcon, un toit… » ;
   - `trop-pres` (toutes les cachettes proches du doigt sont à moins de
     `distance_min_canards` d'un canard posé ; sinon la plus proche qui convient est prise) :
     « Trop près d'un autre canard » ;
   - `plein` (30 canards déjà posés) : « 30 canards au maximum : retires-en un pour le
     déplacer ».
4. **Retirer** : taper un canard déjà posé (priorité sur la pose).
5. **Partager** : panneau « Ton prénom (facultatif) » prérempli, bouton **Envoyer le défi**.
   Partage natif, sinon copie (comme aujourd'hui). Texte : « Camille a caché 7 canards dans
   Lille. À toi de les trouver ! » + lien ; sans prénom : « Un ami a caché… ».

### Jouer un défi (`?ville=<id>&defi=<code>`)

- Chargement : « Le défi de Camille · Lille ».
- Partie normale avec les canards du défi à la place des 30 : compteur 0 / *n*, temps, taps,
  précision, mêmes règles de zoom et de tap.
- **Fin** : « Défi de Camille réussi ! » avec temps, taps, précision, et :
  **Envoyer mon temps à Camille** (« J'ai trouvé tes 7 canards dans Lille en 2:31 ! »),
  **Rejouer**, **Cacher mes canards à mon tour**, **Autres villes**.

## 7. Composants

### Générateur

| Fichier | Rôle |
|---|---|
| `blender/citygen/cachettes.py` (nouveau, testé) | Filtre, format compact, empreinte |
| `blender/place_objets.py` | Appelle `cachettes.py`, écrit `cachettes.json`, ajoute le nombre de cachettes au rapport |

### App

| Fichier | Rôle | Testé |
|---|---|---|
| `src/defi.js` (nouveau) | Encoder / décoder le code, raisons de rejet ; textes d'invitation, de fin et de temps renvoyé | oui |
| `src/cachettes.js` (nouveau) | Charger `cachettes.json` ; l'aimant : tap + cachettes projetées + canards posés → numéro ou raison | oui |
| `src/mesdefis.js` (nouveau) | « Mes défis », dernier prénom, progression d'un défi reçu | oui |
| `src/cacher.js` (nouveau) | Assemble l'écran « Cacher » sur le modèle de `jouer()` | navigateur |
| `src/main.js` | Aiguille : partie normale, `&cacher`, `&defi=` ; la partie normale ne change pas | navigateur |
| `src/scene.js` | Accepte une liste de canards fournie ; 30 emplacements de canards qu'on montre ou cache sans recharger | navigateur |
| `src/hud.js`, `index.html`, `src/style.css` | Bouton d'accueil, cartes « Mes défis », panneau prénom, compteur « cachés », fin de défi | formats |

## 8. Erreurs

| Cas | Comportement |
|---|---|
| `cachettes.json` absent (Vite renvoie `index.html`) | « Le mode défi n'est pas encore prêt pour cette ville », retour à l'accueil |
| Lien rejeté | Message de la section 4, retour à l'accueil |
| `localStorage` bloqué | Jeu et partage fonctionnent, rien n'est gardé |
| Partage impossible | Comme aujourd'hui : le lien est affiché |

## 9. Tests

- **Python** (`blender/tests/`) : filtre (visibilité, orientation, distance aux leurres),
  sortie identique d'un lancement à l'autre, empreinte qui change dès qu'une cachette change.
- **JavaScript** (`app/tests/`) :
  - aller-retour du code : 1 et 30 canards, prénom vide, accents, émoji, prénom tronqué ;
  - rejets : `abime`, `format`, `version`, `empreinte` ;
  - aimant : choix de la plus proche, `aucune`, `trop-pres`, `zoom`, cachette déjà prise ;
  - « Mes défis » : brouillon, modification, suppression, défi grisé, stockage bloqué.
- **Navigateur** (390 px de large) : cacher 3 canards, partager (copie), ouvrir le lien, les
  trouver, écran de fin, carte dans « Mes défis », lien abîmé.

## 10. Livraison

Un commit et un push par étape :

1. Générateur (`cachettes.py`, tests, `place_objets.py`), puis placement relancé sur les
   quatre villes (demander avant de lancer).
2. Modules testés : `defi.js`, `cachettes.js`, `mesdefis.js`.
3. Jouer un défi.
4. Cacher ses canards.
5. « Mes défis » sur l'accueil.
6. Doc : `docs/01` (formats, fichiers), `docs/06` (mode fait), `CLAUDE.md` (état, fichiers,
   nombre de tests).

## 11. Hors périmètre de cette version

- Tester son propre défi avant de l'envoyer.
- Montrer les cachettes possibles.
- Garder la liste des défis reçus.
- Pose libre n'importe où (visibilité calculée dans le navigateur) : prévue par le numéro
  de format du lien.

## Journal des révisions

- 2026-11-22 : première version, validée avec l'utilisateur.
- 2026-11-22 (plan d'implémentation) : `echelle` ajoutée à `cachettes.json` (centre du
  canard) ; `empreinte` ajoutée à `scenes.json` (validité des défis sur l'accueil) ; raison
  `plein` à 30 canards ; l'aimant prend la plus proche cachette **qui respecte l'écart**,
  `trop-pres` seulement si aucune ne le respecte.
- 2026-11-22 (livraison, écarts constatés entre cette spec et le code ; le code fait foi) :
  - le compteur du mode Cacher affiche « 7 / 30 » sans « canards cachés » (place à 390 px) ;
    le mot est porté par l'`aria-label` « Canards cachés » ;
  - le dernier prénom est retenu dès la validation du panneau, même si le partage est
    ensuite annulé (et pas seulement après un partage abouti) ;
  - « Envoyer » dans « Mes défis » réutilise le prénom enregistré avec le défi, sans rouvrir
    le panneau, et ne change pas le dernier prénom ;
  - un brouillon périmé (version ou empreinte changée, numéros invalides) ouvert par
    `cacher=<id>` : un nouveau défi est commencé, avec le message « Ce défi n'est plus
    valable pour <ville> : on en commence un nouveau. » ;
  - un défi dont la ville a disparu de `scenes.json` reste listé, grisé, avec
    « Supprimer » seul (comme un défi périmé) ;
  - un brouillon sans canard n'est pas listé : il est supprimé dès que le dernier canard est
    retiré ;
  - l'identifiant du brouillon est mis dans l'adresse (`history.replaceState`) : un
    rechargement rouvre le même brouillon ;
  - sur l'accueil, le bouton « Cacher mes canards » devient « Annuler » tant que les tickets
    servent à choisir la ville ; les tickets reçoivent alors un libellé « Cacher mes canards
    à <ville> » ;
  - le panneau du prénom se ferme avec Échap (`role="dialog"`), et un double tap sur
    « Envoyer » / « Annuler » est ignoré pendant 400 ms (il retomberait sur la scène) ;
  - en cours de partie, « Partager » d'un défi reçu fait suivre l'invitation au défi ; le
    temps n'est renvoyé qu'une fois le défi fini ;
  - messages de refus de pose terminés par un point ; aide du zoom de près : « Tape pour
    cacher un canard ; tape un canard posé pour le retirer. » ;
  - **non respecté** : § 8 (`localStorage` bloqué) : le lancement échoue encore, les accès
    à `localStorage` n'étant pas gardés (voir « Restes du mode défi » dans `docs/06`) ;
  - tests : 47 Python et 85 JS à la livraison ; `npm run lint` (ESLint `no-undef`) ajouté
    avant les tests dans la publication.
