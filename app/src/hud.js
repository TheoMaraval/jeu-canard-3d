// Interface par-dessus la scène : compteur, aide, messages, écran de fin.

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

/** Menu des villes disponibles (scenes.json). */
export function afficherVilles(scenes, courante, choisir) {
  const menu = $('ville');
  menu.replaceChildren(...scenes.map((s) => {
    const o = document.createElement('option');
    o.value = s.id;
    o.textContent = s.nom;
    o.selected = s.id === courante;
    return o;
  }));
  menu.hidden = scenes.length < 2;
  menu.onchange = () => choisir(menu.value);
}

export function afficherMessage(texte) {
  $('message').textContent = texte;
  $('message').hidden = !texte;
}

export function afficherFin({ ecouleMs, taps, precision }, rejouer) {
  $('fin-temps').textContent = duree(ecouleMs);
  $('fin-taps').textContent = String(taps);
  $('fin-precision').textContent = pourcent(precision, taps);
  $('fin').hidden = false;
  $('rejouer').onclick = rejouer;
}
