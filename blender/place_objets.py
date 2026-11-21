"""Mesure la visibilité des cachettes et place canards et leurres.

    blender --background blender/scenes/<ville>.blend --python blender/place_objets.py -- --ville paris

Écrit assets/scenes/<ville>/placements.json et met à jour assets/scenes.json.
La visibilité d'une cachette est la part de 27 points du volume d'un canard d'où un
rayon atteint la caméra de jeu sans toucher le décor ni les passants, véhicules et
mobilier du kit. Les vitres ne bloquent pas : on compte celles que le rayon traverse.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))

from citygen.layout import AZIMUT, ELEVATION, charger_theme, make_layout  # noqa: E402
from citygen.placement import CANARD, PlacementImpossible, cellule, choisir  # noqa: E402

EL, AZ = math.radians(ELEVATION), math.radians(AZIMUT)
VERS_CAMERA = Vector((math.cos(EL) * math.sin(AZ), -math.cos(EL) * math.cos(AZ), math.sin(EL)))
ECHANTILLONS = [Vector((dx, dy, dz)) for dx in (-0.15, 0.0, 0.15)
                for dy in (-0.12, 0.0, 0.12) for dz in (0.06, 0.22, 0.38)]
# Points du modèle Canard (repère local, +x = avant) qui doivent rester visibles
BEC = (0.29, 0.0, 0.31)
YEUX = ((0.20, 0.075, 0.37), (0.20, -0.075, 0.37))
FACE_CAMERA = -math.radians(AZIMUT)  # rotation Z qui tourne le bec vers la caméra
ECARTS = [math.radians(a) for a in (0, 25, -25, 50, -50, 70, -70)]
DEGAGEMENT = 0.22  # m libres autour du centre, sinon l'objet traverserait un mur


def argument(nom, defaut):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return argv[argv.index(nom) + 1] if nom in argv else defaut


def rayon(scene, dg, origine, direction, portee=400.0):
    """Lance un rayon qui traverse les vitres. Renvoie (bloqué, nombre de vitres traversées)."""
    o, vitres = Vector(origine), 0
    while portee > 0:
        touche, point, _n, _i, objet, _m = scene.ray_cast(dg, o, direction, distance=portee)
        if not touche:
            return False, vitres
        if objet.name != "Vitres":
            return True, vitres
        vitres += 1
        portee -= (point - o).length + 0.002
        o = point + direction * 0.002
    return False, vitres


def mesurer(scene, dg, slot, k):
    """Recale le slot sur la surface et renvoie sa visibilité, ou None s'il est inutilisable.

    Un slot « vitre » n'est gardé que si tout ce qu'on en voit est vu à travers une vitre :
    c'est ce qui garantit qu'un canard « derrière une vitre » l'est vraiment.
    """
    p = Vector(slot["pos"])
    touche, point, *_ = scene.ray_cast(dg, p + Vector((0, 0, 0.6)), Vector((0, 0, -1)), distance=1.2)
    if not touche or abs(point.z - p.z) > 0.3:
        return None
    p.z = point.z
    centre = p + Vector((0, 0, 0.22 * k))
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
        if rayon(scene, dg, centre, Vector(d), DEGAGEMENT * k)[0]:
            return None
    vus = [v for bloque, v in (rayon(scene, dg, p + e * k, VERS_CAMERA) for e in ECHANTILLONS) if not bloque]
    if slot["lieu"] == "vitre" and any(v == 0 for v in vus):
        return None  # une partie dépasserait devant la vitre
    slot["rot_canard"] = orientation_canard(scene, dg, p, slot["rot"], k, slot["lieu"] == "vitre")
    slot["pos"] = [round(p.x, 3), round(p.y, 3), round(p.z, 3)]
    return len(vus) / len(ECHANTILLONS)


def orientation_canard(scene, dg, p, graine, k, sous_vitre):
    """Rotation qui montre le bec et au moins un œil à la caméra, ou None.

    Sans cela un canard vu de dos serait indiscernable d'une boule jaune, même de près.
    Derrière une vitre, le bec doit lui aussi rester derrière.
    """
    def visible(local, rot):
        c, s = math.cos(rot), math.sin(rot)
        monde = p + k * Vector((local[0] * c - local[1] * s, local[0] * s + local[1] * c, local[2]))
        bloque, vitres = rayon(scene, dg, monde, VERS_CAMERA)
        return not bloque and (vitres > 0 or not sous_vitre)

    depart = int(graine * 1000) % len(ECARTS)  # varie l'angle essayé en premier
    for ecart in ECARTS[depart:] + ECARTS[:depart]:
        rot = FACE_CAMERA + ecart
        if visible(BEC, rot) and (visible(YEUX[0], rot) or visible(YEUX[1], rot)):
            return round(rot % (2 * math.pi), 3)
    return None


def gltf(o):
    x, y, z = o["pos"]
    return {"id": o["id"], "type": o["type"], "position": [x, round(z, 3), round(-y, 3)],
            "rotation": o["rot"], "visibilite": o["visibilite"], "lieu": o["lieu"], "zone": o["zone"],
            **({"assoupli": o["assoupli"]} if o.get("assoupli") else {})}


def main():
    ville = argument("--ville", "paris")
    theme = charger_theme(ville)
    k = theme["echelle_objets"]
    scene = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()

    slots = []
    for s in make_layout(theme)["slots"]:
        vis = mesurer(scene, dg, s, k)
        if vis is not None:
            s["vis"] = vis
            slots.append(s)
    try:
        objets = choisir(slots, theme)
    except PlacementImpossible:
        # diagnostic : candidats canard par case et par lieu
        lo, hi = theme["visibilite_canard"]
        diag = {}
        for s in slots:
            d = diag.setdefault(cellule(s["pos"], theme), {"slots": 0})
            d["slots"] += 1
            if lo <= s["vis"] <= hi:
                d[s["lieu"]] = d.get(s["lieu"], 0) + 1
        print("DIAGNOSTIC", json.dumps(dict(sorted(diag.items()))))
        raise

    dossier = os.path.join(ROOT, "assets", "scenes", ville)
    with open(os.path.join(dossier, "placements.json"), "w", encoding="utf8") as f:
        json.dump({
            "ville": ville, "version": theme["version"], "graine": theme["graine"],
            "repere": "glTF : Y vers le haut, mètres, carte centrée sur l'origine",
            "taille": theme["taille"],
            "echelle": k, "gabarit": round(0.5 * k, 3),
            "camera": {"azimut": AZIMUT, "elevation": ELEVATION,
                       "vers_camera": [round(VERS_CAMERA.x, 5), round(VERS_CAMERA.z, 5), round(-VERS_CAMERA.y, 5)]},
            "objets": [gltf(o) for o in objets],
        }, f, ensure_ascii=False, indent=1)

    index = os.path.join(ROOT, "assets", "scenes.json")
    scenes = json.load(open(index, encoding="utf8")) if os.path.exists(index) else []
    scenes = [s for s in scenes if s["id"] != ville]
    # "ordre" (facultatif dans le thème) fixe la place dans le menu de l'app ; sinon : à la fin
    scenes.append({"id": ville, "nom": theme["nom"], "version": theme["version"], "ordre": theme.get("ordre", 99),
                   "embleme": theme.get("embleme", "🏙️"), "canards": theme["canards"]})
    with open(index, "w", encoding="utf8") as f:
        json.dump(sorted(scenes, key=lambda s: (s.get("ordre", 99), s["id"])), f, ensure_ascii=False, indent=1)

    canards = [o for o in objets if o["type"] == CANARD]
    lo, hi = theme["visibilite_canard"]
    histo = {}
    for s in slots:
        k = "0" if s["vis"] == 0 else "1" if s["vis"] == 1 else f"{int(s['vis'] * 5) / 5:.1f}+"
        histo[k] = histo.get(k, 0) + 1
    par = lambda objs, cle: {v: sum(1 for o in objs if o[cle] == v) for v in sorted({o[cle] for o in objs})}
    return {
        "slots_utilisables": len(slots), "histogramme_visibilite": dict(sorted(histo.items())),
        "candidats_canard": sum(1 for s in slots if lo <= s["vis"] <= hi),
        "canards_par_lieu": par(canards, "lieu"),
        "leurres_par_lieu": par([o for o in objets if o["type"] != CANARD], "lieu"),
        "leurres_par_type": par([o for o in objets if o["type"] != CANARD], "type"),
        "slots_ou_la_tete_se_voit": sum(1 for s in slots if s["rot_canard"] is not None),
        "canards_plage_elargie": {o["zone"]: o["visibilite"] for o in canards if o.get("assoupli")},
        "visibilite_moyenne_canards": round(sum(o["visibilite"] for o in canards) / len(canards), 2),
        "leurres_dans_plage_canard": sum(1 for o in objets if o["type"] != CANARD and lo <= o["visibilite"] <= hi),
    }


result = main()
print("RESULTAT", json.dumps(result, ensure_ascii=False))
