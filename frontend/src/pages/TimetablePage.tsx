import React, { useEffect, useState, useMemo } from "react";
import {
  Calendar,
  Lock,
  Printer,
  Search,
  FileSpreadsheet,
  FileText,
} from "lucide-react";
import { api } from "../services/api";
import { SchedulingCycle, ScheduleVersionSummary, ScheduleVersionDetail, ExamAssignmentItem } from "../types/api";
import { Button } from "../components/ui/Button";
import { Badge, BadgeVariant } from "../components/ui/Badge";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

const statusVariants: Record<string, BadgeVariant> = {
  Candidate: "warning",
  Reviewed: "info",
  Published: "success",
  Archived: "default",
};

export const TimetablePage: React.FC = () => {
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [versions, setVersions] = useState<ScheduleVersionSummary[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");
  const [versionDetail, setVersionDetail] = useState<ScheduleVersionDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDept, setSelectedDept] = useState("");

  useEffect(() => {
    api.get<SchedulingCycle[]>("/api/v1/cycles")
      .then((data) => {
        setCycles(data);
        if (data.length > 0) setSelectedCycleId(data[0].id);
      })
      .catch((err) => console.error("Error loading cycles:", err));
  }, []);

  useEffect(() => {
    if (!selectedCycleId) return;
    setIsLoading(true);
    api.get<ScheduleVersionSummary[]>(`/api/v1/cycles/${selectedCycleId}/schedules`)
      .then((data) => {
        setVersions(data);
        if (data.length > 0) {
          setSelectedVersionId(data[0].id);
        } else {
          setSelectedVersionId("");
          setVersionDetail(null);
        }
      })
      .catch((err) => console.error("Error loading versions:", err))
      .finally(() => setIsLoading(false));
  }, [selectedCycleId]);

  useEffect(() => {
    if (!selectedVersionId) return;
    setIsLoading(true);
    api.get<ScheduleVersionDetail>(`/api/v1/schedules/${selectedVersionId}`)
      .then((data) => setVersionDetail(data))
      .catch((err) => console.error("Error loading version detail:", err))
      .finally(() => setIsLoading(false));
  }, [selectedVersionId]);

  const handleExport = (type: "csv" | "pdf" | "excel") => {
    if (!selectedVersionId) return;
    window.open(`/api/v1/schedules/${selectedVersionId}/export/${type}`, "_blank");
  };

  const handlePrint = () => {
    window.print();
  };

  // Group assignments into calendar grid: Date -> Session -> Exams[]
  const gridData = useMemo(() => {
    if (!versionDetail || !versionDetail.assignments) return {};

    const filtered = versionDetail.assignments.filter((a) => {
      const matchSearch =
        a.subjectCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
        a.subjectName.toLowerCase().includes(searchTerm.toLowerCase());
      const matchDept = !selectedDept || a.departmentCode === selectedDept;
      return matchSearch && matchDept;
    });

    const grid: Record<string, Record<string, ExamAssignmentItem[]>> = {};
    for (const a of filtered) {
      const d = a.slotDate;
      const s = a.sessionLabel || "Morning";
      if (!grid[d]) grid[d] = {};
      if (!grid[d][s]) grid[d][s] = [];
      grid[d][s].push(a);
    }
    return grid;
  }, [versionDetail, searchTerm, selectedDept]);

  const sortedDates = Object.keys(gridData).sort();
  const sessionLabels = ["Morning", "Afternoon"];

  return (
    <div className="space-y-6">
      {/* Top Header & Actions (hidden on print) */}
      <div className="print:hidden flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold text-slate-900">Examination Timetable Grid</h1>
            {versionDetail && (
              <Badge variant={statusVariants[versionDetail.status] || "default"}>
                {versionDetail.status.toUpperCase()}
              </Badge>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Published and candidate examination assignments distributed across calendar sessions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Cycle Picker */}
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

          {/* Version Switcher */}
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

          {/* Export Dropdown Actions */}
          <Button
            variant="outline"
            size="sm"
            leftIcon={<FileText className="w-3.5 h-3.5" />}
            onClick={() => handleExport("pdf")}
          >
            PDF
          </Button>
          <Button
            variant="outline"
            size="sm"
            leftIcon={<FileSpreadsheet className="w-3.5 h-3.5" />}
            onClick={() => handleExport("csv")}
          >
            CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Printer className="w-3.5 h-3.5" />}
            onClick={handlePrint}
          >
            Print
          </Button>
        </div>
      </div>

      {/* Filter Bar (hidden on print) */}
      <div className="print:hidden flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search exam by subject code or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Departments</option>
          <option value="CS">Computer Science (CS)</option>
          <option value="EE">Electrical Engineering (EE)</option>
        </select>
      </div>

      {/* Print-Only Header */}
      <div className="hidden print:block mb-6 border-b pb-4">
        <h1 className="text-xl font-bold">University Examination Timetable</h1>
        <p className="text-xs text-slate-600">
          Cycle: {cycles.find((c) => c.id === selectedCycleId)?.name} | Version:{" "}
          {versionDetail?.versionNumber} ({versionDetail?.status})
        </p>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : !versionDetail || sortedDates.length === 0 ? (
        <EmptyState
          title="No Schedule Version Available"
          description="Generate a schedule or choose another cycle to view the timetable."
        />
      ) : (
        /* Calendar Timetable Grid */
        <div className="space-y-6">
          {sortedDates.map((dateStr) => (
            <div key={dateStr} className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-2.5 bg-slate-100 border-b border-slate-200 flex items-center justify-between">
                <span className="font-bold text-xs text-slate-800 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-blue-600" />
                  {new Date(dateStr + "T00:00:00").toLocaleDateString(undefined, {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </span>
                <span className="text-[11px] font-mono text-slate-500">{dateStr}</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200">
                {sessionLabels.map((sess) => {
                  const examsInSession = gridData[dateStr]?.[sess] || [];
                  return (
                    <div key={sess} className="p-4 space-y-3">
                      <div className="flex items-center justify-between pb-1.5 border-b border-slate-100">
                        <span className="text-xs font-bold uppercase text-slate-600">{sess} Session</span>
                        <span className="text-[10px] font-semibold text-slate-400">
                          {examsInSession.length} Exams
                        </span>
                      </div>

                      {examsInSession.length === 0 ? (
                        <p className="text-[11px] text-slate-400 italic py-2">No examinations scheduled</p>
                      ) : (
                        <div className="space-y-2">
                          {examsInSession.map((exam) => (
                            <div
                              key={exam.id}
                              className="p-3 bg-slate-50 border border-slate-200 rounded-lg hover:border-blue-400 transition-colors"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-mono font-bold text-xs text-blue-700">
                                  {exam.subjectCode}
                                </span>
                                <div className="flex items-center gap-1.5">
                                  {exam.locked && (
                                    <span title="Locked Assignment" className="text-amber-600">
                                      <Lock className="w-3.5 h-3.5" />
                                    </span>
                                  )}
                                  <span className="text-[10px] font-medium px-1.5 py-0.2 bg-white border border-slate-300 rounded text-slate-600">
                                    {exam.durationMinutes}m
                                  </span>
                                </div>
                              </div>
                              <p className="text-xs font-medium text-slate-800 mt-1 truncate">
                                {exam.subjectName}
                              </p>
                              <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 pt-1 border-t border-slate-200/60 font-mono">
                                <span>{exam.startTime} - {exam.endTime}</span>
                                <span>{exam.departmentCode || "GEN"}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
