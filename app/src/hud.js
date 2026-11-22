// Interface par-dessus la scène : accueil, barre de jeu, aide, chargement, messages, fin.
// Les fonctions de format (`chrono`, `pourcent`) sont pures et testées.

const $ = (id) => document.getElementById(id);
const SVG = 'http://www.w3.org/2000/svg';

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

/** Icône du jeu d'icônes de index.html (`<symbol id="i-…">`). */
function icone(nom, classe = 'ico') {
  const svg = document.createElementNS(SVG, 'svg');
  svg.setAttribute('class', classe);
  svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS(SVG, 'use');
  use.setAttribute('href', `#${nom}`);
  svg.append(use);
  return svg;
}

function element(balise, classe, texte) {
  const e = document.createElement(balise);
  if (classe) e.className = classe;
  if (texte !== undefined) e.textContent = texte;
  return e;
}

// ------------------------------------------------------------------ barre de jeu

export function afficherCompteur(trouves, total) {
  $('compteur-texte').textContent = `${trouves} / ${total}`;
  $('compteur-barre').style.width = `${total ? (100 * trouves) / total : 0}%`;
}

/** Petite fête quand un canard est trouvé : le compteur saute, un « +1 » jaillit. */
export function celebrer() {
  for (const [id, classe] of [['compteur', 'saute'], ['bravo', 'actif']]) {
    const e = $(id);
    e.classList.remove(classe);
    void e.offsetWidth; // relance l'animation même si elle vient de jouer
    e.classList.add(classe);
  }
  navigator.vibrate?.(30);
}

/** Temps, taps et précision en direct. */
export function afficherStats({ ecouleMs, taps, precision }) {
  $('stat-temps').textContent = chrono(ecouleMs);
  $('stat-taps').textContent = String(taps);
  $('stat-precision').textContent = pourcent(precision, taps);
}

export const DUREE_AIDE_MS = 5000;
let minuterieAide = null;

export const AIDE_JEU = {
  loin: 'Zoome sur un point jaune pour voir si c’est un canard.',
  pres: 'Touche le canard : bec orange, œil noir. Regarde aussi derrière les vitres !',
};
export const AIDE_CACHER = {
  loin: 'Zoome, puis tape là où cacher un canard.',
  pres: 'Tape pour cacher un canard ; tape un canard posé pour le retirer.',
};

/**
 * Aide contextuelle, en bas de l'écran. Chaque message reste 5 s puis disparaît ; il ne
 * revient que lorsque le message change (passage du zoom de révélation, dans un sens ou l'autre).
 */
export function afficherAide(revele, textes = AIDE_JEU) {
  const aide = $('aide');
  const texte = revele ? textes.pres : textes.loin;
  if (aide.textContent === texte) return; // déjà montré (ou déjà effacé) : on ne le relance pas
  aide.textContent = texte;
  aide.hidden = false;
  clearTimeout(minuterieAide);
  minuterieAide = setTimeout(() => { aide.hidden = true; }, DUREE_AIDE_MS);
}

export function afficherHud({ menu, partager, son }) {
  $('menu').onclick = menu;
  $('partager').onclick = partager;
  $('son').onclick = son;
  $('hud').hidden = false;
}

/** Bouton haut-parleur : icône et libellé selon l'état du son. */
export function afficherSon(actif) {
  $('son-icone').setAttribute('href', actif ? '#i-son' : '#i-muet');
  $('son').setAttribute('aria-pressed', String(actif));
  $('son').setAttribute('aria-label', actif ? 'Couper le son' : 'Remettre le son');
}

/** Barre du mode « Cacher » : compteur de canards posés, menu et partage ; ni chrono ni son. */
export function afficherHudCacher({ menu, partager }) {
  $('menu').onclick = menu;
  $('partager').onclick = partager;
  $('partager').setAttribute('aria-label', 'Envoyer mon défi');
  $('compteur').setAttribute('aria-label', 'Canards cachés');
  $('stats').hidden = true;
  $('son').hidden = true;
  $('hud').hidden = false;
}

