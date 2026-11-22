"""Plan d'un quartier, en Python pur (pas de bpy) : testable hors de Blender.

make_layout(theme) renvoie :
  prims : primitives à mailler (bâti, sol, détails de façade et de toit)
  insts : instances de modèles du kit {type, pos, rot, k, c} (passants, véhicules, arbres, mobilier)
  slots : cachettes candidates {lieu, pos, rot}, lieu = sol | balcon | toit | vitre
  cachettes_denses : cachettes du mode « Cacher » seulement, même format que slots, posées
          sans aucun tirage (voir Plan.dense) : canards et leurres du jeu n'en dépendent pas
  lots  : emprises des immeubles [x0, y0, x1, y1]
  blocs : emprises des îlots, trottoir compris

Repère Blender : Z vers le haut, carte centrée sur l'origine, mètres.
La caméra de jeu est côté (+x, -y) : seules les façades sud et est sont détaillées.

Une ville = themes/<id>.json fusionné avec themes/_commun.json. Tout ce qui distingue
Paris de Delhi passe par theme["style"] ; aucune ville n'est codée en dur ici, sauf le
contenu de la place centrale (une fonction square_<nom> par ville).
"""
import json
import math
import os
import random

AZIMUT = 45.0
ELEVATION = 35.264
LOIN = (-math.sqrt(0.5), math.sqrt(0.5))    # direction horizontale qui s'éloigne de la caméra
LATERAL = (math.sqrt(0.5), math.sqrt(0.5))  # perpendiculaire à LOIN, à l'horizontale
PENTE = math.tan(math.radians(ELEVATION))   # un rayon vers la caméra monte de PENTE m par mètre
H_TROTTOIR = 0.15
MARGE_SLOT = 0.3
EP = 0.8          # profondeur des niches derrière les vitres
VISIBLES = "SE"   # façades tournées vers la caméra
# Modèles du kit (blender/build_kit.py) que la ville instancie au lieu de les mailler.
KIT = {"Perso_Debout", "Perso_Marche", "Perso_Salue", "Perso_Robe", "Perso_Raye", "Perso_Assis",
       "Perso_Buste", "Coiffe_Court", "Coiffe_Long", "Coiffe_Chignon", "Coiffe_Chapeau",
       "Coiffe_Casquette", "Voiture", "Taxi", "Camionnette", "Bus", "Rickshaw", "Arbre_A",
       "Arbre_B", "Arbre_C", "Banc", "Lampadaire", "Poubelle", "Table_Cafe", "Chaise", "Parasol",
       "Etal", "Vache",
       # kit_loufoque.py : animaux, tags, désordre, végétation, saynètes, coiffes folles
       "Chien", "Chat", "Pigeon", "Poule", "Singe", "Elephant", "Tag_Coin", "Tag_Zap", "Tag_Lol",
       "Tag_Coeur", "Tag_Smiley", "Tag_Couronne", "Tag_Fleche", "Tag_Eclair", "Tag_Canard", "Fissure",
       "Lierre", "Planches", "Echelle", "Flaque", "Cartons", "Canape", "Piano_Suspendu", "Fumee",
       "Borne_Geyser", "Fruits_Sol", "Tambour", "Barriere", "Trou", "Tas_Sable", "Brouette", "Confettis",
       "Sacs_Poubelle", "Poubelle_Renversee", "Transat", "Chevalet", "Ballons", "Velo", "Lampadaire_Tordu",
       "Pot_Plante", "Pot_Fleurs", "Buisson", "Massif_Fleurs", "Palmier", "Arbre_D", "Coiffe_Toque",
       "Coiffe_Couronne", "Coiffe_HautDeForme", "Coiffe_Cone", "Coiffe_Sombrero", "Coiffe_Heaume",
       "Coiffe_Helice", "Coiffe_Lapin"}
TAGS = ["Tag_Coin", "Tag_Zap", "Tag_Lol", "Tag_Coeur", "Tag_Smiley", "Tag_Couronne", "Tag_Fleche",
        "Tag_Eclair", "Tag_Canard"]
COIFFES_FOLLES = ["Coiffe_Toque", "Coiffe_Couronne", "Coiffe_HautDeForme", "Coiffe_Cone", "Coiffe_Sombrero",
                  "Coiffe_Heaume", "Coiffe_Helice", "Coiffe_Lapin"]
DEBOUT = ["Perso_Debout", "Perso_Marche", "Perso_Salue", "Perso_Robe", "Perso_Raye"]
DZ_TETE = {"Perso_Assis": -0.12, "Perso_Buste": -0.56}  # tête plus basse que debout
VEHICULES = {  # type du thème -> (modèle, longueur, largeur, hauteur)
    "voiture": ("Voiture", 4.2, 1.8, 1.45), "taxi": ("Taxi", 4.2, 1.8, 1.55),
    "camionnette": ("Camionnette", 5.0, 2.0, 2.2), "bus": ("Bus", 9.0, 2.5, 2.95),
    "rickshaw": ("Rickshaw", 2.6, 1.4, 1.75), "bus_scolaire": ("Bus", 9.0, 2.5, 2.95),
}
DOSSIER_THEMES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "themes")

# Cachettes denses du mode « Cacher » (Plan.dense) : pas des grilles, en mètres.
DECALAGES_FENETRE = (-0.36, 0.0, 0.36)  # le long de l'appui, depuis le milieu de la fenêtre
PAS_VITRINE = 0.6
PAS_BALCON = 0.8
PAS_TOIT = 1.2
PAS_SOL = 1.0   # trottoirs et places
RUE_UN_SUR = 2  # chaussée : un point sur deux de la grille du sol, dans chaque sens


def _grille(a, b, pas):
    """Points espacés de `pas` dans [a, b], la grille centrée dans l'intervalle (vide s'il est trop court)."""
    if b < a:
        return []
    n = int((b - a) / pas) + 1
    debut = (a + b) / 2 - (n - 1) * pas / 2
    return [debut + i * pas for i in range(n)]


FACADES = {  # côté -> (coin d'origine, direction le long du mur, normale sortante)
    "S": (("x0", "y0"), (1, 0), (0, -1)),
    "N": (("x0", "y1"), (1, 0), (0, 1)),
    "W": (("x0", "y0"), (0, 1), (-1, 0)),
    "E": (("x1", "y0"), (0, 1), (1, 0)),
}


def _lire(nom):
    with open(os.path.join(DOSSIER_THEMES, nom + ".json"), encoding="utf8") as f:
        return json.load(f)


def villes():
    return sorted(f[:-5] for f in os.listdir(DOSSIER_THEMES) if f.endswith(".json") and not f.startswith("_"))


def fusionner(theme):
    """Complète le thème d'une ville avec _commun.json : palette et style héritent clé par clé."""
    commun = _lire("_commun")
    complet = {**{k: v for k, v in commun.items() if k not in ("palette", "style")}, **theme}
    complet["palette"] = {**commun["palette"], **theme.get("palette", {})}
    complet["style"] = {**commun["style"], **theme.get("style", {})}
    return complet


def charger_theme(ville):
    """Thème d'une ville (themes/<ville>.json), complété par _commun.json."""
    return fusionner(_lire(ville))


SAYNETES_RUE_SEULEMENT = {"peintre", "demenagement", "panne", "geyser", "chantier"}  # besoin d'un mur et d'une chaussée
TOITS = {"mansarde", "plat", "pignon"}
BALCONS = {"filants", "secours", "jharokha", "aucun"}
EXTRAS_TOIT = {"cheminee", "chateau_eau", "clim", "citerne", "cabanon", "dome", "linge", "transat", "jardin",
               "pigeons", "singe", "chat", "vache"}


class ThemeInvalide(ValueError):
    pass


