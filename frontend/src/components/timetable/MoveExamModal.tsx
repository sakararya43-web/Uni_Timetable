import React, { useState } from "react";
import { ArrowRight, AlertTriangle, CheckCircle } from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { api } from "../../services/api";
import { ExamAssignmentItem, TimeSlot } from "../../types/api";

export interface MoveExamModalProps {
  isOpen: boolean;
  onClose: () => void;
  versionId: string;
  assignment: ExamAssignmentItem | null;
  slots: TimeSlot[];
  onSuccess: () => void;
}

interface PreviewResult {
  valid: boolean;
  softScoreDelta: number;
  conflictingExams: Array<{ code: string; sharedStudentCount: number }>;
  reason?: string;
}

export const MoveExamModal: React.FC<MoveExamModalProps> = ({
  isOpen,
  onClose,
  versionId,
  assignment,
  slots,
  onSuccess,
}) => {
  const [targetSlotId, setTargetSlotId] = useState<string>("");
  const [isPreviewing, setIsPreviewing] = useState<boolean>(false);
  const [isCommitting, setIsCommitting] = useState<boolean>(false);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!assignment) return null;

  const handlePreview = async () => {
    if (!targetSlotId) return;
    setIsPreviewing(true);
    setErrorMsg(null);
    setPreview(null);

    try {
      const res = await api.post<PreviewResult>(
        `/api/v1/schedules/${versionId}/assignments/${assignment.id}/preview-move`,
        { targetSlotId }
      );
      setPreview(res);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to preview assignment move.");
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleConfirmMove = async () => {
    if (!targetSlotId) return;
    setIsCommitting(true);
    setErrorMsg(null);

    try {
      await api.patch(
        `/api/v1/schedules/${versionId}/assignments/${assignment.id}`,
        { timeSlotId: targetSlotId }
      );
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to move assignment.");
    } finally {
      setIsCommitting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={`Move Examination: ${assignment.subjectCode}`}
      description={`${assignment.subjectName} · Current: ${assignment.slotDate} (${assignment.sessionLabel})`}
      maxWidth="md"
    >
      <div className="space-y-4">
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Choose Destination Slot
          </label>
          <select
            value={targetSlotId}
            onChange={(e) => {
              setTargetSlotId(e.target.value);
              setPreview(null);
            }}
            className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select destination date and session...</option>
            {slots.map((s) => (
              <option key={s.id} value={s.id}>
                {s.date} · {s.sessionLabel} ({s.startTime} - {s.endTime})
              </option>
            ))}
          </select>
        </div>

        {/* Dry-run validation preview */}
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            disabled={!targetSlotId}
            isLoading={isPreviewing}
            onClick={handlePreview}
          >
            Preview Move & Check Clashes
          </Button>
        </div>

        {preview && (
          <div
            className={`p-3.5 rounded-lg border text-xs space-y-2 ${
              preview.valid
                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                : "bg-rose-50 border-rose-200 text-rose-900"
            }`}
          >
            <div className="flex items-center gap-2 font-bold">
              {preview.valid ? (
                <>
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span>Valid Move: Zero Student Clashes</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-rose-600" />
                  <span>Invalid Move: Student Timetable Clash</span>
                </>
              )}
            </div>

            {preview.valid ? (
              <p className="text-[11px] text-emerald-800">
                Moving {assignment.subjectCode} to this slot is safe. Soft-constraint penalty delta:{" "}
                <span className="font-mono font-bold">
                  {preview.softScoreDelta > 0 ? `+${preview.softScoreDelta}` : preview.softScoreDelta}
                </span>
              </p>
            ) : (
              <div>
                <p className="text-[11px] text-rose-800 mb-1.5">{preview.reason}</p>
                {preview.conflictingExams.map((ce, i) => (
                  <p key={i} className="text-[11px] font-semibold text-rose-700">
                    Clashes with {ce.code} ({ce.sharedStudentCount} shared students)
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <Button variant="secondary" size="md" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            disabled={!preview || !preview.valid}
            isLoading={isCommitting}
            onClick={handleConfirmMove}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Confirm Move
          </Button>
        </div>
      </div>
    </Dialog>
  );
};
