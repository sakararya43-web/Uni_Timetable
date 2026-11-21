import React, { useState } from "react";
import { RefreshCw, AlertTriangle } from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { api } from "../../services/api";

export interface RegenerateModalProps {
  isOpen: boolean;
  onClose: () => void;
  versionId: string;
  versionNumber: number;
  onSuccess: (newVersionId: string) => void;
}

export const RegenerateModal: React.FC<RegenerateModalProps> = ({
  isOpen,
  onClose,
  versionId,
  versionNumber,
  onSuccess,
}) => {
  const [mode, setMode] = useState<"full" | "unlocked_only">("unlocked_only");
  const [algorithm, setAlgorithm] = useState<"dsatur" | "welsh_powell" | "greedy">("dsatur");
  const [preserveLocks, setPreserveLocks] = useState<boolean>(true);
  const [minimizeDisruption, setMinimizeDisruption] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRegenerate = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await api.post<{ id: string; versionNumber: number }>(
        `/api/v1/schedules/${versionId}/regenerate`,
        {
          mode,
          algorithm,
          preserveLockedExams: preserveLocks,
          minimizeDisruption,
          autoRebuildGraph: true,
        }
      );
      onSuccess(res.id);
      onClose();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Schedule regeneration failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={`Regenerate Schedule from Version ${versionNumber}`}
      description="Produces a new Candidate version without altering historical schedules."
      maxWidth="md"
    >
      <div className="space-y-4 text-xs">
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div>
          <label className="block font-semibold text-slate-700 mb-1">Regeneration Mode</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setMode("unlocked_only")}
              className={`p-3 text-left border rounded-lg transition-all ${
                mode === "unlocked_only"
                  ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/20"
                  : "border-slate-200 text-slate-700 hover:border-slate-300"
              }`}
            >
              <p className="font-bold">Unlocked Only (Repair)</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Keeps locked exams fixed in place</p>
            </button>
            <button
              type="button"
              onClick={() => setMode("full")}
              className={`p-3 text-left border rounded-lg transition-all ${
                mode === "full"
                  ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/20"
                  : "border-slate-200 text-slate-700 hover:border-slate-300"
              }`}
            >
              <p className="font-bold">Full Recalculation</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Re-colors all vertices</p>
            </button>
          </div>
        </div>

        <div>
          <label className="block font-semibold text-slate-700 mb-1">Coloring Algorithm</label>
          <select
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value as typeof algorithm)}
            className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="dsatur">DSATUR (Saturation Degree)</option>
            <option value="welsh_powell">Welsh-Powell (Descending Degree)</option>
            <option value="greedy">Greedy (First-Fit)</option>
          </select>
        </div>

        <div className="space-y-2 pt-1">
          <label className="flex items-center gap-2 cursor-pointer text-slate-700">
            <input
              type="checkbox"
              checked={preserveLocks}
              onChange={(e) => setPreserveLocks(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Preserve Locked Assignments (Guaranteed slot stability)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer text-slate-700">
            <input
              type="checkbox"
              checked={minimizeDisruption}
              onChange={(e) => setMinimizeDisruption(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Minimize Disruption (Bias unlocked exams to previous slots)</span>
          </label>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
          <Button variant="secondary" size="md" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            isLoading={isSubmitting}
            onClick={handleRegenerate}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Regenerate Schedule
          </Button>
        </div>
      </div>
    </Dialog>
  );
};
