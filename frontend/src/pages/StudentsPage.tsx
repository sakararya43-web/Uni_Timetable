import React, { useEffect, useState } from "react";
import { Plus, Search, Upload, ShieldAlert, CheckCircle, RefreshCw } from "lucide-react";
import { api } from "../services/api";
import { Student, Department, SchedulingCycle } from "../types/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Dialog } from "../components/ui/Dialog";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ImportWizardModal } from "../components/imports/ImportWizardModal";

interface DiagnosticReport {
  valid: boolean;
  totalEnrollments: number;
  duplicateEnrollments: Array<{ studentId: string; subjectId: string; count: number }>;
  orphanStudents: number;
  orphanSubjects: number;
}

export const StudentsPage: React.FC = () => {
  const [tab, setTab] = useState<"roster" | "diagnostics">("roster");
  const [students, setStudents] = useState<Student[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDeptId, setSelectedDeptId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);

  // Diagnostic state
  const [diagnosticReport, setDiagnosticReport] = useState<DiagnosticReport | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Student Form
  const [studentNumber, setStudentNumber] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [semester, setSemester] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [studs, depts, cycs] = await Promise.all([
        api.get<Student[]>("/api/v1/students"),
        api.get<Department[]>("/api/v1/academic/departments"),
        api.get<SchedulingCycle[]>("/api/v1/cycles"),
      ]);
      setStudents(studs);
      setDepartments(depts);
      setCycles(cycs);
      if (depts.length > 0 && !departmentId) setDepartmentId(depts[0].id);
      if (cycs.length > 0 && !selectedCycleId) setSelectedCycleId(cycs[0].id);
    } catch (err) {
      console.error("Failed to load students:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      await api.post("/api/v1/students", {
        student_number: studentNumber,
        full_name: fullName,
        email,
        department_id: departmentId,
        semester,
      });
      setIsCreateOpen(false);
      setStudentNumber("");
      setFullName("");
      setEmail("");
      fetchData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to create student.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunDiagnostics = async () => {
    if (!selectedCycleId) return;
    setIsValidating(true);
    try {
      const report = await api.get<DiagnosticReport>(`/api/v1/enrollments/validate?cycle_id=${selectedCycleId}`);
      setDiagnosticReport(report);
    } catch (err) {
      console.error("Failed to run diagnostic report:", err);
    } finally {
      setIsValidating(false);
    }
  };

  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      s.studentNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDept = !selectedDeptId || s.departmentId === selectedDeptId;
    return matchesSearch && matchesDept;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Student Directory & Enrollments</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage student registrations, academic cohorts, and cycle enrollment integrity.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => setIsImportOpen(true)}
          >
            Import CSV
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setIsCreateOpen(true)}
          >
            Add Student
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setTab("roster")}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all ${
            tab === "roster"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Students Roster ({students.length})
        </button>
        <button
          onClick={() => {
            setTab("diagnostics");
            if (!diagnosticReport) handleRunDiagnostics();
          }}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all ${
            tab === "diagnostics"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Enrollment Health Diagnostics
        </button>
      </div>

      {tab === "roster" ? (
        <>
          {/* Search & Filter */}
          <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-3 border border-slate-200 rounded-xl shadow-sm">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by student number, full name, or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={selectedDeptId}
              onChange={(e) => setSelectedDeptId(e.target.value)}
              className="w-full sm:w-56 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          {/* Students Table */}
          {isLoading ? (
            <LoadingSkeleton rows={5} />
          ) : filteredStudents.length === 0 ? (
            <EmptyState
              title="No Students Found"
              description="No student records match your query or none have been enrolled yet."
              actionLabel="Add Student"
              onAction={() => setIsCreateOpen(true)}
            />
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                    <th className="py-3 px-4">Student ID / Number</th>
                    <th className="py-3 px-4">Full Name</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Semester</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredStudents.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-900">{s.studentNumber}</td>
                      <td className="py-3.5 px-4 font-semibold text-slate-900">{s.fullName}</td>
                      <td className="py-3.5 px-4 text-slate-500">{s.email}</td>
                      <td className="py-3.5 px-4">{s.departmentCode || "GEN"}</td>
                      <td className="py-3.5 px-4">Sem {s.semester}</td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {s.status.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : (
        /* Diagnostics View */
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
            <div className="flex items-center gap-3">
              <label htmlFor="diag-cycle" className="text-xs font-semibold text-slate-700">
                Target Cycle:
              </label>
              <select
                id="diag-cycle"
                value={selectedCycleId}
                onChange={(e) => setSelectedCycleId(e.target.value)}
                className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg"
              >
                {cycles.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <Button
              variant="outline"
              size="sm"
              isLoading={isValidating}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={handleRunDiagnostics}
            >
              Re-run Diagnostic Scan
            </Button>
          </div>

          {diagnosticReport && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Total Enrollments</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{diagnosticReport.totalEnrollments}</p>
                </div>
                <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Duplicate Enrollments</p>
                  <p className={`text-2xl font-bold mt-1 ${diagnosticReport.duplicateEnrollments.length > 0 ? "text-rose-600" : "text-emerald-600"}`}>
                    {diagnosticReport.duplicateEnrollments.length}
                  </p>
                </div>
                <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Orphan References</p>
                  <p className={`text-2xl font-bold mt-1 ${diagnosticReport.orphanStudents + diagnosticReport.orphanSubjects > 0 ? "text-rose-600" : "text-emerald-600"}`}>
                    {diagnosticReport.orphanStudents + diagnosticReport.orphanSubjects}
                  </p>
                </div>
              </div>

              {diagnosticReport.valid ? (
                <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-medium">
                  <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  <span>
                    Zero enrollment integrity issues found. All students and subjects have valid foreign keys and zero duplicate enrollments.
                  </span>
                </div>
              ) : (
                <div className="p-4 bg-rose-50 border border-rose-200 text-rose-900 rounded-xl text-xs">
                  <div className="flex items-center gap-2 font-bold mb-2">
                    <ShieldAlert className="w-5 h-5 text-rose-600" />
                    <span>Integrity Warnings Detected</span>
                  </div>
                  <p>Please resolve duplicate enrollments or orphan student/course references prior to schedule generation.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Add Student Modal */}
      <Dialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Student Record"
        description="Register a student into the academic database roster."
        maxWidth="md"
      >
        <form onSubmit={handleCreateStudent} className="space-y-4">
          {errorMsg && (
            <p className="p-2.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg">
              {errorMsg}
            </p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Student Number"
              placeholder="e.g. S2026101"
              value={studentNumber}
              onChange={(e) => setStudentNumber(e.target.value.toUpperCase())}
              required
            />
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Department</label>
              <select
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.code})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Input
            label="Full Name"
            placeholder="e.g. Eleanor Vance"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Email Address"
              type="email"
              placeholder="e.g. eleanor@univ.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              label="Semester"
              type="number"
              min="1"
              max="12"
              value={semester}
              onChange={(e) => setSemester(Number(e.target.value))}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" size="md" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="md" type="submit" isLoading={isSubmitting}>
              Add Student
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Import Wizard */}
      <ImportWizardModal
        isOpen={isImportOpen}
        defaultType="students"
        cycleId={selectedCycleId}
        onClose={() => setIsImportOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
};
