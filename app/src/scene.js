// Rendu Three.js : charge une ville, instancie le kit, les canards et les leurres, applique la vue.
// Seul module (avec main.js) qui dépend de Three.js et du DOM.
//
// Style « dessin » : aplats de couleur en trois paliers (toon), ombres légères,
// et deux sortes de traits d'encre :
//   - les arêtes vives du bâti (EdgesGeometry) : contours des fenêtres, toits, trottoirs ;
//   - une coque noire retournée autour de tout : silhouettes des rondeurs (arbres,
//     passants, canards), dont l'épaisseur reste constante à l'écran.
//
// Tout ce qui est instancié (kit.glb, props.glb) passe par `instancier` : un seul maillage
// par modèle, dont les matériaux T_<rôle> prennent une teinte propre à chaque instance.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { axesCamera, limitesCarte } from './vue.js';

const TYPE_CANARD = 'Canard';
const TYPE_CANARD_LOIN = 'Canard_Loin';
const MAT_JAUNE = 'MAT_Jaune';
const MAT_VERRE = 'verre';
const ENCRE = '#1c1b22';
const VERT_TROUVE = new THREE.Color('#35c759');
const HAUTEUR_CENTRE = 0.22; // centre d'un objet au-dessus de son point d'appui, à l'échelle 1 (m)
const DISTANCE_CAMERA = 300;
const ANGLE_ARETE = 50; // degrés : en dessous, pas de trait (flancs des cylindres, sphères)
const ROLES_MAX = 4;
const SEUIL_CONTOURS_PPM = 12; // en dessous, les coques des modèles ne sont pas dessinées
const SEUIL_DECOUPE = 80; // au-delà de ce nombre d'instances, un modèle est découpé par zones
const TAILLE_ZONE = 40; // mètres

// Ombrage en trois paliers nets (cel-shading) au lieu d'un dégradé.
const PALIERS = new THREE.DataTexture(new Uint8Array([150, 215, 255]), 3, 1, THREE.RedFormat);
PALIERS.minFilter = THREE.NearestFilter;
PALIERS.magFilter = THREE.NearestFilter;
PALIERS.needsUpdate = true;

async function json(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} introuvable (${r.status})`);
  return r.json().catch(() => {
    throw new Error(`${url} est absent ou illisible : relancer blender/tout_generer.sh`);
  });
}

/** Matériau « dessin » du bâti à partir d'un matériau glTF. */
function dessin(source) {
  if (source.name === MAT_VERRE) {
    return new THREE.MeshBasicMaterial({
      name: MAT_VERRE, color: '#6fc3ee', transparent: true, opacity: 0.42, depthWrite: false,
    });
  }
  return new THREE.MeshToonMaterial({
    gradientMap: PALIERS,
    name: source.name,
    color: source.color,
    polygonOffset: true, // recule les faces d'un cheveu : les traits d'arête passent devant
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1,
  });
}

/** Matériau des modèles instanciés : couleur par sommet, ou teinte d'instance selon le rôle. */
function materiauInstances() {
  const m = new THREE.MeshToonMaterial({ gradientMap: PALIERS, vertexColors: true });
  m.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
attribute float role;
attribute vec3 tint1;
attribute vec3 tint2;
attribute vec3 tint3;
attribute vec3 tint4;`)
      .replace('#include <color_vertex>', `#include <color_vertex>
  if (role > 3.5) vColor.rgb = tint4;
  else if (role > 2.5) vColor.rgb = tint3;
  else if (role > 1.5) vColor.rgb = tint2;
  else if (role > 0.5) vColor.rgb = tint1;`);
  };
  return m;
}

/** Matériau de coque : faces arrière noires, gonflées de `epaisseur` mètres le long des normales. */
function materiauCoque(epaisseur) {
  const m = new THREE.MeshBasicMaterial({ color: ENCRE, side: THREE.BackSide });
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uEpaisseur = epaisseur;
    shader.vertexShader = `uniform float uEpaisseur;\n${shader.vertexShader}`.replace(
      '#include <begin_vertex>',
      '#include <begin_vertex>\n  transformed += normalize(normal) * uEpaisseur;',
    );
  };
  return m;
}

