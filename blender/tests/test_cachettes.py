import unittest

from citygen.cachettes import cachettes_valables, dedoublonner, empreinte, en_gltf

THEME = {"visibilite_canard": [0.3, 0.8], "distance_min": 1.0}


def slot(x, vis=0.5, rot_canard=1.0, lieu="sol"):
    return {"lieu": lieu, "pos": [x, 0.0, 0.0], "rot": 0.0, "vis": vis, "rot_canard": rot_canard}


class TestCachettes(unittest.TestCase):
    def test_garde_les_cachettes_assez_visibles_dont_la_tete_se_voit(self):
        slots = [slot(0), slot(10, vis=0.29), slot(20, rot_canard=None), slot(30, vis=1.0), slot(40, rot_canard=0.0)]
        gardees = cachettes_valables(slots, [], THEME)
        # pas de borne haute ; une rotation nulle est une vraie rotation
        self.assertEqual([s["pos"][0] for s in gardees], [0, 30, 40])

    def test_ecarte_les_cachettes_collees_a_un_leurre(self):
        leurres = [{"pos": [0.5, 0.0, 0.0]}]
        gardees = cachettes_valables([slot(0), slot(5)], leurres, THEME)
        self.assertEqual([s["pos"][0] for s in gardees], [5])

    def test_garde_l_ordre_des_slots(self):
        slots = [slot(x) for x in (9, 3, 7, 1)]
        self.assertEqual([s["pos"][0] for s in cachettes_valables(slots, [], THEME)], [9, 3, 7, 1])

    def test_convertit_en_repere_gltf(self):
        s = {"lieu": "toit", "pos": [1.0, 2.0, 3.0], "rot": 0.0, "vis": 0.4567, "rot_canard": 5.5}
        self.assertEqual(en_gltf(s), [1.0, 3.0, -2.0, 5.5, 0.457, "toit"])

    def test_empreinte_stable_et_sensible(self):
        a = [[1.0, 0.0, -2.0, 0.5, 0.4, "sol"], [3.0, 0.0, 1.0, 1.5, 0.9, "toit"]]
        self.assertRegex(empreinte(a), r"^[0-9a-z]{4}$")
        self.assertEqual(empreinte(a), empreinte([list(c) for c in a]))
        b = [list(c) for c in a]
        b[1][0] = 3.001
        self.assertNotEqual(empreinte(a), empreinte(b))
        self.assertNotEqual(empreinte(a), empreinte(a[::-1]))

    def test_dedoublonner_garde_la_premiere_de_chaque_groupe_proche(self):
        pts = [slot(0), slot(0.2), slot(0.5), slot(0.34), slot(5), slot(5.0)]
        pts[4]["pos"] = [5.0, 0.0, 0.3]  # 0,3 m plus haut : trop près aussi
        pts[5]["pos"] = [5.0, 0.0, 1.0]
        gardees = dedoublonner(pts, 0.35)
        self.assertEqual([s["pos"] for s in gardees], [[0, 0.0, 0.0], [0.5, 0.0, 0.0], [5.0, 0.0, 0.3], [5.0, 0.0, 1.0]])

    def test_dedoublonner_traverse_les_cases_de_la_grille(self):
        # 0,30 et 0,36 sont dans deux cases différentes de 0,35 m : le doublon doit être vu quand même
        gardees = dedoublonner([slot(0.36), slot(0.30)], 0.35)
        self.assertEqual(len(gardees), 1)
