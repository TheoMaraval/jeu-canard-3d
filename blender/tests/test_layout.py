import json
import os
import unittest

from citygen.layout import charger_theme, make_layout
from citygen.placement import cellule

THEME = charger_theme("paris")


def hex_rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


class TestLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = make_layout(THEME)

    def test_deterministe(self):
        autre = make_layout(charger_theme("paris"))
        self.assertEqual(json.dumps(self.plan, sort_keys=True), json.dumps(autre, sort_keys=True))

    def test_graine_change_le_plan(self):
        t = dict(THEME, graine=THEME["graine"] + 1)
        self.assertNotEqual(json.dumps(make_layout(t)["slots"]), json.dumps(self.plan["slots"]))

    def test_primitives_dans_la_carte(self):
        demi = THEME["taille"] / 2 + 0.01
        for p in self.plan["prims"]:
            self.assertLessEqual(abs(p["pos"][0]), demi, p)
            self.assertLessEqual(abs(p["pos"][1]), demi, p)

    def test_materiaux_connus(self):
        for p in self.plan["prims"]:
            self.assertIn(p["mat"], THEME["palette"])

    def test_decor_jamais_jaune(self):
        # Le jaune est réservé aux canards et aux leurres : c'est la règle de camouflage.
        for nom, h in THEME["palette"].items():
            r, g, b = hex_rgb(h)
            self.assertFalse(r > 0.8 and g > 0.7 and b < 0.45, f"{nom} {h} est trop jaune")

    def test_assez_de_slots(self):
        self.assertGreaterEqual(len(self.plan["slots"]), 1500)
        self.assertEqual({s["lieu"] for s in self.plan["slots"]}, {"sol", "balcon", "toit"})

    def test_chaque_case_a_des_slots(self):
        compte = {}
        for s in self.plan["slots"]:
            c = cellule(s["pos"], THEME)
            compte[c] = compte.get(c, 0) + 1
        cols, rangs = THEME["grille"]
        self.assertEqual(len(compte), cols * rangs)
        self.assertGreaterEqual(min(compte.values()), 20, compte)

    def test_slots_sol_hors_des_immeubles(self):
        for s in self.plan["slots"]:
            if s["lieu"] != "sol":
                continue
            x, y, _ = s["pos"]
            for x0, y0, x1, y1 in self.plan["lots"]:
                self.assertFalse(x0 < x < x1 and y0 < y < y1, s)

    def test_theme_sur_disque(self):
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(__file__), "..", "themes", "paris.json")))


if __name__ == "__main__":
    unittest.main()
