import React, { useState } from "react";
import { Download, UploadCloud, AlertCircle, CheckCircle2, ArrowRight, ArrowLeft } from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { api } from "../../services/api";
import { ImportPreviewResponse } from "../../types/api";

export interface ImportWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  defaultType?: "subjects" | "students" | "enrollments";
  cycleId?: string;
}

export const ImportWizardModal: React.FC<ImportWizardModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  defaultType = "subjects",
  cycleId,
}) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [importType, setImportType] = useState<"subjects" | "students" | "enrollments">(defaultType);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const resetState = () => {
    setStep(1);
    setSelectedFile(null);
    setPreview(null);
    setErrorMsg(null);
  };

  const handleDownloadTemplate = async () => {
    try {
      const blob = await fetch(`/api/v1/imports/templates/${importType}`).then((r) => r.blob());
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `template_${importType}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error("Template download error:", err);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMsg(null);
    }
  };

  const handleUploadPreview = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (cycleId && importType === "enrollments") {
        formData.append("cycle_id", cycleId);
      }

      const res = await api.post<ImportPreviewResponse>(`/api/v1/imports/${importType}/preview`, formData);
      setPreview(res);
      setStep(3);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to validate import file.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!preview) return;
    setIsLoading(true);
    setErrorMsg(null);

    try {
      await api.post(`/api/v1/imports/batches/${preview.batchId}/commit`);
      if (onSuccess) onSuccess();
      onClose();
      resetState();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to commit import batch.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={() => {
        onClose();
        resetState();
      }}
      title={`Import Academic Data (${importType.toUpperCase()})`}
      description="Upload and validate bulk CSV records with schema and constraint verification."
      maxWidth="xl"
    >
      {/* Wizard Progress Stepper */}
      <div className="flex items-center justify-between mb-6 px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-600">
        <span className={step >= 1 ? "text-blue-600 font-bold" : ""}>1. Select & Template</span>
        <span>&rarr;</span>
        <span className={step >= 2 ? "text-blue-600 font-bold" : ""}>2. Upload CSV</span>
        <span>&rarr;</span>
        <span className={step >= 3 ? "text-blue-600 font-bold" : ""}>3. Validate & Commit</span>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 p-3 mb-4 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Step 1: Select Type & Template */}
      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2">Select Dataset Type</label>
            <div className="grid grid-cols-3 gap-3">
              {(["subjects", "students", "enrollments"] as const).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setImportType(type)}
                  className={`p-3 text-left border rounded-lg transition-all ${
                    importType === type
                      ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/20"
                      : "border-slate-200 hover:border-slate-300 text-slate-700"
                  }`}
                >
                  <p className="text-xs font-bold capitalize">{type}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    {type === "subjects" && "Courses, credits & durations"}
                    {type === "students" && "Roster numbers & accounts"}
                    {type === "enrollments" && "Cycle student course ties"}
                  </p>
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-800">RFC 4180 Template CSV</p>
              <p className="text-[11px] text-slate-500">Download the required columns and format specifications.</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Download className="w-3.5 h-3.5" />}
              onClick={handleDownloadTemplate}
            >
              Download Template
            </Button>
          </div>

          <div className="flex justify-end pt-4">
            <Button
              variant="primary"
              size="md"
              rightIcon={<ArrowRight className="w-4 h-4" />}
              onClick={() => setStep(2)}
            >
              Continue to Upload
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Upload CSV */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors">
            <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-800">Select or drag & drop CSV file</p>
            <p className="text-[11px] text-slate-500 mt-0.5 mb-4">UTF-8 encoded .csv files up to 10MB</p>

            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              id="csv-file-upload"
              className="hidden"
            />
            <label htmlFor="csv-file-upload">
              <span className="inline-flex items-center justify-center px-4 py-2 border border-slate-300 text-xs font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50 cursor-pointer shadow-sm">
                Browse Files
              </span>
            </label>
            {selectedFile && (
              <p className="mt-3 text-xs font-medium text-emerald-700">Selected: {selectedFile.name}</p>
            )}
          </div>

          <div className="flex items-center justify-between pt-4">
            <Button
              variant="secondary"
              size="md"
              leftIcon={<ArrowLeft className="w-4 h-4" />}
              onClick={() => setStep(1)}
            >
              Back
            </Button>
            <Button
              variant="primary"
              size="md"
              disabled={!selectedFile}
              isLoading={isLoading}
              onClick={handleUploadPreview}
            >
              Validate & Preview
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Validate & Preview */}
      {step === 3 && preview && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
              <p className="text-xs text-slate-500 font-medium">Total Rows</p>
              <p className="text-lg font-bold text-slate-900">{preview.totalRows}</p>
            </div>
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-center">
              <p className="text-xs text-emerald-700 font-medium">Valid Rows</p>
              <p className="text-lg font-bold text-emerald-800">{preview.validRows}</p>
            </div>
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-center">
              <p className="text-xs text-rose-700 font-medium">Invalid Rows</p>
              <p className="text-lg font-bold text-rose-800">{preview.invalidRows}</p>
            </div>
          </div>

          {preview.errors.length > 0 ? (
            <div>
              <p className="text-xs font-semibold text-rose-700 mb-1.5">Validation Errors Detected:</p>
              <div className="max-h-40 overflow-y-auto border border-rose-200 rounded-lg divide-y divide-rose-100 bg-rose-50/30">
                {preview.errors.map((err, i) => (
                  <div key={i} className="p-2.5 text-xs text-rose-900 flex items-start gap-2">
                    <span className="font-bold text-rose-700">Row {err.row}:</span>
                    <span>{err.message}</span>
                    {err.suggestion && <span className="text-slate-500 italic">({err.suggestion})</span>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-medium">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>All rows verified successfully without constraint conflicts. Ready to commit.</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-4">
            <Button
              variant="secondary"
              size="md"
              leftIcon={<ArrowLeft className="w-4 h-4" />}
              onClick={() => setStep(2)}
            >
              Re-upload File
            </Button>
            <Button
              variant="primary"
              size="md"
              disabled={preview.invalidRows > 0}
              isLoading={isLoading}
              onClick={handleCommit}
            >
              Commit to Database
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
};
