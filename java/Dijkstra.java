// Dijkstra.java - Requerimiento 2: caminos minimos (implementacion propia)
//
// Dos versiones de Dijkstra sobre listas de adyacencia (CSR):
//   lineal : busca el minimo con un recorrido de todos los nodos, O(V^2 + E)
//   pq     : cola de prioridad (monticulo binario propio con eliminacion perezosa), O((V+E) log V)
// Ambas se detienen al sacar el nodo destino (si hay destino) y reconstruyen la ruta con
// el predecesor de cada nodo. Cada nodo cuenta como explorado una sola vez, la primera
// vez que sale de la cola.
//
// Modos:
//   Dijkstra bench  <dir> <pares.csv> <salida.csv> [limite_s]
//   Dijkstra routes <dir> <pares_nodos.txt>            (imprime rutas por la salida estandar)
//   Dijkstra matrix <dir> <lugares_nodos.csv> <salida.csv>
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.StringTokenizer;

public class Dijkstra {
    static final double INF = Double.POSITIVE_INFINITY;

    static final class Result {
        double dist = INF;    // tiempo de viaje al destino (s)
        long explored = 0;    // nodos explorados
        boolean ok = true;    // false si se paso el limite de tiempo
    }

    // ---- Version 1: minimo por recorrido lineal ----
    // Invariante: al sacar u con la menor distancia entre los nodos no fijados, dist[u] ya es
    // la distancia minima real (los pesos son >= 0).
    static Result dijkstraLineal(Common.Graph g, int s, int t, double[] dist, int[] pred, double limiteS) {
        int V = g.V;
        Arrays.fill(dist, 0, V, INF);
        boolean[] fijo = new boolean[V];
        if (pred != null) Arrays.fill(pred, 0, V, -1);
        dist[s] = 0.0;
        Result r = new Result();
        long t0 = Common.ahora();
        for (int it = 0; it < V; ++it) {
            int u = -1;
            double best = INF;
            for (int i = 0; i < V; ++i)                 // recorrido lineal: O(V) por extraccion
                if (!fijo[i] && dist[i] < best) { best = dist[i]; u = i; }
            if (u == -1) break;                          // lo que queda es inalcanzable
            fijo[u] = true;
            r.explored++;
            if (u == t) break;                           // parada temprana
            for (int e = g.off[u]; e < g.off[u + 1]; ++e) {
                int v = g.to[e];
                double nd = dist[u] + g.w[e];
                if (!fijo[v] && nd < dist[v]) { dist[v] = nd; if (pred != null) pred[v] = u; }
            }
            if ((it & 255) == 0 && Common.msDesde(t0) > limiteS * 1000.0) { r.ok = false; return r; }
        }
        r.dist = (t >= 0) ? dist[t] : 0.0;
        return r;
    }

    // ---- Monticulo binario de minimos (clave double, valor int) ----
    static final class Heap {
        double[] key = new double[1024];
        int[] val = new int[1024];
        int n = 0;

        boolean isEmpty() { return n == 0; }

        void push(double k, int v) {
            if (n == key.length) { key = Arrays.copyOf(key, n * 2); val = Arrays.copyOf(val, n * 2); }
            int i = n++;
            while (i > 0) {
                int p = (i - 1) >> 1;
                if (key[p] <= k) break;
                key[i] = key[p]; val[i] = val[p];
                i = p;
            }
            key[i] = k; val[i] = v;
        }

        // Quita el minimo; el minimo quitado queda en topKey / topVal
        double topKey;
        int topVal;

        void pop() {
            topKey = key[0]; topVal = val[0];
            n--;
            if (n == 0) return;
            double k = key[n];
            int v = val[n];
            int i = 0;
            while (true) {
                int c = 2 * i + 1;
                if (c >= n) break;
                if (c + 1 < n && key[c + 1] < key[c]) c++;
                if (key[c] >= k) break;
                key[i] = key[c]; val[i] = val[c];
                i = c;
            }
            key[i] = k; val[i] = v;
        }
    }

