// Les sons du jeu, deux enregistrements joués avec Web Audio :
// - `assets/sons/coin.mp3` (16 Ko) : le « coin coin » d'un canard trouvé. Chaque cri varie
//   un peu de hauteur et de vitesse ;
// - `assets/sons/fin.mp3` (22 Ko) : la musique quand les 30 canards sont trouvés.
//
// Tant que le « coin coin » n'est pas prêt (ou s'il manque), un cri synthétisé prend le
// relais : une voix grinçante (dent de scie + carré) dont la hauteur monte un peu puis
// retombe, passée dans deux filtres « nasaux » (formants vers 1,1 et 2,6 kHz).

const CLE = 'jeu-canard-3d:son';
export const FICHIERS = { coin: 'sons/coin.mp3', fin: 'sons/fin.mp3' };
const VOLUME = 0.8;

/** Vitesse de lecture du cri : ±6 % autour de 1 (plus vite = plus aigu). */
export function vitesseCri(alea = Math.random) {
  return 1 + (alea() * 2 - 1) * 0.06;
}

/** Télécharge un enregistrement ; `null` s'il est absent. */
function telechargerSon(chemin) {
  if (!globalThis.fetch) return Promise.resolve(null);
  // Vite renvoie index.html pour un fichier absent : une réponse HTML veut dire « pas de son »
  return fetch(chemin)
    .then((r) => (r.ok && !(r.headers.get('content-type') ?? '').includes('html') ? r.arrayBuffer() : null))
    .catch(() => null);
}

/** Paramètres d'un cri, tirés autour d'une base. `alea` : fonction qui renvoie [0, 1[. */
export function parametresCoin(alea = Math.random) {
  const varie = (base, ecart) => base * (1 + (alea() * 2 - 1) * ecart);
  return {
    hauteur: varie(330, 0.08), // Hz au début du cri
    chute: varie(0.62, 0.06), // hauteur finale = hauteur × chute
    duree: varie(0.55, 0.1), // secondes
    nasal: varie(1150, 0.08), // premier formant (Hz)
    grain: varie(34, 0.15), // fréquence du « grésillement » (Hz)
  };
}

function lire(stockage) {
  try {
    return stockage.getItem(CLE) !== 'non';
  } catch {
    return true;
  }
}

/**
 * @param stockage objet de type localStorage (le choix du joueur y est gardé)
 * @param Contexte constructeur AudioContext (remplaçable pour les tests)
 * @param telecharger (chemin) → promesse des octets de l'enregistrement, ou de `null`
 */
export function creerSon(
  stockage = globalThis.localStorage,
  Contexte = globalThis.AudioContext ?? globalThis.webkitAudioContext,
  telecharger = telechargerSon,
) {
  let actif = lire(stockage);
  let ctx = null;
  const tampons = {}; // enregistrements décodés, prêts à jouer : { coin, fin }
  // téléchargés tout de suite (sans contexte audio), décodés dès que le contexte existe
  const octets = {};
  if (Contexte) {
    for (const [nom, chemin] of Object.entries(FICHIERS)) {
      octets[nom] = Promise.resolve(chemin).then(telecharger).catch(() => null);
    }
  }

  /** iOS n'autorise le son qu'après un geste : à appeler dans un gestionnaire de toucher. */
  function deverrouiller() {
    if (!Contexte) return null;
    if (!ctx) {
      ctx = new Contexte();
      for (const [nom, promesse] of Object.entries(octets)) {
        promesse
          .then((b) => (b ? ctx.decodeAudioData(b) : null))
          .then((t) => { tampons[nom] = t; })
          .catch(() => {}); // format illisible : pas de ce son (le cri synthétisé reste)
      }
    }
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }

  function jouer(nom, { vitesse = 1, delai = 0 } = {}) {
    const source = ctx.createBufferSource();
    source.buffer = tampons[nom];
    source.playbackRate.value = vitesse;
    const volume = ctx.createGain();
    volume.gain.value = VOLUME;
    source.connect(volume).connect(ctx.destination);
    source.start(ctx.currentTime + 0.01 + delai);
  }

  function coin() {
    if (!actif || !deverrouiller()) return;
    if (tampons.coin) jouer('coin', { vitesse: vitesseCri() });
    else coinSynthetise();
  }

  /** Musique de fin, après `delai` secondes (pour laisser finir le dernier « coin coin »). */
  function fanfare(delai = 0) {
    if (!actif || !deverrouiller() || !tampons.fin) return;
    jouer('fin', { delai });
  }

  function coinSynthetise() {
    const p = parametresCoin();
    const t0 = ctx.currentTime + 0.01;
    const fin = t0 + p.duree;

    // voix : deux oscillateurs mêlés, hauteur qui monte un peu puis retombe
    const voix = [['sawtooth', 1, 0.6], ['square', 1.005, 0.25]].map(([forme, desaccord, volume]) => {
      const o = ctx.createOscillator();
      o.type = forme;
      const f = o.frequency;
      f.setValueAtTime(p.hauteur * desaccord, t0);
      f.linearRampToValueAtTime(p.hauteur * desaccord * 1.08, t0 + 0.05);
      f.exponentialRampToValueAtTime(p.hauteur * p.chute * desaccord, fin);
      const g = ctx.createGain();
      g.gain.value = volume;
      o.connect(g);
      return { o, g };
    });

    // grésillement : une modulation rapide du volume rend la voix rauque
    const lfo = ctx.createOscillator();
    lfo.frequency.value = p.grain;
    const profondeur = ctx.createGain();
    profondeur.gain.value = 0.35;
    const rauque = ctx.createGain();
    rauque.gain.value = 0.65;
    lfo.connect(profondeur).connect(rauque.gain);

    // formants : le côté nasal du cancan
    const f1 = ctx.createBiquadFilter();
    f1.type = 'peaking';
    f1.frequency.value = p.nasal;
    f1.Q.value = 3;
    f1.gain.value = 14;
    const f2 = ctx.createBiquadFilter();
    f2.type = 'peaking';
    f2.frequency.value = p.nasal * 2.3;
    f2.Q.value = 4;
    f2.gain.value = 9;
    const doux = ctx.createBiquadFilter();
    doux.type = 'lowpass';
    doux.frequency.setValueAtTime(3800, t0);
    doux.frequency.exponentialRampToValueAtTime(1600, fin); // le « nnn » s'assourdit

    // enveloppe : attaque sèche, tenue, puis un « nnn » qui traîne avant de s'éteindre
    const env = ctx.createGain();
    env.gain.setValueAtTime(0.0001, t0);
    env.gain.exponentialRampToValueAtTime(0.32, t0 + 0.015);
    env.gain.setValueAtTime(0.32, t0 + p.duree * 0.35);
    env.gain.linearRampToValueAtTime(0.16, t0 + p.duree * 0.8);
    env.gain.exponentialRampToValueAtTime(0.0001, fin);

    for (const { g } of voix) g.connect(rauque);
    rauque.connect(f1).connect(f2).connect(doux).connect(env).connect(ctx.destination);
    for (const { o } of voix) {
      o.start(t0);
      o.stop(fin + 0.02);
    }
    lfo.start(t0);
    lfo.stop(fin + 0.02);
  }

  function basculer() {
    actif = !actif;
    try {
      stockage.setItem(CLE, actif ? 'oui' : 'non');
    } catch {
      // stockage bloqué : le choix vaut pour cette visite seulement
    }
    if (actif) coin(); // on entend tout de suite que le son est revenu
    return actif;
  }

  return { coin, fanfare, deverrouiller, basculer, actif: () => actif };
}
