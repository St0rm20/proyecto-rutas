"""Envoltura en Python del programa Tsp (Java): resuelve instancias y devuelve diccionarios."""
import tempfile
from pathlib import Path

import pandas as pd

from common import RES, correr, exe


def costo_orden(matriz, orden):
    """Recalcula el costo de un recorrido (lista de indices) sumando la matriz. Sirve para verificar."""
    return sum(float(matriz.iloc[a, b]) for a, b in zip(orden[:-1], orden[1:]))


def escribir_instancias(ruta, instancias):
    """instancias: lista de (nombre, inicio, [lugares])."""
    filas = [{"inst": n, "k": len(ls), "inicio": ini, "lugares": " ".join(map(str, ls))} for n, ini, ls in instancias]
    pd.DataFrame(filas).to_csv(ruta, index=False)


def resolver(instancias, algoritmos=("hk", "greedy"), matriz=None, limite_s=300):
    """Ejecuta tsp sobre varias instancias. Devuelve un DataFrame con tiempo, costo, estado y orden."""
    matriz = matriz or (RES / "matriz_tiempos.csv")
    with tempfile.TemporaryDirectory() as d:
        inst, sal = Path(d) / "inst.csv", Path(d) / "out.csv"
        escribir_instancias(inst, instancias)
        correr([exe("tsp"), matriz, inst, sal, ",".join(algoritmos), limite_s])
        df = pd.read_csv(sal)
    df["orden"] = df["orden"].apply(lambda s: [int(x) for x in str(s).split()] if isinstance(s, str) else [])
    return df
