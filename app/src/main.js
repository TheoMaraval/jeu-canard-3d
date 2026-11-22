// Assemble l'accueil, la scène, la vue, les gestes, la partie, la sauvegarde et le partage.
//
// Sans `?ville=` dans l'adresse : écran d'accueil (choix de la ville). Avec : la partie.
// Passer de l'un à l'autre recharge la page : une seule scène 3D par page, rien à nettoyer.
import { chargerScene } from './scene.js';
import { cacher } from './cacher.js';
import { ecouterEntrees } from './entrees.js';
import { creerPartie, precision, serialiser, taper, terminee } from './partie.js';
import {
  chargerCle, chargerRecord, cle, effacerCle, enregistrerCle, meilleur, retenirRecord,
} from './sauvegarde.js';
import { choisirCanard } from './picking.js';
import { creerSon } from './son.js';
import { canardsDuDefi, chargerCachettes } from './cachettes.js';
import {
  decoderDefi, encoderDefi, libelleRenvoi, lienCacher, lienDefi, messageRejet, texteInvitationDefi, texteTempsDefi,
  titreDefi, titreFinDefi, verifierDefi,
} from './defi.js';
import { cleDefiRecu, detailDefi, estValable, listerDefis, supprimerDefi, trouverDefi } from './mesdefis.js';
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
  afficherMesDefis, afficherMessage, afficherSon, afficherStats, celebrer, chrono,
} from './hud.js';

const canvas = document.getElementById('scene');

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
    cacher: (ville) => { location.href = lienCacher(location.href, ville); },
  });
  montrerMesDefis(scenes);
}

/** Section « Mes défis » : renvoyer, modifier ou supprimer un défi créé sur cet appareil. */
function montrerMesDefis(scenes) {
  const parId = new Map(scenes.map((s) => [s.id, s]));
  const nomVille = (id) => decouperNom(parId.get(id).nom).ville;
  // un brouillon sans canard n'a rien à envoyer (enregistrerDefi les retire déjà, mais on ne s'y fie pas)
  const defis = listerDefis(localStorage).filter((d) => parId.has(d.ville) && d.numeros.length > 0);
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
      if (!d) return;
      let url;
      try {
        url = lienDefi(location.href, d.ville, encoderDefi(d));
      } catch {
        afficherBref('Impossible de créer le lien de ce défi.');
        return;
      }
      partagerAvecRetour({ texte: texteInvitationDefi({ prenom: d.prenom, n: d.numeros.length, ville: nomVille(d.ville) }), url });
    },
    modifier: (id) => {
      const d = trouverDefi(localStorage, id);
      if (d) location.href = lienCacher(location.href, d.ville, id);
    },
    supprimer: (id) => {
      if (!window.confirm('Supprimer ce défi ? Les liens déjà envoyés continueront de marcher.')) return;
      supprimerDefi(localStorage, id);
      montrerMesDefis(scenes);
    },
  });
}

/**
 * Lit le défi du lien et le vérifie contre les cachettes de la ville.
 * @returns {{ok: true, code, defi, canards} | {ok: false, raison, contexte}}
 */
async function preparerDefi(info, code) {
  const { ville } = decouperNom(info.nom);
  const lu = decoderDefi(code);
  if (!lu.ok) return { ok: false, raison: lu.raison, contexte: { ville } };
  const contexte = { ville, prenom: lu.defi.prenom };
  let lot;
  try {
    lot = await chargerCachettes(info.id);
  } catch {
    return { ok: false, raison: 'pas-pret', contexte };
  }
  const raison = verifierDefi(lu.defi, { version: lot.version, empreinte: lot.empreinte, nombre: lot.cachettes.length });
  if (raison) return { ok: false, raison, contexte };
  return { ok: true, code, defi: lu.defi, canards: canardsDuDefi(lot.cachettes, lu.defi.numeros) };
}

/** Retour à l'accueil avec un message, quand un défi (ou le mode « Cacher ») est impossible. */
function refuser(scenes, { raison, contexte }) {
  afficherChargement(false);
  history.replaceState(null, '', lienJeu(location.href));
  accueil(scenes);
  afficherBref(messageRejet(raison, contexte), 8000);
}

/**
 * Une partie : la ville normale, ou un défi reçu.
 * @param recu null, ou {code, defi: {prenom, numeros…}, canards} (voir preparerDefi)
 */
async function jouer(info, recu = null) {
  const { ville } = decouperNom(info.nom);
  afficherChargement(true, recu ? `${titreDefi(recu.defi.prenom)} · ${ville}…` : `Chargement de ${ville}…`);
  const t0 = performance.now();
  const scene = await chargerScene(canvas, info, recu ? { canards: recu.canards } : {});
  const chargementMs = performance.now() - t0;
  afficherChargement(false);

  // un défi a sa propre progression : la partie normale et le record de la ville n'y sont pour rien
  const cleSauvegarde = recu ? cleDefiRecu(recu.code) : cle(info.id, info.version);

  let partie = creerPartie(scene.canards.map((c) => c.id), chargerCle(localStorage, cleSauvegarde));
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
    enregistrerCle(localStorage, cleSauvegarde, serialiser(partie));
  };
  document.addEventListener('visibilitychange', sauver);
  window.addEventListener('pagehide', sauver);

  const texteAPartager = () => {
    const n = partie.ids.length;
    if (!recu) return texteScore({ nom: info.nom, trouves: partie.trouves.size, total: n, ...resume() });
    const { prenom } = recu.defi;
    return terminee(partie)
      ? texteTempsDefi({ prenom, n, ville, ecouleMs: partie.ecouleMs })
      : texteInvitationDefi({ prenom, n, ville }); // en cours : on fait suivre le même défi
  };
  const partagerPartie = () => {
    horloge();
    partagerAvecRetour({
      texte: texteAPartager(),
      url: recu ? lienDefi(location.href, info.id, recu.code) : lienJeu(location.href, info.id),
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
        effacerCle(localStorage, cleSauvegarde);
        location.reload();
      },
      partager: partagerPartie,
      autreVille: () => allerA(null),
    };
    const sousTitre = sousTitreFin(partie.ids.length);
    if (recu) {
      afficherFin(resume(), { ...medaille, titre: titreFinDefi(recu.defi.prenom) }, null, {
        ...actions,
        cacherAMonTour: () => { location.href = lienCacher(location.href, info.id); },
      }, { sousTitre, libellePartager: libelleRenvoi(recu.defi.prenom) });
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
  window.jeu = { stats: scene.stats, vue: () => vue, partie: () => serialiser(partie), get canards() { return scene.canards; }, axes: scene.axes };

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

async function demarrer() {
  const scenes = await chargerIndex();
  const params = new URLSearchParams(location.search);
  const info = scenes.find((s) => s.id === params.get('ville'));
  // pas de ville, ou une ville inconnue (vieux lien) : on montre l'accueil
  if (!info) {
    accueil(scenes);
    return;
  }
  if (params.has('cacher')) {
    const refus = await cacher(canvas, info, params.get('cacher'));
    if (refus) refuser(scenes, refus);
    return;
  }
  if (!params.has('defi')) {
    await jouer(info);
    return;
  }
  afficherChargement(true, 'Préparation du défi…');
  const prepare = await preparerDefi(info, params.get('defi'));
  if (!prepare.ok) refuser(scenes, prepare);
  else await jouer(info, prepare);
}

demarrer().catch((erreur) => {
  console.error(erreur);
  afficherChargement(false);
  afficherMessage(`Impossible de lancer le jeu : ${erreur.message}`, { erreur: true });
});
