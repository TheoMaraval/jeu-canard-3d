// Mesure de fluidité, activée en ajoutant `&debug` à l'adresse d'une ville
// (par exemple `…/?ville=paris&debug`). Chargé à la demande : absent des parties normales.
//
// Le jeu ne redessine la ville que lorsque la vue bouge. La mesure fait donc glisser la
// vue toute seule à travers la carte, à trois zooms, et chronomètre l'intervalle entre deux
// images (requestAnimationFrame). Les fonctions de calcul sont pures et testées.

const DUREE_MS = 4000; // par zoom
const ECHAUFFEMENT_MS = 500; // début de chaque zoom ignoré (compilation des shaders…)
const IMAGES_MINI = 5; // en dessous, pas de conclusion (onglet en arrière-plan ?)
const SACCADE_MS = 34; // au moins deux images d'écran perdues à 60 Hz

export const SCENARIOS = [
  { id: 'ensemble', nom: 'Vue d’ensemble' },
  { id: 'moyen', nom: 'Zoom moyen' },
  { id: 'pres', nom: 'De près' },
];

export function mediane(liste) {
  const n = liste.length;
  if (!n) return 0;
  const tri = [...liste].sort((a, b) => a - b);
  return n % 2 ? tri[(n - 1) / 2] : (tri[n / 2 - 1] + tri[n / 2]) / 2;
}

/** Intervalles entre images (ms) → images/s (médiane), image lente (95e centile), saccades. */
export function resumer(intervalles) {
  const n = intervalles.length;
  if (!n) return { images: 0, ips: 0, lenteMs: 0, saccades: 0 };
  const tri = [...intervalles].sort((a, b) => a - b);
  return {
    images: n,
    ips: Math.round(1000 / mediane(tri)),
    lenteMs: Math.round(tri[Math.ceil(0.95 * n) - 1] * 10) / 10,
    saccades: intervalles.filter((d) => d >= SACCADE_MS).length,
  };
}

/** Vue au temps t (0 → 1) : une boucle qui balaie le centre de la carte, au zoom `ppm`. */
export function parcours(t, lim, ppm) {
  const a = 2 * Math.PI * t;
  const cu = (lim.uMin + lim.uMax) / 2;
  const cv = (lim.vMin + lim.vMax) / 2;
  return {
    u: cu + 0.35 * (lim.uMax - lim.uMin) * Math.sin(a),
    v: cv + 0.35 * (lim.vMax - lim.vMin) * Math.sin(2 * a),
    ppm,
  };
}

const virgule = (x, chiffres = 1) => x.toFixed(chiffres).replace('.', ',');

/** Résultats en texte, pour les copier et les envoyer. */
export function texteResultats({ ville, appareil, ecran, chargementMs }, resultats) {
  return [
    `Mesure de fluidité — ${ville}`,
    `Appareil : ${appareil}`,
    `Écran : ${ecran}`,
    `Chargement : ${virgule(chargementMs / 1000)} s`,
    ...resultats.map((r) => `${r.nom} : ${r.images < IMAGES_MINI
      ? 'trop peu d’images pour conclure (écran éteint ou onglet caché ?)'
      : `${r.ips} images/s, image lente ${virgule(r.lenteMs)} ms, `
        + `${r.saccades} saccade${r.saccades > 1 ? 's' : ''}`}, `
      + `image calculée en ${virgule(r.calculMs)} ms, `
      + `${Math.round(r.triangles / 1000)} k triangles, ${r.appels} appels`),
  ].join('\n');
}

// ------------------------------------------------------------------ dans la page

function nomAppareil(gl) {
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
}

/** Fait glisser la vue pendant DUREE_MS à un zoom donné ; renvoie les intervalles mesurés. */
function balayer(ppm, { limites, regler }) {
  return new Promise((fin) => {
    const intervalles = [];
    let debut = null;
    let avant = null;
    let fini = false;
    const terminer = () => {
      if (fini) return;
      fini = true;
      fin(intervalles);
    };
    // onglet caché : le navigateur ne dessine plus, on conclut quand même (« trop peu d'images »)
    setTimeout(terminer, DUREE_MS + 3000);
    const pas = (t) => {
      if (fini) return;
      debut ??= t;
      const ecoule = t - debut;
      if (avant !== null && ecoule > ECHAUFFEMENT_MS) intervalles.push(t - avant);
      avant = t;
      regler(parcours(ecoule / DUREE_MS, limites, ppm));
      if (ecoule < DUREE_MS) requestAnimationFrame(pas);
      else terminer();
    };
    requestAnimationFrame(pas);
  });
}

/**
 * Panneau de mesure.
 * @param o.scene  scène chargée (stats, contexte, limites, gabarit)
 * @param o.lireVue / o.regler  lire et imposer la vue du jeu
 * @param o.zooms  { ensemble, moyen, pres } en pixels par mètre
 */
export function installerMesure({ scene, ville, chargementMs, lireVue, regler, zooms }) {
  const gl = scene.contexte;
  const infos = {
    ville,
    appareil: nomAppareil(gl),
    ecran: `${innerWidth}×${innerHeight} ×${Math.min(devicePixelRatio || 1, 2)}`,
    chargementMs,
  };

  const panneau = document.createElement('div');
  panneau.className = 'mesure';
  const titre = document.createElement('b');
  titre.textContent = 'Mesure de fluidité';
  const texte = document.createElement('pre');
  texte.textContent = `${infos.appareil}\nChargement : ${virgule(chargementMs / 1000)} s`;
  const lancer = document.createElement('button');
  lancer.type = 'button';
  lancer.className = 'bouton';
  lancer.textContent = 'Mesurer (12 s)';
  const copier = document.createElement('button');
  copier.type = 'button';
  copier.className = 'bouton secondaire';
  copier.textContent = 'Copier les résultats';
  copier.hidden = true;
  panneau.append(titre, texte, lancer, copier);
  document.body.append(panneau);

  let rapport = '';
  lancer.onclick = async () => {
    lancer.disabled = true;
    const depart = lireVue();
    const resultats = [];
    for (const s of SCENARIOS) {
      texte.textContent = `${s.nom}… ne touche pas l'écran`;
      const intervalles = await balayer(zooms[s.id], { limites: scene.limites, regler });
      // coût d'une image, indépendant du rythme de l'écran (60 ou 120 Hz) : vue fixe, chronométrée
      regler(parcours(0.3, scene.limites, zooms[s.id]));
      const calculMs = mediane(scene.chronometrerRendu(15));
      const { triangles, calls } = scene.stats();
      resultats.push({ nom: s.nom, ...resumer(intervalles), calculMs, triangles, appels: calls });
    }
    regler(depart);
    rapport = texteResultats(infos, resultats);
    texte.textContent = rapport.split('\n').slice(3).join('\n');
    lancer.disabled = false;
    lancer.textContent = 'Recommencer';
    copier.hidden = false;
    console.info(rapport);
  };
  copier.onclick = async () => {
    try {
      await navigator.clipboard.writeText(rapport);
      copier.textContent = 'Copié !';
    } catch {
      copier.textContent = 'Copie impossible : faire une capture d’écran';
    }
  };
}
