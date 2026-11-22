import React, { useEffect, useState } from "react";
import { FlaskConical, Play, CheckCircle, BarChart2, Info, Save } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from "recharts";
import { api } from "../services/api";
import { SchedulingCycle, unwrapCycles } from "../types/api";
import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";

interface AlgorithmComparisonRow {
  algorithm: string;
  colorsUsed: number;
  executionTimeMs: number;
  isValid: boolean;
  examsScheduled: number;
  unscheduledCount: number;
  largestClassSize: number;
  smallestClassSize: number;
  softScore: number;
  scheduleRunId: string;
}

interface CompareResponse {
  cycleId: string;
  graphSnapshotId: string;
  graphVertices: number;
  graphEdges: number;
  algorithms: AlgorithmComparisonRow[];
  notes: string[];
}

export const AlgorithmLabPage: React.FC = () => {
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [savingRunId, setSavingRunId] = useState<string | null>(null);

  useEffect(() => {
    api.get<SchedulingCycle[] | { items: SchedulingCycle[] }>("/api/v1/cycles")
      .then((data) => {
        const list = unwrapCycles(data);
        setCycles(list);
        if (list.length > 0) setSelectedCycleId(list[0].id);
      })
      .catch((err) => console.error("Error loading cycles:", err));
  }, []);

  const handleRunComparison = async () => {
    if (!selectedCycleId) return;
    setIsRunning(true);
    try {
      const data = await api.post<CompareResponse>(
        `/api/v1/cycles/${selectedCycleId}/schedule/compare`,
        { preserveLockedExams: true, repetitions: 5 }
      );
      setComparison(data);
    } catch (err) {
      console.error("Comparison run failed:", err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSaveAsCandidate = async (runId: string) => {
    setSavingRunId(runId);
    try {
      await api.post(`/api/v1/schedule-runs/${runId}/save`);
      alert("Candidate version saved successfully!");
    } catch (err) {
      console.error("Failed to save candidate:", err);
    } finally {
      setSavingRunId(null);
    }
  };

  const chartData = comparison?.algorithms.map((a) => ({
    name: a.algorithm.toUpperCase(),
    runtimeMs: a.executionTimeMs,
    colors: a.colorsUsed,
  }));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center gap-3">
          <FlaskConical className="w-5 h-5 text-indigo-600 flex-shrink-0" />
          <div>
            <h1 className="text-base font-bold text-slate-900">Algorithm Comparison Lab</h1>
            <p className="text-xs text-slate-500">
              Benchmark Greedy, Welsh–Powell, and DSATUR graph coloring algorithms on identical snapshot topology.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedCycleId}
            onChange={(e) => setSelectedCycleId(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {cycles.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          <Button
            variant="primary"
            size="sm"
            isLoading={isRunning}
            leftIcon={<Play className="w-3.5 h-3.5" />}
            onClick={handleRunComparison}
          >
            Run Comparison (5x Median)
          </Button>
        </div>
      </div>

      {/* Heuristic Honesty Banner (PRD FR-10) */}
      <div className="flex items-start gap-3 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900">
        <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-bold">Algorithmic Heuristic Note & Theoretical Limits</p>
          <p className="mt-0.5 text-amber-800">
            Results are heuristic approximations. Finding the optimal chromatic number is NP-hard. Wall-clock runtimes on small graphs reflect noise-level jitter. A coloring with fewer colors does not guarantee fewer real calendar slots due to duration restrictions.
          </p>
        </div>
      </div>

      {isRunning ? (
        <LoadingSkeleton rows={5} />
      ) : !comparison ? (
        <div className="p-12 text-center bg-white border border-dashed border-slate-300 rounded-xl">
          <FlaskConical className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-slate-800">No Comparison Run Loaded</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Click Run Comparison to execute all three algorithms against the current conflict graph snapshot.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* PRD Comparison Table */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between text-xs">
              <span className="font-bold text-slate-900">
                Comparison Results: |V| = {comparison.graphVertices}, |E| = {comparison.graphEdges}
              </span>
              <span className="text-slate-500 font-mono text-[11px]">
                Snapshot ID: {comparison.graphSnapshotId.slice(0, 8)}
              </span>
            </div>

            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                  <th className="py-3 px-4">Algorithm</th>
                  <th className="py-3 px-4">Colors Used</th>
                  <th className="py-3 px-4">Runtime (ms)</th>
                  <th className="py-3 px-4">Validity</th>
                  <th className="py-3 px-4">Scheduled</th>
                  <th className="py-3 px-4">Max/Min Class</th>
                  <th className="py-3 px-4">Soft Penalty</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {comparison.algorithms.map((a) => (
                  <tr key={a.algorithm} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-bold text-slate-900 capitalize">{a.algorithm}</td>
                    <td className="py-3 px-4 font-bold text-indigo-600">{a.colorsUsed} slots</td>
                    <td className="py-3 px-4 font-mono">{a.executionTimeMs} ms</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-bold">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                        Valid
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {a.examsScheduled} exams ({a.unscheduledCount} unassigned)
                    </td>
                    <td className="py-3 px-4">
                      {a.largestClassSize} / {a.smallestClassSize}
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-800">{a.softScore}</td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        leftIcon={<Save className="w-3.5 h-3.5" />}
                        isLoading={savingRunId === a.scheduleRunId}
                        onClick={() => handleSaveAsCandidate(a.scheduleRunId)}
                      >
                        Save Candidate
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Recharts Bar Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <h3 className="text-xs font-bold uppercase text-slate-700 mb-4 flex items-center gap-1.5">
                <BarChart2 className="w-4 h-4 text-indigo-600" />
                Color Classes / Slots Required
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="colors" fill="#6366f1" name="Slots / Colors" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <h3 className="text-xs font-bold uppercase text-slate-700 mb-4 flex items-center gap-1.5">
                <BarChart2 className="w-4 h-4 text-blue-600" />
                Wall-Clock Execution Time (ms)
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="runtimeMs" fill="#3b82f6" name="Time (ms)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
