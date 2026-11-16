// La vue : où regarde la caméra orthographique et à quelle échelle. Fonctions pures.
//
// u, v : position du centre de l'écran dans le plan de la caméra, en mètres
//        (u vers la droite de l'écran, v vers le haut).
// ppm  : pixels par mètre. C'est le zoom.

// `gabarit` : taille d'un canard en mètres, lue dans placements.json (elle dépend de la ville).
export const PX_REVELATION = 28; // bec et œil affichés quand le canard fait au moins 28 px
export const PX_MAX = 120; // taille du canard au zoom maximal

export const ppmRevelation = (gabarit) => PX_REVELATION / gabarit;

export const estRevele = (vue, gabarit) => vue.ppm >= ppmRevelation(gabarit);

/** Zoom le plus large : toute la carte tient à l'écran. */
export const ppmMini = (ecran, lim) =>
  Math.min(ecran.w / (lim.uMax - lim.uMin), ecran.h / (lim.vMax - lim.vMin));

export function borner(vue, ecran, lim) {
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  return {
    u: clamp(vue.u, lim.uMin, lim.uMax),
    v: clamp(vue.v, lim.vMin, lim.vMax),
    ppm: clamp(vue.ppm, ppmMini(ecran, lim), lim.ppmMax),
  };
}

export const creerVue = (ecran, lim) => ({
  u: (lim.uMin + lim.uMax) / 2, v: (lim.vMin + lim.vMax) / 2, ppm: ppmMini(ecran, lim),
});

/** Le doigt glisse de (dx, dy) px : le décor suit le doigt. */
export const deplacer = (vue, dx, dy) => ({ ...vue, u: vue.u - dx / vue.ppm, v: vue.v + dy / vue.ppm });

/** Multiplie le zoom par `facteur` en gardant immobile le point sous `doigt`. */
export function zoomer(vue, facteur, doigt, ecran, lim) {
  const ppm = Math.min(lim.ppmMax, Math.max(ppmMini(ecran, lim), vue.ppm * facteur));
  const ex = doigt.x - ecran.w / 2;
  const ey = doigt.y - ecran.h / 2;
  return borner({
    u: vue.u + ex / vue.ppm - ex / ppm,
    v: vue.v - ey / vue.ppm + ey / ppm,
    ppm,
  }, ecran, lim);
}

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

/** Point du monde [x, y, z] -> pixel. `axes` : vecteurs droite et haut de la caméra. */
export const projeter = (p, vue, ecran, axes) => ({
  x: ecran.w / 2 + (dot(p, axes.droite) - vue.u) * vue.ppm,
  y: ecran.h / 2 - (dot(p, axes.haut) - vue.v) * vue.ppm,
});

/** Axes de la caméra à partir du vecteur unitaire qui pointe du décor vers elle. */
export function axesCamera(versCamera) {
  const [x, y, z] = versCamera;
  const n = Math.hypot(z, x);
  const droite = [z / n, 0, -x / n]; // (0,1,0) × versCamera
  const haut = [
    y * droite[2] - z * droite[1],
    z * droite[0] - x * droite[2],
    x * droite[1] - y * droite[0],
  ]; // versCamera × droite
  return { droite, haut };
}

/** Bornes de la vue pour une carte carrée de côté `taille` et des toits jusqu'à `hauteurMax`. */
export function limitesCarte(taille, hauteurMax, axes, gabarit) {
  const ppmMax = PX_MAX / gabarit;
  const d = taille / 2;
  const us = [];
  const vs = [];
  for (const x of [-d, d]) for (const z of [-d, d]) for (const y of [0, hauteurMax]) {
    us.push(dot([x, y, z], axes.droite));
    vs.push(dot([x, y, z], axes.haut));
  }
  return { uMin: Math.min(...us), uMax: Math.max(...us), vMin: Math.min(...vs), vMax: Math.max(...vs), ppmMax };
}
