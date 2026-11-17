# Proyecto Rutas del Paisaje Cultural Cafetero

Sistema de planificación de rutas sobre la red vial del Quindío. Se implementan y analizan algoritmos de caminos mínimos (Dijkstra), envolvente convexa (divide y vencerás) y el problema del viajante asimétrico (fuerza bruta, Held-Karp y vecino más cercano); además, se incluye una aplicación web demostrativa.

Curso Análisis de Algoritmos, Universidad del Quindío, 2026-2.
Integrantes: Juan Pablo López Gómez, Miguel Ángel Vargas Peláez y Willinton Vergara Cataño.

## Organización del proyecto

Los algoritmos de implementación propia están en **Java**, de modo que todas las mediciones son comparables. **Python** se usa para descargar y preparar la red con OSMnx, generar los datos, llamar a los programas de Java, verificar los resultados y producir las tablas y gráficas. Los dos lenguajes se comunican mediante archivos CSV: Python ejecuta los programas de Java como procesos externos y lee lo que estos escriben.

```
proyecto-rutas/
├── data/
│   ├── catalogo.csv          catálogo de 40 lugares (id, nombre, municipio, categoría, lat, lon, duración de visita)
│   ├── raw/                  redes descargadas de OSMnx (GraphML): departamento y radios de 2, 5, 10 y 20 km
│   └── processed/            componente fuertemente conexa: nodes.csv, edges.csv, lugares_nodos.csv, lugares_idx.csv
├── java/                     algoritmos propios: Dijkstra.java, Hull.java, Tsp.java y Common.java
├── python/                   scripts de cada requerimiento (r1_*.py, r2_*.py, r3_*.py, r4_*.py)
├── app/                      aplicación web (Flask + Leaflet)
├── scripts/compilar.sh       compila Java y crea los lanzadores build/dijkstra, build/hull y build/tsp
├── spec/                     especificaciones de cada requerimiento (comportamiento esperado y casos de prueba)
└── results/                  resultados de los experimentos (CSV, JSON) y figuras (results/figuras/)
```

## Requisitos

| Herramienta | Versión usada | Para qué |
|---|---|---|
| Python | 3.13 | preparación de datos, experimentos, gráficas y aplicación |
| JDK (Java) | OpenJDK 21 | compilar y ejecutar los algoritmos (se necesita `javac`, no solo `java`) |
| Bash | cualquiera | ejecutar `scripts/compilar.sh` y los lanzadores de `build/` |

El proyecto se ejecutó en Linux (Fedora 42). En macOS funciona igual; en Windows se recomienda usar **WSL**, ya que los lanzadores de `build/` son scripts de Bash.

## Instalación

```bash
git clone https://github.com/St0rm20/proyecto-rutas.git
cd proyecto-rutas

# entorno virtual de Python
python3 -m venv .venv
source .venv/bin/activate          # en Windows con WSL es el mismo comando
pip install -r requirements.txt

# compilar los algoritmos en Java
bash scripts/compilar.sh
```

`compilar.sh` se debe ejecutar de nuevo cada vez que se clone el repositorio en otra carpeta o se modifique un archivo de `java/`, ya que los lanzadores guardan la ruta absoluta de las clases compiladas.

## Reproducir los experimentos

Todos los comandos se ejecutan **desde la raíz del repositorio** y en este orden, porque cada requerimiento lee los archivos que produce el anterior.

### R1. Modelo de la red vial

```bash
python python/r1_preparar.py
python python/r1_tiempos.py
```

- `r1_preparar.py` usa la red guardada en `data/raw/quindio.graphml`; si el archivo no existe, la descarga con `ox.graph_from_place("Quindío, Colombia", network_type="drive")`. También admite un GraphML entregado por el docente: `python python/r1_preparar.py --graphml ruta/archivo.graphml`.
- Calcula los pesos (distancia y tiempo de viaje), extrae la componente fuertemente conexa, asocia cada lugar a su nodo más cercano y guarda el grafo procesado en `data/processed/`.
- `r1_tiempos.py` mide `ox.truncate.largest_component(G, strongly=True)` en las redes de 2, 5, 10 y 20 km y en el departamento completo; si alguna red de radio no está en `data/raw/`, la descarga.

La red usada en los resultados se descargó el **15 de noviembre de 2026**. Para obtener exactamente los mismos valores no se deben borrar los GraphML de `data/raw/`, porque una descarga nueva puede traer cambios de OpenStreetMap.

### R2. Caminos mínimos

```bash
python python/r2_experimentos.py
```

Elige 20 pares origen-destino (semilla 42), mide Dijkstra con cola de prioridad en los 20 y la versión lineal en 10 de ellos, genera la gráfica de tiempo frente a nodos explorados, calcula el cociente entre versiones, verifica los resultados contra NetworkX y calcula la matriz de tiempos 40 × 40. Opción: `--limite 300` (límite por ejecución, en segundos). Los 10 pares de la versión lineal se eligen entre lugares del mismo municipio o de municipios vecinos; los otros 10 se eligen al azar entre todos los lugares.

