// Assemble l'accueil, la scène, la vue, les gestes, la partie, la sauvegarde et le partage.
//
// Sans `?ville=` dans l'adresse : écran d'accueil (choix de la ville). Avec : la partie.
// Passer de l'un à l'autre recharge la page : une seule scène 3D par page, rien à nettoyer.
import { chargerScene } from './scene.js';
import { ecouterEntrees } from './entrees.js';
import { creerPartie, precision, serialiser, taper, terminee } from './partie.js';
import { charger, chargerRecord, effacer, enregistrer, meilleur, retenirRecord } from './sauvegarde.js';
import { choisirCanard } from './picking.js';
import { creerSon } from './son.js';
import { borner, creerVue, deplacer, estRevele, projeter, zoomer } from './vue.js';
import '@fontsource/fredoka/600.css';
import '@fontsource/fredoka/700.css';
import '@fontsource/nunito/400.css';
import '@fontsource/nunito/700.css';
import '@fontsource/nunito/800.css';
import {
  TEXTE_INVITATION, decouperNom, lienJeu, partager, progression, resumeVille, texteRecord, texteScore, titreFin,
} from './partage.js';
import {
  afficherAccueil, afficherAide, afficherBref, afficherChargement, afficherCompteur, afficherFin, afficherHud,
  afficherMessage, afficherSon, afficherStats, celebrer, chrono,
} from './hud.js';

const canvas = document.getElementById('scene');
const TITRE = 'Où sont les canards ?';

async function chargerIndex() {
  const r = await fetch('scenes.json');
  if (!r.ok) throw new Error('scenes.json introuvable : lancer le pipeline Blender.');
  // Vite renvoie index.html pour un fichier absent : un JSON illisible veut dire « pas d'index »
  const scenes = await r.json().catch(() => {
    throw new Error('scenes.json est absent : lancer blender/tout_generer.sh.');
  });
  if (!scenes.length) throw new Error('scenes.json ne liste aucune ville.');
  return scenes;
}

const allerA = (ville) => { location.href = lienJeu(location.href, ville); };

/** Partage, avec un retour visible quand le lien a été copié plutôt que partagé. */
async function partagerAvecRetour(contenu) {
  const issue = await partager({ titre: TITRE, ...contenu });
  if (issue === 'copie') afficherBref('Message et lien copiés : colle-les dans un SMS ou une messagerie.');
  if (issue === 'impossible') afficherBref(`Copie impossible ici. Le lien : ${contenu.url}`, 6000);
}

function accueil(scenes) {
  const villes = scenes.map((s) => {
    const total = s.canards ?? 30;
    const sauvegarde = charger(localStorage, s.id, s.version);
    const fini = Boolean(sauvegarde && sauvegarde.trouves.length >= total);
    // une partie finie avant l'arrivée des records compte aussi
    const record = meilleur(chargerRecord(localStorage, s.id, s.version), fini ? sauvegarde : null);
    return {
      id: s.id,
      embleme: s.embleme ?? '🏙️',
      couleur: s.couleur ?? '#3f6fd8',
      ...decouperNom(s.nom),
      etat: resumeVille(sauvegarde, total),
      avance: progression(sauvegarde, total),
      fini,
      record: record ? chrono(record.ecouleMs) : null,
    };
  });
  afficherAccueil(villes, {
    choisir: allerA,
    inviter: () => partagerAvecRetour({ texte: TEXTE_INVITATION, url: lienJeu(location.href) }),
  });
}

async function jouer(info) {
  afficherChargement(true, `Chargement de ${decouperNom(info.nom).ville}…`);
  const scene = await chargerScene(canvas, info);
  afficherChargement(false);

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
    enregistrer(localStorage, info.id, info.version, serialiser(partie));
  };
  document.addEventListener('visibilitychange', sauver);
  window.addEventListener('pagehide', sauver);

  const partagerPartie = () => {
    horloge();
    partagerAvecRetour({
      texte: texteScore({ nom: info.nom, trouves: partie.trouves.size, total: partie.ids.length, ...resume() }),
      url: lienJeu(location.href, info.id),
    });
  };

  const finir = () => {
    clearInterval(minuteur);
    majStats(); // dernière valeur exacte, figée
    // le record survit à « Rejouer », qui n'efface que la partie
    const { ancien } = retenirRecord(localStorage, info.id, info.version, resume());
    afficherFin(resume(), titreFin(precision(partie)), texteRecord(resume(), ancien), {
      rejouer: () => {
        // location.reload() déclenche `pagehide`, donc `sauver` : sans ce drapeau, la partie
        // terminée serait réenregistrée juste après l'effacement et l'écran de fin reviendrait.
        rejoue = true;
        effacer(localStorage, info.id, info.version);
        location.reload();
      },
      partager: partagerPartie,
      autreVille: () => allerA(null),
    });
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
}

async function demarrer() {
  const scenes = await chargerIndex();
  const demandee = new URLSearchParams(location.search).get('ville');
  const info = scenes.find((s) => s.id === demandee);
  // pas de ville, ou une ville inconnue (vieux lien) : on montre l'accueil
  if (info) await jouer(info);
  else accueil(scenes);
}

demarrer().catch((erreur) => {
  console.error(erreur);
  afficherChargement(false);
  afficherMessage(`Impossible de lancer le jeu : ${erreur.message}`, { erreur: true });
});
