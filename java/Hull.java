// Hull.java - Requerimiento 3: envolvente convexa por divide y venceras (implementacion propia)
//
// Algoritmo: divide y venceras por mezcla de envolventes.
//   1. Se ordenan los puntos por (x, y) y se eliminan repetidos (una sola vez).
//   2. Dividir: se parte el arreglo ordenado en dos mitades.
//   3. Vencer: se calcula recursivamente la envolvente de cada mitad.
//   4. Combinar: como todos los puntos de la mitad izquierda quedan antes que los de la
//      derecha, los vertices de ambas envolventes ya forman una lista ordenada; sobre ella
//      se hace una sola pasada de cadena monotona (producto cruz) y se obtiene la envolvente
//      de la union. El costo de combinar es proporcional al numero de vertices de las dos
//      envolventes (h1 + h2 <= n).
// Recurrencia: T(n) = 2T(n/2) + O(n)  ->  O(n log n) en el peor caso, sin importar la
// distribucion de los puntos. Memoria: O(n).
// Los productos cruz usan enteros de 64 bits; los puntos alineados sobre un lado no se
// cuentan como vertices (se descartan con cross <= 0 / cross >= 0).
//
// Uso: java Hull <puntos.csv> <vertices_salida.csv> [repeticiones]
//   puntos.csv: encabezado x,y y coordenadas enteras (metros, UTM 18N)
//   salida estandar: n_unicos,h,tiempo_ms
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Hull {
    static final class P implements Comparable<P> {
        final long x, y;
        P(long x, long y) { this.x = x; this.y = y; }
        @Override public int compareTo(P o) { return x != o.x ? Long.compare(x, o.x) : Long.compare(y, o.y); }
        boolean igual(P o) { return x == o.x && y == o.y; }
    }

    static long cross(P o, P a, P b) {
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
    }

    // Envolvente como dos cadenas ordenadas de izquierda a derecha.
    static final class HullCadenas {
        ArrayList<P> lower = new ArrayList<>(), upper = new ArrayList<>();
    }

    // Une dos cadenas (ambas ordenadas) en una lista ordenada sin repetir los extremos.
    static ArrayList<P> verticesOrdenados(HullCadenas h) {
        ArrayList<P> out = new ArrayList<>(h.lower.size() + h.upper.size());
        int i = 0, j = 0;
        while (i < h.lower.size() || j < h.upper.size()) {
            P p;
            if (j >= h.upper.size() || (i < h.lower.size() && h.lower.get(i).compareTo(h.upper.get(j)) <= 0)) p = h.lower.get(i++);
            else p = h.upper.get(j++);
            if (out.isEmpty() || !out.get(out.size() - 1).igual(p)) out.add(p);
        }
        return out;
    }

    // Cadena monotona sobre puntos ya ordenados (un solo recorrido, O(m)).
    static HullCadenas cadenaMonotona(List<P> pts) {
        HullCadenas h = new HullCadenas();
        for (P p : pts) {
            ArrayList<P> L = h.lower;
            while (L.size() >= 2 && cross(L.get(L.size() - 2), L.get(L.size() - 1), p) <= 0) L.remove(L.size() - 1);
            L.add(p);
        }
        for (P p : pts) {
            ArrayList<P> U = h.upper;
            while (U.size() >= 2 && cross(U.get(U.size() - 2), U.get(U.size() - 1), p) >= 0) U.remove(U.size() - 1);
            U.add(p);
        }
        return h;
    }

    // Envolvente de pts[l, r) (ya ordenados y sin repetidos)
    static HullCadenas dyv(P[] pts, int l, int r) {
        if (r - l == 1) {
            HullCadenas h = new HullCadenas();
            h.lower.add(pts[l]);
            h.upper.add(pts[l]);
            return h;
        }
        int mid = (l + r) >>> 1;
        HullCadenas A = dyv(pts, l, mid);
        HullCadenas B = dyv(pts, mid, r);
        ArrayList<P> uni = verticesOrdenados(A);
        uni.addAll(verticesOrdenados(B));        // A < B en el orden lexicografico
        return cadenaMonotona(uni);
    }

    static P[] unicos(P[] pts) {
        P[] s = pts.clone();
        Arrays.sort(s);
        int m = 0;
        for (int i = 0; i < s.length; i++)
            if (m == 0 || !s[m - 1].igual(s[i])) s[m++] = s[i];
        return Arrays.copyOf(s, m);
    }

    // Resultado en sentido antihorario, empezando por el punto mas a la izquierda y abajo.
    static List<P> envolvente(P[] pts) {
        P[] u = unicos(pts);
        if (u.length == 0) return new ArrayList<>();
        HullCadenas h = dyv(u, 0, u.length);
        List<P> res = new ArrayList<>(h.lower);
        if (h.lower.size() > 1)
            for (int i = h.upper.size() - 2; i >= 1; --i) res.add(h.upper.get(i));
        return res;
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 2) { System.err.println("Uso: Hull <puntos.csv> <vertices.csv> [reps]"); System.exit(1); }
        int reps = args.length >= 3 ? Common.atoi(args[2]) : 5;
        List<P> lista = new ArrayList<>();
        try (BufferedReader f = Common.abrir(args[0])) {
            f.readLine();
            String line;
            while ((line = f.readLine()) != null) {
                if (line.isEmpty()) continue;
                String[] c = Common.split(line);
                lista.add(new P(Common.atoll(c[0]), Common.atoll(c[1])));
            }
        } catch (IOException e) {
            System.err.println("No se pudo abrir " + args[0]);
            System.exit(1);
        }
        P[] pts = lista.toArray(new P[0]);
        @SuppressWarnings("unchecked")
        List<P>[] res = new List[1];
        Common.Medicion m = new Common.Medicion();
        // Solo se mide el algoritmo (ordenar + dividir + combinar); la lectura queda por fuera
        Common.medirMediana(() -> { res[0] = envolvente(pts); return true; }, m, reps);
        int nUnicos = unicos(pts).length;
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(Paths.get(args[1])))) {
            out.print("x,y\n");
            for (P p : res[0]) out.print(p.x + "," + p.y + "\n");
        }
        System.out.println(nUnicos + "," + res[0].size() + "," + Common.fmt(m.ms, 4));
    }
}