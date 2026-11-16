"""Plan d'un quartier, en Python pur (pas de bpy) : testable hors de Blender.

make_layout(theme) renvoie :
  prims : primitives à mailler (contrat dans le plan du pipeline)
  slots : cachettes candidates {lieu, pos, rot}
  lots  : emprises des immeubles [x0, y0, x1, y1]
  blocs : emprises des îlots, trottoir compris

Repère Blender : Z vers le haut, carte centrée sur l'origine, mètres.
La caméra de jeu est côté (+x, -y) : les façades visibles regardent le sud et l'est.
"""
import json
import math
import os
import random

AZIMUT = 45.0
ELEVATION = 35.264
LOIN = (-math.sqrt(0.5), math.sqrt(0.5))  # direction horizontale qui s'éloigne de la caméra
H_TROTTOIR = 0.15
LATERAL = (math.sqrt(0.5), math.sqrt(0.5))  # perpendiculaire à LOIN, à l'horizontale
MARGE_SLOT = 0.3
PENTE = math.tan(math.radians(ELEVATION))  # un rayon vers la caméra monte de PENTE m par mètre

FACADES = {  # côté -> (coin d'origine, direction le long du mur, normale sortante)
    "S": (("x0", "y0"), (1, 0), (0, -1)),
    "N": (("x0", "y1"), (1, 0), (0, 1)),
    "W": (("x0", "y0"), (0, 1), (-1, 0)),
    "E": (("x1", "y0"), (0, 1), (1, 0)),
}


def charger_theme(ville):
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "themes", ville + ".json")
    with open(chemin, encoding="utf8") as f:
        return json.load(f)


