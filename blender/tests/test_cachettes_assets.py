"""Les cachettes.json publiées dans assets/ sont cohérentes avec scenes.json (sans Blender)."""
import json
import os
import unittest

from citygen.cachettes import empreinte

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(RACINE, "assets")


def lire(chemin):
    with open(chemin, encoding="utf8") as f:
        return json.load(f)


class TestCachettesAssets(unittest.TestCase):
    def test_chaque_ville_a_des_cachettes_coherentes(self):
        scenes = lire(os.path.join(ASSETS, "scenes.json"))
        self.assertTrue(scenes)
        for entree in scenes:
            with self.subTest(ville=entree["id"]):
                d = lire(os.path.join(ASSETS, "scenes", entree["id"], "cachettes.json"))
                self.assertEqual(empreinte(d["cachettes"]), d["empreinte"])
                self.assertEqual(d["empreinte"], entree["empreinte"])
                self.assertEqual(d["version"], entree["version"])
                for c in d["cachettes"]:
                    self.assertEqual(len(c), 6)


if __name__ == "__main__":
    unittest.main()