def valider_theme(theme):
    """Vérifie un thème complet et lève ThemeInvalide avec la liste de toutes les fautes.

    Appelée au début de chaque génération : une faute de frappe dans un thème donne un
    message clair au lieu d'une erreur Python obscure en plein milieu de la génération.
    """
    from .placement import LEURRES  # import local : placement n'a pas besoin de layout

    s, pal, fautes = theme["style"], theme["palette"], []
    saynetes = {n[2:] for n in dir(Plan) if n.startswith("s_")}
    places = {n[7:] for n in dir(Plan) if n.startswith("square_")}

    def verifier(cle, valeurs, permis, quoi):
        for v in valeurs:
            if v not in permis:
                fautes.append(f"style.{cle} : « {v} » n'est pas {quoi} (possibles : {', '.join(sorted(permis))})")

    verifier("square", [s["square"]], places, "une place connue")
    verifier("toit", [s["toit"]], TOITS, "un type de toit")
    verifier("balcons", [s["balcons"]], BALCONS, "un type de balcon")
    verifier("toit_extras", s["toit_extras"], EXTRAS_TOIT, "un élément de toit")
    verifier("vehicules", s["vehicules"], VEHICULES, "un véhicule")
    verifier("saynetes_rue", s["saynetes_rue"], saynetes, "une saynète")
    verifier("saynetes_place", s["saynetes_place"], saynetes - SAYNETES_RUE_SEULEMENT,
             "une saynète possible sur une place")
    verifier("betes", s["betes"], KIT, "un modèle du kit")
    verifier("arbres_modeles", s["arbres_modeles"], KIT, "un modèle du kit")
    for lieu, types in theme["leurres_par_lieu"].items():
        verifier(f"leurres_par_lieu.{lieu}", types, LEURRES, "un leurre")
    couleurs = ["murs", "auvents", "voitures", "bus", "couleurs", "vetements", "pantalons", "peaux", "cheveux",
                "rayures", "fleurs", "linge", "accents", "poils", "tags_couleurs", "feuillages", "toits", "volets"]
    for cle in couleurs:
        verifier(cle, s.get(cle) or [], pal, "une couleur de la palette")
    verifier("bandeaux", s.get("bandeaux") or [], pal, "une couleur de la palette")
    for nom, h in pal.items():
        if not (isinstance(h, str) and len(h) == 7 and h.startswith("#")):
            fautes.append(f"palette.{nom} : « {h} » n'est pas une couleur #RRGGBB")
    cols, rangs = theme["grille"]
    if cols * rangs != theme["canards"]:
        fautes.append(f"grille {cols} x {rangs} = {cols * rangs} cases, mais canards = {theme['canards']} "
                      "(il faut exactement un canard par case)")
    n = theme["ilots"]
    bloc = (theme["taille"] - n * theme["rue"]) / n
    mini = 2 * (theme["trottoir"] + s["profondeur"]) + 4
    if bloc < mini:
        fautes.append(f"îlots de {bloc:.1f} m trop petits pour des immeubles de {s['profondeur']} m de profondeur "
                      f"(au moins {mini:.0f} m) : baisser ilots, rue ou style.profondeur, ou augmenter taille")
    i, j = theme["square"]
    if not (0 <= i < n and 0 <= j < n):
        fautes.append(f"square {theme['square']} hors de la grille d'îlots {n} x {n} (indices de 0 à {n - 1})")
    if fautes:
        liste = "".join(f"\n  - {f}" for f in fautes)
        raise ThemeInvalide(f"thème « {theme.get('id', '?')} » invalide :{liste}")