class Plan:
    def __init__(self, theme):
        self.t = theme
        self.rng = random.Random(theme["graine"])
        self.demi = theme["taille"] / 2
        self.prims, self.slots = [], []
        self.lots, self.blocs, self.herbes, self.emprises = [], [], [], []

    # ---- primitives -------------------------------------------------------
    def box(self, mat, size, pos, rot=0.0, haut=None, emprise=False):
        p = {"t": "box", "mat": mat, "size": list(size), "pos": list(pos), "rot": rot}
        if haut:
            p["haut"] = list(haut)
        self.prims.append(p)
        if emprise:
            r = max(size[0], size[1]) / 2 if rot else None
            hx, hy = (r, r) if rot else (size[0] / 2, size[1] / 2)
            self.emprises.append((pos[0] - hx, pos[1] - hy, pos[0] + hx, pos[1] + hy))

    def cyl(self, mat, r, h, base, r2=None, seg=10, emprise=False):
        """base = centre de la face du bas."""
        self.prims.append({"t": "cyl", "mat": mat, "r1": r, "r2": r if r2 is None else r2,
                           "h": h, "seg": seg, "pos": [base[0], base[1], base[2] + h / 2]})
        if emprise:
            self.emprises.append((base[0] - r, base[1] - r, base[0] + r, base[1] + r))

    def sph(self, mat, r, pos, scale=(1, 1, 1)):
        self.prims.append({"t": "sph", "mat": mat, "r": r, "pos": list(pos), "scale": list(scale)})

    # ---- sol et slots -----------------------------------------------------
    @staticmethod
    def _dans(x, y, rects, marge=0.0):
        return any(x0 - marge < x < x1 + marge and y0 - marge < y < y1 + marge
                   for x0, y0, x1, y1 in rects)

    def sol_z(self, x, y):
        if self._dans(x, y, self.herbes):
            return H_TROTTOIR + 0.06
        return H_TROTTOIR if self._dans(x, y, self.blocs) else 0.0

    def libre(self, x, y):
        return (abs(x) < self.demi - 0.5 and abs(y) < self.demi - 0.5
                and not self._dans(x, y, self.emprises, MARGE_SLOT)
                and not self._dans(x, y, self.lots, 0.25))

    def slot(self, lieu, x, y, z):
        self.slots.append({"lieu": lieu, "pos": [round(x, 3), round(y, 3), round(z, 3)],
                           "rot": round(self.rng.uniform(0, 2 * math.pi), 3)})

    def slot_sol(self, x, y):
        if self.libre(x, y):
            self.slot("sol", x, y, self.sol_z(x, y))

    def slot_derriere(self, x, y, r, h, n=3):
        """n cachettes derrière un obstacle (demi-largeur r, hauteur h), vu de la caméra.

        La distance va jusqu'à l'endroit où le rayon passe par-dessus l'obstacle et le
        décalage latéral dépasse ses bords : on obtient des objets à moitié cachés,
        pas seulement tout visibles ou tout invisibles.
        """
        for _ in range(n):
            d = self.rng.uniform(r + 0.5, max(r + 0.7, h / PENTE + 0.2))
            lat = self.rng.uniform(-(r + 0.3), r + 0.3)
            self.slot_sol(x + LOIN[0] * d + LATERAL[0] * lat, y + LOIN[1] * d + LATERAL[1] * lat)

    # ---- mobilier ---------------------------------------------------------
    def arbre(self, x, y, z):
        self.cyl("tronc", 0.13, 2.4, (x, y, z), seg=6, emprise=True)
        f = self.rng.choice(["feuillage", "feuillage2"])
        r = self.rng.uniform(1.0, 1.35)
        self.sph(f, r, (x, y, z + 3.2), (1, 1, 0.9))
        self.sph(f, r * 0.65, (x + self.rng.uniform(-0.5, 0.5), y + self.rng.uniform(-0.5, 0.5), z + 4.1))
        self.slot_derriere(x, y, 0.13, 2.4, n=2)
        for _ in range(2):  # sous le feuillage, vu de la caméra
            d, lat = self.rng.uniform(3.3, 5.6), self.rng.uniform(-1.3, 1.3)
            self.slot_sol(x + LOIN[0] * d + LATERAL[0] * lat, y + LOIN[1] * d + LATERAL[1] * lat)

    def haie(self, x, y, longueur, le_long_de_x, mat="feuillage2", ep=0.5, h=0.6):
        """Écran bas (haie, claustra de terrasse), cachettes du côté opposé à la caméra."""
        z = self.sol_z(x, y)
        self.box(mat, (longueur, ep, h) if le_long_de_x else (ep, longueur, h), (x, y, z + h / 2), emprise=True)
        s = -longueur / 2 + 0.4
        while s < longueur / 2 - 0.3:
            o = ep / 2 + MARGE_SLOT + self.rng.uniform(0.05, 0.4)
            if le_long_de_x:
                self.slot_sol(x + s, y + o)
            else:
                self.slot_sol(x - o, y + s)
            s += self.rng.uniform(0.9, 1.5)

    def lampadaire(self, x, y, z):
        self.cyl("fer", 0.06, 4.6, (x, y, z), seg=6, emprise=True)
        self.sph("lampe", 0.22, (x, y, z + 4.7))

    def banc(self, x, y, z, rot=0.0):
        self.box("bois", (1.5, 0.45, 0.45), (x, y, z + 0.225), rot, emprise=True)
        self.box("bois", (1.5, 0.08, 0.45), (x - math.sin(rot) * 0.2, y + math.cos(rot) * 0.2, z + 0.65), rot)
        self.slot_derriere(x, y, 0.75, 0.9)

    def poubelle(self, x, y, z):
        self.cyl("vertfonce", 0.25, 0.85, (x, y, z), seg=8, emprise=True)
        self.slot_derriere(x, y, 0.25, 0.85)

    def voiture(self, x, y, le_long_de_x):
        mat = self.rng.choice(self.t["immeuble"]["voitures"])
        long, larg = 4.2, 1.8
        sx, sy = (long, larg) if le_long_de_x else (larg, long)
        kx, ky = (0.55, 0.88) if le_long_de_x else (0.88, 0.55)
        self.box("fer", (sx * 0.85, sy * 1.04, 0.4), (x, y, 0.25))            # roues
        self.box(mat, (sx, sy, 0.65), (x, y, 0.60), emprise=True)             # caisse
        self.box(mat, (sx * kx, sy * ky, 0.5), (x, y, 1.17), haut=(0.8, 0.8))  # habitacle
        self.slot_derriere(x, y, 1.0, 1.4)

    # ---- immeubles --------------------------------------------------------
    def _facade(self, rect, cote):
        coins = dict(zip(("x0", "y0", "x1", "y1"), rect))
        (cx, cy), u, n = FACADES[cote]
        longueur = (rect[2] - rect[0]) if u[0] else (rect[3] - rect[1])
        return (coins[cx], coins[cy]), u, n, longueur

    def _element(self, facade, mat, s, la, o, th, zc, hz):
        """Boîte posée sur une façade : s le long du mur, o vers l'extérieur."""
        a, u, n, _ = facade
        pos = (a[0] + u[0] * s + n[0] * o, a[1] + u[1] * s + n[1] * o, zc)
        self.box(mat, (la, th, hz) if u[0] else (th, la, hz), pos)
        return pos

    def immeuble(self, rect, cotes):
        rng, im = self.rng, self.t["immeuble"]
        x0, y0, x1, y1 = rect
        lx, ly, cx, cy = x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2
        n, he, rdc, z0 = rng.randint(*im["etages"]), im["hauteur_etage"], im["rdc"], H_TROTTOIR
        haut = rdc + n * he
        self.lots.append(list(rect))
        self.box(rng.choice(im["murs"]), (lx, ly, haut), (cx, cy, z0 + haut / 2))
        self.box("pierre", (lx + 0.4, ly + 0.4, 0.25), (cx, cy, z0 + haut - 0.125))  # corniche

        # toit mansardé : dessus rétréci de 0,9 m par côté
        self.box("zinc", (lx + 0.3, ly + 0.3, 2.4), (cx, cy, z0 + haut + 1.2),
                 haut=((lx - 1.8) / (lx + 0.3), (ly - 1.8) / (ly + 0.3)))
        ztoit, m = z0 + haut + 2.4, 1.5
        for _ in range(rng.randint(1, 3)):
            px, py = rng.uniform(x0 + m + 0.3, x1 - m - 0.3), rng.uniform(y0 + m + 0.3, y1 - m - 0.3)
            self.box("cheminee", (0.7, 0.7, 1.3), (px, py, ztoit + 0.65))
            for _ in range(3):  # cachettes derrière la cheminée, plus ou moins masquées
                d, lat = rng.uniform(0.9, 1.9), rng.uniform(-0.55, 0.55)
                sx = px + LOIN[0] * d + LATERAL[0] * lat
                sy = py + LOIN[1] * d + LATERAL[1] * lat
                if x0 + m < sx < x1 - m and y0 + m < sy < y1 - m:
                    self.slot("toit", sx, sy, ztoit)
        # acrotère : muret bas au bord du toit plat, cachettes derrière les côtés sud et est
        a0, b0, a1, b1 = x0 + 0.96, y0 + 0.96, x1 - 0.96, y1 - 0.96
        for size, pos in (((a1 - a0, 0.12, 0.4), (cx, b0, ztoit + 0.2)),
                          ((a1 - a0, 0.12, 0.4), (cx, b1, ztoit + 0.2)),
                          ((0.12, b1 - b0, 0.4), (a0, cy, ztoit + 0.2)),
                          ((0.12, b1 - b0, 0.4), (a1, cy, ztoit + 0.2))):
            self.box("zinc", size, pos)
        s = a0 + 0.6
        while s < a1 - 0.9:
            self.slot("toit", s, b0 + 0.06 + rng.uniform(0.28, 0.6), ztoit)
            s += rng.uniform(1.2, 2.0)
        s = b0 + 0.9
        while s < b1 - 0.6:
            self.slot("toit", a1 - 0.06 - rng.uniform(0.28, 0.6), s, ztoit)
            s += rng.uniform(1.2, 2.0)
        for _ in range(4):
            self.slot("toit", rng.uniform(x0 + m, x1 - m), rng.uniform(y0 + m, y1 - m), ztoit)

        for cote in cotes:
            f = self._facade(rect, cote)
            long = f[3]
            self._element(f, "vitrine", long / 2, long - 1.0, 0.05, 0.1, z0 + 1.6, 2.6)
            if rng.random() < 0.6:
                self._element(f, rng.choice(im["auvents"]), long / 2, long - 1.2, 0.6, 1.2, z0 + 3.2, 0.12)
            k = max(1, int((long - 1) / 2.2))
            for etage in range(n):
                zf = z0 + rdc + etage * he
                for i in range(k):
                    self._element(f, "fenetre", (i + 0.5) * long / k, 1.0, 0.03, 0.06, zf + 1.5, 1.7)
                if etage in (1, n - 2):  # balcons filants, 2e et avant-dernier étage
                    self._element(f, "pierre", long / 2, long - 0.6, 0.4, 0.8, zf - 0.06, 0.12)
                    self._element(f, "fer", long / 2, long - 0.6, 0.78, 0.05, zf + 0.225, 0.45)
                    s = 0.8
                    while s < long - 0.8:
                        o = rng.uniform(0.25, 0.55)
                        a, u, nrm, _ = f
                        self.slot("balcon", a[0] + u[0] * s + nrm[0] * o, a[1] + u[1] * s + nrm[1] * o, zf)
                        s += 1.3

    def _decoupe(self, a, b):
        """Coupe [a, b] en 2 ou 3 lots de largeurs inégales."""
        k = self.rng.choice([2, 3])
        pas = (b - a) / k
        coupes = [a] + [a + pas * i + self.rng.uniform(-1.5, 1.5) for i in range(1, k)] + [b]
        return list(zip(coupes[:-1], coupes[1:]))

    def ilot_bati(self, bx, by, bloc):
        t, d = self.t["trottoir"], self.t["immeuble"]["profondeur"]
        x0, y0, x1, y1 = bx + t, by + t, bx + bloc - t, by + bloc - t
        sud, nord = self._decoupe(x0, x1), self._decoupe(x0, x1)
        for i, (a, b) in enumerate(sud):
            self.immeuble((a, y0, b, y0 + d), "S" + ("W" if i == 0 else "") + ("E" if i == len(sud) - 1 else ""))
        for i, (a, b) in enumerate(nord):
            self.immeuble((a, y1 - d, b, y1), "N" + ("W" if i == 0 else "") + ("E" if i == len(nord) - 1 else ""))
        self.immeuble((x0, y0 + d, x0 + d, y1 - d), "W")
        self.immeuble((x1 - d, y0 + d, x1, y1 - d), "E")
        self._trottoirs(bx, by, bloc)

    def _trottoirs(self, bx, by, bloc):
        rng, t, z = self.rng, self.t["trottoir"], H_TROTTOIR
        bandes = {  # côté -> fonction (s le long, o depuis la bordure) -> (x, y)
            "S": lambda s, o: (bx + s, by + o),
            "N": lambda s, o: (bx + s, by + bloc - o),
            "W": lambda s, o: (bx + o, by + s),
            "E": lambda s, o: (bx + bloc - o, by + s),
        }
        for cote, pt in bandes.items():
            s = 2.0
            while s < bloc - 2.0:
                x, y = pt(s + rng.uniform(-0.6, 0.6), 0.8)
                tirage = rng.random()
                if tirage < 0.30:
                    self.arbre(x, y, z)
                elif tirage < 0.40:
                    self.lampadaire(x, y, z)
                elif tirage < 0.48:
                    self.banc(x, y, z, 0.0 if cote in "SN" else math.pi / 2)
                elif tirage < 0.54:
                    self.poubelle(x, y, z)
                s += 3.5
            if cote in "SE":  # claustras de terrasse devant les façades visibles
                s = 4.0
                while s < bloc - 4.0:
                    if rng.random() < 0.45:
                        self.haie(*pt(s, 1.35), 2.6, cote == "S",
                                  mat=rng.choice(["bois", "vertfonce"]), ep=0.1, h=0.55)
                    s += 5.0
            for _ in range(28):  # cachettes libres sur le trottoir
                self.slot_sol(*pt(rng.uniform(0.5, bloc - 0.5), rng.uniform(0.3, t - 0.3)))
            s = 3.5
            while s < bloc - 3.0:  # stationnement le long de la bordure, côté chaussée
                if rng.random() < 0.5:
                    self.voiture(*pt(s, -1.2), le_long_de_x=cote in "SN")
                s += 5.5

    # ---- square -----------------------------------------------------------
    def ilot_square(self, bx, by, bloc):
        rng, z = self.rng, H_TROTTOIR
        cx, cy = bx + bloc / 2, by + bloc / 2
        m = 1.5
        self.box("herbe", (bloc - 2 * m, bloc - 2 * m, 0.06), (cx, cy, z + 0.03))
        self.herbes.append((bx + m, by + m, bx + bloc - m, by + bloc - m))
        zh = z + 0.06

        self.cyl("pierre", 3.0, 0.5, (cx, cy, zh), seg=20, emprise=True)   # fontaine
        self.cyl("eau", 2.6, 0.52, (cx, cy, zh), seg=20)
        self.cyl("pierre", 0.4, 1.7, (cx, cy, zh), seg=8)
        self.cyl("pierre", 1.0, 0.25, (cx, cy, zh + 1.7), r2=1.3, seg=12)
        for _ in range(12):  # sur la margelle
            a = rng.uniform(0, 2 * math.pi)
            self.slot("sol", cx + 2.8 * math.cos(a), cy + 2.8 * math.sin(a), zh + 0.5)

        for i in range(6):  # bancs en cercle
            a = i * math.pi / 3 + 0.3
            self.banc(cx + 5.5 * math.cos(a), cy + 5.5 * math.sin(a), zh, a + math.pi / 2)

        kx, ky = bx + 5.0, by + bloc - 5.0  # kiosque
        self.cyl("vertfonce", 1.2, 3.0, (kx, ky, zh), seg=8, emprise=True)
        self.cyl("vertfonce", 1.6, 0.9, (kx, ky, zh + 3.0), r2=0.1, seg=8)
        self.slot_derriere(kx, ky, 1.2, 3.5, n=5)

        for i in range(6):  # terrasse de café
            tx, ty = bx + bloc - 9.0 + (i % 3) * 3.0, by + 4.0 + (i // 3) * 3.2
            self.cyl("fer", 0.05, 0.72, (tx, ty, zh), seg=6, emprise=True)
            self.cyl("parasol2", 0.45, 0.04, (tx, ty, zh + 0.72), seg=10)
            for dx in (-0.7, 0.7):
                self.box("bois", (0.4, 0.4, 0.45), (tx + dx, ty, zh + 0.225), emprise=True)
            if i % 2 == 0:
                self.cyl("fer", 0.03, 2.3, (tx + 0.1, ty + 0.9, zh), seg=6, emprise=True)
                self.cyl(rng.choice(["parasol1", "parasol2"]), 1.2, 0.4, (tx + 0.1, ty + 0.9, zh + 2.2), r2=0.0, seg=8)
            self.slot_derriere(tx, ty, 0.5, 0.75, n=2)

        for dx, dy, le_long_de_x in ((0, -9.5, True), (9.5, 0, False), (-6, -11.5, True), (11.5, 6, False)):
            self.haie(cx + dx, cy + dy, 5.0, le_long_de_x)

        arbres = 0
        while arbres < 10:
            x, y = rng.uniform(bx + 2.5, bx + bloc - 2.5), rng.uniform(by + 2.5, by + bloc - 2.5)
            if math.hypot(x - cx, y - cy) > 7.5 and self.libre(x, y):
                self.arbre(x, y, zh)
                arbres += 1
        for _ in range(140):
            self.slot_sol(rng.uniform(bx + 0.5, bx + bloc - 0.5), rng.uniform(by + 0.5, by + bloc - 0.5))

    # ---- ensemble ---------------------------------------------------------
    def construire(self):
        t = self.t
        taille, n, rue = t["taille"], t["ilots"], t["rue"]
        bloc = (taille - n * rue) / n  # demi-rue en bordure de carte
        self.box("asphalte", (taille, taille, 0.2), (0, 0, -0.1))
        origines = [-self.demi + rue / 2 + i * (bloc + rue) for i in range(n)]
        for bx in origines:
            for by in origines:
                self.box("trottoir", (bloc, bloc, H_TROTTOIR), (bx + bloc / 2, by + bloc / 2, H_TROTTOIR / 2))
                self.blocs.append((bx, by, bx + bloc, by + bloc))
        for c in origines[1:]:  # pointillés au milieu des rues intérieures
            s = -self.demi + 2
            while s < self.demi - 2:
                self.box("marquage", (0.15, 1.6, 0.02), (c - rue / 2, s, 0.01))
                self.box("marquage", (1.6, 0.15, 0.02), (s, c - rue / 2, 0.01))
                s += 4.0
        for i, bx in enumerate(origines):
            for j, by in enumerate(origines):
                if [i, j] == t["square"]:
                    self.ilot_square(bx, by, bloc)
                else:
                    self.ilot_bati(bx, by, bloc)
        return {"prims": self.prims, "slots": self.slots, "lots": self.lots,
                "blocs": [list(b) for b in self.blocs]}


def make_layout(theme):
    return Plan(theme).construire()
