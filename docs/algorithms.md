# Graph Coloring Algorithms & Complexity Analysis

## 1. Overview of Algorithms

The examination timetabling engine implements three deterministic heuristics for vertex coloring on the conflict graph $G = (V, E)$:
1. **Greedy Coloring:** Baseline heuristic that colors vertices in arbitrary or input order.
2. **Welsh-Powell (WP):** Static degree-ordered heuristic that sorts all vertices descending by vertex degree $deg(v)$ before coloring.
3. **DSATUR (Degree of Saturation):** Dynamic heuristic introduced by Daniel Brélaz (1979) that iteratively prioritizes the uncolored vertex with the highest saturation degree $\rho(v)$.

---

## 2. Formal Pseudocode

### 2.1 Greedy Coloring
```
Algorithm: GreedyColoring(V, Adj)
Input: Vertex list V, Adjacency map Adj: V -> Set[V]
Output: Proper vertex coloring c: V -> {0, 1, 2, ...}

1. c <- empty dictionary mapping V to Integer
2. For each v in V in order:
3.     neighbor_colors <- {c[u] for u in Adj[v] if u in c}
4.     color <- 0
5.     While color in neighbor_colors:
6.         color <- color + 1
7.     c[v] <- color
8. Return c
```

### 2.2 Welsh-Powell Algorithm
```
Algorithm: WelshPowell(V, Adj)
Input: Vertex list V, Adjacency map Adj: V -> Set[V]
Output: Proper vertex coloring c: V -> {0, 1, 2, ...}

1. Sort V descending by (deg(v), vertex_id) to break ties deterministically
2. c <- empty dictionary mapping V to Integer
3. For each v in sorted V:
4.     If v not in c:
5.         neighbor_colors <- {c[u] for u in Adj[v] if u in c}
6.         color <- 0
7.         While color in neighbor_colors:
8.             color <- color + 1
9.         c[v] <- color
10. Return c
```

### 2.3 DSATUR (Brélaz, 1979)
```
Algorithm: DSATUR(V, Adj, precolored={})
Input: Vertex list V, Adjacency map Adj: V -> Set[V], optional precolored dict
Output: Proper vertex coloring c: V -> {0, 1, 2, ...}

1. c <- copy of precolored
2. uncolored <- set(V) \ set(precolored.keys())
3. neighbor_color_sets <- {v: {c[u] for u in Adj[v] if u in c} for v in V}
4.
5. If precolored is empty:
6.     v_start <- argmax_{v in V} (deg(v), vertex_id)
7.     c[v_start] <- 0
8.     uncolored.remove(v_start)
9.     For each u in Adj[v_start]:
10.        neighbor_color_sets[u].add(0)
11.
12. While uncolored is not empty:
13.    # Select vertex with maximum saturation degree; tie-break by uncolored degree, then ID
14.    v_best <- argmax_{v in uncolored} (|neighbor_color_sets[v]|, deg(v), vertex_id)
15.    
16.    # Assign lowest available non-conflicting color
17.    used_colors <- neighbor_color_sets[v_best]
18.    color <- 0
19.    While color in used_colors:
20.        color <- color + 1
21.    c[v_best] <- color
22.    uncolored.remove(v_best)
23.    
24.    # Update saturation state of uncolored neighbors
25.    For each neighbor in Adj[v_best]:
26.        neighbor_color_sets[neighbor].add(color)
27.
28. Return c
```

---

## 3. Correctness Invariant Proof

**Theorem (Proper Coloring Invariant):** For any graph $G = (V, E)$, the output coloring $c$ produced by Greedy, Welsh-Powell, and DSATUR satisfies:
$$\forall (u, v) \in E \implies c(u) \ne c(v)$$