### R3. Envolvente convexa

```bash
python python/r3_experimentos.py
```

Calcula la envolvente de los nodos de la red y de 1 000, 10 000 y 50 000 puntos al azar (semilla 42), compara los vértices y los tiempos con `scipy.spatial.ConvexHull` y genera el GeoJSON que usa la aplicación.

### R4. Ruta óptima de recorrido

```bash
python python/r4_experimentos.py
python python/r4_itinerario.py
```

- `r4_experimentos.py` ejecuta fuerza bruta y Held-Karp para k de 5 a 12, mide la calidad de la heurística (k = 5, 8, 10 y 12, cinco instancias por cada k) y guarda el ejemplo en el que la heurística no encuentra el óptimo. Opciones: `--limite 300` y `--hk-hasta 18` (serie adicional solo con Held-Karp; `0` la omite). Es el paso más lento: la fuerza bruta con k = 12 tarda unos 20 s por repetición, de modo que el script completo toma alrededor de 3 minutos.
- `r4_itinerario.py` arma el itinerario de un día (jornada de 11 h) saliendo de Armenia. Opciones: `--inicio M01` y `--atractivos T01,T03,...` (entre 6 y 8 identificadores del catálogo; por defecto se eligen 8 al azar con semilla 42).

## Ejecutar la aplicación (R5)

Requiere haber compilado Java y haber ejecutado R1 a R4 (o usar los resultados ya incluidos en el repositorio).

```bash
python app/app.py
```

Luego se abre **http://127.0.0.1:5000** en el navegador. La aplicación tiene cuatro pestañas:

- **Ruta:** se eligen origen y destino; la ruta se calcula en el momento con Dijkstra con cola de prioridad y se dibuja en el mapa con su tiempo de viaje.
- **Envolvente:** muestra la envolvente convexa de la red sobre el mapa del departamento.
- **Itinerario:** se elige el lugar de partida (por defecto Armenia) y entre 6 y 8 atractivos (Ctrl o Cmd para seleccionar varios); se muestran el recorrido de Held-Karp y el de la heurística voraz, con el tiempo de cada uno y la diferencia entre ellos.
- **Resultados:** tablas y gráficas de los requerimientos 1 a 4.

El mapa base se carga desde OpenStreetMap, por lo que el navegador necesita conexión a internet.

## Archivos de resultados

| Requerimiento | Archivos |
|---|---|
| Máquina y semilla | `results/maquina.json` |
| R1 | `results/r1/r1_tamano.csv`, `r1_memoria.csv`, `r1_lugares_lejanos.csv`, `r1_metadatos.json`, `results/r1/1.2/r1_tiempos.csv`, `r1_algoritmo.txt` |
| R2 | `results/r2/r2_pares.csv`, `r2_mediciones.csv`, `r2_cociente.csv`, `r2_verificacion.txt`, `matriz_tiempos.csv` |
| R3 | `results/r3/r3_tiempos.csv`, `envolvente.geojson` |
| R4 | `results/r4/4.1/r4_exactas.csv`, `r4_hk_extra.csv`, `r4_calidad.csv`, `r4_calidad_detalle.csv`, `r4_ejemplo_voraz.txt`, `results/r4/4.2/r4_itinerario.csv`, `r4_itinerario_resumen.json` |
| Figuras | `results/figuras/r1_tiempos.png`, `r2_tiempo_vs_nodos.png`, `r3_envolvente.png`, `r4_tiempo_vs_k.png` |

Todas las tablas y gráficas del documento técnico se generan a partir de estos archivos.

## Protocolo experimental

- Equipo de las mediciones: AMD Ryzen 5 5500U (6 núcleos), 17,4 GB de RAM, Linux Fedora 42 (núcleo 6.19.14), Python 3.13.13 y OpenJDK 21.0.11.
- La máquina virtual de Java se ejecuta con `-Xss64m -Xmx6g -XX:+UseSerialGC` (ver `scripts/compilar.sh`).
- Solo se mide el algoritmo; la lectura de archivos, el arranque de Java y la escritura de resultados quedan por fuera.
- Cada medición se repite 5 veces y se reporta la mediana; si la primera ejecución pasa de 60 s, se mide una sola vez.
- Los tiempos se guardan en milisegundos.
- Semilla fija: **42** para todos los datos aleatorios.
- Límite de tiempo: una ejecución que pasa de 5 minutos se detiene y se reporta como `no_completada`.
- Antes de reportar, cada algoritmo se verifica: Dijkstra lineal contra Dijkstra con cola de prioridad y contra NetworkX; la envolvente contra SciPy; Held-Karp contra fuerza bruta; y en todos los recorridos se recalcula el costo sumando la matriz.

## Problemas conocidos

- Si la descarga de OSMnx falla por bloqueo del servidor de Overpass, se puede descargar la red desde otra conexión y pasarla con `--graphml`, o usar el GraphML que entregue el docente.
- Si aparece `Falta build/...`, no se ha ejecutado `bash scripts/compilar.sh`.
