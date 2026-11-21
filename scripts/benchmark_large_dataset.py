"""Benchmark Schedule Generation on 500 Exams (Performance Profiling).

PRD §19, §20, Task P14.20.
Executes pure graph coloring algorithms on a synthetic 500-exam graph:
- DSATUR
- Welsh-Powell
- Greedy
Measures total runtime in milliseconds and asserts < 5,000 ms SLA.
"""

import os
import sys
import time

# Ensure root and backend root are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.algorithms import dsatur, greedy_color, validate_coloring, welsh_powell
from app.algorithms.types import ConflictGraph

from scripts.generate_large_benchmark import generate_synthetic_benchmark


def run_benchmark():
    print("=" * 70)
    print("UNIVERSITY TIMETABLE SCHEDULING SYSTEM — PERFORMANCE BENCHMARK")
    print("PRD §19, §20 SLA Target: < 5.0 seconds for 500 Exams")
    print("=" * 70)

    t0 = time.perf_counter()
    data = generate_synthetic_benchmark(num_exams=500, num_students=5000, target_enrollments=15000)
    gen_time_ms = (time.perf_counter() - t0) * 1000

    # Build ConflictGraph
    adj: dict[str, set[str]] = data.conflict_adjacency
    vertices = sorted(data.conflict_adjacency.keys())
    edge_count = sum(len(neighbors) for neighbors in adj.values()) // 2
    avg_degree = sum(len(neighbors) for neighbors in adj.values()) / len(vertices)

    _graph = ConflictGraph(
        vertices=set(vertices),
        adjacency=adj,
        edge_weights={},
        vertex_metadata={},
    )

    print("Dataset:              500 Exams, 5,000 Students, 15,000 Enrollments")
    print(f"Graph Vertices (|V|): {len(vertices)}")
    print(f"Graph Edges (|E|):    {edge_count}")
    print(f"Average Degree:       {avg_degree:.2f}")
    print(f"Dataset Gen Time:     {gen_time_ms:.2f} ms")
    print("-" * 70)
    print(f"{'Algorithm':<20} | {'Runtime (ms)':<15} | {'Colors':<10} | {'Valid?':<8} | {'Status'}")
    print("-" * 70)

    algorithms = [
        ("DSATUR (Primary)", dsatur),
        ("Welsh-Powell", welsh_powell),
        ("Greedy (First-Fit)", greedy_color),
    ]

    all_passed = True
    for name, algo_fn in algorithms:
        start_time = time.perf_counter()
        result = algo_fn(adj)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Validate zero hard clashes
        val_report = validate_coloring(adj, result.colors)
        is_valid = val_report.valid

        # Target: < 5000 ms
        meets_target = elapsed_ms < 5000.0 and is_valid
        if not meets_target:
            all_passed = False

        status = "PASS (<5s)" if meets_target else "FAIL"
        print(f"{name:<20} | {elapsed_ms:<15.2f} | {result.color_count:<10} | {is_valid!s:<8} | {status}")

    print("=" * 70)
    if all_passed:
        print("ALL ALGORITHMS COMPLETED WITHIN THE 5-SECOND PERFORMANCE SLA.")
    else:
        print("SOME ALGORITHMS FAILED THE PERFORMANCE OR VALIDITY SLA.")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
