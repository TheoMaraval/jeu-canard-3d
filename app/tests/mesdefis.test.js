import { describe, expect, it } from 'vitest';
import {
  CLE_DEFIS, cleDefiRecu, dernierPrenom, detailDefi, enregistrerDefi, estValable, listerDefis, nouvelId,
  retenirPrenom, supprimerDefi, trouverDefi,
} from '../src/mesdefis.js';

function fauxStockage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}
const bloque = () => { throw new Error('stockage bloqué'); };
const STOCKAGE_BLOQUE = { getItem: bloque, setItem: bloque, removeItem: bloque };

const defi = (id, numeros = [1, 2]) => ({
  id, ville: 'lille', version: 3, empreinte: 'k7f2', prenom: 'Camille', numeros, cree: new Date(2026, 10, 21, 12).getTime(),
});

describe('mes défis', () => {
  it('garde un brouillon, le met à jour à sa place et le retrouve', () => {
    const s = fauxStockage();
    enregistrerDefi(s, defi('a'));
    enregistrerDefi(s, defi('b'));
    enregistrerDefi(s, defi('a', [1, 2, 3]));
    expect(listerDefis(s).map((d) => d.id)).toEqual(['b', 'a']);
    expect(trouverDefi(s, 'a').numeros).toEqual([1, 2, 3]);
    expect(trouverDefi(s, 'zzz')).toBeNull();
  });

  it('retire un défi sans canard, ou supprimé', () => {
    const s = fauxStockage();
    enregistrerDefi(s, defi('a'));
    enregistrerDefi(s, defi('b'));
    enregistrerDefi(s, defi('a', []));
    expect(listerDefis(s).map((d) => d.id)).toEqual(['b']);
    supprimerDefi(s, 'b');
    expect(listerDefis(s)).toEqual([]);
  });

  it('ignore une liste illisible et les entrées invalides', () => {
    const s = fauxStockage();
    s.setItem(CLE_DEFIS, '{pas du json');
    expect(listerDefis(s)).toEqual([]);
    s.setItem(CLE_DEFIS, JSON.stringify([defi('a'), { id: 'b' }, null]));
    expect(listerDefis(s).map((d) => d.id)).toEqual(['a']);
  });

  it('survit à un stockage bloqué', () => {
    expect(listerDefis(STOCKAGE_BLOQUE)).toEqual([]);
    expect(() => enregistrerDefi(STOCKAGE_BLOQUE, defi('a'))).not.toThrow();
    expect(() => supprimerDefi(STOCKAGE_BLOQUE, 'a')).not.toThrow();
    expect(dernierPrenom(STOCKAGE_BLOQUE)).toBe('');
    expect(() => retenirPrenom(STOCKAGE_BLOQUE, 'Zoé')).not.toThrow();
  });

  it('retient le dernier prénom', () => {
    const s = fauxStockage();
    expect(dernierPrenom(s)).toBe('');
    retenirPrenom(s, 'Zoé');
    expect(dernierPrenom(s)).toBe('Zoé');
  });

  it('dit si un défi vaut encore pour sa ville', () => {
    const scenes = [{ id: 'lille', version: 3, empreinte: 'k7f2' }, { id: 'paris', version: 3, empreinte: 'aaaa' }];
    expect(estValable(defi('a'), scenes)).toBe(true);
    expect(estValable({ ...defi('a'), version: 2 }, scenes)).toBe(false);
    expect(estValable({ ...defi('a'), empreinte: 'zzzz' }, scenes)).toBe(false);
    expect(estValable({ ...defi('a'), ville: 'rome' }, scenes)).toBe(false);
  });

  it('résume un défi, fabrique ses clés et identifiants', () => {
    expect(detailDefi(defi('a', [4]))).toBe('1 canard · 21/11');
    expect(detailDefi(defi('a', [1, 2, 3]))).toBe('3 canards · 21/11');
    expect(nouvelId(1000, () => 0.5)).toBe(`${(1000).toString(36)}i0`);
    expect(cleDefiRecu('AQMk')).toBe('jeu-canard-3d:defi:AQMk');
  });
});
