// Partage du score, invitations et résumés de progression. Fonctions pures, sauf `partager`
// qui reçoit le navigateur en paramètre (testable avec un faux).
import { afficherBref, chrono } from './hud.js';
import { meilleur } from './sauvegarde.js';

/** « Paris — Grands Boulevards » → { ville: « Paris », quartier: « Grands Boulevards » }. */
export function decouperNom(nom) {
  const [ville, ...reste] = nom.split(' — ');
  return { ville, quartier: reste.join(' — ') };
}

/** Lien vers le jeu, ou vers une ville précise : sans paramètres ni ancre parasites. */
export function lienJeu(adresse, ville = null) {
  const url = new URL(adresse);
  url.search = '';
  url.hash = '';
  if (ville) url.searchParams.set('ville', ville);
  return url.toString();
}

export function texteScore({ nom, trouves, total, ecouleMs, taps, precision }) {
  const { ville } = decouperNom(nom);
  if (trouves >= total) {
    return `🦆 J'ai trouvé les ${total} canards cachés à ${ville} en ${chrono(ecouleMs)} `
      + `(${taps} taps, ${Math.round(precision * 100)} % de précision). Tu fais mieux ?`;
  }
  if (trouves === 0) return `🦆 Je cherche ${total} canards cachés à ${ville}. Tu m'aides ?`;
  return `🦆 J'ai déjà trouvé ${trouves} canard${trouves > 1 ? 's' : ''} sur ${total} à ${ville} `
    + `(${chrono(ecouleMs)}). Viens chercher les autres !`;
}

export const TEXTE_INVITATION = '🦆 30 canards en plastique se cachent dans une ville pleine de monde. '
  + 'Zoome, cherche le bec orange et l\'œil noir… Tu les trouves ? Gratuit, sur téléphone ou ordinateur.';

/** Ligne d'état d'une ville sur l'écran d'accueil, d'après sa sauvegarde. */
export function resumeVille(sauvegarde, total) {
  if (!sauvegarde || (!sauvegarde.trouves.length && !sauvegarde.taps)) return 'Nouvelle partie';
  const n = sauvegarde.trouves.length;
  if (n >= total) return `✓ Terminée en ${chrono(sauvegarde.ecouleMs)}`;
  return `${n} / ${total} trouvé${n > 1 ? 's' : ''} · ${chrono(sauvegarde.ecouleMs)}`;
}

/**
 * Ligne « record » de l'écran de fin : la partie comparée au record d'avant.
 * `null` s'il n'y a rien à dire (première partie finie, ou partie finie rouverte).
 */
export function texteRecord(partie, ancien) {
  if (!ancien) return null;
  if (partie.ecouleMs === ancien.ecouleMs && partie.taps === ancien.taps) return null;
  if (meilleur(ancien, partie) === partie) {
    return { texte: `Nouveau record ! L’ancien : ${chrono(ancien.ecouleMs)}`, nouveau: true };
  }
  return { texte: `Ton record : ${chrono(ancien.ecouleMs)}`, nouveau: false };
}

/** Part des canards trouvés dans une ville, entre 0 et 1 (barre de progression de l'accueil). */
export function progression(sauvegarde, total) {
  if (!sauvegarde || !total) return 0;
  return Math.min(1, sauvegarde.trouves.length / total);
}

/** Titre de l'écran de fin selon la précision (canards trouvés / taps). */
export function titreFin(precision) {
  if (precision >= 0.7) return { titre: 'Œil de lynx !', etoiles: 3 };
  if (precision >= 0.4) return { titre: 'Fin limier !', etoiles: 2 };
  return { titre: 'Chasseur tenace !', etoiles: 1 };
}

/**
 * Partage natif (téléphone) ou copie dans le presse-papiers (ordinateur).
 * @returns {'partage'|'copie'|'annule'|'impossible'}
 */
export async function partager({ titre, texte, url }, nav = globalThis.navigator) {
  if (nav?.share) {
    try {
      await nav.share({ title: titre, text: texte, url });
      return 'partage';
    } catch (e) {
      if (e?.name === 'AbortError') return 'annule'; // le joueur a fermé la feuille de partage
      // autre échec (permission refusée…) : on tente la copie
    }
  }
  if (nav?.clipboard?.writeText) {
    try {
      await nav.clipboard.writeText(`${texte}\n${url}`);
      return 'copie';
    } catch {
      return 'impossible';
    }
  }
  return 'impossible';
}

export const TITRE = 'Où sont les canards ?';

/** Partage, avec un retour visible quand le lien a été copié plutôt que partagé. */
export async function partagerAvecRetour(contenu) {
  const issue = await partager({ titre: TITRE, ...contenu });
  if (issue === 'copie') afficherBref('Message et lien copiés : colle-les dans un SMS ou une messagerie.');
  if (issue === 'impossible') afficherBref(`Copie impossible ici. Le lien : ${contenu.url}`, 6000);
}

/** Sous-titre de l'écran de fin. */
export const sousTitreFin = (n) => (n > 1 ? `Les ${n} canards sont trouvés` : 'Le canard est trouvé');
