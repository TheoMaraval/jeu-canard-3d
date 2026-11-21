// Progression par ville et par version de scène, dans un stockage de type localStorage.
// Une sauvegarde illisible, ou d'une autre version, est ignorée : on repart d'une partie neuve.

export const cle = (ville, version) => `jeu-canard-3d:${ville}:v${version}`;

export function charger(stockage, ville, version) {
  try {
    const d = JSON.parse(stockage.getItem(cle(ville, version)));
    if (!d || !Array.isArray(d.trouves) || typeof d.taps !== 'number') return null;
    return { trouves: d.trouves, taps: d.taps, ecouleMs: Number(d.ecouleMs) || 0 };
  } catch {
    return null;
  }
}

export function enregistrer(stockage, ville, version, donnees) {
  try {
    stockage.setItem(cle(ville, version), JSON.stringify(donnees));
  } catch {
    // stockage plein ou bloqué (navigation privée) : la partie continue sans sauvegarde
  }
}

export function effacer(stockage, ville, version) {
  try {
    stockage.removeItem(cle(ville, version));
  } catch {
    // idem
  }
}

// ----------------------------------------------------------------------- record
// Le meilleur résultat d'une ville terminée, gardé à part de la partie : « Rejouer » efface
// la partie, pas le record. Par version, comme la partie (autre version = autres canards).

export const cleRecord = (ville, version) => `${cle(ville, version)}:record`;

/** Le meilleur de deux résultats {ecouleMs, taps} : le plus rapide, puis le moins de taps. */
export function meilleur(a, b) {
  if (!a || !b) return a ?? b ?? null;
  if (b.ecouleMs !== a.ecouleMs) return b.ecouleMs < a.ecouleMs ? b : a;
  return b.taps < a.taps ? b : a;
}

export function chargerRecord(stockage, ville, version) {
  try {
    const d = JSON.parse(stockage.getItem(cleRecord(ville, version)));
    if (!d || typeof d.ecouleMs !== 'number' || typeof d.taps !== 'number') return null;
    return { ecouleMs: d.ecouleMs, taps: d.taps };
  } catch {
    return null;
  }
}

/**
 * Note une partie terminée et garde le meilleur résultat.
 * @returns {{record, ancien}} le record après cette partie, et celui d'avant (ou null)
 */
export function retenirRecord(stockage, ville, version, { ecouleMs, taps }) {
  const ancien = chargerRecord(stockage, ville, version);
  const record = meilleur(ancien, { ecouleMs, taps });
  try {
    stockage.setItem(cleRecord(ville, version), JSON.stringify(record));
  } catch {
    // stockage plein ou bloqué : le record ne vaut que pour cette visite
  }
  return { record, ancien };
}
