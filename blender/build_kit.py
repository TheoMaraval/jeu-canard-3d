"""Kit de modèles instanciés dans les villes : personnages, coiffes, véhicules, arbres, mobilier.

    blender --background --python blender/build_kit.py

Écrit blender/kit.blend (repris par build_quartier.py pour mesurer ce qui cache quoi) et
assets/kit.glb (instancié par l'app). Tous les modèles regardent vers +x, posés à z = 0.

Matériaux :
  T_<rôle> : teinte choisie par instance (T_haut, T_bas, T_peau, T_cheveux, T_caisse…) ;
             4 rôles au plus par modèle.
  K_<nom>  : couleur fixe.
Direction artistique (skills chibi-style, cartoon-style, vehicle-artist) : personnages
de 4 têtes environ, grosse tête, mains et pieds simplifiés ; volumes arrondis ; chaque
système lisible séparément (caisse, vitres, roues, phares).
"""
import math
import os
import sys

import bpy

ROOT = (os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if "__file__" in globals() else os.getcwd())
sys.path.insert(0, os.path.join(ROOT, "blender"))

from citygen.geo import Builder, register, xf  # noqa: E402
from citygen.layout import KIT  # noqa: E402

register({
    # teintes par défaut (aperçus Blender) ; l'app les remplace instance par instance
    "T_haut": "#2F74D0", "T_bas": "#2B3F6B", "T_peau": "#F2C6A0", "T_cheveux": "#5A3A22",
    "T_chapeau": "#E0392B", "T_caisse": "#E0392B", "T_toit": "#FFD21E", "T_feuille": "#4FA84A",
    "T_toile": "#E0392B",
    "K_Chaussure": "#3A2E2A", "K_Oeil": "#16151A", "K_Blanc": "#FAF6EC", "K_Fer": "#2A2D34",
    "K_Bois": "#B07A48", "K_Tronc": "#8A5A3A", "K_Pneu": "#22232A", "K_Chrome": "#9AA3AD",
    "K_VitreAuto": "#3D5A80", "K_Phare": "#FFF3C4", "K_Feu": "#D83A2E", "K_Lampe": "#FFF6E0",
    "K_Vert": "#2F6B4A", "K_Orange": "#F28C28", "K_Rouge": "#D8342B", "K_Pomme": "#7DBB3C",
    "K_Tache": "#4A3B33", "K_Museau": "#F0A8A8", "K_Interieur": "#3A3550",
})
H = math.pi / 2
TETE = {"debout": 1.37, "assis": 1.25, "buste": 0.81}  # hauteur du centre de la tête


# ---- personnages -------------------------------------------------------------
def perso(nom, pose="debout", pas=0.0, robe=False, raye=False, salue=False):
    b = Builder(nom)
    dz = TETE[pose] - TETE["debout"]  # le buste et la tête descendent quand on s'assoit
    if pose == "debout":
        for s in (1, -1):
            pied = (-s * pas, s * 0.09, 0.09)
            b.tube("T_peau" if robe else "T_bas", pied, (0, s * 0.085, 0.62), 0.05 if robe else 0.07, 0.06 if robe else 0.09)
            b.box("K_Chaussure", (0.22, 0.11, 0.09), (pied[0] + 0.04, pied[1], 0.045))
    elif pose == "assis":
        for s in (1, -1):
            b.tube("T_bas", (0, s * 0.085, 0.5), (0.36, s * 0.09, 0.5), 0.09, 0.075)
            b.tube("T_bas", (0.36, s * 0.09, 0.5), (0.36, s * 0.09, 0.09), 0.075, 0.065)
            b.box("K_Chaussure", (0.22, 0.11, 0.09), (0.40, s * 0.09, 0.045))

    if robe:
        profil = [(0, 0.34), (0.27, 0.36), (0.22, 0.6), (0.18, 0.92), (0.14, 1.08), (0.07, 1.15), (0, 1.16)]
    else:
        profil = [(0, 0.56), (0.16, 0.58), (0.2, 0.72), (0.19, 0.92), (0.15, 1.08), (0.07, 1.15), (0, 1.16)]
    profil = [(r, z + dz) for r, z in profil]
    if raye:  # marinière : bandes alternées
        for i in range(len(profil) - 1):
            b.lathe("T_haut" if i % 2 else "K_Blanc", profil[i:i + 2])
    else:
        b.lathe("T_haut", profil)

    for s in (1, -1):  # bras et mains
        epaule = (0, s * 0.19, 1.06 + dz)
        if salue and s == -1:
            main = (0.05, -0.34, 1.62)
        elif pose == "assis":
            main = (0.25, s * 0.14, 0.62)
        elif pose == "buste":
            main = (0.22, s * 0.16, 0.08)
        else:
            main = (s * pas * 1.1 + 0.02, s * 0.27, 0.69)
        b.tube("K_Blanc" if raye else "T_haut", epaule, main, 0.058, 0.05)
        b.sphere("T_peau", 0.065, xf(main), u=5, v=3)

    zt = TETE[pose]
    b.sphere("T_peau", 0.21, xf((0.01, 0, zt), (1, 1, 0.96)), u=8, v=6)
    for y in (0.075, -0.075):
        b.sphere("K_Oeil", 0.032, xf((0.195, y, zt + 0.02), (0.5, 1, 1.3)), u=5, v=3)
    return b


