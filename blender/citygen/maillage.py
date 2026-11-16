"""Primitives -> sommets et faces, en Python pur (pas de bpy).

Remplace bmesh pour le décor : bmesh ralentit à mesure que le maillage grossit (plus de
7 minutes pour Paris), alors qu'ici le coût est linéaire. Les faces sont orientées vers
l'extérieur (vérifié par un test de volume signé) : pas besoin de recalculer les normales.
"""
import math


def _box(p):
    sx, sy, sz = p["size"]
    fx, fy = p.get("haut", (1.0, 1.0))
    c, s = math.cos(p.get("rot", 0.0)), math.sin(p.get("rot", 0.0))
    verts = []
    for z, kx, ky in ((-0.5, 1.0, 1.0), (0.5, fx, fy)):
        for x, y in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
            lx, ly = x * sx * kx, y * sy * ky
            verts.append((lx * c - ly * s, lx * s + ly * c, z * sz))
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return verts, faces, False


def _cyl(p):
    n, r1, r2, h = p.get("seg", 8), p["r1"], p["r2"], p["h"]
    anneau = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    verts = [(x * r1, y * r1, -h / 2) for x, y in anneau]
    faces = [tuple(range(n - 1, -1, -1))]  # dessous
    if r2 < 1e-6:  # cône : un seul sommet en haut
        verts.append((0.0, 0.0, h / 2))
        faces += [(i, (i + 1) % n, n) for i in range(n)]
    else:
        verts += [(x * r2, y * r2, h / 2) for x, y in anneau]
        faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        faces.append(tuple(range(n, 2 * n)))  # dessus
    return verts, faces, False


def _sph(p, u=8, v=5):
    r = p["r"]
    sx, sy, sz = p.get("scale", (1.0, 1.0, 1.0))
    verts = [(0.0, 0.0, r * sz)]
    for j in range(1, v):
        t = math.pi * j / v
        for i in range(u):
            a = 2 * math.pi * i / u
            verts.append((r * math.sin(t) * math.cos(a) * sx, r * math.sin(t) * math.sin(a) * sy, r * math.cos(t) * sz))
    verts.append((0.0, 0.0, -r * sz))
    bas = len(verts) - 1
    k = lambda j, i: 1 + (j - 1) * u + i % u  # noqa: E731  sommet i de l'anneau j
    faces = [(0, k(1, i), k(1, i + 1)) for i in range(u)]
    for j in range(1, v - 1):
        faces += [(k(j, i), k(j + 1, i), k(j + 1, i + 1), k(j, i + 1)) for i in range(u)]
    faces += [(bas, k(v - 1, i + 1), k(v - 1, i)) for i in range(u)]
    return verts, faces, True


FORMES = {"box": _box, "cyl": _cyl, "sph": _sph}


def primitive(p):
    """(sommets dans le repère du monde, faces, lissé) pour une primitive du plan."""
    verts, faces, lisse = FORMES[p["t"]](p)
    x, y, z = p["pos"]
    return [(a + x, b + y, c + z) for a, b, c in verts], faces, lisse


def assembler(prims):
    """Fusionne des primitives : sommets, faces, matériau et lissage par face, matériaux."""
    sommets, faces, mats, lisses, noms = [], [], [], [], []
    for p in prims:
        v, f, lisse = primitive(p)
        base = len(sommets)
        sommets += v
        faces += [tuple(i + base for i in face) for face in f]
        if p["mat"] not in noms:
            noms.append(p["mat"])
        mats += [noms.index(p["mat"])] * len(f)
        lisses += [lisse] * len(f)
    return {"sommets": sommets, "faces": faces, "mats": mats, "lisses": lisses, "noms": noms}


def volume(verts, faces):
    """Volume signé : positif si les faces regardent vers l'extérieur."""
    total = 0.0
    for f in faces:
        a = verts[f[0]]
        for i in range(1, len(f) - 1):
            b, c = verts[f[i]], verts[f[i + 1]]
            total += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                      + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return total / 6.0
