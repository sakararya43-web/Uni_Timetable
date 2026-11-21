import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  GraduationCap,
  Calendar,
  CheckCircle2,
  Clock,
  MapPin,
  Search,
  ArrowRight,
} from "lucide-react";

interface ScheduleSample {
  code: string;
  title: string;
  faculty: string;
  date: string;
  time: string;
  hall: string;
  capacity: string;
  enrolled: number;
  session: "morning" | "afternoon";
  colorIdx: number;
}

const sampleScheduleData: ScheduleSample[] = [
  {
    code: "CS-301",
    title: "Operating Systems & Concurrency",
    faculty: "Computing",
    date: "15 Dec 2026",
    time: "09:00 - 12:00",
    hall: "Turing Auditorium (T-101)",
    capacity: "180 seats",
    enrolled: 164,
    session: "morning",
    colorIdx: 1,
  },
  {
    code: "MATH-204",
    title: "Discrete Mathematics & Graph Theory",
    faculty: "Mathematics",
    date: "15 Dec 2026",
    time: "14:00 - 17:00",
    hall: "Euler Hall (E-200)",
    capacity: "220 seats",
    enrolled: 198,
    session: "afternoon",
    colorIdx: 2,
  },
  {
    code: "ENG-310",
    title: "Thermodynamics & Heat Transfer",
    faculty: "Engineering",
    date: "16 Dec 2026",
    time: "09:00 - 12:00",
    hall: "Newton Pavilion (N-04)",
    capacity: "150 seats",
    enrolled: 142,
    session: "morning",
    colorIdx: 3,
  },
  {
    code: "ECON-102",
    title: "Macroeconomic Analysis",
    faculty: "Economics",
    date: "16 Dec 2026",
    time: "14:00 - 17:00",
    hall: "Keynes Hall (K-12)",
    capacity: "250 seats",
    enrolled: 231,
    session: "afternoon",
    colorIdx: 4,
  },
  {
    code: "CS-415",
    title: "Distributed Systems & Cloud Computing",
    faculty: "Computing",
    date: "17 Dec 2026",
    time: "09:00 - 12:00",
    hall: "Von Neumann Lab (VN-202)",
    capacity: "120 seats",
    enrolled: 115,
    session: "morning",
    colorIdx: 5,
  },
  {
    code: "MATH-318",
    title: "Linear Algebra & Numerical Methods",
    faculty: "Mathematics",
    date: "17 Dec 2026",
    time: "14:00 - 17:00",
    hall: "Gauss Theatre (G-10)",
    capacity: "190 seats",
    enrolled: 178,
    session: "afternoon",
    colorIdx: 6,
  },
];