/** Rôle de teinte d'un matériau : T_haut -> "haut", MAT_Jaune -> "jaune", sinon null (couleur fixe). */
function roleDe(materiau) {
  if (materiau.name.startsWith('T_')) return materiau.name.slice(2);
  return materiau.name === MAT_JAUNE ? 'jaune' : null;
}

/**
 * Fusionne les primitives d'un modèle glTF en une géométrie : attribut `color` (couleur
 * fixe du matériau) et attribut `role` (0 = fixe, 1..4 = teinte d'instance).
 */
function fusionnerModele(racine, nom) {
  const noeud = racine.getObjectByName(nom);
  if (!noeud) throw new Error(`modèle « ${nom} » absent du fichier glb`);
  const parties = noeud.isMesh ? [noeud] : noeud.children.filter((c) => c.isMesh);
  const roles = [];
  const defauts = [];
  const geometrie = mergeGeometries(parties.map((m) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', m.geometry.getAttribute('position').clone());
    g.setAttribute('normal', m.geometry.getAttribute('normal').clone());
    g.setIndex(m.geometry.getIndex().clone());
    const n = g.getAttribute('position').count;
    const role = roleDe(m.material);
    let index = 0;
    if (role) {
      if (!roles.includes(role)) {
        roles.push(role);
        defauts.push(m.material.color.clone());
      }
      index = roles.indexOf(role) + 1;
    }
    const c = m.material.color;
    const couleurs = new Float32Array(n * 3);
    for (let i = 0; i < n; i += 1) couleurs.set([c.r, c.g, c.b], i * 3);
    g.setAttribute('color', new THREE.BufferAttribute(couleurs, 3));
    g.setAttribute('role', new THREE.BufferAttribute(new Float32Array(n).fill(index), 1));
    return g;
  }));
  if (roles.length > ROLES_MAX) throw new Error(`${nom} : ${roles.length} teintes, ${ROLES_MAX} au plus`);
  return { geometrie, roles, defauts };
}

