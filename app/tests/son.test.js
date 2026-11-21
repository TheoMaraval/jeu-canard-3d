import { describe, expect, it } from 'vitest';
import { creerSon, parametresCoin } from '../src/son.js';

function faussStockage(depart = {}) {
  const m = new Map(Object.entries(depart));
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, v), m };
}

/** Faux AudioContext : compte les sons joués, sans rien jouer. */
function fauxContexte() {
  const journal = { contextes: 0, demarrages: 0, reprises: 0 };
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
  }
  return { Ctx, journal };
}

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

  it('joue un cri (trois oscillateurs) et débloque le son au premier geste', () => {
    const { Ctx, journal } = fauxContexte();
    const son = creerSon(faussStockage(), Ctx);
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
    const son = creerSon(stockage, Ctx);
    expect(son.actif()).toBe(true);
    expect(son.basculer()).toBe(false);
    son.coin();
    expect(journal.demarrages).toBe(0);
    expect(creerSon(stockage, Ctx).actif()).toBe(false);
    expect(son.basculer()).toBe(true);
    expect(journal.demarrages).toBe(3); // rallumer fait entendre un cri
  });

  it('reste silencieux sans Web Audio et survit à un stockage bloqué', () => {
    const casse = { getItem() { throw new Error('bloqué'); }, setItem() { throw new Error('bloqué'); } };
    const son = creerSon(casse, undefined);
    expect(son.actif()).toBe(true);
    expect(() => son.coin()).not.toThrow();
    expect(() => son.basculer()).not.toThrow();
  });
});