def coiffe(nom, genre):
    """Cheveux ou chapeau, modelés à la hauteur de tête d'un personnage debout."""
    b = Builder(nom)
    z = TETE["debout"]
    if genre in ("court", "long", "chignon"):
        b.sphere("T_cheveux", 0.228, xf((-0.005, 0, z + 0.005), rot=(0, -math.radians(22), 0)), half=True, u=10, v=6)
    if genre == "long":
        b.sphere("T_cheveux", 0.2, xf((-0.1, 0, z - 0.12), (0.7, 1.05, 1.25)), u=8, v=6)
    if genre == "chignon":
        b.sphere("T_cheveux", 0.1, xf((-0.07, 0, z + 0.25)), u=8, v=6)
    if genre == "chapeau":
        b.lathe("T_chapeau", [(0, z + 0.14), (0.31, z + 0.14), (0.31, z + 0.17), (0.17, z + 0.175),
                              (0.155, z + 0.3), (0, z + 0.31)], seg=10)
    if genre == "casquette":
        b.sphere("T_chapeau", 0.228, xf((0.005, 0, z + 0.02)), half=True, u=10, v=6)
        b.rbox("T_chapeau", (0.18, 0.22, 0.025), (0.27, 0, z + 0.045), bevel=0.01)
    return b


# ---- véhicules -----------------------------------------------------------------
def _roues(b, xs, y, r, larg=0.24):
    for x in xs:
        for s in (1, -1):
            b.cyl("K_Pneu", r, larg, xf((x, s * y, r), rot=(H, 0, 0)), seg=12)
            b.cyl("K_Chrome", r * 0.42, larg + 0.03, xf((x, s * y, r), rot=(H, 0, 0)), seg=8)


def _feux(b, x, y, z, larg=0.3):
    for s in (1, -1):
        b.rbox("K_Phare", (0.07, larg, 0.15), (x, s * y, z), bevel=0.03)
        b.rbox("K_Feu", (0.07, larg, 0.13), (-x, s * y, z), bevel=0.03)


def voiture(nom, taxi=False):
    b = Builder(nom)
    b.rbox("T_caisse", (4.1, 1.75, 0.62), (0, 0, 0.62), bevel=0.16)
    b.rbox("K_VitreAuto", (2.15, 1.56, 0.56), (-0.2, 0, 1.13), bevel=0.2)  # habitacle vitré
    b.rbox("T_caisse", (1.75, 1.5, 0.09), (-0.2, 0, 1.4), bevel=0.04)       # toit
    for x in (-1.1, 0.7):                                                   # montants
        b.rbox("T_caisse", (0.09, 1.6, 0.5), (x, 0, 1.15), bevel=0.03)
    for x in (2.06, -2.06):
        b.rbox("K_Chrome", (0.14, 1.72, 0.16), (x, 0, 0.4), bevel=0.05)     # pare-chocs
    _roues(b, (1.3, -1.3), 0.82, 0.34)
    _feux(b, 2.04, 0.58, 0.7)
    if taxi:
        b.rbox("K_Blanc", (0.5, 0.26, 0.15), (-0.2, 0, 1.52), bevel=0.04)
        b.box("K_Fer", (2.7, 1.77, 0.08), (0, 0, 0.8))                      # bande noire
    return b


