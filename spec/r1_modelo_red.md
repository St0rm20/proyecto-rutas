# Spec R1 - Modelo de la red vial

**Entradas:** red de OSMnx (`graph_from_place("Quindío, Colombia", network_type="drive")`), `data/catalogo.csv`.
**Salidas:** `data/processed/{nodes,edges,lugares_nodos,lugares_idx}.csv`, `componente.graphml`, `results/r1_*.csv|json`.

## Comportamiento esperado
1. Se reportan V y E reales y la memoria estimada (MiB) de matriz y de listas de adyacencia, con los supuestos escritos en la tabla.
2. Cada arista tiene `length_m` y `time_s = length_m / (speed_kph * 1000 / 3600)`. La velocidad sale de `maxspeed` si existe; si no, de la tabla por tipo de via; si el tipo no esta en la tabla, 30 km/h.
3. Se conserva solo la componente fuertemente conexa mas grande. Se reportan nodos y aristas antes y despues.
4. Cada lugar queda asociado al nodo mas cercano (distancia euclidiana en UTM 18N). Los que quedan a mas de 500 m se listan en `r1_lugares_lejanos.csv`.
5. `r1_tiempos.py` mide `largest_component(strongly=True)` en radios de 2, 5, 10 y 20 km y en el departamento (mediana de 5 repeticiones).

## Casos de prueba
- Todo `u`, `v` de `edges.csv` es un indice valido de `nodes.csv`.
- `time_s > 0` y `length_m > 0` en todas las aristas.
- Desde cualquier nodo de la componente se llega a cualquier otro (se comprueba con `nx.is_strongly_connected`).
- `lugares_nodos.csv` tiene al menos 40 filas y 12/15/8/5 lugares por categoria.
