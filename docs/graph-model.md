# Conflict Graph Formal Mathematical Model

## 1. Mathematical Formulation

Let $E = \{e_1, e_2, \dots, e_n\}$ denote the set of all examinations required for a given academic scheduling cycle. Each examination $e_i$ is uniquely associated with an academic subject or course.

Let $S = \{s_1, s_2, \dots, s_m\}$ denote the universe of enrolled students. For each examination $e \in E$, let $Enroll(e) \subseteq S$ represent the subset of students enrolled in the subject evaluated by examination $e$.

We define the undirected **Conflict Graph** $G = (V, E_G, w)$ as follows:
- **Vertex Set ($V$):** Each vertex $v_i \in V$ corresponds one-to-one with an examination $e_i \in E$. Thus, $|V| = |E| = n$.
- **Edge Set ($E_G$):** An undirected edge $(u, v) \in E_G$ exists if and only if examinations $u$ and $v$ share at least one mutually enrolled student:
  $$(u, v) \in E_G \iff Enroll(u) \cap Enroll(v) \ne \emptyset$$
- **Edge Weights ($w: E_G \to \mathbb{Z}^+$):** The weight of edge $(u, v)$ denotes the exact number of students in common:
  $$w(u, v) = |Enroll(u) \cap Enroll(v)|$$

---

## 2. Graph Construction Algorithm & Complexity

### Construction Pipeline
Rather than performing pairwise intersections across all $\binom{n}{2}$ exam pairs ($O(n^2 \cdot m)$), the conflict graph is constructed via an inverted enrollment index mapping students to their enrolled subjects:
1. **Inverted Index Map:** $StudentCourses: s_k \mapsto \{e \in E \mid s_k \in Enroll(e)\}$.
2. **Cliques Generation:** For each student $s_k$ taking $k$ subjects, all $\binom{k}{2} = \frac{k(k-1)}{2}$ unordered subject pairs $(u, v)$ with $u < v$ form a conflict clique.
3. **Weight Aggregation:** Conflicts are accumulated into an integer counter map. An edge is created between $u$ and $v$ with weight equal to the count of overlapping students.

```
Student Enrollments:
Student 1 -> {CS101, CS102, EE102}  => Edges: (CS101, CS102), (CS101, EE102), (CS102, EE102)
Student 2 -> {CS102, CS201}          => Edges: (CS102, CS201)
```

### Complexity Analysis
- **Time Complexity:** Let $\bar{k}$ be the maximum courses taken by a single student (typically $3 \le \bar{k} \le 7$). The total number of pairwise combinations evaluated across $m$ students is $\sum_{i=1}^m \binom{k_i}{2} \le m \cdot \frac{\bar{k}(\bar{k}-1)}{2}$. Since $\bar{k}$ is bounded by institutional curriculum limits, graph construction scales strictly **linearly** with the number of student enrollments: $O(m \cdot \bar{k}^2) = O(m)$.
- **Space Complexity:** Storing vertices and adjacency lists consumes $O(|V| + |E_G|)$ memory. In the worst theoretical case where every student shares a subject with every other, $|E_G| \le \frac{n(n-1)}{2}$. In empirical university schedules, course clustering by degree program and semester yields graph densities typically between $0.05$ and $0.25$.

---

## 3. Vertex Degree, Saturation, and Metrics

### Degree Metric
The degree of vertex $v$ represents the total number of distinct conflicting exams:
$$deg(v) = |\{u \in V \mid (u, v) \in E_G\}|$$

### Saturation Degree ($\rho(v)$)
Given a partial coloring $c: V' \to \mathbb{N}$ where $V' \subset V$, the saturation degree $\rho(v)$ of uncolored vertex $v \in V \setminus V'$ is defined as the number of **distinct** colors assigned to its colored neighbors:
$$\rho(v) = |\{c(u) \mid u \in Adj(v) \cap V'\}|$$

### Chromatic Lower Bound
Any complete subgraph (clique) $K_r \subseteq G$ requires at least $r$ colors. The maximum clique size $\omega(G)$ provides an absolute lower bound for the chromatic number $\chi(G)$:
$$\chi(G) \ge \omega(G) \ge \max_{v \in V} \text{local\_clique}(v)$$

---

## 4. Invariants and Graph Integrity Rules

1. **No Self-Loops:** $\forall v \in V, (v, v) \notin E_G$. An exam cannot conflict with itself.
2. **Undirected Symmetry:** $(u, v) \in E_G \iff (v, u) \in E_G$, and $w(u, v) = w(v, u)$.
3. **Strictly Positive Weights:** $\forall e \in E_G, w(e) \ge 1$. Zero-overlap edges are omitted.
4. **Deterministic Canonical IDs:** Conflict edges are canonically identified using lexicographically sorted exam UUIDs: `edge_id = min(u, v) + ":" + max(u, v)`.
5. **PII Free Payload:** Standard graph queries and client visualisations omit student identifiers to protect student privacy (PRD §23, FERPA compliance). Privileged audit drilldowns for staff require scoped authorization (`/cycles/{id}/graph/conflicts/{edge_id}/students`).
