import { describe, expect, it } from 'vitest';
import { creerSon, parametresCoin, vitesseCri } from '../src/son.js';

function faussStockage(depart = {}) {
  const m = new Map(Object.entries(depart));
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, v), m };
}

/** Faux AudioContext : compte les sons joués, sans rien jouer. */
function fauxContexte() {
  const journal = { contextes: 0, demarrages: 0, reprises: 0, lectures: [], decodages: 0 };
  const param = () => ({
    value: 0, setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {},
  });
  const noeud = () => ({ connect: (n) => n ?? {}, gain: param(), frequency: param(), Q: param() });
  class Ctx {
    constructor() { journal.contextes += 1; this.state = 'suspended'; this.currentTime = 0; this.destination = {}; }
    resume() { journal.reprises += 1; this.state = 'running'; }
    createOscillator() { return { ...noeud(), start() { journal.demarrages += 1; }, stop() {} }; }
    createGain() { return noeud(); }
    createBiquadFilter() { return noeud(); }
    createBufferSource() {
      const src = { ...noeud(), playbackRate: param(), buffer: null };
      src.start = (quand) => journal.lectures.push({ buffer: src.buffer, vitesse: src.playbackRate.value, quand });
      return src;
    }
    decodeAudioData(octets) {
      journal.decodages += 1;
      return octets === 'illisible' ? Promise.reject(new Error('format')) : Promise.resolve({ decode: octets });
    }
  }
  return { Ctx, journal };
}

const sansFichier = () => null;
const attendre = () => new Promise((r) => setTimeout(r, 0));

describe('son', () => {
  it('fait varier le cri autour de sa base, sans sortir des bornes', () => {
    const bas = parametresCoin(() => 0);
    const haut = parametresCoin(() => 0.999);
    expect(bas.hauteur).toBeLessThan(haut.hauteur);
    for (const p of [bas, haut, parametresCoin()]) {
      expect(p.hauteur).toBeGreaterThan(290);
      expect(p.hauteur).toBeLessThan(370);
      expect(p.chute).toBeLessThan(1); // la voix retombe : « coinnn »
      expect(p.duree).toBeGreaterThan(0.45);
      expect(p.duree).toBeLessThan(0.65);
    }
  });

  it('sans enregistrement, joue le cri synthétisé (trois oscillateurs) et débloque le son au premier geste', () => {
    const { Ctx, journal } = fauxContexte();
    const son = creerSon(faussStockage(), Ctx, sansFichier);
    son.coin();
    expect(journal.contextes).toBe(1);
    expect(journal.reprises).toBe(1);
    expect(journal.demarrages).toBe(3);
    son.coin();
    expect(journal.contextes).toBe(1); // un seul contexte audio pour toute la partie
  });

  it('se coupe, et s’en souvient', () => {
    const { Ctx, journal } = fauxContexte();
    const stockage = faussStockage();
    const son = creerSon(stockage, Ctx, sansFichier);
    expect(son.actif()).toBe(true);
    expect(son.basculer()).toBe(false);
    son.coin();
    expect(journal.demarrages).toBe(0);
    expect(creerSon(stockage, Ctx, sansFichier).actif()).toBe(false);
    expect(son.basculer()).toBe(true);
    expect(journal.demarrages).toBe(3); // rallumer fait entendre un cri
  });

  it('reste silencieux sans Web Audio et survit à un stockage bloqué', () => {
    const casse = { getItem() { throw new Error('bloqué'); }, setItem() { throw new Error('bloqué'); } };
    const son = creerSon(casse, undefined, sansFichier);
    expect(son.actif()).toBe(true);
    expect(() => son.coin()).not.toThrow();
    expect(() => son.basculer()).not.toThrow();
  });

  it('joue l’enregistrement une fois décodé, à une vitesse un peu variable', async () => {
    const { Ctx, journal } = fauxContexte();
    const son = creerSon(faussStockage(), Ctx, (chemin) => Promise.resolve(chemin));
    son.deverrouiller(); // premier contact : le décodage commence
    await attendre();
    son.coin();
    son.coin();
    expect(journal.decodages).toBe(2); // le cri et la musique, décodés une seule fois
    expect(journal.demarrages).toBe(0); // plus de cri synthétisé
    expect(journal.lectures).toHaveLength(2);
    expect(journal.lectures[0].buffer).toEqual({ decode: 'sons/coin.mp3' });
    expect(journal.lectures[0].quand).toBeCloseTo(0.01);
    for (const { vitesse } of journal.lectures) {
      expect(vitesse).toBeGreaterThan(0.93);
      expect(vitesse).toBeLessThan(1.07);
    }
  });

  it('garde le cri synthétisé si l’enregistrement est absent ou illisible', async () => {
    for (const telecharger of [() => Promise.resolve(null), () => Promise.resolve('illisible'), () => Promise.reject(new Error('réseau'))]) {
      const { Ctx, journal } = fauxContexte();
      const son = creerSon(faussStockage(), Ctx, telecharger);
      son.deverrouiller();
      await attendre();
      son.coin();
      expect(journal.lectures).toHaveLength(0);
      expect(journal.demarrages).toBe(3);
    }
  });

  it('joue la musique de fin après le délai demandé, sauf son coupé ou fichier absent', async () => {
    const { Ctx, journal } = fauxContexte();
    const son = creerSon(faussStockage(), Ctx, (chemin) => Promise.resolve(chemin));
    son.deverrouiller();
    await attendre();
    son.fanfare(1);
    expect(journal.lectures).toEqual([{ buffer: { decode: 'sons/fin.mp3' }, vitesse: 1, quand: 1.01 }]);
    son.basculer(); // coupé
    son.fanfare(1);
    expect(journal.lectures).toHaveLength(1);

    const sansMusique = fauxContexte();
    const muet = creerSon(faussStockage(), sansMusique.Ctx, (c) => Promise.resolve(c === 'sons/fin.mp3' ? null : c));
    muet.deverrouiller();
    await attendre();
    muet.fanfare(1);
    expect(sansMusique.journal.lectures).toHaveLength(0);
    expect(sansMusique.journal.demarrages).toBe(0); // pas de remplaçant synthétisé pour la musique
  });

  it('fait varier la vitesse du cri de ±6 % au plus', () => {
    expect(vitesseCri(() => 0)).toBeCloseTo(0.94);
    expect(vitesseCri(() => 0.5)).toBeCloseTo(1);
    expect(vitesseCri(() => 0.999)).toBeLessThan(1.06);
  });
});
