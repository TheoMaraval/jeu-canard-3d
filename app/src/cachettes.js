// Cachettes du mode défi (cachettes.json) et l'aimant qui pose un canard. Géométrie pure,
// sauf `chargerCachettes` qui reçoit `fetch` en paramètre (testable avec un faux).
import { MAX_CANARDS } from './defi.js';

export const RAYON_AIMANT_PX = 40;
const HAUTEUR_CENTRE = 0.22; // comme scene.js : centre du canard au-dessus de son appui, à l'échelle 1

export const idCachette = (numero) => `cachette-${numero}`;

/**
 * Lit scenes/<ville>/cachettes.json. Lève Error('pas-pret') s'il manque : Vite renvoie
 * alors index.html, illisible en JSON.
 */
export async function chargerCachettes(ville, lire = globalThis.fetch) {
  let d = null;
  try {
    const r = await lire(`scenes/${ville}/cachettes.json`);
    if (r.ok) d = await r.json();
  } catch {
    d = null;
  }
  if (!d || !Array.isArray(d.cachettes)) throw new Error('pas-pret');
  const k = d.echelle ?? 1;
  return {
    version: d.version,
    empreinte: d.empreinte,
    distanceMin: d.distance_min_canards,
    cachettes: d.cachettes.map(([x, y, z, rotation, visibilite, lieu], numero) => ({
      numero, position: [x, y, z], rotation, visibilite, lieu, centre: [x, y + HAUTEUR_CENTRE * k, z],
    })),
  };
}

/** Les canards d'un défi, au format attendu par la scène : un par numéro de cachette. */
export const canardsDuDefi = (cachettes, numeros) => numeros.map((n) => ({
  id: idCachette(n), position: cachettes[n].position, rotation: cachettes[n].rotation, lieu: cachettes[n].lieu,
}));

const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

/**
 * Où poser un canard pour ce tap ?
 * @param tap {x, y} en px
 * @param ecran [{numero, x, y}] cachettes projetées à l'écran
 * @param cachettes liste complète (centres en mètres), indexée par numéro
 * @param posees numéros des cachettes déjà occupées
 * @returns {{numero}} ou {{raison: 'zoom'|'plein'|'aucune'|'trop-pres'}}
 */
export function aimanter(tap, ecran, cachettes, posees, { revele, distanceMin, rayonPx = RAYON_AIMANT_PX }) {
  if (!revele) return { raison: 'zoom' };
  if (posees.length >= MAX_CANARDS) return { raison: 'plein' };
  const prises = new Set(posees);
  const proches = ecran
    .map((c) => ({ numero: c.numero, d: Math.hypot(c.x - tap.x, c.y - tap.y) }))
    .filter((c) => c.d <= rayonPx && !prises.has(c.numero))
    .sort((a, b) => a.d - b.d);
  if (!proches.length) return { raison: 'aucune' };
  const libre = proches.find((c) => posees.every(
    (p) => distance(cachettes[c.numero].centre, cachettes[p].centre) >= distanceMin,
  ));
  return libre ? { numero: libre.numero } : { raison: 'trop-pres' };
}
