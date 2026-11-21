// Interface par-dessus la scène : accueil, compteur, chrono, aide, messages, écran de fin.

const $ = (id) => document.getElementById(id);

export function duree(ms) {
  const s = Math.round(ms / 1000);
  return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
}

/** Chronomètre : « 3:07 », ou « 1:02:09 » au-delà d'une heure. */
export function chrono(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const ss = String(s % 60).padStart(2, '0');
  return h ? `${h}:${String(m).padStart(2, '0')}:${ss}` : `${m}:${ss}`;
}

/** Précision en pourcentage, ou « — » tant qu'aucun tap n'a été fait. */
export function pourcent(precision, taps) {
  return taps ? `${Math.round(precision * 100)} %` : '—';
}

export function afficherCompteur(trouves, total) {
  $('compteur').textContent = `${trouves} / ${total}`;
}

/** Temps, taps et précision en direct. */
export function afficherStats({ ecouleMs, taps, precision }) {
  $('stat-temps').textContent = chrono(ecouleMs);
  $('stat-taps').textContent = String(taps);
  $('stat-precision').textContent = pourcent(precision, taps);
}

/** Aide contextuelle : dit quoi faire tant que la vue ne révèle pas les canards. */
export function afficherAide(revele) {
  $('aide').textContent = revele
    ? 'Touchez un canard : bec orange, œil noir. Regardez aussi derrière les vitres.'
    : 'Zoomez sur un point jaune pour voir si c’est un canard.';
}

/**
 * Écran d'accueil : une carte par ville.
 * @param villes [{id, embleme, ville, quartier, etat, fini}]
 */
export function afficherAccueil(villes, { choisir, inviter }) {
  $('villes').replaceChildren(...villes.map((v) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'carte-ville';
    b.dataset.ville = v.id;
    const morceau = (classe, texte) => {
      const s = document.createElement('span');
      s.className = classe;
      s.textContent = texte;
      return s;
    };
    b.append(morceau('embleme', v.embleme), morceau('nom', v.ville), morceau('quartier', v.quartier),
      morceau(v.fini ? 'etat fini' : 'etat', v.etat));
    b.onclick = () => choisir(v.id);
    return b;
  }));
  $('inviter').onclick = inviter;
  $('accueil').hidden = false;
  $('hud').hidden = true;
}

/** Barre du haut pendant la partie. */
export function afficherHud({ menu, partager }) {
  $('menu').onclick = menu;
  $('partager').onclick = partager;
  $('hud').hidden = false;
}

export function afficherMessage(texte) {
  $('message').textContent = texte;
  $('message').hidden = !texte;
}

let minuterieBref = null;
/** Message qui s'efface tout seul (« lien copié »…). */
export function afficherBref(texte, ms = 2600) {
  afficherMessage(texte);
  clearTimeout(minuterieBref);
  minuterieBref = setTimeout(() => afficherMessage(''), ms);
}

export function afficherFin({ ecouleMs, taps, precision }, { rejouer, partager, autreVille }) {
  $('fin-temps').textContent = duree(ecouleMs);
  $('fin-taps').textContent = String(taps);
  $('fin-precision').textContent = pourcent(precision, taps);
  $('fin').hidden = false;
  $('rejouer').onclick = rejouer;
  $('partager-score').onclick = partager;
  $('autre-ville').onclick = autreVille;
}
