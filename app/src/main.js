// Assemble la scène, la vue, les gestes, la partie et la sauvegarde.
import { chargerScene } from './scene.js';
import { ecouterEntrees } from './entrees.js';
import { creerPartie, precision, serialiser, taper, terminee } from './partie.js';
import { charger, effacer, enregistrer } from './sauvegarde.js';
import { choisirCanard } from './picking.js';
import { borner, creerVue, deplacer, estRevele, projeter, zoomer } from './vue.js';
import {
  afficherAide, afficherCompteur, afficherFin, afficherMessage, afficherStats, afficherVilles,
} from './hud.js';

const canvas = document.getElementById('scene');

async function choisirVille() {
  const r = await fetch('scenes.json');
  if (!r.ok) throw new Error('scenes.json introuvable : lancer le pipeline Blender.');
  // Vite renvoie index.html pour un fichier absent : un JSON illisible veut dire « pas d'index »
  const scenes = await r.json().catch(() => {
    throw new Error('scenes.json est absent : lancer blender/tout_generer.sh.');
  });
  if (!scenes.length) throw new Error('scenes.json ne liste aucune ville.');
  const demandee = new URLSearchParams(location.search).get('ville');
  const info = scenes.find((s) => s.id === demandee) ?? scenes[0];
  afficherVilles(scenes, info.id, (id) => {
    location.search = `?ville=${encodeURIComponent(id)}`;
  });
  return info;
}

async function demarrer() {
  afficherMessage('Chargement du quartier…');
  const info = await choisirVille();
  const scene = await chargerScene(canvas, info);
  afficherMessage('');

  let partie = creerPartie(scene.canards.map((c) => c.id), charger(localStorage, info.id, info.version));
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
  // temps, taps et précision en direct : le chrono avance deux fois par seconde
  const majStats = () => {
    horloge();
    afficherStats({ ecouleMs: partie.ecouleMs, taps: partie.taps, precision: precision(partie) });
  };
  const minuteur = setInterval(majStats, 500);

  let rejoue = false; // « Rejouer » : plus aucune sauvegarde, sinon la partie finie est réécrite
  const sauver = () => {
    if (rejoue) return;
    horloge();
    enregistrer(localStorage, info.id, info.version, serialiser(partie));
  };
  document.addEventListener('visibilitychange', sauver);
  window.addEventListener('pagehide', sauver);

  const finir = () => {
    clearInterval(minuteur);
    majStats(); // dernière valeur exacte, figée
    afficherFin(
      { ecouleMs: partie.ecouleMs, taps: partie.taps, precision: precision(partie) },
      () => {
        // location.reload() déclenche `pagehide`, donc `sauver` : sans ce drapeau, la partie
        // terminée serait réenregistrée juste après l'effacement et l'écran de fin reviendrait.
        rejoue = true;
        effacer(localStorage, info.id, info.version);
        location.reload();
      },
    );
  };

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
      }
      sauver();
      majStats(); // le tap compte tout de suite, sans attendre le prochain tic du chrono
      if (terminee(partie)) finir();
    },
  });

  window.addEventListener('resize', rafraichir);
  afficherCompteur(partie.trouves.size, partie.ids.length);
  majStats();
  rafraichir();
  if (terminee(partie)) finir();

  // pour le diagnostic depuis la console : window.jeu.stats()
  window.jeu = { stats: scene.stats, vue: () => vue, partie: () => serialiser(partie), canards: scene.canards, axes: scene.axes };
}

demarrer().catch((erreur) => {
  console.error(erreur);
  afficherMessage(`Impossible de lancer le jeu : ${erreur.message}`);
});
