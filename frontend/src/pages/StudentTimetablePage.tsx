import React, { useEffect, useState } from "react";
import {
  Calendar,
  Download,
  Printer,
  ShieldCheck,
  GraduationCap,
  BookOpen,
  User,
  Info,
} from "lucide-react";
import { api } from "../services/api";
import { StudentTimetableResponse } from "../types/api";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

export const StudentTimetablePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"timetable" | "academic">("timetable");
  const [timetable, setTimetable] = useState<StudentTimetableResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    setIsLoading(true);
    api.get<StudentTimetableResponse>("/api/v1/me/timetable")
      .then((data) => setTimetable(data))
      .catch((err: unknown) => {
        const e = err as { code?: string };
        if (e.code === "PUBLISHED_SCHEDULE_NOT_FOUND" || e.code === "STUDENT_PROFILE_NOT_FOUND") {
          setTimetable(null);
        } else {
          setTimetable(null);
        }
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = () => {
    if (!timetable?.scheduleVersionId) return;
    window.open(`/api/v1/schedules/${timetable.scheduleVersionId}/export/pdf`, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="print:hidden flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Personal Examination Schedule</h1>
            <Badge variant="success">OFFICIAL PUBLISHED</Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Verified clash-free examination timetable for your registered courses.
          </p>
        </div>

        {timetable && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Download className="w-3.5 h-3.5" />}
              onClick={handleDownloadPDF}
            >
              Download PDF
            </Button>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Printer className="w-3.5 h-3.5" />}
              onClick={handlePrint}
            >
              Print Schedule
            </Button>
          </div>
        )}
      </div>

      {/* Navigation Tabs (Task P13.13) */}
      <div className="print:hidden flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("timetable")}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "timetable"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>My Examination Timetable</span>
        </button>
        <button
          onClick={() => setActiveTab("academic")}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "academic"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <GraduationCap className="w-3.5 h-3.5" />
          <span>Academic Information & Enrollments</span>
        </button>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : !timetable || timetable.exams.length === 0 ? (
        <EmptyState
          title="No Timetable Published Yet"
          description="The examination administration has not published the official timetable for your academic cycle yet. Please check back later."
          icon={<GraduationCap className="w-8 h-8" />}
        />
      ) : activeTab === "timetable" ? (
        <div className="space-y-6">
          {/* Student Profile & Cycle Banner */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div>
              <p className="font-bold text-slate-900 text-sm">{timetable.studentName}</p>
              <p className="text-slate-500 font-mono">Student ID: {timetable.studentNumber}</p>
            </div>
            <div className="sm:text-right text-slate-600">
              <p className="font-semibold text-slate-800">{timetable.cycleName}</p>
              <p className="text-[11px] text-slate-500">
                Version {timetable.versionNumber} · Published:{" "}
                {timetable.publishedAt ? new Date(timetable.publishedAt).toLocaleDateString() : "Official"}
              </p>
            </div>
          </div>

          {/* Timetable List View */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                  <th className="py-3 px-4">Date & Day</th>
                  <th className="py-3 px-4">Time Window</th>
                  <th className="py-3 px-4">Subject Code</th>
                  <th className="py-3 px-4">Course Title</th>
                  <th className="py-3 px-4">Session</th>
                  <th className="py-3 px-4">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {timetable.exams.map((exam, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="py-3.5 px-4 font-bold text-slate-900 whitespace-nowrap">
                      {new Date(exam.examDate + "T00:00:00").toLocaleDateString(undefined, {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold text-blue-700 whitespace-nowrap">
                      {exam.startTime} - {exam.endTime}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">{exam.subjectCode}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-800">{exam.subjectName}</td>
                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border">
                        {exam.sessionLabel || "Standard"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">{exam.durationMinutes} min</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Exam Regulations Notice */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 space-y-1">
            <p className="font-bold text-slate-800 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              Examination Attendance Instructions:
            </p>
            <p className="text-[11px]">
              Candidates must report to their designated examination hall 15 minutes prior to the scheduled start time with their valid Student Identification Card. Electronic devices are strictly prohibited.
            </p>
          </div>
        </div>
      ) : (
        /* Academic Information Tab (Task P13.13 & P13.14 Data Minimization) */
        <div className="space-y-6">
          <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <User className="w-4 h-4 text-blue-600" />
              Student Registration Summary
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <p className="text-slate-500 font-medium">Full Name</p>
                <p className="font-bold text-slate-800 mt-0.5">{timetable.studentName}</p>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <p className="text-slate-500 font-medium">Roll / Registration Number</p>
                <p className="font-mono font-bold text-slate-800 mt-0.5">{timetable.studentNumber}</p>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <p className="text-slate-500 font-medium">Scheduling Cycle</p>
                <p className="font-bold text-slate-800 mt-0.5">{timetable.cycleName}</p>
              </div>
            </div>
          </div>

          <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-blue-600" />
              Registered Subjects in Current Cycle ({timetable.exams.length})
            </h2>
            <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
              {timetable.exams.map((ex, i) => (
                <div key={i} className="p-3 bg-white flex items-center justify-between text-xs">
                  <div>
                    <span className="font-mono font-bold text-blue-700">{ex.subjectCode}</span>
                    <span className="text-slate-800 font-medium ml-2">{ex.subjectName}</span>
                  </div>
                  <span className="text-slate-500 font-mono text-[11px]">{ex.durationMinutes} mins</span>
                </div>
              ))}
            </div>

            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-900 flex items-start gap-2">
              <Info className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Privacy Guarantee:</strong> You are authenticated as an individual student. In compliance with strict university privacy protocols, this portal isolates your registered courses and does not expose other students&apos; enrollment or identity records.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
