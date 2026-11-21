# Où sont les canards ?

Un jeu d'observation façon « scène fourmillante » : trouve les **30 canards en plastique
jaunes** cachés dans un quartier dessiné, plein de monde et de situations loufoques.
Quatre villes : Paris, New York, Lille, Delhi.

**Jouer : https://theomaraval.github.io/jeu-canard-3d/** (téléphone, tablette, ordinateur)

- Choisis ta ville sur l'écran d'accueil.
- Déplace la vue avec un doigt, zoome en pinçant (molette sur ordinateur).
- À zoom moyen, canards et leurres jaunes se ressemblent tous. Zoome : seul le canard a un
  bec orange et un œil noir. Certains sont derrière des vitres.
- Touche un canard pour le trouver : « coin coin ! », et une musique quand on les a tous. Pas de pénalité pour un tap raté.
- Temps, taps et précision s'affichent en direct ; partage ton score ou invite quelqu'un.
- La progression est sauvegardée sur l'appareil, ville par ville. Pas de compte, pas de pub.

## Documentation

Tout est dans [docs/](docs/README.md) : comprendre le projet, **ajouter une ville**, régler la
difficulté, étendre le générateur, tester et publier, et les pistes pour la suite (mode
« cacher ses canards », création de mondes).

## Développement

```bash
cd app && npm install
npm run dev      # http://localhost:5173
npm test
```

Les villes sont générées par Blender 5.3 (`bash blender/tout_generer.sh`). Chaque envoi sur
`main` republie le site automatiquement (GitHub Pages).

Les fiches de `.claude/skills/` viennent de
[arjun988/blender-skills](https://github.com/arjun988/blender-skills) (licence MIT, copiée
dans `.claude/skills/LICENSE-blender-skills`). Les polices Fredoka et Nunito (licence SIL
Open Font) sont embarquées via `@fontsource`.
