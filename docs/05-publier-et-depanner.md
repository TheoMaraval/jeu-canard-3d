# 05 — Publier et dépanner

## Ce qu'il faut sur la machine

| Outil | Pourquoi | Où |
|---|---|---|
| Git | Versions et publication | — |
| Node.js 22 et npm | L'application | — |
| Python 3 | Tests du générateur | — |
| Blender 5.3 | Générer les villes | `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe` (pas dans le PATH ; `tout_generer.sh` le trouve tout seul, sinon variable `BLENDER`) |

Seul Blender est nécessaire pour **générer**. Pour modifier l'app seule (interface, règles
du tap, compteurs), Node suffit.

## Jouer en local

```bash
cd app
npm install        # la première fois
npm run dev        # http://localhost:5173
```

- L'accueil : `http://localhost:5173/` ; une ville précise : `http://localhost:5173/?ville=lille`.
- Le partage natif n'existe que sur téléphone (et sur certains navigateurs d'ordinateur) ;
  ailleurs, le bouton copie le message et le lien. En local, les liens partagés pointent
  vers `localhost` : seuls ceux du site publié sont utilisables par d'autres.
- **Sur un téléphone du même Wi-Fi** : utiliser l'adresse « Network » affichée par
  `npm run dev` (par exemple `http://192.168.1.20:5173`).
- Dans une session Claude, le serveur se lance avec la configuration `canard-3d` de
  `.claude/launch.json`.

## Les tests

```bash
python -m unittest discover -s blender/tests -t blender   # 41 tests du générateur, sans Blender
cd app && npm test                                        # 51 tests de l'app
```

## Publier

Le site est servi par **GitHub Pages** depuis le dépôt `TheoMaraval/jeu-canard-3d`.

```bash
git add -A
git commit -m "ce qui a changé"
git push
```

À chaque envoi sur `main`, le workflow `.github/workflows/pages.yml` installe l'app, lance
ses tests, la construit (en y copiant tout `assets/`) et publie le résultat. Compter deux à
cinq minutes. Si les tests échouent, le site reste sur la version précédente.

- Suivre la publication : onglet **Actions** du dépôt sur GitHub.
- Le site : **https://theomaraval.github.io/jeu-canard-3d/**
- Sur téléphone, après une mise à jour : recharger la page ; si l'ancienne version reste,
  fermer et rouvrir l'onglet.

**Important** : le générateur ne tourne pas sur GitHub (il faudrait Blender). Les fichiers
de `assets/` doivent donc être générés en local et **commités** avec le thème.

## Diagnostiquer dans le navigateur

Ouvrir la console du navigateur (F12 sur ordinateur) sur la page du jeu :

| Commande | Réponse |
|---|---|
| `jeu.stats()` | Ce que dessine la dernière image : `triangles`, `calls` (appels de dessin), nombre d'objets |
| `&debug` dans l'adresse | Panneau de mesure de fluidité (voir plus bas) |
| `jeu.vue()` | Position et zoom (`ppm` = pixels par mètre) |
| `jeu.partie()` | Canards trouvés, taps, temps |
| `jeu.canards` | Les 30 canards, avec leur lieu (`vitre`, `toit`…) |

Pour remettre une ville à zéro : console, puis
`localStorage.removeItem('jeu-canard-3d:paris:v3')` et recharger.

## Tester dans le navigateur (sans téléphone)

Recettes utilisées pour vérifier les changements, par exemple dans le navigateur intégré de
Claude. Toujours tester à **taille de téléphone (390 × 800)** en plus de l'ordinateur.

**Préparer une sauvegarde** (une ville à moitié faite, une ville terminée). Le faire depuis
une page **sans jeu**, sinon le jeu réécrit sa propre sauvegarde en quittant la page :

```js
// sur http://localhost:5173/scenes.json, dans la console
const ids = (n) => Array.from({ length: n }, (_, i) => 'canard-' + String(i + 1).padStart(2, '0'));
localStorage.setItem('jeu-canard-3d:paris:v3', JSON.stringify({ trouves: ids(12), taps: 20, ecouleMs: 187000 }));
localStorage.setItem('jeu-canard-3d:lille:v3', JSON.stringify({ trouves: ids(30), taps: 41, ecouleMs: 754000 }));
```

Puis ouvrir `/` (accueil avec les progressions) ou `/?ville=lille` (écran de fin).
Pour un record : `localStorage.setItem('jeu-canard-3d:paris:v3:record', JSON.stringify({ ecouleMs: 492000, taps: 44 }))`.
Une sauvegarde à 29/30 plus rapide que le record, puis le dernier canard trouvé, montre
« Nouveau record ! ». Effacer ensuite ces sauvegardes et records, toujours depuis `/scenes.json`.