    // ---- Version 2: cola de prioridad ----
    static Result dijkstraPq(Common.Graph g, int s, int t, double[] dist, int[] pred, double limiteS) {
        int V = g.V;
        Arrays.fill(dist, 0, V, INF);
        boolean[] fijo = new boolean[V];
        if (pred != null) Arrays.fill(pred, 0, V, -1);
        Heap pq = new Heap();
        dist[s] = 0.0;
        pq.push(0.0, s);
        Result r = new Result();
        long t0 = Common.ahora();
        long iter = 0;
        while (!pq.isEmpty()) {
            pq.pop();
            double d = pq.topKey;
            int u = pq.topVal;
            if (fijo[u]) continue;                       // entrada vieja: el nodo ya salio antes
            fijo[u] = true;
            r.explored++;
            if (u == t) break;
            for (int e = g.off[u]; e < g.off[u + 1]; ++e) {
                int v = g.to[e];
                double nd = d + g.w[e];
                if (!fijo[v] && nd < dist[v]) {
                    dist[v] = nd;
                    if (pred != null) pred[v] = u;
                    pq.push(nd, v);
                }
            }
            if ((++iter & 1023) == 0 && Common.msDesde(t0) > limiteS * 1000.0) { r.ok = false; return r; }
        }
        r.dist = (t >= 0) ? dist[t] : 0.0;
        return r;
    }

    static List<Integer> reconstruir(int[] pred, int s, int t) {
        List<Integer> ruta = new ArrayList<>();
        for (int v = t; v != -1; v = pred[v]) {
            ruta.add(v);
            if (v == s) break;
        }
        java.util.Collections.reverse(ruta);
        return ruta;
    }

