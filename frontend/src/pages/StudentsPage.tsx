import React, { useEffect, useState } from "react";
import { Plus, Search, Upload, ShieldAlert, CheckCircle, RefreshCw, UserCheck, Trash2, BookOpen } from "lucide-react";
import { api } from "../services/api";
import { Student, Department, SchedulingCycle, Subject, Enrollment, PaginatedEnrollmentsResponse } from "../types/api";
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
  const [tab, setTab] = useState<"roster" | "enrollments" | "diagnostics">("roster");
  const [students, setStudents] = useState<Student[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDeptId, setSelectedDeptId] = useState("");
  const [enrollmentSearchTerm, setEnrollmentSearchTerm] = useState("");
  const [selectedEnrollmentSubjectId, setSelectedEnrollmentSubjectId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEnrollOpen, setIsEnrollOpen] = useState(false);
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

  // Enrollment Form
  const [enrollStudentId, setEnrollStudentId] = useState("");
  const [enrollSubjectId, setEnrollSubjectId] = useState("");
  const [enrollCycleId, setEnrollCycleId] = useState("");
  const [enrollMode, setEnrollMode] = useState<"single" | "cohort">("single");
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [enrollSuccessMsg, setEnrollSuccessMsg] = useState<string | null>(null);
  const [enrollErrorMsg, setEnrollErrorMsg] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [studs, depts, cycs, subs, enrs] = await Promise.all([
        api.get<Student[]>("/api/v1/students"),
        api.get<Department[]>("/api/v1/academic/departments"),
        api.get<SchedulingCycle[]>("/api/v1/cycles"),
        api.get<Subject[]>("/api/v1/subjects"),
        api.get<PaginatedEnrollmentsResponse | Enrollment[]>("/api/v1/enrollments").catch(() => ({ items: [] })),
      ]);
      setStudents(studs);
      setDepartments(depts);
      setCycles(cycs);
      setSubjects(subs);

      const items = Array.isArray(enrs) ? enrs : (enrs as PaginatedEnrollmentsResponse).items || [];
      setEnrollments(items);

      if (depts.length > 0 && !departmentId) setDepartmentId(depts[0].id);
      if (cycs.length > 0 && !selectedCycleId) {
        setSelectedCycleId(cycs[0].id);
        setEnrollCycleId(cycs[0].id);
      }
      if (studs.length > 0 && !enrollStudentId) setEnrollStudentId(studs[0].id);
      if (subs.length > 0 && !enrollSubjectId) setEnrollSubjectId(subs[0].id);
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

  const handleEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsEnrolling(true);
    setEnrollSuccessMsg(null);
    setEnrollErrorMsg(null);

    try {
      const targetCycleId = enrollCycleId || selectedCycleId || (cycles[0]?.id ?? "cycle-demo-2026");

      if (enrollMode === "cohort") {
        const targetSub = subjects.find((s) => s.id === enrollSubjectId);
        const cohortStudents = students.filter(
          (s) =>
            (!targetSub?.departmentId || s.departmentId === targetSub.departmentId) &&
            (!targetSub?.semester || s.semester === targetSub.semester)
        );

        if (cohortStudents.length === 0) {
          throw new Error("No students found in the matching department and semester cohort.");
        }

        let count = 0;
        for (const stu of cohortStudents) {
          await api.post("/api/v1/enrollments", {
            student_id: stu.id,
            subject_id: enrollSubjectId,
            cycle_id: targetCycleId,
          });
          count++;
        }
        setEnrollSuccessMsg(`Successfully enrolled ${count} students from ${targetSub?.subjectCode || "course"} cohort!`);
      } else {
        await api.post("/api/v1/enrollments", {
          student_id: enrollStudentId,
          subject_id: enrollSubjectId,
          cycle_id: targetCycleId,
        });
        const stu = students.find((s) => s.id === enrollStudentId);
        const sub = subjects.find((s) => s.id === enrollSubjectId);
        setEnrollSuccessMsg(`Enrolled ${stu?.fullName || "student"} into ${sub?.subjectCode || "subject"}!`);
      }

      await fetchData();
      setTimeout(() => {
        setIsEnrollOpen(false);
        setEnrollSuccessMsg(null);
      }, 1400);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setEnrollErrorMsg(e.message || "Failed to create enrollment.");
    } finally {
      setIsEnrolling(false);
    }
  };

  const handleWithdrawEnrollment = async (enrollmentId: string) => {
    try {
      await api.delete(`/api/v1/enrollments/${enrollmentId}`);
      setEnrollments((prev) => prev.filter((e) => e.id !== enrollmentId));
      fetchData();
    } catch (err) {
      console.error("Failed to withdraw enrollment:", err);
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

  const filteredEnrollments = enrollments.filter((e) => {
    const matchesSearch =
      (e.studentNumber || "").toLowerCase().includes(enrollmentSearchTerm.toLowerCase()) ||
      (e.studentName || "").toLowerCase().includes(enrollmentSearchTerm.toLowerCase()) ||
      (e.subjectCode || "").toLowerCase().includes(enrollmentSearchTerm.toLowerCase()) ||
      (e.subjectName || "").toLowerCase().includes(enrollmentSearchTerm.toLowerCase());
    const matchesSubject = !selectedEnrollmentSubjectId || e.subjectId === selectedEnrollmentSubjectId;
    return matchesSearch && matchesSubject;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Student Directory & Course Enrollments</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage student registrations, enroll students into subjects via dropdown menus, or import CSVs.
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
            variant="outline"
            size="sm"
            className="border-blue-300 text-blue-700 hover:bg-blue-50 font-semibold"
            leftIcon={<UserCheck className="w-4 h-4 text-blue-600" />}
            onClick={() => {
              if (students.length > 0 && !enrollStudentId) setEnrollStudentId(students[0].id);
              if (subjects.length > 0 && !enrollSubjectId) setEnrollSubjectId(subjects[0].id);
              setIsEnrollOpen(true);
            }}
          >
            + Enroll in Course
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
          onClick={() => setTab("enrollments")}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all ${
            tab === "enrollments"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Course Enrollments ({enrollments.length})
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
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Semester</th>
                    <th className="py-3 px-4">Enrolled Courses</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredStudents.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-900">{s.studentNumber}</td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900">{s.fullName}</div>
                        <div className="text-[11px] text-slate-400">{s.email}</div>
                      </td>
                      <td className="py-3.5 px-4">{s.departmentCode || "GEN"}</td>
                      <td className="py-3.5 px-4">Sem {s.semester}</td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2.5 py-0.5 text-[11px] font-bold rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                          {s.enrollmentCount ?? 0} courses
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {s.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEnrollStudentId(s.id);
                            setIsEnrollOpen(true);
                          }}
                        >
                          + Enroll
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : tab === "enrollments" ? (
        /* Enrollments Tab */
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-3 border border-slate-200 rounded-xl shadow-sm">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search enrollments by student name, ID or subject code..."
                value={enrollmentSearchTerm}
                onChange={(e) => setEnrollmentSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={selectedEnrollmentSubjectId}
              onChange={(e) => setSelectedEnrollmentSubjectId(e.target.value)}
              className="w-full sm:w-64 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Academic Subjects</option>
              {subjects.map((sub) => (
                <option key={sub.id} value={sub.id}>
                  {sub.subjectCode} — {sub.subjectName}
                </option>
              ))}
            </select>
          </div>

          {filteredEnrollments.length === 0 ? (
            <EmptyState
              title="No Enrollments Found"
              description="No active course enrollments match your filter criteria."
              actionLabel="+ Enroll Student"
              onAction={() => setIsEnrollOpen(true)}
            />
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                    <th className="py-3 px-4">Student</th>
                    <th className="py-3 px-4">Course / Subject</th>
                    <th className="py-3 px-4">Examination Cycle</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredEnrollments.map((enr) => (
                    <tr key={enr.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-mono font-bold text-slate-900 block">{enr.studentNumber}</span>
                        <span className="text-slate-500 text-[11px] block">{enr.studentName}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-blue-600 block">{enr.subjectCode}</span>
                        <span className="text-slate-700 text-[11px] block">{enr.subjectName}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {cycles.find((c) => c.id === enr.cycleId)?.name || "June 2026 Academic Final Examinations"}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-block px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          ACTIVE
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                          leftIcon={<Trash2 className="w-3.5 h-3.5" />}
                          onClick={() => handleWithdrawEnrollment(enr.id)}
                        >
                          Withdraw
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
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

      {/* Enroll Student Modal (Dropdown Menus) */}
      <Dialog
        isOpen={isEnrollOpen}
        onClose={() => setIsEnrollOpen(false)}
        title="Enroll Student in Subject"
        description="Select student, course, and exam cycle from dropdown menus to create enrollment records."
        maxWidth="md"
      >
        <form onSubmit={handleEnroll} className="space-y-4">
          {enrollSuccessMsg && (
            <p className="p-3 text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg font-medium flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              {enrollSuccessMsg}
            </p>
          )}

          {enrollErrorMsg && (
            <p className="p-2.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg">
              {enrollErrorMsg}
            </p>
          )}

          {/* Enrollment Scope */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Enrollment Mode (Dropdown)
            </label>
            <select
              value={enrollMode}
              onChange={(e) => setEnrollMode(e.target.value as "single" | "cohort")}
              className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            >
              <option value="single">Single Student Enrollment</option>
              <option value="cohort">Batch Cohort Enrollment (All students in Department & Semester)</option>
            </select>
          </div>

          {/* Student Selector (Dropdown) */}
          {enrollMode === "single" && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Select Student (Dropdown)
              </label>
              <select
                value={enrollStudentId}
                onChange={(e) => setEnrollStudentId(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.studentNumber} — {s.fullName} ({s.departmentCode || "GEN"}, Sem {s.semester})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Subject Selector (Dropdown) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Select Subject / Course (Dropdown)
            </label>
            <select
              value={enrollSubjectId}
              onChange={(e) => setEnrollSubjectId(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              {subjects.map((sub) => (
                <option key={sub.id} value={sub.id}>
                  {sub.subjectCode} — {sub.subjectName} ({sub.departmentCode || "GEN"}, Sem {sub.semester})
                </option>
              ))}
            </select>
          </div>

          {/* Cycle Selector (Dropdown) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Scheduling Cycle (Dropdown)
            </label>
            <select
              value={enrollCycleId}
              onChange={(e) => setEnrollCycleId(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              {cycles.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.startDate} to {c.endDate})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
            <Button variant="secondary" size="md" onClick={() => setIsEnrollOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              type="submit"
              isLoading={isEnrolling}
              leftIcon={<BookOpen className="w-4 h-4" />}
            >
              {enrollMode === "cohort" ? "Enroll Entire Cohort" : "Confirm Enrollment"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Add Student Modal */}
      <Dialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Student Record"
        description="Register a student into the academic database roster using dropdown selectors."
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
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Department (Dropdown)
              </label>
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
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Semester (Dropdown)
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {Array.from({ length: 8 }, (_, i) => i + 1).map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
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
