import { describe, expect, it } from 'vitest';
import {
  deQui, decoderDefi, encoderDefi, libelleRenvoi, lienCacher, lienDefi, messageRejet, texteInvitationDefi,
  texteTempsDefi, titreDefi, titreFinDefi, verifierDefi,
} from '../src/defi.js';

const DEFI = { version: 3, empreinte: 'k7f2', numeros: [0, 17, 3499], prenom: 'Camille' };

describe('code de défi', () => {
  it('fait l’aller-retour, en caractères sûrs pour une adresse', () => {
    const code = encoderDefi(DEFI);
    expect(code).toMatch(/^[A-Za-z0-9_-]+$/);
    expect(decoderDefi(code)).toEqual({ ok: true, defi: DEFI });
  });

  it('accepte 1 et 30 canards, avec ou sans prénom, en moins de 100 caractères', () => {
    const un = { ...DEFI, numeros: [42], prenom: '' };
    expect(decoderDefi(encoderDefi(un))).toEqual({ ok: true, defi: un });
    const trente = { ...DEFI, numeros: Array.from({ length: 30 }, (_, i) => i * 100) };
    const code = encoderDefi(trente);
    expect(decoderDefi(code)).toEqual({ ok: true, defi: trente });
    expect(code.length).toBeLessThan(100);
  });

  it('garde accents et émoji, et coupe le prénom à 20 caractères', () => {
    expect(decoderDefi(encoderDefi({ ...DEFI, prenom: 'Zoé 🦆' })).defi.prenom).toBe('Zoé 🦆');
    const long = encoderDefi({ ...DEFI, prenom: '  Maximilien-Alexandre de la Tour ' });
    expect(decoderDefi(long).defi.prenom).toBe('Maximilien-Alexandre');
  });

  it('rejette un code abîmé', () => {
    const code = encoderDefi(DEFI);
    for (const abime of ['', null, undefined, 'pas un code !', code.slice(0, 10),
      encoderDefi({ ...DEFI, numeros: [5, 5] }), encoderDefi({ ...DEFI, numeros: [] })]) {
      expect(decoderDefi(abime)).toEqual({ ok: false, raison: 'abime' });
    }
  });

  it('rejette un format inconnu', () => {
    const code = encoderDefi(DEFI);
    expect(code.slice(0, 2)).toBe('AQ'); // premier octet = 1 (format)
    // « Ag » : premier octet = 2, le reste inchangé
    expect(decoderDefi(`Ag${code.slice(2)}`)).toEqual({ ok: false, raison: 'format' });
  });

  it('vérifie le défi contre les cachettes chargées', () => {
    const ville = { version: 3, empreinte: 'k7f2', nombre: 3500 };
    expect(verifierDefi(DEFI, ville)).toBeNull();
    expect(verifierDefi(DEFI, { ...ville, version: 4 })).toBe('version');
    expect(verifierDefi(DEFI, { ...ville, empreinte: 'zzzz' })).toBe('empreinte');
    expect(verifierDefi(DEFI, { ...ville, nombre: 3499 })).toBe('abime');
  });
});

describe('textes des défis', () => {
  it('accorde « de » devant le prénom', () => {
    expect(deQui('Camille')).toBe('de Camille');
    expect(deQui('Amélie')).toBe('d’Amélie');
    expect(deQui('Élodie')).toBe('d’Élodie');
    expect(deQui('')).toBe('d’un ami');
    expect(titreDefi('Camille')).toBe('Le défi de Camille');
    expect(titreFinDefi('Amélie')).toBe('Défi d’Amélie réussi !');
    expect(titreFinDefi('')).toBe('Défi réussi !');
    expect(libelleRenvoi('Camille')).toBe('Envoyer mon temps à Camille');
    expect(libelleRenvoi('')).toBe('Envoyer mon temps');
  });

  it('écrit l’invitation et le temps renvoyé', () => {
    expect(texteInvitationDefi({ prenom: 'Camille', n: 7, ville: 'Lille' }))
      .toBe('🦆 Camille a caché 7 canards dans Lille. À toi de les trouver !');
    expect(texteInvitationDefi({ prenom: '', n: 1, ville: 'Lille' }))
      .toBe('🦆 Un ami a caché 1 canard dans Lille. À toi de le trouver !');
    expect(texteTempsDefi({ prenom: 'Camille', n: 7, ville: 'Lille', ecouleMs: 151000 }))
      .toBe("🦆 Camille, j'ai trouvé tes 7 canards dans Lille en 2:31 !");
    expect(texteTempsDefi({ prenom: '', n: 1, ville: 'Lille', ecouleMs: 5000 }))
      .toBe("🦆 J'ai trouvé ton canard dans Lille en 0:05 !");
  });

  it('explique chaque rejet', () => {
    expect(messageRejet('version', { ville: 'Lille', prenom: 'Camille' }))
      .toBe('Ce défi a été créé pour une ancienne version de Lille : demande à Camille d’en refaire un.');
    expect(messageRejet('empreinte', { ville: 'Lille' })).toContain('demande à ton ami');
    expect(messageRejet('format', { ville: 'Lille' })).toContain('recharge la page');
    expect(messageRejet('abime', { ville: 'Lille' })).toBe('Ce lien de défi est abîmé.');
    expect(messageRejet('pas-pret', { ville: 'Lille' })).toBe('Le mode défi n’est pas encore prêt pour Lille.');
  });

  it('construit les liens', () => {
    const page = 'https://exemple.io/jeu-canard-3d/?ville=paris&x=1#y';
    expect(lienDefi(page, 'lille', 'AQMk')).toBe('https://exemple.io/jeu-canard-3d/?ville=lille&defi=AQMk');
    expect(lienCacher(page, 'lille')).toBe('https://exemple.io/jeu-canard-3d/?ville=lille&cacher=');
    expect(lienCacher(page, 'lille', 'd1')).toBe('https://exemple.io/jeu-canard-3d/?ville=lille&cacher=d1');
  });
});