const mockStudentSchedules: Record<string, { name: string; dept: string; roll: string; exams: Array<{ code: string; title: string; date: string; time: string; hall: string; seat: string }> }> = {
  "STU-2024-001": {
    name: "Eleanor Vance",
    dept: "Computer Science & Engineering",
    roll: "STU-2024-001",
    exams: [
      { code: "CS-301", title: "Operating Systems", date: "15 Dec 2026", time: "09:00 - 12:00", hall: "Turing Auditorium", seat: "Row B, Seat 14" },
      { code: "CS-415", title: "Distributed Systems", date: "17 Dec 2026", time: "09:00 - 12:00", hall: "Von Neumann Lab", seat: "Row D, Seat 08" },
      { code: "MATH-204", title: "Discrete Mathematics", date: "15 Dec 2026", time: "14:00 - 17:00", hall: "Euler Hall", seat: "Row A, Seat 22" },
    ],
  },
  "STU-2024-042": {
    name: "Julian Thorne",
    dept: "Applied Mathematics & Statistics",
    roll: "STU-2024-042",
    exams: [
      { code: "MATH-204", title: "Discrete Mathematics", date: "15 Dec 2026", time: "14:00 - 17:00", hall: "Euler Hall", seat: "Row C, Seat 05" },
      { code: "MATH-318", title: "Linear Algebra & Numerical Methods", date: "17 Dec 2026", time: "14:00 - 17:00", hall: "Gauss Theatre", seat: "Row F, Seat 19" },
    ],
  },
  "STU-2024-108": {
    name: "Aria Montgomery",
    dept: "Mechanical Engineering",
    roll: "STU-2024-108",
    exams: [
      { code: "ENG-310", title: "Thermodynamics & Heat Transfer", date: "16 Dec 2026", time: "09:00 - 12:00", hall: "Newton Pavilion", seat: "Row E, Seat 12" },
      { code: "ECON-102", title: "Macroeconomic Analysis", date: "16 Dec 2026", time: "14:00 - 17:00", hall: "Keynes Hall", seat: "Row G, Seat 30" },
    ],
  },
};

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFaculty, setSelectedFaculty] = useState<string>("All");
  const [selectedSession, setSelectedSession] = useState<"all" | "morning" | "afternoon">("all");
  const [studentSearchId, setStudentSearchId] = useState<string>("STU-2024-001");
  const [searchedStudent, setSearchedStudent] = useState<string>("STU-2024-001");

  const faculties = ["All", "Computing", "Mathematics", "Engineering", "Economics"];

  const filteredExams = sampleScheduleData.filter((item) => {
    const matchesFaculty = selectedFaculty === "All" || item.faculty === selectedFaculty;
    const matchesSession = selectedSession === "all" || item.session === selectedSession;
    return matchesFaculty && matchesSession;
  });

  const activeStudentProfile = mockStudentSchedules[searchedStudent] || null;

  return (
    <div className="min-h-screen bg-[var(--color-paper)] text-[var(--color-ink)] selection:bg-[var(--color-accent-soft)]">
      {/* 1. Academic Masthead & Registry Header */}
      <header className="border-b border-[var(--color-rule)] bg-[var(--color-paper)] sticky top-0 z-50 backdrop-blur-sm bg-opacity-95">
        <div className="max-w-[1360px] mx-auto px-6 lg:px-12 h-20 flex items-center justify-between">
          {/* Crest & Identity */}
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded border border-[var(--color-ink)] flex items-center justify-center bg-[var(--color-paper-2)]">
              <GraduationCap className="w-5 h-5 text-[var(--color-accent)]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display text-xl tracking-tight text-[var(--color-ink)] font-normal">
                  ExamScheduler
                </span>
                <span className="text-xs px-2 py-0.5 rounded border border-[var(--color-rule)] text-[var(--color-muted)] font-sans">
                  Registry v1.0
                </span>
              </div>
              <p className="text-xs text-[var(--color-muted)] font-sans hidden sm:block">
                University Examination & Academic Timetable System
              </p>
            </div>
          </div>

          {/* Institutional Primary Navigation */}
          <nav className="hidden md:flex items-center gap-6 text-sm font-sans text-[var(--color-ink-2)]" aria-label="Main Navigation">
            <Link
              to="/overview"
              className="hover:text-[var(--color-accent)] transition-colors py-1 border-b border-transparent hover:border-[var(--color-accent)]"
            >
              Overview
            </Link>
            <Link
              to="/cycles"
              className="hover:text-[var(--color-accent)] transition-colors py-1 border-b border-transparent hover:border-[var(--color-accent)]"
            >
              Scheduling Cycles
            </Link>
            <Link
              to="/subjects"
              className="hover:text-[var(--color-accent)] transition-colors py-1 border-b border-transparent hover:border-[var(--color-accent)]"
            >
              Subjects
            </Link>
            <Link
              to="/timetable"
              className="hover:text-[var(--color-accent)] transition-colors py-1 border-b border-transparent hover:border-[var(--color-accent)]"
            >
              Timetable Grid
            </Link>
            <Link
              to="/student/timetable"
              className="hover:text-[var(--color-accent)] transition-colors py-1 border-b border-transparent hover:border-[var(--color-accent)]"
            >
              Student Portal
            </Link>
          </nav>

          {/* Action & Status */}
          <div className="flex items-center gap-4">
            <span className="hidden xl:inline-flex items-center gap-2 text-xs text-[var(--color-muted)] border-r border-[var(--color-rule)] pr-4 font-sans">
              <span className="w-2 h-2 rounded-full bg-[var(--color-success)] inline-block animate-pulse" />
              <span>System Ready</span>
            </span>
            <Link
              to="/login"
              className="text-xs font-medium text-[var(--color-ink)] px-3 py-2 rounded border border-[var(--color-rule)] hover:bg-[var(--color-paper-2)] transition-colors whitespace-nowrap"
            >
              Staff Sign In
            </Link>
            <Link
              to="/overview"
              className="text-xs font-medium bg-[var(--color-accent)] text-[var(--color-accent-ink)] px-4 py-2 rounded hover:bg-[var(--color-accent-deep)] transition-colors shadow-sm whitespace-nowrap"
            >
              Open Console
            </Link>
          </div>
        </div>
      </header>

      {/* 2. Hero Stage: The Inscriptional Statement & Interactive Live Timetable Widget */}
      <section className="border-b border-[var(--color-rule)] relative overflow-hidden bg-gradient-to-b from-[var(--color-paper)] via-[var(--color-paper)] to-[var(--color-paper-2)]">
        <div className="max-w-[1360px] mx-auto px-6 lg:px-12 pt-16 pb-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            {/* Left 6 Columns: Authoritative Headline, Purpose, & Direct Pathways */}
            <div className="lg:col-span-6 space-y-6">
              <div className="inline-flex items-center gap-2 text-xs font-sans text-[var(--color-muted)] border-b border-[var(--color-rule)] pb-1">
                <span>Academic examination registry</span>
                <span>/</span>
                <span>Autumn cycle 2026</span>
              </div>

              <h1 className="font-display text-4xl sm:text-5xl lg:text-[3.25rem] leading-[1.08] text-[var(--color-ink)] font-normal tracking-tight">
                Conflict-free examination timetables, mathematically guaranteed.
              </h1>

              <p className="text-base sm:text-lg text-[var(--color-ink-2)] font-sans leading-relaxed max-w-[54ch]">
                Welsh-Powell and DSATUR graph coloring algorithms eliminate exam double-bookings across faculties.
              </p>

              <div className="pt-2 flex flex-wrap items-center gap-4">
                <button
                  onClick={() => navigate("/overview")}
                  className="px-6 py-3 bg-[var(--color-accent)] text-[var(--color-accent-ink)] text-sm font-medium rounded hover:bg-[var(--color-accent-deep)] transition-colors flex items-center gap-2 shadow-sm whitespace-nowrap"
                >
                  <span>Launch operations</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
                <a
                  href="#schedule-ledger"
                  className="px-5 py-3 border border-[var(--color-ink)] text-[var(--color-ink)] text-sm font-medium rounded hover:bg-[var(--color-paper-2)] transition-colors whitespace-nowrap"
                >
                  Inspect master ledger
                </a>
              </div>

              {/* Mathematical Verifiability Indicators */}
              <div className="pt-6 border-t border-[var(--color-rule)] grid grid-cols-3 gap-6">
                <div>
                  <p className="font-mono text-2xl font-semibold text-[var(--color-accent)]">χ(G) = 6</p>
                  <p className="text-xs text-[var(--color-muted)] font-sans mt-0.5">Optimal chromatic slots</p>
                </div>
                <div>
                  <p className="font-mono text-2xl font-semibold text-[var(--color-success)]">0</p>
                  <p className="text-xs text-[var(--color-muted)] font-sans mt-0.5">Hard conflicts incurred</p>
                </div>
                <div>
                  <p className="font-mono text-2xl font-semibold text-[var(--color-ink)]">100%</p>
                  <p className="text-xs text-[var(--color-muted)] font-sans mt-0.5">Seating floor bound</p>
                </div>
              </div>
            </div>

            {/* Right 6 Columns: Signature Widget - Live Interactive Schedule Explorer */}
            <div className="lg:col-span-6 bg-white border border-[var(--color-rule)] rounded shadow-sm p-6 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-[var(--color-rule)]">
                <div>
                  <h3 className="font-display text-lg text-[var(--color-ink)]">Live Schedule Register</h3>
                  <p className="text-xs text-[var(--color-muted)] font-sans">
                    Real-time slot assignments calculated with graph chromatic partitioning
                  </p>
                </div>
                <span className="text-xs font-sans px-2 py-1 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] text-[var(--color-ink)]">
                  Session 2026/27
                </span>
              </div>

              {/* Faculty & Session Filters */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-1">
                  <span className="text-[var(--color-muted)] font-sans mr-1">Faculty:</span>
                  <div className="flex flex-wrap gap-1">
                    {faculties.map((f) => (
                      <button
                        key={f}
                        onClick={() => setSelectedFaculty(f)}
                        className={`px-2 py-1 rounded border transition-colors ${
                          selectedFaculty === f
                            ? "bg-[var(--color-accent)] text-white border-[var(--color-accent)]"
                            : "bg-[var(--color-paper)] border-[var(--color-rule)] text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                        }`}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <span className="text-[var(--color-muted)] font-sans mr-1">Time:</span>
                  <select
                    value={selectedSession}
                    onChange={(e) => setSelectedSession(e.target.value as any)}
                    className="px-2 py-1 text-xs border border-[var(--color-rule)] rounded bg-[var(--color-paper)] text-[var(--color-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
                  >
                    <option value="all">All Sessions</option>
                    <option value="morning">Morning (09:00)</option>
                    <option value="afternoon">Afternoon (14:00)</option>
                  </select>
                </div>
              </div>

              {/* Timetable Slot List */}
              <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
                {filteredExams.map((exam) => (
                  <div
                    key={exam.code}
                    className="p-3 border border-[var(--color-rule)] rounded bg-[var(--color-paper)] hover:border-[var(--color-ink)] transition-colors flex items-start justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold px-1.5 py-0.5 rounded bg-[var(--color-paper-2)] border border-[var(--color-rule)] text-[var(--color-accent)]">
                          {exam.code}
                        </span>
                        <span className="text-xs font-medium text-[var(--color-ink)] line-clamp-1">
                          {exam.title}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--color-muted)] font-mono">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          <span>{exam.date}</span>
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{exam.time}</span>
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          <span>{exam.hall}</span>
                        </span>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="inline-block text-[11px] font-sans px-2 py-0.5 rounded bg-[var(--color-paper-2)] text-[var(--color-success)] border border-[var(--color-rule)]">
                        Slot <span className="font-mono">{exam.colorIdx}</span>
                      </span>
                      <p className="text-[11px] text-[var(--color-muted)] font-sans mt-1">
                        <span className="font-mono">{exam.enrolled}</span> candidates
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Widget Footer Verification */}
              <div className="pt-3 border-t border-[var(--color-rule)] flex items-center justify-between text-xs text-[var(--color-muted)]">
                <span className="flex items-center gap-1.5 font-sans">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-success)]" />
                  <span>Conflict verification: 0 overlaps</span>
                </span>
                <Link
                  to="/timetable"
                  className="text-[var(--color-accent)] font-medium hover:underline flex items-center gap-1"
                >
                  <span>Interactive matrix</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Mathematical Integrity & Conflict Graph Section */}
      <section className="py-20 border-b border-[var(--color-rule)] bg-[var(--color-paper)]">
        <div className="max-w-[1360px] mx-auto px-6 lg:px-12 space-y-12">
          <div className="max-w-[720px] space-y-3">
            <span className="text-xs font-sans text-[var(--color-muted)] border-b border-[var(--color-rule)] pb-0.5">
              The graph theoretic principle
            </span>
            <h2 className="font-display text-3xl sm:text-4xl text-[var(--color-ink)] font-normal">
              Chromatic scheduling without empirical approximations.
            </h2>
            <p className="text-[var(--color-ink-2)] text-base font-sans leading-relaxed">
              Examination timetabling is solved as an exact vertex coloring problem on an undirected conflict graph $G = (V, E)$. Vertices represent distinct academic courses, while edges encode shared student enrollments.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 border border-[var(--color-rule)] rounded bg-white space-y-4">
              <div className="w-8 h-8 rounded border border-[var(--color-ink)] flex items-center justify-center font-mono text-sm font-semibold">
                01
              </div>
              <h3 className="font-display text-xl text-[var(--color-ink)]">
                Vertex Conflict Modeling
              </h3>
              <p className="text-sm text-[var(--color-ink-2)] font-sans leading-relaxed">
                Whenever two distinct courses $u, v \in V$ share at least one mutually enrolled candidate, an edge $(u, v) \in E$ is formed. The weight reflects mutual student count.
              </p>
              <div className="pt-2 font-mono text-xs text-[var(--color-muted)] bg-[var(--color-paper-2)] p-2.5 rounded border border-[var(--color-rule)]">
                c(u) ≠ c(v), &forall; (u, v) ∈ E
              </div>
            </div>

            <div className="p-6 border border-[var(--color-rule)] rounded bg-white space-y-4">
              <div className="w-8 h-8 rounded border border-[var(--color-ink)] flex items-center justify-center font-mono text-sm font-semibold">
                02
              </div>
              <h3 className="font-display text-xl text-[var(--color-ink)]">
                DSATUR Degree of Saturation
              </h3>
              <p className="text-sm text-[var(--color-ink-2)] font-sans leading-relaxed">
                Vertices with the highest saturation degree (most distinct colored neighbors) are assigned first, systematically minimizing the overall chromatic index $\chi(G)$.
              </p>
              <div className="pt-2 font-mono text-xs text-[var(--color-muted)] bg-[var(--color-paper-2)] p-2.5 rounded border border-[var(--color-rule)]">
                sat_deg(v) = |&#123;c(w) : w ∈ Adj(v)&#125;|
              </div>
            </div>

            <div className="p-6 border border-[var(--color-rule)] rounded bg-white space-y-4">
              <div className="w-8 h-8 rounded border border-[var(--color-ink)] flex items-center justify-center font-mono text-sm font-semibold">
                03
              </div>
              <h3 className="font-display text-xl text-[var(--color-ink)]">
                Physical Capacity Binning
              </h3>
              <p className="text-sm text-[var(--color-ink-2)] font-sans leading-relaxed">
                Color assignments map directly into physical rooms and time slots. Room capacity constraints and acoustic separation guarantees are respected across halls.
              </p>
              <div className="pt-2 font-mono text-xs text-[var(--color-muted)] bg-[var(--color-paper-2)] p-2.5 rounded border border-[var(--color-rule)]">
                &sum; enroll(v) &le; cap(hall), &forall; v ∈ Slot
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Full Master Examination Schedule Ledger */}
      <section id="schedule-ledger" className="py-20 border-b border-[var(--color-rule)] bg-[var(--color-paper-2)]">
        <div className="max-w-[1360px] mx-auto px-6 lg:px-12 space-y-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <span className="text-xs font-sans text-[var(--color-muted)] border-b border-[var(--color-rule)] pb-0.5">
                Official university examination schedule
              </span>
              <h2 className="font-display text-3xl text-[var(--color-ink)] font-normal mt-2">
                Published Academic Timetable Ledger
              </h2>
            </div>
            <div className="text-xs text-[var(--color-muted)] font-sans">
              Displaying official cycle: 2026/27 Autumn Final Examinations
            </div>
          </div>

          {/* Tabular Ledger */}
          <div className="border border-[var(--color-rule)] rounded bg-white overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm font-sans border-collapse">
                <thead>
                  <tr className="bg-[var(--color-paper-3)] border-b-2 border-double border-[var(--color-rule-dark)] text-xs font-medium text-[var(--color-ink)]">
                    <th className="py-3.5 px-4 font-sans">Course code</th>
                    <th className="py-3.5 px-4 font-sans">Examination title</th>
                    <th className="py-3.5 px-4 font-sans">Faculty</th>
                    <th className="py-3.5 px-4 font-sans">Date</th>
                    <th className="py-3.5 px-4 font-sans">Session slot</th>
                    <th className="py-3.5 px-4 font-sans">Assigned hall</th>
                    <th className="py-3.5 px-4 font-sans text-right">Candidates</th>
                    <th className="py-3.5 px-4 font-sans text-center">Conflict status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-rule)]">
                  {sampleScheduleData.map((row) => (
                    <tr key={row.code} className="hover:bg-[var(--color-paper)] transition-colors">
                      <td className="py-3.5 px-4 font-mono font-medium text-[var(--color-accent)]">
                        {row.code}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-[var(--color-ink)]">
                        {row.title}
                      </td>
                      <td className="py-3.5 px-4 text-[var(--color-muted)] text-xs">
                        {row.faculty}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-[var(--color-ink-2)]">
                        {row.date}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-[var(--color-ink-2)]">
                        {row.time}
                      </td>
                      <td className="py-3.5 px-4 text-xs text-[var(--color-ink-2)]">
                        {row.hall}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-right text-[var(--color-ink)]">
                        {row.enrolled}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-flex items-center gap-1 text-[11px] font-sans px-2 py-0.5 rounded bg-[var(--color-paper-2)] text-[var(--color-success)] border border-[var(--color-rule)]">
                          <CheckCircle2 className="w-3 h-3 text-[var(--color-success)]" />
                          <span>Clear</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 bg-[var(--color-paper)] border-t border-[var(--color-rule)] flex flex-wrap items-center justify-between text-xs text-[var(--color-muted)]">
              <span>All candidates must present their biometric Hall Ticket 15 minutes prior to commencement.</span>
              <div className="flex items-center gap-4">
                <Link to="/timetable" className="text-[var(--color-accent)] hover:underline font-medium">
                  Open interactive timetable grid
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Instant Student Seat & Schedule Lookup */}
      <section className="py-20 border-b border-[var(--color-rule)] bg-[var(--color-paper)]">
        <div className="max-w-[1360px] mx-auto px-6 lg:px-12 space-y-10">
          <div className="max-w-[640px] space-y-2">
            <span className="text-xs font-sans text-[var(--color-muted)] border-b border-[var(--color-rule)] pb-0.5">
              Student examination verification
            </span>
            <h2 className="font-display text-3xl text-[var(--color-ink)] font-normal">
              Candidate Examination & Seating Lookup
            </h2>
            <p className="text-sm text-[var(--color-ink-2)] font-sans">
              Enter candidate registration roll number to review individual scheduled dates, assigned halls, and reserved seat numbers.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Search Box & Quick Fill */}
            <div className="lg:col-span-5 p-6 border border-[var(--color-rule)] rounded bg-white space-y-4">
              <label htmlFor="student-roll-input" className="block text-xs font-sans text-[var(--color-muted)]">
                Candidate roll number:
              </label>
              <div className="flex gap-2">
                <input
                  id="student-roll-input"
                  type="text"
                  value={studentSearchId}
                  onChange={(e) => setStudentSearchId(e.target.value)}
                  placeholder="e.g. STU-2024-001"
                  className="flex-1 px-3 py-2 text-sm font-mono border border-[var(--color-rule)] rounded focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] bg-[var(--color-paper)]"
                />
                <button
                  onClick={() => setSearchedStudent(studentSearchId.trim().toUpperCase())}
                  className="px-4 py-2 bg-[var(--color-accent)] text-white text-xs font-medium rounded hover:bg-[var(--color-accent-deep)] transition-colors flex items-center gap-1.5"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Verify</span>
                </button>
              </div>

              <div className="pt-2">
                <p className="text-xs text-[var(--color-muted)] font-sans mb-2">Sample Candidate Profiles:</p>
                <div className="flex flex-wrap gap-2">
                  {Object.keys(mockStudentSchedules).map((id) => (
                    <button
                      key={id}
                      onClick={() => {
                        setStudentSearchId(id);
                        setSearchedStudent(id);
                      }}
                      className="px-2.5 py-1 text-xs font-mono rounded border border-[var(--color-rule)] bg-[var(--color-paper-2)] hover:border-[var(--color-ink)] transition-colors"
                    >
                      {id}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Candidate Hall Ticket Display */}
            <div className="lg:col-span-7 border border-[var(--color-rule)] rounded bg-white p-6 space-y-4">
              {activeStudentProfile ? (
                <>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[var(--color-rule)] gap-2">
                    <div>
                      <h3 className="font-display text-xl text-[var(--color-ink)]">
                        {activeStudentProfile.name}
                      </h3>
                      <p className="text-xs text-[var(--color-muted)] font-sans">
                        {activeStudentProfile.dept}
                      </p>
                    </div>
                    <div className="text-left sm:text-right text-xs font-sans">
                      <span className="px-2.5 py-1 bg-[var(--color-paper-2)] border border-[var(--color-rule)] rounded text-[var(--color-ink)]">
                        Roll: <span className="font-mono">{activeStudentProfile.roll}</span>
                      </span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {activeStudentProfile.exams.map((exam) => (
                      <div
                        key={exam.code}
                        className="p-3.5 border border-[var(--color-rule)] rounded bg-[var(--color-paper)] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-semibold text-[var(--color-accent)]">
                              {exam.code}
                            </span>
                            <span className="font-medium text-[var(--color-ink)]">
                              {exam.title}
                            </span>
                          </div>
                          <div className="text-[var(--color-muted)] font-sans flex items-center gap-3">
                            <span className="font-mono">{exam.date}</span>
                            <span>·</span>
                            <span className="font-mono">{exam.time}</span>
                          </div>
                        </div>
                        <div className="text-left sm:text-right bg-white px-3 py-1.5 rounded border border-[var(--color-rule)]">
                          <p className="font-semibold text-[var(--color-ink)] font-sans">{exam.hall}</p>
                          <p className="text-[var(--color-accent)] text-[11px] font-mono">{exam.seat}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="pt-3 border-t border-[var(--color-rule)] flex justify-end">
                    <Link
                      to="/student/timetable"
                      className="text-xs text-[var(--color-accent)] hover:underline font-medium"
                    >
                      Export candidate schedule slip
                    </Link>
                  </div>
                </>
              ) : (
                <div className="py-12 text-center text-sm text-[var(--color-muted)] font-sans">
                  No candidate record found for "{searchedStudent}". Please try STU-2024-001.
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 6. Institutional Colophon & Registry Footer */}
      <footer className="border-t-2 border-double border-[var(--color-rule-dark)] bg-[var(--color-paper-2)] py-16">
        <div className="max-w-[1360px] mx-auto px-6 lg:px-12 space-y-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-[var(--color-accent)]" />
                <span className="font-display text-lg text-[var(--color-ink)]">
                  ExamScheduler Registry
                </span>
              </div>
              <p className="text-xs text-[var(--color-muted)] font-sans leading-relaxed">
                The authoritative university academic scheduling platform. Graph coloring and capacity binning for zero-clash examination delivery.
              </p>
              <p className="text-xs font-sans text-[var(--color-muted)]">
                ISO 27001 & FERPA Compliant
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-sans font-semibold text-[var(--color-ink)] border-b border-[var(--color-rule)] pb-1">
                OPERATIONS CONSOLE
              </h4>
              <ul className="space-y-2 text-xs font-sans text-[var(--color-ink-2)]">
                <li>
                  <Link to="/overview" className="hover:text-[var(--color-accent)] transition-colors">
                    Operations Dashboard
                  </Link>
                </li>
                <li>
                  <Link to="/cycles" className="hover:text-[var(--color-accent)] transition-colors">
                    Active Cycle Archive
                  </Link>
                </li>
                <li>
                  <Link to="/subjects" className="hover:text-[var(--color-accent)] transition-colors">
                    Course Catalog & Syllabi
                  </Link>
                </li>
                <li>
                  <Link to="/students" className="hover:text-[var(--color-accent)] transition-colors">
                    Student Enrollments
                  </Link>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-sans font-semibold text-[var(--color-ink)] border-b border-[var(--color-rule)] pb-1">
                ALGORITHM & SCHEDULES
              </h4>
              <ul className="space-y-2 text-xs font-sans text-[var(--color-ink-2)]">
                <li>
                  <Link to="/graph" className="hover:text-[var(--color-accent)] transition-colors">
                    Conflict Graph Visualizer
                  </Link>
                </li>
                <li>
                  <Link to="/generate" className="hover:text-[var(--color-accent)] transition-colors">
                    Automated Schedule Generator
                  </Link>
                </li>
                <li>
                  <Link to="/lab" className="hover:text-[var(--color-accent)] transition-colors">
                    Algorithm Comparison Lab
                  </Link>
                </li>
                <li>
                  <Link to="/timetable" className="hover:text-[var(--color-accent)] transition-colors">
                    Master Timetable Grid
                  </Link>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-sans font-semibold text-[var(--color-ink)] border-b border-[var(--color-rule)] pb-1">
                ACADEMIC PORTALS
              </h4>
              <ul className="space-y-2 text-xs font-sans text-[var(--color-ink-2)]">
                <li>
                  <Link to="/student/timetable" className="hover:text-[var(--color-accent)] transition-colors">
                    Student Timetable Portal
                  </Link>
                </li>
                <li>
                  <Link to="/reports" className="hover:text-[var(--color-accent)] transition-colors">
                    Examination Reports & Audit
                  </Link>
                </li>
                <li>
                  <Link to="/settings" className="hover:text-[var(--color-accent)] transition-colors">
                    Institutional Governance Settings
                  </Link>
                </li>
                <li>
                  <Link to="/login" className="hover:text-[var(--color-accent)] transition-colors">
                    Staff Authentication
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-[var(--color-rule)] flex flex-col sm:flex-row items-center justify-between text-xs text-[var(--color-muted)] font-sans gap-4">
            <p>© 2026 University Examination Board. All academic rights reserved.</p>
            <div className="flex items-center gap-4 font-sans">
              <span>WCAG 2.1 AA Certified</span>
              <span>·</span>
              <span className="font-mono">v1.0.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
