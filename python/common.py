"""Utilidades compartidas: rutas del repositorio, proyeccion UTM y ejecucion de los programas en C++."""
import json
import os
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
RAW = DATOS / "raw"
PROC = DATOS / "processed"
RES = RAIZ / "results"
FIG = RES / "figuras"
BUILD = RAIZ / "build"

SEMILLA = 42  # semilla fija de todos los experimentos aleatorios

# WGS84 (lat, lon) -> UTM zona 18N (metros). always_xy => (lon, lat) -> (x, y)
_a_utm = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
_a_geo = Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True)


def a_utm(lon, lat):
    x, y = _a_utm.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))
    return np.asarray(x), np.asarray(y)


def a_geo(x, y):
    lon, lat = _a_geo.transform(np.asarray(x, dtype=float), np.asarray(y, dtype=float))
    return np.asarray(lat), np.asarray(lon)


def crear_carpetas():
    for p in (RAW, PROC, RES, FIG):
        p.mkdir(parents=True, exist_ok=True)


def exe(nombre):
    ruta = BUILD / nombre
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Compile primero: cmake -S . -B build && cmake --build build")
    return str(ruta)


def correr(args, **kw):
    """Ejecuta un programa en C++ y devuelve (stdout, stderr). Falla si el codigo de salida no es 0."""
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"Fallo {' '.join(map(str, args))}\n{r.stderr}")
    return r.stdout, r.stderr


def info_maquina():
    """Datos de la maquina que exige el protocolo experimental (seccion 6, regla 1)."""
    cpu = platform.processor()
    try:
        for linea in open("/proc/cpuinfo"):
            if linea.startswith("model name"):
                cpu = linea.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    try:
        import psutil
        ram = round(psutil.virtual_memory().total / 2**30, 1)
    except ImportError:
        ram = None
    try:
        gpp = subprocess.run(["g++", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    except Exception:
        gpp = "desconocido"
    return {
        "procesador": cpu,
        "ram_gb": ram,
        "sistema_operativo": platform.platform(),
        "python": platform.python_version(),
        "compilador_cpp": gpp,
        "banderas": "-O2 -std=c++17",
        "semilla": SEMILLA,
    }


def guardar_maquina():
    crear_carpetas()
    (RES / "maquina.json").write_text(json.dumps(info_maquina(), indent=2, ensure_ascii=False), encoding="utf-8")


def cargar_nodos():
    return pd.read_csv(PROC / "nodes.csv")


def cargar_lugares():
    """Catalogo + nodo asociado (salida de r1_preparar.py)."""
    return pd.read_csv(PROC / "lugares_nodos.csv")


def cargar_matriz():
    m = pd.read_csv(RES / "matriz_tiempos.csv", index_col=0)
    return m
