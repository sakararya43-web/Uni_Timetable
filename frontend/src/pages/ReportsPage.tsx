import React, { useEffect, useState } from "react";
import { BarChart3, FileText, FileSpreadsheet } from "lucide-react";
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
import { SchedulingCycle, ScheduleVersionSummary, CycleSummaryReport } from "../types/api";
import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

interface ScheduleDistribution {
  scheduleVersionId: string;
  versionNumber: number;
  byDate: Array<{ date: string; examCount: number; studentSessions: number }>;
  bySession: Array<{ sessionLabel: string; examCount: number; studentSessions: number }>;
  multiExamDays: Array<{ examsPerDay: number; studentCount: number }>;
}

export const ReportsPage: React.FC = () => {
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [versions, setVersions] = useState<ScheduleVersionSummary[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");
  const [summary, setSummary] = useState<CycleSummaryReport | null>(null);
  const [distribution, setDistribution] = useState<ScheduleDistribution | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    setIsLoading(true);
    api.get<SchedulingCycle[]>("/api/v1/cycles")
      .then((data) => {
        setCycles(data);
        if (data.length > 0) {
          setSelectedCycleId(data[0].id);
        } else {
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error("Error loading cycles:", err);
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedCycleId) return;
    setIsLoading(true);
    Promise.all([
      api.get<CycleSummaryReport>(`/api/v1/cycles/${selectedCycleId}/reports/summary`),
      api.get<ScheduleVersionSummary[]>(`/api/v1/cycles/${selectedCycleId}/schedules`),
    ])
      .then(([sumData, verData]) => {
        setSummary(sumData);
        setVersions(verData);
        if (verData.length > 0) {
          setSelectedVersionId(verData[0].id);
        } else {
          setSelectedVersionId("");
          setDistribution(null);
        }
      })
      .catch((err) => console.error("Failed to load reports:", err))
      .finally(() => setIsLoading(false));
  }, [selectedCycleId]);

  useEffect(() => {
    if (!selectedVersionId) return;
    api.get<ScheduleDistribution>(`/api/v1/schedules/${selectedVersionId}/reports/distribution`)
      .then((data) => setDistribution(data))
      .catch((err) => console.error("Error loading distribution report:", err));
  }, [selectedVersionId]);

  const handleExport = (type: "csv" | "pdf" | "excel") => {
    if (!selectedVersionId) return;
    window.open(`/api/v1/schedules/${selectedVersionId}/export/${type}`, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-blue-600 flex-shrink-0" />
          <div>
            <h1 className="text-base font-bold text-slate-900">Institutional Analytics & Reports</h1>
            <p className="text-xs text-slate-500">
              Workload distributions, student density histograms, and timetable compliance audits.
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

          {versions.length > 0 && (
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(e.target.value)}
              className="px-3 py-1.5 text-xs font-bold bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  Version {v.versionNumber} ({v.status})
                </option>
              ))}
            </select>
          )}

          <Button
            variant="outline"
            size="sm"
            leftIcon={<FileText className="w-3.5 h-3.5" />}
            onClick={() => handleExport("pdf")}
          >
            PDF Report
          </Button>
          <Button
            variant="outline"
            size="sm"
            leftIcon={<FileSpreadsheet className="w-3.5 h-3.5" />}
            onClick={() => handleExport("csv")}
          >
            CSV Data
          </Button>
        </div>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <div className="space-y-6">
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-500">Total Exams</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">{summary?.totalExams ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">{summary?.totalSubjects ?? 0} Catalog Subjects</p>
            </div>
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-500">Total Students</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">{summary?.totalStudents ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">{summary?.totalEnrollments ?? 0} Enrollments</p>
            </div>
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-500">Conflict Graph Density</span>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                {summary ? `${(summary.averageDegree).toFixed(1)} avg deg` : "0.0"}
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">{summary?.graphEdges ?? 0} Conflict Edges</p>
            </div>
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-500">Slot Utilization</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {summary?.slotsUsed ?? 0} / {summary?.totalSlots ?? 0}
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">Time Slots Used</p>
            </div>
          </div>

          {/* Charts Grid */}
          {distribution ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Daily Workload Chart */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <h3 className="text-xs font-bold uppercase text-slate-700 mb-4">
                  Examination Load by Date
                </h3>
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distribution.byDate}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="examCount" fill="#3b82f6" name="Exams" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Session Load Chart */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <h3 className="text-xs font-bold uppercase text-slate-700 mb-4">
                  Session Distribution (Morning vs Afternoon)
                </h3>
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distribution.bySession}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="sessionLabel" tick={{ fontSize: 11 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="examCount" fill="#8b5cf6" name="Exams" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Multi-Exam Days Histogram */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm md:col-span-2">
                <h3 className="text-xs font-bold uppercase text-slate-700 mb-4">
                  Student Workload: Exams Scheduled on Same Day
                </h3>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distribution.multiExamDays}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis
                        dataKey="examsPerDay"
                        tick={{ fontSize: 11 }}
                        tickFormatter={(v) => `${v} Exam(s)/Day`}
                      />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="studentCount" fill="#10b981" name="Number of Students" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No Schedule Distribution Loaded"
              description="Save a candidate timetable version to view student workload distribution charts."
            />
          )}
        </div>
      )}
    </div>
  );
};
