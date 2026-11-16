"""Rend deux aperçus de blender/props.blend dans docs/previews/ sans modifier le .blend.

    blender --background blender/props.blend --python blender/render_preview.py

- props_pres.png : alignement vu de près (bec et œil lisibles).
- props_loin.png : même cadrage à ~12 px par objet, pour juger le camouflage.
"""
import math
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "previews")
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
props = sorted(bpy.data.collections["Props"].objects, key=lambda o: o.location.x)
cx = (props[0].location.x + props[-1].location.x) / 2

cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = len(props) * 1.0 + 0.6
cam = bpy.data.objects.new("PreviewCam", cam_data)
scene.collection.objects.link(cam)
# élévation isométrique (~35°), de face pour que l'alignement reste horizontal
tilt, d = math.radians(54.7), 20
cam.rotation_euler = (tilt, 0, 0)
cam.location = (cx, -d * math.sin(tilt), d * math.cos(tilt) + 0.3)
scene.camera = cam

sun_data = bpy.data.lights.new("PreviewSun", "SUN")
sun_data.energy = 2.0
sun = bpy.data.objects.new("PreviewSun", sun_data)
sun.rotation_euler = (math.radians(50), 0, math.radians(-20))
scene.collection.objects.link(sun)

bpy.ops.mesh.primitive_plane_add(size=40, location=(cx, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("PreviewSol")
if gmat.node_tree is None:
    gmat.use_nodes = True
gmat.node_tree.nodes.clear()
_bsdf = gmat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
_out = gmat.node_tree.nodes.new("ShaderNodeOutputMaterial")
gmat.node_tree.links.new(_bsdf.outputs["BSDF"], _out.inputs["Surface"])
_bsdf.inputs["Base Color"].default_value = (0.12, 0.13, 0.14, 1)  # bitume
_bsdf.inputs["Roughness"].default_value = 0.9
ground.data.materials.append(gmat)

world = scene.world or bpy.data.worlds.new("PreviewWorld")
scene.world = world
world.color = (0.6, 0.65, 0.7)

for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "PNG"

result = {"engine": scene.render.engine}
for name, (w, h) in {"props_pres": (1600, 500), "props_loin": (160, 50)}.items():
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    result[name] = scene.render.filepath
print(result)
