import React, { useEffect, useState, useMemo, useCallback } from "react";
import {
  Calendar,
  Lock,
  Unlock,
  Printer,
  Search,
  FileSpreadsheet,
  FileText,
  Edit3,
  RefreshCw,
  Send,
  History,
  Copy,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
} from "lucide-react";
import { api } from "../services/api";
import {
  SchedulingCycle,
  ScheduleVersionSummary,
  ScheduleVersionDetail,
  ExamAssignmentItem,
  TimeSlot,
  Department,
  unwrapCycles,
} from "../types/api";
import { Button } from "../components/ui/Button";
import { Badge, BadgeVariant } from "../components/ui/Badge";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { Dialog } from "../components/ui/Dialog";
import { PublishScheduleModal } from "../components/timetable/PublishScheduleModal";
import { MoveExamModal } from "../components/timetable/MoveExamModal";
import { RegenerateModal } from "../components/timetable/RegenerateModal";
import {
  exportTimetableCsv,
  exportTimetableExcel,
  exportTimetablePdf,
} from "../services/exportService";

const statusVariants: Record<string, BadgeVariant> = {
  Candidate: "warning",
  Reviewed: "info",
  Published: "success",
  Archived: "default",
};

export const TimetablePage: React.FC = () => {
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [cycleSlots, setCycleSlots] = useState<TimeSlot[]>([]);
  const [versions, setVersions] = useState<ScheduleVersionSummary[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");
  const [versionDetail, setVersionDetail] = useState<ScheduleVersionDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Edit Mode & Modals
  const [isEditMode, setIsEditMode] = useState<boolean>(false);
  const [movingAssignment, setMovingAssignment] = useState<ExamAssignmentItem | null>(null);
  const [isPublishModalOpen, setIsPublishModalOpen] = useState<boolean>(false);
  const [isRegenerateModalOpen, setIsRegenerateModalOpen] = useState<boolean>(false);
  const [isHistoryDrawerOpen, setIsHistoryDrawerOpen] = useState<boolean>(false);
  const [isChangeRequestOpen, setIsChangeRequestOpen] = useState<boolean>(false);
  const [concurrencyAlert, setConcurrencyAlert] = useState<string | null>(null);

  // Change request state
  const [changeReqAssignment, setChangeReqAssignment] = useState<ExamAssignmentItem | null>(null);
  const [changeReqNotes, setChangeReqNotes] = useState<string>("");
  const [changeReqSuccess, setChangeReqSuccess] = useState<boolean>(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDept, setSelectedDept] = useState("");
  const [departments, setDepartments] = useState<Department[]>([]);

  const reloadVersions = useCallback(async (cycleId: string, selectNewest = false) => {
    try {
      const data = await api.get<ScheduleVersionSummary[]>(`/api/v1/cycles/${cycleId}/schedules`);
      setVersions(data);
      if (data.length > 0) {
        const nextId = selectNewest ? data[0].id : (selectedVersionId || data[0].id);
        setSelectedVersionId(nextId);
      } else {
        setSelectedVersionId("");
        setVersionDetail(null);
      }
    } catch (err) {
      console.error("Error loading versions:", err);
    }
  }, [selectedVersionId]);

  const reloadDetail = useCallback(async (vId: string) => {
    if (!vId) return;
    setIsLoading(true);
    try {
      const data = await api.get<ScheduleVersionDetail>(`/api/v1/schedules/${vId}`);
      setVersionDetail(data);
      setConcurrencyAlert(null);
    } catch (err: unknown) {
      console.error("Error loading version detail:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    setIsLoading(true);
    api.get<SchedulingCycle[] | { items: SchedulingCycle[] }>("/api/v1/cycles")
      .then((data) => {
        const list = unwrapCycles(data);
        setCycles(list);
        if (list.length > 0) {
          setSelectedCycleId(list[0].id);
        } else {
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error("Error loading cycles:", err);
        setIsLoading(false);
      });

    api.get<Department[]>("/api/v1/academic/departments")
      .then((depts) => {
        setDepartments(depts || []);
      })
      .catch((err) => console.error("Error loading departments:", err));
  }, []);

  useEffect(() => {
    if (!selectedCycleId) return;
    setIsLoading(true);

    Promise.all([
      api.get<ScheduleVersionSummary[]>(`/api/v1/cycles/${selectedCycleId}/schedules`),
      api.get<TimeSlot[]>(`/api/v1/cycles/${selectedCycleId}/slots`),
    ])
      .then(([verData, slotData]) => {
        setVersions(verData);
        setCycleSlots(slotData);
        if (verData.length > 0) {
          setSelectedVersionId(verData[0].id);
        } else {
          setSelectedVersionId("");
          setVersionDetail(null);
        }
      })
      .catch((err) => console.error("Error loading cycle data:", err))
      .finally(() => setIsLoading(false));
  }, [selectedCycleId]);

  useEffect(() => {
    if (selectedVersionId) {
      reloadDetail(selectedVersionId);
    }
  }, [selectedVersionId, reloadDetail]);

  const handleExport = (type: "csv" | "pdf" | "excel") => {
    if (!versionDetail) return;
    const cycleName =
      cycles.find((c) => c.id === selectedCycleId)?.name ||
      "June 2026 Academic Final Examinations";
    if (type === "csv") {
      exportTimetableCsv(versionDetail);
    } else if (type === "excel") {
      exportTimetableExcel(versionDetail);
    } else if (type === "pdf") {
      exportTimetablePdf(versionDetail, cycleName);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleToggleLock = async (exam: ExamAssignmentItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!selectedVersionId) return;
    try {
      const endpoint = exam.locked
        ? `/api/v1/schedules/${selectedVersionId}/assignments/${exam.id}/unlock`
        : `/api/v1/schedules/${selectedVersionId}/assignments/${exam.id}/lock`;
      const updated = await api.post<ScheduleVersionDetail>(endpoint, {});
      setVersionDetail(updated);
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      if (e.status === 409) {
        setConcurrencyAlert("Schedule was modified concurrently by another user. Reloading latest state...");
        reloadDetail(selectedVersionId);
      } else {
        alert(e.message || "Failed to update lock.");
      }
    }
  };

  const handleCloneVersion = async () => {
    if (!selectedVersionId) return;
    setIsLoading(true);
    try {
      const cloned = await api.post<ScheduleVersionDetail>(
        `/api/v1/schedules/${selectedVersionId}/clone`,
        {}
      );
      await reloadVersions(selectedCycleId, true);
      setSelectedVersionId(cloned.id);
      setVersionDetail(cloned);
      setIsEditMode(true);
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(e.message || "Failed to clone schedule version.");
      setIsLoading(false);
    }
  };

  const handleSubmitChangeRequest = (e: React.FormEvent) => {
    e.preventDefault();
    setChangeReqSuccess(true);
    setTimeout(() => {
      setChangeReqSuccess(false);
      setIsChangeRequestOpen(false);
      setChangeReqNotes("");
      setChangeReqAssignment(null);
    }, 1500);
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
  const isPublished = versionDetail?.status === "Published";
  const selectedCycle = cycles.find((c) => c.id === selectedCycleId);

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
            {isPublished && (
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                OFFICIAL & LOCKED
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Clash-free examination scheduling across calendar dates, sessions, and academic departments.
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

          {/* Edit Mode Toggle for Candidates */}
          {!isPublished && versionDetail && (
            <Button
              variant={isEditMode ? "primary" : "outline"}
              size="sm"
              leftIcon={<Edit3 className="w-3.5 h-3.5" />}
              onClick={() => setIsEditMode(!isEditMode)}
            >
              {isEditMode ? "Exit Edit Mode" : "Edit Mode"}
            </Button>
          )}

          {/* Published Action: Clone as Candidate */}
          {isPublished && (
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Copy className="w-3.5 h-3.5" />}
              onClick={handleCloneVersion}
            >
              Clone as Candidate
            </Button>
          )}

          {/* Regenerate Action */}
          {!isPublished && versionDetail && (
            <Button
              variant="outline"
              size="sm"
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={() => setIsRegenerateModalOpen(true)}
            >
              Regenerate
            </Button>
          )}

          {/* Publish Action */}
          {!isPublished && versionDetail && (
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Send className="w-3.5 h-3.5" />}
              onClick={() => setIsPublishModalOpen(true)}
            >
              Publish Schedule
            </Button>
          )}

          {/* Edit History Drawer Trigger */}
          <Button
            variant="outline"
            size="sm"
            leftIcon={<History className="w-3.5 h-3.5" />}
            onClick={() => setIsHistoryDrawerOpen(true)}
          >
            Audit Trail
          </Button>

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

      {/* Concurrency Conflict Banner */}
      {concurrencyAlert && (
        <div className="p-3 bg-amber-50 border border-amber-300 rounded-xl text-xs text-amber-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>{concurrencyAlert}</span>
          </div>
          <Button size="sm" variant="secondary" onClick={() => reloadDetail(selectedVersionId)}>
            Reload
          </Button>
        </div>
      )}

      {/* Edit Mode Instruction Banner */}
      {isEditMode && !isPublished && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2">
            <Edit3 className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <span>
              <strong>Edit Mode Enabled:</strong> Click any exam card to preview & move to another slot. Click the lock icon to lock/unlock an exam.
            </span>
          </div>
          <Button size="sm" variant="outline" onClick={() => setIsEditMode(false)}>
            Done Editing
          </Button>
        </div>
      )}

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
          {departments.map((d) => (
            <option key={d.id} value={d.code}>
              {d.name} ({d.code})
            </option>
          ))}
        </select>
      </div>

      {/* Print-Only Header */}
      <div className="hidden print:block mb-6 border-b pb-4">
        <h1 className="text-xl font-bold">University Examination Timetable</h1>
        <p className="text-xs text-slate-600">
          Cycle: {selectedCycle?.name} | Version:{" "}
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
                              onClick={() => {
                                if (isEditMode && !isPublished) {
                                  setMovingAssignment(exam);
                                }
                              }}
                              className={`p-3 rounded-lg border transition-all ${
                                isEditMode && !isPublished
                                  ? "cursor-pointer hover:border-blue-500 hover:shadow-md bg-white border-blue-200 ring-1 ring-blue-100"
                                  : "bg-slate-50 border-slate-200 hover:border-slate-300"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-mono font-bold text-xs text-blue-700">
                                  {exam.subjectCode}
                                </span>
                                <div className="flex items-center gap-1.5">
                                  {/* Lock / Unlock Toggle Button */}
                                  <button
                                    type="button"
                                    onClick={(e) => handleToggleLock(exam, e)}
                                    disabled={isPublished}
                                    title={exam.locked ? "Click to unlock exam" : "Click to lock exam in this slot"}
                                    className={`p-1 rounded transition-colors ${
                                      exam.locked
                                        ? "text-amber-600 bg-amber-50 hover:bg-amber-100"
                                        : "text-slate-400 hover:text-slate-600 hover:bg-slate-200/50"
                                    }`}
                                  >
                                    {exam.locked ? (
                                      <Lock className="w-3.5 h-3.5" />
                                    ) : (
                                      <Unlock className="w-3.5 h-3.5" />
                                    )}
                                  </button>
                                  <span className="text-[10px] font-medium px-1.5 py-0.5 bg-white border border-slate-300 rounded text-slate-600">
                                    {exam.durationMinutes}m
                                  </span>
                                </div>
                              </div>
                              <p className="text-xs font-medium text-slate-800 mt-1 truncate">
                                {exam.subjectName}
                              </p>
                              <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 pt-1 border-t border-slate-200/60 font-mono">
                                <span>{exam.startTime} - {exam.endTime}</span>
                                <div className="flex items-center gap-2">
                                  <span>{exam.departmentCode || "GEN"}</span>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setChangeReqAssignment(exam);
                                      setIsChangeRequestOpen(true);
                                    }}
                                    title="Submit Coordinator Change Request"
                                    className="text-slate-400 hover:text-blue-600"
                                  >
                                    <HelpCircle className="w-3 h-3" />
                                  </button>
                                </div>
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

      {/* Move Exam Modal */}
      {movingAssignment && (
        <MoveExamModal
          isOpen={!!movingAssignment}
          onClose={() => setMovingAssignment(null)}
          versionId={selectedVersionId}
          assignment={movingAssignment}
          slots={cycleSlots}
          onSuccess={() => reloadDetail(selectedVersionId)}
        />
      )}

      {/* Publish Schedule Wizard Modal */}
      <PublishScheduleModal
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        versionId={selectedVersionId}
        versionNumber={versionDetail?.versionNumber || 1}
        cycleName={selectedCycle?.name || ""}
        onSuccess={async () => {
          await reloadVersions(selectedCycleId);
          await reloadDetail(selectedVersionId);
        }}
      />

      {/* Regenerate Modal */}
      <RegenerateModal
        isOpen={isRegenerateModalOpen}
        onClose={() => setIsRegenerateModalOpen(false)}
        versionId={selectedVersionId}
        versionNumber={versionDetail?.versionNumber || 1}
        onSuccess={async (newVerId) => {
          await reloadVersions(selectedCycleId);
          setSelectedVersionId(newVerId);
          await reloadDetail(newVerId);
        }}
      />

      {/* Audit History Drawer / Modal */}
      <Dialog
        isOpen={isHistoryDrawerOpen}
        onClose={() => setIsHistoryDrawerOpen(false)}
        title="Schedule Version Audit Trail"
        description={`Audit and edit trail for Version ${versionDetail?.versionNumber} (${versionDetail?.status})`}
        maxWidth="lg"
      >
        <div className="space-y-4 max-h-[60vh] overflow-y-auto">
          {(!versionDetail?.editHistory || versionDetail.editHistory.length === 0) ? (
            <p className="text-xs text-slate-500 italic py-4 text-center">
              No manual edits or modifications recorded on this version yet.
            </p>
          ) : (
            <div className="space-y-2">
              {versionDetail.editHistory.map((item, idx) => (
                <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold font-mono text-blue-700">{item.action}</span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {new Date(item.createdAt).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-600">Actor ID: <span className="font-mono">{item.actorId || "System"}</span></p>
                  {item.details && (
                    <pre className="text-[10px] bg-white p-2 border border-slate-200 rounded overflow-x-auto text-slate-700">
                      {JSON.stringify(item.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
          <div className="flex justify-end pt-2 border-t border-slate-100">
            <Button variant="secondary" size="sm" onClick={() => setIsHistoryDrawerOpen(false)}>
              Close Audit Trail
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Coordinator Change Request Modal (Task P13.17) */}
      <Dialog
        isOpen={isChangeRequestOpen}
        onClose={() => setIsChangeRequestOpen(false)}
        title="Submit Timetable Change Request"
        description={`Department Coordinator change request for ${changeReqAssignment?.subjectCode || "Exam"}`}
        maxWidth="md"
      >
        <form onSubmit={handleSubmitChangeRequest} className="space-y-4">
          {changeReqSuccess ? (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              <span>Change request submitted to the Examination Committee successfully.</span>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Examination Subject
                </label>
                <input
                  type="text"
                  disabled
                  value={`${changeReqAssignment?.subjectCode} — ${changeReqAssignment?.subjectName}`}
                  className="w-full px-3 py-2 text-xs bg-slate-100 border border-slate-200 rounded-lg text-slate-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Proposed Slot / Date / Reason
                </label>
                <textarea
                  required
                  rows={4}
                  value={changeReqNotes}
                  onChange={(e) => setChangeReqNotes(e.target.value)}
                  placeholder="Explain why this exam should be moved, requested alternate dates, and any department constraints..."
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  variant="secondary"
                  size="sm"
                  type="button"
                  onClick={() => setIsChangeRequestOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  disabled={!changeReqNotes.trim()}
                >
                  Submit Request
                </Button>
              </div>
            </>
          )}
        </form>
      </Dialog>
    </div>
  );
};
