import React, { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { api } from "../services/api";
import { SchedulingCycle, TimeSlot } from "../types/api";
import { Badge, BadgeVariant } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { Input } from "../components/ui/Input";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

const cycleStatusVariants: Record<string, BadgeVariant> = {
  draft: "neutral",
  generated: "info",
  reviewed: "warning",
  published: "success",
  archived: "default",
};

export const CyclesPage: React.FC = () => {
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [academicYears, setAcademicYears] = useState<Array<{ id: string; name: string }>>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);
  const [previewSlots, setPreviewSlots] = useState<TimeSlot[]>([]);
  const [selectedCycle, setSelectedCycle] = useState<SchedulingCycle | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [startDate, setStartDate] = useState("2026-12-01");
  const [endDate, setEndDate] = useState("2026-12-15");
  const [selectedDays, setSelectedDays] = useState<number[]>([1, 2, 3, 4, 5]); // Mon-Fri
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchCyclesAndYears = async () => {
    setIsLoading(true);
    try {
      const [cyclesData, yearsData] = await Promise.all([
        api.get<SchedulingCycle[] | { items: SchedulingCycle[] }>("/api/v1/cycles"),
        api.get<Array<{ id: string; name: string }>>("/api/v1/academic/years"),
      ]);
      const list = Array.isArray(cyclesData) ? cyclesData : (cyclesData as any)?.items || [];
      setCycles(list);
      setAcademicYears(yearsData);
      if (yearsData.length > 0 && !academicYearId) {
        setAcademicYearId(yearsData[0].id);
      }
    } catch (err) {
      console.error("Error fetching cycle data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCyclesAndYears();
  }, []);

  const handleCreateCycle = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const payload = {
        name,
        academic_year_id: academicYearId,
        academicYearId: academicYearId,
        start_date: startDate,
        startDate: startDate,
        end_date: endDate,
        endDate: endDate,
        configuration: {
          startDate: startDate,
          endDate: endDate,
          start_date: startDate,
          end_date: endDate,
          examDaysOfWeek: selectedDays,
          sessions: [
            { label: "Morning", startTime: "09:00", endTime: "12:00", enabled: true },
            { label: "Afternoon", startTime: "14:00", endTime: "17:00", enabled: true },
          ],
          maxExamsPerSession: 50,
          maxExamsPerDay: 100,
        },
      };

      const res = await api.post<SchedulingCycle>("/api/v1/cycles", payload);
      setIsCreateOpen(false);
      setName("");
      setSuccessMsg(`Scheduling cycle "${res?.name || name}" created successfully!`);
      setTimeout(() => setSuccessMsg(null), 5000);
      await fetchCyclesAndYears();
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMsg(error.message || "Failed to create cycle.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGenerateSlots = async (cycleId: string) => {
    try {
      await api.post(`/api/v1/cycles/${cycleId}/slots/generate`);
      setSuccessMsg("Examination time slots generated successfully!");
      setTimeout(() => setSuccessMsg(null), 4000);
      await fetchCyclesAndYears();
    } catch (err) {
      console.error("Failed to generate slots:", err);
    }
  };

  const handleViewSlots = async (cycle: SchedulingCycle) => {
    setSelectedCycle(cycle);
    try {
      const slots = await api.get<TimeSlot[]>(`/api/v1/cycles/${cycle.id}/slots`);
      setPreviewSlots(slots);
      setIsPreviewOpen(true);
    } catch (err) {
      console.error("Failed to fetch slots:", err);
    }
  };

  const toggleDay = (dayIndex: number) => {
    setSelectedDays((prev) =>
      prev.includes(dayIndex) ? prev.filter((d) => d !== dayIndex) : [...prev, dayIndex].sort()
    );
  };

  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Scheduling Cycles & Time Slots</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure examination periods, daily session layouts, and calendar slot templates.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setIsCreateOpen(true)}
        >
          New Scheduling Cycle
        </Button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between shadow-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium">{successMsg}</span>
          </div>
          <button
            onClick={() => setSuccessMsg(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-4"
          >
            &times;
          </button>
        </div>
      )}

      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : cycles.length === 0 ? (
        <EmptyState
          title="No Scheduling Cycles Found"
          description="Create your first examination cycle to configure exam date ranges and generate slot templates."
          actionLabel="Create Cycle"
          onAction={() => setIsCreateOpen(true)}
        />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                <th className="py-3 px-4">Cycle Name</th>
                <th className="py-3 px-4">Date Range</th>
                <th className="py-3 px-4">Sessions</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {cycles.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-900">{c.name}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-600">
                    {c.startDate} &rarr; {c.endDate}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="text-slate-600 font-medium">
                      {(c.configurationJson?.sessions || []).map((s) => s.label).join(", ") || "Standard 2-session"}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={cycleStatusVariants[c.status] || "default"}>
                      {c.status.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewSlots(c)}
                    >
                      View Slots
                    </Button>
                    {c.status === "draft" && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleGenerateSlots(c.id)}
                      >
                        Generate Slots
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Cycle Modal */}
      <Dialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Scheduling Cycle"
        description="Specify examination timeframe, active weekdays, and examination sessions."
        maxWidth="lg"
      >
        <form onSubmit={handleCreateCycle} className="space-y-4">
          {errorMsg && (
            <p className="p-2.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg">
              {errorMsg}
            </p>
          )}

          <Input
            label="Cycle Name"
            placeholder="e.g. Winter 2026 Examination Period"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Academic Year</label>
            <select
              value={academicYearId}
              onChange={(e) => setAcademicYearId(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              {academicYears.map((ay) => (
                <option key={ay.id} value={ay.id}>
                  {ay.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
            <Input
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Exam Days of Week</label>
            <div className="flex gap-2">
              {dayNames.map((dname, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => toggleDay(idx)}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                    selectedDays.includes(idx)
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {dname}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" size="md" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="md" type="submit" isLoading={isSubmitting}>
              Create Cycle
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Slots Preview Modal */}
      <Dialog
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        title={`Generated Time Slots (${selectedCycle?.name})`}
        description={`Total ${previewSlots.length} calendar slots available for exam mapping.`}
        maxWidth="xl"
      >
        <div className="max-h-96 overflow-y-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px] sticky top-0">
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Session</th>
                <th className="py-2.5 px-3">Timings</th>
                <th className="py-2.5 px-3">Duration</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {previewSlots.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-medium text-slate-900">{s.date}</td>
                  <td className="py-2 px-3 font-semibold text-slate-800">{s.sessionLabel}</td>
                  <td className="py-2 px-3 text-slate-600 font-mono">
                    {s.startTime} - {s.endTime}
                  </td>
                  <td className="py-2 px-3 text-slate-600">{s.durationMinutes}m</td>
                  <td className="py-2 px-3">
                    <span className="inline-block px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {s.enabled ? "ACTIVE" : "DISABLED"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Dialog>
    </div>
  );
};
