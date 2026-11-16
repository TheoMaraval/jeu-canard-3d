// Interface par-dessus la scène : compteur, aide, messages, écran de fin.

const $ = (id) => document.getElementById(id);

export function duree(ms) {
  const s = Math.round(ms / 1000);
  return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
}

export function afficherCompteur(trouves, total) {
  $('compteur').textContent = `${trouves} / ${total}`;
}

/** Aide contextuelle : dit quoi faire tant que la vue ne révèle pas les canards. */
export function afficherAide(revele) {
  $('aide').textContent = revele
    ? 'Touchez un canard : bec orange, œil noir.'
    : 'Zoomez sur un point jaune pour voir si c’est un canard.';
}

export function afficherMessage(texte) {
  $('message').textContent = texte;
  $('message').hidden = !texte;
}

export function afficherFin({ ecouleMs, taps, precision }, rejouer) {
  $('fin-temps').textContent = duree(ecouleMs);
  $('fin-taps').textContent = String(taps);
  $('fin-precision').textContent = `${Math.round(precision * 100)} %`;
  $('fin').hidden = false;
  $('rejouer').onclick = rejouer;
}
