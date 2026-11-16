"""Requerimiento 4, punto 4 - Itinerario de un dia (jornada de 11 h).

Se sale de un lugar de partida (por defecto Armenia, M01), se ordenan entre 6 y 8 atractivos con Held-Karp
y se regresa. Si visitas + desplazamientos superan 11 h se quita, uno por uno, el atractivo que mas tiempo
consume (duracion de su visita + desvio extra que causa en el recorrido) y se recalcula con Held-Karp hasta
que quepa. Asi se conserva la mayor cantidad posible de atractivos.

Salidas: results/r4_itinerario.csv y results/r4_itinerario_resumen.json

Uso: python python/r4_itinerario.py [--inicio M01] [--atractivos T01,T03,...]
"""
import argparse
import json
import random

import pandas as pd

from common import RES, SEMILLA, cargar_lugares, cargar_matriz, crear_carpetas
from viajante import resolver

JORNADA_MIN = 11 * 60


def tabla_itinerario(orden, m, lugares):
    """Construye las filas del anexo: orden, lugar, desplazamiento (min), visita (min), acumulado (h)."""
    nombres = lugares.set_index("id")["nombre"].to_dict()
    visita = lugares.set_index("id")["duracion_visita_min"].to_dict()
    ids = list(m.index)
    filas, acum = [], 0.0
    for n, (a, b) in enumerate(zip(orden[:-1], orden[1:]), start=1):
        desp = float(m.iloc[a, b]) / 60
        es_regreso = n == len(orden) - 1
        vis = 0 if es_regreso else float(visita[ids[b]])
        acum += desp + vis
        filas.append({"orden": "Regreso" if es_regreso else n, "lugar": nombres[ids[b]],
                      "desplazamiento_min": round(desp, 1), "visita_min": "-" if es_regreso else int(vis),
                      "tiempo_acumulado_h": round(acum / 60, 2)})
    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default="M01")
    ap.add_argument("--atractivos", help="ids separados por coma (6 a 8); por defecto 8 al azar con semilla fija")
    a = ap.parse_args()
    crear_carpetas()
    m = cargar_matriz()
    lugares = cargar_lugares()
    ids = list(m.index)
    visita = lugares.set_index("id")["duracion_visita_min"].to_dict()
    tur = lugares[lugares["categoria"] == "Atractivo turistico"]["id"].tolist()
    if a.atractivos:
        elegidos = a.atractivos.split(",")
    else:
        elegidos = random.Random(SEMILLA).sample(tur, 8)
    assert 6 <= len(elegidos) <= 8, "El itinerario usa entre 6 y 8 atractivos"
    inicio = ids.index(a.inicio)
    lug = [ids.index(x) for x in elegidos]
    iniciales = [ids[i] for i in lug]
    removidos = []

    while True:
        r = resolver([("itin", inicio, lug)], ("hk", "greedy"))
        hk = r[r.algoritmo == "hk"].iloc[0]
        gr = r[r.algoritmo == "greedy"].iloc[0]
        visitas = sum(visita[ids[i]] for i in lug)
        total_min = visitas + hk.costo_s / 60
        print(f"{len(lug)} atractivos: visitas {visitas} min + desplazamientos {hk.costo_s / 60:.1f} min = {total_min / 60:.2f} h")
        if total_min <= JORNADA_MIN or len(lug) == 1:
            break
        # candidatos de remocion: tiempo total que se ahorra al quitar cada atractivo
        cand = resolver([(f"sin{j}", inicio, [x for x in lug if x != j]) for j in lug], ("hk",))
        ahorros = {}
        for j in lug:
            c = cand[cand.inst == f"sin{j}"].iloc[0].costo_s
            ahorros[j] = visita[ids[j]] + (hk.costo_s - c) / 60
        quitar = max(ahorros, key=ahorros.get)
        removidos.append({"id": ids[quitar], "ahorro_min": round(ahorros[quitar], 1)})
        print(f"  No cabe en 11 h: se quita {ids[quitar]} (ahorra {ahorros[quitar]:.1f} min)")
        lug.remove(quitar)

    tabla = tabla_itinerario(hk.orden, m, lugares)
    tabla.to_csv(RES / "r4_itinerario.csv", index=False)
    print(tabla.to_string(index=False))
    resumen = {
        "lugar_partida": a.inicio, "atractivos_iniciales": iniciales, "atractivos_finales": [ids[i] for i in lug],
        "atractivos_removidos": removidos, "tiempo_total_visitas_min": visitas,
        "tiempo_total_desplazamientos_min": round(hk.costo_s / 60, 1), "duracion_total_jornada_h": round(total_min / 60, 2),
        "cabe_en_11_h": bool(total_min <= JORNADA_MIN),
        "voraz_desplazamientos_min": round(gr.costo_s / 60, 1),
        "diferencia_voraz_vs_optimo_min": round((gr.costo_s - hk.costo_s) / 60, 1),
    }
    (RES / "r4_itinerario_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
