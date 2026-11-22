# Mode « Cacher mes canards » — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un joueur cache de 1 à 30 canards sur des cachettes garanties visibles, partage un lien, et son ami les retrouve ; les défis créés sont gardés dans « Mes défis ».

**Architecture:** Le générateur écrit `assets/scenes/<ville>/cachettes.json` (toutes les cachettes valables, numérotées, avec une empreinte). L'app encode un défi dans le lien (`?ville=…&defi=<code>` : format, version, empreinte, numéros, prénom) ; un écran « Cacher » (`?ville=…&cacher`) pose les canards par aimant sur ces cachettes. Logique pure dans `defi.js`, `cachettes.js`, `mesdefis.js` (testés) ; assemblage dans `main.js` et `cacher.js`.

**Tech Stack:** Python 3 pur + Blender 5.3 (`--background`), Vite + Three.js, Vitest, `localStorage`.

## Avancement (22/11/2026, pour reprendre dans une autre session)

Exécution par sous-agents (skill `superpowers:subagent-driven-development`), sur `main`,
commit et push à chaque tâche (accord de l'utilisateur). Le placement Blender des quatre
villes est fait : ne pas le relancer.

| Tâches | État | Commits |
|---|---|---|
| 1-2 générateur, `cachettes.json` (paris 1123, new_york 1038, lille **408**, delhi 827 cachettes) | fait, relu | `e244deb`, `81ae7bb` |
| 3-7 modules purs | fait, relu (qualité) | `6b4aba3` … `24939c6` |
| Corrections de relecture | fait | `482863b` |
| 8-9 scène + jouer un défi reçu | fait, vérifié dans le navigateur, relu (qualité) | `ebaa108`, `77952dc` |
| Corrections de relecture 8-9 (clé de sauvegarde unique, « Préparation du défi… », `rebondir` sur l'objet, teintes remises à zéro, `recu`, `{ok}`) | fait | `30f0af5` |
| 10 écran « Cacher » | fait, vérifié dans le navigateur (390 px, cachettes 150, 0, 300 de Lille), relu (spec + qualité) | `eda11fc` |
| Corrections de relecture 10 (id du brouillon dans l'adresse, champ prénom sélectionnable sur iOS, panneau `role=dialog` + Échap + retour du focus, double tap bloqué 400 ms, brouillon abîmé ou périmé → nouveau défi avec message, erreur d'encodage affichée, chargement avant `cachettes.json`) | fait, revérifié | `8e8ccfa` |
| Correctif : accueil cassé (`charger` retiré par erreur en `30f0af5`, publié de 14 h 26 à la republication suivante) | fait, vérifié | `871dacf` |
| 11 accueil « Mes défis » | fait, vérifié dans le navigateur (390 px et ordinateur) ; relecture en cours | `e891309` |
| 12 doc | à faire | |

Écarts par rapport au texte ci-dessous, à appliquer en reprenant :

- **`encoderDefi` lève une erreur** si l'empreinte n'est pas 4 caractères `[0-9a-z]` ou si
  `numeros` n'a pas 1 à 30 entiers 0–65535 ; `nettoyerPrenom` retire aussi caractères de
  contrôle et d'inversion de sens. `chargerCachettes` exige `distance_min_canards` et
  `empreinte`. Tests : 47 Python, 85 JS (avant les tâches 10-11).
- **Lille n'a que 408 cachettes** (pas de balcons) : dans les vérifications navigateur,
  utiliser des numéros < 408 (par ex. 0, 150, 300 au lieu de 200, 900, 1800).
- Tâche 9 étape 8.3 : `defi=abc` donne le message « version plus récente » (premier octet
  ≠ 1 → `format`), pas « abîmé » ; c'est correct. `defi=AQ` donne « abîmé ».
- Points de relecture laissés pour plus tard (mineurs) : `chrono` importé de `hud.js` par
  `defi.js` (dépendance inversée), constante `HAUTEUR_CENTRE` en double (`scene.js`,
  `cachettes.js`), pas de plafond ni de ménage des clés `jeu-canard-3d:defi:*` (à noter
  dans `docs/06` à la tâche 12).
- À noter dans le journal de la spec (tâche 12) : compteur « 7 / 30 » sans le mot « cachés »
  (place à 390 px) ; le dernier prénom est retenu dès la validation du panneau, même si le
  partage est ensuite annulé ; un brouillon périmé ouvert par `cacher=<id>` démarre un
  nouveau défi avec un message. À noter dans `docs/06` : `localStorage` bloqué fait encore
  échouer le lancement (défaut antérieur, aussi dans `jouer`) ; panneau prénom sans piège à
  focus (un `<dialog>` serait mieux, comme pour l'écran de fin) ; champ prénom à essayer sur
  un vrai iPhone.
- Vérifications navigateur : sauvegardes à lister puis restaurer depuis `/scenes.json` ;
  couper le son (`jeu-canard-3d:son` = `non`) et neutraliser `start`/`stop` avant tout tap.

**Spec :** `docs/superpowers/specs/2026-11-22-cacher-mes-canards-design.md`. Lire aussi `CLAUDE.md` (pièges) et `docs/05` (« Tester dans le navigateur »).

**Commandes :**

```bash
python -m unittest discover -s blender/tests -t blender   # tests Python (41 avant ce plan)
cd app && npm test                                        # tests JS (51 avant ce plan)
```

Le serveur de dev : configuration `canard-3d` de `.claude/launch.json` (port 5173).

---

## Carte des fichiers

| Fichier | Statut | Rôle |
|---|---|---|
| `blender/citygen/cachettes.py` | créer | Filtre des cachettes valables, format glTF compact, empreinte |
| `blender/tests/test_cachettes.py` | créer | Tests du filtre et de l'empreinte |
| `blender/place_objets.py` | modifier | Écrit `cachettes.json`, ajoute `empreinte` à `scenes.json` |
| `assets/scenes/<ville>/cachettes.json` | généré | Une cachette par ligne |
| `app/src/sauvegarde.js` | modifier | Lecture / écriture d'une progression sous une clé quelconque |
| `app/src/defi.js` | créer | Code du lien, rejets, textes, liens |
| `app/src/cachettes.js` | créer | Chargement de `cachettes.json`, aimant |
| `app/src/mesdefis.js` | créer | « Mes défis », dernier prénom, clé de progression d'un défi reçu |
| `app/src/partage.js` | modifier | `partagerAvecRetour` (déplacé de `main.js`), `sousTitreFin` |
| `app/src/scene.js` | modifier | Canards fournis, emplacements vides, `placerCanards`, `rebondir` |
| `app/src/hud.js` | modifier | Fin de défi, HUD « Cacher », panneau prénom, « Mes défis », mode cacher de l'accueil |
| `app/src/cacher.js` | créer | Écran « Cacher » |
| `app/src/main.js` | modifier | Aiguillage partie / défi / cacher, accueil avec « Mes défis » |
| `app/index.html`, `app/src/style.css` | modifier | Éléments et styles nouveaux |
| `app/tests/*.test.js` | créer | `defi`, `cachettes`, `mesdefis`, `sauvegarde-cle` ; `partage` complété |

---

### Task 1: Cachettes valables (Python pur)

**Files:**
- Create: `blender/citygen/cachettes.py`
- Test: `blender/tests/test_cachettes.py`

- [ ] **Step 1: Écrire les tests qui échouent**

`blender/tests/test_cachettes.py` :

```python
import unittest

from citygen.cachettes import cachettes_valables, empreinte, en_gltf
from citygen.layout import charger_theme

THEME = charger_theme("paris")  # visibilite_canard [0.3, 0.8], distance_min 1.0


def slot(x, vis=0.5, rot_canard=1.0, lieu="sol"):
    return {"lieu": lieu, "pos": [x, 0.0, 0.0], "rot": 0.0, "vis": vis, "rot_canard": rot_canard}


class TestCachettes(unittest.TestCase):
    def test_garde_les_cachettes_assez_visibles_dont_la_tete_se_voit(self):
        slots = [slot(0), slot(10, vis=0.29), slot(20, rot_canard=None), slot(30, vis=1.0), slot(40, rot_canard=0.0)]
        gardees = cachettes_valables(slots, [], THEME)
        # pas de borne haute ; une rotation nulle est une vraie rotation
        self.assertEqual([s["pos"][0] for s in gardees], [0, 30, 40])

    def test_ecarte_les_cachettes_collees_a_un_leurre(self):
        leurres = [{"pos": [0.5, 0.0, 0.0]}]
        gardees = cachettes_valables([slot(0), slot(5)], leurres, THEME)
        self.assertEqual([s["pos"][0] for s in gardees], [5])

    def test_garde_l_ordre_des_slots(self):
        slots = [slot(x) for x in (9, 3, 7, 1)]
        self.assertEqual([s["pos"][0] for s in cachettes_valables(slots, [], THEME)], [9, 3, 7, 1])

    def test_convertit_en_repere_gltf(self):
        s = {"lieu": "toit", "pos": [1.0, 2.0, 3.0], "rot": 0.0, "vis": 0.4567, "rot_canard": 5.5}
        self.assertEqual(en_gltf(s), [1.0, 3.0, -2.0, 5.5, 0.457, "toit"])

    def test_empreinte_stable_et_sensible(self):
        a = [[1.0, 0.0, -2.0, 0.5, 0.4, "sol"], [3.0, 0.0, 1.0, 1.5, 0.9, "toit"]]
        self.assertRegex(empreinte(a), r"^[0-9a-z]{4}$")
        self.assertEqual(empreinte(a), empreinte([list(c) for c in a]))
        b = [list(c) for c in a]
        b[1][0] = 3.001
        self.assertNotEqual(empreinte(a), empreinte(b))
        self.assertNotEqual(empreinte(a), empreinte(a[::-1]))
```

- [ ] **Step 2: Vérifier qu'ils échouent**

Run: `python -m unittest blender.tests.test_cachettes` depuis la racine ne marche pas (imports `citygen`) ; utiliser :
`python -m unittest discover -s blender/tests -t blender -p "test_cachettes.py"`
Expected: erreur `ModuleNotFoundError: No module named 'citygen.cachettes'`.

- [ ] **Step 3: Écrire le module**

`blender/citygen/cachettes.py` :

```python
"""Cachettes valables pour le mode « Cacher mes canards ». Python pur.

Entrée : les slots mesurés par place_objets.py ({lieu, pos, rot, vis, rot_canard}, repère
Blender) et les leurres placés. Sortie : la liste compacte de cachettes.json, en repère glTF,
et son empreinte. L'ordre des slots est conservé : le numéro d'une cachette est sa position
dans la liste, et c'est ce numéro que porte le lien de défi.
"""
import json
import zlib

CHIFFRES_36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def _dist(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def cachettes_valables(slots, leurres, theme):
    """Slots où un canard de défi reste trouvable : assez visible, tête visible, loin des leurres."""
    vis_min = theme["visibilite_canard"][0]
    dmin = theme["distance_min"]
    return [s for s in slots
            if s["vis"] >= vis_min
            and s.get("rot_canard") is not None
            and all(_dist(s["pos"], l["pos"]) >= dmin for l in leurres)]


def en_gltf(slot):
    """[x, y, z, rotation, visibilité, lieu] en repère glTF (Y vers le haut), comme placements.json."""
    x, y, z = slot["pos"]
    return [round(x, 3), round(z, 3), round(-y, 3), slot["rot_canard"], round(slot["vis"], 3), slot["lieu"]]


def empreinte(liste):
    """4 caractères base 36 tirés du CRC32 de la liste : changent dès qu'une cachette change."""
    n = zlib.crc32(json.dumps(liste, separators=(",", ":")).encode("utf8")) % 36 ** 4
    out = ""
    for _ in range(4):
        n, r = divmod(n, 36)
        out = CHIFFRES_36[r] + out
    return out
```

- [ ] **Step 4: Vérifier qu'ils passent, et tous les tests Python**

Run: `python -m unittest discover -s blender/tests -t blender`
Expected: `Ran 46 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add blender/citygen/cachettes.py blender/tests/test_cachettes.py
git commit -m "feat(generateur): cachettes valables pour le mode Cacher mes canards"
```

---

### Task 2: Écrire `cachettes.json` et l'empreinte dans `scenes.json`

**Files:**
- Modify: `blender/place_objets.py`
- Generated: `assets/scenes/{paris,new_york,lille,delhi}/cachettes.json`, `assets/scenes.json`

- [ ] **Step 1: Importer le module**

Dans `blender/place_objets.py`, après la ligne `from citygen.placement import …` :

```python
from citygen.cachettes import cachettes_valables, empreinte, en_gltf  # noqa: E402
```

- [ ] **Step 2: Écrire `cachettes.json` juste après `placements.json`**

Dans `main()`, juste après le bloc `with open(os.path.join(dossier, "placements.json"), …)` et **avant** la mise à jour de `scenes.json`, insérer :

```python
    # Mode « Cacher mes canards » : toutes les cachettes où un canard reste trouvable.
    # Aucun tirage aléatoire ici : canards et leurres ne bougent pas.
    leurres = [o for o in objets if o["type"] != CANARD]
    cachettes = [en_gltf(s) for s in cachettes_valables(slots, leurres, theme)]
    emp = empreinte(cachettes)
    entete = {"ville": ville, "version": theme["version"], "empreinte": emp, "echelle": k,
              "gabarit": round(0.5 * k, 3), "distance_min_canards": theme["distance_min_canards"]}
    with open(os.path.join(dossier, "cachettes.json"), "w", encoding="utf8") as f:
        # une cachette par ligne : fichier lisible et diff git utile
        f.write(json.dumps(entete, ensure_ascii=False)[:-1] + ', "cachettes": [\n')
        f.write(",\n".join(json.dumps(c, ensure_ascii=False) for c in cachettes))
        f.write("\n]}\n")
```

- [ ] **Step 3: Ajouter l'empreinte à la ligne de la ville dans `scenes.json`**

Remplacer le `scenes.append({...})` existant par :

```python
    scenes.append({"id": ville, "nom": theme["nom"], "version": theme["version"], "ordre": theme.get("ordre", 99),
                   "embleme": theme.get("embleme", "🏙️"), "couleur": theme.get("couleur", "#3F6FD8"),
                   "canards": theme["canards"], "empreinte": emp})
```

- [ ] **Step 4: Ajouter le nombre de cachettes au rapport**

Dans le `return {...}` final de `main()`, ajouter la ligne :

```python
        "cachettes_defi": len(cachettes),
```

- [ ] **Step 5: Demander à l'utilisateur avant de lancer les quatre villes**

(Pièges `CLAUDE.md` : les générations Blender sont longues.) Ici seule l'étape de placement tourne, sur les `.blend` déjà présents.

- [ ] **Step 6: Relancer le placement des quatre villes**

```bash
B="/c/Program Files/Blender Foundation/Blender 5.3/blender.exe"
for v in paris new_york lille delhi; do
  echo "=== $v"
  PYTHONIOENCODING=utf8 "$B" --background "blender/scenes/$v.blend" --python blender/place_objets.py -- --ville "$v" 2>&1 | grep -E "Traceback|Error|RESULTAT"
done
```

Expected : une ligne `RESULTAT` par ville, avec `"cachettes_defi"` entre environ 1 000 et 3 500, aucun `Traceback`.

- [ ] **Step 7: Vérifier que rien d'autre n'a bougé**

```bash
git status --short assets/
git diff --stat assets/scenes/*/placements.json
python -c "import json;[print(s['id'],s['version'],s['empreinte']) for s in json.load(open('assets/scenes.json',encoding='utf8'))]"
```

Expected : `assets/scenes.json` modifié, quatre `cachettes.json` nouveaux, **aucune** différence dans les `placements.json` (sinon : les `.blend` ne correspondent plus aux placements publiés ; s'arrêter et prévenir l'utilisateur). Chaque ville a une empreinte de 4 caractères.

- [ ] **Step 8: Commit**

```bash
git add blender/place_objets.py assets/scenes.json assets/scenes/*/cachettes.json
git commit -m "feat(generateur): cachettes.json par ville et empreinte dans scenes.json"
git push
```

---

### Task 3: Progression sous une clé quelconque (`sauvegarde.js`)

**Files:**
- Modify: `app/src/sauvegarde.js`
- Test: `app/tests/sauvegarde-cle.test.js`

- [ ] **Step 1: Écrire le test qui échoue**

`app/tests/sauvegarde-cle.test.js` :

```js
import { describe, expect, it } from 'vitest';
import { charger, chargerCle, cle, effacerCle, enregistrerCle } from '../src/sauvegarde.js';

function fauxStockage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}

describe('progression sous une clé quelconque', () => {
  it('enregistre, relit et efface', () => {
    const s = fauxStockage();
    enregistrerCle(s, 'cle-test', { trouves: ['a'], taps: 3, ecouleMs: 1200 });
    expect(chargerCle(s, 'cle-test')).toEqual({ trouves: ['a'], taps: 3, ecouleMs: 1200 });
    effacerCle(s, 'cle-test');
    expect(chargerCle(s, 'cle-test')).toBeNull();
  });

  it('reste compatible avec la sauvegarde par ville', () => {
    const s = fauxStockage();
    enregistrerCle(s, cle('lille', 3), { trouves: [], taps: 1, ecouleMs: 0 });
    expect(charger(s, 'lille', 3)).toEqual({ trouves: [], taps: 1, ecouleMs: 0 });
  });
});
```

- [ ] **Step 2: Vérifier qu'il échoue**

Run: `cd app && npx vitest run tests/sauvegarde-cle.test.js`
Expected: FAIL, `chargerCle is not a function` (ou export manquant).

- [ ] **Step 3: Remplacer `charger`, `enregistrer`, `effacer` dans `app/src/sauvegarde.js`**

Remplacer les trois fonctions (de `export function charger(` jusqu'à la fin de `effacer`) par :

```js
/** Progression {trouves, taps, ecouleMs} rangée sous la clé `k`, ou null. */
export function chargerCle(stockage, k) {
  try {
    const d = JSON.parse(stockage.getItem(k));
    if (!d || !Array.isArray(d.trouves) || typeof d.taps !== 'number') return null;
    return { trouves: d.trouves, taps: d.taps, ecouleMs: Number(d.ecouleMs) || 0 };
  } catch {
    return null;
  }
}

export function enregistrerCle(stockage, k, donnees) {
  try {
    stockage.setItem(k, JSON.stringify(donnees));
  } catch {
    // stockage plein ou bloqué (navigation privée) : la partie continue sans sauvegarde
  }
}

export function effacerCle(stockage, k) {
  try {
    stockage.removeItem(k);
  } catch {
    // idem
  }
}

export const charger = (stockage, ville, version) => chargerCle(stockage, cle(ville, version));
export const enregistrer = (stockage, ville, version, donnees) => enregistrerCle(stockage, cle(ville, version), donnees);
export const effacer = (stockage, ville, version) => effacerCle(stockage, cle(ville, version));
```

- [ ] **Step 4: Vérifier que tout passe**

Run: `cd app && npm test`
Expected: tous les tests passent (les anciens tests de sauvegarde compris).

- [ ] **Step 5: Commit**

```bash
git add app/src/sauvegarde.js app/tests/sauvegarde-cle.test.js
git commit -m "refactor(app): sauvegarde d'une progression sous une cle quelconque"
```

---

### Task 4: Le code du lien de défi et ses textes (`defi.js`)

**Files:**
- Create: `app/src/defi.js`
- Test: `app/tests/defi.test.js`

- [ ] **Step 1: Écrire les tests qui échouent**

`app/tests/defi.test.js` :

```js
import { describe, expect, it } from 'vitest';
import {
  deQui, decoderDefi, encoderDefi, libelleRenvoi, lienCacher, lienDefi, messageRejet, texteInvitationDefi,
  texteTempsDefi, titreDefi, titreFinDefi, verifierDefi,
} from '../src/defi.js';

const DEFI = { version: 3, empreinte: 'k7f2', numeros: [0, 17, 3499], prenom: 'Camille' };

describe('code de défi', () => {
  it('fait l’aller-retour, en caractères sûrs pour une adresse', () => {
    const code = encoderDefi(DEFI);
    expect(code).toMatch(/^[A-Za-z0-9_-]+$/);
    expect(decoderDefi(code)).toEqual({ ok: true, defi: DEFI });
  });

  it('accepte 1 et 30 canards, avec ou sans prénom, en moins de 100 caractères', () => {
    const un = { ...DEFI, numeros: [42], prenom: '' };
    expect(decoderDefi(encoderDefi(un))).toEqual({ ok: true, defi: un });
    const trente = { ...DEFI, numeros: Array.from({ length: 30 }, (_, i) => i * 100) };
    const code = encoderDefi(trente);
    expect(decoderDefi(code)).toEqual({ ok: true, defi: trente });
    expect(code.length).toBeLessThan(100);
  });

  it('garde accents et émoji, et coupe le prénom à 20 caractères', () => {
    expect(decoderDefi(encoderDefi({ ...DEFI, prenom: 'Zoé 🦆' })).defi.prenom).toBe('Zoé 🦆');
    const long = encoderDefi({ ...DEFI, prenom: '  Maximilien-Alexandre de la Tour ' });
    expect(decoderDefi(long).defi.prenom).toBe('Maximilien-Alexandre');
  });

  it('rejette un code abîmé', () => {
    const code = encoderDefi(DEFI);
    for (const abime of ['', null, undefined, 'pas un code !', code.slice(0, 10),
      encoderDefi({ ...DEFI, numeros: [5, 5] }), encoderDefi({ ...DEFI, numeros: [] })]) {
      expect(decoderDefi(abime)).toEqual({ ok: false, raison: 'abime' });
    }
  });

  it('rejette un format inconnu', () => {
    const code = encoderDefi(DEFI);
    expect(code.slice(0, 2)).toBe('AQ'); // premier octet = 1 (format)
    // « Ag » : premier octet = 2, le reste inchangé
    expect(decoderDefi(`Ag${code.slice(2)}`)).toEqual({ ok: false, raison: 'format' });
  });

  it('vérifie le défi contre les cachettes chargées', () => {
    const ville = { version: 3, empreinte: 'k7f2', nombre: 3500 };
    expect(verifierDefi(DEFI, ville)).toBeNull();
    expect(verifierDefi(DEFI, { ...ville, version: 4 })).toBe('version');
    expect(verifierDefi(DEFI, { ...ville, empreinte: 'zzzz' })).toBe('empreinte');
    expect(verifierDefi(DEFI, { ...ville, nombre: 3499 })).toBe('abime');
  });
});

describe('textes des défis', () => {
  it('accorde « de » devant le prénom', () => {
    expect(deQui('Camille')).toBe('de Camille');
    expect(deQui('Amélie')).toBe('d’Amélie');
    expect(deQui('Élodie')).toBe('d’Élodie');
    expect(deQui('')).toBe('d’un ami');
    expect(titreDefi('Camille')).toBe('Le défi de Camille');
    expect(titreFinDefi('Amélie')).toBe('Défi d’Amélie réussi !');
    expect(titreFinDefi('')).toBe('Défi réussi !');
    expect(libelleRenvoi('Camille')).toBe('Envoyer mon temps à Camille');
    expect(libelleRenvoi('')).toBe('Envoyer mon temps');
  });

  it('écrit l’invitation et le temps renvoyé', () => {
    expect(texteInvitationDefi({ prenom: 'Camille', n: 7, ville: 'Lille' }))
      .toBe('🦆 Camille a caché 7 canards dans Lille. À toi de les trouver !');
    expect(texteInvitationDefi({ prenom: '', n: 1, ville: 'Lille' }))
      .toBe('🦆 Un ami a caché 1 canard dans Lille. À toi de le trouver !');
    expect(texteTempsDefi({ prenom: 'Camille', n: 7, ville: 'Lille', ecouleMs: 151000 }))
      .toBe("🦆 Camille, j'ai trouvé tes 7 canards dans Lille en 2:31 !");
    expect(texteTempsDefi({ prenom: '', n: 1, ville: 'Lille', ecouleMs: 5000 }))
      .toBe("🦆 J'ai trouvé ton canard dans Lille en 0:05 !");
  });

  it('explique chaque rejet', () => {
    expect(messageRejet('version', { ville: 'Lille', prenom: 'Camille' }))
      .toBe('Ce défi a été créé pour une ancienne version de Lille : demande à Camille d’en refaire un.');
    expect(messageRejet('empreinte', { ville: 'Lille' })).toContain('demande à ton ami');
    expect(messageRejet('format', { ville: 'Lille' })).toContain('recharge la page');
    expect(messageRejet('abime', { ville: 'Lille' })).toBe('Ce lien de défi est abîmé.');
    expect(messageRejet('pas-pret', { ville: 'Lille' })).toBe('Le mode défi n’est pas encore prêt pour Lille.');
  });

  it('construit les liens', () => {
    const page = 'https://exemple.io/jeu-canard-3d/?ville=paris&x=1#y';
    expect(lienDefi(page, 'lille', 'AQMk')).toBe('https://exemple.io/jeu-canard-3d/?ville=lille&defi=AQMk');
    expect(lienCacher(page, 'lille')).toBe('https://exemple.io/jeu-canard-3d/?ville=lille&cacher=');
    expect(lienCacher(page, 'lille', 'd1')).toBe('https://exemple.io/jeu-canard-3d/?ville=lille&cacher=d1');
  });
});
```

- [ ] **Step 2: Vérifier qu'ils échouent**

Run: `cd app && npx vitest run tests/defi.test.js`
Expected: FAIL, `Failed to load url ../src/defi.js` (ou équivalent).

- [ ] **Step 3: Écrire le module**

`app/src/defi.js` :

```js
// Défis « Cacher mes canards » : le code du lien, ses rejets, les textes et les liens.
// Fonctions pures.
//
// Le code est en base64url, sur des octets :
//   format (1) | version de la ville (1) | empreinte des cachettes (3) | nombre n (1)
//   | numéros des cachettes (2 × n) | prénom en UTF-8 (le reste)
import { chrono } from './hud.js';

export const FORMAT = 1;
export const MAX_CANARDS = 30;
export const MAX_PRENOM = 20;
const ENTETE = 6;

function versBase64url(octets) {
  let binaire = '';
  for (const o of octets) binaire += String.fromCharCode(o);
  return btoa(binaire).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function depuisBase64url(texte) {
  if (typeof texte !== 'string' || !/^[A-Za-z0-9_-]+$/.test(texte)) return null;
  const b64 = texte.replace(/-/g, '+').replace(/_/g, '/');
  try {
    return Uint8Array.from(atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4)), (c) => c.charCodeAt(0));
  } catch {
    return null;
  }
}

/** Prénom sans espaces autour, 20 caractères au plus (un émoji compte pour un). */
export const nettoyerPrenom = (prenom) => [...String(prenom ?? '').trim()].slice(0, MAX_PRENOM).join('');

/** @param defi {version, empreinte (4 caractères base 36), numeros, prenom} */
export function encoderDefi({ version, empreinte, numeros, prenom = '' }) {
  const e = parseInt(empreinte, 36);
  const octets = [FORMAT, version & 255, (e >> 16) & 255, (e >> 8) & 255, e & 255, numeros.length];
  for (const n of numeros) octets.push((n >> 8) & 255, n & 255);
  octets.push(...new TextEncoder().encode(nettoyerPrenom(prenom)));
  return versBase64url(octets);
}

/** @returns {{ok: true, defi}} ou {{ok: false, raison: 'abime'|'format'}} */
export function decoderDefi(code) {
  const o = depuisBase64url(code);
  if (!o || !o.length) return { ok: false, raison: 'abime' };
  if (o[0] !== FORMAT) return { ok: false, raison: 'format' };
  const n = o[5];
  if (o.length < ENTETE || n < 1 || n > MAX_CANARDS || o.length < ENTETE + 2 * n) return { ok: false, raison: 'abime' };
  const numeros = [];
  for (let i = 0; i < n; i += 1) numeros.push((o[ENTETE + 2 * i] << 8) | o[ENTETE + 2 * i + 1]);
  if (new Set(numeros).size !== n) return { ok: false, raison: 'abime' };
  let prenom;
  try {
    prenom = new TextDecoder('utf-8', { fatal: true }).decode(o.slice(ENTETE + 2 * n));
  } catch {
    return { ok: false, raison: 'abime' };
  }
  const empreinte = ((o[2] << 16) | (o[3] << 8) | o[4]).toString(36).padStart(4, '0');
  return { ok: true, defi: { version: o[1], empreinte, numeros, prenom: nettoyerPrenom(prenom) } };
}

/**
 * Le défi correspond-il aux cachettes chargées ?
 * @param ville {version, empreinte, nombre} (nombre = cachettes dans cachettes.json)
 * @returns null, ou la raison du rejet : 'version' | 'empreinte' | 'abime'
 */
export function verifierDefi(defi, { version, empreinte, nombre }) {
  if (defi.version !== (version & 255)) return 'version';
  if (defi.empreinte !== empreinte) return 'empreinte';
  if (defi.numeros.some((n) => n >= nombre)) return 'abime';
  return null;
}

// ----------------------------------------------------------------------- textes

const VOYELLE = /^[aeiouyàâäéèêëîïôöùûü]/i;

/** « de Camille », « d’Amélie », ou « d’un ami » sans prénom. */
export const deQui = (prenom) => (prenom ? `${VOYELLE.test(prenom) ? 'd’' : 'de '}${prenom}` : 'd’un ami');

const canards = (n) => `${n} canard${n > 1 ? 's' : ''}`;

export const titreDefi = (prenom) => `Le défi ${deQui(prenom)}`;
export const titreFinDefi = (prenom) => (prenom ? `Défi ${deQui(prenom)} réussi !` : 'Défi réussi !');
export const libelleRenvoi = (prenom) => (prenom ? `Envoyer mon temps à ${prenom}` : 'Envoyer mon temps');

export const texteInvitationDefi = ({ prenom, n, ville }) =>
  `🦆 ${prenom || 'Un ami'} a caché ${canards(n)} dans ${ville}. À toi de ${n > 1 ? 'les' : 'le'} trouver !`;

export function texteTempsDefi({ prenom, n, ville, ecouleMs }) {
  const quoi = n > 1 ? `tes ${n} canards` : 'ton canard';
  return `🦆 ${prenom ? `${prenom}, j'ai` : "J'ai"} trouvé ${quoi} dans ${ville} en ${chrono(ecouleMs)} !`;
}

/** Message affiché quand un défi (ou le mode « Cacher ») est impossible. */
export function messageRejet(raison, { ville, prenom = '' }) {
  if (raison === 'format') return 'Ce défi vient d’une version plus récente du jeu : recharge la page.';
  if (raison === 'version' || raison === 'empreinte') {
    return `Ce défi a été créé pour une ancienne version de ${ville} : demande à ${prenom || 'ton ami'} d’en refaire un.`;
  }
  if (raison === 'pas-pret') return `Le mode défi n’est pas encore prêt pour ${ville}.`;
  return 'Ce lien de défi est abîmé.';
}

// ------------------------------------------------------------------------ liens

function lienVille(adresse, ville, parametre, valeur) {
  const url = new URL(adresse);
  url.search = '';
  url.hash = '';
  url.searchParams.set('ville', ville);
  url.searchParams.set(parametre, valeur);
  return url.toString();
}

export const lienDefi = (adresse, ville, code) => lienVille(adresse, ville, 'defi', code);

/** Écran « Cacher » : `id` vide pour un nouveau défi, sinon celui de « Mes défis » à modifier. */
export const lienCacher = (adresse, ville, id = '') => lienVille(adresse, ville, 'cacher', id);
```

- [ ] **Step 4: Vérifier qu'ils passent**

Run: `cd app && npx vitest run tests/defi.test.js`
Expected: PASS (10 tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/defi.js app/tests/defi.test.js
git commit -m "feat(app): code du lien de defi, rejets et textes"
```

---

### Task 5: Cachettes et aimant (`cachettes.js`)

**Files:**
- Create: `app/src/cachettes.js`
- Test: `app/tests/cachettes.test.js`

- [ ] **Step 1: Écrire les tests qui échouent**

`app/tests/cachettes.test.js` :

```js
import { describe, expect, it } from 'vitest';
import { aimanter, canardsDuDefi, chargerCachettes, idCachette } from '../src/cachettes.js';

const FICHIER = {
  ville: 'lille', version: 3, empreinte: 'k7f2', echelle: 0.7, gabarit: 0.35, distance_min_canards: 6,
  cachettes: [[1, 0, 2, 0.5, 0.4, 'sol'], [10, 3, 0, 1, 0.9, 'toit']],
};
const repondre = (reponse) => async () => reponse;

describe('chargement des cachettes', () => {
  it('lit le fichier et calcule le centre de chaque canard', async () => {
    const lot = await chargerCachettes('lille', repondre({ ok: true, json: async () => FICHIER }));
    expect(lot.version).toBe(3);
    expect(lot.empreinte).toBe('k7f2');
    expect(lot.distanceMin).toBe(6);
    expect(lot.cachettes[1]).toEqual({
      numero: 1, position: [10, 3, 0], rotation: 1, visibilite: 0.9, lieu: 'toit', centre: [10, 3 + 0.22 * 0.7, 0],
    });
  });

  it('dit « pas prêt » si le fichier manque', async () => {
    const html = { ok: true, json: async () => { throw new SyntaxError('index.html'); } };
    await expect(chargerCachettes('lille', repondre(html))).rejects.toThrow('pas-pret');
    await expect(chargerCachettes('lille', repondre({ ok: false }))).rejects.toThrow('pas-pret');
    await expect(chargerCachettes('lille', async () => { throw new TypeError('réseau'); })).rejects.toThrow('pas-pret');
  });

  it('prépare les canards d’un défi pour la scène', async () => {
    const lot = await chargerCachettes('lille', repondre({ ok: true, json: async () => FICHIER }));
    expect(canardsDuDefi(lot.cachettes, [1])).toEqual([
      { id: idCachette(1), position: [10, 3, 0], rotation: 1, lieu: 'toit' },
    ]);
    expect(idCachette(1)).toBe('cachette-1');
  });
});

describe('aimant', () => {
  // centres à x = 0, 3, 20 et 10 m ; à l'écran à x = 100, 130, 300 et 140 px
  const cachettes = [0, 3, 20, 10].map((x, numero) => ({ numero, centre: [x, 0, 0] }));
  const ecran = [100, 130, 300, 140].map((x, numero) => ({ numero, x, y: 100 }));
  const options = { revele: true, distanceMin: 6 };

  it('demande de zoomer sous le seuil de révélation', () => {
    expect(aimanter({ x: 130, y: 100 }, ecran, cachettes, [], { ...options, revele: false })).toEqual({ raison: 'zoom' });
  });

  it('choisit la cachette la plus proche du doigt', () => {
    expect(aimanter({ x: 125, y: 100 }, ecran, cachettes, [], options)).toEqual({ numero: 1 });
  });

  it('ne trouve rien loin de toute cachette', () => {
    expect(aimanter({ x: 200, y: 300 }, ecran, cachettes, [], options)).toEqual({ raison: 'aucune' });
  });

  it('ignore une cachette déjà prise', () => {
    expect(aimanter({ x: 300, y: 100 }, ecran, cachettes, [2], options)).toEqual({ raison: 'aucune' });
  });

  it('prend la suivante si la plus proche est trop près d’un canard posé', () => {
    // la 1 est à 3 m du canard posé sur la 0 ; la 3 est à 10 m
    expect(aimanter({ x: 131, y: 100 }, ecran, cachettes, [0], options)).toEqual({ numero: 3 });
  });

  it('refuse si toutes les cachettes proches sont trop près', () => {
    expect(aimanter({ x: 101, y: 100 }, ecran, cachettes, [1], { ...options, rayonPx: 20 })).toEqual({ raison: 'trop-pres' });
  });

  it('refuse au-delà de 30 canards', () => {
    const trente = Array.from({ length: 30 }, (_, i) => i + 100);
    expect(aimanter({ x: 125, y: 100 }, ecran, cachettes, trente, options)).toEqual({ raison: 'plein' });
  });
});
```

- [ ] **Step 2: Vérifier qu'ils échouent**

Run: `cd app && npx vitest run tests/cachettes.test.js`
Expected: FAIL (module absent).

- [ ] **Step 3: Écrire le module**

`app/src/cachettes.js` :

```js
// Cachettes du mode défi (cachettes.json) et l'aimant qui pose un canard. Géométrie pure,
// sauf `chargerCachettes` qui reçoit `fetch` en paramètre (testable avec un faux).
import { MAX_CANARDS } from './defi.js';

export const RAYON_AIMANT_PX = 40;
const HAUTEUR_CENTRE = 0.22; // comme scene.js : centre du canard au-dessus de son appui, à l'échelle 1

export const idCachette = (numero) => `cachette-${numero}`;

/**
 * Lit scenes/<ville>/cachettes.json. Lève Error('pas-pret') s'il manque : Vite renvoie
 * alors index.html, illisible en JSON.
 */
export async function chargerCachettes(ville, lire = globalThis.fetch) {
  let d = null;
  try {
    const r = await lire(`scenes/${ville}/cachettes.json`);
    if (r.ok) d = await r.json();
  } catch {
    d = null;
  }
  if (!d || !Array.isArray(d.cachettes)) throw new Error('pas-pret');
  const k = d.echelle ?? 1;
  return {
    version: d.version,
    empreinte: d.empreinte,
    distanceMin: d.distance_min_canards,
    cachettes: d.cachettes.map(([x, y, z, rotation, visibilite, lieu], numero) => ({
      numero, position: [x, y, z], rotation, visibilite, lieu, centre: [x, y + HAUTEUR_CENTRE * k, z],
    })),
  };
}

/** Les canards d'un défi, au format attendu par la scène : un par numéro de cachette. */
export const canardsDuDefi = (cachettes, numeros) => numeros.map((n) => ({
  id: idCachette(n), position: cachettes[n].position, rotation: cachettes[n].rotation, lieu: cachettes[n].lieu,
}));

const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

/**
 * Où poser un canard pour ce tap ?
 * @param tap {x, y} en px
 * @param ecran [{numero, x, y}] cachettes projetées à l'écran
 * @param cachettes liste complète (centres en mètres), indexée par numéro
 * @param posees numéros des cachettes déjà occupées
 * @returns {{numero}} ou {{raison: 'zoom'|'plein'|'aucune'|'trop-pres'}}
 */
export function aimanter(tap, ecran, cachettes, posees, { revele, distanceMin, rayonPx = RAYON_AIMANT_PX }) {
  if (!revele) return { raison: 'zoom' };
  if (posees.length >= MAX_CANARDS) return { raison: 'plein' };
  const prises = new Set(posees);
  const proches = ecran
    .map((c) => ({ numero: c.numero, d: Math.hypot(c.x - tap.x, c.y - tap.y) }))
    .filter((c) => c.d <= rayonPx && !prises.has(c.numero))
    .sort((a, b) => a.d - b.d);
  if (!proches.length) return { raison: 'aucune' };
  const libre = proches.find((c) => posees.every(
    (p) => distance(cachettes[c.numero].centre, cachettes[p].centre) >= distanceMin,
  ));
  return libre ? { numero: libre.numero } : { raison: 'trop-pres' };
}
```

- [ ] **Step 4: Vérifier qu'ils passent**

Run: `cd app && npx vitest run tests/cachettes.test.js`
Expected: PASS (10 tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/cachettes.js app/tests/cachettes.test.js
git commit -m "feat(app): chargement des cachettes et aimant"
```

---

### Task 6: « Mes défis » (`mesdefis.js`)

**Files:**
- Create: `app/src/mesdefis.js`
- Test: `app/tests/mesdefis.test.js`

- [ ] **Step 1: Écrire les tests qui échouent**

`app/tests/mesdefis.test.js` :

```js
import { describe, expect, it } from 'vitest';
import {
  CLE_DEFIS, cleDefiRecu, dernierPrenom, detailDefi, enregistrerDefi, estValable, listerDefis, nouvelId,
  retenirPrenom, supprimerDefi, trouverDefi,
} from '../src/mesdefis.js';

function fauxStockage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}
const bloque = () => { throw new Error('stockage bloqué'); };
const STOCKAGE_BLOQUE = { getItem: bloque, setItem: bloque, removeItem: bloque };

const defi = (id, numeros = [1, 2]) => ({
  id, ville: 'lille', version: 3, empreinte: 'k7f2', prenom: 'Camille', numeros, cree: Date.UTC(2026, 10, 21, 12),
});

describe('mes défis', () => {
  it('garde un brouillon, le met à jour à sa place et le retrouve', () => {
    const s = fauxStockage();
    enregistrerDefi(s, defi('a'));
    enregistrerDefi(s, defi('b'));
    enregistrerDefi(s, defi('a', [1, 2, 3]));
    expect(listerDefis(s).map((d) => d.id)).toEqual(['b', 'a']);
    expect(trouverDefi(s, 'a').numeros).toEqual([1, 2, 3]);
    expect(trouverDefi(s, 'zzz')).toBeNull();
  });

  it('retire un défi sans canard, ou supprimé', () => {
    const s = fauxStockage();
    enregistrerDefi(s, defi('a'));
    enregistrerDefi(s, defi('b'));
    enregistrerDefi(s, defi('a', []));
    expect(listerDefis(s).map((d) => d.id)).toEqual(['b']);
    supprimerDefi(s, 'b');
    expect(listerDefis(s)).toEqual([]);
  });

  it('ignore une liste illisible et les entrées invalides', () => {
    const s = fauxStockage();
    s.setItem(CLE_DEFIS, '{pas du json');
    expect(listerDefis(s)).toEqual([]);
    s.setItem(CLE_DEFIS, JSON.stringify([defi('a'), { id: 'b' }, null]));
    expect(listerDefis(s).map((d) => d.id)).toEqual(['a']);
  });

  it('survit à un stockage bloqué', () => {
    expect(listerDefis(STOCKAGE_BLOQUE)).toEqual([]);
    expect(() => enregistrerDefi(STOCKAGE_BLOQUE, defi('a'))).not.toThrow();
    expect(() => supprimerDefi(STOCKAGE_BLOQUE, 'a')).not.toThrow();
    expect(dernierPrenom(STOCKAGE_BLOQUE)).toBe('');
    expect(() => retenirPrenom(STOCKAGE_BLOQUE, 'Zoé')).not.toThrow();
  });

  it('retient le dernier prénom', () => {
    const s = fauxStockage();
    expect(dernierPrenom(s)).toBe('');
    retenirPrenom(s, 'Zoé');
    expect(dernierPrenom(s)).toBe('Zoé');
  });

  it('dit si un défi vaut encore pour sa ville', () => {
    const scenes = [{ id: 'lille', version: 3, empreinte: 'k7f2' }, { id: 'paris', version: 3, empreinte: 'aaaa' }];
    expect(estValable(defi('a'), scenes)).toBe(true);
    expect(estValable({ ...defi('a'), version: 2 }, scenes)).toBe(false);
    expect(estValable({ ...defi('a'), empreinte: 'zzzz' }, scenes)).toBe(false);
    expect(estValable({ ...defi('a'), ville: 'rome' }, scenes)).toBe(false);
  });

  it('résume un défi, fabrique ses clés et identifiants', () => {
    expect(detailDefi(defi('a', [4]))).toBe('1 canard · 21/11');
    expect(detailDefi(defi('a', [1, 2, 3]))).toBe('3 canards · 21/11');
    expect(nouvelId(1000, () => 0.5)).toBe(`${(1000).toString(36)}i0`);
    expect(cleDefiRecu('AQMk')).toBe('jeu-canard-3d:defi:AQMk');
  });
});
```

- [ ] **Step 2: Vérifier qu'ils échouent**

Run: `cd app && npx vitest run tests/mesdefis.test.js`
Expected: FAIL (module absent).

- [ ] **Step 3: Écrire le module**

`app/src/mesdefis.js` :

```js
// « Mes défis » : les défis créés sur cet appareil, et le dernier prénom utilisé.
// Le stockage (de type localStorage) est passé en paramètre ; bloqué, il ne casse rien.
//
// Un défi : {id, ville, version, empreinte, prenom, numeros, cree (ms)}.

export const CLE_DEFIS = 'jeu-canard-3d:mes-defis';
export const CLE_PRENOM = 'jeu-canard-3d:prenom';

/** Progression d'un défi reçu, rangée à part de la partie normale. */
export const cleDefiRecu = (code) => `jeu-canard-3d:defi:${code}`;

const estDefi = (d) => Boolean(d) && typeof d.id === 'string' && typeof d.ville === 'string'
  && Number.isInteger(d.version) && typeof d.empreinte === 'string'
  && Array.isArray(d.numeros) && d.numeros.every(Number.isInteger) && typeof d.cree === 'number';

export function listerDefis(stockage) {
  try {
    const liste = JSON.parse(stockage.getItem(CLE_DEFIS));
    if (!Array.isArray(liste)) return [];
    return liste.filter(estDefi).map((d) => ({ ...d, prenom: typeof d.prenom === 'string' ? d.prenom : '' }));
  } catch {
    return [];
  }
}

function ecrire(stockage, liste) {
  try {
    stockage.setItem(CLE_DEFIS, JSON.stringify(liste));
  } catch {
    // stockage plein ou bloqué : le défi marche quand même, il n'est simplement pas gardé
  }
}

export const trouverDefi = (stockage, id) => listerDefis(stockage).find((d) => d.id === id) ?? null;

/** Ajoute un défi en tête, ou le remplace à sa place ; sans canard, il est retiré. */
export function enregistrerDefi(stockage, defi) {
  const liste = listerDefis(stockage);
  const i = liste.findIndex((d) => d.id === defi.id);
  if (!defi.numeros.length) {
    if (i >= 0) liste.splice(i, 1);
  } else if (i >= 0) {
    liste[i] = defi;
  } else {
    liste.unshift(defi);
  }
  ecrire(stockage, liste);
  return liste;
}

export function supprimerDefi(stockage, id) {
  ecrire(stockage, listerDefis(stockage).filter((d) => d.id !== id));
}

export const nouvelId = (maintenant = Date.now(), alea = Math.random) =>
  `${maintenant.toString(36)}${Math.floor(alea() * 1296).toString(36).padStart(2, '0')}`;

export function dernierPrenom(stockage) {
  try {
    return stockage.getItem(CLE_PRENOM) ?? '';
  } catch {
    return '';
  }
}

export function retenirPrenom(stockage, prenom) {
  try {
    stockage.setItem(CLE_PRENOM, prenom);
  } catch {
    // idem
  }
}

/** Le défi correspond-il encore à sa ville (même version, mêmes cachettes) ? */
export const estValable = (defi, scenes) => scenes.some(
  (s) => s.id === defi.ville && s.version === defi.version && s.empreinte === defi.empreinte,
);

/** « 7 canards · 21/11 » */
export function detailDefi(defi) {
  const n = defi.numeros.length;
  const date = new Date(defi.cree);
  const jj = String(date.getDate()).padStart(2, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  return `${n} canard${n > 1 ? 's' : ''} · ${jj}/${mm}`;
}
```

- [ ] **Step 4: Vérifier qu'ils passent**

Run: `cd app && npx vitest run tests/mesdefis.test.js`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/mesdefis.js app/tests/mesdefis.test.js
git commit -m "feat(app): liste Mes defis et dernier prenom"
git push
```

---

### Task 7: `partagerAvecRetour` et `sousTitreFin` dans `partage.js`

**Files:**
- Modify: `app/src/partage.js`, `app/src/main.js`
- Test: `app/tests/partage.test.js`

- [ ] **Step 1: Écrire le test qui échoue**

Dans `app/tests/partage.test.js`, ajouter `sousTitreFin` à l'import depuis `../src/partage.js`, puis ce test dans le `describe('partage', …)` :

```js
  it('écrit le sous-titre de fin selon le nombre de canards', () => {
    expect(sousTitreFin(30)).toBe('Les 30 canards sont trouvés');
    expect(sousTitreFin(1)).toBe('Le canard est trouvé');
  });
```

- [ ] **Step 2: Vérifier qu'il échoue**

Run: `cd app && npx vitest run tests/partage.test.js`
Expected: FAIL, `sousTitreFin is not a function`.

- [ ] **Step 3: Compléter `partage.js`**

Remplacer `import { chrono } from './hud.js';` par :

```js
import { afficherBref, chrono } from './hud.js';
```

Puis ajouter à la fin du fichier :

```js
export const TITRE = 'Où sont les canards ?';

/** Partage, avec un retour visible quand le lien a été copié plutôt que partagé. */
export async function partagerAvecRetour(contenu) {
  const issue = await partager({ titre: TITRE, ...contenu });
  if (issue === 'copie') afficherBref('Message et lien copiés : colle-les dans un SMS ou une messagerie.');
  if (issue === 'impossible') afficherBref(`Copie impossible ici. Le lien : ${contenu.url}`, 6000);
}

/** Sous-titre de l'écran de fin. */
export const sousTitreFin = (n) => (n > 1 ? `Les ${n} canards sont trouvés` : 'Le canard est trouvé');
```

- [ ] **Step 4: Retirer la copie de `main.js`**

Dans `app/src/main.js` : supprimer `const TITRE = 'Où sont les canards ?';` et la fonction `partagerAvecRetour` (avec son commentaire), et remplacer `partager,` par `partagerAvecRetour,` dans l'import depuis `./partage.js`.

- [ ] **Step 5: Vérifier**

Run: `cd app && npm test && npm run build`
Expected: tous les tests passent ; build sans erreur.

- [ ] **Step 6: Commit**

```bash
git add app/src/partage.js app/src/main.js app/tests/partage.test.js
git commit -m "refactor(app): partagerAvecRetour dans partage.js, sous-titre de fin"
```

---

### Task 8: Scène — canards fournis, emplacements vides, rebond

**Files:**
- Modify: `app/src/scene.js`

Pas de test unitaire (Three.js et DOM) : vérification dans le navigateur à l'étape 5.

- [ ] **Step 1: Accepter des options**

Remplacer la ligne `export async function chargerScene(canvas, info) {` par :

```js
/**
 * @param options.canards canards à afficher à la place de ceux de placements.json
 *        ([{id, position, rotation, lieu}], comme les objets de placements.json)
 * @param options.capacite emplacements de canards à prévoir (mode « Cacher » : 30)
 */
export async function chargerScene(canvas, info, { canards: fournis = null, capacite = 0 } = {}) {
```

- [ ] **Step 2: Remplacer l'instanciation des canards**

Remplacer :

```js
  const enInstance = (o) => ({ p: o.position, r: o.rotation, s: k });
  const canards = placements.objets.filter((o) => o.type === TYPE_CANARD);
  const pres = instancier(props.scene, TYPE_CANARD, canards.map(enInstance));
  const loin = instancier(props.scene, TYPE_CANARD_LOIN, canards.map(enInstance));
```

par :

```js
  const enInstance = (o) => ({ p: o.position, r: o.rotation, s: k });
  const VIDE = { p: [0, -1000, 0], r: 0, s: 0 }; // emplacement libre : hors de vue, taille nulle
  let canards = fournis ?? placements.objets.filter((o) => o.type === TYPE_CANARD);
  const places = Math.max(capacite, canards.length);
  const emplacements = Array.from({ length: places }, (_, i) => (canards[i] ? enInstance(canards[i]) : VIDE));
  const pres = instancier(props.scene, TYPE_CANARD, emplacements);
  const loin = instancier(props.scene, TYPE_CANARD_LOIN, emplacements);
  // les canards bougent en mode « Cacher » : leur sphère englobante calculée au départ serait fausse
  for (const m of [pres, loin]) {
    m.frustumCulled = false;
    for (const c of m.children) c.frustumCulled = false;
  }
```

- [ ] **Step 3: Séparer le rebond, ajouter `placerCanards`**

Remplacer toute la fonction `marquerTrouve` (commentaire compris) par :

```js
  /** Courte animation d'un canard (trouvé, ou posé en mode « Cacher »). */
  function rebondir(index) {
    const debut = performance.now();
    const pas = (t) => {
      if (!canards[index]) return; // retiré entre-temps
      const a = Math.min(1, (t - debut) / 380);
      const mat = matrice(enInstance(canards[index]), 1 + 0.7 * Math.sin(Math.PI * a));
      for (const m of [pres, loin]) {
        m.setMatrixAt(index, mat);
        m.instanceMatrix.needsUpdate = true;
      }
      demanderRendu();
      if (a < 1) requestAnimationFrame(pas);
    };
    requestAnimationFrame(pas);
  }

  /** Passe un canard en vert ; `rebond` joue une courte animation. */
  function marquerTrouve(id, rebond = false) {
    const index = canards.findIndex((c) => c.id === id);
    if (index < 0) return;
    for (const m of [pres, loin]) m.userData.teindre(index, 'jaune', VERT_TROUVE);
    if (rebond) rebondir(index);
    else demanderRendu();
  }

  /** Mode « Cacher » : remplace les canards affichés ; les emplacements en trop sont vidés. */
  function placerCanards(liste) {
    if (liste.length > places) throw new Error(`${liste.length} canards pour ${places} emplacements`);
    canards = liste;
    for (let i = 0; i < places; i += 1) {
      const mat = matrice(canards[i] ? enInstance(canards[i]) : VIDE);
      for (const m of [pres, loin]) m.setMatrixAt(i, mat);
    }
    for (const m of [pres, loin]) m.instanceMatrix.needsUpdate = true;
    renderer.shadowMap.needsUpdate = true; // les ombres suivent les canards
    demanderRendu();
  }
```

- [ ] **Step 4: Exposer les nouvelles fonctions et un `canards` toujours à jour**

Dans l'objet renvoyé : ajouter `placerCanards,` et `rebondir,` après `marquerTrouve,`, et remplacer la propriété

```js
    canards: canards.map((c) => ({
      id: c.id, lieu: c.lieu, centre: [c.position[0], c.position[1] + HAUTEUR_CENTRE * k, c.position[2]],
    })),
```

par :

```js
    get canards() {
      return canards.map((c) => ({
        id: c.id, lieu: c.lieu, centre: [c.position[0], c.position[1] + HAUTEUR_CENTRE * k, c.position[2]],
      }));
    },
```

- [ ] **Step 5: Vérifier qu'une partie normale ne change pas**

Run: `cd app && npm test && npm run build` → tout passe.

Puis navigateur (configuration `canard-3d`, `resize_window` 390 × 800) : ouvrir `/?ville=lille`, attendre le chargement, et dans la console :

```js
[jeu.canards.length, jeu.canards[0].id]
```

Expected : `[30, "canard-01"]`, aucune erreur dans la console, la ville s'affiche comme avant (capture d'écran). Trouver un canard avec la recette « Zoomer sur un canard » de `docs/05` : il passe au vert avec un rebond.

- [ ] **Step 6: Commit**

```bash
git add app/src/scene.js
git commit -m "feat(app): scene avec canards fournis et emplacements a remplir"
```

---

### Task 9: Jouer un défi reçu

**Files:**
- Modify: `app/src/main.js`, `app/src/hud.js`, `app/index.html`

- [ ] **Step 1: Écran de fin paramétrable (`index.html`)**

Dans la section `#fin` :
- remplacer `<p class="sous-titre">Les 30 canards sont trouvés</p>` par `<p id="fin-sous-titre" class="sous-titre"></p>` ;
- dans le bouton `#partager-score`, remplacer le texte ` Partager mon score` par ` <span id="partager-score-texte">Partager mon score</span>` ;
- juste avant `<div class="actions-2">`, ajouter :

```html
        <button id="cacher-tour" class="bouton secondaire large" type="button" hidden>
          <svg class="ico" aria-hidden="true"><use href="#i-tap"/></svg> Cacher mes canards à mon tour
        </button>
```

- [ ] **Step 2: `afficherFin` (`hud.js`)**

Remplacer la signature et le début de `afficherFin` :

```js
/**
 * @param stats {ecouleMs, taps, precision}
 * @param medaille {titre, etoiles} (voir titreFin dans partage.js)
 * @param record {texte, nouveau} ou null (voir texteRecord dans partage.js)
 * @param actions {rejouer, partager, autreVille, cacherAMonTour (défi seulement)}
 * @param textes {sousTitre, libellePartager}
 */
export function afficherFin(
  { ecouleMs, taps, precision }, medaille, record,
  { rejouer, partager, autreVille, cacherAMonTour = null },
  { sousTitre = '', libellePartager = 'Partager mon score' } = {},
) {
  $('fin-sous-titre').textContent = sousTitre;
  $('partager-score-texte').textContent = libellePartager;
  const tour = $('cacher-tour');
  tour.hidden = !cacherAMonTour;
  tour.onclick = cacherAMonTour;
```

(le reste de la fonction, à partir de `const r = $('fin-record');`, est inchangé.)

- [ ] **Step 3: Imports de `main.js`**

Remplacer le bloc d'imports (de `import { chargerScene }` jusqu'à l'import de `./hud.js`, polices comprises) par :

```js
import { chargerScene } from './scene.js';
import { ecouterEntrees } from './entrees.js';
import { creerPartie, precision, serialiser, taper, terminee } from './partie.js';
import {
  charger, chargerCle, chargerRecord, effacer, effacerCle, enregistrer, enregistrerCle, meilleur, retenirRecord,
} from './sauvegarde.js';
import { choisirCanard } from './picking.js';
import { creerSon } from './son.js';
import { canardsDuDefi, chargerCachettes } from './cachettes.js';
import {
  decoderDefi, libelleRenvoi, lienCacher, lienDefi, messageRejet, texteInvitationDefi, texteTempsDefi, titreDefi,
  titreFinDefi, verifierDefi,
} from './defi.js';
import { cleDefiRecu } from './mesdefis.js';
import {
  borner, creerVue, deplacer, estRevele, ppmMini, ppmRevelation, projeter, zoomer,
} from './vue.js';
import '@fontsource/fredoka/600.css';
import '@fontsource/fredoka/700.css';
import '@fontsource/nunito/400.css';
import '@fontsource/nunito/700.css';
import '@fontsource/nunito/800.css';
import {
  TEXTE_INVITATION, decouperNom, lienJeu, partagerAvecRetour, progression, resumeVille, sousTitreFin, texteRecord,
  texteScore, titreFin,
} from './partage.js';
import {
  afficherAccueil, afficherAide, afficherBref, afficherChargement, afficherCompteur, afficherFin, afficherHud,
  afficherMessage, afficherSon, afficherStats, celebrer, chrono,
} from './hud.js';
```

- [ ] **Step 4: Préparer un défi et revenir à l'accueil en cas de refus**

Dans `main.js`, juste avant `async function jouer(`, ajouter :

```js
/**
 * Lit le défi du lien et le vérifie contre les cachettes de la ville.
 * @returns {{code, defi, canards}} ou {{raison, contexte}}
 */
async function preparerDefi(info, code) {
  const { ville } = decouperNom(info.nom);
  const lu = decoderDefi(code);
  if (!lu.ok) return { raison: lu.raison, contexte: { ville } };
  const contexte = { ville, prenom: lu.defi.prenom };
  let lot;
  try {
    lot = await chargerCachettes(info.id);
  } catch {
    return { raison: 'pas-pret', contexte };
  }
  const raison = verifierDefi(lu.defi, { version: lot.version, empreinte: lot.empreinte, nombre: lot.cachettes.length });
  if (raison) return { raison, contexte };
  return { code, defi: lu.defi, canards: canardsDuDefi(lot.cachettes, lu.defi.numeros) };
}

/** Retour à l'accueil avec un message, quand un défi (ou le mode « Cacher ») est impossible. */
function refuser(scenes, { raison, contexte }) {
  history.replaceState(null, '', lienJeu(location.href));
  accueil(scenes);
  afficherBref(messageRejet(raison, contexte), 8000);
}
```

- [ ] **Step 5: `jouer` accepte un défi**

Remplacer la fonction `jouer` entière par :

```js
/**
 * Une partie : la ville normale, ou un défi reçu.
 * @param defi null, ou {code, defi: {prenom, numeros…}, canards} (voir preparerDefi)
 */
async function jouer(info, defi = null) {
  const { ville } = decouperNom(info.nom);
  afficherChargement(true, defi ? `${titreDefi(defi.defi.prenom)} · ${ville}…` : `Chargement de ${ville}…`);
  const t0 = performance.now();
  const scene = await chargerScene(canvas, info, defi ? { canards: defi.canards } : {});
  const chargementMs = performance.now() - t0;
  afficherChargement(false);

  // un défi a sa propre progression : la partie normale et le record de la ville n'y sont pour rien
  const cleDefi = defi && cleDefiRecu(defi.code);
  const lire = () => (defi ? chargerCle(localStorage, cleDefi) : charger(localStorage, info.id, info.version));
  const ecrire = (donnees) => (defi
    ? enregistrerCle(localStorage, cleDefi, donnees)
    : enregistrer(localStorage, info.id, info.version, donnees));
  const oublier = () => (defi ? effacerCle(localStorage, cleDefi) : effacer(localStorage, info.id, info.version));

  let partie = creerPartie(scene.canards.map((c) => c.id), lire());
  for (const id of partie.trouves) scene.marquerTrouve(id);

  const ecran = () => ({ w: canvas.clientWidth, h: canvas.clientHeight });
  let vue = creerVue(ecran(), scene.limites);
  const revele = () => estRevele(vue, scene.gabarit);
  const rafraichir = () => {
    vue = borner(vue, ecran(), scene.limites);
    scene.appliquerVue(vue, ecran(), revele());
    afficherAide(revele());
  };

  // temps de jeu : ne compte que lorsque la page est visible et la partie en cours
  let repere = performance.now();
  const horloge = () => {
    const t = performance.now();
    if (!document.hidden && !terminee(partie)) partie = { ...partie, ecouleMs: partie.ecouleMs + (t - repere) };
    repere = t;
  };
  const resume = () => ({ ecouleMs: partie.ecouleMs, taps: partie.taps, precision: precision(partie) });
  // temps, taps et précision en direct : le chrono avance deux fois par seconde
  const majStats = () => {
    horloge();
    afficherStats(resume());
  };
  const minuteur = setInterval(majStats, 500);

  let rejoue = false; // « Rejouer » : plus aucune sauvegarde, sinon la partie finie est réécrite
  const sauver = () => {
    if (rejoue) return;
    horloge();
    ecrire(serialiser(partie));
  };
  document.addEventListener('visibilitychange', sauver);
  window.addEventListener('pagehide', sauver);

  const texteAPartager = () => {
    const n = partie.ids.length;
    if (!defi) return texteScore({ nom: info.nom, trouves: partie.trouves.size, total: n, ...resume() });
    const { prenom } = defi.defi;
    return terminee(partie)
      ? texteTempsDefi({ prenom, n, ville, ecouleMs: partie.ecouleMs })
      : texteInvitationDefi({ prenom, n, ville }); // en cours : on fait suivre le même défi
  };
  const partagerPartie = () => {
    horloge();
    partagerAvecRetour({
      texte: texteAPartager(),
      url: defi ? lienDefi(location.href, info.id, defi.code) : lienJeu(location.href, info.id),
    });
  };

  const finir = () => {
    clearInterval(minuteur);
    majStats(); // dernière valeur exacte, figée
    const medaille = titreFin(precision(partie));
    const actions = {
      rejouer: () => {
        // location.reload() déclenche `pagehide`, donc `sauver` : sans ce drapeau, la partie
        // terminée serait réenregistrée juste après l'effacement et l'écran de fin reviendrait.
        rejoue = true;
        oublier();
        location.reload();
      },
      partager: partagerPartie,
      autreVille: () => allerA(null),
    };
    const sousTitre = sousTitreFin(partie.ids.length);
    if (defi) {
      afficherFin(resume(), { ...medaille, titre: titreFinDefi(defi.defi.prenom) }, null, {
        ...actions,
        cacherAMonTour: () => { location.href = lienCacher(location.href, info.id); },
      }, { sousTitre, libellePartager: libelleRenvoi(defi.defi.prenom) });
      return;
    }
    // le record survit à « Rejouer », qui n'efface que la partie
    const { ancien } = retenirRecord(localStorage, info.id, info.version, resume());
    afficherFin(resume(), medaille, texteRecord(resume(), ancien), actions, { sousTitre });
  };

  const son = creerSon();
  // iOS n'autorise le son qu'après un geste : on débloque l'audio dès le premier contact
  canvas.addEventListener('pointerdown', () => son.deverrouiller(), { once: true });
  afficherHud({
    menu: () => allerA(null),
    partager: partagerPartie,
    son: () => afficherSon(son.basculer()),
  });
  afficherSon(son.actif());

  ecouterEntrees(canvas, {
    deplacer: (dx, dy) => {
      vue = deplacer(vue, dx, dy);
      rafraichir();
    },
    zoomer: (facteur, point) => {
      vue = zoomer(vue, facteur, point, ecran(), scene.limites);
      rafraichir();
    },
    taper: (point) => {
      if (terminee(partie)) return;
      const e = ecran();
      const aLEcran = scene.canards
        .filter((c) => !partie.trouves.has(c.id))
        .map((c) => ({ id: c.id, ...projeter(c.centre, vue, e, scene.axes), rayon: (scene.gabarit / 2) * vue.ppm }));
      const resultat = taper(partie, choisirCanard(point, aLEcran, { revele: revele() }));
      partie = resultat.partie;
      if (resultat.trouve) {
        scene.marquerTrouve([...partie.trouves].at(-1), true);
        afficherCompteur(partie.trouves.size, partie.ids.length);
        celebrer();
        son.coin();
      }
      sauver();
      majStats(); // le tap compte tout de suite, sans attendre le prochain tic du chrono
      if (terminee(partie)) {
        son.fanfare(1); // la musique de fin, une fois le dernier « coin coin » fini
        finir();
      }
    },
  });

  window.addEventListener('resize', rafraichir);
  afficherCompteur(partie.trouves.size, partie.ids.length);
  majStats();
  rafraichir();
  if (terminee(partie)) finir();

  // pour le diagnostic depuis la console : window.jeu.stats()
  window.jeu = { stats: scene.stats, vue: () => vue, partie: () => serialiser(partie), canards: scene.canards, axes: scene.axes };

  // `&debug` dans l'adresse : panneau de mesure de fluidité (voir docs/05)
  if (new URLSearchParams(location.search).has('debug')) {
    const { installerMesure } = await import('./mesure.js');
    installerMesure({
      scene,
      ville: info.id,
      chargementMs,
      lireVue: () => vue,
      regler: (v) => {
        vue = v;
        rafraichir();
      },
      zooms: { ensemble: ppmMini(ecran(), scene.limites), moyen: 30, pres: 1.2 * ppmRevelation(scene.gabarit) },
    });
  }
}
```

- [ ] **Step 6: Aiguiller vers un défi**

Remplacer `demarrer` par :

```js
async function demarrer() {
  const scenes = await chargerIndex();
  const params = new URLSearchParams(location.search);
  const info = scenes.find((s) => s.id === params.get('ville'));
  // pas de ville, ou une ville inconnue (vieux lien) : on montre l'accueil
  if (!info) {
    accueil(scenes);
    return;
  }
  if (!params.has('defi')) {
    await jouer(info);
    return;
  }
  const prepare = await preparerDefi(info, params.get('defi'));
  if (prepare.raison) refuser(scenes, prepare);
  else await jouer(info, prepare);
}
```

- [ ] **Step 7: Tests et build**

Run: `cd app && npm test && npm run build`
Expected: tout passe.

- [ ] **Step 8: Vérifier dans le navigateur (390 × 800)**

1. `/?ville=lille` : partie normale inchangée, écran de fin « Les 30 canards sont trouvés » (sauvegarde terminée injectée depuis `/scenes.json`, recette de `docs/05`), bouton « Cacher mes canards à mon tour » **absent**.
2. Fabriquer un défi de 2 canards depuis une page sans jeu (`/scenes.json`), console :

```js
const { encoderDefi } = await import('/src/defi.js');
const c = await (await fetch('/scenes/lille/cachettes.json')).json();
location.href = `/?ville=lille&defi=${encoderDefi({ version: c.version, empreinte: c.empreinte, numeros: [0, 500], prenom: 'Camille' })}`;
```

   Expected : chargement « Le défi de Camille · Lille… », compteur « 0 / 2 ». Trouver les deux canards (recette « Zoomer sur un canard ») : fin « Défi de Camille réussi ! », « Les 2 canards sont trouvés », bouton « Envoyer mon temps à Camille », bouton « Cacher mes canards à mon tour » visible. Capture d'écran.
3. `/?ville=lille&defi=abc` : retour à l'accueil, message « Ce lien de défi est abîmé. », adresse nettoyée (`/?` sans paramètres).
4. Remettre à zéro depuis `/scenes.json` : `Object.keys(localStorage).filter((k) => k.startsWith('jeu-canard-3d:')).forEach((k) => localStorage.removeItem(k))` (prévenir l'utilisateur si des sauvegardes réelles existaient avant : les lister d'abord).

- [ ] **Step 9: Commit**

```bash
git add app/src/main.js app/src/hud.js app/index.html
git commit -m "feat(app): jouer un defi recu par lien"
git push
```

---

### Task 10: L'écran « Cacher mes canards »

**Files:**
- Create: `app/src/cacher.js`
- Modify: `app/src/hud.js`, `app/index.html`, `app/src/style.css`, `app/src/main.js`

- [ ] **Step 1: Aide paramétrable et HUD « Cacher » (`hud.js`)**

Remplacer la fonction `afficherAide` (et son commentaire) par :

```js
export const AIDE_JEU = {
  loin: 'Zoome sur un point jaune pour voir si c’est un canard.',
  pres: 'Touche le canard : bec orange, œil noir. Regarde aussi derrière les vitres !',
};
export const AIDE_CACHER = {
  loin: 'Zoome, puis tape là où cacher un canard.',
  pres: 'Tape pour cacher un canard ; tape un canard posé pour le retirer.',
};

/**
 * Aide contextuelle, en bas de l'écran. Chaque message reste 5 s puis disparaît ; il ne
 * revient que lorsque le message change (passage du zoom de révélation, dans un sens ou l'autre).
 */
export function afficherAide(revele, textes = AIDE_JEU) {
  const aide = $('aide');
  const texte = revele ? textes.pres : textes.loin;
  if (aide.textContent === texte) return; // déjà montré (ou déjà effacé) : on ne le relance pas
  aide.textContent = texte;
  aide.hidden = false;
  clearTimeout(minuterieAide);
  minuterieAide = setTimeout(() => { aide.hidden = true; }, DUREE_AIDE_MS);
}
```

Après `afficherSon`, ajouter :

```js
/** Barre du mode « Cacher » : compteur de canards posés, menu et partage ; ni chrono ni son. */
export function afficherHudCacher({ menu, partager }) {
  $('menu').onclick = menu;
  $('partager').onclick = partager;
  $('partager').setAttribute('aria-label', 'Envoyer mon défi');
  $('compteur').setAttribute('aria-label', 'Canards cachés');
  $('stats').hidden = true;
  $('son').hidden = true;
  $('hud').hidden = false;
}

/** Le bouton de partage n'a de sens qu'à partir d'un canard caché. */
export function activerPartage(actif) {
  $('partager').disabled = !actif;
}

/**
 * Panneau « Envoyer le défi » : demande le prénom (facultatif).
 * @returns {Promise<string|null>} le prénom saisi, ou null si le joueur annule
 */
export function demanderPrenom(initial) {
  const panneau = $('panneau-defi');
  const champ = $('prenom');
  champ.value = initial;
  panneau.hidden = false;
  champ.focus();
  return new Promise((resoudre) => {
    const fermer = (valeur) => {
      panneau.hidden = true;
      $('panneau-form').onsubmit = null;
      $('panneau-annuler').onclick = null;
      resoudre(valeur);
    };
    $('panneau-form').onsubmit = (e) => {
      e.preventDefault();
      fermer(champ.value);
    };
    $('panneau-annuler').onclick = () => fermer(null);
  });
}
```

- [ ] **Step 2: Panneau prénom (`index.html`)**

Juste avant `<script type="module" src="./src/main.js"></script>`, ajouter :

```html
  <!-- PANNEAU « ENVOYER LE DÉFI » (mode Cacher) -->
  <section id="panneau-defi" class="voile" hidden>
    <form id="panneau-form" class="carte-fin panneau" role="dialog" aria-labelledby="panneau-titre">
      <h2 id="panneau-titre">Envoyer le défi</h2>
      <label class="champ" for="prenom">Ton prénom <span>(facultatif)</span></label>
      <input id="prenom" class="champ-texte" type="text" maxlength="20" autocomplete="given-name" enterkeyhint="send">
      <p class="pied">Il apparaît dans le lien : ton ami saura que le défi vient de toi.</p>
      <div class="actions">
        <button class="bouton large" type="submit">
          <svg class="ico" aria-hidden="true"><use href="#i-partager"/></svg> Envoyer le défi
        </button>
        <button id="panneau-annuler" class="bouton secondaire large" type="button">Annuler</button>
      </div>
    </form>
  </section>
```

- [ ] **Step 3: Styles (`style.css`)**

Ajouter à la fin de `app/src/style.css` :

```css
/* ------------------------------------------------------- mode « Cacher mes canards » */

.rond:disabled { opacity: 0.45; cursor: default; box-shadow: none; }

.panneau { padding-top: 22px; }
.panneau h2 { margin: 0 0 14px; font-family: var(--titre); font-size: 26px; }
.champ { display: block; margin-bottom: 6px; text-align: left; font-weight: 800; }
.champ span { color: var(--doux); font-weight: 600; }
.champ-texte {
  width: 100%;
  min-height: 48px;
  padding: 10px 14px;
  font: inherit;
  font-size: 18px; /* 16 px au moins : iOS ne zoome pas sur le champ */
  color: var(--encre);
  background: #fff;
  border: var(--trait) solid var(--encre);
  border-radius: 14px;
}
.champ-texte:focus-visible { outline: 3px solid var(--orange); outline-offset: 2px; }
.panneau .pied { margin: 8px 0 16px; text-align: left; }
```

- [ ] **Step 4: Écrire `cacher.js`**

`app/src/cacher.js` :

```js
// Écran « Cacher mes canards » : on pose ses canards sur des cachettes garanties visibles,
// puis on envoie le lien du défi. Assemble scène, vue, gestes, aimant et « Mes défis ».
import { chargerScene } from './scene.js';
import { ecouterEntrees } from './entrees.js';
import { choisirCanard } from './picking.js';
import { aimanter, canardsDuDefi, chargerCachettes, idCachette } from './cachettes.js';
import { MAX_CANARDS, encoderDefi, lienDefi, nettoyerPrenom, texteInvitationDefi } from './defi.js';
import { dernierPrenom, enregistrerDefi, nouvelId, retenirPrenom, trouverDefi } from './mesdefis.js';
import { borner, creerVue, deplacer, estRevele, projeter, zoomer } from './vue.js';
import { decouperNom, lienJeu, partagerAvecRetour } from './partage.js';
import {
  AIDE_CACHER, activerPartage, afficherAide, afficherBref, afficherChargement, afficherCompteur, afficherHudCacher,
  celebrer, demanderPrenom,
} from './hud.js';

const RAISONS = {
  zoom: 'Zoome davantage pour cacher un canard.',
  aucune: 'Pas de cachette ici : essaie un rebord, un balcon, un toit…',
  'trop-pres': 'Trop près d’un autre canard.',
  plein: `${MAX_CANARDS} canards au maximum : retires-en un pour le déplacer.`,
};

/**
 * @param info ligne de scenes.json
 * @param idDefi défi de « Mes défis » à modifier, ou '' pour un nouveau
 * @returns null, ou {raison, contexte} si le mode n'est pas disponible pour cette ville
 */
export async function cacher(canvas, info, idDefi) {
  const { ville } = decouperNom(info.nom);
  let lot;
  try {
    lot = await chargerCachettes(info.id);
  } catch {
    return { raison: 'pas-pret', contexte: { ville } };
  }

  // un défi fait pour une autre version de la ville ne se modifie plus : on en commence un neuf
  const existant = idDefi ? trouverDefi(localStorage, idDefi) : null;
  const valable = existant && existant.ville === info.id
    && existant.version === lot.version && existant.empreinte === lot.empreinte;
  const defi = valable ? { ...existant } : {
    id: nouvelId(),
    ville: info.id,
    version: lot.version,
    empreinte: lot.empreinte,
    prenom: dernierPrenom(localStorage),
    numeros: [],
    cree: Date.now(),
  };

  afficherChargement(true, `Chargement de ${ville}…`);
  const scene = await chargerScene(canvas, info, {
    canards: canardsDuDefi(lot.cachettes, defi.numeros), capacite: MAX_CANARDS,
  });
  afficherChargement(false);

  const ecran = () => ({ w: canvas.clientWidth, h: canvas.clientHeight });
  let vue = creerVue(ecran(), scene.limites);
  const revele = () => estRevele(vue, scene.gabarit);
  const rafraichir = () => {
    vue = borner(vue, ecran(), scene.limites);
    scene.appliquerVue(vue, ecran(), revele());
    afficherAide(revele(), AIDE_CACHER);
  };

  const majCompteur = () => {
    afficherCompteur(defi.numeros.length, MAX_CANARDS);
    activerPartage(defi.numeros.length > 0);
  };
  /** Nouveaux canards posés : scène, brouillon gardé dans « Mes défis », compteur. */
  const changer = (numeros) => {
    defi.numeros = numeros;
    scene.placerCanards(canardsDuDefi(lot.cachettes, numeros));
    enregistrerDefi(localStorage, defi);
    majCompteur();
  };

  const partager = async () => {
    if (!defi.numeros.length) return;
    const prenom = await demanderPrenom(defi.prenom);
    if (prenom === null) return; // panneau fermé
    defi.prenom = nettoyerPrenom(prenom);
    retenirPrenom(localStorage, defi.prenom);
    enregistrerDefi(localStorage, defi);
    partagerAvecRetour({
      texte: texteInvitationDefi({ prenom: defi.prenom, n: defi.numeros.length, ville }),
      url: lienDefi(location.href, info.id, encoderDefi(defi)),
    });
  };

  afficherHudCacher({ menu: () => { location.href = lienJeu(location.href); }, partager });

  ecouterEntrees(canvas, {
    deplacer: (dx, dy) => {
      vue = deplacer(vue, dx, dy);
      rafraichir();
    },
    zoomer: (facteur, point) => {
      vue = zoomer(vue, facteur, point, ecran(), scene.limites);
      rafraichir();
    },
    taper: (point) => {
      const e = ecran();
      // un canard déjà posé sous le doigt : on le retire
      const posees = scene.canards.map((c) => ({
        id: c.id, ...projeter(c.centre, vue, e, scene.axes), rayon: (scene.gabarit / 2) * vue.ppm,
      }));
      const touche = choisirCanard(point, posees, { revele: revele() });
      if (touche !== null) {
        changer(defi.numeros.filter((n) => idCachette(n) !== touche));
        return;
      }
      const ecranCachettes = lot.cachettes.map((c) => ({ numero: c.numero, ...projeter(c.centre, vue, e, scene.axes) }));
      const choix = aimanter(point, ecranCachettes, lot.cachettes, defi.numeros, {
        revele: revele(), distanceMin: lot.distanceMin,
      });
      if (choix.raison) {
        afficherBref(RAISONS[choix.raison]);
        return;
      }
      changer([...defi.numeros, choix.numero]);
      scene.rebondir(defi.numeros.length - 1);
      celebrer();
    },
  });

  window.addEventListener('resize', rafraichir);
  majCompteur();
  rafraichir();

  // pour les vérifications depuis la console (voir docs/05)
  window.jeu = { vue: () => vue, axes: scene.axes, cachettes: lot.cachettes, defi: () => ({ ...defi }) };
  return null;
}
```

- [ ] **Step 5: Aiguiller vers `cacher` (`main.js`)**

Ajouter l'import `import { cacher } from './cacher.js';` après celui de `./scene.js`, puis dans `demarrer`, juste après le bloc `if (!info) { … }`, insérer :

```js
  if (params.has('cacher')) {
    const refus = await cacher(canvas, info, params.get('cacher'));
    if (refus) refuser(scenes, refus);
    return;
  }
```

- [ ] **Step 6: Tests et build**

Run: `cd app && npm test && npm run build`
Expected: tout passe.

- [ ] **Step 7: Vérifier dans le navigateur (390 × 800)**

1. Ouvrir `/?ville=lille&cacher=` : la ville sans canards, compteur « 0 / 30 », pas de chrono ni de bouton son, bouton partager grisé, aide « Zoome, puis tape là où cacher un canard. ».
2. Zoomer vers une cachette (console), puis **vrai clic** à la position donnée :

```js
const cv = document.getElementById('scene');
const cible = jeu.cachettes[200];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const pos = () => { const v = jeu.vue(); return {
  x: cv.clientWidth / 2 + (dot(cible.centre, jeu.axes.droite) - v.u) * v.ppm,
  y: cv.clientHeight / 2 - (dot(cible.centre, jeu.axes.haut) - v.v) * v.ppm }; };
for (let k = 0; k < 13; k++) {
  const p = pos();
  cv.dispatchEvent(new WheelEvent('wheel', { deltaY: -200, clientX: p.x, clientY: p.y, bubbles: true, cancelable: true }));
}
pos();
```

   Expected après le clic : un canard apparaît avec un rebond, compteur « 1 / 30 », partage actif, `jeu.defi().numeros` vaut `[200]` (ou une cachette voisine). Capture d'écran.
3. Clic au même endroit : le canard disparaît, « 0 / 30 ». Le reposer.
4. Clic tout près (à moins de 6 m) d'un canard posé, hors de lui : message « Trop près d'un autre canard. ». Dézoomer et taper : « Zoome davantage… ».
5. Poser un 2e et un 3e canard (cachettes 900 et 1800), puis bouton partager : panneau « Envoyer le défi » (capture), saisir « Camille », Envoyer → toast « Message et lien copiés ». Lire le presse-papiers n'est pas possible : prendre le lien avec
   `(await import('/src/defi.js')).lienDefi(location.href, 'lille', (await import('/src/defi.js')).encoderDefi(jeu.defi()))`,
   l'ouvrir : « Le défi de Camille · Lille… », compteur « 0 / 3 ».
6. Revenir sur `/?ville=lille&cacher=<id de jeu.defi()>` : les 3 canards sont toujours posés.

- [ ] **Step 8: Commit**

```bash
git add app/src/cacher.js app/src/hud.js app/src/main.js app/index.html app/src/style.css
git commit -m "feat(app): ecran Cacher mes canards (pose aimantee, retrait, envoi du defi)"
git push
```

---

### Task 11: « Cacher mes canards » et « Mes défis » sur l'accueil

**Files:**
- Modify: `app/index.html`, `app/src/hud.js`, `app/src/main.js`, `app/src/style.css`

- [ ] **Step 1: Éléments de l'accueil (`index.html`)**

- Ajouter l'icône dans `<defs>`, après le symbole `i-etoile` :

```html
      <symbol id="i-corbeille" viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6"/></symbol>
```

  (vérifier que les autres symboles n'ont pas d'attributs de trait propres ; sinon copier ceux de `i-carte`.)
- Remplacer `<h2>Choisis ta ville</h2>` par `<h2 id="titre-villes">Choisis ta ville</h2>`.
- Juste après `<div id="villes" class="villes"></div>`, ajouter :

```html
      <button id="cacher" class="bouton large" type="button">
        <svg class="ico" aria-hidden="true"><use href="#i-tap"/></svg> <span id="cacher-texte">Cacher mes canards</span>
      </button>
      <section id="mes-defis" class="mes-defis" hidden>
        <h2>Mes défis</h2>
        <div id="liste-defis" class="liste-defis"></div>
      </section>
```

- [ ] **Step 2: Mode « choisir où cacher » et cartes (`hud.js`)**

Dans `afficherAccueil`, changer la signature en `export function afficherAccueil(villes, { choisir, inviter, cacher }) {`, remplacer `b.onclick = () => choisir(v.id);` par `b.onclick = () => (modeCacher ? cacher(v.id) : choisir(v.id));`, et insérer au **début** de la fonction :

```js
  // « Cacher mes canards » : les tickets servent alors à choisir la ville où cacher
  let modeCacher = false;
  $('cacher').onclick = () => {
    modeCacher = !modeCacher;
    $('titre-villes').textContent = modeCacher ? 'Où cacher tes canards ?' : 'Choisis ta ville';
    $('cacher-texte').textContent = modeCacher ? 'Annuler' : 'Cacher mes canards';
    $('cacher').classList.toggle('secondaire', modeCacher);
    $('accueil').classList.toggle('mode-cacher', modeCacher);
    if (modeCacher) $('titre-villes').scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
```

Puis ajouter après `afficherAccueil` :

```js
/**
 * Section « Mes défis » de l'accueil, masquée si la liste est vide.
 * @param defis [{id, embleme, couleur, ville, detail (« 7 canards · 21/11 »), valable}]
 */
export function afficherMesDefis(defis, { envoyer, modifier, supprimer }) {
  $('mes-defis').hidden = !defis.length;
  $('liste-defis').replaceChildren(...defis.map((d) => {
    const carte = element('div', `carte-defi${d.valable ? '' : ' perime'}`);
    carte.style.setProperty('--couleur', d.couleur);
    const texte = element('span', 'texte');
    texte.append(
      element('span', 'nom', d.ville),
      element('span', 'detail', d.valable ? d.detail : `${d.detail} · plus valable`),
    );
    const actions = element('span', 'actions-defi');
    const bouton = (libelle, nomIcone, action, classe = '') => {
      const b = element('button', `mini-bouton ${classe}`.trim());
      b.type = 'button';
      b.append(icone(nomIcone), element('span', '', libelle));
      b.onclick = () => action(d.id);
      return b;
    };
    if (d.valable) actions.append(bouton('Envoyer', 'i-partager', envoyer), bouton('Modifier', 'i-tap', modifier));
    actions.append(bouton('Supprimer', 'i-corbeille', supprimer, 'discret'));
    carte.append(element('span', 'embleme', d.embleme), texte, actions);
    return carte;
  }));
}
```

- [ ] **Step 3: Brancher l'accueil (`main.js`)**

Remplacer les imports de `./defi.js` et `./mesdefis.js` par :

```js
import {
  decoderDefi, encoderDefi, libelleRenvoi, lienCacher, lienDefi, messageRejet, texteInvitationDefi, texteTempsDefi,
  titreDefi, titreFinDefi, verifierDefi,
} from './defi.js';
import {
  cleDefiRecu, detailDefi, estValable, listerDefis, supprimerDefi, trouverDefi,
} from './mesdefis.js';
```

et ajouter `afficherMesDefis` à la liste importée de `./hud.js` (après `afficherFin`).

Dans `accueil(scenes)`, remplacer l'appel `afficherAccueil(villes, {...});` par :

```js
  afficherAccueil(villes, {
    choisir: allerA,
    inviter: () => partagerAvecRetour({ texte: TEXTE_INVITATION, url: lienJeu(location.href) }),
    cacher: (ville) => { location.href = lienCacher(location.href, ville); },
  });
  montrerMesDefis(scenes);
```

Puis ajouter après `accueil` :

```js
/** Section « Mes défis » : renvoyer, modifier ou supprimer un défi créé sur cet appareil. */
function montrerMesDefis(scenes) {
  const parId = new Map(scenes.map((s) => [s.id, s]));
  const nomVille = (id) => decouperNom(parId.get(id).nom).ville;
  const defis = listerDefis(localStorage).filter((d) => parId.has(d.ville));
  afficherMesDefis(defis.map((d) => ({
    id: d.id,
    embleme: parId.get(d.ville).embleme ?? '🏙️',
    couleur: parId.get(d.ville).couleur ?? '#3f6fd8',
    ville: nomVille(d.ville),
    detail: detailDefi(d),
    valable: estValable(d, scenes),
  })), {
    envoyer: (id) => {
      const d = trouverDefi(localStorage, id);
      partagerAvecRetour({
        texte: texteInvitationDefi({ prenom: d.prenom, n: d.numeros.length, ville: nomVille(d.ville) }),
        url: lienDefi(location.href, d.ville, encoderDefi(d)),
      });
    },
    modifier: (id) => {
      location.href = lienCacher(location.href, trouverDefi(localStorage, id).ville, id);
    },
    supprimer: (id) => {
      if (!window.confirm('Supprimer ce défi ? Les liens déjà envoyés continueront de marcher.')) return;
      supprimerDefi(localStorage, id);
      montrerMesDefis(scenes);
    },
  });
}
```

- [ ] **Step 4: Styles (`style.css`)**

Ajouter à la fin de `app/src/style.css` :

```css
#cacher { margin-bottom: 12px; }
.mode-cacher .carte-ville { outline: 3px dashed var(--orange); outline-offset: 3px; }

.mes-defis { margin: 12px 0 24px; }
.liste-defis { display: grid; gap: 12px; }
.carte-defi {
  --couleur: #3f6fd8;
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 8px 12px;
  padding: 12px 14px 12px 22px;
  background: linear-gradient(var(--couleur), var(--couleur)) left / 10px 100% no-repeat, var(--carton);
  border: var(--trait) solid var(--encre);
  border-radius: var(--rayon);
  box-shadow: var(--ombre-petite);
}
.carte-defi.perime { opacity: 0.6; }
.carte-defi .embleme { font-size: 30px; line-height: 1; }
.carte-defi .nom { display: block; font-family: var(--titre); font-size: 20px; font-weight: 700; }
.carte-defi .detail { display: block; font-size: 14px; font-weight: 700; color: var(--doux); }
.carte-defi .actions-defi { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 8px; }
.mini-bouton {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  padding: 6px 14px;
  font-family: var(--titre);
  font-size: 15px;
  font-weight: 600;
  color: var(--encre);
  background: var(--jaune);
  border: 2px solid var(--encre);
  border-radius: 999px;
  box-shadow: 2px 2px 0 var(--encre);
  cursor: pointer;
}
.mini-bouton.discret { background: var(--carton); }
.mini-bouton .ico { width: 18px; height: 18px; }
```

- [ ] **Step 5: Tests et build**

Run: `cd app && npm test && npm run build`
Expected: tout passe.

- [ ] **Step 6: Vérifier dans le navigateur (390 × 800, puis ordinateur)**

1. `/` sans défi : bouton « Cacher mes canards » sous les tickets, pas de section « Mes défis ». Clic : titre « Où cacher tes canards ? », tickets en pointillés, bouton « Annuler ». Clic sur Lille : `/?ville=lille&cacher=`.
2. Avec les défis de la tâche 10 : section « Mes défis », carte « Lille · 3 canards · jj/mm » avec Envoyer, Modifier, Supprimer (captures 390 px et ordinateur).
3. Envoyer : toast « Message et lien copiés ». Modifier : écran « Cacher » avec les 3 canards.
4. Défi grisé : depuis `/scenes.json`, modifier l'empreinte d'un défi gardé
   (`const l = JSON.parse(localStorage['jeu-canard-3d:mes-defis']); l[0].empreinte = 'zzzz'; localStorage['jeu-canard-3d:mes-defis'] = JSON.stringify(l);`),
   ouvrir `/` : carte grisée « … · plus valable », seul Supprimer reste. Supprimer → confirmation → la carte disparaît.
5. Remettre à zéro les sauvegardes de test depuis `/scenes.json` (voir tâche 9, étape 8).

- [ ] **Step 7: Commit**

```bash
git add app/index.html app/src/hud.js app/src/main.js app/src/style.css
git commit -m "feat(app): Cacher mes canards et Mes defis sur l'accueil"
git push
```

---

### Task 12: Documentation

**Files:**
- Modify: `docs/01-comprendre-le-projet.md`, `docs/05-publier-et-depanner.md`, `docs/06-pistes-d-amelioration.md`, `CLAUDE.md`, `docs/superpowers/specs/2026-11-22-cacher-mes-canards-design.md`

- [ ] **Step 1: `docs/01`** — dans la partie formats de fichiers : `cachettes.json` (champs, une cachette par ligne, numéro = position, empreinte) et le champ `empreinte` de `scenes.json` ; dans la partie app : `defi.js`, `cachettes.js`, `mesdefis.js`, `cacher.js` ; dans la partie sauvegarde : clés `jeu-canard-3d:mes-defis`, `jeu-canard-3d:prenom`, `jeu-canard-3d:defi:<code>` ; le format du lien de défi (tableau d'octets de la spec, section 4) ; nombres de tests à jour.
- [ ] **Step 2: `docs/05`** — recettes de la tâche 9 (fabriquer un lien de défi depuis la console) et de la tâche 10 (zoomer sur une cachette avec `jeu.cachettes`) ; rappeler que relancer seulement le placement (`place_objets.py`) réécrit `cachettes.json` et l'empreinte, et qu'une empreinte changée invalide les défis déjà envoyés pour cette ville.
- [ ] **Step 3: `docs/06`** — section 1 : marquer « fait (22/11/2026) », garder la « variante plus libre » comme piste ; mettre à jour l'ordre conseillé (prochaine piste : niveaux de difficulté).
- [ ] **Step 4: `CLAUDE.md`** — table des fichiers de l'app (nouveaux modules, colonne « Testé »), nombre de tests (Python et JS), état (mode défi), règles qui définissent le jeu (un canard de défi n'est posé que sur une cachette de `cachettes.json`), piège : « augmenter la `version` ou régénérer une ville change l'empreinte : les défis envoyés pour cette ville deviennent invalides (le jeu le dit) ».
- [ ] **Step 5: Spec** — vérifier que le code correspond à la spec ; noter tout écart dans son journal des révisions.
- [ ] **Step 6: Vérifier et commiter**

```bash
python -m unittest discover -s blender/tests -t blender
cd app && npm test && cd ..
git add docs CLAUDE.md
git commit -m "docs: mode Cacher mes canards (formats, recettes, etat)"
git push
```

Puis vérifier que la publication GitHub Pages passe (onglet Actions, ou l'API publique comme dans `docs/05`) et ouvrir le site publié sur `?ville=lille&cacher=`.
