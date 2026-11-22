import { describe, expect, it } from 'vitest';
import { aimanter, canardsDuDefi, chargerCachettes, idCachette } from '../src/cachettes.js';

const FICHIER = {
  ville: 'lille', version: 3, empreinte: 'k7f2', echelle: 0.7, gabarit: 0.35, distance_min_canards: 6,
  cachettes: [[1, 0, 2, 0.5, 0.4, 'sol'], [10, 3, 0, 1, 0.9, 'toit']],
};
const repondre = (reponse) => async () => reponse;

describe('chargement des cachettes', () => {
  it('lit le fichier et calcule le centre de chaque canard', async () => {
    const lot = await chargerCachettes('lille', repondre({ ok: true, json: async () => FICHIER }));
    expect(lot.version).toBe(3);
    expect(lot.empreinte).toBe('k7f2');
    expect(lot.distanceMin).toBe(6);
    expect(lot.cachettes[1]).toEqual({
      numero: 1, position: [10, 3, 0], rotation: 1, visibilite: 0.9, lieu: 'toit', centre: [10, 3 + 0.22 * 0.7, 0],
    });
  });

  it('dit « pas prêt » si le fichier manque', async () => {
    const html = { ok: true, json: async () => { throw new SyntaxError('index.html'); } };
    await expect(chargerCachettes('lille', repondre(html))).rejects.toThrow('pas-pret');
    await expect(chargerCachettes('lille', repondre({ ok: false }))).rejects.toThrow('pas-pret');
    await expect(chargerCachettes('lille', async () => { throw new TypeError('réseau'); })).rejects.toThrow('pas-pret');
    const sansDistance = { ...FICHIER, distance_min_canards: undefined };
    await expect(chargerCachettes('lille', repondre({ ok: true, json: async () => sansDistance })))
      .rejects.toThrow('pas-pret');
  });

  it('prépare les canards d’un défi pour la scène', async () => {
    const lot = await chargerCachettes('lille', repondre({ ok: true, json: async () => FICHIER }));
    expect(canardsDuDefi(lot.cachettes, [1])).toEqual([
      { id: idCachette(1), position: [10, 3, 0], rotation: 1, lieu: 'toit' },
    ]);
    expect(idCachette(1)).toBe('cachette-1');
  });
});

describe('aimant', () => {
  // centres à x = 0, 3, 20 et 10 m ; à l'écran à x = 100, 130, 300 et 140 px
  const cachettes = [0, 3, 20, 10].map((x, numero) => ({ numero, centre: [x, 0, 0] }));
  const ecran = [100, 130, 300, 140].map((x, numero) => ({ numero, x, y: 100 }));
  const options = { revele: true, distanceMin: 6 };

  it('demande de zoomer sous le seuil de révélation', () => {
    expect(aimanter({ x: 130, y: 100 }, ecran, cachettes, [], { ...options, revele: false })).toEqual({ raison: 'zoom' });
  });

  it('choisit la cachette la plus proche du doigt', () => {
    expect(aimanter({ x: 125, y: 100 }, ecran, cachettes, [], options)).toEqual({ numero: 1 });
  });

  it('ne trouve rien loin de toute cachette', () => {
    expect(aimanter({ x: 200, y: 300 }, ecran, cachettes, [], options)).toEqual({ raison: 'aucune' });
  });

  it('ignore une cachette déjà prise', () => {
    expect(aimanter({ x: 300, y: 100 }, ecran, cachettes, [2], options)).toEqual({ raison: 'aucune' });
  });

  it('prend la suivante si la plus proche est trop près d’un canard posé', () => {
    // la 1 est à 3 m du canard posé sur la 0 ; la 3 est à 10 m
    expect(aimanter({ x: 131, y: 100 }, ecran, cachettes, [0], options)).toEqual({ numero: 3 });
  });

  it('refuse si toutes les cachettes proches sont trop près', () => {
    expect(aimanter({ x: 101, y: 100 }, ecran, cachettes, [1], { ...options, rayonPx: 20 })).toEqual({ raison: 'trop-pres' });
  });

  it('refuse au-delà de 30 canards', () => {
    // les numéros 100 à 129 n'existent pas dans `cachettes` exprès : le test « plein » rend avant de les lire
    const trente = Array.from({ length: 30 }, (_, i) => i + 100);
    expect(aimanter({ x: 125, y: 100 }, ecran, cachettes, trente, options)).toEqual({ raison: 'plein' });
  });
});
