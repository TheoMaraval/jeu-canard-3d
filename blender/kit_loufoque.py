"""Deuxième partie du kit : animaux, tags, désordre, végétation, accessoires de saynètes,
coiffes loufoques. Importé par build_kit.py. Mêmes conventions : +x vers l'avant, z = 0 au sol,
T_<rôle> teinté par instance, K_<nom> fixe.

Les modèles « muraux » (tags, lierre, planches, fissure) sont dans le plan XZ, face visible
vers -y : la ville les tourne pour les plaquer sur une façade.
"""
import math
import random

from citygen.geo import Builder, register, xf

register({
    "T_poil": "#8A5A3A", "T_tag": "#E0392B", "T_flaque": "#58B8E8", "T_fleur": "#F07AA8",
    "T_b1": "#E0392B", "T_b2": "#2F74D0", "T_b3": "#3DAA5A",
    "K_Pigeon": "#8C93A0", "K_Gris": "#9A9AA6", "K_Carton": "#C9A070", "K_Fumee": "#8E8E96",
    "K_Eau": "#58B8E8", "K_Sable": "#E3CFA0", "K_Terre": "#A8603C", "K_Bleu": "#2F74D0",
    "K_Rose": "#F07AA8", "K_Or": "#C8922A", "K_Ivoire": "#F4EEDC", "K_Peau": "#E0A77A",
    "K_Palme": "#B08A5A",
})
H = math.pi / 2
TETE = 1.37


# ---- animaux -----------------------------------------------------------------
def chien():
    b = Builder("Chien")
    b.rbox("T_poil", (0.5, 0.2, 0.22), (0, 0, 0.34), bevel=0.08)
    b.rbox("T_poil", (0.2, 0.18, 0.18), (0.31, 0, 0.5), bevel=0.06)
    b.rbox("T_poil", (0.12, 0.1, 0.08), (0.44, 0, 0.46), bevel=0.03)
    b.sphere("K_Oeil", 0.025, xf((0.5, 0, 0.48)), u=5, v=3)
    for s in (1, -1):
        b.sphere("K_Oeil", 0.02, xf((0.4, s * 0.07, 0.54)), u=5, v=3)
        b.box("K_Tache", (0.06, 0.03, 0.12), (0.26, s * 0.1, 0.56))  # oreilles tombantes
        for x in (0.17, -0.17):
            b.tube("T_poil", (x, s * 0.07, 0.0), (x, s * 0.07, 0.26), 0.035, 0.04, seg=5)
    b.tube("T_poil", (-0.25, 0, 0.4), (-0.36, 0, 0.6), 0.03, 0.02, seg=5)
    return b


def chat():
    b = Builder("Chat")
    b.lathe("T_poil", [(0, 0), (0.11, 0.02), (0.12, 0.15), (0.07, 0.3), (0, 0.32)], seg=8)
    b.sphere("T_poil", 0.09, xf((0.03, 0, 0.38)), u=8, v=5)
    for s in (1, -1):
        b.cone("T_poil", 0.035, 0.0, 0.07, xf((0.02, s * 0.055, 0.48)), seg=4)
        b.sphere("K_Oeil", 0.016, xf((0.11, s * 0.035, 0.39)), u=5, v=3)
    b.tube("T_poil", (-0.1, 0, 0.03), (-0.2, 0.14, 0.03), 0.03, 0.025, seg=5)
    return b


def pigeon():
    b = Builder("Pigeon")
    b.sphere("K_Pigeon", 0.07, xf((0, 0, 0.11), (1.5, 1, 1)), u=6, v=4)
    b.sphere("K_Pigeon", 0.042, xf((0.09, 0, 0.19)), u=6, v=4)
    b.cone("K_Fer", 0.015, 0.0, 0.04, xf((0.14, 0, 0.185), rot=(0, H, 0)), seg=4)
    b.box("K_Fer", (0.1, 0.07, 0.015), (-0.13, 0, 0.1))
    return b