def camionnette():
    b = Builder("Camionnette")
    b.rbox("T_caisse", (3.1, 2.0, 1.75), (-0.85, 0, 1.3), bevel=0.14)       # caisse
    b.rbox("T_caisse", (1.55, 1.95, 1.0), (1.5, 0, 0.92), bevel=0.16)       # cabine
    b.rbox("K_VitreAuto", (1.0, 1.8, 0.62), (1.42, 0, 1.6), bevel=0.2)
    b.rbox("T_caisse", (0.9, 1.74, 0.08), (1.3, 0, 1.92), bevel=0.03)
    b.rbox("K_Chrome", (0.14, 1.95, 0.18), (2.28, 0, 0.45), bevel=0.05)
    b.rbox("K_Blanc", (3.14, 2.04, 0.24), (-0.85, 0, 1.02), bevel=0.03)     # bande
    for s in (1, -1):
        b.cyl("K_Blanc", 0.36, 0.03, xf((-0.85, s * 1.0, 1.62), rot=(H, 0, 0)), seg=12)  # logo
    b.box("K_Fer", (0.03, 0.04, 1.5), (-2.41, 0, 1.3))                      # portes arrière
    b.box("K_Fer", (0.05, 0.3, 0.06), (-2.42, 0.2, 1.25))
    _roues(b, (1.45, -1.5), 0.98, 0.38)
    _feux(b, 2.3, 0.68, 0.78)
    return b


def bus():
    b = Builder("Bus")
    b.rbox("T_caisse", (9.0, 2.45, 2.5), (0, 0, 1.65), bevel=0.22)
    b.rbox("K_VitreAuto", (8.3, 2.5, 0.85), (0, 0, 2.05), bevel=0.1)
    for x in (-3.2, -1.6, 0.0, 1.6, 3.2):                                   # montants
        b.rbox("T_caisse", (0.12, 2.52, 0.9), (x, 0, 2.05), bevel=0.02)
    b.rbox("K_VitreAuto", (0.1, 2.1, 1.1), (4.47, 0, 1.95), bevel=0.04)     # pare-brise
    b.rbox("K_Blanc", (8.6, 2.2, 0.08), (0, 0, 2.93), bevel=0.03)
    _roues(b, (3.0, -2.9), 1.2, 0.48, larg=0.3)
    _feux(b, 4.48, 0.85, 0.8, larg=0.35)
    return b


def rickshaw():
    b = Builder("Rickshaw")
    b.rbox("T_caisse", (2.3, 1.3, 0.75), (-0.1, 0, 0.72), bevel=0.2)
    b.rbox("T_caisse", (0.7, 0.7, 0.55), (1.15, 0, 0.6), bevel=0.2)         # nez
    b.rbox("K_Interieur", (1.5, 1.1, 0.55), (-0.25, 0, 1.3), bevel=0.05)    # cabine ouverte
    for x in (0.55, -1.05):
        for s in (1, -1):
            b.tube("K_Fer", (x, s * 0.58, 1.05), (x, s * 0.58, 1.6), 0.03, 0.03, seg=5)
    b.rbox("T_toit", (2.0, 1.36, 0.14), (-0.25, 0, 1.68), bevel=0.06)       # capote
    b.rbox("K_VitreAuto", (0.06, 1.0, 0.45), (0.72, 0, 1.33), bevel=0.02)
    for x, y in ((1.2, 0.0), (-0.9, 0.62), (-0.9, -0.62)):                  # trois roues
        b.cyl("K_Pneu", 0.26, 0.16, xf((x, y, 0.26), rot=(H, 0, 0)), seg=12)
    b.rbox("K_Phare", (0.06, 0.2, 0.14), (1.5, 0, 0.72), bevel=0.03)
    return b


# ---- arbres ----------------------------------------------------------------------
def arbre(nom, masses, tronc=2.4):
    b = Builder(nom)
    b.lathe("K_Tronc", [(0.18, 0), (0.13, tronc * 0.5), (0.1, tronc + 0.3)], seg=7)
    for x, y, z, r in masses:
        b.ico("T_feuille", r, (x, y, z), (1, 1, 0.9), sub=2)
    return b


