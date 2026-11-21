"""Algorithm Benchmarking and DAA Comparison Harness.

PRD §12, §22, Task P7.18:
Generates random and structured graphs (Erdos-Renyi, Complete, Bipartite, Cycle)
across multiple vertex sizes (50, 100, 250, 500) and benchmarks:
- Greedy (stable ID order)
- Welsh-Powell (descending degree order)
- DSATUR (linear scan)
- DSATUR (heap accelerated)

Outputs performance metrics (color count, execution time ms, vertex visits, color checks)
to standard output and downloadable CSV.
"""

import argparse
import csv
import io
import random
import time

from app.algorithms.dsatur import dsatur
from app.algorithms.greedy import greedy_color
from app.algorithms.types import AdjacencyList
from app.algorithms.welsh_powell import welsh_powell


def generate_erdos_renyi_graph(n: int, p: float, seed: int = 42) -> AdjacencyList:
    """Generates an Erdos-Renyi G(n, p) random undirected graph."""
    rng = random.Random(seed)
    vertices = [f"v{i}" for i in range(n)]
    adj: AdjacencyList = {v: set() for v in vertices}

    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                u, v = vertices[i], vertices[j]
                adj[u].add(v)
                adj[v].add(u)
    return adj


def generate_complete_graph(n: int) -> AdjacencyList:
    """Generates a complete graph K_n."""
    vertices = [f"v{i}" for i in range(n)]
    adj: AdjacencyList = {v: set() for v in vertices}
    for i in range(n):
        for j in range(i + 1, n):
            u, v = vertices[i], vertices[j]
            adj[u].add(v)
            adj[v].add(u)
    return adj


def generate_bipartite_graph(n: int, p: float = 0.3, seed: int = 42) -> AdjacencyList:
    """Generates a random bipartite graph with partitions of size n/2."""
    rng = random.Random(seed)
    n1 = n // 2
    n2 = n - n1
    part1 = [f"a{i}" for i in range(n1)]
    part2 = [f"b{j}" for j in range(n2)]
    adj: AdjacencyList = {v: set() for v in part1 + part2}

    for u in part1:
        for v in part2:
            if rng.random() < p:
                adj[u].add(v)
                adj[v].add(u)
    return adj


def generate_cycle_graph(n: int) -> AdjacencyList:
    """Generates a cycle graph C_n."""
    vertices = [f"v{i}" for i in range(n)]
    adj: AdjacencyList = {v: set() for v in vertices}
    for i in range(n):
        u = vertices[i]
        v = vertices[(i + 1) % n]
        adj[u].add(v)
        adj[v].add(u)
    return adj


def benchmark_suite(sizes: list[int] | None = None) -> list[dict[str, object]]:
    """Runs the benchmark across graph families and sizes."""
    target_sizes = sizes or [50, 100, 250, 500]
    benchmarks: list[tuple[str, AdjacencyList]] = []

    for n in target_sizes:
        benchmarks.append((f"ErdosRenyi_n{n}_p0.1", generate_erdos_renyi_graph(n, p=0.1, seed=n)))
        benchmarks.append((f"ErdosRenyi_n{n}_p0.3", generate_erdos_renyi_graph(n, p=0.3, seed=n * 2)))
        benchmarks.append((f"Bipartite_n{n}", generate_bipartite_graph(n, p=0.2, seed=n)))
        benchmarks.append((f"Cycle_n{n}", generate_cycle_graph(n)))

    # Add small complete graph
    benchmarks.append(("Complete_K50", generate_complete_graph(50)))

    results: list[dict[str, object]] = []

    for name, adj in benchmarks:
        v_count = len(adj)
        e_count = sum(len(nbrs) for nbrs in adj.values()) // 2

        # 1. Greedy
        r_greedy = greedy_color(adj, deterministic=True)
        results.append({
            "graph_name": name,
            "vertices": v_count,
            "edges": e_count,
            "algorithm": "Greedy",
            "colors": r_greedy.color_count,
            "time_ms": r_greedy.execution_time_ms,
            "vertex_visits": r_greedy.vertex_visits,
            "color_checks": r_greedy.color_checks,
            "valid": r_greedy.valid,
        })

        # 2. Welsh-Powell
        r_wp = welsh_powell(adj, deterministic=True)
        results.append({
            "graph_name": name,
            "vertices": v_count,
            "edges": e_count,
            "algorithm": "Welsh-Powell",
            "colors": r_wp.color_count,
            "time_ms": r_wp.execution_time_ms,
            "vertex_visits": r_wp.vertex_visits,
            "color_checks": r_wp.color_checks,
            "valid": r_wp.valid,
        })

        # 3. DSATUR (Linear Scan)
        r_dsatur = dsatur(adj, deterministic=True, use_heap=False)
        results.append({
            "graph_name": name,
            "vertices": v_count,
            "edges": e_count,
            "algorithm": "DSATUR_Linear",
            "colors": r_dsatur.color_count,
            "time_ms": r_dsatur.execution_time_ms,
            "vertex_visits": r_dsatur.vertex_visits,
            "color_checks": r_dsatur.color_checks,
            "valid": r_dsatur.valid,
        })

        # 4. DSATUR (Heap Variant)
        r_dsatur_heap = dsatur(adj, deterministic=True, use_heap=True)
        results.append({
            "graph_name": name,
            "vertices": v_count,
            "edges": e_count,
            "algorithm": "DSATUR_Heap",
            "colors": r_dsatur_heap.color_count,
            "time_ms": r_dsatur_heap.execution_time_ms,
            "vertex_visits": r_dsatur_heap.vertex_visits,
            "color_checks": r_dsatur_heap.color_checks,
            "valid": r_dsatur_heap.valid,
        })

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Graph Coloring Algorithms Suite")
    parser.add_argument("--sizes", nargs="+", type=int, default=[50, 100, 250, 500])
    parser.add_argument("--output", type=str, default=None, help="Optional output CSV path")
    args = parser.parse_args()

    print(f"Running benchmark across sizes: {args.sizes}...")
    start_total = time.perf_counter()
    results = benchmark_suite(args.sizes)
    total_duration = time.perf_counter() - start_total

    print(f"\nBenchmark completed in {total_duration:.2f} seconds ({len(results)} runs).")

    # Format output
    headers = [
        "graph_name",
        "vertices",
        "edges",
        "algorithm",
        "colors",
        "time_ms",
        "vertex_visits",
        "color_checks",
        "valid",
    ]

    out_stream = io.StringIO()
    writer = csv.DictWriter(out_stream, fieldnames=headers)
    writer.writeheader()
    writer.writerows(results)
    csv_content = out_stream.getvalue()

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            f.write(csv_content)
        print(f"Saved benchmark CSV to {args.output}")
    else:
        print("\nBenchmark Summary (first 12 rows):")
        lines = csv_content.strip().split("\n")
        for line in lines[:13]:
            print(line)


if __name__ == "__main__":
    main()
