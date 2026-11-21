# Examination Timetabling Scheduling & Constraint Optimization Engine

## 1. Two-Stage Scheduling Architecture

The scheduling engine decouples conflict-free session partitioning from physical calendar slot assignment via a two-stage pipeline:
1. **Stage 1 (Graph Vertex Coloring):** The conflict graph $G = (V, E)$ is colored using DSATUR, Welsh-Powell, or Greedy algorithms to produce $k$ independent sets (color partitions):
   $$\mathcal{P} = \{P_0, P_1, \dots, P_{k-1}\} \quad \text{where } \forall u, v \in P_c, (u, v) \notin E$$
2. **Stage 2 (Bipartite Slot Mapping & Constraint Optimization):** The $k$ color partitions are mapped onto physical calendar `TimeSlots` $\{T_0, T_1, \dots, T_{S-1}\}$ satisfying session capacity and minimizing soft constraint penalties.

```
+--------------------+      Coloring      +---------------------------+
|  Conflict Graph G  | -----------------> | Color Partitions P_0..P_k |
+--------------------+                    +---------------------------+
                                                        |
                                                        | Bipartite Matching
                                                        v
+--------------------+   Optimization     +---------------------------+
|  Calendar Slots T  | <----------------- | Physical Exam Assignments |
+--------------------+   Penalty Minimise +---------------------------+
```

---

## 2. Hard Constraints (Zero Tolerance Invariants)

A schedule candidate is **invalid** and cannot be published if any hard constraint is violated:
1. **HC-1 (Zero Student Conflicts):** No student can be scheduled for two examinations occurring in the exact same calendar time slot:
   $$\forall s \in S, \quad |\{e \in Enroll(s) \mid Slot(e) = T_j\}| \le 1 \quad \forall T_j$$
2. **HC-2 (Slot Duration Compliance):** An examination duration cannot exceed the physical slot window duration:
   $$Duration(e) \le Duration(Slot(e))$$
3. **HC-3 (Session Capacity Limits):** The total number of examinations scheduled in slot $T_j$ cannot exceed the configured slot capacity:
   $$|\{e \in E \mid Slot(e) = T_j\}| \le Capacity(T_j)$$
4. **HC-4 (Slot Enablement):** No examinations may be assigned to disabled calendar slots or holidays.

---

## 3. Soft Constraints & Penalty Formulation

When hard constraints are satisfied, schedules are evaluated and compared using a scalar **Soft Penalty Score**:
$$\text{Penalty} = W_{\text{consec}} \cdot N_{\text{consec}} + W_{\text{sameday}} \cdot N_{\text{sameday}} + W_{\text{gap}} \cdot N_{\text{gap}} + W_{\text{balance}} \cdot \sigma_{\text{session}}$$

| Soft Constraint | Description | Default Weight ($W_i$) | Objective |
|---|---|---|---|
| **$N_{\text{consec}}$ (Consecutive Sessions)** | A student having exams in consecutive sessions (e.g., Morning and Afternoon of the same day). | 10.0 | Minimize student fatigue |
| **$N_{\text{sameday}}$ (Same-Day Multiple)** | A student having 2 or more exams on the same calendar date. | 5.0 | Minimize cognitive overload |
| **$N_{\text{gap}}$ (Large Idle Gap)** | Large gaps between exams for student cohorts causing prolonged exam periods. | 2.0 | Maintain study momentum |
| **$\sigma_{\text{session}}$ (Load Imbalance)** | Variance in total exam count between Morning vs Afternoon sessions across all days. | 1.0 | Balance proctor & room load |

---

## 4. Locked-Exam Pre-coloring Mechanics

To support institutional overrides, special accommodations, and departmental requests:
1. Administrators or coordinators can apply a **Lock** to any exam assignment: `is_locked = True`.
2. When regenerating or re-optimizing the schedule (`preserveLockedExams = True`):
   - The slot indices of all locked exams are converted into fixed pre-colors: $c(e_{\text{locked}}) = SlotIndex(e_{\text{locked}})$.
   - DSATUR initializes its state with these pre-colored vertices, immediately updating the saturation degrees and neighbor color sets of all adjacent unlocked exams.
   - Unlocked exams are colored around the fixed anchors without disrupting the locked assignments.
3. If two locked exams conflict, the validator detects the conflict prior to execution and returns `LOCKED_EXAMS_CONFLICT` with 409 Conflict.

---

## 5. Incremental Regeneration & Version Diffs

When enrollments change or manual edits occur:
1. **Regeneration Modes:**
   - **Full Regeneration:** Clears all non-locked assignments and re-runs the coloring heuristic across the entire cycle graph.
   - **Unlocked-Only Regeneration:** Preserves locked exams and re-optimizes only un-locked courses.
2. **Version Diff Reports:**
   Comparing Candidate Version $V_B$ against Published Version $V_A$ generates an audit diff containing:
   - **Moved Exams:** $\{e \mid Slot_A(e) \ne Slot_B(e)\}$
   - **Affected Students:** Count of enrolled students whose examination date/time changed.
   - **Soft Score Delta:** $\Delta = Score(V_B) - Score(V_A)$ indicating improvement or degradation.
