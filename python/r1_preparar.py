"""Requerimiento 1 - Modelo de la red vial.

Pasos:
  1. Descarga la red del Quindio con OSMnx (o lee un GraphML entregado por el docente).
  2. Estima la memoria de la matriz de adyacencia frente a las listas de adyacencia.
  3. Calcula pesos: distancia (m) y tiempo de viaje (s) por arista.
  4. Se queda con la componente fuertemente conexa mas grande.
  5. Asocia cada lugar del catalogo con el nodo mas cercano (distancia euclidiana, UTM 18N).
  6. Guarda el grafo procesado (nodes.csv, edges.csv, lugares_nodos.csv, componente.graphml).

Uso:
  python python/r1_preparar.py                          # descarga la red real
  python python/r1_preparar.py --graphml archivo.graphml  # usa un GraphML ya existente
"""
import argparse # Recibir argumentos desde la linea de comandos
import datetime
import json #Shhhh
import os

import numpy as np # Manejar los arreglos
import osmnx as ox # Calcular las velocidades, claramente tambien descargar los mapas
import pandas as pd #Kung fu
from scipy.spatial import cKDTree # Arból KD 

from common import DATOS, PROC, RAW, RES, a_utm, crear_carpetas, guardar_maquina

routing = ox.routing if hasattr(ox, "routing") else ox

# Velocidades por tipo de via (km/h) usadas cuando el tramo NO trae la etiqueta maxspeed.
# Es una decision del modelo: se documenta en el informe.
VELOCIDADES_TIPO = {
    "motorway": 80, "motorway_link": 50, "trunk": 70, "trunk_link": 45,
    "primary": 60, "primary_link": 40, "secondary": 50, "secondary_link": 35,
    "tertiary": 40, "tertiary_link": 30, "unclassified": 30, "residential": 30,
    "living_street": 15, "service": 20, "track": 15, "road": 30,
}
VELOCIDAD_RESPALDO = 30  # km/h para tipos de via que no estan en el diccionario

"""
Metodo para descargar el grafo
Revisa si este ya existe en la ruta para no descargarlo de nuevo, 
Devuelve el grafo del graphml y la fecha en la cual de obtiene
"""
def descargar(lugar="Quindío, Colombia"):
    ruta = RAW / "quindio.graphml"
    if ruta.exists():
        print(f"Se usa la descarga existente: {ruta}")
        fecha = datetime.datetime.fromtimestamp(ruta.stat().st_mtime).date().isoformat()
        return ox.load_graphml(ruta), fecha
    print(f"Descargando la red de '{lugar}' (puede tardar varios minutos)...")
    G = ox.graph_from_place(lugar, network_type="drive")
    ox.save_graphml(G, ruta)
    return G, datetime.date.today().isoformat()


"""
Metodo para estimar el consumo de memoria MiB, para la matriz de adyacencia 
y lista de adyacencia

Devuelve un Pandas.DataFrame con la tabla

La table genera 3 columna
representacion, supuesto, mib
"""
def estimar_memoria(V, E):
    """Estimacion en MiB de matriz y listas de adyacencia bajo dos supuestos de tamano de dato."""
    filas = []
    for nombre, b in (("float32 (4 B)", 4), ("float64 (8 B)", 8)):
        filas.append({
            "representacion": "Matriz de adyacencia",
            "supuesto": f"{V}x{V} celdas, {nombre} por celda (un solo peso)",
            "mib": V * V * b / 2**20,
        })
    # lista de adyacencia compacta: por arista destino int32 + tiempo float32 + distancia float32
    for nombre, bpa in (("12 B por arista (int32 + 2 float32)", 12), ("24 B por arista (int64 + 2 float64)", 24)):
        filas.append({
            "representacion": "Listas de adyacencia",
            "supuesto": f"{E} aristas, {nombre}, mas {V + 1} desplazamientos de 4 B",
            "mib": (E * bpa + (V + 1) * 4) / 2**20,
        })
    return pd.DataFrame(filas)



"""

Se agrega un peso a cada tramo
travel_time (s) = length (m) / (speed_kph × 1000/3600)

devuelve el diccionario de stats = {
    "aristas": total,
    "con_maxspeed_en_osm": con_maxspeed,
    "sin_maxspeed_imputadas_por_tipo": total - con_maxspeed,
}

"""
def agregar_pesos(G):
    """Anade speed_kph y travel_time (s) a cada arista y devuelve estadisticas del origen de la velocidad."""
    total = G.number_of_edges()
    con_maxspeed = sum(1 for _, _, d in G.edges(data=True) if d.get("maxspeed") not in (None, "", []))
    G = routing.add_edge_speeds(G, hwy_speeds=VELOCIDADES_TIPO, fallback=VELOCIDAD_RESPALDO)
    G = routing.add_edge_travel_times(G)  # travel_time = length / (speed_kph * 1000/3600)
    stats = {
        "aristas": total,
        "con_maxspeed_en_osm": con_maxspeed,
        "sin_maxspeed_imputadas_por_tipo": total - con_maxspeed,
    }
    return G, stats


def primero(valor):
    if isinstance(valor, list):
        return valor[0]
    return valor

