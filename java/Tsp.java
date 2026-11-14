// Tsp.java - Requerimiento 4: ruta optima de recorrido (problema del viajante asimetrico)
//
// Algoritmos (implementacion propia):
//   brute  : fuerza bruta, recorre todas las permutaciones de los k lugares (sin podas)
//   hk     : Held-Karp, programacion dinamica sobre subconjuntos, O(2^k * k^2) tiempo y
//            O(2^k * k) memoria; devuelve el orden de visita
//   greedy : heuristica voraz del vecino mas cercano, O(k^2)
//
// Uso: java Tsp <matriz.csv> <instancias.csv> <salida.csv> <algoritmos> [limite_s]
//   matriz.csv     : primera fila y primera columna con los identificadores; celda (i,j) = segundos de i a j
//   instancias.csv : encabezado inst,k,inicio,lugares  (indices de la matriz; "lugares" separados por espacio)
//   algoritmos     : lista separada por comas, por ejemplo brute,hk,greedy
//   salida.csv     : inst,k,algoritmo,tiempo_ms,costo_s,estado,orden
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.StringTokenizer;

public class Tsp {
    static final double INF = Double.POSITIVE_INFINITY;

    static final class Sol {
        double costo = INF;
        int[] orden = new int[0];  // indices locales 0..k (0 = inicio), incluye inicio al principio y al final
        boolean ok = true;
    }

    // ---------------- fuerza bruta ----------------
    static final class Brute {
        final double[][] c;
        final int k;
        double best = INF;
        final int[] cur;
        int[] bestOrd;
        final boolean[] usado;
        long hojas = 0;
        final long t0 = Common.ahora();
        final double limiteMs;
        boolean timeout = false;

        Brute(double[][] c, int k, double limiteS) {
            this.c = c; this.k = k;
            this.cur = new int[k];
            this.usado = new boolean[k + 1];
            this.limiteMs = limiteS * 1000.0;
        }

        void dfs(int prof, int ultimo, double costo) {
            if (timeout) return;
            if (prof == k) {
                double total = costo + c[ultimo][0];
                if (total < best) { best = total; bestOrd = cur.clone(); }
                if ((++hojas & ((1 << 20) - 1)) == 0 && Common.msDesde(t0) > limiteMs) timeout = true;
                return;
            }
            for (int j = 1; j <= k; ++j) {
                if (usado[j]) continue;
                usado[j] = true;
                cur[prof] = j;
                dfs(prof + 1, j, costo + c[ultimo][j]);
                usado[j] = false;
            }
        }
    }

    static Sol fuerzaBruta(double[][] c, int k, double limiteS) {
        Brute b = new Brute(c, k, limiteS);
        b.dfs(0, 0, 0.0);
        Sol s = new Sol();
        if (b.timeout) { s.ok = false; return s; }
        s.costo = b.best;
        s.orden = new int[k + 2];
        s.orden[0] = 0;
        if (b.bestOrd != null) System.arraycopy(b.bestOrd, 0, s.orden, 1, k);
        s.orden[k + 1] = 0;
        return s;
    }

    // ---------------- Held-Karp ----------------
    // dp[S][j] = menor costo de salir del inicio, visitar exactamente los lugares de S y terminar en j (j en S)
    // dp[{j}][j] = c[0][j];  dp[S][j] = min_{i en S\{j}} dp[S\{j}][i] + c[i][j]
    // Optimo = min_j dp[todos][j] + c[j][0]
    static Sol heldKarp(double[][] c, int k, double limiteS) {
        Sol s = new Sol();
        if (k > 22) { s.ok = false; return s; }              // 2^22 * 22 doubles ya son ~740 MB
        int N = 1 << k;
        double[] dp = new double[N * k];
        Arrays.fill(dp, INF);
        byte[] padre = new byte[N * k];
        Arrays.fill(padre, (byte) -1);
        long t0 = Common.ahora();
        for (int j = 0; j < k; ++j) dp[(1 << j) * k + j] = c[0][j + 1];
        for (int S = 1; S < N; ++S) {
            for (int j = 0; j < k; ++j) {
                if (((S >> j) & 1) == 0) continue;
                int Sp = S & ~(1 << j);
                if (Sp == 0) continue;
                double mejor = INF;
                int arg = -1;
                for (int i = 0; i < k; ++i) {
                    if (((Sp >> i) & 1) == 0) continue;
                    double v = dp[Sp * k + i] + c[i + 1][j + 1];
                    if (v < mejor) { mejor = v; arg = i; }
                }
                dp[S * k + j] = mejor;
                padre[S * k + j] = (byte) arg;
            }
            if ((S & 0xFFFF) == 0 && Common.msDesde(t0) > limiteS * 1000.0) { s.ok = false; return s; }
        }
        int full = N - 1;
        double mejor = INF;
        int ult = -1;
        for (int j = 0; j < k; ++j) {
            double v = dp[full * k + j] + c[j + 1][0];
            if (v < mejor) { mejor = v; ult = j; }
        }
        s.costo = mejor;
        // reconstruccion del recorrido con la tabla de padres
        List<Integer> rev = new ArrayList<>();
        int S = full;
        int j = ult;
        while (j != -1) {
            rev.add(j + 1);
            int p = padre[S * k + j];
            S &= ~(1 << j);
            j = p;
        }
        s.orden = new int[rev.size() + 2];
        s.orden[0] = 0;
        for (int i = rev.size() - 1, q = 1; i >= 0; --i, ++q) s.orden[q] = rev.get(i);
        s.orden[s.orden.length - 1] = 0;
        return s;
    }

