"""Requerimiento 5 - Aplicacion demostrativa (Flask + Leaflet).

Las rutas y el itinerario se calculan en el momento llamando a los programas en Java:
  - Dijkstra con cola de prioridad  (build/dijkstra routes)
  - Held-Karp y vecino mas cercano  (build/tsp)
La envolvente convexa ya esta calculada (results/r3/envolvente.geojson).

Uso (desde la raiz del repositorio):  python app/app.py      y abrir http://127.0.0.1:5000
"""
import io
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
from common import FIG, PROC, RES, RES_R1, RES_R1_2, RES_R2, RES_R3, RES_R4_1, RES_R4_2, cargar_lugares, cargar_matriz, cargar_nodos, correr, exe  # noqa: E402
from viajante import resolver  # noqa: E402

app = Flask(__name__)

NODOS = cargar_nodos()
LAT, LON = NODOS["lat"].values, NODOS["lon"].values
LUGARES = cargar_lugares()
MATRIZ = cargar_matriz()
IDS = list(MATRIZ.index)
NODO_DE = dict(zip(LUGARES["id"], LUGARES["nodo"]))
NOMBRE = dict(zip(LUGARES["id"], LUGARES["nombre"]))
VISITA = dict(zip(LUGARES["id"], LUGARES["duracion_visita_min"]))

TABLAS = [(RES_R1 / "r1_tamano.csv", "R1. Tamano de la red antes y despues de la componente"),
          (RES_R1 / "r1_memoria.csv", "R1. Memoria estimada de las representaciones"),
          (RES_R1_2 / "r1_tiempos.csv", "R1. Tiempo de obtener la componente"),
          (RES_R2 / "r2_cociente.csv", "R2. Cociente lineal / cola de prioridad"),
          (RES_R3 / "r3_tiempos.csv", "R3. Envolvente convexa: propia frente a SciPy"),
          (RES_R4_1 / "r4_exactas.csv", "R4. Soluciones exactas"),
          (RES_R4_1 / "r4_calidad.csv", "R4. Calidad de la heuristica"),
          (RES_R4_2 / "r4_itinerario.csv", "R4. Itinerario de un dia")]


def rutas_nodos(pares):
    """pares: lista de (nodo_origen, nodo_destino). Devuelve lista de dicts con tiempo, explorados y coordenadas."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(f"{o} {d}" for o, d in pares) + "\n")
        ruta = f.name
    out, _ = correr([exe("dijkstra"), "routes", PROC, ruta])
    df = pd.read_csv(io.StringIO(out))
    res = []
    for _, r in df.iterrows():
        nodos = [int(x) for x in str(r["ruta"]).split()] if isinstance(r["ruta"], str) else []
        res.append({"tiempo_s": float(r["tiempo_s"]), "explorados": int(r["explorados"]),
                    "coords": [[float(LAT[n]), float(LON[n])] for n in nodos]})
    return res


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/lugares")
def api_lugares():
    cols = ["id", "nombre", "municipio", "categoria", "lat", "lon", "duracion_visita_min"]
    return jsonify(LUGARES[cols].to_dict(orient="records"))


@app.route("/api/ruta")
def api_ruta():
    o, d = request.args["o"], request.args["d"]
    r = rutas_nodos([(NODO_DE[o], NODO_DE[d])])[0]
    r.update({"origen": NOMBRE[o], "destino": NOMBRE[d]})
    return jsonify(r)


@app.route("/api/envolvente")
def api_envolvente():
    return send_from_directory(RES_R3, "envolvente.geojson")


@app.route("/api/itinerario", methods=["POST"])
def api_itinerario():
    datos = request.get_json()
    inicio_id, ids = datos["inicio"], datos["atractivos"]
    if not 6 <= len(ids) <= 8:
        return jsonify({"error": "Elija entre 6 y 8 atractivos"}), 400
    inicio = IDS.index(inicio_id)
    lug = [IDS.index(x) for x in ids]
    r = resolver([("app", inicio, lug)], ("hk", "greedy"))
    salida = {}
    for alg in ("hk", "greedy"):
        fila = r[r.algoritmo == alg].iloc[0]
        orden = fila.orden
        pares = [(NODO_DE[IDS[a]], NODO_DE[IDS[b]]) for a, b in zip(orden[:-1], orden[1:])]
        tramos = rutas_nodos(pares)
        visitas = sum(VISITA[IDS[i]] for i in lug)
        salida[alg] = {"orden": [{"id": IDS[i], "nombre": NOMBRE[IDS[i]]} for i in orden],
                       "desplazamientos_min": round(fila.costo_s / 60, 1), "visitas_min": int(visitas),
                       "total_h": round((visitas + fila.costo_s / 60) / 60, 2),
                       "tramos": [t["coords"] for t in tramos]}
    salida["diferencia_min"] = round(salida["greedy"]["desplazamientos_min"] - salida["hk"]["desplazamientos_min"], 1)
    salida["cabe_en_11_h"] = bool(salida["hk"]["total_h"] <= 11)
    return jsonify(salida)


@app.route("/api/resultados")
def api_resultados():
    tablas = []
    for ruta, titulo in TABLAS:
        if ruta.exists():
            df = pd.read_csv(ruta)
            tablas.append({"titulo": titulo, "html": df.to_html(index=False, border=0, classes="t")})
    figuras = sorted(p.name for p in FIG.glob("*.png"))
    return jsonify({"tablas": tablas, "figuras": figuras})


@app.route("/figuras/<path:nombre>")
def figura(nombre):
    return send_from_directory(FIG, nombre)


if __name__ == "__main__":
    app.run(debug=False, port=5000)