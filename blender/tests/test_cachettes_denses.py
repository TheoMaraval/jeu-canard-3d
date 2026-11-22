"""Cachettes denses du mode « Cacher » : nombreuses, et sans effet sur la partie normale.

Les 30 canards et les leurres du jeu sont tirés de make_layout()["slots"] par une suite de
tirages ; les records sont liés à la `version` de la ville. Les cachettes denses ne doivent
donc rien tirer au sort ni rien changer au reste du plan.
"""
import hashlib
import json
import unittest

from citygen import layout
from citygen.layout import charger_theme, make_layout
from tests.test_layout import PLANS

CLES_DU_JEU = ("prims", "insts", "slots", "lots", "blocs")
# Empreinte de make_layout (clés du jeu) relevée AVANT l'ajout des cachettes denses
# (commit fc21374, version 3 des quatre villes). Si un changement voulu du plan la modifie,
# les canards bougent : régénérer la ville, augmenter sa `version`, puis mettre à jour ici.
EMPREINTES_PLAN = {
    "delhi": "46aaf63b3a850fa6f02750fba6682587b4118f81fad21d15c8983111abf06725",
    "lille": "04edcf5476a693ef3e1c5cfbec138c3f3f315e9225d21fb5f06b542828e2c61a",
    "new_york": "14d486c5c56f46e2cc85a6994ff218b2314f318970e30633fe7dfc181fdc2150",
    "paris": "5e5ec627e5bf8ff2d1845c7d69e15429c67c79ee7cf7a2dff193f2386487ae83",
}


def empreinte_du_jeu(plan):
    jeu = {k: plan[k] for k in CLES_DU_JEU}
    return hashlib.sha256(json.dumps(jeu, sort_keys=True).encode()).hexdigest()


class TestCachettesDenses(unittest.TestCase):
    def test_le_plan_du_jeu_n_a_pas_change(self):
        for ville, attendue in EMPREINTES_PLAN.items():
            with self.subTest(ville=ville):
                self.assertEqual(empreinte_du_jeu(PLANS[ville]), attendue)

    def test_ne_consomme_aucun_tirage(self):
        # Même plan, cachettes denses coupées : le générateur finit dans le même état et
        # produit exactement le même jeu.
        theme = charger_theme("paris")
        avec = layout.Plan(theme)
        jeu_avec = avec.construire()
        sans = layout.Plan(theme)
        sans.dense = lambda *a: None
        jeu_sans = sans.construire()
        self.assertEqual(avec.rng.getstate(), sans.rng.getstate())
        self.assertEqual(jeu_sans["cachettes_denses"], [])
        self.assertEqual(empreinte_du_jeu(jeu_avec), empreinte_du_jeu(jeu_sans))

    def test_nombreuses_et_partout(self):
        for ville, plan in PLANS.items():
            with self.subTest(ville=ville):
                denses = plan["cachettes_denses"]
                lieux = {}
                for d in denses:
                    lieux[d["lieu"]] = lieux.get(d["lieu"], 0) + 1
                    self.assertEqual(set(d), {"lieu", "pos", "rot"})
                for lieu in ("sol", "toit", "vitre"):
                    self.assertGreater(lieux.get(lieu, 0), 300, lieu)
                if charger_theme(ville)["style"]["balcons"] in ("filants", "secours"):
                    self.assertGreater(lieux.get("balcon", 0), 300)
                # bien plus que les slots du jeu, sans exploser cachettes.json
                self.assertGreater(len(denses), 3000)
                self.assertLess(len(denses), 12000)

    def test_bien_plus_de_vitres_que_dans_le_jeu(self):
        # le jeu n'a une cachette « vitre » que dans 30 % des fenêtres ; ici : toutes, 3 par appui
        for ville, plan in PLANS.items():
            with self.subTest(ville=ville):
                jeu = sum(1 for s in plan["slots"] if s["lieu"] == "vitre")
                denses = [d for d in plan["cachettes_denses"] if d["lieu"] == "vitre"]
                self.assertGreater(len(denses), 4 * jeu)
                self.assertGreaterEqual(len({d["pos"][2] for d in denses}), 5)  # vitrines et plusieurs étages

    def test_au_sol_hors_des_immeubles(self):
        for ville, plan in PLANS.items():
            with self.subTest(ville=ville):
                for d in plan["cachettes_denses"]:
                    if d["lieu"] != "sol":
                        continue
                    x, y, _ = d["pos"]
                    self.assertFalse(any(a < x < c and b < y < e for a, b, c, e in plan["lots"]), d)

    def test_une_ville_minimale_a_aussi_ses_cachettes_denses(self):
        plan = make_layout(layout.fusionner({"id": "mini", "nom": "Mini", "graine": 7}))
        self.assertGreater(len(plan["cachettes_denses"]), 3000)


if __name__ == "__main__":
    unittest.main()