    // ---------------- heuristica voraz: vecino mas cercano ----------------
    static Sol vecinoMasCercano(double[][] c, int k) {
        Sol s = new Sol();
        boolean[] usado = new boolean[k + 1];
        int actual = 0;
        s.orden = new int[k + 2];
        s.orden[0] = 0;
        s.costo = 0;
        for (int paso = 0; paso < k; ++paso) {
            int mejor = -1;
            for (int j = 1; j <= k; ++j)
                if (!usado[j] && (mejor == -1 || c[actual][j] < c[actual][mejor])) mejor = j;
            usado[mejor] = true;
            s.costo += c[actual][mejor];
            s.orden[paso + 1] = mejor;
            actual = mejor;
        }
        s.costo += c[actual][0];
        s.orden[k + 1] = 0;
        return s;
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 4) {
            System.err.println("Uso: Tsp <matriz.csv> <instancias.csv> <salida.csv> <brute,hk,greedy> [limite_s]");
            System.exit(1);
        }
        double limiteS = args.length >= 5 ? Common.atof(args[4]) : 300.0;
        String[] algos = Common.split(args[3]);

        // matriz
        List<double[]> filas = new ArrayList<>();
        try (BufferedReader fm = Common.abrir(args[0])) {
            fm.readLine();
            String line;
            while ((line = fm.readLine()) != null) {
                if (line.isEmpty()) continue;
                String[] c = Common.split(line);
                double[] fila = new double[c.length - 1];
                for (int i = 1; i < c.length; ++i) fila[i - 1] = Common.atof(c[i]);
                filas.add(fila);
            }
        } catch (IOException e) {
            System.err.println("No se pudo abrir " + args[0]);
            System.exit(1);
        }
        double[][] M = filas.toArray(new double[0][]);

        BufferedReader fi;
        try { fi = Common.abrir(args[1]); }
        catch (IOException e) { System.err.println("No se pudo abrir " + args[1]); System.exit(1); return; }
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(Paths.get(args[2]))); BufferedReader fr = fi) {
            out.print("inst,k,algoritmo,tiempo_ms,costo_s,estado,orden\n");
            String line = fr.readLine();  // inst,k,inicio,lugares
            while ((line = fr.readLine()) != null) {
                if (line.isEmpty()) continue;
                String[] c = Common.split(line);
                String inst = c[0];
                final int k = Common.atoi(c[1]);
                int inicio = Common.atoi(c[2]);
                List<Integer> lugares = new ArrayList<>();
                StringTokenizer st = new StringTokenizer(c[3]);
                while (st.hasMoreTokens()) lugares.add(Integer.parseInt(st.nextToken()));
                // submatriz local: 0 = inicio, 1..k = lugares
                int[] idx = new int[lugares.size() + 1];
                idx[0] = inicio;
                for (int i = 0; i < lugares.size(); i++) idx[i + 1] = lugares.get(i);
                final double[][] sub = new double[k + 1][k + 1];
                for (int a = 0; a <= k; ++a)
                    for (int b = 0; b <= k; ++b) sub[a][b] = M[idx[a]][idx[b]];

                for (String alg : algos) {
                    final Sol[] sol = new Sol[1];
                    Common.Medicion m = new Common.Medicion();
                    boolean ok;
                    switch (alg) {
                        case "brute":
                            ok = Common.medirMediana(() -> { sol[0] = fuerzaBruta(sub, k, limiteS); return sol[0].ok; }, m);
                            break;
                        case "hk":
                            ok = Common.medirMediana(() -> { sol[0] = heldKarp(sub, k, limiteS); return sol[0].ok; }, m);
                            break;
                        case "greedy":
                            ok = Common.medirMediana(() -> { sol[0] = vecinoMasCercano(sub, k); return true; }, m);
                            break;
                        default:
                            System.err.println("Algoritmo desconocido: " + alg);
                            System.exit(1);
                            return;
                    }
                    StringBuilder sb = new StringBuilder();
                    sb.append(inst).append(',').append(k).append(',').append(alg).append(',');
                    if (!ok) {
                        sb.append(",,no_completada,\n");
                    } else {
                        sb.append(Common.fmt(m.ms, 4)).append(',').append(Common.fmt(sol[0].costo, 4)).append(",ok,");
                        for (int i = 0; i < sol[0].orden.length; ++i)
                            sb.append(i > 0 ? " " : "").append(idx[sol[0].orden[i]]);
                        sb.append('\n');
                    }
                    out.print(sb);
                    System.err.println(inst + " k=" + k + " " + alg + " " + (ok ? Common.fmt(m.ms, 4) : "-1") + " ms");
                }
            }
        }
    }
}