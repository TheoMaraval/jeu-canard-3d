# Jeu Canard 3D

Un jeu d'observation façon « scène fourmillante » : trouve les **30 canards en plastique
jaunes** cachés dans un quartier dessiné, plein de monde et de situations loufoques.
Quatre villes : Paris, New York, Lille, Delhi.

**Jouer : https://theomaraval.github.io/jeu-canard-3d/** (téléphone, tablette, ordinateur)

- Déplace la vue avec un doigt, zoome en pinçant (molette sur ordinateur).
- À zoom moyen, canards et leurres jaunes se ressemblent tous. Zoome : seul le canard a un
  bec orange et un œil noir. Certains sont derrière des vitres.
- Touche un canard pour le trouver. Pas de pénalité pour un tap raté.
- La progression est sauvegardée sur l'appareil, ville par ville.

## Documentation

Tout est dans [docs/](docs/README.md) : comprendre le projet, **ajouter une ville**, régler la
difficulté, étendre le générateur, publier, et les pistes pour la suite (mode « cacher ses
canards », création de mondes).

## Développement

```bash
cd app && npm install
npm run dev      # http://localhost:5173
npm test
```

Les décors sont générés par Blender 5.3 (`bash blender/tout_generer.sh`). L'architecture, les
règles de jeu et les réglages de difficulté sont décrits dans [CLAUDE.md](CLAUDE.md) et dans
`docs/superpowers/specs/`.

Les fiches de `.claude/skills/` viennent de
[arjun988/blender-skills](https://github.com/arjun988/blender-skills) (licence MIT, copiée
dans `.claude/skills/LICENSE-blender-skills`).
