# Spec R4 - Ruta optima de recorrido (viajante asimetrico)

**Programa:** `build/tsp` (`brute`, `hk`, `greedy`). **Entrada:** `results/matriz_tiempos.csv`.

## Comportamiento esperado
1. Fuerza bruta (todas las permutaciones, sin podas) y Held-Karp con recurrencia
   `dp[S][j] = min_{i in S\{j}} dp[S\{j}][i] + c[i][j]`, `dp[{j}][j] = c[0][j]`, optimo `min_j dp[todos][j] + c[j][0]`.
2. Held-Karp devuelve el orden de visita (tabla de padres).
3. Heuristica voraz: vecino mas cercano desde la partida, con regreso.
4. Experimentos: partida en Armenia, k de 5 a 12, lugares al azar con semilla fija; calidad con k = 5, 8, 10, 12 y 5 instancias por k.
5. Itinerario: 6 a 8 atractivos, jornada de 11 h; si no cabe, se quita el atractivo que mas tiempo consume y se recalcula.

## Casos de prueba
- Fuerza bruta y Held-Karp dan el mismo costo para todos los k resueltos por ambas.
- El orden devuelto por Held-Karp suma exactamente el costo informado y visita cada lugar una vez.
- La heuristica nunca es mejor que el optimo (brecha >= 0).
- k = 1: el recorrido es ida y vuelta.
