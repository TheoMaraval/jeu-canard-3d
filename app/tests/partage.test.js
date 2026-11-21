import { describe, expect, it } from 'vitest';
import {
  decouperNom, lienJeu, partager, progression, resumeVille, texteScore, titreFin,
} from '../src/partage.js';

describe('partage', () => {
  it('découpe le nom affiché en ville et quartier', () => {
    expect(decouperNom('Paris — Grands Boulevards')).toEqual({ ville: 'Paris', quartier: 'Grands Boulevards' });
    expect(decouperNom('Tokyo')).toEqual({ ville: 'Tokyo', quartier: '' });
  });

  it('construit un lien propre vers le jeu ou une ville', () => {
    const page = 'https://exemple.io/jeu-canard-3d/?ville=lille&x=1#defi';
    expect(lienJeu(page)).toBe('https://exemple.io/jeu-canard-3d/');
    expect(lienJeu(page, 'new_york')).toBe('https://exemple.io/jeu-canard-3d/?ville=new_york');
  });

  it('écrit le message de score selon l’avancée', () => {
    const base = { nom: 'Paris — Grands Boulevards', total: 30, ecouleMs: 754000, taps: 41, precision: 30 / 41 };
    expect(texteScore({ ...base, trouves: 30 })).toBe(
      "🦆 J'ai trouvé les 30 canards cachés à Paris en 12:34 (41 taps, 73 % de précision). Tu fais mieux ?",
    );
    expect(texteScore({ ...base, trouves: 1, ecouleMs: 65000 })).toBe(
      "🦆 J'ai déjà trouvé 1 canard sur 30 à Paris (1:05). Viens chercher les autres !",
    );
    expect(texteScore({ ...base, trouves: 12 })).toContain('12 canards sur 30');
    expect(texteScore({ ...base, trouves: 0 })).toBe("🦆 Je cherche 30 canards cachés à Paris. Tu m'aides ?");
  });

  it('résume la progression d’une ville pour l’accueil', () => {
    expect(resumeVille(null, 30)).toBe('Nouvelle partie');
    expect(resumeVille({ trouves: [], taps: 0, ecouleMs: 4000 }, 30)).toBe('Nouvelle partie');
    expect(resumeVille({ trouves: ['a', 'b'], taps: 5, ecouleMs: 187000 }, 30)).toBe('2 / 30 trouvés · 3:07');
    expect(resumeVille({ trouves: Array(30).fill('x'), taps: 40, ecouleMs: 754000 }, 30)).toBe('✓ Terminée en 12:34');
  });

  it('calcule la progression d’une ville', () => {
    expect(progression(null, 30)).toBe(0);
    expect(progression({ trouves: ['a', 'b', 'c'] }, 30)).toBeCloseTo(0.1);
    expect(progression({ trouves: Array(31).fill('x') }, 30)).toBe(1);
    expect(progression({ trouves: ['a'] }, 0)).toBe(0);
  });

  it('donne un titre de fin selon la précision', () => {
    expect(titreFin(0.73)).toEqual({ titre: 'Œil de lynx !', etoiles: 3 });
    expect(titreFin(0.7)).toEqual({ titre: 'Œil de lynx !', etoiles: 3 });
    expect(titreFin(0.5).etoiles).toBe(2);
    expect(titreFin(0.39).etoiles).toBe(1);
  });

  it('utilise le partage natif quand il existe', async () => {
    const recu = [];
    const nav = { share: async (d) => recu.push(d), clipboard: { writeText: async () => { throw new Error('non'); } } };
    expect(await partager({ titre: 'T', texte: 'x', url: 'u' }, nav)).toBe('partage');
    expect(recu).toEqual([{ title: 'T', text: 'x', url: 'u' }]);
  });

  it('ne copie rien si le joueur annule le partage natif', async () => {
    let copie = false;
    const nav = {
      share: async () => { throw Object.assign(new Error('annulé'), { name: 'AbortError' }); },
      clipboard: { writeText: async () => { copie = true; } },
    };
    expect(await partager({ titre: 'T', texte: 'x', url: 'u' }, nav)).toBe('annule');
    expect(copie).toBe(false);
  });

  it('copie le message et le lien quand le partage natif manque ou échoue', async () => {
    let copie = null;
    const nav = { clipboard: { writeText: async (t) => { copie = t; } } };
    expect(await partager({ titre: 'T', texte: 'Viens !', url: 'https://x/' }, nav)).toBe('copie');
    expect(copie).toBe('Viens !\nhttps://x/');
    const refuse = { share: async () => { throw new Error('refusé'); }, clipboard: nav.clipboard };
    expect(await partager({ titre: 'T', texte: 'a', url: 'b' }, refuse)).toBe('copie');
  });

  it('signale quand rien n’est possible', async () => {
    expect(await partager({ titre: 'T', texte: 'a', url: 'b' }, {})).toBe('impossible');
    const casse = { clipboard: { writeText: async () => { throw new Error('bloqué'); } } };
    expect(await partager({ titre: 'T', texte: 'a', url: 'b' }, casse)).toBe('impossible');
  });
});
