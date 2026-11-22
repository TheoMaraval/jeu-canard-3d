// Écran « Cacher mes canards » : on pose ses canards sur des cachettes garanties visibles,
// puis on envoie le lien du défi. Assemble scène, vue, gestes, aimant et « Mes défis ».
import { chargerScene } from './scene.js';
import { ecouterEntrees } from './entrees.js';
import { choisirCanard } from './picking.js';
import { aimanter, cachettesLibres, canardsDuDefi, chargerCachettes, idCachette } from './cachettes.js';
import { MAX_CANARDS, encoderDefi, lienCacher, lienDefi, nettoyerPrenom, texteInvitationDefi } from './defi.js';
import { dernierPrenom, enregistrerDefi, nouvelId, retenirPrenom, trouverDefi } from './mesdefis.js';
import { borner, creerVue, deplacer, estRevele, projeter, zoomer } from './vue.js';
import { decouperNom, lienJeu, partagerAvecRetour } from './partage.js';
import {
  AIDE_CACHER, activerPartage, afficherAide, afficherBref, afficherChargement, afficherCompteur, afficherHudCacher,
  celebrer, demanderPrenom,
} from './hud.js';

const RAISONS = {
  zoom: 'Zoome davantage pour cacher un canard.',
  aucune: 'Pas de cachette ici : vise un des petits ronds.',
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
  afficherChargement(true, `Chargement de ${ville}…`);
  let lot;
  try {
    lot = await chargerCachettes(info.id);
  } catch {
    return { raison: 'pas-pret', contexte: { ville } };
  }

  // un défi fait pour une autre version de la ville ne se modifie plus : on en commence un neuf
  const existant = idDefi ? trouverDefi(localStorage, idDefi) : null;
  const valable = existant && existant.ville === info.id
    && existant.version === lot.version && existant.empreinte === lot.empreinte
    && existant.numeros.length <= MAX_CANARDS
    && new Set(existant.numeros).size === existant.numeros.length
    && existant.numeros.every((n) => n < lot.cachettes.length);
  const defi = valable ? { ...existant } : {
    id: nouvelId(),
    ville: info.id,
    version: lot.version,
    empreinte: lot.empreinte,
    prenom: dernierPrenom(localStorage),
    numeros: [],
    cree: Date.now(),
  };
  // l'identifiant dans l'adresse : un rechargement (fréquent sur iOS au retour de la messagerie) rouvre le même brouillon
  history.replaceState(null, '', lienCacher(location.href, info.id, defi.id));
  const scene = await chargerScene(canvas, info, {
    canards: canardsDuDefi(lot.cachettes, defi.numeros), capacite: MAX_CANARDS,
  });
  afficherChargement(false);
  scene.creerReperes(lot.cachettes.map((c) => c.centre));
  if (idDefi && existant && !valable) afficherBref(`Ce défi n’est plus valable pour ${ville} : on en commence un nouveau.`);

  const ecran = () => ({ w: canvas.clientWidth, h: canvas.clientHeight });
  let vue = creerVue(ecran(), scene.limites);
  const revele = () => estRevele(vue, scene.gabarit);
  const rafraichir = () => {
    vue = borner(vue, ecran(), scene.limites);
    scene.appliquerVue(vue, ecran(), revele());
    scene.afficherReperes(revele());
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
    scene.majReperes(cachettesLibres(lot.cachettes, numeros, lot.distanceMin));
    enregistrerDefi(localStorage, defi);
    majCompteur();
  };

  // après la fermeture du panneau, un double tap sur « Envoyer » / « Annuler » ne doit pas retomber sur la scène
  let bloqueJusqua = 0;

  const partager = async () => {
    if (!defi.numeros.length) return;
    const prenom = await demanderPrenom(defi.prenom);
    bloqueJusqua = performance.now() + 400;
    if (prenom === null) return; // panneau fermé
    defi.prenom = nettoyerPrenom(prenom);
    retenirPrenom(localStorage, defi.prenom);
    enregistrerDefi(localStorage, defi);
    let url;
    try {
      url = lienDefi(location.href, info.id, encoderDefi(defi));
    } catch {
      afficherBref('Impossible de créer le lien de ce défi.');
      return;
    }
    partagerAvecRetour({
      texte: texteInvitationDefi({ prenom: defi.prenom, n: defi.numeros.length, ville }),
      url,
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
      if (performance.now() < bloqueJusqua) return;
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
  scene.majReperes(cachettesLibres(lot.cachettes, defi.numeros, lot.distanceMin));
  rafraichir();

  // pour les vérifications depuis la console (voir docs/05)
  window.jeu = { vue: () => vue, axes: scene.axes, cachettes: lot.cachettes, defi: () => ({ ...defi }) };
  return null;
}