**Zoomer sur un canard pour le trouver** (dans une partie, console) :

```js
const cv = document.getElementById('scene');
const cible = jeu.canards.find((c) => !jeu.partie().trouves.includes(c.id));
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const pos = () => { const v = jeu.vue(); return {
  x: cv.clientWidth / 2 + (dot(cible.centre, jeu.axes.droite) - v.u) * v.ppm,
  y: cv.clientHeight / 2 - (dot(cible.centre, jeu.axes.haut) - v.v) * v.ppm }; };
for (let k = 0; k < 13; k++) {
  const p = pos();
  cv.dispatchEvent(new WheelEvent('wheel', { deltaY: -200, clientX: p.x, clientY: p.y, bubbles: true, cancelable: true }));
}
pos(); // coordonnées du canard à l'écran : taper (vrai clic) à cet endroit
```

Le canard n'est « révélé » (bec visible, tap accepté) qu'à partir de `jeu.vue().ppm` ≥ 80.

**Analyser les sons sans les jouer** (on ne peut pas les écouter depuis un script) :

```js
const { creerSon } = await import('/src/son.js');
let ctx;
class HorsLigne extends OfflineAudioContext {
  constructor() { super(1, 44100 * 3, 44100); ctx = this; }
  resume() { return Promise.resolve(); }
}
const son = creerSon({ getItem: () => null, setItem() {} }, HorsLigne);
son.deverrouiller();
await new Promise((r) => setTimeout(r, 800)); // téléchargement et décodage des fichiers
son.coin(); // ou son.fanfare()
const d = (await ctx.startRendering()).getChannelData(0); // échantillons : volume, durée…
```

Repères actuels du « coin coin » : environ 0,9 s audible (deux « coin »), pic vers 0,75
(pas de saturation). Sans attendre le décodage, c'est le cri synthétisé qui est rendu
(~0,45 s).

**Vérifier les sons pendant une vraie partie, sans bruit** (console de la partie, avant
de taper) : remplacer la lecture par un journal.

```js
window.journalSon = [];
AudioBufferSourceNode.prototype.start = function (quand) {
  journalSon.push({ duree: this.buffer.duration, dans: quand - this.context.currentTime });
};
OscillatorNode.prototype.start = function () { journalSon.push('synthèse'); };
AudioScheduledSourceNode.prototype.stop = function () {}; // sinon `stop` sans `start` lève une erreur
```

Toucher la ville une première fois (déblocage du son), attendre une seconde, puis trouver
le dernier canard d'une sauvegarde à 29/30 : le journal montre le « coin coin » (1,25 s,
tout de suite) puis la musique (1,78 s, une seconde après).

