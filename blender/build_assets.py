"""Construit le canard et les leurres jaunes, puis exporte assets/props.glb.

Lancement :
    blender --background --python blender/build_assets.py
ou coller dans Blender (MCP execute_blender_code), Blender lancé depuis la racine du projet.

Règle de camouflage : la masse JAUNE de chaque asset tient dans un cube de
GABARIT mètres de côté et utilise le même matériau MAT_Jaune. Le script le
vérifie et échoue sinon.
"""
import math
import os
import sys

import bpy

# Sans __file__ (code collé via MCP), lancer Blender depuis la racine du projet.
ROOT = (os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if "__file__" in globals() else os.getcwd())
sys.path.insert(0, os.path.join(ROOT, "blender"))

from citygen.geo import Builder, register, xf  # noqa: E402

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
register(COULEURS)

H = math.pi / 2  # quart de tour


def canard(detail=True):
    """detail=False : niveau « loin », sans bec ni yeux (camouflage à zoom moyen)."""
    b = Builder("Canard" if detail else "Canard_Loin")
    b.sphere(J, 1, xf((0, 0, 0.13), (0.22, 0.16, 0.13)))            # corps
    b.sphere(J, 0.11, xf((0.12, 0, 0.33)))                           # tête
    b.cone(J, 0.07, 0.0, 0.12, xf((-0.19, 0, 0.21), rot=(0, -math.radians(60), 0)))  # queue
    if detail:
        b.cone(O, 0.05, 0.02, 0.10, xf((0.25, 0, 0.31), (0.5, 1, 1), (0, H, 0)))     # bec
        for y in (0.07, -0.07):
            b.sphere(N, 0.022, xf((0.19, y, 0.37)), u=8, v=6)        # yeux
    return b


def canard_loin():
    return canard(detail=False)


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


def arrosoir():
    """Silhouette proche du canard : un corps rond et un bec... jaune, sans œil."""
    b = Builder("Leurre_Arrosoir")
    b.cyl(J, 0.13, 0.24, xf((-0.04, 0, 0.12)))
    b.cone(J, 0.04, 0.025, 0.22, xf((0.15, 0, 0.20), rot=(0, math.radians(55), 0)), seg=10)
    b.cyl(J, 0.05, 0.03, xf((0.245, 0, 0.265), rot=(0, math.radians(55), 0)), seg=10)
    b.box(J, (0.03, 0.03, 0.20), (-0.185, 0, 0.14))
    b.box(J, (0.05, 0.03, 0.03), (-0.165, 0, 0.235))
    return b


def botte():
    b = Builder("Leurre_Botte")
    b.box(N, (0.30, 0.12, 0.03), (0.03, 0, 0.015))
    b.sphere(J, 1, xf((0.04, 0, 0.085), (0.15, 0.065, 0.06)))
    b.cyl(J, 0.065, 0.30, xf((-0.05, 0, 0.20)))
    b.cyl(J, 0.075, 0.03, xf((-0.05, 0, 0.36)))
    return b


def ballon():
    b = Builder("Leurre_Ballon")
    b.sphere(J, 0.20, xf((0, 0, 0.20)))
    b.sphere(N, 0.02, xf((0, 0, 0.40)), u=8, v=6)
    return b


def banane():
    b = Builder("Leurre_Banane")
    pts = [(0.23 * math.cos(a), 0.0, 0.05 + 0.23 * (1 - math.sin(a))) for a in (0.45, 1.0, 1.57, 2.14, 2.69)]
    for p0, p1 in zip(pts, pts[1:]):
        b.tube(J, p0, p1, 0.055, 0.055, seg=6)
    for p in (pts[0], pts[-1]):
        b.sphere(N, 0.03, xf(p), u=5, v=3)
    return b


def citron():
    b = Builder("Leurre_Citron")
    b.sphere(J, 0.13, xf((0, 0, 0.13), (1.3, 1, 1)), u=10, v=6)
    for s in (1, -1):
        b.cone(J, 0.05, 0.0, 0.08, xf((s * 0.19, 0, 0.13), rot=(0, s * H, 0)), seg=6)
    b.box(V, (0.1, 0.06, 0.015), (-0.12, 0.05, 0.24), rot=(0, 0.4, 0.5))
    return b


def fromage():
    """Part de fromage : un prisme à trois côtés, et ses trous."""
    b = Builder("Leurre_Fromage")
    b.cyl(J, 0.27, 0.2, xf((0, 0, 0.1)), seg=3)
    for x, y in ((0.02, 0.02), (-0.08, 0.08), (0.1, -0.03)):
        b.sphere(T, 0.035, xf((x, y, 0.2), (1, 1, 0.3)), u=6, v=4)
    b.sphere(T, 0.04, xf((-0.135, 0.0, 0.1), (0.3, 1, 1)), u=6, v=4)
    return b


def sous_marin():
    b = Builder("Leurre_SousMarin")
    b.lathe(J, [(0, -0.21), (0.08, -0.17), (0.11, -0.05), (0.11, 0.1), (0.07, 0.19), (0, 0.22)],
            xf((0, 0, 0.14), rot=(0, H, 0)), seg=10)
    b.rbox(J, (0.14, 0.09, 0.1), (0.02, 0, 0.28), bevel=0.03)
    b.cyl(G, 0.012, 0.12, xf((0.05, 0, 0.38)), seg=5)
    b.box(G, (0.02, 0.2, 0.02), (-0.21, 0, 0.14))
    for x in (-0.06, 0.04, 0.12):
        b.sphere(B, 0.028, xf((x, -0.105, 0.15), (1, 0.3, 1)), u=6, v=4)
    return b


