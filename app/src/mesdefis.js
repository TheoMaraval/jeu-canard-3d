// « Mes défis » : les défis créés sur cet appareil, et le dernier prénom utilisé.
// Le stockage (de type localStorage) est passé en paramètre ; bloqué, il ne casse rien.
//
// Un défi : {id, ville, version, empreinte, prenom, numeros, cree (ms)}.

export const CLE_DEFIS = 'jeu-canard-3d:mes-defis';
export const CLE_PRENOM = 'jeu-canard-3d:prenom';

/** Progression d'un défi reçu, rangée à part de la partie normale. */
export const cleDefiRecu = (code) => `jeu-canard-3d:defi:${code}`;

const estDefi = (d) => Boolean(d) && typeof d.id === 'string' && typeof d.ville === 'string'
  && Number.isInteger(d.version) && typeof d.empreinte === 'string'
  && Array.isArray(d.numeros) && d.numeros.every(Number.isInteger) && typeof d.cree === 'number';

export function listerDefis(stockage) {
  try {
    const liste = JSON.parse(stockage.getItem(CLE_DEFIS));
    if (!Array.isArray(liste)) return [];
    return liste.filter(estDefi).map((d) => ({ ...d, prenom: typeof d.prenom === 'string' ? d.prenom : '' }));
  } catch {
    return [];
  }
}

function ecrire(stockage, liste) {
  try {
    stockage.setItem(CLE_DEFIS, JSON.stringify(liste));
  } catch {
    // stockage plein ou bloqué : le défi marche quand même, il n'est simplement pas gardé
  }
}

export const trouverDefi = (stockage, id) => listerDefis(stockage).find((d) => d.id === id) ?? null;

/** Ajoute un défi en tête, ou le remplace à sa place ; sans canard, il est retiré. */
export function enregistrerDefi(stockage, defi) {
  const liste = listerDefis(stockage);
  const i = liste.findIndex((d) => d.id === defi.id);
  if (!defi.numeros.length) {
    if (i >= 0) liste.splice(i, 1);
  } else if (i >= 0) {
    liste[i] = defi;
  } else {
    liste.unshift(defi);
  }
  ecrire(stockage, liste);
  return liste;
}

export function supprimerDefi(stockage, id) {
  ecrire(stockage, listerDefis(stockage).filter((d) => d.id !== id));
}

export const nouvelId = (maintenant = Date.now(), alea = Math.random) =>
  `${maintenant.toString(36)}${Math.floor(alea() * 1296).toString(36).padStart(2, '0')}`;

export function dernierPrenom(stockage) {
  try {
    return stockage.getItem(CLE_PRENOM) ?? '';
  } catch {
    return '';
  }
}

export function retenirPrenom(stockage, prenom) {
  try {
    stockage.setItem(CLE_PRENOM, prenom);
  } catch {
    // idem
  }
}

/** Le défi correspond-il encore à sa ville (même version, mêmes cachettes) ? */
// « Mes défis » garde la `version` entière (jamais l'octet décodé d'un lien) : d'où la comparaison directe.
export const estValable = (defi, scenes) => scenes.some(
  (s) => s.id === defi.ville && s.version === defi.version && s.empreinte === defi.empreinte,
);

/** « 7 canards · 21/11 » */
export function detailDefi(defi) {
  const n = defi.numeros.length;
  const date = new Date(defi.cree);
  const jj = String(date.getDate()).padStart(2, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  return `${n} canard${n > 1 ? 's' : ''} · ${jj}/${mm}`;
}
