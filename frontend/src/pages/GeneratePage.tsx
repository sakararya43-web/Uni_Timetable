import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, CheckCircle, AlertTriangle, XCircle, ArrowRight, Save } from "lucide-react";
import { api } from "../services/api";
import { SchedulingCycle, unwrapCycles } from "../types/api";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";

interface ScheduleRunResult {
  id: string;
  schedulingCycleId: string;
  algorithm: string;
  executionTimeMs: number;
  colorsUsed: number;
  isValid: boolean;
  softScore: number;
  status: string;
  unscheduledExams?: string[];
  infeasibilityReason?: string;
  validationReport?: {
    valid: boolean;
    hardViolations: Array<{ message: string }>;
    softBreakdown: Array<{ rule: string; penalty: number }>;
  };
}

export const GeneratePage: React.FC = () => {
  const navigate = useNavigate();
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [algorithm, setAlgorithm] = useState<"dsatur" | "welsh_powell" | "greedy">("dsatur");
  const [preserveLocks, setPreserveLocks] = useState<boolean>(true);
  const [optimizeSoft, setOptimizeSoft] = useState<boolean>(false);
  const [deterministic, setDeterministic] = useState<boolean>(true);

  const [isLoadingCycles, setIsLoadingCycles] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<ScheduleRunResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    api.get<SchedulingCycle[] | { items: SchedulingCycle[] }>("/api/v1/cycles")
      .then((data) => {
        const list = unwrapCycles(data);
        setCycles(list);
        if (list.length > 0) setSelectedCycleId(list[0].id);
      })
      .catch((err) => console.error("Error loading cycles:", err))
      .finally(() => setIsLoadingCycles(false));
  }, []);

  const handleGenerate = async () => {
    if (!selectedCycleId) return;
    setIsGenerating(true);
    setErrorMsg(null);
    setRunResult(null);

    try {
      const payload = {
        algorithm,
        preserveLockedExams: preserveLocks,
        optimizeSoftConstraints: optimizeSoft,
        deterministic,
      };
      const res = await api.post<ScheduleRunResult>(
        `/api/v1/cycles/${selectedCycleId}/schedule/generate`,
        payload
      );
      setRunResult(res);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Schedule generation failed.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveCandidate = async () => {
    if (!runResult) return;
    setIsSaving(true);
    try {
      await api.post(`/api/v1/schedule-runs/${runResult.id}/save`);
      navigate("/timetable");
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to save candidate version.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div>
          <h1 className="text-base font-bold text-slate-900">Automated Timetable Generation Engine</h1>
          <p className="text-xs text-slate-500">
            Transforms graph coloring candidate classes into validated calendar timetables (PRD §13, FR-13).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="gen-cycle" className="text-xs font-semibold text-slate-600">
            Cycle:
          </label>
          <select
            id="gen-cycle"
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
        </div>
      </div>

      {isLoadingCycles ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1 space-y-4">
            {/* Algorithm Selector */}
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm space-y-3">
              <h2 className="text-xs font-bold uppercase text-slate-700">1. Select Algorithm</h2>
              <div className="space-y-2">
                {[
                  {
                    id: "dsatur",
                    name: "DSATUR (Primary)",
                    desc: "Dynamic saturation degree heuristic. Minimizes chromatic color count.",
                  },
                  {
                    id: "welsh_powell",
                    name: "Welsh-Powell",
                    desc: "Descending degree static ordering greedy coloring.",
                  },
                  {
                    id: "greedy",
                    name: "Greedy Coloring",
                    desc: "Natural ID sequence first-fit allocation.",
                  },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setAlgorithm(item.id as typeof algorithm)}
                    className={`w-full p-3 text-left border rounded-lg transition-all ${
                      algorithm === item.id
                        ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/20"
                        : "border-slate-200 hover:border-slate-300 text-slate-700"
                    }`}
                  >
                    <p className="text-xs font-bold">{item.name}</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">{item.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Optimization Options */}
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm space-y-3">
              <h2 className="text-xs font-bold uppercase text-slate-700">2. Run Parameters</h2>
              <div className="space-y-2 text-xs">
                <label className="flex items-center gap-2 cursor-pointer text-slate-700">
                  <input
                    type="checkbox"
                    checked={preserveLocks}
                    onChange={(e) => setPreserveLocks(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Preserve Locked Assignments</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-700">
                  <input
                    type="checkbox"
                    checked={optimizeSoft}
                    onChange={(e) => setOptimizeSoft(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Optimize Soft Constraints (Local Search)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-700">
                  <input
                    type="checkbox"
                    checked={deterministic}
                    onChange={(e) => setDeterministic(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Deterministic Tie-breaking (Reproducible)</span>
                </label>
              </div>

              <div className="pt-2">
                <Button
                  variant="primary"
                  size="md"
                  className="w-full"
                  isLoading={isGenerating}
                  onClick={handleGenerate}
                  leftIcon={<Sparkles className="w-4 h-4" />}
                >
                  Generate Timetable
                </Button>
              </div>
            </div>
          </div>

          {/* Results & Inspection Panel */}
          <div className="lg:col-span-2 space-y-4">
            {errorMsg && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2">
                <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">Generation Stopped</p>
                  <p className="mt-0.5">{errorMsg}</p>
                </div>
              </div>
            )}

            {!runResult && !errorMsg && (
              <div className="p-12 text-center bg-white border border-dashed border-slate-300 rounded-xl">
                <Sparkles className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <h3 className="text-sm font-semibold text-slate-800">Ready to Generate</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                  Select an algorithm and click Generate Timetable to produce a conflict-free candidate schedule.
                </p>
              </div>
            )}

            {runResult && (
              <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Generation Result</h3>
                    <p className="text-xs text-slate-500 font-mono">Run ID: {runResult.id.slice(0, 8)}</p>
                  </div>
                  <Badge
                    variant={
                      runResult.status === "success"
                        ? "success"
                        : runResult.status === "infeasible"
                        ? "danger"
                        : "warning"
                    }
                  >
                    {runResult.status.toUpperCase()}
                  </Badge>
                </div>

                <div className="grid grid-cols-4 gap-3 text-center">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Colors Used</span>
                    <span className="text-lg font-bold text-slate-900 block mt-0.5">{runResult.colorsUsed}</span>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Runtime</span>
                    <span className="text-lg font-bold text-slate-900 block mt-0.5">{runResult.executionTimeMs} ms</span>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Hard Validity</span>
                    <span className="text-lg font-bold text-emerald-600 block mt-0.5">
                      {runResult.isValid ? "100% PASS" : "CLASH"}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Soft Penalty</span>
                    <span className="text-lg font-bold text-slate-900 block mt-0.5">{runResult.softScore}</span>
                  </div>
                </div>

                {runResult.isValid ? (
                  <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-medium">
                    <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>0 student timetable clashes detected. All examinations assigned to valid calendar slots.</span>
                  </div>
                ) : (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs space-y-1">
                    <p className="font-bold flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-rose-600" />
                      Infeasibility Detected:
                    </p>
                    <p>{runResult.infeasibilityReason || "Color classes exceeded available calendar slots."}</p>
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <Button
                    variant="primary"
                    size="md"
                    isLoading={isSaving}
                    disabled={!runResult.isValid}
                    onClick={handleSaveCandidate}
                    leftIcon={<Save className="w-4 h-4" />}
                    rightIcon={<ArrowRight className="w-4 h-4" />}
                  >
                    Save as Candidate & View Timetable
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
