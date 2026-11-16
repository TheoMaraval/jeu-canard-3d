// Rendu Three.js : charge une ville, instancie canards et leurres, applique la vue.
// Seul module (avec main.js) qui dépend de Three.js et du DOM.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { axesCamera, limitesCarte } from './vue.js';

const TYPE_CANARD = 'Canard';
const TYPE_CANARD_LOIN = 'Canard_Loin';
const MAT_JAUNE = 'MAT_Jaune';
const VERT_TROUVE = new THREE.Color('#35c759');
const HAUTEUR_CENTRE = 0.22; // centre d'un objet au-dessus de son point d'appui (m)
const DISTANCE_CAMERA = 300;

async function json(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} introuvable (${r.status})`);
  return r.json();
}

/** Maillages d'un nœud glTF : lui-même s'il n'a qu'un matériau, sinon ses enfants. */
function maillages(racine, nom) {
  const noeud = racine.getObjectByName(nom);
  if (!noeud) throw new Error(`props.glb ne contient pas « ${nom} »`);
  return noeud.isMesh ? [noeud] : noeud.children.filter((c) => c.isMesh);
}

function matrice(objet, echelle = 1) {
  const [x, y, z] = objet.position;
  return new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), objet.rotation),
    new THREE.Vector3(echelle, echelle, echelle),
  );
}

/** Un InstancedMesh par primitive du modèle ; `teinte` rend le jaune recolorable par instance. */
function instancier(racine, nom, objets, teinte = false) {
  return maillages(racine, nom).map((m) => {
    let materiau = m.material;
    const recolorable = teinte && materiau.name === MAT_JAUNE;
    const jaune = materiau.color.clone();
    if (recolorable) {
      materiau = materiau.clone();
      materiau.color.set('#ffffff'); // la couleur vient alors de chaque instance
    }
    const im = new THREE.InstancedMesh(m.geometry, materiau, objets.length);
    objets.forEach((o, i) => {
      im.setMatrixAt(i, matrice(o));
      if (recolorable) im.setColorAt(i, jaune);
    });
    im.castShadow = true;
    im.receiveShadow = true;
    im.userData.recolorable = recolorable;
    return im;
  });
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

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#cfd8e3');
  quartier.scene.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });
  scene.add(quartier.scene);

  scene.add(new THREE.HemisphereLight('#ffffff', '#a9b0bb', 1.7));
  const soleil = new THREE.DirectionalLight('#fff4e0', 2.0);
  soleil.position.set(-70, 130, 90); // sud-ouest : ombres portées vers la droite de l'écran
  soleil.castShadow = true;
  soleil.shadow.mapSize.set(2048, 2048);
  Object.assign(soleil.shadow.camera, { left: -95, right: 95, top: 95, bottom: -95, near: 1, far: 400 });
  soleil.shadow.bias = -0.0004;
  soleil.shadow.normalBias = 0.04;
  scene.add(soleil);

  // --- canards et leurres ---------------------------------------------------
  const canards = placements.objets.filter((o) => o.type === TYPE_CANARD);
  const pres = instancier(props.scene, TYPE_CANARD, canards, true);
  const loin = instancier(props.scene, TYPE_CANARD_LOIN, canards, true);
  scene.add(...pres, ...loin);
  const parType = new Map();
  for (const o of placements.objets) {
    if (o.type === TYPE_CANARD) continue;
    if (!parType.has(o.type)) parType.set(o.type, []);
    parType.get(o.type).push(o);
  }
  for (const [type, objets] of parType) scene.add(...instancier(props.scene, type, objets));

  // --- caméra orthographique à angle fixe -----------------------------------
  const versCamera = placements.camera.vers_camera;
  const axes = axesCamera(versCamera);
  const hauteurMax = new THREE.Box3().setFromObject(quartier.scene).max.y;
  const limites = limitesCarte(placements.taille, hauteurMax, axes);
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

  function echelle(index, k) {
    const mat = matrice(canards[index], k);
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
    appliquerVue,
    marquerTrouve,
    demanderRendu,
    /** Centres des canards dans le repère du monde, pour le picking. */
    canards: canards.map((c) => ({ id: c.id, centre: [c.position[0], c.position[1] + HAUTEUR_CENTRE, c.position[2]] })),
    stats: () => ({ ...renderer.info.render, objets: placements.objets.length }),
  };
}
