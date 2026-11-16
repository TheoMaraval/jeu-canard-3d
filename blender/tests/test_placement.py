import random
import unittest

from citygen.layout import charger_theme
from citygen.placement import PlacementImpossible, cellule, choisir, valider

THEME = charger_theme("paris")


def slots_synthetiques(pas=2.0, graine=1):
    """Grille régulière de slots couvrant la carte, visibilités variées."""
    rng = random.Random(graine)
    demi = THEME["taille"] / 2
    out = []
    x = -demi + 1
    while x < demi:
        y = -demi + 1
        while y < demi:
            out.append({"lieu": rng.choice(["sol", "sol", "balcon", "toit"]),
                        "pos": [x, y, 0.0], "rot": 0.0, "vis": rng.uniform(0.0, 1.0)})
            y += pas
        x += pas
    return out


class TestPlacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objets = choisir(slots_synthetiques(), THEME)
        cls.canards = [o for o in cls.objets if o["type"] == "Canard"]
        cls.leurres = [o for o in cls.objets if o["type"] != "Canard"]

    def test_cellule(self):
        self.assertEqual(cellule([-59, -59, 0], THEME), "A1")
        self.assertEqual(cellule([59, 59, 0], THEME), "F5")

    def test_comptes(self):
        self.assertEqual(len(self.canards), 30)
        self.assertEqual(len(self.leurres), 170)
        self.assertEqual(len({o["id"] for o in self.objets}), 200)

    def test_un_canard_par_case(self):
        self.assertEqual(len({o["zone"] for o in self.canards}), 30)

    def test_canards_dans_des_lieux_varies(self):
        for lieu in THEME["leurres_par_lieu"]:
            self.assertGreaterEqual(sum(1 for o in self.canards if o["lieu"] == lieu), 8, lieu)

    def test_plages_de_visibilite(self):
        lo, hi = THEME["visibilite_canard"]
        for o in self.canards:
            self.assertTrue(lo <= o["visibilite"] <= hi, o)
        lo, hi = THEME["visibilite_leurre"]
        for o in self.leurres:
            self.assertTrue(lo <= o["visibilite"] <= hi, o)

    def test_distances(self):
        def d(a, b):
            return sum((a["pos"][i] - b["pos"][i]) ** 2 for i in range(3)) ** 0.5
        for i, a in enumerate(self.objets):
            for b in self.objets[i + 1:]:
                self.assertGreaterEqual(d(a, b), THEME["distance_min"] - 1e-9)
        for i, a in enumerate(self.canards):
            for b in self.canards[i + 1:]:
                self.assertGreaterEqual(d(a, b), THEME["distance_min_canards"] - 1e-9)

    def test_type_compatible_avec_le_lieu(self):
        for o in self.leurres:
            self.assertIn(o["type"], THEME["leurres_par_lieu"][o["lieu"]])

    def test_tous_les_types_de_leurres_servent(self):
        self.assertEqual({o["type"] for o in self.leurres},
                         {t for ts in THEME["leurres_par_lieu"].values() for t in ts})

    def test_deterministe(self):
        self.assertEqual(choisir(slots_synthetiques(), THEME), self.objets)

    def test_valider_accepte_le_resultat(self):
        valider(self.objets, THEME)

    def test_valider_refuse_un_canard_en_trop(self):
        with self.assertRaises(AssertionError):
            valider(self.objets + [dict(self.canards[0], id="canard-99")], THEME)

    def test_case_sans_candidat(self):
        slots = [s for s in slots_synthetiques() if cellule(s["pos"], THEME) != "C3"]
        with self.assertRaises(PlacementImpossible) as ctx:
            choisir(slots, THEME)
        self.assertIn("C3", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
