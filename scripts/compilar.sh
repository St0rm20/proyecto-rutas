#!/usr/bin/env bash
# Compila los tres programas en Java (Dijkstra, Hull, Tsp) en build/classes y crea los
# lanzadores build/dijkstra, build/hull y build/tsp que usa el codigo de Python.
set -e
cd "$(dirname "$0")/.."
RAIZ="$(pwd)"
rm -rf build
mkdir -p build/classes
javac -O -d build/classes java/*.java 2>/dev/null || javac -d build/classes java/*.java
for par in dijkstra:Dijkstra hull:Hull tsp:Tsp; do
  bin="${par%%:*}"; clase="${par##*:}"
  cat > "build/$bin" <<LANZ
#!/usr/bin/env bash
exec java -Xss64m -Xmx6g -XX:+UseSerialGC -cp "$RAIZ/build/classes" $clase "\$@"
LANZ
  chmod +x "build/$bin"
done
echo "Compilado en build/ (dijkstra, hull, tsp)"
