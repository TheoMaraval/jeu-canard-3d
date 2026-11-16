import math
import unittest

from citygen.layout import charger_theme, make_layout
from citygen.maillage import assembler, primitive, volume


class TestMaillage(unittest.TestCase):
    def vol(self, p):
        verts, faces, _ = primitive(dict({"mat": "m", "pos": [3, -2, 5]}, **p))
        return volume(verts, faces)

    def test_boite(self):
        self.assertAlmostEqual(self.vol({"t": "box", "size": [2, 3, 4]}), 24)
        self.assertAlmostEqual(self.vol({"t": "box", "size": [2, 3, 4], "rot": 0.7}), 24)

    def test_boite_retrecie_en_haut(self):
        # tronc de pyramide : h/3 * (A1 + A2 + sqrt(A1*A2)), dessus réduit de moitié
        self.assertAlmostEqual(self.vol({"t": "box", "size": [2, 2, 3], "haut": [0.5, 0.5]}), 3 / 3 * (4 + 1 + 2))

    def test_cylindre_et_cone(self):
        aire = 8 * 0.5 * math.sin(2 * math.pi / 8)  # octogone de rayon 1
        self.assertAlmostEqual(self.vol({"t": "cyl", "r1": 1, "r2": 1, "h": 2, "seg": 8}), 2 * aire)
        self.assertAlmostEqual(self.vol({"t": "cyl", "r1": 1, "r2": 0, "h": 3, "seg": 8}), aire)

    def test_sphere_tournee_vers_l_exterieur(self):
        v = self.vol({"t": "sph", "r": 1})
        self.assertGreater(v, 2.0)  # grossière (8 x 5), mais positive et proche de 4,19
        self.assertLess(v, 4.19)
        self.assertAlmostEqual(self.vol({"t": "sph", "r": 1, "scale": [1, 1, 0.5]}), v / 2)

    def test_position(self):
        verts, _, _ = primitive({"t": "box", "mat": "m", "size": [2, 2, 2], "pos": [10, 20, 30]})
        self.assertEqual(min(verts), (9, 19, 29))
        self.assertEqual(max(verts), (11, 21, 31))

    def test_assembler(self):
        m = assembler([
            {"t": "box", "mat": "a", "size": [1, 1, 1], "pos": [0, 0, 0]},
            {"t": "sph", "mat": "b", "r": 1, "pos": [5, 0, 0]},
            {"t": "box", "mat": "a", "size": [1, 1, 1], "pos": [9, 0, 0]},
        ])
        self.assertEqual(m["noms"], ["a", "b"])
        self.assertEqual(len(m["faces"]), len(m["mats"]))
        self.assertEqual(len(m["faces"]), len(m["lisses"]))
        self.assertEqual(m["mats"][:6], [0] * 6)
        self.assertEqual(m["mats"][-6:], [0] * 6)
        self.assertTrue(all(m["lisses"][6:-6]) and not any(m["lisses"][:6]))
        self.assertEqual(max(i for f in m["faces"] for i in f), len(m["sommets"]) - 1)

    def test_tout_paris_est_tourne_vers_l_exterieur(self):
        for p in make_layout(charger_theme("paris"))["prims"]:
            verts, faces, _ = primitive(p)
            self.assertGreater(volume(verts, faces), 0, p)


if __name__ == "__main__":
    unittest.main()