def arbre_cone():
    b = Builder("Arbre_C")
    b.lathe("K_Tronc", [(0.14, 0), (0.1, 1.7)], seg=7)
    b.lathe("T_feuille", [(0, 1.3), (0.95, 1.9), (0.75, 3.6), (0.4, 4.8), (0, 5.5)], seg=8)
    return b


# ---- mobilier ----------------------------------------------------------------------
def banc():
    b = Builder("Banc")
    for y in (-0.15, 0.0, 0.15):
        b.rbox("K_Bois", (1.5, 0.12, 0.04), (0, y, 0.45), bevel=0.015)
    for z in (0.62, 0.8):
        b.rbox("K_Bois", (1.5, 0.04, 0.13), (0, 0.24, z), bevel=0.015)
    for x in (-0.6, 0.6):
        b.box("K_Fer", (0.05, 0.5, 0.06), (x, 0.02, 0.42))
        b.box("K_Fer", (0.05, 0.05, 0.9), (x, 0.24, 0.45))
        b.box("K_Fer", (0.05, 0.05, 0.42), (x, -0.2, 0.21))
    return b


def lampadaire():
    b = Builder("Lampadaire")
    b.lathe("K_Fer", [(0.15, 0), (0.11, 0.3), (0.05, 0.45), (0.045, 4.0), (0.1, 4.05)], seg=8)
    b.lathe("K_Lampe", [(0.08, 4.05), (0.17, 4.2), (0.14, 4.55), (0.05, 4.62)], seg=8)
    b.lathe("K_Fer", [(0.19, 4.6), (0.05, 4.75), (0, 4.85)], seg=8)
    return b


def poubelle():
    b = Builder("Poubelle")
    b.lathe("K_Vert", [(0.2, 0), (0.25, 0.75), (0.28, 0.78), (0.28, 0.83), (0.2, 0.86), (0, 0.86)], seg=10)
    return b


def table_cafe():
    b = Builder("Table_Cafe")
    b.lathe("K_Fer", [(0.22, 0), (0.05, 0.05), (0.04, 0.7)], seg=8)
    b.lathe("K_Blanc", [(0, 0.7), (0.42, 0.7), (0.42, 0.75), (0, 0.75)], seg=12)
    return b


def chaise():
    b = Builder("Chaise")
    b.rbox("T_toile", (0.38, 0.38, 0.05), (0, 0, 0.45), bevel=0.02)
    b.rbox("T_toile", (0.04, 0.38, 0.32), (-0.18, 0, 0.72), bevel=0.02)
    for x in (-0.16, 0.16):
        for y in (-0.16, 0.16):
            b.tube("K_Fer", (x, y, 0), (x, y, 0.88 if x < 0 else 0.43), 0.02, 0.02, seg=5)
    return b


def parasol():
    b = Builder("Parasol")
    b.lathe("K_Fer", [(0.2, 0), (0.2, 0.06), (0.03, 0.08), (0.03, 2.35)], seg=8)
    b.lathe("T_toile", [(1.3, 2.0), (1.28, 2.06), (0.65, 2.3), (0, 2.45)], seg=10)
    b.sphere("K_Blanc", 0.05, xf((0, 0, 2.47)), u=6, v=4)
    return b


