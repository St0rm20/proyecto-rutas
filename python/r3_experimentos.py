"""Requerimiento 3 - Envolvente convexa: implementacion propia (Java) frente a scipy.spatial.ConvexHull.

Conjuntos de puntos: nodos de la componente (UTM 18N redondeados a entero y sin repetidos) y puntos al
azar dentro de un cuadrado (1 000, 10 000 y 50 000, semilla fija).
Salidas: results/r3_tiempos.csv, results/envolvente.geojson, results/figuras/r3_envolvente.png

Uso: python python/r3_experimentos.py
"""
import json
import statistics
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

from common import FIG, PROC, RES, SEMILLA, a_geo, cargar_nodos, correr, crear_carpetas, exe, guardar_maquina

LADO = 100_000  # lado del cuadrado de los puntos aleatorios (m)


def preparar(x, y):
    """Redondea al entero mas cercano y elimina repetidos."""
    p = np.unique(np.column_stack([np.rint(x), np.rint(y)]).astype(np.int64), axis=0)
    return p


def cruz(o, a, b):
    return (int(a[0]) - int(o[0])) * (int(b[1]) - int(o[1])) - (int(a[1]) - int(o[1])) * (int(b[0]) - int(o[0]))


def sin_colineales(poligono):
    """Quita, con aritmetica entera exacta, los vertices alineados sobre un lado del poligono."""
    pts = [tuple(map(int, p)) for p in poligono]
    cambio = True
    while cambio and len(pts) > 2:
        cambio = False
        for i in range(len(pts)):
            if cruz(pts[i - 1], pts[i], pts[(i + 1) % len(pts)]) == 0:
                pts.pop(i)
                cambio = True
                break
    return pts


def hull_scipy(p):
    h = ConvexHull(p.astype(np.float64))
    return sin_colineales(p[h.vertices])


def tiempo_scipy(p, reps=5):
    t = []
    for _ in range(reps):
        t0 = time.perf_counter()
        ConvexHull(p.astype(np.float64))
        t.append((time.perf_counter() - t0) * 1000)
    return statistics.median(t)


def hull_propio(p, nombre):
    archivo = RES / f"_puntos_{nombre}.csv"
    salida = RES / f"_hull_{nombre}.csv"
    pd.DataFrame(p, columns=["x", "y"]).to_csv(archivo, index=False)
    out, _ = correr([exe("hull"), archivo, salida, 5])
    n, h, ms = out.strip().split(",")
    v = pd.read_csv(salida)[["x", "y"]].values
    archivo.unlink(); salida.unlink()
    return int(n), int(h), float(ms), [tuple(map(int, r)) for r in v]


def mismo_conjunto(a, b):
    return set(a) == set(b)


def main():
    crear_carpetas()
    guardar_maquina()
    nodos = cargar_nodos()
    conjuntos = [("Nodos de la red", preparar(nodos["x"].values, nodos["y"].values))]
    rng = np.random.default_rng(SEMILLA)
    for n in (1000, 10000, 50000):
        pts = rng.integers(0, LADO + 1, size=(n, 2))
        etiqueta = f"{n:,}".replace(",", " ")
        conjuntos.append((f"Cuadrado, {etiqueta} puntos", np.unique(pts, axis=0)))

    filas = []
    hull_red = None
    for nombre, p in conjuntos:
        n, h, ms_propio, v_propio = hull_propio(p, "tmp")
        v_scipy = hull_scipy(p)
        ms_scipy = tiempo_scipy(p)
        igual = mismo_conjunto(v_propio, v_scipy)
        assert igual, f"Los vertices no coinciden en '{nombre}'"
        filas.append({"conjunto": nombre, "n": n, "vertices_envolvente": h, "tiempo_propio_ms": round(ms_propio, 3),
                      "tiempo_scipy_ms": round(ms_scipy, 3), "cociente": round(ms_propio / ms_scipy, 2),
                      "mismos_vertices": igual})
        print(filas[-1])
        if hull_red is None:
            hull_red = v_propio
    pd.DataFrame(filas).to_csv(RES / "r3_tiempos.csv", index=False)

    # envolvente de la red: GeoJSON para la aplicacion y figura para el informe
    xs = np.array([v[0] for v in hull_red]); ys = np.array([v[1] for v in hull_red])
    lat, lon = a_geo(xs, ys)
    anillo = [[float(a), float(b)] for a, b in zip(lon, lat)] + [[float(lon[0]), float(lat[0])]]
    geo = {"type": "Feature", "properties": {"vertices": len(hull_red)}, "geometry": {"type": "Polygon", "coordinates": [anillo]}}
    (RES / "envolvente.geojson").write_text(json.dumps(geo), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(5.5, 6))
    ax.scatter(nodos["lon"], nodos["lat"], s=0.3, c="gray", alpha=.5, label="nodos")
    ax.plot([c[0] for c in anillo], [c[1] for c in anillo], "r-", lw=1.5, label=f"envolvente ({len(hull_red)} vertices)")
    ax.set_xlabel("Longitud"); ax.set_ylabel("Latitud"); ax.legend(markerscale=10)
    ax.set_title("Envolvente convexa de la red vial"); ax.set_aspect("equal")
    fig.tight_layout(); fig.savefig(FIG / "r3_envolvente.png", dpi=160)
    print("Guardado results/r3_tiempos.csv, results/envolvente.geojson y la figura")


if __name__ == "__main__":
    main()