def poule():
    b = Builder("Poule")
    b.sphere("T_poil", 0.13, xf((0, 0, 0.22), (1.25, 1, 1)), u=8, v=5)
    b.sphere("T_poil", 0.06, xf((0.14, 0, 0.38)), u=6, v=4)
    b.box("K_Rouge", (0.06, 0.02, 0.05), (0.14, 0, 0.45))
    b.cone("K_Orange", 0.02, 0.0, 0.05, xf((0.21, 0, 0.37), rot=(0, H, 0)), seg=4)
    b.sphere("K_Oeil", 0.012, xf((0.18, 0.04, 0.4)), u=4, v=3)
    b.box("T_poil", (0.1, 0.05, 0.14), (-0.17, 0, 0.32), rot=(0, 0.5, 0))
    for s in (1, -1):
        b.tube("K_Orange", (0.02, s * 0.05, 0.0), (0.02, s * 0.05, 0.12), 0.012, 0.012, seg=4)
    return b


def singe():
    b = Builder("Singe")
    b.lathe("T_poil", [(0, 0), (0.14, 0.03), (0.15, 0.25), (0.1, 0.45), (0, 0.48)], seg=8)
    b.sphere("T_poil", 0.11, xf((0.02, 0, 0.56)), u=8, v=5)
    b.sphere("K_Peau", 0.07, xf((0.08, 0, 0.54), (0.6, 1, 1)), u=6, v=4)
    for s in (1, -1):
        b.sphere("K_Oeil", 0.014, xf((0.125, s * 0.03, 0.57)), u=4, v=3)
        b.sphere("K_Peau", 0.035, xf((0.0, s * 0.11, 0.57)), u=5, v=3)
        b.tube("T_poil", (0, s * 0.13, 0.38), (0.12, s * 0.2, 0.1), 0.035, 0.03, seg=5)
    b.tube("T_poil", (-0.12, 0, 0.05), (-0.3, 0.05, 0.3), 0.025, 0.02, seg=5)
    b.tube("T_poil", (-0.3, 0.05, 0.3), (-0.22, 0.1, 0.5), 0.02, 0.02, seg=5)
    return b


def elephant():
    b = Builder("Elephant")
    b.rbox("K_Gris", (2.4, 1.3, 1.5), (0, 0, 1.8), bevel=0.5)
    b.rbox("K_Gris", (1.0, 1.0, 1.1), (1.45, 0, 2.15), bevel=0.4)
    b.tube("K_Gris", (1.9, 0, 2.0), (2.25, 0, 1.1), 0.2, 0.14, seg=7)
    b.tube("K_Gris", (2.25, 0, 1.1), (2.05, 0, 0.5), 0.14, 0.1, seg=7)
    for s in (1, -1):
        b.rbox("K_Gris", (0.14, 0.85, 1.0), (1.2, s * 0.75, 2.2), rot=(0, 0, s * 0.5), bevel=0.06)
        b.cone("K_Ivoire", 0.06, 0.0, 0.5, xf((2.0, s * 0.3, 1.75), rot=(0, 2.0, 0)), seg=6)
        b.sphere("K_Oeil", 0.045, xf((1.9, s * 0.38, 2.4)), u=5, v=3)
        for x in (0.75, -0.75):
            b.tube("K_Gris", (x, s * 0.4, 0.0), (x, s * 0.4, 1.3), 0.26, 0.28, seg=7)
    b.rbox("T_toile", (1.3, 1.36, 0.9), (-0.1, 0, 2.2), bevel=0.3)       # tapis d'apparat
    b.rbox("K_Or", (1.0, 1.4, 0.12), (-0.1, 0, 1.85), bevel=0.04)
    b.tube("K_Gris", (-1.2, 0, 2.2), (-1.45, 0, 1.3), 0.05, 0.04, seg=5)
    return b


