"""Cachettes denses du mode « Cacher » : nombreuses, et sans effet sur la partie normale.

Les 30 canards et les leurres du jeu sont tirés de make_layout()["slots"] par une suite de
tirages ; les records sont liés à la `version` de la ville. Les cachettes denses ne doivent
donc rien tirer au sort ni rien changer au reste du plan : tout leur code est sous le drapeau
`denses` de Plan, et le plan sans elles (denses=False) doit être identique au plan complet.
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
# Empreinte des cachettes denses candidates (make_layout()["cachettes_denses"]), relevée au
# commit 3a1cdad, celui des assets/scenes/*/cachettes.json publiés. Inchangée, elle prouve que
# ces fichiers restent valables sans relancer Blender ; changée, régénérer le placement
# (les défis déjà envoyés pour la ville deviennent invalides).
EMPREINTES_DENSES = {
    "delhi": "aa13cebf83b6b4c91c3b12e382fec2f485dc84dd1bc16ca6116861d794ea3ea9",
    "lille": "6cefbb71a8ef2c551ce7b99598590eb8ea586422afc22ef6f451a36a7cd920c3",
    "new_york": "7fedb07a00422a7721c11e72ecb17cefb17b9e27e2fea0e0078df176c14bcb7a",
    "paris": "645064df986f7d1abf6287a07486ec8ff080f14db00e8785a7f004a077adab61",
}
SI_VOULU = ("si le changement est voulu, régénérer puis vérifier d'abord que placements.json n'a pas "
            "changé (git diff --stat assets/scenes/*/placements.json)")


def empreinte(donnees):
    return hashlib.sha256(json.dumps(donnees, sort_keys=True).encode()).hexdigest()


def empreinte_du_jeu(plan):
    return empreinte({k: plan[k] for k in CLES_DU_JEU})


class TestCachettesDenses(unittest.TestCase):
    def test_le_plan_du_jeu_n_a_pas_change(self):
        for ville, attendue in EMPREINTES_PLAN.items():
            with self.subTest(ville=ville):
                self.assertEqual(empreinte_du_jeu(PLANS[ville]), attendue, SI_VOULU)

    def test_les_cachettes_denses_n_ont_pas_change(self):
        for ville, attendue in EMPREINTES_DENSES.items():
            with self.subTest(ville=ville):
                self.assertEqual(empreinte(PLANS[ville]["cachettes_denses"]), attendue, SI_VOULU)

    def test_ne_consomme_aucun_tirage(self):
        # Cachettes denses coupées (denses=False : aucune ligne de leur code ne tourne) : le
        # générateur finit dans le même état et produit exactement le même jeu, ville par ville.
        for ville in EMPREINTES_PLAN:
            with self.subTest(ville=ville):
                theme = charger_theme(ville)
                avec = layout.Plan(theme)
                jeu_avec = avec.construire()
                sans = layout.Plan(theme, denses=False)
                jeu_sans = sans.construire()
                self.assertEqual(avec.rng.getstate(), sans.rng.getstate())
                self.assertEqual(jeu_sans["cachettes_denses"], [])
                for cle in CLES_DU_JEU:
                    self.assertEqual(jeu_avec[cle], jeu_sans[cle], cle)
                self.assertEqual(make_layout(theme, denses=False)["cachettes_denses"], [])

    def test_une_cachette_dense_hors_du_drapeau_est_refusee(self):
        with self.assertRaises(RuntimeError):
            layout.Plan(charger_theme("lille"), denses=False).dense("sol", 0, 0, 0)

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
