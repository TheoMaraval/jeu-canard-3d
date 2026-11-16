"""Primitives -> maillage Blender. Seul module de citygen qui dépend de bpy."""
import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

PALETTE = {}  # nom de matériau -> (hex sRGB, rugosité)
ALPHA = {"verre": 0.38}  # matériaux translucides


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
    alpha = ALPHA.get(name, 1.0)
    if alpha < 1.0:  # vitres : l'exporteur glTF écrit alphaMode BLEND
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            mat.surface_render_method = "BLENDED"
        except AttributeError:
            mat.blend_method = "BLEND"
    mat.diffuse_color = (*rgb, alpha)
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
            self.cone(p["mat"], p["r1"], p["r2"], p["h"], xf(p["pos"]), p.get("seg", 8))
        elif p["t"] == "sph":
            # 8 x 5 : arêtes sous 50 degrés, donc pas de trait d'encre sur les rondeurs
            self.sphere(p["mat"], p["r"], xf(p["pos"], p.get("scale", (1, 1, 1))), u=8, v=5)
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


def objet_rapide(nom, prims, collection):
    """Maillage d'une liste de primitives sans bmesh (voir maillage.py) : coût linéaire."""
    from .maillage import assembler

    m = assembler(prims)
    mesh = bpy.data.meshes.new(nom)
    mesh.from_pydata(m["sommets"], [], m["faces"])
    mesh.polygons.foreach_set("material_index", m["mats"])
    mesh.polygons.foreach_set("use_smooth", m["lisses"])
    for n in m["noms"]:
        mesh.materials.append(material(n))
    mesh.update()
    obj = bpy.data.objects.new(nom, mesh)
    collection.objects.link(obj)
    return obj


# ---- formes modelées pour le kit (personnages, véhicules, mobilier) ------------
def _coller(self, tmp, mat, smooth, matrix=None):
    """Ajoute un bmesh temporaire au maillage en cours, avec son matériau."""
    if matrix is not None:
        bmesh.ops.transform(tmp, matrix=matrix, verts=tmp.verts)
    me = bpy.data.meshes.new("_tmp")
    tmp.to_mesh(me)
    tmp.free()
    n0 = len(self.bm.faces)
    self.bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    self.bm.faces.ensure_lookup_table()
    if mat not in self.slots:
        self.slots.append(mat)
    idx = self.slots.index(mat)
    for f in self.bm.faces[n0:]:
        f.material_index = idx
        f.smooth = smooth


def _rbox(self, mat, size, loc, rot=(0, 0, 0), bevel=0.05, smooth=True):
    """Boîte aux arêtes chanfreinées : lue comme arrondie une fois lissée."""
    tmp = bmesh.new()
    bmesh.ops.create_cube(tmp, size=1.0)
    for v in tmp.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=min(bevel, min(size) * 0.45),
                    segments=1, affect="EDGES", profile=0.5)
    self._coller(tmp, mat, smooth, xf(loc, rot=rot))


def _ico(self, mat, r, loc, scale=(1, 1, 1), sub=1):
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=sub, radius=r)
    self._coller(tmp, mat, True, xf(loc, scale))


def _lathe(self, mat, profil, matrix=None, seg=8, smooth=True):
    """Surface de révolution autour de Z. profil : [(rayon, z), ...] de bas en haut."""
    import math
    tmp = bmesh.new()
    anneaux = []
    for r, z in profil:
        if r < 1e-6:
            anneaux.append([tmp.verts.new((0, 0, z))])
        else:
            anneaux.append([tmp.verts.new((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z))
                            for i in range(seg)])
    for a, b in zip(anneaux, anneaux[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                tmp.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                tmp.faces.new((a[i], a[j], b[0]))
            else:
                tmp.faces.new((a[i], a[j], b[j], b[i]))
    if len(anneaux[0]) > 1:
        tmp.faces.new(list(reversed(anneaux[0])))
    if len(anneaux[-1]) > 1:
        tmp.faces.new(anneaux[-1])
    self._coller(tmp, mat, smooth, matrix)


def _tube(self, mat, p0, p1, r0, r1, seg=6):
    """Membre : cylindre effilé de p0 à p1, bouts arrondis."""
    d = Vector(p1) - Vector(p0)
    m = Matrix.Translation(Vector(p0)) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    self.lathe(mat, [(0, -r0 * 0.5), (r0, 0), (r1, d.length), (0, d.length + r1 * 0.5)], m, seg)


Builder._coller, Builder.rbox, Builder.ico, Builder.lathe, Builder.tube = _coller, _rbox, _ico, _lathe, _tube