class Plan:
    def __init__(self, theme):
        self.t, self.s = theme, theme["style"]
        self.rng = random.Random(theme["graine"])
        self.demi = theme["taille"] / 2
        self.prims, self.slots, self.insts = [], [], []
        self.lots, self.blocs, self.herbes, self.emprises = [], [], [], []
        self.denses = []  # cachettes_denses : jamais de self.rng pour elles

    def choix(self, cle):
        if not self.s.get(cle):
            raise KeyError(f"style.{cle} : liste absente ou vide dans le thème et dans _commun.json")
        return self.rng.choice(self.s[cle])

    # ---- primitives -------------------------------------------------------
    def box(self, mat, size, pos, rot=0.0, haut=None, emprise=False):
        p = {"t": "box", "mat": mat, "size": list(size), "pos": list(pos), "rot": rot}
        if haut:
            p["haut"] = list(haut)
        self.prims.append(p)
        if emprise:
            r = max(size[0], size[1]) / 2
            hx, hy = (r, r) if rot else (size[0] / 2, size[1] / 2)
            self.emprises.append((pos[0] - hx, pos[1] - hy, pos[0] + hx, pos[1] + hy))

    def cyl(self, mat, r, h, base, r2=None, seg=8, emprise=False):
        """base = centre de la face du bas. seg >= 8 : pas de trait d'encre sur les flancs."""
        self.prims.append({"t": "cyl", "mat": mat, "r1": r, "r2": r if r2 is None else r2,
                           "h": h, "seg": seg, "pos": [base[0], base[1], base[2] + h / 2]})
        if emprise:
            self.emprises.append((base[0] - r, base[1] - r, base[0] + r, base[1] + r))

    def sph(self, mat, r, pos, scale=(1, 1, 1)):
        self.prims.append({"t": "sph", "mat": mat, "r": r, "pos": list(pos), "scale": list(scale)})

    def inst(self, typ, x, y, z, rot=0.0, k=1.0, **couleurs):
        """Instance d'un modèle du kit ; couleurs : rôle de teinte -> nom de la palette."""
        self.insts.append({"type": typ, "pos": [round(x, 3), round(y, 3), round(z, 3)],
                           "rot": round(rot, 3), "k": round(k, 3), "c": couleurs})

    def emprise(self, x, y, rx, ry=None):
        ry = rx if ry is None else ry
        self.emprises.append((x - rx, y - ry, x + rx, y + ry))

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

    def dense(self, lieu, x, y, z):
        """Cachette dense du mode « Cacher » : toutes les fenêtres, grilles au sol et sur les toits.

        Ne tire JAMAIS au sort (ni self.rng ni autre) : un tirage de plus décalerait toute la
        suite du plan, donc les 30 canards et les leurres du jeu. Sa rotation, qui ne sert
        qu'à varier l'angle essayé en premier pour le bec, est tirée de la position.
        """
        rot = (abs(x) * 7.31 + abs(y) * 3.17 + z * 1.93) % (2 * math.pi)
        self.denses.append({"lieu": lieu, "pos": [round(x, 3), round(y, 3), round(z, 3)], "rot": round(rot, 3)})

    def slot_sol(self, x, y):
        if self.libre(x, y):
            self.slot("sol", x, y, self.sol_z(x, y))

    def _derriere(self, x, y, r, h):
        """Point derrière un obstacle (demi-largeur r, hauteur h), plus ou moins masqué."""
        d = self.rng.uniform(r + 0.5, max(r + 0.7, h / PENTE + 0.2))
        lat = self.rng.uniform(-(r + 0.3), r + 0.3)
        return x + LOIN[0] * d + LATERAL[0] * lat, y + LOIN[1] * d + LATERAL[1] * lat

    def slot_derriere(self, x, y, r, h, n=3):
        """n cachettes au sol derrière un obstacle : à moitié cachées, pas tout ou rien."""
        for _ in range(n):
            self.slot_sol(*self._derriere(x, y, r, h))

    # ---- passants ---------------------------------------------------------
    def _personne(self, modele, x, y, z, rot, k=1.0, haut=None, coiffe="auto", chapeau=None):
        """Un personnage du kit, ses couleurs et sa coiffe (imposées ou tirées au sort)."""
        rng = self.rng
        self.inst(modele, x, y, z, rot, k,
                  haut=haut or (self.choix("rayures") if modele == "Perso_Raye" else self.choix("vetements")),
                  bas=self.choix("pantalons"), peau=self.choix("peaux"))
        if coiffe == "auto":
            if rng.random() < self.s["coiffes_folles"]:  # toque, heaume, plot sur la tête…
                coiffe = rng.choice(COIFFES_FOLLES)
            else:
                coiffe = rng.choices([None, "Coiffe_Court", "Coiffe_Long", "Coiffe_Chignon", "Coiffe_Chapeau",
                                      "Coiffe_Casquette"], [1, 4, 3, 1.5, 1.5, 1.5])[0]
        if coiffe:
            self.inst(coiffe, x, y, z + DZ_TETE.get(modele, 0.0) * k, rot, k,
                      cheveux=self.choix("cheveux"), chapeau=chapeau or self.choix("vetements"))

    def poser(self, typ, pos, z, rot=0.0, k=1.0, r=0.3, **couleurs):
        """Pose un modèle au sol s'il y a la place (r = 0 : sans emprise, toujours posé)."""
        if r and not self.libre(*pos):
            return False
        self.inst(typ, pos[0], pos[1], z, rot, k, **couleurs)
        if r:
            self.emprise(pos[0], pos[1], r)
        return True

    def figurant(self, pos, z, rot, modele=None, k=None, **options):
        """Un personnage de saynète, s'il y a la place."""
        if not self.libre(*pos):
            return False
        self._personne(modele or self.rng.choice(DEBOUT), pos[0], pos[1], z, rot,
                       k or self.rng.uniform(0.94, 1.06), **options)
        self.emprise(pos[0], pos[1], 0.25)
        return True

    # ---- saynètes : (P, le long, vers la rue, z, distance au mur ou None) ---------
    def s_chiens(self, P, ra, rd, z, m):
        self.figurant(P(0), z, ra, "Perso_Marche")
        for i in range(self.rng.randint(4, 6)):
            self.poser("Chien", P(0.8 + 0.5 * (i % 3) + self.rng.uniform(-0.1, 0.1), (i // 3) * 0.5 - 0.25), z,
                       ra + self.rng.uniform(-0.4, 0.4), self.rng.uniform(0.7, 1.25), r=0.2, poil=self.choix("poils"))

    def s_fanfare(self, P, ra, rd, z, m):
        couleur = self.choix("rayures")
        for i in range(6):
            self.figurant(P(i * 0.75), z, ra + math.pi, "Perso_Marche", haut=couleur,
                          coiffe="Coiffe_Casquette", chapeau=couleur)
        x, y = P(-0.55)
        self.inst("Tambour", x, y, z + 0.85, ra)

    def s_queue(self, P, ra, rd, z, m):
        for i in range(self.rng.randint(5, 8)):
            self.figurant(P(i * 0.62, self.rng.uniform(-0.08, 0.08)), z, ra + math.pi,
                          self.rng.choice(["Perso_Debout", "Perso_Robe", "Perso_Raye"]))

    def s_peintre(self, P, ra, rd, z, m):
        x, y = P(0, -m + 0.08)
        self.inst("Echelle", x, y, z, rd)
        x, y = P(0, -m + 0.5)
        self._personne("Perso_Salue", x, y, z + 1.6, rd + math.pi, coiffe="Coiffe_Casquette", haut="blanc")
        x, y = P(1.3, 0.2)
        self.inst("Flaque", x, y, z + 0.005, self.rng.uniform(0, 6), 0.8, flaque=self.choix("couleurs"))
        self.figurant(P(-1.3, 0.4), z, ra)

    def s_demenagement(self, P, ra, rd, z, m):
        x, y = P(0.5, m + 1.4)
        self.inst("Camionnette", x, y, 0.0, ra, caisse="blanc")
        self.emprise(x, y, 2.5)
        self.poser("Cartons", P(-1.2, 0.3), z, ra, r=0.5)
        self.poser("Cartons", P(1.9, -0.2), z, ra + 1.0, r=0.5)
        self.poser("Canape", P(3.3, 0.1), z, rd, r=0.9, toile=self.choix("auvents"))
        x, y = P(-2.4, -m + 0.8)
        self.inst("Piano_Suspendu", x, y, z + 4.2, rd)  # le piano monte par la façade
        self.figurant(P(-2.4, 0.7), z, rd + math.pi, "Perso_Salue")
        self.figurant(P(-3.1, 0.4), z, rd + math.pi, "Perso_Salue")

    def s_panne(self, P, ra, rd, z, m):
        x, y = P(0, m + 1.4)
        self.inst("Voiture", x, y, 0.0, ra, caisse=self.choix("voitures"))
        self.emprise(x, y, 2.2)
        x, y = P(1.6, m + 1.4)
        self.inst("Fumee", x, y, 0.9)
        self.figurant(P(3.0, m + 1.0), 0.0, ra, "Perso_Salue")
        self.slot_derriere(*P(0, m + 1.4), 1.0, 1.4, n=2)

    def s_geyser(self, P, ra, rd, z, m):
        self.poser("Borne_Geyser", P(0, m - 0.5), z, r=0.2)
        x, y = P(0.3, m + 1.0)
        self.inst("Flaque", x, y, 0.005, 0.5, 1.7, flaque="eau")
        for a, c in ((-0.9, 0.3), (0.9, 0.2), (-0.4, -0.5), (0.6, -0.6)):
            self.figurant(P(a, m - 0.5 + c), z, self.rng.uniform(0, 6.28), "Perso_Salue", k=0.68)

    def s_etal_renverse(self, P, ra, rd, z, m):
        x, y = P(0)
        self.inst("Fruits_Sol", x, y, z, self.rng.uniform(0, 6.28))
        self.figurant(P(-1.1, 0.2), z, ra, "Perso_Salue")
        self.poser("Chien", P(1.2, -0.2), z, ra + math.pi, r=0.2, poil=self.choix("poils"))
        self.poser("Poule", P(0.6, 0.6), z, self.rng.uniform(0, 6.28), r=0.15, poil=self.choix("poils"))

    def s_musicien(self, P, ra, rd, z, m):
        self.figurant(P(0, -0.5), z, rd, "Perso_Debout", coiffe="Coiffe_HautDeForme")
        for i in range(6):
            self.figurant(P(-1.5 + i * 0.6, 0.85 + 0.25 * (i % 2)), z, rd + math.pi)

    def s_chantier(self, P, ra, rd, z, m):
        x, y = P(0, m + 1.7)
        self.inst("Trou", x, y, 0.0)
        self.emprise(x, y, 1.1)
        self.poser("Barriere", P(0, m + 0.45), 0.0, ra, r=0.4)
        self.poser("Barriere", P(-1.5, m + 1.7), 0.0, rd, r=0.4)
        self.poser("Barriere", P(1.5, m + 1.7), 0.0, rd, r=0.4)
        self.poser("Tas_Sable", P(2.9, m + 1.5), 0.0, r=0.9)
        self.poser("Brouette", P(-2.8, m + 1.4), 0.0, ra, r=0.5)
        self.figurant(P(0.4, m + 3.1), 0.0, rd + math.pi, "Perso_Debout", coiffe="Coiffe_Casquette", chapeau="v_orange")
        self.slot_derriere(*P(2.9, m + 1.5), 0.9, 0.7, n=2)

    def s_mariage(self, P, ra, rd, z, m):
        self.figurant(P(-0.3), z, rd, "Perso_Robe", haut="blanc", coiffe="Coiffe_Chignon")
        self.figurant(P(0.3), z, rd, "Perso_Debout", haut="v_marine", coiffe="Coiffe_HautDeForme")
        x, y = P(0, 0.7)
        self.inst("Confettis", x, y, z + 0.01)
        for i in range(6):
            self.figurant(P(-1.8 + i * 0.7, 1.4), z, rd + math.pi, "Perso_Salue")

    def s_ballons(self, P, ra, rd, z, m):
        if self.figurant(P(0), z, rd):
            x, y = P(0)
            teintes = [self.choix("couleurs") for _ in range(3)]
            if self.rng.random() < 0.5:
                teintes[0] = "jaune"
            self.inst("Ballons", x, y, z, 0.0, b1=teintes[0], b2=teintes[1], b3=teintes[2])
        self.figurant(P(0.8, 0.3), z, ra + math.pi, "Perso_Salue", k=0.68)
        self.figurant(P(-0.7, 0.4), z, ra, k=0.68)

    def s_ordures(self, P, ra, rd, z, m):
        self.poser("Sacs_Poubelle", P(0, -0.2), z, self.rng.uniform(0, 6), r=0.5)
        self.poser("Poubelle_Renversee", P(1.3, 0), z, ra, r=0.3)
        self.poser("Chat", P(-0.9, 0.1), z, rd, r=0.15, poil=self.choix("poils"))
        self.poser("Cartons", P(-1.7, -0.3), z, 0.4, r=0.5)

    def s_artiste(self, P, ra, rd, z, m):
        self.poser("Chevalet", P(0), z, ra, r=0.4, toile=self.choix("couleurs"))
        self.figurant(P(0.85), z, ra + math.pi, "Perso_Debout", coiffe="Coiffe_Chapeau")
        self.figurant(P(1.7, 0.5), z, ra + math.pi)
        self.figurant(P(1.8, -0.4), z, ra + math.pi)

    def s_pigeons(self, P, ra, rd, z, m):
        self.figurant(P(0, -0.4), z, rd)
        for _ in range(9):
            self.poser("Pigeon", P(self.rng.uniform(-1.6, 1.6), self.rng.uniform(0.0, 1.4)), z,
                       self.rng.uniform(0, 6.28), r=0.1)

    def s_velos(self, P, ra, rd, z, m):
        for i in range(self.rng.randint(3, 5)):
            self.poser("Velo", P(i * 0.5, 0.0), z, rd + 0.25, r=0.2, caisse=self.choix("couleurs"))

    def s_elephant(self, P, ra, rd, z, m):
        if self.poser("Elephant", P(0), z, ra, r=1.6, toile=self.choix("auvents")):
            x, y = P(-0.1)
            self._personne("Perso_Assis", x, y, z + 2.62, ra, coiffe="Coiffe_Couronne")
        for a, c in ((2.6, 0.8), (2.9, -0.6), (-2.6, 0.9)):
            self.figurant(P(a, c), z, ra + math.pi, "Perso_Salue")

    def s_geant(self, P, ra, rd, z, m):
        """Géant de procession : un personnage de plus de cinq mètres et ses porteurs."""
        x, y = P(0)
        if not self.libre(x, y):
            return
        self._personne("Perso_Robe", x, y, z, rd, 3.2, coiffe="Coiffe_Couronne")
        self.emprise(x, y, 0.9)
        for a, c in ((1.5, 0.6), (-1.5, 0.6), (1.2, -0.9), (-1.2, -0.9), (0, 1.6)):
            self.figurant(P(a, c), z, rd + math.pi, "Perso_Salue")

    def saynete(self, nom, P, ra, rd, z, m):
        getattr(self, "s_" + nom)(P, ra, rd, z, m)
        self.slot_derriere(*P(0), 0.6, 1.2, n=2)

    def passant(self, x, y, z, emprise=True):
        rng = self.rng
        modele = rng.choices(["Perso_Debout", "Perso_Marche", "Perso_Salue", "Perso_Robe", "Perso_Raye"],
                             [4, 4, 1, 3, 1.5])[0]
        k = 0.68 if rng.random() < 0.12 else rng.uniform(0.94, 1.06)  # un enfant sur huit
        self._personne(modele, x, y, z, rng.uniform(0, 2 * math.pi), k)
        if emprise:
            self.emprise(x, y, 0.25)
            if rng.random() < 0.35:
                self.slot_derriere(x, y, 0.2, 1.6, n=1)

    def buste(self, x, y, z, rot):
        """Quelqu'un accoudé à sa fenêtre, tourné vers `rot`."""
        self._personne("Perso_Buste", x, y, z, rot)

    def foule(self, n, tirage):
        for _ in range(n):
            x, y = tirage()
            if self.libre(x, y):
                self.passant(x, y, self.sol_z(x, y))

    # ---- mobilier ---------------------------------------------------------
    def arbre(self, x, y, z, k=1.0):
        rng = self.rng
        modele = self.choix("arbres_modeles")
        self.inst(modele, x, y, z, rng.uniform(0, 2 * math.pi), k * rng.uniform(0.9, 1.12),
                  feuille=self.choix("feuillages"))
        self.emprise(x, y, 0.2 * k)
        self.slot_derriere(x, y, 0.15 * k, 2.4 * k, n=2)
        for _ in range(2):  # sous le feuillage, vu de la caméra
            d, lat = rng.uniform(3.3, 5.6) * k, rng.uniform(-1.3, 1.3)
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
        self.inst("Lampadaire", x, y, z)
        self.emprise(x, y, 0.15)

    def banc(self, x, y, z, rot=0.0):
        self.inst("Banc", x, y, z, rot)
        if rot % math.pi < 1e-6:
            self.emprise(x, y, 0.75, 0.3)
        else:
            self.emprise(x, y, 0.75)
        self.slot_derriere(x, y, 0.75, 0.9)

    def poubelle(self, x, y, z):
        self.inst("Poubelle", x, y, z)
        self.emprise(x, y, 0.28)
        self.slot_derriere(x, y, 0.28, 0.86)

    def rayures(self, mats, taille, centre, le_long_de_x, pas=0.6):
        """Toile rayée : bandes alternées de deux couleurs (store, auvent d'étal)."""
        long = taille[0] if le_long_de_x else taille[1]
        n = max(1, round(long / pas))
        for i in range(n):
            d = -long / 2 + (i + 0.5) * long / n
            size = (long / n, taille[1], taille[2]) if le_long_de_x else (taille[0], long / n, taille[2])
            pos = (centre[0] + d, centre[1], centre[2]) if le_long_de_x else (centre[0], centre[1] + d, centre[2])
            self.box(mats[i % len(mats)], size, pos)

    def toile(self):
        """Couleurs d'une toile : parfois jaune (gros leurre de décor), souvent rayée."""
        if self.rng.random() < self.s["toile_jaune"]:
            return ["jaune"]
        a = self.choix("auvents")
        return [a, "blanc"] if self.rng.random() < 0.6 else [a]

    def etal(self, x, y, z, le_long_de_x):
        """Étal de marché du kit ; le bout libre de sa table reçoit parfois un objet."""
        self.inst("Etal", x, y, z, 0.0 if le_long_de_x else math.pi / 2, toile=self.toile()[0])
        if le_long_de_x:
            self.emprise(x, y, 1.0, 0.45)
        else:
            self.emprise(x, y, 0.45, 1.0)
        if self.rng.random() < 0.6:
            px, py = (x + 0.7, y) if le_long_de_x else (x, y + 0.7)
            self.slot("sol", px, py, z + 0.82)
        self.slot_derriere(x, y, 1.0, 0.8, n=2)

    def fontaine(self, cx, cy, z):
        self.cyl("pierre", 3.0, 0.5, (cx, cy, z), seg=20, emprise=True)
        self.cyl("eau", 2.6, 0.52, (cx, cy, z), seg=20)
        self.cyl("pierre", 0.4, 1.7, (cx, cy, z))
        self.cyl("pierre", 1.0, 0.25, (cx, cy, z + 1.7), r2=1.3, seg=12)
        for _ in range(12):  # sur la margelle
            a = self.rng.uniform(0, 2 * math.pi)
            self.slot("sol", cx + 2.8 * math.cos(a), cy + 2.8 * math.sin(a), z + 0.5)

    def arche(self, cx, cy, z, large, haut, ep, mat, le_long_de_x=True):
        """Porte monumentale : deux piles et un linteau."""
        pile = large * 0.28
        for d in (-(large - pile) / 2, (large - pile) / 2):
            pos = (cx + d, cy, z + haut * 0.35) if le_long_de_x else (cx, cy + d, z + haut * 0.35)
            self.box(mat, (pile, ep, haut * 0.7) if le_long_de_x else (ep, pile, haut * 0.7), pos, emprise=True)
            self.slot_derriere(pos[0], pos[1], pile / 2, 2.0, n=3)
        self.box(mat, (large, ep, haut * 0.3) if le_long_de_x else (ep, large, haut * 0.3), (cx, cy, z + haut * 0.85))
        self.box("pierre", (large + 0.6, ep + 0.6, 0.4) if le_long_de_x else (ep + 0.6, large + 0.6, 0.4),
                 (cx, cy, z + haut + 0.2))

    # ---- véhicules --------------------------------------------------------
    def vehicule(self, x, y, le_long_de_x, typ=None):
        """Pose un véhicule du kit et renvoie sa longueur. Taxis, camionnettes et capotes de
        rickshaw sont jaunes : ce sont les gros leurres du décor."""
        typ = typ or self.choix("vehicules")
        modele, long, larg, h = VEHICULES[typ]
        rot = (0.0 if le_long_de_x else math.pi / 2) + (math.pi if self.rng.random() < 0.5 else 0.0)
        couleurs = {"voiture": {"caisse": self.choix("voitures")}, "taxi": {"caisse": "jaune"},
                    "camionnette": {"caisse": "jaune"}, "bus": {"caisse": self.choix("bus")}, "bus_scolaire": {"caisse": "jaune"},
                    "rickshaw": {"caisse": "vertfonce", "toit": "jaune"}}[typ]
        self.inst(modele, x, y, 0.0, rot, **couleurs)
        if le_long_de_x:
            self.emprise(x, y, long / 2, larg / 2)
        else:
            self.emprise(x, y, larg / 2, long / 2)
        self.slot_derriere(x, y, larg / 2 + 0.1, h)
        return long

    def vache(self, x, y, z):
        self.inst("Vache", x, y, z, self.rng.uniform(0, 2 * math.pi))
        self.emprise(x, y, 0.85)
        self.slot_derriere(x, y, 0.8, 1.3, n=2)

    # ---- façades ----------------------------------------------------------
    def _facade(self, rect, cote):
        coins = dict(zip(("x0", "y0", "x1", "y1"), rect))
        (cx, cy), u, n = FACADES[cote]
        longueur = (rect[2] - rect[0]) if u[0] else (rect[3] - rect[1])
        return (coins[cx], coins[cy]), u, n, longueur

    @staticmethod
    def _pt(f, s, o):
        a, u, n, _ = f
        return a[0] + u[0] * s + n[0] * o, a[1] + u[1] * s + n[1] * o

    def _el(self, f, mat, s0, s1, o0, o1, zb, zh, haut=None):
        """Boîte sur une façade : [s0, s1] le long du mur, [o0, o1] vers l'extérieur, [zb, zh]."""
        x, y = self._pt(f, (s0 + s1) / 2, (o0 + o1) / 2)
        la, th = s1 - s0, o1 - o0
        self.box(mat, (la, th, zh - zb) if f[1][0] else (th, la, zh - zb), (x, y, (zb + zh) / 2), haut=haut)

    def facade(self, f, n, haut, mur, trim):
        """Façade détaillée : vitrine au rez-de-chaussée, fenêtres en niche derrière une vitre.

        Le mur est une peau de EP m devant le noyau de l'immeuble : bandeaux horizontaux
        (allèges et linteaux) et trumeaux verticaux. Les trous entre eux sont de vraies
        niches où l'on peut poser un objet, fermées par une vitre.
        """
        rng, s = self.rng, self.s
        long = f[3]
        z0, he, rdc, al, wf = H_TROTTOIR, s["hauteur_etage"], s["rdc"], 0.9, 1.1
        hf = he - 1.4
        self._el(f, "interieur", 0, long, -EP, -EP + 0.05, z0, z0 + haut)  # fond sombre des niches

        rot_mur = math.atan2(f[2][1], f[2][0]) + math.pi / 2  # modèles muraux : face vers la rue

        def mural(typ, sx, o, z, k=1.0, **c):
            x, y = self._pt(f, sx, o)
            self.inst(typ, x, y, z, rot_mur, k, **c)

        # rez-de-chaussée : vitrine, ou rideau de fer tagué si la boutique est fermée
        ferme = long > 3 and rng.random() < s["rideaux"]
        zl = z0 + rdc - 0.6
        self._el(f, trim, 0, long, -EP, 0, z0, z0 + 0.4)
        for s0, s1 in ((0, 0.45), (long - 0.45, long)):
            self._el(f, mur, s0, s1, -EP, 0.06, z0, z0 + rdc)
        porte = rng.uniform(1.3, long - 1.3) if long > 4 else None
        if porte:
            self._el(f, "porte", porte - 0.5, porte + 0.5, -EP, -0.12, z0, zl)
        if ferme:
            self._el(f, "metal", 0.45, long - 0.45, -0.13, -0.09, z0 + 0.4, zl)
            for _ in range(rng.randint(1, 3)):
                mural(rng.choice(TAGS), rng.uniform(1.2, long - 1.2), -0.085, z0 + rng.uniform(0.6, 1.6),
                      rng.uniform(0.8, 1.2), tag=self.choix("tags_couleurs"))
        else:
            self._el(f, "verre", 0.45, long - 0.45, -0.1, -0.07, z0 + 0.4, zl)
        sx = 0.45
        while sx < long - 0.4:  # montants de vitrine
            self._el(f, "blanc", sx - 0.035, sx + 0.035, -0.14, -0.06, z0 + 0.4, zl)
            sx += (long - 0.9) / max(1, round((long - 0.9) / 1.7))
        if rng.random() < s["auvent"]:
            x, y = self._pt(f, long / 2, 0.66)
            taille = (long - 1.2, 1.2, 0.1) if f[1][0] else (1.2, long - 1.2, 0.1)
            self.rayures(self.toile(), taille, (x, y, z0 + rdc - 0.45), bool(f[1][0]), pas=0.7)
        sx = long if ferme else 0.9
        while sx < long - 0.9:
            if porte is None or abs(sx - porte) > 0.85:
                x, y = self._pt(f, sx, -rng.uniform(0.38, 0.56))
                if rng.random() < 0.45:  # marchandise en vitrine
                    h = rng.uniform(0.25, 0.6)
                    self.box(self.choix("couleurs"), (0.3, 0.3, h), (x, y, z0 + 0.4 + h / 2))
                else:
                    self.slot("vitre", x, y, z0 + 0.4)
            sx += rng.uniform(0.9, 1.5)
        if not ferme:  # cachettes denses : tout le long de la vitrine, hors de la porte
            for i in range(int((long - 1.8) / PAS_VITRINE) + 1):
                sx = 0.9 + i * PAS_VITRINE
                if porte is None or abs(sx - porte) > 0.85:
                    self.dense("vitre", *self._pt(f, sx, -0.47), z0 + 0.4)

        # étages : trumeaux sur toute la hauteur, bandeaux sur toute la longueur
        k = max(1, int(long / 2.4))
        centres = [(i + 0.5) * long / k for i in range(k)]
        bords = [0.0] + [c + d for c in centres for d in (-wf / 2, wf / 2)] + [long]
        for i in range(0, len(bords), 2):
            self._el(f, mur, bords[i], bords[i + 1], -EP, 0.06, z0 + rdc, z0 + haut)
        for e in range(n + 1):
            zb = z0 + rdc + e * he - (0.6 if e == 0 else 0.5)
            self._el(f, trim, 0, long, -EP, 0, zb, min(z0 + haut, z0 + rdc + e * he + al))
        # tags sur les bandeaux entre deux rangées de fenêtres, lierre et fissures sur les trumeaux
        libres = [e for e in range(1, n + 1) if not (s["balcons"] == "filants" and e in (1, 2, n - 2, n - 1))] or [n]
        if long > 2.6 and rng.random() < s["tags"]:
            for _ in range(rng.randint(1, 3)):
                e = rng.choice(libres[:2] + libres)  # plus souvent en bas
                k = rng.uniform(0.75, 1.15)
                mural(rng.choice(TAGS), rng.uniform(1.1, long - 1.1), 0.065, z0 + rdc + e * he - 0.35, k,
                      tag=self.choix("tags_couleurs"))
        if rng.random() < s["lierre"]:
            mural("Lierre", rng.choice(bords[::2]) + 0.3, 0.07, z0, rng.uniform(1.0, 1.7), feuille=self.choix("feuillages"))
        if rng.random() < s["fissures"]:
            mural("Fissure", rng.choice(bords[::2]) + 0.25, 0.065, z0 + rdc + rng.uniform(0.5, 3.0), rng.uniform(1.0, 2.2))
        volets = self.choix("volets") if s["volets"] and rng.random() < 0.6 else None
        for e in range(n):
            zs = z0 + rdc + e * he + al  # appui de fenêtre = sol de la niche
            self._el(f, "verre", 0.1, long - 0.1, -0.1, -0.07, zs, zs + hf)
            for c in centres:
                if s["balcons"] == "jharokha" and e >= 1 and rng.random() < 0.22:
                    self._el(f, self.choix("accents"), c - 0.75, c + 0.75, 0.06, 0.7, zs - 0.3, zs + hf + 0.2)
                    self._el(f, "interieur", c - 0.4, c + 0.4, 0.7, 0.72, zs, zs + hf - 0.2)
                    self._el(f, "blanc", c - 0.85, c + 0.85, 0.0, 0.8, zs + hf + 0.2, zs + hf + 0.6, haut=(0.5, 0.5))
                    continue
                # croisée : un montant et une traverse, qui masquent un peu ce qui est derrière
                self._el(f, "blanc", c - 0.03, c + 0.03, -0.14, -0.06, zs, zs + hf)
                self._el(f, "blanc", c - wf / 2, c + wf / 2, -0.14, -0.06, zs + hf * 0.62, zs + hf * 0.62 + 0.05)
                if rng.random() < s["planches"]:  # fenêtre condamnée
                    mural("Planches", c, 0.07, zs + hf / 2)
                    continue
                for d in DECALAGES_FENETRE:  # cachettes denses : chaque fenêtre, plusieurs places
                    self.dense("vitre", *self._pt(f, c + d, -0.47), zs)
                if volets:
                    self._el(f, volets, c - wf / 2 - 0.3, c - wf / 2, 0.06, 0.11, zs, zs + hf)
                    self._el(f, volets, c + wf / 2, c + wf / 2 + 0.3, 0.06, 0.11, zs, zs + hf)
                x, y = self._pt(f, c + rng.uniform(-0.25, 0.25), -rng.uniform(0.38, 0.56))
                tirage = rng.random()
                if tirage < 0.30:
                    self.slot("vitre", x, y, zs)
                elif tirage < 0.40:
                    self.buste(x, y, zs, math.atan2(f[2][1], f[2][0]))
                elif tirage < 0.40 + s["jardinieres_fenetre"]:
                    self._el(f, "terre", c - 0.45, c + 0.45, 0.0, 0.22, zs - 0.22, zs)
                    fleur = self.choix("fleurs")
                    for d in (-0.28, 0.0, 0.28):
                        px, py = self._pt(f, c + d, 0.11)
                        self.sph(fleur, 0.1, (px, py, zs + 0.06))

    def balcons(self, f, n):
        rng, s = self.rng, self.s
        long, z0, he, rdc = f[3], H_TROTTOIR, s["hauteur_etage"], s["rdc"]
        if s["balcons"] == "filants":
            for e in {1, n - 2}:
                if e < 1:
                    continue
                zf = z0 + rdc + e * he
                self._el(f, "pierre", 0.3, long - 0.3, 0.0, 0.8, zf - 0.12, zf)
                self._el(f, "fer", 0.3, long - 0.3, 0.75, 0.8, zf, zf + 0.45)
                sx = 0.8
                while sx < long - 0.8:
                    x, y = self._pt(f, sx, rng.uniform(0.25, 0.55))
                    tirage = rng.random()
                    if tirage < 0.08:
                        self.passant(x, y, zf, emprise=False)
                    elif tirage < 0.08 + s["pots"]:
                        self.inst(rng.choice(["Pot_Plante", "Pot_Fleurs"]), x, y, zf, 0.0, rng.uniform(0.8, 1.2),
                                  feuille=self.choix("feuillages"), fleur=self.choix("fleurs"))
                    else:
                        self.slot("balcon", x, y, zf)
                    sx += 1.3
                for i in range(int((long - 1.2) / PAS_BALCON) + 1):  # cachettes denses
                    self.dense("balcon", *self._pt(f, 0.6 + i * PAS_BALCON, 0.4), zf)
        elif s["balcons"] == "secours":  # escalier de secours new-yorkais
            c = rng.uniform(1.7, long - 1.7) if long > 3.6 else long / 2
            demi = min(1.3, long / 2 - 0.2)
            for e in range(1, n):
                zf = z0 + rdc + e * he
                self._el(f, "fer", c - demi, c + demi, 0.06, 0.96, zf - 0.08, zf)
                self._el(f, "fer", c - demi, c + demi, 0.92, 0.96, zf, zf + 0.5)
                echelle = c + (demi - 0.3) * (1 if e % 2 else -1)
                self._el(f, "fer", echelle - 0.2, echelle + 0.2, 0.5, 0.55, zf - he, zf)
                for d in (-0.5, 0.5):
                    x, y = self._pt(f, c + d * demi, rng.uniform(0.3, 0.7))
                    self.slot("balcon", x, y, zf)
                for i in range(int((2 * demi - 0.6) / PAS_BALCON) + 1):  # cachettes denses
                    self.dense("balcon", *self._pt(f, c - demi + 0.3 + i * PAS_BALCON, 0.5), zf)

    # ---- toits ------------------------------------------------------------
    def extra_toit(self, typ, x, y, z):
        """Pose un élément de toit, renvoie (demi-largeur, hauteur) pour les cachettes."""
        rng = self.rng
        if typ == "transat":
            rot = rng.uniform(0, 6.28)
            self.inst("Transat", x, y, z, rot, toile=self.choix("auvents"))
            if rng.random() < 0.6:
                self._personne("Perso_Assis", x, y, z - 0.12, rot)
            return 0.6, 0.9
        if typ == "jardin":
            self.inst("Buisson", x, y, z, rng.uniform(0, 6.28), 0.8, feuille=self.choix("feuillages"))
            for a in (0.5, 2.6, 4.4):
                self.inst(rng.choice(["Pot_Plante", "Pot_Fleurs"]), x + 0.9 * math.cos(a), y + 0.9 * math.sin(a), z,
                          0.0, rng.uniform(0.9, 1.3), feuille=self.choix("feuillages"), fleur=self.choix("fleurs"))
            return 0.9, 0.9
        if typ in ("pigeons", "singe", "chat"):
            modele, nb = {"pigeons": ("Pigeon", 5), "singe": ("Singe", 2), "chat": ("Chat", 1)}[typ]
            for _ in range(nb):
                self.inst(modele, x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.6, 0.6), z, rng.uniform(0, 6.28),
                          poil=self.choix("poils"))
            return 0.3, 0.5
        if typ == "vache":  # que fait-elle là ?
            self.inst("Vache", x, y, z, rng.uniform(0, 6.28), 0.8)
            return 0.7, 1.1
        if typ == "chateau_eau":
            for dx in (-0.6, 0.6):
                for dy in (-0.6, 0.6):
                    self.box("fer", (0.12, 0.12, 1.6), (x + dx, y + dy, z + 0.8))
            self.cyl("bois", 1.0, 1.7, (x, y, z + 1.6), seg=10)
            self.cyl("zinc", 1.1, 0.7, (x, y, z + 3.3), r2=0.05, seg=10)
            return 1.0, 4.0
        if typ == "clim":
            self.box("metal", (1.2, 0.9, 0.8), (x, y, z + 0.4))
            return 0.6, 0.8
        if typ == "citerne":
            self.cyl("citerne", 0.6, 1.1, (x, y, z), seg=10)
            return 0.6, 1.1
        if typ == "cabanon":
            self.box("pierre", (1.8, 2.2, 2.1), (x, y, z + 1.05))
            self.box("porte", (0.8, 0.05, 1.7), (x, y - 1.12, z + 0.85))
            return 1.1, 2.1
        if typ == "dome":
            self.box("blanc", (2.0, 2.0, 1.5), (x, y, z + 0.75))
            self.sph(self.choix("accents"), 1.0, (x, y, z + 1.5), (1, 1, 0.95))
            self.cyl("fer", 0.05, 0.6, (x, y, z + 2.4), seg=6)
            return 1.0, 2.5
        if typ == "linge":
            for dx in (-1.4, 1.4):
                self.cyl("fer", 0.04, 1.9, (x + dx, y, z), seg=6)
            for i in range(5):
                h = rng.uniform(0.5, 0.9)
                self.box(self.choix("linge"), (0.45, 0.04, h), (x - 1.1 + i * 0.55, y, z + 1.85 - h / 2))
            return 1.4, 1.9
        self.box("cheminee", (0.7, 0.7, 1.3), (x, y, z + 0.65))
        return 0.35, 1.3

    def _garnir_toit(self, rect, z, marge):
        """Éléments de toit, cachettes derrière eux, quelques cachettes libres, des gens."""
        rng = self.rng
        x0, y0, x1, y1 = rect
        if x1 - x0 < 2 * marge + 0.6 or y1 - y0 < 2 * marge + 0.6:
            return
        poses = []
        for _ in range(rng.randint(1, 1 + int((x1 - x0) * (y1 - y0) / 30))):
            for _ in range(6):
                px, py = rng.uniform(x0 + marge, x1 - marge), rng.uniform(y0 + marge, y1 - marge)
                if all(math.hypot(px - a, py - b) > 2.8 for a, b in poses):
                    break
            else:
                continue
            poses.append((px, py))
            r, h = self.extra_toit(self.choix("toit_extras"), px, py, z)
            for _ in range(3):
                sx, sy = self._derriere(px, py, r, h)
                if x0 + 0.9 < sx < x1 - 0.9 and y0 + 0.9 < sy < y1 - 0.9 \
                        and all(math.hypot(sx - a, sy - b) > 1.0 for a, b in poses):
                    self.slot("toit", sx, sy, z)
        for _ in range(3):
            self.slot("toit", rng.uniform(x0 + marge, x1 - marge), rng.uniform(y0 + marge, y1 - marge), z)
        if rng.random() < self.s["gens_sur_toits"]:
            self.passant(rng.uniform(x0 + marge, x1 - marge), rng.uniform(y0 + marge, y1 - marge), z, emprise=False)

    def _acrotere(self, a0, b0, a1, b1, z, mat, ep, h):
        """Muret bas au bord d'un toit plat, cachettes derrière les côtés sud et est."""
        rng = self.rng
        cx, cy = (a0 + a1) / 2, (b0 + b1) / 2
        for size, pos in (((a1 - a0, ep, h), (cx, b0 + ep / 2, z + h / 2)), ((a1 - a0, ep, h), (cx, b1 - ep / 2, z + h / 2)),
                          ((ep, b1 - b0, h), (a0 + ep / 2, cy, z + h / 2)), ((ep, b1 - b0, h), (a1 - ep / 2, cy, z + h / 2))):
            self.box(mat, size, pos)
        s = a0 + 0.7
        while s < a1 - 0.9:
            self.slot("toit", s, b0 + ep + rng.uniform(0.2, 0.5), z)
            s += rng.uniform(1.2, 2.0)
        s = b0 + 0.9
        while s < b1 - 0.7:
            self.slot("toit", a1 - ep - rng.uniform(0.2, 0.5), s, z)
            s += rng.uniform(1.2, 2.0)

    def toit_mansarde(self, rect, haut):
        x0, y0, x1, y1 = rect
        lx, ly, cx, cy, z0 = x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2, H_TROTTOIR
        self.box("pierre", (lx + 0.4, ly + 0.4, 0.25), (cx, cy, z0 + haut - 0.125))  # corniche
        self.box("zinc", (lx + 0.3, ly + 0.3, 2.4), (cx, cy, z0 + haut + 1.2),
                 haut=(max(0.1, (lx - 1.8) / (lx + 0.3)), max(0.1, (ly - 1.8) / (ly + 0.3))))
        z = z0 + haut + 2.4
        self._acrotere(x0 + 0.9, y0 + 0.9, x1 - 0.9, y1 - 0.9, z, "zinc", 0.12, 0.4)
        self._garnir_toit(rect, z, 1.6)
        self._toit_dense(x0 + 1.3, y0 + 1.3, x1 - 1.3, y1 - 1.3, z)

    def toit_plat(self, rect, haut, mur):
        x0, y0, x1, y1 = rect
        lx, ly, cx, cy = x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2
        z = H_TROTTOIR + haut + 0.1
        self.box("toiture", (lx - 0.3, ly - 0.3, 0.1), (cx, cy, z - 0.05))
        self._acrotere(x0, y0, x1, y1, z - 0.1, mur, 0.25, 0.7)
        self._garnir_toit(rect, z, 1.5)
        self._toit_dense(x0 + 0.6, y0 + 0.6, x1 - 0.6, y1 - 0.6, z)

    def _toit_dense(self, a0, b0, a1, b1, z):
        """Cachettes denses sur un toit plat : grille régulière, centrée dans [a0, a1] x [b0, b1]."""
        for x in _grille(a0, a1, PAS_TOIT):
            for y in _grille(b0, b1, PAS_TOIT):
                self.dense("toit", x, y, z)

    def toit_pignon(self, rect, haut, mur, cotes):
        """Toit à deux pentes ; pignon à gradins flamand côté rue si le style le demande."""
        x0, y0, x1, y1 = rect
        lx, ly, cx, cy, z0 = x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2, H_TROTTOIR
        cote = next((c for c in cotes if c in VISIBLES), cotes[0])
        faitage_y = cote in "SN"  # le pignon regarde la rue
        hr = min(5.0, (lx if faitage_y else ly) * 0.55)
        self.box(self.choix("toits"), (lx + 0.3, ly + 0.3, hr), (cx, cy, z0 + haut + hr / 2),
                 haut=(0.04, 1) if faitage_y else (1, 0.04))
        # Souche de cheminée sur le faîtage : seul endroit plat d'un toit en pente. Son
        # rebord sud et est cache à moitié ce qu'on y perche.
        d = self.rng.uniform(-0.25, 0.25) * (ly if faitage_y else lx)
        px, py = (cx, cy + d) if faitage_y else (cx + d, cy)
        zs = z0 + haut + hr + 0.5
        self.box("cheminee", (1.0, 1.0, hr + 0.5), (px, py, z0 + haut + (hr + 0.5) / 2))
        self.box("cheminee", (1.0, 0.1, 0.2), (px, py - 0.45, zs + 0.1))
        self.box("cheminee", (0.1, 1.0, 0.2), (px + 0.45, py, zs + 0.1))
        self.slot("toit", px - 0.1 + self.rng.uniform(-0.1, 0.1), py + 0.1 + self.rng.uniform(-0.1, 0.1), zs)
        if self.s["gradins"] and cote in VISIBLES:
            f = self._facade(rect, cote)
            long = f[3]
            for i in range(4):
                demi = long / 2 * (1 - i / 4)
                self._el(f, mur, long / 2 - demi, long / 2 + demi, -0.4, 0.06,
                         z0 + haut + i * hr / 4, z0 + haut + (i + 1) * hr / 4 + (0.5 if i == 3 else 0))

    # ---- immeubles et îlots -----------------------------------------------
    def immeuble(self, rect, cotes, tour=False):
        rng, s = self.rng, self.s
        x0, y0, x1, y1 = rect
        n = rng.randint(*(s["etages_tour"] if tour else s["etages"]))
        haut = s["rdc"] + n * s["hauteur_etage"]
        mur = self.choix("murs")
        trim = self.choix("bandeaux") if s["bandeaux"] else mur
        visibles = [c for c in cotes if c in VISIBLES]
        self.lots.append(list(rect))
        # noyau : en retrait de EP derrière chaque façade détaillée
        nx1 = x1 - EP if "E" in visibles else x1
        ny0 = y0 + EP if "S" in visibles else y0
        self.box(mur, (nx1 - x0, y1 - ny0, haut), ((x0 + nx1) / 2, (ny0 + y1) / 2, H_TROTTOIR + haut / 2))
        for c in visibles:
            f = self._facade(rect, c)
            self.facade(f, n, haut, mur, trim)
            self.balcons(f, n)
        toit = "plat" if tour or (s["toit"] == "pignon" and rng.random() < s["part_toit_plat"]) else s["toit"]
        if toit == "mansarde":
            self.toit_mansarde(rect, haut)
        elif toit == "pignon":
            self.toit_pignon(rect, haut, mur, cotes)
        else:
            self.toit_plat(rect, haut, mur)

    def _decoupe(self, a, b):
        """Coupe [a, b] en lots de largeur proche de style.largeur_lot."""
        k = max(1, round((b - a) / self.rng.uniform(*self.s["largeur_lot"])))
        pas = (b - a) / k
        j = min(1.5, pas * 0.2)
        coupes = [a] + [a + pas * i + self.rng.uniform(-j, j) for i in range(1, k)] + [b]
        return list(zip(coupes[:-1], coupes[1:]))

    def ilot_bati(self, bx, by, bloc, fond):
        """Immeubles en anneau autour d'une cour. fond : îlot du bord nord ou ouest (tours permises)."""
        t, d = self.t["trottoir"], self.s["profondeur"]
        x0, y0, x1, y1 = bx + t, by + t, bx + bloc - t, by + bloc - t
        tour = lambda: fond and self.rng.random() < self.s["tours"]  # noqa: E731
        sud, nord = self._decoupe(x0, x1), self._decoupe(x0, x1)
        for i, (a, b) in enumerate(sud):
            self.immeuble((a, y0, b, y0 + d), "S" + ("W" if i == 0 else "") + ("E" if i == len(sud) - 1 else ""))
        for i, (a, b) in enumerate(nord):
            self.immeuble((a, y1 - d, b, y1), "N" + ("W" if i == 0 else "") + ("E" if i == len(nord) - 1 else ""), tour())
        for a, b in self._decoupe(y0 + d, y1 - d):
            self.immeuble((x0, a, x0 + d, b), "W", tour())
            self.immeuble((x1 - d, a, x1, b), "E")
        self._trottoirs(bx, by, bloc)

    def _trottoirs(self, bx, by, bloc):
        rng, s, t, z = self.rng, self.s, self.t["trottoir"], H_TROTTOIR
        bandes = {  # côté -> fonction (s le long, o depuis la bordure) -> (x, y)
            "S": lambda a, o: (bx + a, by + o),
            "N": lambda a, o: (bx + a, by + bloc - o),
            "W": lambda a, o: (bx + o, by + a),
            "E": lambda a, o: (bx + bloc - o, by + a),
        }
        for cote, pt in bandes.items():
            a = 2.0
            while a < bloc - 2.0:
                x, y = pt(a + rng.uniform(-0.6, 0.6), 0.7)
                tirage = rng.random()
                if tirage < s["arbres"]:
                    self.arbre(x, y, z)
                elif tirage < s["arbres"] + 0.10:
                    self.lampadaire(x, y, z)
                elif tirage < s["arbres"] + 0.18:
                    self.banc(x, y, z, 0.0 if cote in "SN" else math.pi / 2)
                elif tirage < s["arbres"] + 0.24:
                    self.poubelle(x, y, z)
                a += 3.5
            if cote in VISIBLES:  # devant les façades visibles : étals ou claustras de terrasse
                a = 4.0
                while a < bloc - 4.0:
                    tirage = rng.random()
                    if tirage < s["etals"]:
                        self.etal(*pt(a, t * 0.56), z, cote == "S")
                    elif tirage < s["etals"] + 0.4:
                        self.haie(*pt(a, t * 0.54), 2.6, cote == "S",
                                  mat=rng.choice(["bois", "vertfonce"]), ep=0.1, h=0.55)
                    a += 5.0
            ra = 0.0 if cote in "SN" else math.pi / 2                      # le long du trottoir
            rd = {"S": -math.pi / 2, "N": math.pi / 2, "W": math.pi, "E": 0.0}[cote]  # vers la chaussée
            if cote in VISIBLES:  # une ou deux saynètes par trottoir visible
                for a in (bloc * 0.3, bloc * 0.72):
                    if rng.random() < s["saynete_rue"]:
                        a0 = a + rng.uniform(-2, 2)
                        self.saynete(self.choix("saynetes_rue"), lambda da, b=0.0, a0=a0: pt(a0 + da, t / 2 - b),
                                     ra, rd, z, t / 2)
            for _ in range(s["nb_betes"]):
                self.poser(self.choix("betes"), pt(rng.uniform(1, bloc - 1), rng.uniform(0.3, t - 0.3)), z,
                           rng.uniform(0, 6.28), rng.uniform(0.8, 1.2), r=0.15, poil=self.choix("poils"))
            a = 2.5
            while a < bloc - 2.5:  # pots au pied des façades, parfois un lampadaire plié
                if rng.random() < s["pots"]:
                    self.poser(rng.choice(["Pot_Plante", "Pot_Fleurs", "Pot_Fleurs"]), pt(a, t - 0.35), z, 0.0,
                               rng.uniform(0.9, 1.4), r=0.25, feuille=self.choix("feuillages"), fleur=self.choix("fleurs"))
                elif rng.random() < 0.03:
                    self.poser("Lampadaire_Tordu", pt(a, 0.7), z, rng.uniform(0, 6.28), r=0.15)
                a += rng.uniform(2.0, 4.0)
            for _ in range(28):  # cachettes libres sur le trottoir
                self.slot_sol(*pt(rng.uniform(0.5, bloc - 0.5), rng.uniform(0.3, t - 0.3)))
            self.foule(s["foule"], lambda: pt(rng.uniform(0.5, bloc - 0.5), rng.uniform(0.3, t - 0.3)))
            a = 3.5
            while a < bloc - 4.5:  # stationnement le long de la bordure, côté chaussée
                if rng.random() < 0.5:
                    typ = self.choix("vehicules")
                    typ = "voiture" if typ.startswith("bus") else typ
                    a += self.vehicule(*pt(a, -1.3), le_long_de_x=cote in "SN", typ=typ) + 1.3
                else:
                    a += 5.5

    # ---- places centrales, une par ville ----------------------------------
    def _place(self, bx, by, bloc, sol):
        """Dalle de la place ; renvoie (cx, cy, z)."""
        m = 1.5
        self.box(sol, (bloc - 2 * m, bloc - 2 * m, 0.06), (bx + bloc / 2, by + bloc / 2, H_TROTTOIR + 0.03))
        self.herbes.append((bx + m, by + m, bx + bloc - m, by + bloc - m))
        return bx + bloc / 2, by + bloc / 2, H_TROTTOIR + 0.06

    def _animer_place(self, bx, by, bloc, cx, cy, z, arbres, gens, rayon_libre=7.5):
        rng = self.rng
        pose = 0
        for _ in range(arbres * 20):
            if pose == arbres:
                break
            x, y = rng.uniform(bx + 2.5, bx + bloc - 2.5), rng.uniform(by + 2.5, by + bloc - 2.5)
            if math.hypot(x - cx, y - cy) > rayon_libre and self.libre(x, y):
                self.arbre(x, y, z)
                pose += 1
        hasard = lambda marge: (rng.uniform(bx + marge, bx + bloc - marge), rng.uniform(by + marge, by + bloc - marge))  # noqa: E731
        for nom in rng.sample(self.s["saynetes_place"], min(self.s["nb_saynetes_place"], len(self.s["saynetes_place"]))):
            for _ in range(12):  # cherche un coin dégagé
                x0, y0 = hasard(4.0)
                if math.hypot(x0 - cx, y0 - cy) > rayon_libre - 2.5 and self.libre(x0, y0):
                    self.saynete(nom, lambda da, b=0.0, x0=x0, y0=y0: (x0 + da, y0 - b), 0.0, -math.pi / 2, z, None)
                    break
        for _ in range(7):
            self.poser(rng.choice(["Buisson", "Buisson", "Massif_Fleurs"]), hasard(2.0), z, rng.uniform(0, 6.28),
                       rng.uniform(0.8, 1.3), r=0.7, feuille=self.choix("feuillages"), fleur=self.choix("fleurs"))
        for _ in range(self.s["nb_betes"] * 4):
            self.poser(self.choix("betes"), hasard(1.0), z, rng.uniform(0, 6.28), rng.uniform(0.8, 1.2), r=0.15,
                       poil=self.choix("poils"))
        for _ in range(140):
            self.slot_sol(rng.uniform(bx + 0.5, bx + bloc - 0.5), rng.uniform(by + 0.5, by + bloc - 0.5))
        self.foule(gens, lambda: (rng.uniform(bx + 1, bx + bloc - 1), rng.uniform(by + 1, by + bloc - 1)))

    def _terrasse(self, x, y, z, n=6):
        """Terrasse de café : tables, chaises, clients attablés, parasols."""
        rng = self.rng
        chaise = self.choix("auvents")
        for i in range(n):
            tx, ty = x + (i % 3) * 3.0, y + (i // 3) * 3.2
            self.inst("Table_Cafe", tx, ty, z)
            self.emprise(tx, ty, 0.45)
            for dx in (-0.7, 0.7):
                rot = 0.0 if dx < 0 else math.pi  # face à la table
                self.inst("Chaise", tx + dx, ty, z, rot, toile=chaise)
                self.emprise(tx + dx, ty, 0.25)
                if rng.random() < 0.55:
                    self._personne("Perso_Assis", tx + dx, ty, z, rot)
            if i % 2 == 0:
                self.inst("Parasol", tx + 0.1, ty + 0.9, z, toile=self.toile()[0])
                self.emprise(tx + 0.1, ty + 0.9, 0.2)
            self.slot_derriere(tx, ty, 0.5, 0.75, n=2)

    def square_paris(self, bx, by, bloc):
        cx, cy, z = self._place(bx, by, bloc, "herbe")
        self.fontaine(cx, cy, z)
        for i in range(6):
            a = i * math.pi / 3 + 0.3
            self.banc(cx + 5.5 * math.cos(a), cy + 5.5 * math.sin(a), z, a + math.pi / 2)
        kx, ky = bx + 5.0, by + bloc - 5.0  # kiosque
        self.cyl("vertfonce", 1.2, 3.0, (kx, ky, z), emprise=True)
        self.cyl("vertfonce", 1.6, 0.9, (kx, ky, z + 3.0), r2=0.1)
        self.slot_derriere(kx, ky, 1.2, 3.5, n=5)
        self._terrasse(bx + bloc - 9.0, by + 4.0, z)
        for dx, dy, le_long_de_x in ((0, -9.5, True), (9.5, 0, False), (-6, -11.5, True), (11.5, 6, False)):
            self.haie(cx + dx, cy + dy, 5.0, le_long_de_x)
        self._animer_place(bx, by, bloc, cx, cy, z, 10, 45)

    def square_new_york(self, bx, by, bloc):
        cx, cy, z = self._place(bx, by, bloc, "herbe")
        self.fontaine(cx, cy - 2, z)
        self.arche(cx, by + bloc - 4.5, z, 8.0, 8.5, 2.2, "pierre")
        for i in range(6):
            a = i * math.pi / 3
            self.banc(cx + 5.5 * math.cos(a), cy - 2 + 5.5 * math.sin(a), z, a + math.pi / 2)
        for dx, dy in ((-8, -8), (8, -9), (9, 4)):  # chariots à hot-dogs
            x, y = cx + dx, cy + dy
            self.box("metal", (1.6, 0.9, 1.0), (x, y, z + 0.5), emprise=True)
            self.inst("Parasol", x + 0.6, y + 0.3, z, toile=self.toile()[0])
            self.slot_derriere(x, y, 0.8, 1.0)
        self.haie(cx - 9, cy + 3, 5.0, False)
        self.haie(cx + 3, cy - 10, 5.0, True)
        self._animer_place(bx, by, bloc, cx, cy, z, 12, 60)

    def square_lille(self, bx, by, bloc):
        cx, cy, z = self._place(bx, by, bloc, "paves")
        self.box("pierre", (2.4, 2.4, 1.2), (cx, cy, z + 0.6), emprise=True)  # colonne de la place
        self.cyl("pierre", 0.5, 8.0, (cx, cy, z + 1.2))
        self.sph("bronze", 0.7, (cx, cy, z + 9.8), (1, 1, 1.4))
        self.slot_derriere(cx, cy, 1.2, 1.2, n=4)
        tx, ty = bx + 5.5, by + bloc - 5.5  # beffroi, au fond pour ne rien masquer
        self.box("brique", (5.0, 5.0, 20.0), (tx, ty, z + 10.0), emprise=True)
        self.box("pierre", (5.4, 5.4, 0.6), (tx, ty, z + 20.3))
        self.box("brique", (3.6, 3.6, 9.0), (tx, ty, z + 25.1))
        self.box("blanc", (1.6, 0.1, 1.6), (tx, ty - 1.85, z + 26.5))  # horloge
        self.box("blanc", (0.1, 1.6, 1.6), (tx + 1.85, ty, z + 26.5))
        self.box("ardoise", (4.2, 4.2, 5.0), (tx, ty, z + 32.1), haut=(0.08, 0.08))
        for i in range(10):  # braderie : deux rangées d'étals
            self.etal(bx + 6.0 + (i % 5) * 4.2, by + 5.0 + (i // 5) * 5.0, z, True)
        for dx, dy in ((7, 8), (-8, 2)):  # tas de coquilles de moules
            self.cyl("ardoise", 0.9, 0.8, (cx + dx, cy + dy, z), r2=0.1, emprise=True)
            self.slot_derriere(cx + dx, cy + dy, 0.9, 0.8, n=2)
        self._terrasse(bx + bloc - 10.0, by + bloc - 9.0, z)
        self._animer_place(bx, by, bloc, cx, cy, z, 3, 90, rayon_libre=4.0)

    def square_delhi(self, bx, by, bloc):
        cx, cy, z = self._place(bx, by, bloc, "terre_battue")
        gy = by + bloc - 3.5  # porte monumentale en grès rouge, au fond
        self.arche(cx, gy, z, 9.0, 9.0, 2.4, "gres")
        for d in (-3.2, 0.0, 3.2):  # chhatris
            self.sph("blanc", 0.8 if d else 1.1, (cx + d, gy, z + 9.9), (1, 1, 0.9))
        self.arbre(bx + 4.5, by + 5.0, z, k=1.9)  # banyan
        for i in range(6):
            self.etal(bx + bloc - 4.0 - (i % 3) * 4.0, by + 4.0 + (i // 3) * 4.6, z, True)
        for dx, dy in ((-3, 0), (2, 3)):
            self.vache(cx + dx, cy + dy, z)
        self._animer_place(bx, by, bloc, cx, cy, z, 2, 70, rayon_libre=3.0)

    # ---- ensemble ---------------------------------------------------------
    def construire(self):
        t, s, rng = self.t, self.s, self.rng
        taille, n, rue = t["taille"], t["ilots"], t["rue"]
        bloc = (taille - n * rue) / n  # demi-rue en bordure de carte
        self.box("asphalte", (taille, taille, 0.2), (0, 0, -0.1))
        origines = [-self.demi + rue / 2 + i * (bloc + rue) for i in range(n)]
        for bx in origines:
            for by in origines:
                self.box("trottoir", (bloc, bloc, H_TROTTOIR), (bx + bloc / 2, by + bloc / 2, H_TROTTOIR / 2))
                self.blocs.append((bx, by, bx + bloc, by + bloc))
        for c in origines[1:]:  # rues intérieures : pointillés, passages piétons, circulation
            axe = c - rue / 2
            a = -self.demi + 2
            while a < self.demi - 2:
                self.box("marquage", (0.15, 1.6, 0.02), (axe, a, 0.01))
                self.box("marquage", (1.6, 0.15, 0.02), (a, axe, 0.01))
                a += 4.0
            for o in origines:  # zébras aux deux bouts de chaque îlot
                for bout in (o + 1.8, o + bloc - 1.8):
                    for k in range(int((rue - 1.5) / 1.3)):
                        d = axe - rue / 2 + 1.0 + k * 1.3
                        self.box("marquage", (0.6, 2.6, 0.02), (d, bout, 0.012))
                        self.box("marquage", (2.6, 0.6, 0.02), (bout, d, 0.012))
            for _ in range(s["trafic"]):
                voie = rng.choice((-1, 1)) * rue * 0.2
                o = rng.choice(origines)
                a = rng.uniform(o + 5, o + bloc - 5)
                if rng.random() < 0.5:
                    self.vehicule(axe + voie, a, False)
                else:
                    self.vehicule(a, axe + voie, True)
        square = getattr(self, "square_" + s["square"])
        for i, bx in enumerate(origines):
            for j, by in enumerate(origines):
                if [i, j] == t["square"]:
                    square(bx, by, bloc)
                else:
                    self.ilot_bati(bx, by, bloc, fond=(i == 0 or j == n - 1))
        self._sol_dense()
        return {"prims": self.prims, "insts": self.insts, "slots": self.slots, "lots": self.lots,
                "blocs": [list(b) for b in self.blocs], "cachettes_denses": self.denses}

    def _sol_dense(self):
        """Cachettes denses au sol, une fois tout posé : grille sur trottoirs et places (PAS_SOL),
        plus lâche sur la chaussée (un point sur RUE_UN_SUR dans chaque sens). Même test que
        libre() (immeubles, objets, bords de carte), accéléré colonne par colonne : seuls les
        rectangles qui coupent la colonne sont essayés."""
        grille = _grille(-self.demi, self.demi, PAS_SOL)
        for i, x in enumerate(grille):
            if abs(x) >= self.demi - 0.5:
                continue
            emprises = [r for r in self.emprises if r[0] - MARGE_SLOT < x < r[2] + MARGE_SLOT]
            lots = [r for r in self.lots if r[0] - 0.25 < x < r[2] + 0.25]
            for j, y in enumerate(grille):
                if (i % RUE_UN_SUR or j % RUE_UN_SUR) and not self._dans(x, y, self.blocs):
                    continue
                if abs(y) < self.demi - 0.5 and not self._dans(x, y, emprises, MARGE_SLOT)                         and not self._dans(x, y, lots, 0.25):
                    self.dense("sol", x, y, self.sol_z(x, y))


def make_layout(theme):
    valider_theme(theme)
    return Plan(theme).construire()
