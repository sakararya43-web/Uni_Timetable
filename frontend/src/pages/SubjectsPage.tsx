import React, { useEffect, useState } from "react";
import { Plus, Search, Upload } from "lucide-react";
import { api } from "../services/api";
import { Subject, Department } from "../types/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Dialog } from "../components/ui/Dialog";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ImportWizardModal } from "../components/imports/ImportWizardModal";

export const SubjectsPage: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDeptId, setSelectedDeptId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [editEnrollmentCount, setEditEnrollmentCount] = useState(20);
  const [isUpdatingEnrollment, setIsUpdatingEnrollment] = useState(false);

  // Form State
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [semester, setSemester] = useState(1);
  const [credits, setCredits] = useState(3.0);
  const [durationMinutes, setDurationMinutes] = useState(180);
  const [initialEnrollment, setInitialEnrollment] = useState(25);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [subs, depts] = await Promise.all([
        api.get<Subject[]>("/api/v1/subjects"),
        api.get<Department[]>("/api/v1/academic/departments"),
      ]);
      setSubjects(subs);
      setDepartments(depts);
      if (depts.length > 0 && !departmentId) {
        setDepartmentId(depts[0].id);
      }
    } catch (err) {
      console.error("Failed to load subjects:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedSubject) {
      setEditEnrollmentCount(selectedSubject.enrollmentCount ?? 20);
    }
  }, [selectedSubject]);

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      await api.post("/api/v1/subjects", {
        subject_code: code,
        subject_name: name,
        department_id: departmentId,
        semester,
        credits,
        default_duration_minutes: durationMinutes,
        initial_enrollment: initialEnrollment,
      });
      setIsCreateOpen(false);
      setCode("");
      setName("");
      setInitialEnrollment(25);
      fetchData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to create subject.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateEnrollmentCount = async () => {
    if (!selectedSubject) return;
    setIsUpdatingEnrollment(true);
    try {
      await api.patch(`/api/v1/subjects/${selectedSubject.id}`, {
        enrollmentCount: editEnrollmentCount,
      });
      setSelectedSubject({
        ...selectedSubject,
        enrollmentCount: editEnrollmentCount,
      });
      setSubjects((prev) =>
        prev.map((s) =>
          s.id === selectedSubject.id
            ? { ...s, enrollmentCount: editEnrollmentCount, conflictDegree: Math.min(8, Math.max(1, Math.floor(editEnrollmentCount / 5))) }
            : s
        )
      );
    } catch (err) {
      console.error("Failed to update enrollment count:", err);
    } finally {
      setIsUpdatingEnrollment(false);
    }
  };

  const filteredSubjects = subjects.filter((s) => {
    const matchesSearch =
      s.subjectCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.subjectName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDept = !selectedDeptId || s.departmentId === selectedDeptId;
    return matchesSearch && matchesDept;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Academic Subjects</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage course catalog, examination duration constraints, and department allocations.
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
            Add Subject
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-3 border border-slate-200 rounded-xl shadow-sm">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by subject code (e.g. CS101) or course title..."
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

      {/* Subjects Table */}
      {isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : filteredSubjects.length === 0 ? (
        <EmptyState
          title="No Subjects Found"
          description="No subjects match your filter criteria or none have been imported yet."
          actionLabel="Add New Subject"
          onAction={() => setIsCreateOpen(true)}
        />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                <th className="py-3 px-4">Subject Code</th>
                <th className="py-3 px-4">Subject Name</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Semester</th>
                <th className="py-3 px-4">Enrolled Students</th>
                <th className="py-3 px-4">Credits</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredSubjects.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-blue-600">{s.subjectCode}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{s.subjectName}</td>
                  <td className="py-3 px-4">{s.departmentCode || "GEN"}</td>
                  <td className="py-3 px-4">Sem {s.semester}</td>
                  <td className="py-3 px-4">
                    <span className="font-semibold text-slate-900">{s.enrollmentCount ?? 0} students</span>
                    <span className="ml-2 inline-block px-1.5 py-0.5 text-[10px] bg-slate-100 text-slate-600 font-medium rounded border border-slate-200">
                      deg {s.conflictDegree ?? 0}
                    </span>
                  </td>
                  <td className="py-3 px-4">{s.credits} cr</td>
                  <td className="py-3 px-4">{s.defaultDurationMinutes} min</td>
                  <td className="py-3 px-4 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedSubject(s)}
                    >
                      Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Subject Modal */}
      <Dialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Academic Subject"
        description="Enter curriculum parameters, examination length, and academic department."
        maxWidth="md"
      >
        <form onSubmit={handleCreateSubject} className="space-y-4">
          {errorMsg && (
            <p className="p-2.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg">
              {errorMsg}
            </p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Subject Code"
              placeholder="e.g. CS201"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
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
            label="Subject Title"
            placeholder="e.g. Advanced Operating Systems"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Student Enrollment (Cohort Size)
              </label>
              <select
                value={initialEnrollment}
                onChange={(e) => setInitialEnrollment(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={15}>15 Students (Lab / Seminar)</option>
                <option value={20}>20 Students (Tutorial Group)</option>
                <option value={25}>25 Students (Standard Class)</option>
                <option value={35}>35 Students (Major Section)</option>
                <option value={50}>50 Students (Combined Lecture)</option>
                <option value={100}>100 Students (Department-wide)</option>
              </select>
            </div>
            <Input
              label="Or Custom Enrollment Count"
              type="number"
              min="1"
              max="500"
              value={initialEnrollment}
              onChange={(e) => setInitialEnrollment(Number(e.target.value))}
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Semester"
              type="number"
              min="1"
              max="12"
              value={semester}
              onChange={(e) => setSemester(Number(e.target.value))}
              required
            />
            <Input
              label="Credits"
              type="number"
              step="0.5"
              min="1"
              max="10"
              value={credits}
              onChange={(e) => setCredits(Number(e.target.value))}
              required
            />
            <Input
              label="Duration (Min)"
              type="number"
              min="30"
              max="360"
              step="15"
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(Number(e.target.value))}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" size="md" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="md" type="submit" isLoading={isSubmitting}>
              Create Subject
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Subject Detail Drawer / Modal */}
      {selectedSubject && (
        <Dialog
          isOpen={Boolean(selectedSubject)}
          onClose={() => setSelectedSubject(null)}
          title={`Subject Details: ${selectedSubject.subjectCode}`}
          description={selectedSubject.subjectName}
          maxWidth="md"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-slate-500 font-medium block">Department</span>
                <span className="text-slate-900 font-bold mt-0.5 block">{selectedSubject.departmentCode || "N/A"}</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-slate-500 font-medium block">Semester & Credits</span>
                <span className="text-slate-900 font-bold mt-0.5 block">
                  Semester {selectedSubject.semester} · {selectedSubject.credits} Credits
                </span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-slate-500 font-medium block">Exam Duration</span>
                <span className="text-slate-900 font-bold mt-0.5 block">{selectedSubject.defaultDurationMinutes} Minutes</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-slate-500 font-medium block">Catalog Status</span>
                <span className="text-emerald-700 font-bold mt-0.5 block capitalize">{selectedSubject.status}</span>
              </div>
            </div>

            {/* Live Enrollment Count & Quick Dropdown Adjuster */}
            <div className="p-3.5 bg-blue-50/70 border border-blue-200 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-blue-900 block">Enrolled Students & Clashes</span>
                  <p className="text-[11px] text-blue-700 mt-0.5">
                    Currently <strong>{selectedSubject.enrollmentCount ?? 0} students</strong> enrolled &middot; Conflict degree: <strong>deg {selectedSubject.conflictDegree ?? 0}</strong>
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-2 pt-1 border-t border-blue-200/60">
                <label className="text-[11px] font-semibold text-slate-700 sm:w-36 flex-shrink-0">
                  Update Enrollment:
                </label>
                <select
                  value={editEnrollmentCount}
                  onChange={(e) => setEditEnrollmentCount(Number(e.target.value))}
                  className="w-full sm:w-auto flex-1 px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={10}>10 Students (Seminar)</option>
                  <option value={15}>15 Students (Lab Session)</option>
                  <option value={20}>20 Students (Tutorial)</option>
                  <option value={25}>25 Students (Standard Class)</option>
                  <option value={35}>35 Students (Lecture Group)</option>
                  <option value={50}>50 Students (Combined Hall)</option>
                  <option value={75}>75 Students (Cohort)</option>
                  <option value={100}>100 Students (Department-wide)</option>
                </select>
                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <input
                    type="number"
                    min="1"
                    max="500"
                    value={editEnrollmentCount}
                    onChange={(e) => setEditEnrollmentCount(Number(e.target.value))}
                    className="w-20 px-2 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-center font-bold"
                  />
                  <Button
                    variant="primary"
                    size="sm"
                    isLoading={isUpdatingEnrollment}
                    onClick={handleUpdateEnrollmentCount}
                  >
                    Save Count
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="secondary" size="sm" onClick={() => setSelectedSubject(null)}>
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* CSV Import Wizard */}
      <ImportWizardModal
        isOpen={isImportOpen}
        defaultType="subjects"
        onClose={() => setIsImportOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
};
