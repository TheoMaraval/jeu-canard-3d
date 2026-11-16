// Quel canard un tap désigne-t-il ? Géométrie écran pure.

export const TOLERANCE_PX = 22;

/**
 * @param {{x:number,y:number}} tap position du tap, en px
 * @param {{id:string,x:number,y:number,rayon:number}[]} canards centres et rayons à l'écran
 * @param {{revele:boolean,tolerance?:number}} options
 * @returns {string|null} identifiant du canard le plus proche dans la tolérance
 *
 * Sous le seuil de révélation, un tap ne trouve rien : sinon il suffirait de tapoter
 * la vue d'ensemble, où 22 px couvrent plusieurs mètres.
 */
export function choisirCanard(tap, canards, { revele, tolerance = TOLERANCE_PX }) {
  if (!revele) return null;
  let meilleur = null;
  let dMin = Infinity;
  for (const c of canards) {
    const d = Math.hypot(c.x - tap.x, c.y - tap.y);
    if (d <= Math.max(c.rayon, tolerance) && d < dMin) {
      dMin = d;
      meilleur = c.id;
    }
  }
  return meilleur;
}