export async function chargerScene(canvas, info) {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  } catch {
    throw new Error('WebGL est indisponible sur cet appareil ou ce navigateur.');
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.shadowMap.autoUpdate = false; // scène statique : l'ombre est calculée une seule fois

  const dossier = `scenes/${info.id}`;
  const loader = new GLTFLoader();
  const [placements, decor, quartier, props, kit] = await Promise.all([
    json(`${dossier}/placements.json`),
    json(`${dossier}/decor.json`),
    loader.loadAsync(`${dossier}/quartier.glb`),
    loader.loadAsync('props.glb'),
    loader.loadAsync('kit.glb'),
  ]);
  const k = placements.echelle ?? 1;
  const gabarit = placements.gabarit ?? 0.5;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#f6ecd4'); // papier, comme --papier dans style.css
  const epaisseur = { value: 0.02 };
  const coque = materiauCoque(epaisseur);
  const teinte = materiauInstances();

  // --- bâti -------------------------------------------------------------------
  quartier.scene.updateMatrixWorld(true);
  const opaques = [];
  quartier.scene.traverse((o) => {
    if (!o.isMesh) return;
    const verre = o.material.name === MAT_VERRE;
    o.material = dessin(o.material);
    o.castShadow = !verre;
    o.receiveShadow = !verre;
    if (verre) o.renderOrder = 2; // après tout ce qui est opaque, canards compris
    else opaques.push(o);
  });
  scene.add(quartier.scene);

  const fusion = mergeGeometries(opaques.map((o) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', o.geometry.getAttribute('position').clone());
    g.setAttribute('normal', o.geometry.getAttribute('normal').clone());
    g.setIndex(o.geometry.getIndex().clone());
    return g.applyMatrix4(o.matrixWorld);
  }));
  const traits = new THREE.LineSegments(
    new THREE.EdgesGeometry(fusion, ANGLE_ARETE),
    new THREE.LineBasicMaterial({ color: ENCRE, transparent: true, opacity: 0.6 }),
  );
  scene.add(traits); // le bâti n'a pas de coque : ses arêtes suffisent
  const contours = []; // coques des modèles instanciés, masquées en vue d'ensemble

  scene.add(new THREE.HemisphereLight('#ffffff', '#efe6d8', 2.1)); // sol presque blanc : murs en aplat
  const soleil = new THREE.DirectionalLight('#fff4e0', 1.0);
  soleil.position.set(-70, 130, 90); // sud-ouest : ombres portées vers la droite de l'écran
  soleil.castShadow = true;
  soleil.shadow.mapSize.set(2048, 2048);
  Object.assign(soleil.shadow.camera, { left: -95, right: 95, top: 95, bottom: -95, near: 1, far: 400 });
  soleil.shadow.bias = -0.0004;
  soleil.shadow.normalBias = 0.04;
  soleil.shadow.intensity = 0.4; // ombre de dessin, pas de photo
  scene.add(soleil);

  // --- modèles instanciés -------------------------------------------------------
  const matrice = ({ p, r, s }, facteur = 1) => new THREE.Matrix4().compose(
    new THREE.Vector3(p[0], p[1], p[2]),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), r),
    new THREE.Vector3(s * facteur, s * facteur, s * facteur),
  );

  /**
   * Un InstancedMesh (plus sa coque) pour toutes les instances d'un modèle.
   * @param instances [{p, r, s, c: {rôle: '#hex'}}]
   */
  function instancier(racine, nom, instances) {
    const modele = fusionnerModele(racine, nom);
    if (instances.length <= SEUIL_DECOUPE) return creer(modele, modele.geometrie, instances);
    // Modèle très répété (passants, arbres) : un maillage par zone de la carte. De près,
    // seules les zones à l'écran sont dessinées (élimination par le champ de la caméra).
    const zones = new Map();
    for (const inst of instances) {
      const cle = `${Math.floor(inst.p[0] / TAILLE_ZONE)}:${Math.floor(inst.p[2] / TAILLE_ZONE)}`;
      if (!zones.has(cle)) zones.set(cle, []);
      zones.get(cle).push(inst);
    }
    for (const groupe of zones.values()) creer(modele, modele.geometrie.clone(), groupe);
    return null;
  }

  function creer({ roles, defauts }, geometrie, instances) {
    const n = instances.length;
    const tints = [];
    for (let j = 0; j < ROLES_MAX; j += 1) {
      const a = new THREE.InstancedBufferAttribute(new Float32Array(n * 3), 3);
      geometrie.setAttribute(`tint${j + 1}`, a);
      tints.push(a);
    }
    const im = new THREE.InstancedMesh(geometrie, teinte, n);
    const couleur = new THREE.Color();
    instances.forEach((inst, i) => {
      im.setMatrixAt(i, matrice(inst));
      roles.forEach((role, j) => {
        const hex = inst.c?.[role];
        if (hex) couleur.set(hex);
        else couleur.copy(defauts[j]);
        tints[j].setXYZ(i, couleur.r, couleur.g, couleur.b);
      });
    });
    im.castShadow = true;
    im.receiveShadow = true;
    const contour = new THREE.InstancedMesh(geometrie, coque, n);
    contour.instanceMatrix = im.instanceMatrix; // mêmes positions, mêmes animations
    im.add(contour); // enfant : suit la visibilité du maillage
    contours.push(contour);
    scene.add(im);
    /** Change la teinte d'un rôle pour une instance. */
    im.userData.teindre = (i, role, c) => {
      const j = roles.indexOf(role);
      if (j < 0) return;
      tints[j].setXYZ(i, c.r, c.g, c.b);
      tints[j].needsUpdate = true;
    };
    return im;
  }

  const parType = (liste) => {
    const m = new Map();
    for (const o of liste) {
      if (!m.has(o.type)) m.set(o.type, []);
      m.get(o.type).push(o);
    }
    return m;
  };
  for (const [type, instances] of parType(decor.instances)) instancier(kit.scene, type, instances);

  const enInstance = (o) => ({ p: o.position, r: o.rotation, s: k });
  const canards = placements.objets.filter((o) => o.type === TYPE_CANARD);
  const pres = instancier(props.scene, TYPE_CANARD, canards.map(enInstance));
  const loin = instancier(props.scene, TYPE_CANARD_LOIN, canards.map(enInstance));
  for (const [type, objets] of parType(placements.objets.filter((o) => o.type !== TYPE_CANARD))) {
    instancier(props.scene, type, objets.map(enInstance));
  }

  // --- caméra orthographique à angle fixe -----------------------------------
  const versCamera = placements.camera.vers_camera;
  const axes = axesCamera(versCamera);
  const hauteurMax = new THREE.Box3().setFromObject(quartier.scene).max.y;
  const limites = limitesCarte(placements.taille, hauteurMax, axes, gabarit);
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 900);
  const base = new THREE.Vector3(...versCamera).multiplyScalar(DISTANCE_CAMERA);
  camera.position.copy(base);
  camera.lookAt(0, 0, 0); // l'orientation ne change plus : la vue ne fait que translater
  const vDroite = new THREE.Vector3(...axes.droite);
  const vHaut = new THREE.Vector3(...axes.haut);

  let enAttente = false;
  function demanderRendu() {
    if (enAttente) return;
    enAttente = true;
    requestAnimationFrame(() => {
      enAttente = false;
      renderer.render(scene, camera);
    });
  }

  function appliquerVue(vue, ecran, revele) {
    renderer.setSize(ecran.w, ecran.h, false);
    const dw = ecran.w / (2 * vue.ppm);
    const dh = ecran.h / (2 * vue.ppm);
    Object.assign(camera, { left: -dw, right: dw, top: dh, bottom: -dh });
    camera.updateProjectionMatrix();
    camera.position.copy(base).addScaledVector(vDroite, vue.u).addScaledVector(vHaut, vue.v);
    // traits : fins et discrets en vue d'ensemble, francs de près
    const px = Math.min(1.5, Math.max(0.45, vue.ppm / 45));
    epaisseur.value = px / vue.ppm;
    traits.material.opacity = Math.min(0.85, Math.max(0.22, 0.15 + vue.ppm / 70));
    // en vue d'ensemble un contour ferait moins d'un pixel : on économise la moitié des triangles
    const avecContours = vue.ppm >= SEUIL_CONTOURS_PPM;
    for (const c of contours) c.visible = avecContours;
    pres.visible = revele;
    loin.visible = !revele;
    demanderRendu();
  }

  /** Passe un canard en vert ; `rebond` joue une courte animation. */
  function marquerTrouve(id, rebond = false) {
    const index = canards.findIndex((c) => c.id === id);
    if (index < 0) return;
    for (const m of [pres, loin]) m.userData.teindre(index, 'jaune', VERT_TROUVE);
    if (!rebond) {
      demanderRendu();
      return;
    }
    const debut = performance.now();
    const pas = (t) => {
      const a = Math.min(1, (t - debut) / 380);
      const mat = matrice(enInstance(canards[index]), 1 + 0.7 * Math.sin(Math.PI * a));
      for (const m of [pres, loin]) {
        m.setMatrixAt(index, mat);
        m.instanceMatrix.needsUpdate = true;
      }
      demanderRendu();
      if (a < 1) requestAnimationFrame(pas);
    };
    requestAnimationFrame(pas);
  }

  renderer.shadowMap.needsUpdate = true;

  return {
    info,
    axes,
    limites,
    gabarit,
    appliquerVue,
    marquerTrouve,
    demanderRendu,
    /** Centres des canards dans le repère du monde, pour le picking. */
    canards: canards.map((c) => ({
      id: c.id, lieu: c.lieu, centre: [c.position[0], c.position[1] + HAUTEUR_CENTRE * k, c.position[2]],
    })),
    stats: () => ({ ...renderer.info.render, objets: placements.objets.length, decor: decor.instances.length }),
  };
}
