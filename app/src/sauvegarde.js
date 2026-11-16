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
