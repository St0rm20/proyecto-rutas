# Spec R2 - Caminos minimos

**Programa:** `build/dijkstra` (modos `bench`, `routes`, `matrix`). **Peso:** `time_s`.

## Comportamiento esperado
1. Dos versiones propias de Dijkstra: minimo por recorrido lineal O(V^2) y cola de prioridad O((V+E) log V). Ambas paran al sacar el destino, cuentan cada nodo una sola vez al salir de la cola y reconstruyen la ruta con el predecesor.
2. `bench`: 20 pares con cola de prioridad; 10 de ellos (cercanos) tambien con la version lineal. Salida: `origen,destino,version,tiempo_viaje_s,nodos_explorados,tiempo_ms,estado`.
3. Mediana de 5 repeticiones (una sola si la primera pasa de 60 s); limite de 5 minutos -> `no_completada`.
4. `matrix`: una ejecucion completa por lugar, matriz de al menos 40 x 40, no necesariamente simetrica.

## Casos de prueba
- Ambas versiones dan el mismo `tiempo_viaje_s` en los 10 pares comunes (diferencia < 1e-6).
- 10 pares coinciden con `nx.dijkstra_path_length` (solo como verificacion).
- Origen = destino da 0 s; la diagonal de la matriz es 0.
- La ruta devuelta suma el mismo tiempo que `tiempo_viaje_s`.
