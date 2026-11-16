"""Requerimiento 2 - Caminos minimos: experimentos, grafica, cociente, matriz y verificacion.

Entradas : data/processed/{nodes,edges,lugares_nodos,lugares_idx}.csv   (salida de r1_preparar.py)
Salidas  : results/r2_mediciones.csv, results/r2_cociente.csv, results/matriz_tiempos.csv,
           results/figuras/r2_tiempo_vs_nodos.png, results/r2_verificacion.txt

Uso: python python/r2_experimentos.py [--limite 300] [--max-cercanos 25000]
"""
import argparse
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from common import FIG, PROC, RES, SEMILLA, cargar_lugares, correr, crear_carpetas, exe, guardar_maquina

N_PQ = 20       # pares para la version con cola de prioridad (minimo del enunciado)
N_LINEAL = 10   # de esos, los que tambien se miden con la version lineal


def elegir_pares(lugares, max_cercanos_m):
    """20 pares: 10 'cercanos' (distancia en linea recta menor a max_cercanos_m; se miden con ambas
    versiones) y 10 al azar entre todos los lugares (solo cola de prioridad)."""
    rng = random.Random(SEMILLA)
    ids = lugares["id"].tolist()
    nodo = dict(zip(lugares["id"], lugares["nodo"]))
    nodos = pd.read_csv(PROC / "nodes.csv").set_index("idx")
    xy = {i: (nodos.loc[nodo[i], "x"], nodos.loc[nodo[i], "y"]) for i in ids}
    candidatos = []
    for a in ids:
        for b in ids:
            if a != b and nodo[a] != nodo[b]:
                d = np.hypot(xy[a][0] - xy[b][0], xy[a][1] - xy[b][1])
                if d <= max_cercanos_m:
                    candidatos.append((a, b))
    rng.shuffle(candidatos)
    cercanos = candidatos[:N_LINEAL]
    usados = set(cercanos)
    resto = [(a, b) for a in ids for b in ids if a != b and nodo[a] != nodo[b] and (a, b) not in usados]
    rng.shuffle(resto)
    lejanos = resto[: N_PQ - len(cercanos)]
    filas = [(a, b, nodo[a], nodo[b], 1) for a, b in cercanos] + [(a, b, nodo[a], nodo[b], 0) for a, b in lejanos]
    return pd.DataFrame(filas, columns=["origen", "destino", "nodo_origen", "nodo_destino", "lineal"])


def verificar_con_networkx(pares, mediciones):
    """Comprobacion cruzada (NetworkX solo se usa para verificar, como permite el enunciado)."""
    aristas = pd.read_csv(PROC / "edges.csv")
    G = nx.DiGraph()
    # con aristas paralelas se conserva la de menor tiempo, igual que haria Dijkstra
    for u, v, t in zip(aristas["u"], aristas["v"], aristas["time_s"]):
        if not G.has_edge(u, v) or t < G[u][v]["w"]:
            G.add_edge(u, v, w=t)
    lineas, maxdif = [], 0.0
    pq = mediciones[mediciones["version"] == "cola_prioridad"].set_index(["origen", "destino"])
    for _, p in pares.head(10).iterrows():
        ref = nx.dijkstra_path_length(G, int(p["nodo_origen"]), int(p["nodo_destino"]), weight="w")
        mio = float(pq.loc[(p["origen"], p["destino"]), "tiempo_viaje_s"])
        maxdif = max(maxdif, abs(ref - mio))
        lineas.append(f'{p["origen"]}->{p["destino"]}: propio={mio:.3f}  networkx={ref:.3f}')
    lineas.append(f"Diferencia maxima contra NetworkX en 10 pares: {maxdif:.6f} s")
    return lineas, maxdif


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=float, default=300, help="limite de tiempo por ejecucion (s)")
    ap.add_argument("--max-cercanos", type=float, default=25000, help="distancia maxima (m) de los pares cercanos")
    a = ap.parse_args()
    crear_carpetas()
    guardar_maquina()
    lugares = cargar_lugares()

    pares = elegir_pares(lugares, a.max_cercanos)
    pares.to_csv(RES / "r2_pares.csv", index=False)

    # --- mediciones (Java) ---
    salida = RES / "r2_mediciones.csv"
    correr([exe("dijkstra"), "bench", PROC, RES / "r2_pares.csv", salida, a.limite])
    med = pd.read_csv(salida)
    print(med.to_string(index=False))

    # --- grafica: nodos explorados (x) frente a tiempo (y), una marca distinta por version ---
    ok = med[med["estado"] == "ok"]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for ver, marca, color in (("lineal", "s", "tab:red"), ("cola_prioridad", "o", "tab:blue")):
        d = ok[ok["version"] == ver]
        ax.scatter(d["nodos_explorados"], d["tiempo_ms"], marker=marca, c=color, label=ver.replace("_", " "), alpha=.8)
    ax.set_yscale("log"); ax.set_xscale("log")
    ax.set_xlabel("Nodos explorados"); ax.set_ylabel("Tiempo (ms, escala log)")
    ax.legend(); ax.grid(alpha=.3, which="both")
    ax.set_title("Dijkstra: tiempo frente a nodos explorados")
    fig.tight_layout(); fig.savefig(FIG / "r2_tiempo_vs_nodos.png", dpi=160)

    # --- cociente lineal / cola de prioridad en los pares medidos con ambas ---
    ancho = ok.pivot_table(index=["origen", "destino"], columns="version", values="tiempo_ms").dropna()
    cociente = (ancho["lineal"] / ancho["cola_prioridad"])
    pd.DataFrame([{"pares": len(cociente), "mediana": cociente.median(), "minimo": cociente.min(),
                   "maximo": cociente.max()}]).round(2).to_csv(RES / "r2_cociente.csv", index=False)
    print("Cociente lineal/cola:", cociente.describe()[["min", "50%", "max"]].round(2).to_dict())

    # --- verificacion: ambas versiones y NetworkX ---
    tiempos = ok.pivot_table(index=["origen", "destino"], columns="version", values="tiempo_viaje_s").dropna()
    maxdif_versiones = float((tiempos["lineal"] - tiempos["cola_prioridad"]).abs().max())
    lineas, maxdif_nx = verificar_con_networkx(pares, med)
    lineas.insert(0, f"Diferencia maxima entre version lineal y cola de prioridad ({len(tiempos)} pares): {maxdif_versiones:.6f} s")
    (RES / "r2_verificacion.txt").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))
    assert maxdif_versiones < 1e-6 and maxdif_nx < 1e-3, "Las implementaciones no coinciden"

    # --- matriz de tiempos entre todos los lugares (una ejecucion completa por lugar) ---
    correr([exe("dijkstra"), "matrix", PROC, PROC / "lugares_idx.csv", RES / "matriz_tiempos.csv"])
    m = pd.read_csv(RES / "matriz_tiempos.csv", index_col=0)
    asim = np.abs(m.values - m.values.T).max()
    print(f"Matriz {m.shape[0]}x{m.shape[1]} guardada. Asimetria maxima |t(i,j)-t(j,i)| = {asim:.1f} s")


if __name__ == "__main__":
    main()
