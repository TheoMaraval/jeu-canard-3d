import { describe, expect, it } from 'vitest';
import { creerPartie, precision, serialiser, taper, terminee } from '../src/partie.js';
import {
  charger, chargerRecord, cle, cleRecord, effacer, enregistrer, meilleur, retenirRecord,
} from '../src/sauvegarde.js';
import { choisirCanard } from '../src/picking.js';
import { chrono, pourcent } from '../src/hud.js';
import {
  axesCamera, borner, creerVue, deplacer, estRevele, limitesCarte, ppmMini, ppmRevelation, projeter, zoomer,
} from '../src/vue.js';

const IDS = ['canard-01', 'canard-02', 'canard-03'];

function faussStockage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}

describe('affichage du temps et de la précision', () => {
  it('formate le chrono en minutes et secondes, puis en heures', () => {
    expect(chrono(0)).toBe('0:00');
    expect(chrono(999)).toBe('0:00');
    expect(chrono(7000)).toBe('0:07');
    expect(chrono(187000)).toBe('3:07');
    expect(chrono(754000)).toBe('12:34');
    expect(chrono(3600000 + 125000)).toBe('1:02:05');
    expect(chrono(-50)).toBe('0:00');
  });

  it('affiche un tiret tant qu’aucun tap n’a été fait, puis la précision', () => {
    expect(pourcent(0, 0)).toBe('—');
    expect(pourcent(3 / 4, 4)).toBe('75 %');
    expect(pourcent(1 / 3, 3)).toBe('33 %');
  });
});

describe('partie', () => {
  it('compte un canard trouvé et le tap', () => {
    const { partie, trouve } = taper(creerPartie(IDS), 'canard-02');
    expect(trouve).toBe(true);
    expect([...partie.trouves]).toEqual(['canard-02']);
    expect(partie.taps).toBe(1);
  });

  it('un tap raté compte mais ne pénalise pas', () => {
    const { partie, trouve } = taper(creerPartie(IDS), null);
    expect(trouve).toBe(false);
    expect(partie.trouves.size).toBe(0);
    expect(partie.taps).toBe(1);
  });

  it('retaper un canard déjà trouvé ne le recompte pas', () => {
    const a = taper(creerPartie(IDS), 'canard-01').partie;
    const { partie, trouve } = taper(a, 'canard-01');
    expect(trouve).toBe(false);
    expect(partie.trouves.size).toBe(1);
    expect(partie.taps).toBe(2);
  });

  it('ignore un identifiant inconnu', () => {
    expect(taper(creerPartie(IDS), 'leurre-001').trouve).toBe(false);
  });

  it('ne modifie pas la partie reçue', () => {
    const p = creerPartie(IDS);
    taper(p, 'canard-01');
    expect(p.trouves.size).toBe(0);
    expect(p.taps).toBe(0);
  });

  it('se termine quand tout est trouvé, avec la précision', () => {
    let p = creerPartie(IDS);
    p = taper(p, null).partie;
    for (const id of IDS) p = taper(p, id).partie;
    expect(terminee(p)).toBe(true);
    expect(precision(p)).toBeCloseTo(3 / 4);
    expect(precision(creerPartie(IDS))).toBe(0);
  });

  it('reprend une sauvegarde en écartant les identifiants inconnus', () => {
    const p = creerPartie(IDS, { trouves: ['canard-03', 'fantome'], taps: 5, ecouleMs: 1200 });
    expect([...p.trouves]).toEqual(['canard-03']);
    expect(serialiser(p)).toEqual({ trouves: ['canard-03'], taps: 5, ecouleMs: 1200 });
  });
});

