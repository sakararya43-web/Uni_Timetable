import React, { useState } from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { api } from "../../services/api";

export interface PublishScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  versionId: string;
  versionNumber: number;
  cycleName: string;
  onSuccess: () => void;
}

export const PublishScheduleModal: React.FC<PublishScheduleModalProps> = ({
  isOpen,
  onClose,
  versionId,
  versionNumber,
  cycleName,
  onSuccess,
}) => {
  const [confirmCheckbox, setConfirmCheckbox] = useState(false);
  const [notes, setNotes] = useState("");
  const [isPublishing, setIsPublishing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handlePublish = async () => {
    if (!confirmCheckbox) return;
    setIsPublishing(true);
    setErrorMsg(null);

    try {
      await api.post(`/api/v1/schedules/${versionId}/publish`, {
        confirm: true,
        notes: notes.trim() || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to publish schedule version.");
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={`Publish Official Timetable: Version ${versionNumber}`}
      description={`Cycle: ${cycleName}`}
      maxWidth="md"
    >
      <div className="space-y-4">
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-900 space-y-1">
          <p className="font-bold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            Publication & Immutability Rules:
          </p>
          <ul className="list-disc list-inside space-y-0.5 text-blue-800 pl-1">
            <li>Once published, this timetable version becomes strictly immutable.</li>
            <li>Student self-service portals and downloads will activate immediately.</li>
            <li>Any prior published version for this cycle will be archived automatically.</li>
          </ul>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Publication Release Notes (Optional)
          </label>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Official Final Examination Schedule approved by Registrar"
            className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <label className="flex items-start gap-2.5 p-3 bg-slate-50 border border-slate-200 rounded-lg cursor-pointer">
          <input
            type="checkbox"
            checked={confirmCheckbox}
            onChange={(e) => setConfirmCheckbox(e.target.checked)}
            className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-xs text-slate-800 font-medium">
            I confirm that I have reviewed the clash-free validation report and authorize the publication of Version {versionNumber} as the official public timetable.
          </span>
        </label>

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" size="md" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            disabled={!confirmCheckbox}
            isLoading={isPublishing}
            onClick={handlePublish}
            leftIcon={<CheckCircle2 className="w-4 h-4" />}
          >
            Confirm & Publish
          </Button>
        </div>
      </div>
    </Dialog>
  );
};