**Changer un son** : enregistrer (par exemple avec l'Enregistreur Windows), puis découper
et convertir en MP3 avec ffmpeg (installé par `winget install Gyan.FFmpeg`). Repérer
d'abord où commence et finit le son (filtre `silencedetect`), puis :

```bash
ffmpeg -i enregistrement.m4a -af "atrim=start=1.07:end=2.32,asetpts=PTS-STARTPTS,aformat=channel_layouts=mono,volume=5dB,afade=t=in:d=0.005,afade=t=out:st=1.20:d=0.05" -ar 44100 -c:a libmp3lame -b:a 96k assets/sons/coin.mp3
ffmpeg -i assets/sons/coin.mp3 -af volumedetect -f null -   # max_volume doit rester sous 0 dB
```

(`fin.mp3` : `atrim=start=0.80`, `volume=4dB`, fondu de sortie à 1,70 s.) MP3 parce que
tous les navigateurs le décodent (Safari ne lit pas toujours l'Ogg). Un son pris sur
Internet doit avoir une licence claire : pas de son tiré de YouTube.

**Partage** : sans partage natif (ordinateur), le bouton copie le message et le lien dans
le presse-papiers. Pour simuler le partage d'un téléphone :
`Object.defineProperty(navigator, 'share', { configurable: true, value: async (d) => console.log(d) })`.

## Mesurer la fluidité (sur téléphone)

Ajouter `&debug` à l'adresse d'une ville, par exemple
**https://theomaraval.github.io/jeu-canard-3d/?ville=delhi&debug** (Delhi est la plus
lourde). Un panneau « Mesure de fluidité » s'affiche (`app/src/mesure.js`, chargé seulement
dans ce cas). « Mesurer (12 s) » fait glisser la vue toute seule à trois zooms (vue
d'ensemble, moyen, de près) ; ne pas toucher l'écran pendant ce temps. Puis « Copier les
résultats » donne un texte à coller dans un message.

Pour chaque zoom :

| Mesure | Ce qu'elle dit | Bon signe |
|---|---|---|
| images/s | Médiane pendant le balayage, plafonnée par l'écran (60 ou 120 Hz) | 50 et plus |
| image lente | 95e centile de l'intervalle entre deux images | moins de 33 ms |
| saccades | Images de plus de 34 ms (au moins deux images d'écran perdues) | 0 à 2 |
| image calculée en | Temps pour dessiner une image, carte graphique comprise, vue fixe | moins de 16 ms |
| triangles, appels | Ce que dessine la dernière image (contours compris) | — |

Le panneau donne aussi la puce graphique, la taille de l'écran et la durée du chargement
de la ville (fichiers déjà en cache ou non). « Trop peu d'images pour conclure » : l'écran
s'est éteint ou l'onglet est passé en arrière-plan pendant la mesure ; recommencer.

**Mesures faites** (21/11/2026) :

| Appareil | Ville | images/s | saccades | image calculée | triangles par image |
|---|---|---|---|---|---|
| iPhone récent (« Apple GPU », écran 402 × 714 ×2, site publié) | Delhi | 59 aux trois zooms | 0 | 4 à 7 ms | 590 k à 810 k |
| Ordinateur, puce graphique intégrée AMD Radeon (390 × 800 ×2) | Delhi | 60 | 0 | 8 à 9 ms | 590 k à 830 k |
| Ordinateur, idem | Paris | (navigateur caché, non fiable) | — | 8 à 11 ms | 480 k à 630 k |

Conclusion : sur un iPhone récent le jeu est fluide, avec une marge de 2 à 4 fois (7 ms
au pire pour 16,7 ms disponibles). Le budget de triangles n'est donc pas un problème sur
ce type d'appareil. **Pas encore mesuré** : un Android d'entrée de gamme ou un téléphone de
plus de 4 ans, qui peuvent être 5 à 10 fois plus lents.

Lecture des chiffres :
- Safari arrondit le chronomètre à la milliseconde : « image calculée » y tombe en
  nombres entiers.
- Safari limite les animations à 60 images/s même sur un écran à 120 Hz : 59-60 est le
  maximum.
- « Chargement » compte les fichiers déjà en cache : la toute première visite est plus
  longue (environ 4,5 Mo à télécharger pour une ville).
- Le navigateur intégré de Claude, masqué, ne dessine presque plus d'images : seul
  « image calculée » y est fiable.

## Si c'est lent sur téléphone

Leviers, du plus simple au plus profond :

1. Dans le thème : baisser `style.foule`, `saynete_rue`, `nb_betes` (moins de passants et
   d'objets), puis régénérer.
2. Dans `app/src/scene.js` : relever `SEUIL_CONTOURS_PPM` (les traits noirs autour des
   objets doublent leur coût ; ils ne sont dessinés qu'à partir de ce zoom).
3. Dans `blender/build_kit.py` : alléger les personnages (360 triangles chacun).
4. Compresser les fichiers `.glb` (Meshopt ou Draco) : le site pèse environ 16 Mo, long à
   charger en 4G. Voir [06](06-pistes-d-amelioration.md).

## Problèmes connus et leurs causes

| Symptôme | Cause | Solution |
|---|---|---|
| « Impossible de lancer le jeu : …scenes.json est absent… » | `assets/scenes.json` supprimé | Ne jamais le supprimer ; le régénérer avec `tout_generer.sh` |
| Un JSON « illisible » alors que le fichier existe | Le serveur de dev renvoie la page d'accueil pour tout fichier absent | Le fichier n'est pas là où l'app le cherche |
| « Rejouer » ramène l'écran de fin | Corrigé : le rechargement déclenchait une sauvegarde (`pagehide`) | Si ça revient : vérifier le drapeau `rejoue` dans `main.js` |
| Une ville met des minutes à se mailler | Ne pas construire le décor avec `bmesh` (lent sur gros maillages) | Le décor passe par `citygen/maillage.py` |
| Matériaux noirs ou absents dans Blender 5 | Un matériau ou un monde créé par script a un arbre de nœuds vide | Voir `material()` dans `blender/citygen/geo.py` |
| Presque aucune cachette « à moitié visible » | Pas assez d'obstacles bas (murets, haies, étals, garde-corps) | Ajouter du décor qui masque partiellement, plutôt que d'élargir les plages de visibilité |
| Le cube et la caméra par défaut apparaissent dans un `.blend` | Script Blender lancé sans repartir d'une scène vide | Les scripts commencent par `read_factory_settings(use_empty=True)` |

Pièges propres au travail avec Claude (navigateur intégré, scripts dans Git Bash) : voir
`CLAUDE.md`.