"""

Primero se le asiganan ids propios para que el manejo sea más sencillo

Luego extrae las coordenadas geográficas (lon/lat) y las convierte a metros en UTM zona 18N

Algo como:

idx | osmid      | lat      | lon       | x (m)    | y (m)
0   | 245831920  | 4.5324   | -75.6734  | 834521.3 | 501823.7
1   | 245831921  | 4.5331   | -75.6741  | 834458.1 | 501901.4


Recorre cada arista y traduce los osmid al índice propio con idx[u] e idx[v].
 El primero() maneja que highway a veces viene como lista 
 (ej. ["tertiary", "residential"]) y toma solo el primer valor.



"""

def exportar(Gc, lugares):
    """Escribe nodes.csv, edges.csv y las asociaciones lugar -> nodo."""
    osmids = sorted(Gc.nodes)
    idx = {o: i for i, o in enumerate(osmids)}
    lons = np.array([Gc.nodes[o]["x"] for o in osmids])
    lats = np.array([Gc.nodes[o]["y"] for o in osmids])


    xs, ys = a_utm(lons, lats)
    nodos = pd.DataFrame({"idx": range(len(osmids)), "osmid": osmids, "lat": lats, "lon": lons, "x": xs, "y": ys})
    nodos.to_csv(PROC / "nodes.csv", index=False)

    filas = []
    for u, v, d in Gc.edges(data=True):
        filas.append((idx[u], idx[v], d["length"], d["travel_time"], primero(d.get("highway")), d.get("speed_kph")))
    aristas = pd.DataFrame(filas, columns=["u", "v", "length_m", "time_s", "highway", "speed_kph"])
    aristas.to_csv(PROC / "edges.csv", index=False)

    # asociacion de cada lugar con el nodo mas cercano en linea recta (euclidiana en metros)
    px, py = a_utm(lugares["lon"].values, lugares["lat"].values)
    arbol = cKDTree(np.column_stack([xs, ys]))
    dist, cerca = arbol.query(np.column_stack([px, py]))
    lugares = lugares.copy()
    lugares["nodo"] = cerca
    lugares["dist_nodo_m"] = np.round(dist, 1)
    lugares["lejano"] = lugares["dist_nodo_m"] > 500
    lugares.to_csv(PROC / "lugares_nodos.csv", index=False)
    lugares[["id", "nodo"]].to_csv(PROC / "lugares_idx.csv", index=False)
    lugares[lugares["lejano"]].to_csv(RES / "r1_lugares_lejanos.csv", index=False)
    return nodos, aristas, lugares


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graphml", help="GraphML existente (por ejemplo el que entregue el docente)")
    ap.add_argument("--catalogo", default=str(DATOS / "catalogo.csv"))
    a = ap.parse_args()
    crear_carpetas()
    guardar_maquina()

    if a.graphml:
        G = ox.load_graphml(a.graphml)
        fecha = datetime.datetime.fromtimestamp(os.path.getmtime(a.graphml)).date().isoformat()
        origen = f"archivo local {a.graphml}"
    else:
        G, fecha = descargar()
        origen = "OSMnx graph_from_place('Quindío, Colombia', network_type='drive')"
    V0, E0 = G.number_of_nodes(), G.number_of_edges()
    print(f"Red descargada: V={V0:,}  E={E0:,}")

    # 1) memoria (con los V y E reales de la red descargada)
    mem = estimar_memoria(V0, E0)
    mem.to_csv(RES / "r1_memoria.csv", index=False)
    print(mem.to_string(index=False))

    # 2) pesos
    G, st = agregar_pesos(G)
    print("Origen de las velocidades:", st)

    # 3) componente fuertemente conexa
    """
    Filtrar callejones, isslas, etc, para cumplir con los requisitos del trabajo
    """
    Gc = ox.truncate.largest_component(G, strongly=True)
    V1, E1 = Gc.number_of_nodes(), Gc.number_of_edges()
    pd.DataFrame([
        {"red": "Red descargada", "nodos": V0, "aristas": E0},
        {"red": "Componente fuertemente conexa", "nodos": V1, "aristas": E1},
    ]).to_csv(RES / "r1_tamano.csv", index=False)
    print(f"Componente: V={V1:,}  E={E1:,}  (se conserva {V1 / V0:.1%} de los nodos)")

    # 4) lugares y exportacion
    lugares = pd.read_csv(a.catalogo)
    nodos, aristas, lugares = exportar(Gc, lugares)
    lejanos = lugares[lugares["lejano"]]
    print(f"Lugares a mas de 500 m de su nodo: {len(lejanos)}")
    if len(lejanos):
        print(lejanos[["id", "nombre", "dist_nodo_m"]].to_string(index=False))
    ox.save_graphml(Gc, PROC / "componente.graphml")

    meta = {
        "fecha_descarga": fecha, "origen": origen, "osmnx": ox.__version__,
        "velocidades": st, "velocidades_por_tipo_kmh": VELOCIDADES_TIPO, "velocidad_respaldo_kmh": VELOCIDAD_RESPALDO,
        "nodos_descargada": V0, "aristas_descargada": E0, "nodos_componente": V1, "aristas_componente": E1,
        "lugares_lejanos": lejanos["id"].tolist(),
    }
    (RES / "r1_metadatos.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Listo. Archivos en data/processed/ y results/")


if __name__ == "__main__":
    main()