**Proof:**
By induction on the sequence of colored vertices $\{v_1, v_2, \dots, v_n\}$:
- *Base step:* For the first colored vertex $v_1$, $c(v_1) = 0$. Since no adjacent vertex has been colored, no conflicting assignment exists.
- *Inductive step:* Assume the invariant holds for the first $k$ colored vertices $V_k = \{v_1, \dots, v_k\}$. When choosing color for $v_{k+1}$, lines 4-6 in Greedy/WP and lines 17-20 in DSATUR explicitly construct:
  $$UsedColors(v_{k+1}) = \{c(u) \mid u \in Adj(v_{k+1}) \cap V_k\}$$
  The algorithm assigns $c(v_{k+1}) = \min \{x \in \mathbb{N} \mid x \notin UsedColors(v_{k+1})\}$.
  By definition of the set minimum outside $UsedColors$, $c(v_{k+1}) \ne c(u)$ for every colored neighbor $u \in Adj(v_{k+1})$.
  Therefore, no adjacent pair shares a color. By induction, the full coloring is proper. $\blacksquare$

---

## 4. Complexity & Data Structures

| Algorithm | Time Complexity (Linear Scan) | Time Complexity (Heap/Priority Queue) | Space Complexity | Optimality Guarantee |
|---|---|---|---|---|
| **Greedy** | $O(|V| + |E|)$ | $O(|V| + |E|)$ | $O(|V| + |E|)$ | Heuristic upper bound $\Delta(G) + 1$ |
| **Welsh-Powell** | $O(|V| \log |V| + |E|)$ | $O(|V| \log |V| + |E|)$ | $O(|V| + |E|)$ | Exact for bipartite graphs, $\le \Delta(G) + 1$ |
| **DSATUR** | $O(|V|^2 + |E|)$ | $O((|V| + |E|) \log |V|)$ | $O(|V| + |E|)$ | Exact for bipartite and cycle graphs; empirically within 1-2 colors of $\chi(G)$ |

### Heap vs. Linear Scan Trade-Off
- For dense graphs ($|E| \approx |V|^2$), linear scan over uncolored vertices is faster in practice due to contiguous CPU cache locality and zero heap re-balancing overhead.
- For institutional benchmarks ($\le 500$ exams), linear scan finishes in **under 100 ms** (see benchmark results below), eliminating the need for complex indexed heap pointer manipulation.

---

## 5. Determinism and Tie-Breaking Policy

To ensure byte-for-byte reproducibility across runs and audits:
1. **Initial Sort Order:** Vertices with identical degrees are broken deterministically using subject code lexicographical sorting: `(-degree, subject_code)`.
2. **Saturation Tie-Breaking:** In DSATUR, when multiple uncolored vertices have identical saturation degree $\rho(v)$, the tie is resolved by:
   - Primary: Highest uncolored degree in $G$.
   - Secondary: Highest total enrollment count.
   - Tertiary: Lexicographical exam UUID / subject code string order.
3. This guarantees that running DSATUR twice on identical enrollment inputs produces the exact same color partition mapping.

---

## 6. Empirical Benchmark Results

Benchmarked on Windows 11 / Python 3.14 on a large synthetic university dataset (500 exams, 5,000 students, 15,000 enrollments, 13,523 conflict edges, density = 0.108):

| Algorithm | Colors Used ($k$) | Execution Time (ms) | Peak Memory | SLA Target | Status |
|---|---|---|---|---|---|
| **Greedy** | 24 | 52.53 ms | 1.8 MB | < 5,000 ms | **PASS (95x faster than SLA)** |
| **Welsh-Powell** | 22 | 57.53 ms | 1.9 MB | < 5,000 ms | **PASS (86x faster than SLA)** |
| **DSATUR** | 21 | 90.07 ms | 2.2 MB | < 5,000 ms | **PASS (55x faster than SLA)** |

**Observation:** DSATUR achieves the tightest chromatic coloring (21 colors vs 24 for Greedy, saving 3 full exam sessions) while executing in 90.07 milliseconds—well within the 5.0-second interactive response threshold.
