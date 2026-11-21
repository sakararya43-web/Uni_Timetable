import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Layers,
  Users,
  BookOpen,
  Network,
  Clock,
  Sparkles,
  Upload,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { api } from "../services/api";
import { SchedulingCycle, CycleSummaryReport } from "../types/api";
import { Badge, BadgeVariant } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { StaleDataBanner } from "../components/common/StaleDataBanner";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { ImportWizardModal } from "../components/imports/ImportWizardModal";

const cycleStatusVariants: Record<string, BadgeVariant> = {
  draft: "neutral",
  generated: "info",
  reviewed: "warning",
  published: "success",
  archived: "default",
};

export const OverviewPage: React.FC = () => {
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [summary, setSummary] = useState<CycleSummaryReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRebuilding, setIsRebuilding] = useState<boolean>(false);
  const [isImportOpen, setIsImportOpen] = useState<boolean>(false);

  const fetchCycles = async () => {
    try {
      const data = await api.get<SchedulingCycle[]>("/api/v1/cycles");
      setCycles(data);
      if (data.length > 0 && !selectedCycleId) {
        setSelectedCycleId(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load cycles:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSummary = async (cycleId: string) => {
    if (!cycleId) return;
    try {
      const data = await api.get<CycleSummaryReport>(`/api/v1/cycles/${cycleId}/reports/summary`);
      setSummary(data);
    } catch (err) {
      console.error("Failed to load cycle summary:", err);
    }
  };

  useEffect(() => {
    fetchCycles();
  }, []);

  useEffect(() => {
    if (selectedCycleId) {
      fetchSummary(selectedCycleId);
    }
  }, [selectedCycleId]);

  const handleRebuildGraph = async () => {
    if (!selectedCycleId) return;
    setIsRebuilding(true);
    try {
      await api.post(`/api/v1/cycles/${selectedCycleId}/graph/build`);
      await fetchSummary(selectedCycleId);
      await fetchCycles();
    } catch (err) {
      console.error("Failed to rebuild graph:", err);
    } finally {
      setIsRebuilding(false);
    }
  };

  const activeCycle = cycles.find((c) => c.id === selectedCycleId);

  return (
    <div className="space-y-6">
      {/* Top Banner & Active Cycle Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">University Timetable Operations</h1>
            {activeCycle && (
              <Badge variant={cycleStatusVariants[activeCycle.status] || "default"}>
                {activeCycle.status.toUpperCase()}
              </Badge>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time conflict graph intelligence, coloring scheduling, and examination publications.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label htmlFor="cycle-select" className="text-xs font-semibold text-slate-600 whitespace-nowrap">
            Active Cycle:
          </label>
          <select
            id="cycle-select"
            value={selectedCycleId}
            onChange={(e) => setSelectedCycleId(e.target.value)}
            className="px-3 py-1.5 text-xs font-medium bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {cycles.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stale Data Alert */}
      {activeCycle && (
        <StaleDataBanner
          isStale={activeCycle.graphStale}
          onRebuildGraph={handleRebuildGraph}
          isRebuilding={isRebuilding}
        />
      )}

      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <>
          {/* Key Performance Indicators Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase text-slate-500">Exams</span>
                <BookOpen className="w-4 h-4 text-blue-500" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{summary?.totalExams ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-1">Subjects: {summary?.totalSubjects ?? 0}</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase text-slate-500">Students</span>
                <Users className="w-4 h-4 text-indigo-500" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{summary?.totalStudents ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-1">Enrollments: {summary?.totalEnrollments ?? 0}</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase text-slate-500">Graph Vertices</span>
                <Network className="w-4 h-4 text-emerald-500" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{summary?.graphVertices ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-1">Edges: {summary?.graphEdges ?? 0}</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase text-slate-500">Avg Degree</span>
                <Layers className="w-4 h-4 text-amber-500" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{summary?.averageDegree ?? 0.0}</p>
              <p className="text-[11px] text-slate-400 mt-1">Conflict Density</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase text-slate-500">Time Slots</span>
                <Clock className="w-4 h-4 text-purple-500" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{summary?.totalSlots ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-1">Slots Used: {summary?.slotsUsed ?? 0}</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase text-slate-500">Published</span>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {summary?.latestPublishedVersion ? `v${summary.latestPublishedVersion}` : "None"}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                {summary?.latestPublishedAt ? new Date(summary.latestPublishedAt).toLocaleDateString() : "Draft mode"}
              </p>
            </div>
          </div>

          {/* Quick Actions & Navigation Pathways */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-slate-800 font-bold text-sm mb-1">
                  <Upload className="w-4 h-4 text-blue-600" />
                  <span>Bulk Import Academic Data</span>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Upload CSV spreadsheets of subjects, registered students, and examination enrollments.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => setIsImportOpen(true)}
              >
                Launch Import Wizard
              </Button>
            </div>

            <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-slate-800 font-bold text-sm mb-1">
                  <Network className="w-4 h-4 text-emerald-600" />
                  <span>Interactive Conflict Graph</span>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Inspect pairwise student examination conflicts, graph degree distribution, and clusters.
                </p>
              </div>
              <Link to="/graph">
                <Button variant="outline" size="sm" className="w-full" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Explore Graph Visualizer
                </Button>
              </Link>
            </div>

            <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-slate-800 font-bold text-sm mb-1">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span>Automated Timetable Generation</span>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Run DSATUR, Welsh–Powell, or Greedy algorithms to create clash-free candidate timetables.
                </p>
              </div>
              <Link to="/generate">
                <Button variant="primary" size="sm" className="w-full" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Generate Timetable
                </Button>
              </Link>
            </div>
          </div>
        </>
      )}

      {/* CSV Import Wizard Modal */}
      <ImportWizardModal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        cycleId={selectedCycleId}
        onSuccess={() => {
          fetchSummary(selectedCycleId);
          fetchCycles();
        }}
      />
    </div>
  );
};
