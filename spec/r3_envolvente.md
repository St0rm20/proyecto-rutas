# Spec R3 - Envolvente convexa

**Programa:** `build/hull`. **Algoritmo:** divide y venceras por mezcla de envolventes (ordenar, dividir, combinar con una pasada de cadena monotona).

## Comportamiento esperado
1. Coordenadas en UTM 18N, redondeadas al entero mas cercano y sin repetidos; productos cruz en enteros de 64 bits.
2. Los puntos alineados sobre un lado no cuentan como vertices. La salida va en sentido antihorario.
3. Se mide con los nodos de la red y con 1 000, 10 000 y 50 000 puntos al azar en un cuadrado (semilla 42), contra `scipy.spatial.ConvexHull`.

## Casos de prueba (`tests/test_hull.py`)
- Un solo punto; todos alineados (queda un segmento de 2 vertices); cuadrado con puntos sobre los lados y uno interior.
- 300 conjuntos aleatorios pequenos con muchos repetidos y alineados: mismos vertices que una cadena monotona independiente y que SciPy.
- Poligono estrictamente convexo y antihorario.
