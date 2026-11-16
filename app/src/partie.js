// État d'une partie. Fonctions pures : aucune dépendance au rendu ni au stockage.

/** @param {string[]} ids identifiants des canards de la scène */
export function creerPartie(ids, sauvegarde = null) {
  const connus = new Set(ids);
  return {
    ids: [...ids],
    trouves: new Set((sauvegarde?.trouves ?? []).filter((id) => connus.has(id))),
    taps: sauvegarde?.taps ?? 0,
    ecouleMs: sauvegarde?.ecouleMs ?? 0,
  };
}

/** Un tap : `id` est le canard touché, ou null (leurre, vide). Jamais de pénalité. */
export function taper(partie, id) {
  const trouve = id !== null && partie.ids.includes(id) && !partie.trouves.has(id);
  const trouves = new Set(partie.trouves);
  if (trouve) trouves.add(id);
  return { partie: { ...partie, trouves, taps: partie.taps + 1 }, trouve };
}

export const terminee = (partie) => partie.trouves.size === partie.ids.length;

/** Taps réussis / taps totaux. */
export const precision = (partie) => (partie.taps ? partie.trouves.size / partie.taps : 0);

export const serialiser = (partie) => ({
  trouves: [...partie.trouves], taps: partie.taps, ecouleMs: partie.ecouleMs,
});
