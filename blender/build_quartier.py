"""Génère le décor d'une ville : blender/scenes/<ville>.blend + assets/scenes/<ville>/quartier.glb.

    blender --background --python blender/build_quartier.py -- --ville paris

Deux maillages : « Quartier » (un slot par matériau de la palette) et « Vitres ».
Le seul jaune du décor est le matériau « jaune » des gros leurres (taxis, stores) ;
canards et petits leurres viennent de props.glb.
"""
import json
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

    # Instances du kit : présentes dans le .blend (elles cachent des choses, la mesure de
    # visibilité doit les voir) mais pas dans quartier.glb : l'app les instancie depuis
    # kit.glb d'après decor.json.
    with bpy.data.libraries.load(os.path.join(ROOT, "blender", "kit.blend")) as (src, dst):
        dst.objects = list(src.objects)
    modeles = {o.name: o for o in dst.objects}
    col_kit = bpy.data.collections.new("Kit")
    bpy.context.scene.collection.children.link(col_kit)
    pal = theme["palette"]
    decor = []
    for i in plan["insts"]:
        o = bpy.data.objects.new(i["type"], modeles[i["type"]].data)
        o.location, o.rotation_euler, o.scale = i["pos"], (0, 0, i["rot"]), (i["k"],) * 3
        col_kit.objects.link(o)
        x, y, z = i["pos"]
        decor.append({"type": i["type"], "p": [x, z, round(-y, 3)], "r": i["rot"], "s": i["k"],
                      "c": {role: pal[nom] for role, nom in i["c"].items()}})

    blend = os.path.join(ROOT, "blender", "scenes", ville + ".blend")
    glb = os.path.join(ROOT, "assets", "scenes", ville, "quartier.glb")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    os.makedirs(os.path.dirname(glb), exist_ok=True)
    with open(os.path.join(os.path.dirname(glb), "decor.json"), "w", encoding="utf8") as f:
        json.dump({"ville": ville, "repere": "glTF : p = position, r = rotation autour de Y, s = échelle, "
                   "c = teinte par rôle", "instances": decor}, f, separators=(",", ":"))
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    for m in modeles.values():
        m.data.calc_loop_triangles()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    verre.select_set(True)
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    return {"ville": ville, "primitives": len(plan["prims"]),
            "triangles": len(obj.data.loop_triangles), "materiaux": len(obj.data.materials),
            "glb_ko": round(os.path.getsize(glb) / 1024), "slots": len(plan["slots"]),
            "instances": len(decor), "personnages": sum(1 for d in decor if d["type"].startswith("Perso_")),
            "triangles_instances": sum(len(modeles[d["type"]].data.loop_triangles) for d in decor)}


result = main()
print("RESULTAT", result)