def etal():
    """Étal de marché. Le bout +x de la table reste libre : la ville y pose un objet."""
    b = Builder("Etal")
    b.rbox("K_Bois", (2.0, 0.85, 0.07), (0, 0, 0.78), bevel=0.02)
    for x in (-0.9, 0.9):
        for y in (-0.36, 0.36):
            b.tube("K_Bois", (x, y, 0), (x, y, 0.76), 0.035, 0.035, seg=5)
    fruits = ("K_Orange", "K_Rouge", "K_Pomme")
    for i, x in enumerate((-0.7, -0.15)):
        b.rbox("K_Bois", (0.5, 0.6, 0.16), (x, 0, 0.9), bevel=0.02)
        for j in range(6):
            b.sphere(fruits[(i + j) % 3], 0.09, xf((x - 0.14 + (j % 3) * 0.14, -0.14 + (j // 3) * 0.28, 1.0)), u=5, v=3)
    for x in (-0.95, 0.95):
        b.tube("K_Fer", (x, 0.4, 0), (x, 0.4, 2.2), 0.03, 0.03, seg=5)
    for i in range(5):  # auvent rayé
        b.rbox("T_toile" if i % 2 == 0 else "K_Blanc", (0.46, 1.35, 0.06), (-0.92 + i * 0.46, 0.0, 2.2), bevel=0.02)
    return b


def vache():
    b = Builder("Vache")
    b.rbox("K_Blanc", (1.5, 0.62, 0.72), (0, 0, 0.98), bevel=0.22)
    for x in (-0.55, 0.55):
        for s in (1, -1):
            b.tube("K_Blanc", (x, s * 0.2, 0.05), (x, s * 0.2, 0.7), 0.07, 0.08, seg=6)
    b.rbox("K_Blanc", (0.48, 0.36, 0.4), (0.95, 0, 1.28), bevel=0.13)
    b.rbox("K_Museau", (0.14, 0.3, 0.2), (1.2, 0, 1.2), bevel=0.06)
    for s in (1, -1):
        b.sphere("K_Oeil", 0.035, xf((1.1, s * 0.17, 1.36)), u=6, v=4)
        b.cone("K_Bois", 0.04, 0.0, 0.16, xf((0.9, s * 0.15, 1.54)), seg=6)
        b.sphere("K_Tache", 0.2, xf((-0.2 * s, s * 0.3, 1.05), (1.2, 0.25, 0.9)), u=8, v=5)
    b.tube("K_Blanc", (-0.75, 0, 1.2), (-0.92, 0, 0.6), 0.03, 0.03, seg=5)
    return b


ASSETS = [
    lambda: perso("Perso_Debout"),
    lambda: perso("Perso_Marche", pas=0.14),
    lambda: perso("Perso_Salue", salue=True),
    lambda: perso("Perso_Robe", robe=True),
    lambda: perso("Perso_Raye", raye=True, pas=0.08),
    lambda: perso("Perso_Assis", pose="assis"),
    lambda: perso("Perso_Buste", pose="buste"),
    lambda: coiffe("Coiffe_Court", "court"),
    lambda: coiffe("Coiffe_Long", "long"),
    lambda: coiffe("Coiffe_Chignon", "chignon"),
    lambda: coiffe("Coiffe_Chapeau", "chapeau"),
    lambda: coiffe("Coiffe_Casquette", "casquette"),
    lambda: voiture("Voiture"),
    lambda: voiture("Taxi", taxi=True),
    camionnette, bus, rickshaw,
    lambda: arbre("Arbre_A", [(0, 0, 3.2, 1.25), (0.6, 0.2, 3.8, 0.85), (-0.5, -0.3, 3.9, 0.9), (0.05, 0.45, 4.4, 0.7)]),
    lambda: arbre("Arbre_B", [(0, 0, 3.4, 1.4), (0.25, 0.1, 4.6, 0.9)], tronc=2.6),
    arbre_cone, banc, lampadaire, poubelle, table_cafe, chaise, parasol, etal, vache,
]


def main():
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Kit")
    bpy.context.scene.collection.children.link(col)
    report, x = {}, 0.0
    for fn in ASSETS:
        obj = fn().build(col, x)
        x += max(1.2, obj.dimensions.x + 0.8)
        obj.data.calc_loop_triangles()
        roles = [m.name[2:] for m in obj.data.materials if m.name.startswith("T_")]
        assert len(roles) <= 4, f"{obj.name} : {len(roles)} teintes, 4 au plus"
        report[obj.name] = {"tris": len(obj.data.loop_triangles), "teintes": roles}
    manquants = set(KIT) - set(report)
    assert not manquants, f"modèles attendus par layout.py mais absents du kit : {sorted(manquants)}"

    blend = os.path.join(ROOT, "blender", "kit.blend")
    glb = os.path.join(ROOT, "assets", "kit.glb")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    bpy.ops.object.select_all(action="DESELECT")
    for o in col.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    return {"modeles": report, "glb_ko": round(os.path.getsize(glb) / 1024)}


result = main()
print("RESULTAT", result)
