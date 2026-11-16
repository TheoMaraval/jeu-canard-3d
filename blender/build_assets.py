"""Construit le canard et les leurres jaunes, puis exporte assets/props.glb.

Lancement :
    blender --background --python blender/build_assets.py
ou coller dans Blender (MCP execute_blender_code) : ROOT sert alors de repli.

Règle de camouflage : la masse JAUNE de chaque asset tient dans un cube de
GABARIT mètres de côté et utilise le même matériau MAT_Jaune. Le script le
vérifie et échoue sinon.
"""
import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

ROOT = r"C:\Users\TMARAVAL\code\jeu-canard-3D"
if "__file__" in globals():
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GABARIT = 0.50  # m — côté du cube englobant la partie jaune
TOL = 0.005
COLLECTION = "Props"

COULEURS = {  # nom -> (sRGB hex, rugosité)
    "MAT_Jaune": ("#FFD21E", 0.45),
    "MAT_Orange": ("#FF7A00", 0.45),
    "MAT_Noir": ("#111111", 0.60),
    "MAT_Gris": ("#8A8F98", 0.60),
    "MAT_Blanc": ("#F2F2F2", 0.60),
    "MAT_Terre": ("#9C5A3C", 0.80),
    "MAT_Vert": ("#3E8E41", 0.70),
}
J, O, N, G, B, T, V = COULEURS  # raccourcis, dans l'ordre du dict


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    hexa, rough = COULEURS[name]
    rgb = [srgb_to_linear(int(hexa[i:i + 2], 16) / 255) for i in (1, 3, 5)]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0
    mat.diffuse_color = (*rgb, 1.0)
    return mat


def xf(loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0)):
    return Matrix.LocRotScale(Vector(loc), Euler(rot), Vector(scale))


