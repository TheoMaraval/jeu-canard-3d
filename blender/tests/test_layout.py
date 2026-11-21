import json
import unittest

from citygen.layout import KIT, ThemeInvalide, charger_theme, fusionner, make_layout, valider_theme, villes
from citygen.placement import cellule

VILLES = villes()
PLANS = {v: make_layout(charger_theme(v)) for v in VILLES}


def hex_rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


class TestLayout(unittest.TestCase):
    def pour_chaque_ville(self):
        return [(v, charger_theme(v), PLANS[v]) for v in VILLES]

    def test_une_ville_minimale_se_genere(self):
        # Promesse de docs/02-ajouter-une-ville.md : id, nom et graine suffisent, tout le
        # reste a une valeur par défaut dans _commun.json.
        theme = fusionner({"id": "mini", "nom": "Mini", "graine": 7})
        plan = make_layout(theme)
        self.assertGreaterEqual(len(plan["slots"]), 2000)
        cols, rangs = theme["grille"]
        self.assertEqual(len({cellule(s["pos"], theme) for s in plan["slots"]}), cols * rangs)
        for p in plan["prims"]:
            self.assertIn(p["mat"], theme["palette"])
        for i in plan["insts"]:
            for couleur in i["c"].values():
                self.assertIn(couleur, theme["palette"])

    def test_les_themes_existants_sont_valides(self):
        for v in VILLES:
            valider_theme(charger_theme(v))

    def test_un_theme_faux_donne_un_message_clair(self):
        theme = fusionner({"id": "faux", "nom": "Faux", "graine": 1, "canards": 25, "palette": {"mur_x": "bleu"},
                           "style": {"toit": "coupole", "saynetes_place": ["chantier"], "murs": ["mur_inconnu"]}})
        with self.assertRaises(ThemeInvalide) as ctx:
            make_layout(theme)
        message = str(ctx.exception)
        for attendu in ("coupole", "chantier", "mur_inconnu", "palette.mur_x", "un canard par case"):
            self.assertIn(attendu, message)

    def test_les_villes_de_base_sont_la(self):
        # d'autres villes peuvent s'ajouter : ce test ne doit pas obliger à le modifier
        self.assertLessEqual({"delhi", "lille", "new_york", "paris"}, set(VILLES))

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
            persos = [i for i in plan["insts"] if i["type"].startswith("Perso_")]
            self.assertGreaterEqual(len(persos), 250, v)
            self.assertGreaterEqual(len({i["type"] for i in persos}), 6, v)  # poses variées
            self.assertTrue(any(i["type"] == "Perso_Buste" for i in persos))  # des gens aux fenêtres

    def test_instances_du_kit(self):
        for v, theme, plan in self.pour_chaque_ville():
            demi = theme["taille"] / 2
            for i in plan["insts"]:
                self.assertIn(i["type"], KIT)
                self.assertLess(abs(i["pos"][0]), demi, i)
                self.assertLess(abs(i["pos"][1]), demi, i)
                for role, couleur in i["c"].items():
                    self.assertIn(couleur, theme["palette"], f"{v} : {i['type']}.{role}")

    def test_du_piment(self):
        # tags, bêtes, végétation variée, accessoires de saynètes : la ville n'est pas lisse
        for v, theme, plan in self.pour_chaque_ville():
            types = [i["type"] for i in plan["insts"]]
            self.assertGreaterEqual(sum(t.startswith("Tag_") for t in types), 10, v)
            self.assertGreaterEqual(sum(t in ("Chien", "Chat", "Pigeon", "Poule", "Singe", "Elephant") for t in types), 15, v)
            self.assertGreaterEqual(sum(t in ("Pot_Plante", "Pot_Fleurs", "Buisson", "Massif_Fleurs", "Lierre") for t in types), 15, v)
            accessoires = {"Cartons", "Sacs_Poubelle", "Velo", "Fumee", "Trou", "Confettis", "Fruits_Sol", "Tambour",
                           "Echelle", "Piano_Suspendu", "Borne_Geyser", "Chevalet", "Ballons", "Elephant", "Barriere"}
            self.assertGreaterEqual(len(accessoires & set(types)), 4, v)
            self.assertGreaterEqual(len(set(types)), 45, v)

    def test_une_signature_par_ville(self):
        types = {v: {i["type"] for i in PLANS[v]["insts"]} for v in VILLES}
        self.assertIn("Elephant", types["delhi"])
        self.assertIn("Palmier", types["delhi"])
        self.assertTrue(any(i["type"] == "Perso_Robe" and i["k"] > 3 for i in PLANS["lille"]["insts"]))  # le géant
        self.assertTrue(any(i["type"] == "Bus" and i["c"].get("caisse") == "jaune" for i in PLANS["new_york"]["insts"])
                        or "Borne_Geyser" in types["new_york"])

    def test_gros_leurres_jaunes(self):
        for v, theme, plan in self.pour_chaque_ville():
            jaunes = [i for i in plan["insts"] if "jaune" in i["c"].values()]
            self.assertGreaterEqual(len(jaunes), 8, v)

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
        types = {v: {i["type"] for i in PLANS[v]["insts"]} for v in VILLES}
        self.assertIn("zinc", mats["paris"])            # toits mansardés
        self.assertIn("bois", mats["new_york"])         # châteaux d'eau
        self.assertIn("Taxi", types["new_york"])
        self.assertIn("tuile", mats["lille"])           # toits à pignon
        self.assertIn("Etal", types["lille"])           # braderie
        self.assertIn("citerne", mats["delhi"])         # citernes sur les toits-terrasses
        self.assertLessEqual({"Rickshaw", "Vache"}, types["delhi"])


if __name__ == "__main__":
    unittest.main()
