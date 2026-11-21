import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen,
  Sparkles,
  GraduationCap,
  Calendar,
  CheckCircle2,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Search,
  Upload,
  Lightbulb,
  ShieldCheck,
  Compass,
} from "lucide-react";

export interface QuickGuideBoxProps {
  variant?: "full" | "compact";
  defaultExpanded?: boolean;
  onSelectSampleStudent?: (rollNumber: string) => void;
  className?: string;
  id?: string;
}

export const QuickGuideBox: React.FC<QuickGuideBoxProps> = ({
  variant = "full",
  defaultExpanded = true,
  onSelectSampleStudent,
  className = "",
  id = "how-to-use",
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  const [activeTab, setActiveTab] = useState<"overview" | "student" | "staff">("overview");

  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div
      id={id}
      className={`border border-[var(--color-rule)] rounded bg-white shadow-sm overflow-hidden transition-all duration-200 ${className}`}
      aria-labelledby="guide-box-heading"
    >
      {/* 1. Header Bar with Collegiate Crest, Title, and Collapse Toggle */}
      <div
        className={`${
          variant === "compact" ? "p-3 sm:p-4" : "p-4 sm:p-5"
        } bg-[var(--color-paper)] border-b border-[var(--color-rule)] flex items-center justify-between gap-4`}
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded border border-[var(--color-ink)] flex items-center justify-center bg-[var(--color-paper-2)] shrink-0">
            {variant === "compact" ? (
              <BookOpen className="w-4 h-4 text-[var(--color-accent)]" />
            ) : (
              <Compass className="w-4 h-4 text-[var(--color-accent)]" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2
                id="guide-box-heading"
                className="font-display text-lg sm:text-xl text-[var(--color-ink)] font-normal tracking-tight"
              >
                How ExamScheduler Works
              </h2>
              <span className="font-mono text-[11px] px-2 py-0.5 rounded border border-[var(--color-rule)] bg-[var(--color-paper-2)] text-[var(--color-accent)] font-medium">
                Plain-English Guide
              </span>
            </div>
            <p className="text-xs text-[var(--color-muted)] font-sans mt-0.5">
              Everything you need to know about creating and viewing clash-free examination timetables.
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-2.5 py-1.5 text-xs font-sans rounded border border-[var(--color-rule)] hover:border-[var(--color-ink)] bg-white text-[var(--color-ink)] flex items-center gap-1.5 transition-colors shrink-0"
          aria-expanded={isExpanded}
          aria-label={isExpanded ? "Collapse guide box" : "Expand guide box"}
        >
          <span className="hidden sm:inline">{isExpanded ? "Hide Guide" : "Show Guide"}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Collapsed Teaser Preview */}
      {!isExpanded && (
        <div className="p-3.5 bg-white text-xs text-[var(--color-ink-2)] font-sans flex flex-wrap items-center justify-between gap-3">
          <span className="flex items-center gap-2">
            <Lightbulb className="w-3.5 h-3.5 text-[var(--color-accent)] shrink-0" />
            <span>
              <strong>Quick summary:</strong> ExamScheduler automatically schedules exams into morning and afternoon slots so no student ever has two exams at once.
            </span>
          </span>
          <button
            onClick={() => setIsExpanded(true)}
            className="text-xs text-[var(--color-accent)] hover:underline font-medium font-sans"
          >
            Read 3-step guide →
          </button>
        </div>
      )}

      {/* 2. Expanded Interactive Content */}
      {isExpanded && (
        <div>
          {/* Tab Selection */}
          <div className="border-b border-[var(--color-rule)] bg-[var(--color-paper-2)] px-4 sm:px-6 flex gap-2 sm:gap-4 overflow-x-auto text-xs font-sans">
            <button
              onClick={() => setActiveTab("overview")}
              className={`py-2.5 px-3 border-b-2 font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === "overview"
                  ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-white font-semibold rounded-t"
                  : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>3-Step Overview</span>
            </button>
            <button
              onClick={() => setActiveTab("student")}
              className={`py-2.5 px-3 border-b-2 font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === "student"
                  ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-white font-semibold rounded-t"
                  : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              }`}
            >
              <GraduationCap className="w-3.5 h-3.5" />
              <span>For Students (Look Up Dates)</span>
            </button>
            <button
              onClick={() => setActiveTab("staff")}
              className={`py-2.5 px-3 border-b-2 font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === "staff"
                  ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-white font-semibold rounded-t"
                  : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>For Exam Coordinators & Staff</span>
            </button>
          </div>

          <div className={`${variant === "compact" ? "p-4 sm:p-5" : "p-5 sm:p-6"} space-y-6`}>
            {/* TAB 1: 3-STEP OVERVIEW */}
            {activeTab === "overview" && (
              <div className="space-y-6">
                {/* Non-technical problem & solution statement */}
                <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)]">
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded border border-[var(--color-accent)] bg-white flex items-center justify-center shrink-0 mt-0.5">
                      <Lightbulb className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="text-sm font-semibold text-[var(--color-ink)] font-sans">
                        What does ExamScheduler do for you?
                      </h3>
                      <p className="text-xs sm:text-sm text-[var(--color-ink-2)] font-sans leading-relaxed">
                        Planning university exams by hand on spreadsheets often leads to overlapping exams, where students are accidentally scheduled for two tests at the exact same hour.
                        <strong> ExamScheduler eliminates this completely.</strong> It inspects all student class enrollments and automatically arranges exams into clash-free morning or afternoon slots, so every student has a clean, conflict-free timetable.
                      </p>
                    </div>
                  </div>
                </div>

                {/* 3 Step Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Step 1 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] text-[var(--color-ink)]">
                          STEP 1
                        </span>
                        <Upload className="w-4 h-4 text-[var(--color-muted)]" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        Input Courses & Students
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        Staff enter or import the list of subjects and who is taking them. You can upload a simple spreadsheet or load instant demo data with one click.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-sans flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-[var(--color-success)]" />
                      <span>Accepts CSV or pre-loaded data</span>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] text-[var(--color-accent)]">
                          STEP 2
                        </span>
                        <Sparkles className="w-4 h-4 text-[var(--color-accent)]" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        Click 'Generate'
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        The smart scheduling engine sorts all exams in seconds. It ensures that any two exams sharing enrolled students are placed into different time slots.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-sans flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-[var(--color-success)]" />
                      <span>Zero clashes guaranteed</span>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] text-[var(--color-success)]">
                          STEP 3
                        </span>
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        Review & Look Up Dates
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        Staff can review and publish the official calendar. Students can simply enter their roll number to get their personalized hall ticket and exam dates.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-sans flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-[var(--color-success)]" />
                      <span>Instant student hall tickets</span>
                    </div>
                  </div>
                </div>

                {/* Direct Action Pathways */}
                <div className="pt-2 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => setActiveTab("student")}
                      className="px-3 py-1.5 rounded border border-[var(--color-rule)] hover:border-[var(--color-ink)] bg-[var(--color-paper-2)] text-[var(--color-ink)] font-medium transition-colors"
                    >
                      Are you a student? Read student guide →
                    </button>
                    <button
                      onClick={() => setActiveTab("staff")}
                      className="px-3 py-1.5 rounded border border-[var(--color-rule)] hover:border-[var(--color-ink)] bg-[var(--color-paper-2)] text-[var(--color-ink)] font-medium transition-colors"
                    >
                      Are you a coordinator? Read staff guide →
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      to="/overview"
                      className="px-3.5 py-1.5 bg-[var(--color-accent)] text-white font-medium rounded hover:bg-[var(--color-accent-deep)] transition-colors flex items-center gap-1.5 shadow-sm"
                    >
                      <span>Open Operations Console</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: FOR STUDENTS */}
            {activeTab === "student" && (
              <div className="space-y-5">
                <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex items-start gap-3">
                  <div className="w-8 h-8 rounded border border-[var(--color-ink)] bg-white flex items-center justify-center shrink-0">
                    <GraduationCap className="w-4 h-4 text-[var(--color-accent)]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-[var(--color-ink)] font-sans">
                      Finding Your Personalized Exam Schedule (No Password Needed)
                    </h3>
                    <p className="text-xs text-[var(--color-muted)] font-sans mt-0.5">
                      Follow these easy steps to see your exam days, times, and assigned seat.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-sans">
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-white space-y-2">
                    <div className="font-mono text-xs font-bold text-[var(--color-accent)]">Step 1</div>
                    <h4 className="font-semibold text-sm text-[var(--color-ink)]">Find the Lookup Box</h4>
                    <p className="text-[var(--color-ink-2)] leading-relaxed">
                      Scroll down to the <strong>Candidate Examination & Seating Lookup</strong> section on this page, or open the <strong>Student Portal</strong> from the top menu.
                    </p>
                  </div>

                  <div className="p-4 rounded border border-[var(--color-rule)] bg-white space-y-2">
                    <div className="font-mono text-xs font-bold text-[var(--color-accent)]">Step 2</div>
                    <h4 className="font-semibold text-sm text-[var(--color-ink)]">Enter Your Roll Number</h4>
                    <p className="text-[var(--color-ink-2)] leading-relaxed">
                      Type your university candidate ID. For example, you can test with sample ID <code className="font-mono bg-[var(--color-paper-2)] px-1 py-0.5 rounded border border-[var(--color-rule)]">STU-2024-001</code>.
                    </p>
                  </div>

                  <div className="p-4 rounded border border-[var(--color-rule)] bg-white space-y-2">
                    <div className="font-mono text-xs font-bold text-[var(--color-accent)]">Step 3</div>
                    <h4 className="font-semibold text-sm text-[var(--color-ink)]">View & Print Hall Ticket</h4>
                    <p className="text-[var(--color-ink-2)] leading-relaxed">
                      Your courses, exam dates, morning or afternoon time slots, hall room, and row/seat numbers appear immediately. You can print or download your slip!
                    </p>
                  </div>
                </div>

                {/* Quick Interactive Test for Students */}
                <div className="p-3.5 bg-[var(--color-paper-2)] rounded border border-[var(--color-rule)] flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2">
                    <Search className="w-4 h-4 text-[var(--color-accent)]" />
                    <span>
                      <strong>Want to test right now?</strong> Click a sample student to test:
                    </span>
                    <div className="flex gap-1.5">
                      {["STU-2024-001", "STU-2024-042", "STU-2024-108"].map((id) => (
                        <button
                          key={id}
                          onClick={() => {
                            if (onSelectSampleStudent) {
                              onSelectSampleStudent(id);
                            }
                            scrollToSection("student-roll-input");
                          }}
                          className="px-2 py-0.5 font-mono text-[11px] bg-white border border-[var(--color-rule)] hover:border-[var(--color-ink)] rounded transition-colors"
                        >
                          {id}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => scrollToSection("student-roll-input")}
                      className="px-3 py-1.5 bg-[var(--color-accent)] text-white rounded hover:bg-[var(--color-accent-deep)] transition-colors font-medium"
                    >
                      Jump to Lookup Box ↓
                    </button>
                    <Link
                      to="/student/timetable"
                      className="px-3 py-1.5 border border-[var(--color-ink)] text-[var(--color-ink)] rounded hover:bg-white transition-colors font-medium"
                    >
                      Open Student Portal
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: FOR STAFF & COORDINATORS */}
            {activeTab === "staff" && (
              <div className="space-y-5">
                <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex items-start gap-3">
                  <div className="w-8 h-8 rounded border border-[var(--color-ink)] bg-white flex items-center justify-center shrink-0">
                    <Calendar className="w-4 h-4 text-[var(--color-accent)]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-[var(--color-ink)] font-sans">
                      Exam Coordinator & Administrator Workflow
                    </h3>
                    <p className="text-xs text-[var(--color-muted)] font-sans mt-0.5">
                      How to build, review, and publish an official exam schedule from start to finish.
                    </p>
                  </div>
                </div>

                <div className="space-y-2.5 text-xs font-sans">
                  <div className="p-3 rounded border border-[var(--color-rule)] bg-white flex items-start gap-3">
                    <span className="font-mono font-bold text-xs w-5 h-5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] flex items-center justify-center shrink-0">
                      1
                    </span>
                    <div>
                      <strong className="text-[var(--color-ink)]">Open the Operations Console:</strong>{" "}
                      Click <Link to="/overview" className="text-[var(--color-accent)] underline font-medium">Open Console</Link> in the navigation bar to enter the administrative dashboard.
                    </div>
                  </div>

                  <div className="p-3 rounded border border-[var(--color-rule)] bg-white flex items-start gap-3">
                    <span className="font-mono font-bold text-xs w-5 h-5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] flex items-center justify-center shrink-0">
                      2
                    </span>
                    <div>
                      <strong className="text-[var(--color-ink)]">Select or Create an Exam Cycle:</strong>{" "}
                      Choose which academic period you are scheduling (e.g. <em>Autumn 2026 Finals</em>). All data is neatly organized per cycle.
                    </div>
                  </div>

                  <div className="p-3 rounded border border-[var(--color-rule)] bg-white flex items-start gap-3">
                    <span className="font-mono font-bold text-xs w-5 h-5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] flex items-center justify-center shrink-0">
                      3
                    </span>
                    <div>
                      <strong className="text-[var(--color-ink)]">Import or Load Data:</strong>{" "}
                      Upload your spreadsheet of subjects and students with the <strong>Bulk Import Wizard</strong>, or head to <strong>Settings → Demo & Help</strong> to load complete sample university data instantly.
                    </div>
                  </div>

                  <div className="p-3 rounded border border-[var(--color-rule)] bg-white flex items-start gap-3">
                    <span className="font-mono font-bold text-xs w-5 h-5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] flex items-center justify-center shrink-0">
                      4
                    </span>
                    <div>
                      <strong className="text-[var(--color-ink)]">Run Automated Schedule Generation:</strong>{" "}
                      Go to <Link to="/generate" className="text-[var(--color-accent)] underline font-medium">Generate Schedule</Link> and click <em>Generate Timetable</em>. In under 1 second, the engine places all exams into clash-free slots.
                    </div>
                  </div>

                  <div className="p-3 rounded border border-[var(--color-rule)] bg-white flex items-start gap-3">
                    <span className="font-mono font-bold text-xs w-5 h-5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] flex items-center justify-center shrink-0">
                      5
                    </span>
                    <div>
                      <strong className="text-[var(--color-ink)]">Review on Grid & Publish:</strong>{" "}
                      Inspect the calendar on the <Link to="/timetable" className="text-[var(--color-accent)] underline font-medium">Timetable Grid</Link>. If you ever need to manually move an exam, the system will immediately alert you if that move creates a student conflict. Once finalized, click <strong>Publish</strong> to release the schedule to students.
                    </div>
                  </div>
                </div>

                <div className="pt-2 flex flex-wrap items-center justify-end gap-3 text-xs">
                  <Link
                    to="/generate"
                    className="px-3.5 py-1.5 border border-[var(--color-ink)] text-[var(--color-ink)] font-medium rounded hover:bg-[var(--color-paper-2)] transition-colors"
                  >
                    Go to Schedule Generator
                  </Link>
                  <Link
                    to="/overview"
                    className="px-3.5 py-1.5 bg-[var(--color-accent)] text-white font-medium rounded hover:bg-[var(--color-accent-deep)] transition-colors flex items-center gap-1.5"
                  >
                    <span>Launch Operations Console</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* 3. Subtle Institutional Footer Note */}
          <div className="p-3 sm:px-6 bg-[var(--color-paper-2)] border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-sans flex flex-col sm:flex-row items-center justify-between gap-2">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-success)] shrink-0" />
              <span>
                <strong>Zero-Clash Guarantee:</strong> Built on mathematical graph coloring to ensure students never have double bookings.
              </span>
            </span>
            <span className="font-mono text-[10px]">Registry Guide v1.0</span>
          </div>
        </div>
      )}
    </div>
  );
};
