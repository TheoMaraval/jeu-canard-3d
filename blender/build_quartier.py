"""Génère le décor d'une ville : blender/scenes/<ville>.blend + assets/scenes/<ville>/quartier.glb.

    blender --background --python blender/build_quartier.py -- --ville paris

Deux maillages : « Quartier » (un slot par matériau de la palette) et « Vitres ».
Le seul jaune du décor est le matériau « jaune » des gros leurres (taxis, stores) ;
canards et petits leurres viennent de props.glb.
"""
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))

from citygen.geo import objet_rapide, register  # noqa: E402
from citygen.layout import charger_theme, make_layout  # noqa: E402


def argument(nom, defaut):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return argv[argv.index(nom) + 1] if nom in argv else defaut


def main():
    ville = argument("--ville", "paris")
    theme = charger_theme(ville)
    plan = make_layout(theme)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    register(theme["palette"])
    col = bpy.data.collections.new("Quartier")
    bpy.context.scene.collection.children.link(col)
    # Les vitres sont un objet à part : translucides côté app, et masquées pendant la
    # mesure de visibilité (un rayon doit traverser une vitre).
    obj = objet_rapide("Quartier", [p for p in plan["prims"] if p["mat"] != "verre"], col)
    verre = objet_rapide("Vitres", [p for p in plan["prims"] if p["mat"] == "verre"], col)
    obj.data.calc_loop_triangles()

    blend = os.path.join(ROOT, "blender", "scenes", ville + ".blend")
    glb = os.path.join(ROOT, "assets", "scenes", ville, "quartier.glb")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    os.makedirs(os.path.dirname(glb), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    obj.select_set(True)
    verre.select_set(True)
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    return {"ville": ville, "primitives": len(plan["prims"]),
            "triangles": len(obj.data.loop_triangles), "materiaux": len(obj.data.materials),
            "glb_ko": round(os.path.getsize(glb) / 1024), "slots": len(plan["slots"])}


result = main()
print("RESULTAT", result)
