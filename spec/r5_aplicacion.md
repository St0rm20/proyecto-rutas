# Spec R5 - Aplicacion

**Programa:** `app/app.py` (Flask + Leaflet). Se ejecuta con `python app/app.py` despues de correr R1 a R4.

## Comportamiento esperado
1. Elegir origen y destino y ver la ruta en el mapa con su tiempo (Dijkstra con cola de prioridad, calculado al momento).
2. Ver la envolvente convexa sobre el mapa.
3. Elegir partida (por defecto Armenia) y 6 a 8 atractivos; ver el recorrido de Held-Karp y el de la heuristica voraz, el tiempo de cada uno y la diferencia.
4. Ver las tablas y figuras de R1 a R4.

## Casos de prueba
- `/api/ruta?o=M01&d=T03` devuelve tiempo, nodos explorados y coordenadas.
- `/api/itinerario` con 5 o 9 atractivos responde error 400.
- `/api/resultados` lista las tablas y figuras existentes.
