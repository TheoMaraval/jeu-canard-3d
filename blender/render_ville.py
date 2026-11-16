"""Aperçus d'une ville avec ses canards et leurres, depuis la caméra de jeu.

    blender --background blender/scenes/<ville>.blend --python blender/render_ville.py -- --ville paris

Écrit docs/previews/<ville>_ensemble.png, _moyen.png (canards sans bec ni œil, comme en
jeu sous le seuil de révélation) et _pres.png (gros plan sur un canard). Ne modifie pas
le .blend.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))

from citygen.layout import AZIMUT, ELEVATION  # noqa: E402


def argument(nom, defaut):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return argv[argv.index(nom) + 1] if nom in argv else defaut


ville = argument("--ville", "paris")
cible_id = argument("--canard", "")
scene = bpy.context.scene
placements = json.load(open(os.path.join(ROOT, "assets", "scenes", ville, "placements.json"), encoding="utf8"))

with bpy.data.libraries.load(os.path.join(ROOT, "blender", "props.blend")) as (src, dst):
    dst.objects = list(src.objects)
modeles = {o.name: o for o in dst.objects}

col = bpy.data.collections.new("Objets")
scene.collection.children.link(col)
canards = []
for p in placements["objets"]:
    x, y, z = p["position"]  # glTF -> Blender : (x, -z, y)
    o = bpy.data.objects.new(p["id"], modeles[p["type"]].data)
    o.location = (x, -z, y)
    o.rotation_euler = (0, 0, p["rotation"])
    o.scale = (placements["echelle"],) * 3
    col.objects.link(o)
    if p["type"] == "Canard":
        canards.append(o)

el, az = math.radians(ELEVATION), math.radians(AZIMUT)
vers_camera = Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)))
cam_data = bpy.data.cameras.new("ApercuCam")
cam_data.type = "ORTHO"
cam_data.clip_end = 1000
cam = bpy.data.objects.new("ApercuCam", cam_data)
cam.rotation_euler = (math.pi / 2 - el, 0, az)
scene.collection.objects.link(cam)
scene.camera = cam

sun_data = bpy.data.lights.new("ApercuSoleil", "SUN")
sun_data.energy = 2.5
sun_data.angle = math.radians(2)
sun = bpy.data.objects.new("ApercuSoleil", sun_data)
sun.rotation_euler = (math.radians(48), 0, math.radians(-15))  # lumière venant du sud-ouest
scene.collection.objects.link(sun)

world = bpy.data.worlds.new("ApercuMonde")
scene.world = world
if world.node_tree is None:
    world.use_nodes = True
world.node_tree.nodes.clear()  # Blender 5 : arbre vide par défaut, donc pas de lumière d'ambiance
_fond = world.node_tree.nodes.new("ShaderNodeBackground")
_sortie = world.node_tree.nodes.new("ShaderNodeOutputWorld")
world.node_tree.links.new(_fond.outputs["Background"], _sortie.inputs["Surface"])
_fond.inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
_fond.inputs["Strength"].default_value = 1.0

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "PNG"


def rendre(nom, cible, echelle, w, h, loin):
    for o in canards:  # sous le seuil de révélation, le jeu affiche le canard sans bec ni œil
        o.data = modeles["Canard_Loin" if loin else "Canard"].data
    cam_data.ortho_scale = echelle
    cam.location = Vector(cible) + vers_camera * 300
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    scene.render.filepath = os.path.join(ROOT, "docs", "previews", f"{ville}_{nom}.png")
    bpy.ops.render.render(write_still=True)
    return {"px_par_objet": round(placements["gabarit"] / echelle * w, 1)}


if not cible_id:  # par défaut : un canard derrière une vitre
    cible_id = next((p["id"] for p in placements["objets"] if p["type"] == "Canard" and p["lieu"] == "vitre"),
                    canards[0].name)
cible = next(o for o in canards if o.name == cible_id).location
result = {
    "ensemble": rendre("ensemble", (0, 0, 8), 178, 1600, 1250, True),
    "moyen": rendre("moyen", cible, 55, 1600, 1100, True),
    "pres": rendre("pres", cible, 8, 1600, 1100, False),
}
print("RESULTAT", json.dumps(result))
