// Rendu Three.js : charge une ville, instancie canards et leurres, applique la vue.
// Seul module (avec main.js) qui dépend de Three.js et du DOM.
//
// Style « dessin » : aplats de couleur en trois paliers (toon), ombres légères,
// et deux sortes de traits d'encre :
//   - les arêtes vives du décor (EdgesGeometry) : contours des fenêtres, toits, trottoirs ;
//   - une coque noire retournée autour de tout : silhouettes des rondeurs (arbres,
//     passants, canards), dont l'épaisseur reste constante à l'écran.
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

/** Matériau « dessin » à partir d'un matériau glTF. */
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

/** Maillages d'un nœud glTF : lui-même s'il n'a qu'un matériau, sinon ses enfants. */
function maillages(racine, nom) {
  const noeud = racine.getObjectByName(nom);
  if (!noeud) throw new Error(`props.glb ne contient pas « ${nom} »`);
  return noeud.isMesh ? [noeud] : noeud.children.filter((c) => c.isMesh);
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
  const [placements, quartier, props] = await Promise.all([
    json(`${dossier}/placements.json`),
    loader.loadAsync(`${dossier}/quartier.glb`),
    loader.loadAsync('props.glb'),
  ]);
  const k = placements.echelle ?? 1;
  const gabarit = placements.gabarit ?? 0.5;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#f3ead6'); // papier
  const epaisseur = { value: 0.02 };
  const coque = materiauCoque(epaisseur);

  // --- décor ----------------------------------------------------------------
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
  scene.add(traits, new THREE.Mesh(fusion, coque));

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

  // --- canards et leurres ---------------------------------------------------
  function matrice(objet, facteur = 1) {
    const [x, y, z] = objet.position;
    const e = k * facteur;
    return new THREE.Matrix4().compose(
      new THREE.Vector3(x, y, z),
      new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), objet.rotation),
      new THREE.Vector3(e, e, e),
    );
  }

  /** Un InstancedMesh par primitive ; `teinte` rend le jaune recolorable par instance. */
  function instancier(nom, objets, teinte = false) {
    return maillages(props.scene, nom).map((m) => {
      const recolorable = teinte && m.material.name === MAT_JAUNE;
      const jaune = m.material.color.clone();
      const materiau = dessin(m.material);
      if (recolorable) materiau.color.set('#ffffff'); // la couleur vient alors de chaque instance
      const im = new THREE.InstancedMesh(m.geometry, materiau, objets.length);
      objets.forEach((o, i) => {
        im.setMatrixAt(i, matrice(o));
        if (recolorable) im.setColorAt(i, jaune);
      });
      im.castShadow = true;
      im.receiveShadow = true;
      im.userData.recolorable = recolorable;
      const contour = new THREE.InstancedMesh(m.geometry, coque, objets.length);
      contour.instanceMatrix = im.instanceMatrix; // mêmes positions, mêmes animations
      im.add(contour); // enfant : suit la visibilité du maillage
      return im;
    });
  }

  const canards = placements.objets.filter((o) => o.type === TYPE_CANARD);
  const pres = instancier(TYPE_CANARD, canards, true);
  const loin = instancier(TYPE_CANARD_LOIN, canards, true);
  scene.add(...pres, ...loin);
  const parType = new Map();
  for (const o of placements.objets) {
    if (o.type === TYPE_CANARD) continue;
    if (!parType.has(o.type)) parType.set(o.type, []);
    parType.get(o.type).push(o);
  }
  for (const [type, objets] of parType) scene.add(...instancier(type, objets));

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
    for (const m of pres) m.visible = revele;
    for (const m of loin) m.visible = !revele;
    demanderRendu();
  }

  function teindre(index, couleur) {
    for (const m of [...pres, ...loin]) {
      if (!m.userData.recolorable) continue;
      m.setColorAt(index, couleur);
      m.instanceColor.needsUpdate = true;
    }
  }

  function echelle(index, facteur) {
    const mat = matrice(canards[index], facteur);
    for (const m of [...pres, ...loin]) {
      m.setMatrixAt(index, mat);
      m.instanceMatrix.needsUpdate = true;
    }
  }

  /** Passe un canard en vert ; `rebond` joue une courte animation. */
  function marquerTrouve(id, rebond = false) {
    const index = canards.findIndex((c) => c.id === id);
    if (index < 0) return;
    teindre(index, VERT_TROUVE);
    if (!rebond) {
      demanderRendu();
      return;
    }
    const debut = performance.now();
    const pas = (t) => {
      const a = Math.min(1, (t - debut) / 380);
      echelle(index, 1 + 0.7 * Math.sin(Math.PI * a));
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
    stats: () => ({ ...renderer.info.render, objets: placements.objets.length }),
  };
}