# ---- tags et marques murales (plan XZ, face vers -y) -------------------------
POLICE = {
    "C": ["###", "#..", "#..", "#..", "###"], "O": ["###", "#.#", "#.#", "#.#", "###"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "N": ["#.#", "###", "###", "###", "#.#"],
    "Z": ["###", "..#", ".#.", "#..", "###"], "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "P": ["##.", "#.#", "##.", "#..", "#.."], "L": ["#..", "#..", "#..", "#..", "###"],
    "!": [".#.", ".#.", ".#.", "...", ".#."],
}
DESSINS = {
    "Coeur": [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."],
    "Smiley": [".#####.", "#.....#", "#.#.#.#", "#.....#", "#.###.#", "#.....#", ".#####."],
    "Couronne": ["#..#..#", "#.###.#", "#######", "#######"],
    "Fleche": ["...#...", "..##...", ".######", "..##...", "...#..."],
    "Eclair": ["..##", "..#.", ".##.", ".###", "..#.", ".#..", "#..."],
    "Canard": ["...###...", "..##.#.##", "..#####..", "#..###...", "########.", "########.", ".######.."],
}


def mot(texte):
    lignes = []
    for ligne in texte.split("/"):
        if lignes:
            lignes.append("")
        lignes += [".".join(POLICE[c][r] for c in ligne) for r in range(5)]
    large = max(len(x) for x in lignes)
    return [x.ljust(large, ".") for x in lignes]


def pixels(nom, lignes, px=0.12, mat="T_tag"):
    """Dessin en pixels épais de 3 cm ; les suites horizontales sont fusionnées."""
    b = Builder(nom)
    large = max(len(x) for x in lignes)
    for r, ligne in enumerate(lignes):
        z = (len(lignes) - 1 - r + 0.5) * px
        c = 0
        while c < len(ligne):
            if ligne[c] != "#":
                c += 1
                continue
            d = c
            while d < len(ligne) and ligne[d] == "#":
                d += 1
            b.box(mat, ((d - c) * px, 0.03, px), (((c + d) / 2 - large / 2) * px, -0.015, z))
            c = d
    return b


def lierre():
    b = Builder("Lierre")
    rng = random.Random(7)
    for i in range(10):
        b.ico("T_feuille", rng.uniform(0.28, 0.5), (rng.uniform(-0.6, 0.6) * (1 - i / 14), -0.06, 0.3 + i * 0.3),
              (1, 0.25, 1), sub=1)
    return b


def planches():
    b = Builder("Planches")  # fenêtre condamnée, centrée sur l'origine
    for z, a in ((0.45, 0.08), (0.0, -0.12), (-0.45, 0.15)):
        b.box("K_Bois", (1.35, 0.04, 0.2), (0, -0.02, z), rot=(0, a, 0))
    for x in (-0.55, 0.55):
        for z in (0.45, 0.0, -0.45):
            b.box("K_Fer", (0.03, 0.05, 0.03), (x, -0.03, z))
    return b


# ---- désordre et accessoires de saynètes -----------------------------------------
def echelle():
    """Échelle appuyée contre un mur situé du côté -x."""
    b = Builder("Echelle")
    for s in (1, -1):
        b.tube("K_Bois", (0.75, s * 0.22, 0), (-0.02, s * 0.22, 3.3), 0.035, 0.035, seg=5)
    for i in range(8):
        t = 0.1 + i * 0.11
        b.box("K_Bois", (0.04, 0.44, 0.04), (0.75 - 0.77 * t, 0, 3.3 * t))
    return b


def flaque():
    b = Builder("Flaque")
    b.lathe("T_flaque", [(0, 0.0), (0.9, 0.0), (0.85, 0.02), (0, 0.025)], xf(scale=(1, 0.7, 1)), seg=9)
    b.lathe("T_flaque", [(0, 0.0), (0.45, 0.0), (0.4, 0.02), (0, 0.025)], xf((0.75, 0.35, 0), (1, 0.8, 1)), seg=7)
    return b


def cartons():
    b = Builder("Cartons")
    for x, y, z, r in ((0, 0, 0.2, 0.2), (0.48, 0.1, 0.2, -0.3), (0.2, 0.05, 0.6, 0.5)):
        b.rbox("K_Carton", (0.5, 0.42, 0.4), (x, y, z), rot=(0, 0, r), bevel=0.02, smooth=False)
        b.box("K_Bois", (0.52, 0.06, 0.41), (x, y, z), rot=(0, 0, r))
    return b


def canape():
    b = Builder("Canape")
    b.rbox("T_toile", (0.85, 1.8, 0.4), (0, 0, 0.3), bevel=0.1)
    b.rbox("T_toile", (0.25, 1.8, 0.55), (-0.32, 0, 0.7), bevel=0.1)
    for s in (1, -1):
        b.rbox("T_toile", (0.85, 0.22, 0.3), (0, s * 0.82, 0.6), bevel=0.08)
    return b


def piano():
    """Piano droit suspendu : la corde monte de 6 m au-dessus de lui."""
    b = Builder("Piano_Suspendu")
    b.rbox("K_Fer", (0.6, 1.5, 1.2), (0, 0, 0.6), bevel=0.05)
    b.box("K_Blanc", (0.25, 1.3, 0.05), (0.4, 0, 0.72))
    b.box("K_Fer", (0.28, 1.4, 0.06), (0.4, 0, 0.66))
    for s in (1, -1):
        b.tube("K_Bois", (0, s * 0.7, 1.2), (0, 0, 2.2), 0.025, 0.025, seg=4)
    b.tube("K_Bois", (0, 0, 2.2), (0, 0, 7.2), 0.03, 0.03, seg=4)
    return b


def fumee():
    b = Builder("Fumee")
    for x, y, z, r in ((0, 0, 0.4, 0.3), (0.15, 0.1, 1.0, 0.45), (0.05, -0.2, 1.8, 0.6), (0.35, 0.1, 2.7, 0.75)):
        b.ico("K_Fumee", r, (x, y, z), sub=2)
    return b


def geyser():
    """Borne à incendie rouge éventrée et son jet d'eau."""
    b = Builder("Borne_Geyser")
    b.lathe("K_Rouge", [(0.14, 0), (0.1, 0.05), (0.1, 0.5), (0.13, 0.55), (0.06, 0.62)], seg=8)
    b.lathe("K_Eau", [(0.07, 0.6), (0.09, 2.4), (0.45, 3.0), (0.3, 3.25), (0, 3.3)], seg=8)
    rng = random.Random(3)
    for _ in range(9):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0.4, 1.1)
        b.sphere("K_Eau", 0.07, xf((d * math.cos(a), d * math.sin(a), rng.uniform(1.2, 2.9))), u=5, v=3)
    return b


def fruits_sol():
    b = Builder("Fruits_Sol")
    rng = random.Random(11)
    b.rbox("K_Bois", (0.5, 0.6, 0.16), (0, 0, 0.25), rot=(0.9, 0, 0.3), bevel=0.02, smooth=False)
    for i in range(14):
        a, d = rng.uniform(0, 6.28), rng.uniform(0.3, 1.3)
        b.sphere(("K_Orange", "K_Rouge", "K_Pomme")[i % 3], 0.085, xf((d * math.cos(a), d * math.sin(a), 0.085)), u=5, v=3)
    return b


def tambour():
    b = Builder("Tambour")
    b.cyl("K_Rouge", 0.36, 0.3, xf((0, 0, 0), rot=(H, 0, H)), seg=12)
    b.cyl("K_Blanc", 0.33, 0.32, xf((0, 0, 0), rot=(H, 0, H)), seg=12)
    return b


def barriere():
    b = Builder("Barriere")
    for i in range(5):
        b.box("K_Rouge" if i % 2 == 0 else "K_Blanc", (0.34, 0.05, 0.18), (-0.68 + i * 0.34, 0, 0.9))
    b.box("K_Blanc", (1.7, 0.04, 0.08), (0, 0, 0.5))
    for x in (-0.75, 0.75):
        b.box("K_Fer", (0.05, 0.05, 1.0), (x, 0, 0.5))
        b.box("K_Fer", (0.06, 0.5, 0.05), (x, 0, 0.025))
    return b


def trou():
    b = Builder("Trou")
    b.lathe("K_Terre", [(0, 0.0), (1.15, 0.0), (1.0, 0.1), (0.9, 0.04), (0, 0.04)], seg=9)
    b.lathe("K_Interieur", [(0, 0.045), (0.85, 0.045), (0, 0.05)], seg=9)
    return b


def tas_sable():
    b = Builder("Tas_Sable")
    b.lathe("K_Sable", [(0.95, 0), (0.55, 0.4), (0.15, 0.68), (0, 0.72)], seg=9)
    return b


def brouette():
    b = Builder("Brouette")
    b.rbox("K_Vert", (0.7, 0.5, 0.25), (0, 0, 0.5), bevel=0.06)
    b.rbox("K_Sable", (0.55, 0.4, 0.12), (0, 0, 0.62), bevel=0.05)
    b.cyl("K_Pneu", 0.17, 0.08, xf((0.48, 0, 0.17), rot=(H, 0, 0)), seg=10)
    for s in (1, -1):
        b.tube("K_Fer", (0.2, s * 0.2, 0.38), (-0.8, s * 0.26, 0.55), 0.02, 0.02, seg=4)
        b.tube("K_Fer", (-0.25, s * 0.2, 0.38), (-0.3, s * 0.2, 0.0), 0.02, 0.02, seg=4)
    return b


def confettis():
    b = Builder("Confettis")
    rng = random.Random(5)
    for i in range(34):
        a, d = rng.uniform(0, 6.28), rng.uniform(0.1, 1.7)
        b.box(("K_Rouge", "K_Pomme", "K_Orange", "K_Bleu", "K_Rose")[i % 5], (0.09, 0.06, 0.01),
              (d * math.cos(a), d * math.sin(a), 0.006), rot=(0, 0, rng.uniform(0, 3)))
    return b


def sacs_poubelle():
    b = Builder("Sacs_Poubelle")
    for x, y, r in ((0, 0, 0.36), (0.5, 0.15, 0.3), (0.2, -0.4, 0.32), (0.3, 0.05, 0.28)):
        z = 0.55 if r == 0.28 else r * 0.75
        b.ico("K_Fer", r, (x, y, z), (1, 1, 0.8), sub=1)
        b.cone("K_Fer", 0.05, 0.0, 0.12, xf((x, y, z + r * 0.8)), seg=4)
    return b


def poubelle_renversee():
    b = Builder("Poubelle_Renversee")
    b.lathe("K_Vert", [(0.2, 0), (0.25, 0.75), (0.28, 0.78), (0.28, 0.83)], xf((0, 0, 0.27), rot=(0, H, 0)), seg=10)
    rng = random.Random(9)
    for i in range(7):
        b.box(("K_Carton", "K_Blanc", "K_Rouge", "K_Bleu")[i % 4], (0.14, 0.1, 0.06),
              (0.95 + rng.uniform(0, 0.8), rng.uniform(-0.45, 0.45), 0.03), rot=(0, 0, rng.uniform(0, 3)))
    return b


def transat():
    b = Builder("Transat")
    b.box("T_toile", (1.0, 0.55, 0.04), (0.15, 0, 0.28), rot=(0, -0.25, 0))
    b.box("T_toile", (0.75, 0.55, 0.04), (-0.55, 0, 0.6), rot=(0, 0.9, 0))
    for s in (1, -1):
        b.tube("K_Bois", (0.65, s * 0.3, 0.0), (-0.85, s * 0.3, 0.9), 0.025, 0.025, seg=4)
        b.tube("K_Bois", (-0.6, s * 0.3, 0.0), (0.3, s * 0.3, 0.4), 0.025, 0.025, seg=4)
    return b


def chevalet():
    b = Builder("Chevalet")
    for p in ((0.0, 0.3, 0), (0.0, -0.3, 0), (-0.5, 0, 0)):
        b.tube("K_Bois", p, (-0.12, 0, 1.6), 0.025, 0.025, seg=4)
    b.box("K_Blanc", (0.04, 0.7, 0.9), (0.02, 0, 1.1), rot=(0, -0.12, 0))
    b.box("T_toile", (0.045, 0.45, 0.4), (0.03, 0.05, 1.15), rot=(0, -0.12, 0))
    b.box("K_Pomme", (0.046, 0.2, 0.25), (0.035, -0.15, 0.95), rot=(0, -0.12, 0))
    return b


def ballons():
    """Bouquet de ballons tenu à hauteur de main."""
    b = Builder("Ballons")
    for i, (y, x, z) in enumerate(((0, 0, 2.3), (0.3, 0.1, 2.05), (-0.3, -0.05, 2.1), (0.12, -0.25, 1.85), (-0.15, 0.25, 1.8))):
        b.sphere(f"T_b{i % 3 + 1}", 0.2, xf((x, y, z), (1, 1, 1.15)), u=8, v=5)
        b.tube("K_Fer", (0, 0, 1.0), (x, y, z - 0.22), 0.008, 0.008, seg=3)
    return b


def velo():
    b = Builder("Velo")
    for x in (0.52, -0.52):
        b.cyl("K_Pneu", 0.33, 0.04, xf((x, 0, 0.33), rot=(H, 0, 0)), seg=12)
        b.cyl("K_Chrome", 0.26, 0.045, xf((x, 0, 0.33), rot=(H, 0, 0)), seg=12)
    for a, c in (((-0.52, 0, 0.33), (-0.15, 0, 0.85)), ((-0.15, 0, 0.85), (0.38, 0, 0.9)), ((0.38, 0, 0.9), (0.52, 0, 0.33)),
                 ((-0.15, 0, 0.85), (0.0, 0, 0.35)), ((0.0, 0, 0.35), (-0.52, 0, 0.33)), ((0.0, 0, 0.35), (0.38, 0, 0.9))):
        b.tube("T_caisse", a, c, 0.025, 0.025, seg=4)
    b.box("K_Fer", (0.22, 0.1, 0.05), (-0.17, 0, 0.93))
    b.box("K_Fer", (0.05, 0.5, 0.04), (0.38, 0, 1.02))
    return b


def lampadaire_tordu():
    b = Builder("Lampadaire_Tordu")
    b.lathe("K_Fer", [(0.15, 0), (0.11, 0.3), (0.05, 0.45), (0.045, 2.2)], seg=8)
    b.tube("K_Fer", (0, 0, 2.2), (0.9, 0.2, 3.3), 0.045, 0.045, seg=6)
    b.tube("K_Fer", (0.9, 0.2, 3.3), (1.7, 0.3, 2.9), 0.045, 0.04, seg=6)
    b.sphere("K_Lampe", 0.17, xf((1.8, 0.32, 2.8)), u=8, v=5)
    return b


# ---- végétation ---------------------------------------------------------------------
def pot(nom, fleurs):
    b = Builder(nom)
    b.lathe("K_Terre", [(0.16, 0), (0.22, 0.32), (0.24, 0.34), (0.2, 0.36), (0, 0.36)], seg=8)
    if fleurs:
        b.ico("T_feuille", 0.22, (0, 0, 0.5), (1, 1, 0.7), sub=1)
        for a in range(5):
            b.sphere("T_fleur", 0.07, xf((0.17 * math.cos(a * 1.26), 0.17 * math.sin(a * 1.26), 0.62)), u=5, v=3)
    else:
        b.ico("T_feuille", 0.3, (0, 0, 0.62), (1, 1, 1.1), sub=1)
        b.ico("T_feuille", 0.2, (0.1, 0.05, 0.95), sub=1)
    return b


def buisson():
    b = Builder("Buisson")
    for x, y, z, r in ((0, 0, 0.45, 0.6), (0.5, 0.2, 0.38, 0.45), (-0.45, -0.1, 0.36, 0.42), (0.1, -0.4, 0.3, 0.36)):
        b.ico("T_feuille", r, (x, y, z), (1, 1, 0.85), sub=2 if r > 0.5 else 1)
    return b


def massif():
    b = Builder("Massif_Fleurs")
    b.ico("T_feuille", 0.8, (0, 0, 0.1), (1.2, 0.8, 0.35), sub=2)
    rng = random.Random(4)
    for _ in range(11):
        b.sphere("T_fleur", 0.09, xf((rng.uniform(-0.75, 0.75), rng.uniform(-0.5, 0.5), 0.36)), u=5, v=3)
    return b


def palmier():
    b = Builder("Palmier")
    pts = [(0, 0, 0), (0.12, 0, 1.6), (0.3, 0, 3.2), (0.55, 0, 4.6)]
    for a, c in zip(pts, pts[1:]):
        b.tube("K_Palme", a, c, 0.17, 0.14, seg=7)
    for i in range(8):
        ang = i * math.pi / 4
        b.box("T_feuille", (1.9, 0.34, 0.05), (0.55 + 0.85 * math.cos(ang), 0.85 * math.sin(ang), 4.45),
              rot=(0, 0.42, ang), haut=(0.5, 0.2))
    for x, y in ((0.7, 0.1), (0.45, -0.15), (0.5, 0.18)):
        b.sphere("K_Tronc", 0.11, xf((x, y, 4.42)), u=5, v=3)
    return b


def arbre_branchu():
    b = Builder("Arbre_D")
    b.tube("K_Tronc", (0, 0, 0), (0, 0, 1.8), 0.2, 0.15, seg=7)
    for x, y, z, r in ((0.9, 0.2, 3.3, 1.0), (-0.8, 0.4, 3.6, 0.95), (0.0, -0.7, 4.2, 1.05), (0.1, 0.3, 4.9, 0.8)):
        b.tube("K_Tronc", (0, 0, 1.7), (x * 0.8, y * 0.8, z - 0.3), 0.11, 0.07, seg=5)
        b.ico("T_feuille", r, (x, y, z), (1, 1, 0.9), sub=2)
    return b


# ---- coiffes loufoques (à la hauteur de tête d'un personnage debout) -------------
def coiffe_folle(nom):
    b = Builder("Coiffe_" + nom)
    z = TETE + 0.13
    if nom == "Toque":
        b.lathe("K_Blanc", [(0.17, z), (0.17, z + 0.14), (0.24, z + 0.2), (0.24, z + 0.36), (0, z + 0.4)], seg=10)
    elif nom == "Couronne":
        b.lathe("K_Or", [(0.18, z), (0.2, z + 0.1)], seg=10)
        for i in range(5):
            a = i * 1.257
            b.cone("K_Or", 0.05, 0.0, 0.13, xf((0.19 * math.cos(a), 0.19 * math.sin(a), z + 0.15)), seg=4)
    elif nom == "HautDeForme":
        b.lathe("K_Fer", [(0, z), (0.3, z), (0.3, z + 0.03), (0.17, z + 0.035), (0.18, z + 0.36), (0, z + 0.37)], seg=10)
        b.lathe("K_Rouge", [(0.172, z + 0.04), (0.175, z + 0.1)], seg=10)
    elif nom == "Cone":  # un plot de chantier sur la tête
        b.box("K_Fer", (0.36, 0.36, 0.03), (0, 0, z + 0.015))
        b.lathe("K_Orange", [(0.15, z + 0.03), (0.03, z + 0.5), (0, z + 0.51)], seg=8)
        b.lathe("K_Blanc", [(0.115, z + 0.18), (0.085, z + 0.3)], seg=8)
    elif nom == "Sombrero":
        b.lathe("T_chapeau", [(0, z), (0.5, z + 0.02), (0.52, z + 0.1), (0.48, z + 0.08), (0.2, z + 0.04),
                              (0.16, z + 0.3), (0, z + 0.34)], seg=10)
    elif nom == "Heaume":
        b.lathe("K_Chrome", [(0.24, TETE - 0.24), (0.25, TETE + 0.15), (0.2, TETE + 0.27), (0, TETE + 0.31)], seg=10)
        b.box("K_Fer", (0.04, 0.3, 0.04), (0.235, 0, TETE + 0.03))
        b.box("K_Rouge", (0.3, 0.03, 0.22), (-0.05, 0, TETE + 0.4))
    elif nom == "Helice":
        b.sphere("T_chapeau", 0.228, xf((0.005, 0, TETE + 0.02)), half=True, u=10, v=6)
        b.box("K_Fer", (0.02, 0.02, 0.1), (0, 0, z + 0.14))
        b.box("K_Rouge", (0.5, 0.07, 0.015), (0, 0, z + 0.19))
    elif nom == "Lapin":
        for s in (1, -1):
            b.rbox("K_Blanc", (0.05, 0.1, 0.42), (-0.02, s * 0.1, z + 0.22), rot=(s * -0.15, 0, 0), bevel=0.02)
            b.box("K_Rose", (0.052, 0.05, 0.3), (-0.018, s * 0.1, z + 0.22), rot=(s * -0.15, 0, 0))
    return b


ASSETS_LOUFOQUES = [
    chien, chat, pigeon, poule, singe, elephant,
    lambda: pixels("Tag_Coin", mot("COIN/COIN"), px=0.1),
    lambda: pixels("Tag_Zap", mot("ZAP!")),
    lambda: pixels("Tag_Lol", mot("LOL")),
    *[(lambda n=n: pixels("Tag_" + n, DESSINS[n])) for n in DESSINS],
    lambda: pixels("Fissure", ["#...", "##..", ".#..", ".##.", "..#.", "..##", "...#", "..##", ".##.", ".#.."],
                   px=0.09, mat="K_Interieur"),
    lierre, planches, echelle, flaque, cartons, canape, piano, fumee, geyser, fruits_sol, tambour, barriere,
    trou, tas_sable, brouette, confettis, sacs_poubelle, poubelle_renversee, transat, chevalet, ballons, velo,
    lampadaire_tordu,
    lambda: pot("Pot_Plante", False), lambda: pot("Pot_Fleurs", True), buisson, massif, palmier, arbre_branchu,
    *[(lambda n=n: coiffe_folle(n)) for n in ("Toque", "Couronne", "HautDeForme", "Cone", "Sombrero", "Heaume",
                                             "Helice", "Lapin")],
]