describe('sauvegarde', () => {
  it('relit ce qui a été enregistré, par ville et version', () => {
    const s = faussStockage();
    enregistrer(s, 'paris', 1, { trouves: ['canard-01'], taps: 2, ecouleMs: 10 });
    expect(charger(s, 'paris', 1)).toEqual({ trouves: ['canard-01'], taps: 2, ecouleMs: 10 });
    expect(charger(s, 'paris', 2)).toBeNull();
    expect(charger(s, 'tokyo', 1)).toBeNull();
    expect(cle('paris', 1)).toBe('jeu-canard-3d:paris:v1');
  });

  it('ignore une sauvegarde illisible ou mal formée', () => {
    const s = faussStockage();
    s.setItem(cle('paris', 1), '{pas du json');
    expect(charger(s, 'paris', 1)).toBeNull();
    s.setItem(cle('paris', 1), JSON.stringify({ trouves: 'non', taps: 1 }));
    expect(charger(s, 'paris', 1)).toBeNull();
  });

  it('survit à un stockage qui lève une erreur', () => {
    const casse = { getItem() { throw new Error('bloqué'); }, setItem() { throw new Error('plein'); }, removeItem() { throw new Error('x'); } };
    expect(charger(casse, 'paris', 1)).toBeNull();
    expect(() => enregistrer(casse, 'paris', 1, { trouves: [], taps: 0, ecouleMs: 0 })).not.toThrow();
    expect(() => effacer(casse, 'paris', 1)).not.toThrow();
  });

  it('efface', () => {
    const s = faussStockage();
    enregistrer(s, 'paris', 1, { trouves: [], taps: 0, ecouleMs: 0 });
    effacer(s, 'paris', 1);
    expect(charger(s, 'paris', 1)).toBeNull();
  });
});

describe('record', () => {
  const lent = { ecouleMs: 600000, taps: 40 };
  const rapide = { ecouleMs: 400000, taps: 60 };

  it('le meilleur est le plus rapide, puis celui qui a le moins de taps', () => {
    expect(meilleur(lent, rapide)).toBe(rapide);
    expect(meilleur(rapide, lent)).toBe(rapide);
    expect(meilleur({ ecouleMs: 1000, taps: 30 }, { ecouleMs: 1000, taps: 31 })).toEqual({ ecouleMs: 1000, taps: 30 });
    expect(meilleur(null, lent)).toBe(lent);
    expect(meilleur(lent, null)).toBe(lent);
    expect(meilleur(null, null)).toBeNull();
  });

  it('garde le meilleur résultat, même quand une partie plus lente le suit', () => {
    const s = faussStockage();
    expect(chargerRecord(s, 'paris', 3)).toBeNull();
    expect(retenirRecord(s, 'paris', 3, { ...lent, trouves: ['x'] })).toEqual({ record: lent, ancien: null });
    expect(retenirRecord(s, 'paris', 3, rapide)).toEqual({ record: rapide, ancien: lent });
    expect(retenirRecord(s, 'paris', 3, lent)).toEqual({ record: rapide, ancien: rapide });
    expect(chargerRecord(s, 'paris', 3)).toEqual(rapide);
    expect(chargerRecord(s, 'paris', 4)).toBeNull(); // une autre version de la ville : autres canards
    expect(cleRecord('paris', 3)).toBe('jeu-canard-3d:paris:v3:record');
  });

  it('survit à l’effacement de la partie (« Rejouer ») et à un record illisible', () => {
    const s = faussStockage();
    enregistrer(s, 'lille', 3, { trouves: ['canard-01'], taps: 40, ecouleMs: 600000 });
    retenirRecord(s, 'lille', 3, lent);
    effacer(s, 'lille', 3);
    expect(chargerRecord(s, 'lille', 3)).toEqual(lent);
    s.setItem(cleRecord('lille', 3), '{"ecouleMs":"vite"}');
    expect(chargerRecord(s, 'lille', 3)).toBeNull();
    const casse = { getItem() { throw new Error('bloqué'); }, setItem() { throw new Error('plein'); } };
    expect(chargerRecord(casse, 'lille', 3)).toBeNull();
    expect(retenirRecord(casse, 'lille', 3, lent)).toEqual({ record: lent, ancien: null });
  });
});

