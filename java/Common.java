// Common.java - utilidades compartidas por los tres programas en Java
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.function.BooleanSupplier;

public final class Common {
    private Common() {}

    // ---------- lectura de CSV simple (sin comillas ni comas dentro de los campos) ----------
    public static String[] split(String s, char sep) {
        List<String> out = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == sep) { out.add(cur.toString()); cur.setLength(0); }
            else if (c != '\r') cur.append(c);
        }
        out.add(cur.toString());
        return out.toArray(new String[0]);
    }

    public static String[] split(String s) { return split(s, ','); }

    public static BufferedReader abrir(String ruta) throws IOException {
        return Files.newBufferedReader(Paths.get(ruta), StandardCharsets.UTF_8);
    }

    public static int atoi(String s) { return Integer.parseInt(s.trim()); }
    public static long atoll(String s) { return Long.parseLong(s.trim()); }
    public static double atof(String s) { return Double.parseDouble(s.trim()); }

    /** Formato de punto fijo con 'dec' decimales (siempre con punto decimal). */
    public static String fmt(double v, int dec) {
        if (Double.isInfinite(v)) return v > 0 ? "inf" : "-inf";
        if (Double.isNaN(v)) return "nan";
        return String.format(Locale.ROOT, "%." + dec + "f", v);
    }

    // ---------- cronometro ----------
    public static long ahora() { return System.nanoTime(); }
    public static double msDesde(long t0) { return (System.nanoTime() - t0) / 1e6; }

    /** Mediana de un arreglo (se modifica el orden). */
    public static double mediana(double[] v, int n) {
        if (n == 0) return 0.0;
        Arrays.sort(v, 0, n);
        return (n % 2 == 1) ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]);
    }

    /** Resultado de medir_mediana: tiempo mediano en ms. */
    public static final class Medicion { public double ms; }

    /**
     * Protocolo experimental: 5 repeticiones y mediana; si la primera ejecucion supera 60 s
     * se mide una sola vez. f devuelve false si la ejecucion paso el limite de tiempo.
     * Devuelve false si alguna ejecucion no se completo.
     */
    public static boolean medirMediana(BooleanSupplier f, Medicion m, int reps) {
        double[] t = new double[Math.max(reps, 1)];
        int n = 0;
        for (int r = 0; r < reps; r++) {
            long t0 = ahora();
            boolean ok = f.getAsBoolean();
            double ms = msDesde(t0);
            if (!ok) return false;
            t[n++] = ms;
            if (r == 0 && ms > 60000.0) break;
        }
        m.ms = mediana(t, n);
        return true;
    }

    public static boolean medirMediana(BooleanSupplier f, Medicion m) { return medirMediana(f, m, 5); }

    // ---------- grafo en listas de adyacencia compactas (CSR) ----------
    public static final class Graph {
        public int V = 0;
        public int[] off;     // off[u] .. off[u+1]-1 son las aristas que salen de u
        public int[] to;      // destino de cada arista
        public double[] w;    // peso (tiempo de viaje en segundos)
    }

    /** Carga nodes.csv (solo cuenta nodos) y edges.csv (u,v,length_m,time_s,...). */
    public static Graph cargarGrafo(String dir) {
        Graph g = new Graph();
        try (BufferedReader f = abrir(dir + "/nodes.csv")) {
            f.readLine();
            String line;
            while ((line = f.readLine()) != null) if (!line.isEmpty()) g.V++;
        } catch (IOException e) {
            System.err.println("No se pudo abrir " + dir + "/nodes.csv");
            System.exit(1);
        }
        int[] U = new int[1 << 16], W = new int[1 << 16];
        double[] T = new double[1 << 16];
        int E = 0;
        try (BufferedReader f = abrir(dir + "/edges.csv")) {
            f.readLine();
            String line;
            while ((line = f.readLine()) != null) {
                if (line.isEmpty()) continue;
                String[] c = split(line);
                if (E == U.length) {
                    U = Arrays.copyOf(U, E * 2);
                    W = Arrays.copyOf(W, E * 2);
                    T = Arrays.copyOf(T, E * 2);
                }
                U[E] = atoi(c[0]);
                W[E] = atoi(c[1]);
                T[E] = atof(c[3]);
                E++;
            }
        } catch (IOException e) {
            System.err.println("No se pudo abrir " + dir + "/edges.csv");
            System.exit(1);
        }
        g.off = new int[g.V + 1];
        for (int i = 0; i < E; i++) g.off[U[i] + 1]++;
        for (int i = 0; i < g.V; i++) g.off[i + 1] += g.off[i];
        g.to = new int[E];
        g.w = new double[E];
        int[] pos = Arrays.copyOf(g.off, g.V);
        for (int i = 0; i < E; i++) {
            int p = pos[U[i]]++;
            g.to[p] = W[i];
            g.w[p] = T[i];
        }
        return g;
    }
}