/** Le bouton de partage n'a de sens qu'à partir d'un canard caché. */
export function activerPartage(actif) {
  $('partager').disabled = !actif;
}

/**
 * Panneau « Envoyer le défi » : demande le prénom (facultatif).
 * @returns {Promise<string|null>} le prénom saisi, ou null si le joueur annule
 */
export function demanderPrenom(initial) {
  const panneau = $('panneau-defi');
  const champ = $('prenom');
  const avant = document.activeElement;
  champ.value = initial;
  panneau.hidden = false;
  champ.focus();
  return new Promise((resoudre) => {
    const fermer = (valeur) => {
      panneau.hidden = true;
      panneau.onkeydown = null;
      $('panneau-form').onsubmit = null;
      $('panneau-annuler').onclick = null;
      avant?.focus?.();
      resoudre(valeur);
    };
    $('panneau-form').onsubmit = (e) => {
      e.preventDefault();
      fermer(champ.value);
    };
    $('panneau-annuler').onclick = () => fermer(null);
    panneau.onkeydown = (e) => { if (e.key === 'Escape') fermer(null); };
  });
}

// ----------------------------------------------------------------------- accueil

/**
 * Écran d'accueil : un ticket par ville.
 * @param villes [{id, embleme, couleur, ville, quartier, etat, avance (0–1), fini, record (« 8:12 » ou null)}]
 */
