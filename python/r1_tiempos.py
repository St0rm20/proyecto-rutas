"""Requerimiento 1, punto 3 - Tiempo de ox.truncate.largest_component en redes de tamano creciente.

Redes: graph_from_point alrededor de la plaza de Bolivar (Armenia) con radios de 2, 5, 10 y 20 km y la
red completa del departamento. Cada medicion se repite 5 veces y se reporta la mediana (si la primera
ejecucion pasa de 60 s se mide una sola vez). Solo se mide la funcion: la descarga queda por fuera.

Uso: python python/r1_tiempos.py
"""
import inspect
import statistics
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd

from common import FIG, RAW, RES, crear_carpetas, guardar_maquina

PLAZA_BOLIVAR = (4.5339, -75.6811)
RADIOS_KM = [2, 5, 10, 20]


def medir(G, reps=5):
    tiempos = []
    for r in range(reps):
        t0 = time.perf_counter()
        ox.truncate.largest_component(G, strongly=True)
        ms = (time.perf_counter() - t0) * 1000
        tiempos.append(ms)
        if r == 0 and ms > 60000:
            break
    return statistics.median(tiempos)


def red_radio(km):
    ruta = RAW / f"radio_{km}km.graphml"
    if ruta.exists():
        return ox.load_graphml(ruta)
    print(f"Descargando radio de {km} km...")
    G = ox.graph_from_point(PLAZA_BOLIVAR, dist=km * 1000, network_type="drive")
    ox.save_graphml(G, ruta)
    return G


def documentar_algoritmo():
    """Guarda el codigo fuente y la documentacion de la version instalada (evidencia para el informe)."""
    texto = [f"osmnx {ox.__version__} / networkx {nx.__version__}\n", "=== osmnx.truncate.largest_component ===\n",
             inspect.getsource(ox.truncate.largest_component), "\n=== networkx.strongly_connected_components (docstring) ===\n",
             nx.strongly_connected_components.__doc__ or ""]
    (RES / "r1_algoritmo.txt").write_text("".join(texto), encoding="utf-8")


def main():
    crear_carpetas()
    guardar_maquina()
    documentar_algoritmo()
    redes = []
    for km in RADIOS_KM:
        redes.append((f"Radio de {km} km", red_radio(km)))
    completa = RAW / "quindio.graphml"
    if not completa.exists():
        raise SystemExit("Falta data/raw/quindio.graphml: ejecute antes python python/r1_preparar.py")
    redes.append(("Departamento completo", ox.load_graphml(completa)))

    filas = []
    for nombre, G in redes:
        V, E = G.number_of_nodes(), G.number_of_edges()
        ms = medir(G)
        filas.append({"red": nombre, "V": V, "E": E, "V+E": V + E, "tiempo_ms": round(ms, 3),
                      "us_por_elemento": round(ms * 1000 / (V + E), 4)})
        print(filas[-1])
    df = pd.DataFrame(filas)
    df.to_csv(RES / "r1_tiempos.csv", index=False)

    # grafica: tiempo frente a V+E, con una recta de referencia O(V+E) ajustada al ultimo punto
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["V+E"], df["tiempo_ms"], "o-", label="medido")
    k = df["tiempo_ms"].iloc[-1] / df["V+E"].iloc[-1]
    ax.plot(df["V+E"], k * df["V+E"], "--", label="recta de referencia O(V+E)")
    ax.set_xlabel("V + E"); ax.set_ylabel("Tiempo (ms)")
    ax.set_title("largest_component (fuertemente conexa)")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(FIG / "r1_tiempos.png", dpi=160)
    print("Guardado results/r1_tiempos.csv y results/figuras/r1_tiempos.png")


if __name__ == "__main__":
    main()