class Builder:
    """Assemble des primitives dans un seul maillage, un slot par matériau."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.slots = []

    def _finish(self, verts, mat, matrix, smooth):
        bmesh.ops.transform(self.bm, matrix=matrix, verts=verts)
        if mat not in self.slots:
            self.slots.append(mat)
        idx = self.slots.index(mat)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = idx
            f.smooth = smooth

    def sphere(self, mat, r, matrix, half=False, u=16, v=8):
        verts = bmesh.ops.create_uvsphere(self.bm, u_segments=u, v_segments=v, radius=r)["verts"]
        if half:  # ne garde que l'hémisphère haut
            low = [x for x in verts if x.co.z < -1e-6]
            bmesh.ops.delete(self.bm, geom=low, context="VERTS")
            verts = [x for x in verts if x.is_valid]
        self._finish(verts, mat, matrix, True)

    def cone(self, mat, r1, r2, depth, matrix, seg=16):
        verts = bmesh.ops.create_cone(
            self.bm, cap_ends=True, cap_tris=False, segments=seg,
            radius1=r1, radius2=r2, depth=depth)["verts"]
        self._finish(verts, mat, matrix, False)

    def cyl(self, mat, r, depth, matrix, seg=16):
        self.cone(mat, r, r, depth, matrix, seg)

    def box(self, mat, size, matrix_loc, rot=(0, 0, 0)):
        verts = bmesh.ops.create_cube(self.bm, size=1.0)["verts"]
        self._finish(verts, mat, xf(matrix_loc, size, rot), False)

    def build(self, collection, x):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in self.slots:
            mesh.materials.append(material(m))
        obj = bpy.data.objects.new(self.name, mesh)
        obj.location.x = x
        collection.objects.link(obj)
        return obj


H = math.pi / 2  # quart de tour


def canard():
    b = Builder("Canard")
    b.sphere(J, 1, xf((0, 0, 0.13), (0.22, 0.16, 0.13)))            # corps
    b.sphere(J, 0.11, xf((0.12, 0, 0.33)))                           # tête
    b.cone(J, 0.07, 0.0, 0.12, xf((-0.19, 0, 0.21), rot=(0, -math.radians(60), 0)))  # queue
    b.cone(O, 0.05, 0.02, 0.10, xf((0.25, 0, 0.31), (0.5, 1, 1), (0, H, 0)))         # bec
    for y in (0.07, -0.07):
        b.sphere(N, 0.022, xf((0.19, y, 0.37)), u=8, v=6)            # yeux
    return b


def plot():
    b = Builder("Leurre_Plot")
    b.box(N, (0.36, 0.36, 0.03), (0, 0, 0.015))
    b.cone(J, 0.15, 0.03, 0.45, xf((0, 0, 0.255)))
    return b


def borne_incendie():
    b = Builder("Leurre_BorneIncendie")
    b.cyl(J, 0.12, 0.04, xf((0, 0, 0.02)))
    b.cyl(J, 0.09, 0.34, xf((0, 0, 0.21)))
    b.sphere(J, 0.09, xf((0, 0, 0.38), (1, 1, 0.8)), half=True)
    b.cyl(J, 0.045, 0.30, xf((0, 0, 0.26), rot=(0, H, 0)), seg=10)
    b.cyl(G, 0.025, 0.04, xf((0, 0, 0.465)), seg=6)
    return b


def parasol():
    b = Builder("Leurre_Parasol")
    b.cyl(N, 0.12, 0.03, xf((0, 0, 0.015)))
    b.cyl(G, 0.012, 1.0, xf((0, 0, 0.5)), seg=8)
    b.cone(J, 0.25, 0.0, 0.16, xf((0, 0, 1.0)), seg=8)
    return b


def taxi():
    b = Builder("Leurre_Taxi")
    b.box(J, (0.46, 0.22, 0.12), (0, 0, 0.12))
    b.box(J, (0.24, 0.20, 0.10), (-0.02, 0, 0.23))
    b.box(B, (0.08, 0.05, 0.03), (-0.02, 0, 0.295))
    for x in (0.14, -0.14):
        for y in (0.11, -0.11):
            b.cyl(N, 0.05, 0.04, xf((x, y, 0.05), rot=(H, 0, 0)), seg=10)
    return b


def boite_aux_lettres():
    b = Builder("Leurre_BoiteAuxLettres")
    b.box(N, (0.06, 0.06, 0.20), (0, 0, 0.10))
    b.box(J, (0.30, 0.22, 0.34), (0, 0, 0.37))
    b.cyl(J, 0.11, 0.30, xf((0, 0, 0.54), rot=(0, H, 0)))
    b.box(N, (0.18, 0.01, 0.02), (0, -0.111, 0.47))
    return b


def jardiniere():
    b = Builder("Leurre_Jardiniere")
    b.box(T, (0.46, 0.20, 0.18), (0, 0, 0.09))
    b.box(V, (0.42, 0.16, 0.06), (0, 0, 0.20))
    for i, x in enumerate((-0.17, -0.085, 0.0, 0.085, 0.17)):
        y = 0.035 if i % 2 else -0.035
        b.sphere(J, 0.05, xf((x, y, 0.26), (1, 1, 0.7)), u=8, v=6)
    return b


def casque():
    b = Builder("Leurre_CasqueChantier")
    b.cyl(J, 0.23, 0.02, xf((0.03, 0, 0.01), (1.0, 0.85, 1)))
    b.sphere(J, 0.19, xf((0, 0, 0.02), (1, 0.9, 0.8)), half=True)
    b.box(J, (0.30, 0.03, 0.02), (0, 0, 0.17))
    return b


ASSETS = [canard, plot, borne_incendie, parasol, taxi, boite_aux_lettres, jardiniere, casque]


def taille_jaune(obj):
    """Dimensions (x, y, z) de la boîte englobant les faces jaunes."""
    mesh = obj.data
    idx = [i for i, m in enumerate(mesh.materials) if m.name == J]
    pts = [mesh.vertices[v].co for p in mesh.polygons if p.material_index in idx for v in p.vertices]
    return [round(max(p[a] for p in pts) - min(p[a] for p in pts), 3) for a in range(3)]


def main():
    old = bpy.data.collections.get(COLLECTION)
    if old:  # reconstruction idempotente : on ne touche qu'à notre collection
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    col = old or bpy.data.collections.new(COLLECTION)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)

    report, errors = {}, []
    for i, fn in enumerate(ASSETS):
        obj = fn().build(col, i * 1.0)
        size = taille_jaune(obj)
        obj.data.calc_loop_triangles()
        report[obj.name] = {"jaune_xyz": size, "tris": len(obj.data.loop_triangles)}
        if max(size) > GABARIT + TOL:
            errors.append(f"{obj.name}: jaune {size} > gabarit {GABARIT}")
    if errors:
        raise ValueError("; ".join(errors))

    blend = os.path.join(ROOT, "blender", "props.blend")
    glb = os.path.join(ROOT, "assets", "props.glb")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    bpy.ops.object.select_all(action="DESELECT")
    for o in col.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    return {"assets": report, "blend": blend, "glb": glb}


result = main()
print(result)
