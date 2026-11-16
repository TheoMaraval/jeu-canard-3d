"""Choix des 30 canards et des leurres parmi les cachettes candidates. Python pur.

Entrée : slots {lieu, pos, rot, vis} où vis (0–1) est la part visible depuis la caméra.
Sortie : objets {id, type, pos, rot, visibilite, lieu, zone} en repère Blender ;
la conversion glTF est faite par place_objets.py.
"""
import random

CANARD = "Canard"


class PlacementImpossible(Exception):
    pass


def cellule(pos, theme):
    """Case de la grille de répartition : "A1" (coin -x, -y) … "F5"."""
    cols, rangs = theme["grille"]
    taille = theme["taille"]
    c = min(cols - 1, max(0, int((pos[0] + taille / 2) / (taille / cols))))
    r = min(rangs - 1, max(0, int((pos[1] + taille / 2) / (taille / rangs))))
    return "ABCDEFGHIJ"[c] + str(r + 1)


def _dist(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def _objet(ident, type_, slot, zone):
    return {"id": ident, "type": type_, "pos": list(slot["pos"]), "rot": slot["rot"],
            "visibilite": round(slot["vis"], 3), "lieu": slot["lieu"], "zone": zone}


def choisir(slots, theme):
    rng = random.Random(theme["graine"] + 1)
    cols, rangs = theme["grille"]
    zones = ["ABCDEFGHIJ"[c] + str(r + 1) for c in range(cols) for r in range(rangs)]
    par_zone = {z: [] for z in zones}
    for s in slots:
        par_zone[cellule(s["pos"], theme)].append(s)
    for liste in par_zone.values():
        rng.shuffle(liste)

    # 1. un canard par case
    lo, hi = theme["visibilite_canard"]
    dmin, dcan = theme["distance_min"], theme["distance_min_canards"]
    canards = []
    lieux = sorted(theme["leurres_par_lieu"])
    for i, z in enumerate(zones):
        # lieu préféré à tour de rôle : sinon les balcons, plus nombreux, auraient tous les canards
        prefere = lieux[i % len(lieux)]
        candidats = sorted(par_zone[z], key=lambda s: s["lieu"] != prefere)  # tri stable
        choix = next((s for s in candidats if lo <= s["vis"] <= hi
                      and all(_dist(s["pos"], c["pos"]) >= dcan for c in canards)), None)
        if choix is None:
            raise PlacementImpossible(
                f"case {z} : aucune cachette de visibilité {lo}–{hi} à plus de {dcan} m des autres canards")
        canards.append(_objet(f"canard-{len(canards) + 1:02d}", CANARD, choix, z))
    if len(canards) != theme["canards"]:
        raise PlacementImpossible(f"la grille {cols}x{rangs} ne donne pas {theme['canards']} canards")

    # 2. leurres, répartis case par case à tour de rôle
    lo, hi = theme["visibilite_leurre"]
    types = theme["leurres_par_lieu"]
    tous_types = sorted({t for ts in types.values() for t in ts})
    places, leurres = list(canards), []
    curseur = {z: 0 for z in zones}
    ordre = list(zones)
    while len(leurres) < theme["leurres"]:
        rng.shuffle(ordre)
        avance = False
        for z in ordre:
            if len(leurres) == theme["leurres"]:
                break
            liste = par_zone[z]
            while curseur[z] < len(liste):
                s = liste[curseur[z]]
                curseur[z] += 1
                if lo <= s["vis"] <= hi and all(_dist(s["pos"], p["pos"]) >= dmin for p in places):
                    # les premiers leurres épuisent la liste des types : tous servent au moins une fois
                    manquants = [t for t in tous_types[len(leurres):] if t in types[s["lieu"]]][:1] \
                        if len(leurres) < len(tous_types) else []
                    type_ = manquants[0] if manquants else rng.choice(types[s["lieu"]])
                    o = _objet(f"leurre-{len(leurres) + 1:03d}", type_, s, z)
                    leurres.append(o)
                    places.append(o)
                    avance = True
                    break
        if not avance:
            raise PlacementImpossible(f"seulement {len(leurres)} leurres placés sur {theme['leurres']}")
    objets = canards + leurres
    valider(objets, theme)
    return objets


def valider(objets, theme):
    """Vérifie les règles du jeu sur un placement. Lève AssertionError sinon."""
    canards = [o for o in objets if o["type"] == CANARD]
    leurres = [o for o in objets if o["type"] != CANARD]
    assert len(canards) == theme["canards"], f"{len(canards)} canards"
    assert len(leurres) == theme["leurres"], f"{len(leurres)} leurres"
    assert len({o["id"] for o in objets}) == len(objets), "identifiants en double"
    assert len({o["zone"] for o in canards}) == len(canards), "deux canards dans la même case"
    for o in objets:
        lo, hi = theme["visibilite_canard" if o["type"] == CANARD else "visibilite_leurre"]
        assert lo <= o["visibilite"] <= hi, f"{o['id']} visibilité {o['visibilite']}"
        assert o["zone"] == cellule(o["pos"], theme), f"{o['id']} zone incohérente"
        if o["type"] != CANARD:
            assert o["type"] in theme["leurres_par_lieu"][o["lieu"]], f"{o['id']} type/lieu"
    for i, a in enumerate(objets):
        for b in objets[i + 1:]:
            d = _dist(a["pos"], b["pos"])
            assert d >= theme["distance_min"] - 1e-9, f"{a['id']} et {b['id']} à {d:.2f} m"
            if a["type"] == CANARD and b["type"] == CANARD:
                assert d >= theme["distance_min_canards"] - 1e-9, f"canards {a['id']}/{b['id']} à {d:.2f} m"
