import json
import unittest

from citygen.layout import charger_theme, make_layout, villes
from citygen.placement import cellule

VILLES = villes()
PLANS = {v: make_layout(charger_theme(v)) for v in VILLES}


def hex_rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


class TestLayout(unittest.TestCase):
    def pour_chaque_ville(self):
        return [(v, charger_theme(v), PLANS[v]) for v in VILLES]

    def test_les_quatre_villes(self):
        self.assertEqual(VILLES, ["delhi", "lille", "new_york", "paris"])

    def test_deterministe(self):
        for v, theme, plan in self.pour_chaque_ville():
            self.assertEqual(json.dumps(plan, sort_keys=True), json.dumps(make_layout(theme), sort_keys=True))

    def test_graine_change_le_plan(self):
        theme = charger_theme("paris")
        autre = make_layout(dict(theme, graine=theme["graine"] + 1))
        self.assertNotEqual(json.dumps(autre["slots"]), json.dumps(PLANS["paris"]["slots"]))

    def test_primitives_dans_la_carte(self):
        for v, theme, plan in self.pour_chaque_ville():
            demi = theme["taille"] / 2 + 0.01
            for p in plan["prims"]:
                self.assertLessEqual(abs(p["pos"][0]), demi, p)
                self.assertLessEqual(abs(p["pos"][1]), demi, p)

    def test_primitives_de_taille_positive(self):
        for v, theme, plan in self.pour_chaque_ville():
            for p in plan["prims"]:
                if p["t"] == "box":
                    self.assertGreater(min(p["size"]), 0, p)

    def test_materiaux_connus(self):
        for v, theme, plan in self.pour_chaque_ville():
            for p in plan["prims"]:
                self.assertIn(p["mat"], theme["palette"])

    def test_seul_le_materiau_jaune_est_jaune(self):
        # Camouflage : dans le décor, le jaune n'existe que sous le nom « jaune » (gros
        # leurres : taxis, camionnettes, stores), à la teinte exacte des canards.
        for v, theme, plan in self.pour_chaque_ville():
            self.assertEqual(theme["palette"]["jaune"].upper(), "#FFD21E")
            for nom, h in theme["palette"].items():
                r, g, b = hex_rgb(h)
                if nom != "jaune":
                    self.assertFalse(r > 0.8 and g > 0.7 and b < 0.45, f"{v} : {nom} {h} est trop jaune")

    def test_vitres(self):
        for v, theme, plan in self.pour_chaque_ville():
            self.assertTrue(any(p["mat"] == "verre" for p in plan["prims"]))
            self.assertGreaterEqual(sum(1 for s in plan["slots"] if s["lieu"] == "vitre"), 200)

    def test_des_passants(self):
        for v, theme, plan in self.pour_chaque_ville():
            peaux = set(theme["style"]["peaux"])
            self.assertGreaterEqual(sum(1 for p in plan["prims"] if p["t"] == "sph" and p["mat"] in peaux), 250)

    def test_assez_de_slots_partout(self):
        for v, theme, plan in self.pour_chaque_ville():
            self.assertGreaterEqual(len(plan["slots"]), 2000, v)
            self.assertLessEqual({"sol", "vitre"}, {s["lieu"] for s in plan["slots"]})
            compte = {}
            for s in plan["slots"]:
                c = cellule(s["pos"], theme)
                compte[c] = compte.get(c, 0) + 1
            cols, rangs = theme["grille"]
            self.assertEqual(len(compte), cols * rangs)
            self.assertGreaterEqual(min(compte.values()), 20, compte)

    def test_slots_sol_hors_des_immeubles(self):
        for v, theme, plan in self.pour_chaque_ville():
            for s in plan["slots"]:
                if s["lieu"] != "sol":
                    continue
                x, y, _ = s["pos"]
                for x0, y0, x1, y1 in plan["lots"]:
                    self.assertFalse(x0 < x < x1 and y0 < y < y1, s)

    def test_chaque_ville_a_son_architecture(self):
        mats = {v: {p["mat"] for p in PLANS[v]["prims"]} for v in VILLES}
        self.assertIn("zinc", mats["paris"])            # toits mansardés
        self.assertIn("bois", mats["new_york"])         # châteaux d'eau
        self.assertIn("tuile", mats["lille"])           # toits à pignon
        self.assertIn("citerne", mats["delhi"])         # citernes sur les toits-terrasses


if __name__ == "__main__":
    unittest.main()
