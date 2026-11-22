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
  SlidersHorizontal,
  Building2,
  UserCheck,
  Layers,
  Filter,
} from "lucide-react";

export interface QuickGuideBoxProps {
  variant?: "full" | "compact";
  defaultExpanded?: boolean;
  defaultTab?: "overview" | "dropdown" | "student" | "staff";
  onSelectSampleStudent?: (rollNumber: string) => void;
  className?: string;
  id?: string;
}

export const QuickGuideBox: React.FC<QuickGuideBoxProps> = ({
  variant = "full",
  defaultExpanded = true,
  defaultTab = "overview",
  onSelectSampleStudent,
  className = "",
  id = "how-to-use",
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  const [activeTab, setActiveTab] = useState<"overview" | "dropdown" | "student" | "staff">(defaultTab);

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
          {/* Method Selector: Dropdown Menu & Quick Tabs */}
          <div className="border-b border-[var(--color-rule)] bg-[var(--color-paper-2)] px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-sans">
            <div className="flex items-center gap-2">
              <label
                htmlFor="guide-method-select"
                className="font-medium text-[var(--color-ink)] flex items-center gap-1.5 whitespace-nowrap"
              >
                <SlidersHorizontal className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                <span>Guide Method:</span>
              </label>
              <select
                id="guide-method-select"
                aria-label="Select Guide Method"
                value={activeTab}
                onChange={(e) =>
                  setActiveTab(
                    e.target.value as "overview" | "dropdown" | "student" | "staff"
                  )
                }
                className="px-2.5 py-1 text-xs font-sans font-medium rounded border border-[var(--color-rule)] bg-white text-[var(--color-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] shadow-xs cursor-pointer"
              >
                <option value="overview">3-Step Overview (System Fundamentals)</option>
                <option value="dropdown">Dropdown Menu Method (No Spreadsheets Needed)</option>
                <option value="student">For Students (Look Up Dates & Hall Tickets)</option>
                <option value="staff">For Exam Coordinators & Staff (Complete Pipeline)</option>
              </select>
            </div>

            {/* Quick-Switch Pill Buttons */}
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <button
                onClick={() => setActiveTab("overview")}
                className={`py-1 px-2.5 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap text-xs ${
                  activeTab === "overview"
                    ? "bg-[var(--color-accent)] text-white font-semibold shadow-xs"
                    : "border border-[var(--color-rule)] bg-white text-[var(--color-ink-2)] hover:border-[var(--color-ink)]"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>3-Step Overview</span>
              </button>
              <button
                onClick={() => setActiveTab("dropdown")}
                aria-label="Dropdown Menu Method Tab"
                className={`py-1 px-2.5 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap text-xs ${
                  activeTab === "dropdown"
                    ? "bg-[var(--color-accent)] text-white font-semibold shadow-xs"
                    : "border border-[var(--color-rule)] bg-white text-[var(--color-ink-2)] hover:border-[var(--color-ink)]"
                }`}
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                <span>Dropdown Menu Method</span>
                <span className="text-[10px] uppercase font-mono px-1 rounded bg-amber-100 text-amber-800 font-bold">Recommended</span>
              </button>
              <button
                onClick={() => setActiveTab("student")}
                className={`py-1 px-2.5 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap text-xs ${
                  activeTab === "student"
                    ? "bg-[var(--color-accent)] text-white font-semibold shadow-xs"
                    : "border border-[var(--color-rule)] bg-white text-[var(--color-ink-2)] hover:border-[var(--color-ink)]"
                }`}
              >
                <GraduationCap className="w-3.5 h-3.5" />
                <span>For Students</span>
              </button>
              <button
                onClick={() => setActiveTab("staff")}
                className={`py-1 px-2.5 rounded font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap text-xs ${
                  activeTab === "staff"
                    ? "bg-[var(--color-accent)] text-white font-semibold shadow-xs"
                    : "border border-[var(--color-rule)] bg-white text-[var(--color-ink-2)] hover:border-[var(--color-ink)]"
                }`}
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>For Exam Coordinators</span>
              </button>
            </div>
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
                      onClick={() => setActiveTab("dropdown")}
                      className="px-3 py-1.5 rounded border border-[var(--color-accent)] bg-amber-50 text-[var(--color-accent-deep)] font-semibold hover:bg-amber-100 transition-colors flex items-center gap-1.5"
                    >
                      <SlidersHorizontal className="w-3.5 h-3.5" />
                      <span>Learn Dropdown Menu Method →</span>
                    </button>
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

            {/* TAB: DROPDOWN MENU METHOD */}
            {activeTab === "dropdown" && (
              <div className="space-y-6">
                {/* Non-technical Statement */}
                <div className="p-4 rounded border border-blue-200 bg-blue-50/70">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded border border-blue-600 bg-white flex items-center justify-center shrink-0 mt-0.5">
                      <SlidersHorizontal className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-bold text-slate-900 font-sans">
                          The Dropdown Menu Method (Zero CSV / Spreadsheet Required)
                        </h3>
                        <span className="text-[10px] font-mono font-bold uppercase px-1.5 py-0.5 rounded bg-blue-600 text-white">
                          Point-and-Click Guide
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-700 font-sans leading-relaxed">
                        You don't need to format spreadsheets or edit CSV templates to manage your examinations.
                        With the <strong>Dropdown Menu Method</strong>, exam coordinators and registrars can set up examination cycles, register courses across all 12 academic departments, enroll students, and filter timetables entirely using simple point-and-click dropdown menus.
                      </p>
                    </div>
                  </div>
                </div>

                {/* 6 Dropdown Menu Steps */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Step 1 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-900 border border-blue-200">
                          DROPDOWN 1
                        </span>
                        <Calendar className="w-4 h-4 text-blue-600" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        1. Exam Cycle Dropdown
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        Use the <strong>Cycle Picker Dropdown</strong> at the top of any page to switch between examination periods (e.g., <em>June 2026 Finals</em> or <em>Winter 2026 Resits</em>). All time slots, courses, and timetables are scoped to your selected cycle.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-mono">
                      Location: Header Bar (Top-Right)
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-900 border border-indigo-200">
                          DROPDOWN 2
                        </span>
                        <Building2 className="w-4 h-4 text-indigo-600" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        2. Department & Semester Dropdowns
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        In <strong>Students</strong> or <strong>Subjects</strong>, click <em>Register Student</em> or <em>Add Subject</em>. Select the <strong>Department Dropdown</strong> (CS, EE, ME, CE, IT, AI, BME, CHE, MATH, PHYS, CHEM, MGMT) and <strong>Semester Dropdown</strong> (1–8) with zero typing.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-mono">
                      Location: /students & /subjects Modals
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-200">
                          DROPDOWN 3
                        </span>
                        <UserCheck className="w-4 h-4 text-emerald-600" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        3. Student Enrollment Dropdowns
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        Click <em>Enroll Student</em> on the Students page. Pick the student from the <strong>Student Dropdown</strong>, the course from the <strong>Subject Dropdown</strong>, and cycle from the <strong>Cycle Dropdown</strong>. The conflict graph connects the courses automatically!
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-mono">
                      Location: Students Page → Enroll Button
                    </div>
                  </div>

                  {/* Step 4 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-200">
                          DROPDOWN 4
                        </span>
                        <Layers className="w-4 h-4 text-amber-600" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        4. Algorithm Selector Dropdown
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        On <strong>Generate Schedule</strong> or <strong>Algorithm Lab</strong>, select your solver from the <strong>Algorithm Dropdown</strong>: <em>DSATUR (Optimal)</em>, <em>Welsh–Powell</em>, or <em>Greedy First-Fit</em>. Click Generate to color vertices into clash-free slots in seconds.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-mono">
                      Location: /generate & /lab Selectors
                    </div>
                  </div>

                  {/* Step 5 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-900 border border-purple-200">
                          DROPDOWN 5
                        </span>
                        <Filter className="w-4 h-4 text-purple-600" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        5. Department Timetable Filter Dropdown
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        On the <strong>Examination Timetable Grid</strong>, use the <strong>Department Filter Dropdown</strong> to view <em>All Departments</em> simultaneously or filter down to any single department (e.g. ME, AI, MATH, CHE, EE) to inspect sessions, dates, and student headcounts.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-mono">
                      Location: /timetable Filter Bar
                    </div>
                  </div>

                  {/* Step 6 */}
                  <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper)] flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-900 border border-teal-200">
                          DROPDOWN 6
                        </span>
                        <CheckCircle2 className="w-4 h-4 text-teal-600" />
                      </div>
                      <h4 className="font-display text-base text-[var(--color-ink)] font-medium">
                        6. Version Switcher & Move Slot Dropdowns
                      </h4>
                      <p className="text-xs text-[var(--color-ink-2)] font-sans leading-relaxed">
                        Switch between candidate timetables using the <strong>Version Switcher Dropdown</strong>. In Edit Mode, click any exam card and use the <strong>Candidate Slot Dropdown</strong> to move exams with instant real-time clash verification.
                      </p>
                    </div>
                    <div className="pt-2 border-t border-[var(--color-rule)] text-[11px] text-[var(--color-muted)] font-mono">
                      Location: /timetable Edit Mode Modal
                    </div>
                  </div>
                </div>

                {/* Direct Action Links */}
                <div className="p-4 rounded border border-[var(--color-rule)] bg-[var(--color-paper-2)] flex flex-wrap items-center justify-between gap-3 text-xs font-sans">
                  <div className="flex items-center gap-2">
                    <SlidersHorizontal className="w-4 h-4 text-[var(--color-accent)] shrink-0" />
                    <span>
                      <strong>Ready to use the Dropdown Menu Method?</strong> Try direct dropdown actions in the system:
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to="/students"
                      className="px-3 py-1.5 rounded border border-[var(--color-ink)] bg-white text-[var(--color-ink)] font-medium hover:bg-slate-50 transition-colors flex items-center gap-1.5"
                    >
                      <span>Enroll Students (Dropdown)</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                    <Link
                      to="/timetable"
                      className="px-3.5 py-1.5 bg-[var(--color-accent)] text-white font-medium rounded hover:bg-[var(--color-accent-deep)] transition-colors flex items-center gap-1.5"
                    >
                      <span>Open Timetable Filter Dropdown</span>
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