describe('picking', () => {
  const canards = [
    { id: 'a', x: 100, y: 100, rayon: 30 },
    { id: 'b', x: 150, y: 100, rayon: 30 },
  ];

  it('rien si la vue ne révèle pas les canards', () => {
    expect(choisirCanard({ x: 100, y: 100 }, canards, { revele: false })).toBeNull();
  });

  it('prend le canard le plus proche du doigt', () => {
    expect(choisirCanard({ x: 120, y: 100 }, canards, { revele: true })).toBe('a');
    expect(choisirCanard({ x: 131, y: 100 }, canards, { revele: true })).toBe('b');
  });

  it('rien au-delà du rayon', () => {
    expect(choisirCanard({ x: 100, y: 140 }, canards, { revele: true })).toBeNull();
  });

  it('garde une tolérance minimale pour le doigt quand le canard est petit', () => {
    const petit = [{ id: 'p', x: 0, y: 0, rayon: 8 }];
    expect(choisirCanard({ x: 20, y: 0 }, petit, { revele: true, tolerance: 22 })).toBe('p');
    expect(choisirCanard({ x: 23, y: 0 }, petit, { revele: true, tolerance: 22 })).toBeNull();
  });
});

describe('vue', () => {
  const ecran = { w: 1000, h: 800 };
  const limites = { uMin: -85, uMax: 85, vMin: -49, vMax: 71, ppmMax: 240 };

  it('part dézoomée sur toute la carte', () => {
    const v = creerVue(ecran, limites);
    expect(v.ppm).toBeCloseTo(ppmMini(ecran, limites));
    expect((limites.uMax - limites.uMin) * v.ppm).toBeLessThanOrEqual(ecran.w + 1e-6);
    expect(estRevele(v, 0.35)).toBe(false);
  });

  it('révèle les canards à partir du seuil', () => {
    expect(estRevele({ ppm: 79.9 }, 0.35)).toBe(false);
    expect(estRevele({ ppm: 80 }, 0.35)).toBe(true); // un canard de 0,35 m fait alors 28 px
    expect(ppmRevelation(0.5)).toBe(56); // un canard plus gros se révèle plus tôt
  });

  it('glisser à droite déplace la vue vers la gauche', () => {
    const v = deplacer({ u: 0, v: 0, ppm: 10 }, 50, -20);
    expect(v.u).toBeCloseTo(-5);
    expect(v.v).toBeCloseTo(-2);
  });

  it('zoomer garde le point sous le doigt immobile', () => {
    const avant = { u: 3, v: 4, ppm: 20 };
    const doigt = { x: 700, y: 250 };
    const apres = zoomer(avant, 2, doigt, ecran, limites);
    const monde = (vue) => ({ U: vue.u + (doigt.x - ecran.w / 2) / vue.ppm, V: vue.v - (doigt.y - ecran.h / 2) / vue.ppm });
    expect(apres.ppm).toBe(40);
    expect(monde(apres).U).toBeCloseTo(monde(avant).U);
    expect(monde(apres).V).toBeCloseTo(monde(avant).V);
  });

  it('borne le zoom et la position', () => {
    expect(zoomer({ u: 0, v: 0, ppm: 200 }, 10, { x: 500, y: 400 }, ecran, limites).ppm).toBe(240);
    expect(zoomer({ u: 0, v: 0, ppm: 20 }, 0.0001, { x: 500, y: 400 }, ecran, limites).ppm).toBeCloseTo(ppmMini(ecran, limites));
    const b = borner({ u: 999, v: -999, ppm: 100 }, ecran, limites);
    expect(b.u).toBe(85);
    expect(b.v).toBe(-49);
  });

  it('déduit le zoom maximal du gabarit et les bornes de la carte', () => {
    const axes = axesCamera([0.57735, 0.57735, 0.57735]);
    const lim = limitesCarte(120, 30, axes, 0.35);
    expect(lim.ppmMax).toBeCloseTo(120 / 0.35);
    expect(lim.uMax).toBeCloseTo(84.85, 1);
    expect(lim.uMin).toBeCloseTo(-84.85, 1);
    expect(lim.vMax).toBeGreaterThan(lim.vMin);
  });

  it('projette un point du monde à l’écran', () => {
    const axes = { droite: [1, 0, 0], haut: [0, 1, 0] };
    const p = projeter([12, 5, 99], { u: 10, v: 0, ppm: 10 }, ecran, axes);
    expect(p.x).toBeCloseTo(520);
    expect(p.y).toBeCloseTo(350);
  });
});