    // ------------------------------------------------------------------------------------
    static int modoBench(String dir, String pares, String salida, double limiteS) throws IOException {
        Common.Graph g = Common.cargarGrafo(dir);
        BufferedReader f;
        try { f = Common.abrir(pares); }
        catch (IOException e) { System.err.println("No se pudo abrir " + pares); return 1; }
        int discrepancias = 0;
        double[] dist = new double[g.V];
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(Paths.get(salida))); BufferedReader fr = f) {
            out.print("origen,destino,version,tiempo_viaje_s,nodos_explorados,tiempo_ms,estado\n");
            String line = fr.readLine();  // encabezado: origen,destino,nodo_origen,nodo_destino,lineal
            while ((line = fr.readLine()) != null) {
                if (line.isEmpty()) continue;
                String[] c = Common.split(line);
                final int s = Common.atoi(c[2]), t = Common.atoi(c[3]);
                boolean conLineal = Common.atoi(c[4]) == 1;
                double viajePq = -1, viajeLin = -1;
                for (int v = 0; v < 2; ++v) {
                    final boolean lineal = (v == 0);
                    if (lineal && !conLineal) continue;
                    final Result[] res = new Result[1];
                    Common.Medicion m = new Common.Medicion();
                    boolean ok = Common.medirMediana(() -> {
                        res[0] = lineal ? dijkstraLineal(g, s, t, dist, null, limiteS)
                                        : dijkstraPq(g, s, t, dist, null, limiteS);
                        return res[0].ok;
                    }, m);
                    String ver = lineal ? "lineal" : "cola_prioridad";
                    if (ok) {
                        out.print(c[0] + "," + c[1] + "," + ver + "," + Common.fmt(res[0].dist, 4) + ","
                                + res[0].explored + "," + Common.fmt(m.ms, 4) + ",ok\n");
                        if (lineal) viajeLin = res[0].dist; else viajePq = res[0].dist;
                    } else {
                        out.print(c[0] + "," + c[1] + "," + ver + ",,,,no_completada\n");
                    }
                    System.err.println(c[0] + "->" + c[1] + " " + ver + " " + (ok ? Common.fmt(m.ms, 4) : "-1") + " ms");
                }
                if (conLineal && viajeLin >= 0 && viajePq >= 0 && Math.abs(viajeLin - viajePq) > 1e-6) {
                    System.err.println("DISCREPANCIA en " + c[0] + "->" + c[1] + ": " + viajeLin + " vs " + viajePq);
                    discrepancias++;
                }
            }
        }
        if (discrepancias > 0) { System.err.println(discrepancias + " discrepancias entre versiones"); return 2; }
        System.err.println("Verificacion: ambas versiones coinciden en todos los pares medidos con las dos.");
        return 0;
    }

    static int modoRoutes(String dir, String archivo) throws IOException {
        Common.Graph g = Common.cargarGrafo(dir);
        String contenido;
        try { contenido = Files.readString(Paths.get(archivo)); }
        catch (IOException e) { System.err.println("No se pudo abrir " + archivo); return 1; }
        PrintStream so = new PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), false);
        StringBuilder sb = new StringBuilder("origen,destino,tiempo_s,explorados,ruta\n");
        double[] dist = new double[g.V];
        int[] pred = new int[g.V];
        StringTokenizer st = new StringTokenizer(contenido);
        while (st.hasMoreTokens()) {
            int s = Integer.parseInt(st.nextToken());
            if (!st.hasMoreTokens()) break;
            int t = Integer.parseInt(st.nextToken());
            Result r = dijkstraPq(g, s, t, dist, pred, 1e9);
            sb.append(s).append(',').append(t).append(',').append(Common.fmt(r.dist, 4)).append(',')
              .append(r.explored).append(',');
            if (r.dist < INF) {
                List<Integer> ruta = reconstruir(pred, s, t);
                for (int i = 0; i < ruta.size(); ++i) sb.append(i > 0 ? " " : "").append(ruta.get(i));
            }
            sb.append('\n');
        }
        so.print(sb);
        so.flush();
        return 0;
    }

    static int modoMatrix(String dir, String lugares, String salida) throws IOException {
        Common.Graph g = Common.cargarGrafo(dir);
        List<String> ids = new ArrayList<>();
        List<Integer> nodosL = new ArrayList<>();
        try (BufferedReader f = Common.abrir(lugares)) {
            String line = f.readLine();  // id,nodo
            while ((line = f.readLine()) != null) {
                if (line.isEmpty()) continue;
                String[] c = Common.split(line);
                ids.add(c[0]);
                nodosL.add(Common.atoi(c[1]));
            }
        } catch (IOException e) { System.err.println("No se pudo abrir " + lugares); return 1; }
        int n = ids.size();
        double[] dist = new double[g.V];
        long t0 = Common.ahora();
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(Paths.get(salida)))) {
            StringBuilder h = new StringBuilder("id");
            for (String id : ids) h.append(',').append(id);
            out.print(h.append('\n'));
            for (int i = 0; i < n; ++i) {
                // una ejecucion completa (sin destino) desde cada lugar
                dijkstraPq(g, nodosL.get(i), -1, dist, null, 1e9);
                StringBuilder sb = new StringBuilder(ids.get(i));
                for (int j = 0; j < n; ++j) sb.append(',').append(Common.fmt(dist[nodosL.get(j)], 3));
                out.print(sb.append('\n'));
            }
        }
        System.err.println("Matriz " + n + "x" + n + " calculada en " + Common.fmt(Common.msDesde(t0), 4) + " ms");
        return 0;
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            System.err.println("Uso:\n  Dijkstra bench <dir> <pares.csv> <salida.csv> [limite_s]\n"
                    + "  Dijkstra routes <dir> <pares_nodos.txt>\n"
                    + "  Dijkstra matrix <dir> <lugares_nodos.csv> <salida.csv>");
            System.exit(1);
        }
        String modo = args[0];
        int rc;
        if (modo.equals("bench") && args.length >= 4)
            rc = modoBench(args[1], args[2], args[3], args.length >= 5 ? Common.atof(args[4]) : 300.0);
        else if (modo.equals("routes") && args.length >= 3) rc = modoRoutes(args[1], args[2]);
        else if (modo.equals("matrix") && args.length >= 4) rc = modoMatrix(args[1], args[2], args[3]);
        else { System.err.println("Argumentos invalidos"); rc = 1; }
        System.exit(rc);
    }
}
