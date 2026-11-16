"""Primitives -> maillage Blender. Seul module de citygen qui dépend de bpy."""
import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

PALETTE = {}  # nom de matériau -> (hex sRGB, rugosité)


def register(couleurs):
    """Ajoute des couleurs à la palette : {nom: "#RRGGBB"} ou {nom: ("#RRGGBB", rugosité)}."""
    for nom, v in couleurs.items():
        PALETTE[nom] = (v, 0.7) if isinstance(v, str) else tuple(v)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    hexa, rough = PALETTE[name]
    rgb = [srgb_to_linear(int(hexa[i:i + 2], 16) / 255) for i in (1, 3, 5)]
    if mat.node_tree is None:  # Blender < 5 : arbre absent tant que use_nodes est faux
        mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()  # Blender 5 : l'arbre existe mais peut être vide
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
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

    def box(self, mat, size, loc, rot=(0, 0, 0), haut=None):
        verts = bmesh.ops.create_cube(self.bm, size=1.0)["verts"]
        if haut:  # rétrécit la face du dessus (toit mansardé)
            for v in verts:
                if v.co.z > 0:
                    v.co.x *= haut[0]
                    v.co.y *= haut[1]
        self._finish(verts, mat, xf(loc, size, rot), False)

    def prim(self, p):
        """Ajoute une primitive décrite par un dict (contrat de layout.py)."""
        if p["t"] == "box":
            self.box(p["mat"], p["size"], p["pos"], (0, 0, p.get("rot", 0.0)), p.get("haut"))
        elif p["t"] == "cyl":
            self.cone(p["mat"], p["r1"], p["r2"], p["h"], xf(p["pos"]), p.get("seg", 10))
        elif p["t"] == "sph":
            self.sphere(p["mat"], p["r"], xf(p["pos"], p.get("scale", (1, 1, 1))), u=10, v=6)
        else:
            raise ValueError(f"primitive inconnue : {p['t']}")

    def build(self, collection, x=0.0):
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
