import { describe, expect, it } from 'vitest';
import { SCENARIOS, mediane, parcours, resumer, texteResultats } from '../src/mesure.js';

describe('mesure de fluidité', () => {
  it('résume les intervalles entre images : images par seconde (médiane) et image lente', () => {
    const r = resumer([16, 17, 16, 17, 16, 50, 16, 17, 16, 17]);
    expect(r.images).toBe(10);
    expect(r.ips).toBe(61); // 1000 / 16,5 ms
    expect(r.lenteMs).toBe(50); // 95e centile : la saccade se voit
    expect(r.saccades).toBe(1); // images de plus de 34 ms : au moins deux images d'écran perdues
    expect(resumer([])).toEqual({ images: 0, ips: 0, lenteMs: 0, saccades: 0 });
    expect(mediane([3, 1, 2])).toBe(2);
    expect(mediane([])).toBe(0);
  });

  it('parcourt la carte en restant dans ses bornes, au zoom du scénario', () => {
    const lim = { uMin: -100, uMax: 100, vMin: -50, vMax: 50, ppmMax: 300 };
    for (const t of [0, 0.25, 0.5, 0.77, 1]) {
      const v = parcours(t, lim, 20);
      expect(v.ppm).toBe(20);
      expect(v.u).toBeGreaterThanOrEqual(-100);
      expect(v.u).toBeLessThanOrEqual(100);
      expect(v.v).toBeGreaterThanOrEqual(-50);
      expect(v.v).toBeLessThanOrEqual(50);
    }
    expect(parcours(0, lim, 20)).not.toEqual(parcours(0.3, lim, 20)); // la vue bouge
  });

  it('prévoit trois zooms : vue d’ensemble, moyen, de près', () => {
    expect(SCENARIOS.map((s) => s.id)).toEqual(['ensemble', 'moyen', 'pres']);
  });

  it('met les résultats en texte à copier', () => {
    const texte = texteResultats(
      { ville: 'paris', appareil: 'Mali-G78', ecran: '390×844 ×2', chargementMs: 4200 },
      [
        { nom: 'Vue d’ensemble', images: 200, ips: 58, lenteMs: 21.4, saccades: 0, calculMs: 9.25, triangles: 412000, appels: 180 },
        { nom: 'De près', images: 2, ips: 1, lenteMs: 900, saccades: 2, calculMs: 7, triangles: 611000, appels: 150 },
      ],
    );
    expect(texte).toContain('paris');
    expect(texte).toContain('Mali-G78');
    expect(texte).toContain('4,2 s');
    expect(texte).toContain('Vue d’ensemble : 58 images/s');
    expect(texte).toContain('412 k triangles');
    expect(texte).toContain('image calculée en 9,3 ms');
    expect(texte).toContain('De près : trop peu d’images pour conclure'); // page en arrière-plan
  });
});
