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
- Dans une session Claude ouverte depuis `jeuFind`, le serveur se lance avec la
  configuration `canard-3d` de `jeuFind/.claude/launch.json`.

## Les tests

```bash
python -m unittest discover -s blender/tests -t blender   # 41 tests du générateur, sans Blender
cd app && npm test                                        # 32 tests de l'app
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
| `jeu.vue()` | Position et zoom (`ppm` = pixels par mètre) |
| `jeu.partie()` | Canards trouvés, taps, temps |
| `jeu.canards` | Les 30 canards, avec leur lieu (`vitre`, `toit`…) |

Pour remettre une ville à zéro : console, puis
`localStorage.removeItem('jeu-canard-3d:paris:v3')` et recharger.

## Si c'est lent sur téléphone

Rien n'a encore été mesuré sur téléphone. Les scènes affichent 400 000 à 570 000 triangles
de décor, au-dessus de la cible de 500 000. Leviers, du plus simple au plus profond :

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
