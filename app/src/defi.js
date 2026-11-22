// Défis « Cacher mes canards » : le code du lien, ses rejets, les textes et les liens.
// Fonctions pures.
//
// Le code est en base64url, sur des octets :
//   format (1) | version de la ville (1) | empreinte des cachettes (3) | nombre n (1)
//   | numéros des cachettes (2 × n) | prénom en UTF-8 (le reste)
import { chrono } from './hud.js';

export const FORMAT = 1;
export const MAX_CANARDS = 30;
export const MAX_PRENOM = 20;
const ENTETE = 6;
// 30 canards et 20 émoji de 4 octets font 195 caractères : au-delà, le lien n'est pas de nous
const MAX_CODE = 200;

function versBase64url(octets) {
  let binaire = '';
  for (const o of octets) binaire += String.fromCharCode(o);
  return btoa(binaire).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function depuisBase64url(texte) {
  if (typeof texte !== 'string' || texte.length > MAX_CODE || !/^[A-Za-z0-9_-]+$/.test(texte)) return null;
  const b64 = texte.replace(/-/g, '+').replace(/_/g, '/');
  try {
    return Uint8Array.from(atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4)), (c) => c.charCodeAt(0));
  } catch {
    return null;
  }
}

/**
 * Prénom sans caractères de contrôle, inversions de sens ni invisibles, sans espaces autour, 20 points de code au plus.
 * Le U+200D (liant des émoji composés) est gardé.
 */
export const nettoyerPrenom = (prenom) => [...String(prenom ?? '')
  .replace(/[\p{Cc}\u061C\u200B\u200C\u200E\u200F\u2028\u2029\u202A-\u202E\u2066-\u2069\uFEFF]/gu, '').trim()]
  .slice(0, MAX_PRENOM).join('');

/** @param defi {version, empreinte (4 caractères base 36), numeros, prenom} */
export function encoderDefi({ version, empreinte, numeros, prenom = '' }) {
  if (typeof empreinte !== 'string' || !/^[0-9a-z]{4}$/.test(empreinte)) {
    throw new Error(`empreinte invalide : ${empreinte}`);
  }
  if (!Array.isArray(numeros) || numeros.length < 1 || numeros.length > MAX_CANARDS
    || !numeros.every((n) => Number.isInteger(n) && n >= 0 && n <= 65535)) {
    throw new Error('numéros de cachettes invalides');
  }
  const e = parseInt(empreinte, 36);
  const octets = [FORMAT, version & 255, (e >> 16) & 255, (e >> 8) & 255, e & 255, numeros.length];
  for (const n of numeros) octets.push((n >> 8) & 255, n & 255);
  octets.push(...new TextEncoder().encode(nettoyerPrenom(prenom)));
  return versBase64url(octets);
}

/** @returns {{ok: true, defi}} ou {{ok: false, raison: 'abime'|'format'}} */
export function decoderDefi(code) {
  const o = depuisBase64url(code);
  if (!o || !o.length) return { ok: false, raison: 'abime' };
  if (o[0] !== FORMAT) return { ok: false, raison: 'format' };
  const n = o[5];
  if (o.length < ENTETE || n < 1 || n > MAX_CANARDS || o.length < ENTETE + 2 * n) return { ok: false, raison: 'abime' };
  const valeur = (o[2] << 16) | (o[3] << 8) | o[4];
  if (valeur >= 36 ** 4) return { ok: false, raison: 'abime' }; // 5 caractères en base 36 : pas une empreinte de chez nous
  const numeros = [];
  for (let i = 0; i < n; i += 1) numeros.push((o[ENTETE + 2 * i] << 8) | o[ENTETE + 2 * i + 1]);
  if (new Set(numeros).size !== n) return { ok: false, raison: 'abime' };
  let prenom;
  try {
    prenom = new TextDecoder('utf-8', { fatal: true }).decode(o.slice(ENTETE + 2 * n));
  } catch {
    return { ok: false, raison: 'abime' };
  }
  const empreinte = valeur.toString(36).padStart(4, '0');
  return { ok: true, defi: { version: o[1], empreinte, numeros, prenom: nettoyerPrenom(prenom) } };
}

/**
 * Le défi correspond-il aux cachettes chargées ?
 * @param ville {version, empreinte, nombre} (nombre = cachettes dans cachettes.json)
 * @returns null, ou la raison du rejet : 'format' | 'version' | 'empreinte' | 'abime'
 */
export function verifierDefi(defi, { version, empreinte, nombre }) {
  // défi plus récent que nos fichiers (cache de Pages, vieil onglet) : recharger, pas « ancienne version »
  if (defi.version > (version & 255)) return 'format';
  if (defi.version !== (version & 255)) return 'version';
  if (defi.empreinte !== empreinte) return 'empreinte';
  if (defi.numeros.some((n) => n >= nombre)) return 'abime';
  return null;
}

// ----------------------------------------------------------------------- textes

const VOYELLE = /^[aeiouyàâäéèêëîïôöùûü]/i;

/** « de Camille », « d’Amélie », ou « d’un ami » sans prénom. */
export const deQui = (prenom) => (prenom ? `${VOYELLE.test(prenom) ? 'd’' : 'de '}${prenom}` : 'd’un ami');

const canards = (n) => `${n} canard${n > 1 ? 's' : ''}`;

export const titreDefi = (prenom) => `Le défi ${deQui(prenom)}`;
export const titreFinDefi = (prenom) => (prenom ? `Défi ${deQui(prenom)} réussi !` : 'Défi réussi !');
export const libelleRenvoi = (prenom) => (prenom ? `Envoyer mon temps à ${prenom}` : 'Envoyer mon temps');

export const texteInvitationDefi = ({ prenom, n, ville }) =>
  `🦆 ${prenom || 'Un ami'} a caché ${canards(n)} dans ${ville}. À toi de ${n > 1 ? 'les' : 'le'} trouver !`;

export function texteTempsDefi({ prenom, n, ville, ecouleMs }) {
  const quoi = n > 1 ? `tes ${n} canards` : 'ton canard';
  return `🦆 ${prenom ? `${prenom}, j'ai` : "J'ai"} trouvé ${quoi} dans ${ville} en ${chrono(ecouleMs)} !`;
}

/** Message affiché quand un défi (ou le mode « Cacher ») est impossible. */
export function messageRejet(raison, { ville, prenom = '' }) {
  if (raison === 'format') return 'Ce défi vient d’une version plus récente du jeu : recharge la page.';
  if (raison === 'version' || raison === 'empreinte') {
    return `Ce défi a été créé pour une ancienne version de ${ville} : demande à ${prenom || 'ton ami'} d’en refaire un.`;
  }
  if (raison === 'pas-pret') return `Le mode défi n’est pas encore prêt pour ${ville}.`;
  return 'Ce lien de défi est abîmé.';
}

// ------------------------------------------------------------------------ liens

function lienVille(adresse, ville, parametre, valeur) {
  const url = new URL(adresse);
  url.search = '';
  url.hash = '';
  url.searchParams.set('ville', ville);
  url.searchParams.set(parametre, valeur);
  return url.toString();
}

export const lienDefi = (adresse, ville, code) => lienVille(adresse, ville, 'defi', code);

/** Écran « Cacher » : `id` vide pour un nouveau défi, sinon celui de « Mes défis » à modifier. */
export const lienCacher = (adresse, ville, id = '') => lienVille(adresse, ville, 'cacher', id);
