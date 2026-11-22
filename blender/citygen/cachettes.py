"""Cachettes valables pour le mode « Cacher mes canards ». Python pur.

Entrée : les slots mesurés par place_objets.py ({lieu, pos, rot, vis, rot_canard}, repère
Blender) et les leurres placés. Sortie : la liste compacte de cachettes.json, en repère glTF,
et son empreinte. L'ordre des slots est conservé : le numéro d'une cachette est sa position
dans la liste, et c'est ce numéro que porte le lien de défi.
"""
import json
import zlib

CHIFFRES_36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def _dist(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def cachettes_valables(slots, leurres, theme):
    """Slots où un canard de défi reste trouvable : assez visible, tête visible, loin des leurres."""
    vis_min = theme["visibilite_canard"][0]
    dmin = theme["distance_min"]
    return [s for s in slots
            if s["vis"] >= vis_min
            and s.get("rot_canard") is not None
            and all(_dist(s["pos"], l["pos"]) >= dmin for l in leurres)]


def en_gltf(slot):
    """[x, y, z, rotation, visibilité, lieu] en repère glTF (Y vers le haut), comme placements.json."""
    x, y, z = slot["pos"]
    return [round(x, 3), round(z, 3), round(-y, 3), slot["rot_canard"], round(slot["vis"], 3), slot["lieu"]]


def empreinte(liste):
    """4 caractères base 36 tirés du CRC32 de la liste : changent dès qu'une cachette change."""
    n = zlib.crc32(json.dumps(liste, separators=(",", ":")).encode("utf8")) % 36 ** 4
    out = ""
    for _ in range(4):
        n, r = divmod(n, 36)
        out = CHIFFRES_36[r] + out
    return out
