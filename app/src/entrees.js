// Gestes : un doigt ou la souris déplace, deux doigts ou la molette zooment, un appui bref tape.
// Ne connaît ni la vue ni le jeu : il appelle trois fonctions.

const TAP_DISTANCE_PX = 10;
const TAP_DUREE_MS = 500;

export function ecouterEntrees(cible, { deplacer, zoomer, taper }) {
  const doigts = new Map(); // pointerId -> {x, y}
  let depart = null; // {x, y, t} du geste à un doigt en cours
  let aBouge = false;
  let ecart = 0; // distance entre les deux doigts au dernier événement

  const pos = (e) => {
    const r = cible.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };
  const deux = () => [...doigts.values()];
  const milieu = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });

  cible.addEventListener('pointerdown', (e) => {
    cible.setPointerCapture(e.pointerId);
    doigts.set(e.pointerId, pos(e));
    if (doigts.size === 1) {
      depart = { ...pos(e), t: performance.now() };
      aBouge = false;
    } else {
      depart = null; // un deuxième doigt : ce n'est plus un tap
      const [a, b] = deux();
      ecart = Math.hypot(a.x - b.x, a.y - b.y);
    }
  });

  cible.addEventListener('pointermove', (e) => {
    const avant = doigts.get(e.pointerId);
    if (!avant) return;
    const p = pos(e);
    if (doigts.size === 1) {
      if (depart && Math.hypot(p.x - depart.x, p.y - depart.y) > TAP_DISTANCE_PX) aBouge = true;
      if (aBouge) deplacer(p.x - avant.x, p.y - avant.y);
      // tant que le doigt n'a pas dépassé le seuil, on ne bouge pas : un tap reste net
      if (!aBouge) return;
      doigts.set(e.pointerId, p);
    } else if (doigts.size === 2) {
      const [a0, b0] = deux();
      const m0 = milieu(a0, b0);
      doigts.set(e.pointerId, p);
      const [a, b] = deux();
      const m = milieu(a, b);
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      deplacer(m.x - m0.x, m.y - m0.y);
      if (ecart > 0 && d > 0) zoomer(d / ecart, m);
      ecart = d;
    }
  });

  const fin = (e) => {
    if (!doigts.has(e.pointerId)) return;
    const p = pos(e);
    doigts.delete(e.pointerId);
    if (e.type === 'pointerup' && depart && !aBouge && doigts.size === 0
        && performance.now() - depart.t <= TAP_DUREE_MS) {
      taper(p);
    }
    if (doigts.size === 0) depart = null;
  };
  cible.addEventListener('pointerup', fin);
  cible.addEventListener('pointercancel', fin);

  cible.addEventListener('wheel', (e) => {
    e.preventDefault();
    // ctrlKey : pincement sur pavé tactile, deltas plus petits
    zoomer(Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0015)), pos(e));
  }, { passive: false });
}