def bus_scolaire():
    b = Builder("Leurre_BusScolaire")
    b.rbox(J, (0.46, 0.18, 0.2), (0, 0, 0.17), bevel=0.03)
    b.box(N, (0.34, 0.185, 0.07), (-0.03, 0, 0.21))
    b.box(N, (0.47, 0.19, 0.02), (0, 0, 0.11))
    b.box(O, (0.02, 0.05, 0.05), (0.1, -0.1, 0.16))
    for x in (0.14, -0.14):
        for s in (1, -1):
            b.cyl(N, 0.045, 0.04, xf((x, s * 0.09, 0.045), rot=(H, 0, 0)), seg=8)
    return b


def seau():
    b = Builder("Leurre_Seau")
    b.lathe(J, [(0, 0.0), (0.13, 0.0), (0.18, 0.3), (0.16, 0.3), (0.12, 0.03), (0, 0.03)], seg=10)
    for s in (1, -1):
        b.tube(G, (0, s * 0.18, 0.28), (0, s * 0.09, 0.44), 0.012, 0.012, seg=4)
    b.tube(G, (0, 0.09, 0.44), (0, -0.09, 0.44), 0.012, 0.012, seg=4)
    return b


def eponge():
    b = Builder("Leurre_Eponge")
    b.rbox(J, (0.3, 0.2, 0.11), (0, 0, 0.055), bevel=0.03)
    b.rbox(V, (0.3, 0.2, 0.04), (0, 0, 0.13), bevel=0.015)
    return b


def smiley():
    """Balle à sourire : deux yeux noirs comme le canard, mais ni bec ni tête."""
    b = Builder("Leurre_Smiley")
    b.sphere(J, 0.2, xf((0, 0, 0.2)))
    for y in (0.07, -0.07):
        b.sphere(N, 0.028, xf((0.18, y, 0.27), (0.4, 1, 1.4)), u=6, v=4)
    for y, z in ((0.09, 0.16), (0.045, 0.13), (0.0, 0.12), (-0.045, 0.13), (-0.09, 0.16)):
        b.sphere(N, 0.018, xf((0.19 - abs(y) * 0.25, y, z)), u=5, v=3)
    return b


def tournesol():
    """Pétales jaunes, cœur orangé : la couleur du bec, sans bec."""
    b = Builder("Leurre_Tournesol")
    b.lathe(T, [(0.1, 0), (0.14, 0.18), (0.11, 0.2), (0, 0.2)], seg=8)
    b.tube(V, (0, 0, 0.2), (0.03, 0, 0.5), 0.02, 0.02, seg=5)
    b.box(V, (0.14, 0.07, 0.015), (0.06, 0.05, 0.34), rot=(0.3, 0, 0.6))
    for i in range(8):
        a = i * math.pi / 4
        b.box(J, (0.02, 0.09, 0.15), (0.05, 0.13 * math.sin(a), 0.6 + 0.13 * math.cos(a)), rot=(-a, 0, 0))
    b.cyl(O, 0.085, 0.035, xf((0.06, 0, 0.6), rot=(0, H, 0)), seg=10)
    return b


def valise():
    b = Builder("Leurre_Valise")
    b.rbox(J, (0.42, 0.15, 0.3), (0, 0, 0.19), bevel=0.04)
    b.box(G, (0.43, 0.155, 0.02), (0, 0, 0.19))
    b.box(G, (0.14, 0.03, 0.05), (0, 0, 0.365))
    for x in (0.15, -0.15):
        b.cyl(N, 0.03, 0.1, xf((x, 0, 0.03), rot=(H, 0, 0)), seg=6)
    return b


def parapluie():
    b = Builder("Leurre_Parapluie")
    b.lathe(J, [(0.245, 0.3), (0.2, 0.37), (0.1, 0.44), (0, 0.47)], seg=8)
    b.cyl(G, 0.012, 0.44, xf((0, 0, 0.25)), seg=5)
    b.tube(G, (0, 0, 0.03), (0.05, 0, 0.0), 0.012, 0.012, seg=4)
    b.sphere(G, 0.02, xf((0, 0, 0.48)), u=5, v=3)
    return b


def panneau():
    b = Builder("Leurre_Panneau")
    b.cyl(G, 0.02, 0.5, xf((0, 0, 0.25)), seg=6)
    b.box(J, (0.03, 0.3, 0.3), (0, 0, 0.62), rot=(math.pi / 4, 0, 0))
    b.box(N, (0.035, 0.05, 0.14), (0, 0, 0.64))
    b.box(N, (0.035, 0.05, 0.04), (0, 0, 0.53))
    return b


ASSETS = [banane, citron, fromage, sous_marin, bus_scolaire, seau, eponge, smiley, tournesol, valise,
          parapluie, panneau, arrosoir, botte, ballon, canard, canard_loin, plot, borne_incendie, parasol, taxi, boite_aux_lettres, jardiniere, casque]


def taille_jaune(obj):
    """Dimensions (x, y, z) de la boîte englobant les faces jaunes."""
    mesh = obj.data
    idx = [i for i, m in enumerate(mesh.materials) if m.name == J]
    pts = [mesh.vertices[v].co for p in mesh.polygons if p.material_index in idx for v in p.vertices]
    return [round(max(p[a] for p in pts) - min(p[a] for p in pts), 3) for a in range(3)]


def main():
    if bpy.app.background:  # pas de cube/caméra par défaut dans props.blend
        bpy.ops.wm.read_factory_settings(use_empty=True)
    old =bpy.data.collections.get(COLLECTION)
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
