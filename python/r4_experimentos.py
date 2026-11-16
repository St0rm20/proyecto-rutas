"""Requerimiento 4 - Ruta optima de recorrido: fuerza bruta, Held-Karp y heuristica del vecino mas cercano.

Salidas:
  results/r4_exactas.csv        k, tiempo fuerza bruta (ms), tiempo Held-Karp (ms), memoria HK (MiB)
  results/r4_hk_extra.csv       Held-Karp para k mayores (solo informativo)
  results/r4_calidad.csv        k, instancias, brecha promedio y maxima (%)
  results/r4_calidad_detalle.csv
  results/r4_ejemplo_voraz.txt  instancia con la mayor brecha (para el punto 5)
  results/figuras/r4_tiempo_vs_k.png

Uso: python python/r4_experimentos.py [--limite 300] [--hk-hasta 18]
"""
import argparse
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIG, RES, SEMILLA, cargar_matriz, crear_carpetas, guardar_maquina
from viajante import costo_orden, resolver


def memoria_hk_mib(k):
    # tabla dp: 2^k * k valores float64 (8 B) + tabla de padres: 2^k * k valores int8 (1 B)
    return (2 ** k) * k * 9 / 2 ** 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=float, default=300)
    ap.add_argument("--hk-hasta", type=int, default=18, help="k maximo de la serie extra solo con Held-Karp (0 = omitir)")
    a = ap.parse_args()
    crear_carpetas()
    guardar_maquina()
    m = cargar_matriz()
    ids = list(m.index)
    inicio = ids.index("M01")                       # Armenia (plaza de Bolivar)
    otros = [i for i in range(len(ids)) if i != inicio]

    # ---------- 1) soluciones exactas, k = 5..12 (instancias anidadas, semilla fija) ----------
    rng = random.Random(SEMILLA)
    base = rng.sample(otros, len(otros))
    inst = [(f"k{k}", inicio, base[:k]) for k in range(5, 13)]
    df = resolver(inst, ("brute", "hk"), limite_s=a.limite)
    filas = []
    for k in range(5, 13):
        b = df[(df.inst == f"k{k}") & (df.algoritmo == "brute")].iloc[0]
        h = df[(df.inst == f"k{k}") & (df.algoritmo == "hk")].iloc[0]
        if b.estado == "ok" and h.estado == "ok":      # verificacion: mismo optimo
            assert abs(b.costo_s - h.costo_s) < 1e-3, f"k={k}: fuerza bruta y Held-Karp difieren"
        if h.estado == "ok":                           # verificacion: el orden devuelto suma el costo informado
            assert abs(costo_orden(m, h.orden) - h.costo_s) < 1e-2, f"k={k}: el orden de Held-Karp no suma su costo"
            assert sorted(h.orden[1:-1]) == sorted(base[:k]), f"k={k}: el recorrido no visita todos los lugares"
        filas.append({"k": k, "tiempo_fuerza_bruta_ms": b.tiempo_ms if b.estado == "ok" else "no completada",
                      "tiempo_held_karp_ms": h.tiempo_ms if h.estado == "ok" else "no completada",
                      "costo_optimo_s": h.costo_s if h.estado == "ok" else None,
                      "memoria_hk_mib": round(memoria_hk_mib(k), 3)})
    ex = pd.DataFrame(filas)
    ex.to_csv(RES / "r4_exactas.csv", index=False)
    print(ex.to_string(index=False))
    for nombre, col in (("fuerza bruta", "tiempo_fuerza_bruta_ms"), ("Held-Karp", "tiempo_held_karp_ms")):
        resueltos = [r["k"] for _, r in ex.iterrows() if r[col] != "no completada"]
        print(f"Mayor k resuelto con {nombre}: {int(max(resueltos)) if resueltos else 'ninguno'}")

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for nombre, col, marca in (("Fuerza bruta", "tiempo_fuerza_bruta_ms", "s-"), ("Held-Karp", "tiempo_held_karp_ms", "o-")):
        d = ex[ex[col] != "no completada"]
        ax.plot(d["k"], d[col].astype(float), marca, label=nombre)
    ax.set_yscale("log"); ax.set_xlabel("k (lugares a visitar, sin contar la partida)"); ax.set_ylabel("Tiempo (ms, escala log)")
    ax.set_title("Viajante asimetrico: tiempo frente a k"); ax.grid(alpha=.3, which="both"); ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "r4_tiempo_vs_k.png", dpi=160)

    # ---------- serie extra: solo Held-Karp ----------
    if a.hk_hasta > 12:
        inst2 = [(f"k{k}", inicio, rng.sample(otros, min(k, len(otros)))) for k in range(13, min(a.hk_hasta, len(otros)) + 1)]
        d2 = resolver(inst2, ("hk",), limite_s=a.limite)
        d2["memoria_hk_mib"] = d2["k"].apply(lambda k: round(memoria_hk_mib(k), 1))
        d2[["k", "tiempo_ms", "costo_s", "estado", "memoria_hk_mib"]].to_csv(RES / "r4_hk_extra.csv", index=False)
        print(d2[["k", "tiempo_ms", "estado", "memoria_hk_mib"]].to_string(index=False))

    # ---------- 3) calidad de la heuristica ----------
    detalle = []
    insts = []
    for k in (5, 8, 10, 12):
        for r in range(5):
            insts.append((f"q{k}_{r}", inicio, random.Random(SEMILLA + 100 * k + r).sample(otros, k)))
    q = resolver(insts, ("hk", "greedy"), limite_s=a.limite)
    for nombre in q["inst"].unique():
        hk = q[(q.inst == nombre) & (q.algoritmo == "hk")].iloc[0]
        gr = q[(q.inst == nombre) & (q.algoritmo == "greedy")].iloc[0]
        brecha = (gr.costo_s - hk.costo_s) / hk.costo_s * 100
        detalle.append({"inst": nombre, "k": int(hk.k), "optimo_s": hk.costo_s, "voraz_s": gr.costo_s,
                        "brecha_pct": round(brecha, 3), "orden_optimo": " ".join(map(str, hk.orden)),
                        "orden_voraz": " ".join(map(str, gr.orden))})
    det = pd.DataFrame(detalle)
    det.to_csv(RES / "r4_calidad_detalle.csv", index=False)
    cal = det.groupby("k")["brecha_pct"].agg(instancias="count", brecha_promedio_pct="mean", brecha_maxima_pct="max").round(2).reset_index()
    cal.to_csv(RES / "r4_calidad.csv", index=False)
    print(cal.to_string(index=False))

    # ---------- 5) ejemplo donde la heuristica no es optima ----------
    peor = det.loc[det["brecha_pct"].idxmax()]
    nom = lambda s: " -> ".join(ids[int(i)] for i in s.split())
    texto = (f"Instancia {peor.inst} (k={peor.k}, salida y regreso en Armenia)\n"
             f"Optimo (Held-Karp): {nom(peor.orden_optimo)}  = {peor.optimo_s:.1f} s\n"
             f"Voraz (vecino mas cercano): {nom(peor.orden_voraz)}  = {peor.voraz_s:.1f} s\n"
             f"Brecha: {peor.brecha_pct:.2f} %\n")
    (RES / "r4_ejemplo_voraz.txt").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
