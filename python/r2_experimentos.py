"""Requerimiento 2 - Caminos minimos: experimentos, grafica, cociente, matriz y verificacion.

Entradas : data/processed/{nodes,edges,lugares_nodos,lugares_idx}.csv   (salida de r1_preparar.py)
Salidas  : results/r2/r2_pares.csv, results/r2/r2_mediciones.csv, results/r2/r2_cociente.csv,
           results/r2/matriz_tiempos.csv, results/r2/r2_verificacion.txt,
           results/figuras/r2_tiempo_vs_nodos.png

Los 10 pares de la version lineal se eligen entre lugares del mismo municipio o de municipios vecinos
(ver VECINOS); los otros 10 pares se eligen al azar entre todos los lugares.

Uso: python python/r2_experimentos.py [--limite 300]
"""
import argparse
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from common import FIG, PROC, RES_R2, SEMILLA, cargar_lugares, correr, crear_carpetas, exe, guardar_maquina

N_PQ = 20       # pares para la version con cola de prioridad (minimo del enunciado)
N_LINEAL = 10   # de esos, los que tambien se miden con la version lineal


# Limites municipales dentro del Quindio (solo municipios del departamento).
VECINOS = {
    "Armenia":    {"Circasia", "Salento", "Calarca", "La Tebaida", "Montenegro"},
    "Buenavista": {"Cordoba", "Pijao", "Calarca"},
    "Calarca":    {"Armenia", "Salento", "Cordoba", "La Tebaida", "Buenavista"},
    "Circasia":   {"Filandia", "Salento", "Armenia", "Montenegro", "Quimbaya"},
    "Cordoba":    {"Calarca", "Buenavista", "Pijao"},
    "Filandia":   {"Circasia", "Salento", "Quimbaya"},
    "Genova":     {"Pijao"},
    "La Tebaida": {"Armenia", "Montenegro", "Calarca"},
    "Montenegro": {"Quimbaya", "Circasia", "Armenia", "La Tebaida"},
    "Pijao":      {"Cordoba", "Buenavista", "Genova"},
    "Quimbaya":   {"Filandia", "Circasia", "Montenegro"},
    "Salento":    {"Filandia", "Circasia", "Armenia", "Calarca"},
}
assert all(a in VECINOS[b] for a in VECINOS for b in VECINOS[a]), "VECINOS no es simetrico"


def son_cercanos(mun_a, mun_b):
    """True si ambos lugares estan en el mismo municipio o en municipios vecinos."""
    return mun_a == mun_b or mun_b in VECINOS[mun_a]


def elegir_pares(lugares):
    """20 pares: 10 'cercanos' (mismo municipio o municipios vecinos; se miden con ambas versiones) y
    10 al azar entre todos los lugares (solo cola de prioridad). Los pares tienen nodos distintos."""
    desconocidos = set(lugares["municipio"]) - set(VECINOS)
    assert not desconocidos, f"Municipio sin entrada en VECINOS: {sorted(desconocidos)}"
    rng = random.Random(SEMILLA)
    ids = lugares["id"].tolist()
    nodo = dict(zip(lugares["id"], lugares["nodo"]))
    mun = dict(zip(lugares["id"], lugares["municipio"]))
    candidatos = [(a, b) for a in ids for b in ids
                  if a != b and nodo[a] != nodo[b] and son_cercanos(mun[a], mun[b])]
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
    a = ap.parse_args()
    crear_carpetas()
    guardar_maquina()
    lugares = cargar_lugares()

    pares = elegir_pares(lugares)
    pares.to_csv(RES_R2 / "r2_pares.csv", index=False)

    # --- mediciones (Java) ---
    salida = RES_R2 / "r2_mediciones.csv"
    correr([exe("dijkstra"), "bench", PROC, RES_R2 / "r2_pares.csv", salida, a.limite])
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
                   "maximo": cociente.max()}]).round(2).to_csv(RES_R2 / "r2_cociente.csv", index=False)
    print("Cociente lineal/cola:", cociente.describe()[["min", "50%", "max"]].round(2).to_dict())

    # --- verificacion: ambas versiones y NetworkX ---
    tiempos = ok.pivot_table(index=["origen", "destino"], columns="version", values="tiempo_viaje_s").dropna()
    maxdif_versiones = float((tiempos["lineal"] - tiempos["cola_prioridad"]).abs().max())
    lineas, maxdif_nx = verificar_con_networkx(pares, med)
    lineas.insert(0, f"Diferencia maxima entre version lineal y cola de prioridad ({len(tiempos)} pares): {maxdif_versiones:.6f} s")
    (RES_R2 / "r2_verificacion.txt").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))
    assert maxdif_versiones < 1e-6 and maxdif_nx < 1e-3, "Las implementaciones no coinciden"

    # --- matriz de tiempos entre todos los lugares (una ejecucion completa por lugar) ---
    correr([exe("dijkstra"), "matrix", PROC, PROC / "lugares_idx.csv", RES_R2 / "matriz_tiempos.csv"])
    m = pd.read_csv(RES_R2 / "matriz_tiempos.csv", index_col=0)
    asim = np.abs(m.values - m.values.T).max()
    print(f"Matriz {m.shape[0]}x{m.shape[1]} guardada. Asimetria maxima |t(i,j)-t(j,i)| = {asim:.1f} s")


if __name__ == "__main__":
    main()
