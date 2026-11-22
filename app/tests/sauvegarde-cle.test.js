import { describe, expect, it } from 'vitest';
import { charger, chargerCle, cle, effacerCle, enregistrerCle } from '../src/sauvegarde.js';

function fauxStockage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}

describe('progression sous une clé quelconque', () => {
  it('enregistre, relit et efface', () => {
    const s = fauxStockage();
    enregistrerCle(s, 'cle-test', { trouves: ['a'], taps: 3, ecouleMs: 1200 });
    expect(chargerCle(s, 'cle-test')).toEqual({ trouves: ['a'], taps: 3, ecouleMs: 1200 });
    effacerCle(s, 'cle-test');
    expect(chargerCle(s, 'cle-test')).toBeNull();
  });

  it('reste compatible avec la sauvegarde par ville', () => {
    const s = fauxStockage();
    enregistrerCle(s, cle('lille', 3), { trouves: [], taps: 1, ecouleMs: 0 });
    expect(charger(s, 'lille', 3)).toEqual({ trouves: [], taps: 1, ecouleMs: 0 });
  });
});