export function afficherAccueil(villes, { choisir, inviter, cacher }) {
  // « Cacher mes canards » : les tickets servent alors à choisir la ville où cacher
  let modeCacher = false;
  const majMode = () => {
    $('titre-villes').textContent = modeCacher ? 'Où cacher tes canards ?' : 'Choisis ta ville';
    $('cacher-texte').textContent = modeCacher ? 'Annuler' : 'Cacher mes canards';
    $('cacher').classList.toggle('secondaire', modeCacher);
    $('accueil').classList.toggle('mode-cacher', modeCacher);
  };
  majMode(); // ré-appelée (après un défi refusé) : repart du mode normal
  $('cacher').onclick = () => {
    modeCacher = !modeCacher;
    majMode();
    if (modeCacher) $('titre-villes').scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  $('villes').replaceChildren(...villes.map((v) => {
    const b = element('button', `carte-ville${v.fini ? ' fini' : ''}${v.avance ? '' : ' neuve'}`);
    b.type = 'button';
    b.dataset.ville = v.id;
    b.style.setProperty('--couleur', v.couleur);
    b.setAttribute('aria-label', `${v.ville}, ${v.quartier} : ${v.etat}${v.record ? `, record ${v.record}` : ''}`);
    if (v.record) {
      const record = element('span', 'record');
      record.append(icone('i-etoile'), element('span', '', v.record));
      record.title = 'Ton record';
      b.append(record);
    }

    const texte = element('span', 'texte');
    texte.append(element('span', 'nom', v.ville), element('span', 'quartier', v.quartier));
    const go = element('span', 'go');
    go.append(icone('i-fleche'));
    const jauge = element('span', 'jauge');
    const plein = element('span');
    jauge.style.setProperty('--avance', String(v.avance));
    jauge.append(plein);
    const etat = element('span', 'etat');
    etat.append(jauge, element('span', 'libelle', v.etat));

    b.append(element('span', 'embleme', v.embleme), texte, go, etat);
    b.onclick = () => (modeCacher ? cacher(v.id) : choisir(v.id));
    return b;
  }));
  $('inviter').onclick = inviter;
  $('accueil').hidden = false;
  $('hud').hidden = true;
  $('aide').hidden = true;
}

/**
 * Section « Mes défis » de l'accueil, masquée si la liste est vide.
 * @param defis [{id, embleme, couleur, ville, detail (« 7 canards · 21/11 »), valable}]
 */
export function afficherMesDefis(defis, { envoyer, modifier, supprimer }) {
  $('mes-defis').hidden = !defis.length;
  $('liste-defis').replaceChildren(...defis.map((d) => {
    const carte = element('div', `carte-defi${d.valable ? '' : ' perime'}`);
    carte.style.setProperty('--couleur', d.couleur);
    const texte = element('span', 'texte');
    texte.append(
      element('span', 'nom', d.ville),
      element('span', 'detail', d.valable ? d.detail : `${d.detail} · plus valable`),
    );
    const actions = element('span', 'actions-defi');
    const bouton = (libelle, nomIcone, action, classe = '') => {
      const b = element('button', `mini-bouton ${classe}`.trim());
      b.type = 'button';
      b.setAttribute('aria-label', `${libelle} le défi de ${d.ville}`);
      b.append(icone(nomIcone), element('span', '', libelle));
      b.onclick = () => action(d.id);
      return b;
    };
    if (d.valable) actions.append(bouton('Envoyer', 'i-partager', envoyer), bouton('Modifier', 'i-tap', modifier));
    actions.append(bouton('Supprimer', 'i-corbeille', supprimer, 'discret'));
    carte.append(element('span', 'embleme', d.embleme), texte, actions);
    return carte;
  }));
}

// --------------------------------------------------------- chargement, messages

export function afficherChargement(actif, texte = 'Chargement du quartier…') {
  $('chargement-texte').textContent = texte;
  $('chargement').hidden = !actif;
}

export function afficherMessage(texte, { erreur = false } = {}) {
  const m = $('message');
  m.textContent = texte;
  m.classList.toggle('erreur', erreur);
  m.hidden = !texte;
}

let minuterieBref = null;
/** Message qui s'efface tout seul (« lien copié »…). */
export function afficherBref(texte, ms = 2600) {
  afficherMessage(texte);
  clearTimeout(minuterieBref);
  minuterieBref = setTimeout(() => afficherMessage(''), ms);
}

// -------------------------------------------------------------------------- fin

function lancerConfettis() {
  const couleurs = ['#ffd21e', '#ff7a00', '#2fb36a', '#3f6fd8', '#e0452f', '#c93f8e'];
  const boite = $('confettis');
  boite.replaceChildren(...Array.from({ length: 60 }, (_, i) => {
    const c = element('i');
    c.style.left = `${Math.random() * 100}%`;
    c.style.background = couleurs[i % couleurs.length];
    c.style.setProperty('--duree', `${1.8 + Math.random() * 1.6}s`);
    c.style.setProperty('--delai', `${Math.random() * 0.6}s`);
    c.style.setProperty('--tour', `${(Math.random() < 0.5 ? -1 : 1) * (360 + Math.random() * 540)}deg`);
    return c;
  }));
}

/**
 * @param stats {ecouleMs, taps, precision}
 * @param medaille {titre, etoiles} (voir titreFin dans partage.js)
 * @param record {texte, nouveau} ou null (voir texteRecord dans partage.js)
 * @param actions {rejouer, partager, autreVille, cacherAMonTour (défi seulement)}
 * @param textes {sousTitre, libellePartager}
 */
export function afficherFin(
  { ecouleMs, taps, precision }, medaille, record,
  { rejouer, partager, autreVille, cacherAMonTour = null },
  { sousTitre = '', libellePartager = 'Partager mon score' } = {},
) {
  $('fin-sous-titre').textContent = sousTitre;
  $('partager-score-texte').textContent = libellePartager;
  const tour = $('cacher-tour');
  tour.hidden = !cacherAMonTour;
  tour.onclick = cacherAMonTour;
  const r = $('fin-record');
  r.textContent = record?.texte ?? '';
  r.classList.toggle('nouveau', Boolean(record?.nouveau));
  r.hidden = !record;
  $('fin-titre').textContent = medaille.titre;
  $('fin-etoiles').replaceChildren(...[1, 2, 3].map((n) => icone('i-etoile', n <= medaille.etoiles ? 'ico pleine' : 'ico')));
  $('fin-temps').textContent = chrono(ecouleMs);
  $('fin-taps').textContent = String(taps);
  $('fin-precision').textContent = pourcent(precision, taps);
  $('aide').hidden = true;
  $('fin').hidden = false;
  $('rejouer').onclick = rejouer;
  $('partager-score').onclick = partager;
  $('autre-ville').onclick = autreVille;
  lancerConfettis();
}
