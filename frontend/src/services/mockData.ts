import {
  SchedulingCycle,
  Department,
  Subject,
  Student,
  Enrollment,
  TimeSlot,
  ScheduleVersionSummary,
  ScheduleVersionDetail,
  CycleSummaryReport,
  UserProfile,
  StudentTimetableResponse,
  AuditLogItem,
  ExamAssignmentItem,
} from "../types/api";

export const mockCycles: SchedulingCycle[] = [
  {
    id: "cycle-demo-2026",
    name: "June 2026 Academic Final Examinations",
    academicYearId: "ay-2026",
    startDate: "2026-06-10",
    endDate: "2026-06-20",
    status: "published",
    timezone: "UTC",
    graphStale: false,
    dataVersion: 1,
    configurationJson: {
      examDaysOfWeek: [1, 2, 3, 4, 5, 6],
      sessions: [
        { label: "Morning", startTime: "09:00", endTime: "12:00", enabled: true },
        { label: "Afternoon", startTime: "14:00", endTime: "17:00", enabled: true },
      ],
      holidays: ["2026-06-14"],
      maxExamsPerSession: 4,
      maxExamsPerDay: 8,
    },
    createdAt: "2026-06-01T08:00:00Z",
  },
];

export const mockAcademicYears: Array<{ id: string; name: string }> = [
  { id: "ay-2026", name: "2025-2026 Academic Year" },
];

export const mockDepartments: Department[] = [
  { id: "dept-cs", code: "CS", name: "Department of Computer Science", status: "active" },
  { id: "dept-ee", code: "EE", name: "Department of Electrical Engineering", status: "active" },
  { id: "dept-math", code: "MATH", name: "Department of Mathematics", status: "active" },
];

export const mockSubjects: Subject[] = [
  {
    id: "sub-cs101",
    subjectCode: "CS101",
    subjectName: "Introduction to Programming",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 1,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 20,
    conflictDegree: 3,
  },
  {
    id: "sub-cs102",
    subjectCode: "CS102",
    subjectName: "Discrete Mathematics",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 1,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 20,
    conflictDegree: 4,
  },
  {
    id: "sub-cs201",
    subjectCode: "CS201",
    subjectName: "Data Structures & Algorithms",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 2,
    credits: 4.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 18,
    conflictDegree: 5,
  },
  {
    id: "sub-cs202",
    subjectCode: "CS202",
    subjectName: "Computer Organization & Architecture",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 2,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 18,
    conflictDegree: 4,
  },
  {
    id: "sub-cs301",
    subjectCode: "CS301",
    subjectName: "Operating Systems & Concurrency",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 3,
    credits: 4.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 28,
    conflictDegree: 7, // High degree hub exam
  },
  {
    id: "sub-cs302",
    subjectCode: "CS302",
    subjectName: "Database Management Systems",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 3,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 22,
    conflictDegree: 5,
  },
  {
    id: "sub-cs303",
    subjectCode: "CS303",
    subjectName: "Computer Networks & Protocols",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 3,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 19,
    conflictDegree: 4,
  },
  {
    id: "sub-cs401",
    subjectCode: "CS401",
    subjectName: "Advanced Machine Learning Capstone",
    departmentId: "dept-cs",
    departmentCode: "CS",
    semester: 4,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 8,
    conflictDegree: 0, // Isolated subject
  },
  {
    id: "sub-ee101",
    subjectCode: "EE101",
    subjectName: "Linear Circuit Analysis",
    departmentId: "dept-ee",
    departmentCode: "EE",
    semester: 1,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 15,
    conflictDegree: 3,
  },
  {
    id: "sub-ee102",
    subjectCode: "EE102",
    subjectName: "Digital Logic & Microprocessors",
    departmentId: "dept-ee",
    departmentCode: "EE",
    semester: 1,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 15,
    conflictDegree: 3,
  },
  {
    id: "sub-ee201",
    subjectCode: "EE201",
    subjectName: "Signals and Linear Systems",
    departmentId: "dept-ee",
    departmentCode: "EE",
    semester: 2,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 12,
    conflictDegree: 3,
  },
  {
    id: "sub-ee202",
    subjectCode: "EE202",
    subjectName: "Electromagnetic Fields & Waves",
    departmentId: "dept-ee",
    departmentCode: "EE",
    semester: 2,
    credits: 3.0,
    defaultDurationMinutes: 180,
    status: "active",
    enrollmentCount: 12,
    conflictDegree: 2,
  },
];

export const mockStudents: Student[] = Array.from({ length: 50 }, (_, i) => {
  const isCS = i < 30;
  const idx = i + 1;
  const num = isCS ? `CS-${idx.toString().padStart(3, "0")}` : `EE-${(idx - 30).toString().padStart(3, "0")}`;
  const sem = isCS ? (idx <= 10 ? 1 : idx <= 20 ? 2 : 3) : (idx <= 40 ? 1 : 2);
  return {
    id: `stu-${num.toLowerCase()}`,
    studentNumber: num,
    fullName: `Synthetic Candidate ${num}`,
    email: `student.${num.toLowerCase()}@university.edu`,
    departmentId: isCS ? "dept-cs" : "dept-ee",
    departmentCode: isCS ? "CS" : "EE",
    semester: sem,
    status: "active",
    enrollmentCount: 3 + (i % 2),
  };
});

export const mockTimeSlots: TimeSlot[] = [
  // 10 June 2026 (Wednesday)
  { id: "slot-01", schedulingCycleId: "cycle-demo-2026", date: "2026-06-10", startTime: "09:00", endTime: "12:00", durationMinutes: 180, sessionLabel: "Morning", slotIndex: 0, enabled: true, capacity: 200 },
  { id: "slot-02", schedulingCycleId: "cycle-demo-2026", date: "2026-06-10", startTime: "14:00", endTime: "17:00", durationMinutes: 180, sessionLabel: "Afternoon", slotIndex: 1, enabled: true, capacity: 200 },
  // 11 June 2026 (Thursday)
  { id: "slot-03", schedulingCycleId: "cycle-demo-2026", date: "2026-06-11", startTime: "09:00", endTime: "12:00", durationMinutes: 180, sessionLabel: "Morning", slotIndex: 2, enabled: true, capacity: 200 },
  { id: "slot-04", schedulingCycleId: "cycle-demo-2026", date: "2026-06-11", startTime: "14:00", endTime: "17:00", durationMinutes: 180, sessionLabel: "Afternoon", slotIndex: 3, enabled: true, capacity: 200 },
  // 12 June 2026 (Friday)
  { id: "slot-05", schedulingCycleId: "cycle-demo-2026", date: "2026-06-12", startTime: "09:00", endTime: "12:00", durationMinutes: 180, sessionLabel: "Morning", slotIndex: 4, enabled: true, capacity: 200 },
  { id: "slot-06", schedulingCycleId: "cycle-demo-2026", date: "2026-06-12", startTime: "14:00", endTime: "17:00", durationMinutes: 180, sessionLabel: "Afternoon", slotIndex: 5, enabled: true, capacity: 200 },
  // 13 June 2026 (Saturday)
  { id: "slot-07", schedulingCycleId: "cycle-demo-2026", date: "2026-06-13", startTime: "09:00", endTime: "12:00", durationMinutes: 180, sessionLabel: "Morning", slotIndex: 6, enabled: true, capacity: 200 },
  { id: "slot-08", schedulingCycleId: "cycle-demo-2026", date: "2026-06-13", startTime: "14:00", endTime: "17:00", durationMinutes: 180, sessionLabel: "Afternoon", slotIndex: 7, enabled: true, capacity: 200 },
  // 15 June 2026 (Monday)
  { id: "slot-09", schedulingCycleId: "cycle-demo-2026", date: "2026-06-15", startTime: "09:00", endTime: "12:00", durationMinutes: 180, sessionLabel: "Morning", slotIndex: 8, enabled: true, capacity: 200 },
  { id: "slot-10", schedulingCycleId: "cycle-demo-2026", date: "2026-06-15", startTime: "14:00", endTime: "17:00", durationMinutes: 180, sessionLabel: "Afternoon", slotIndex: 9, enabled: true, capacity: 200 },
  // 16 June 2026 (Tuesday)
  { id: "slot-11", schedulingCycleId: "cycle-demo-2026", date: "2026-06-16", startTime: "09:00", endTime: "12:00", durationMinutes: 180, sessionLabel: "Morning", slotIndex: 10, enabled: true, capacity: 200 },
  { id: "slot-12", schedulingCycleId: "cycle-demo-2026", date: "2026-06-16", startTime: "14:00", endTime: "17:00", durationMinutes: 180, sessionLabel: "Afternoon", slotIndex: 11, enabled: true, capacity: 200 },
];

export const initialAssignments: ExamAssignmentItem[] = [
  { id: "asg-01", scheduleVersionId: "ver-demo-1", examId: "exam-cs101", subjectCode: "CS101", subjectName: "Introduction to Programming", departmentCode: "CS", timeSlotId: "slot-01", slotDate: "2026-06-10", startTime: "09:00", endTime: "12:00", sessionLabel: "Morning", durationMinutes: 180, studentCount: 20, colorId: 1, locked: false, manualOverride: false },
  { id: "asg-02", scheduleVersionId: "ver-demo-1", examId: "exam-ee101", subjectCode: "EE101", subjectName: "Linear Circuit Analysis", departmentCode: "EE", timeSlotId: "slot-01", slotDate: "2026-06-10", startTime: "09:00", endTime: "12:00", sessionLabel: "Morning", durationMinutes: 180, studentCount: 15, colorId: 1, locked: false, manualOverride: false },
  { id: "asg-03", scheduleVersionId: "ver-demo-1", examId: "exam-cs102", subjectCode: "CS102", subjectName: "Discrete Mathematics", departmentCode: "CS", timeSlotId: "slot-02", slotDate: "2026-06-10", startTime: "14:00", endTime: "17:00", sessionLabel: "Afternoon", durationMinutes: 180, studentCount: 20, colorId: 2, locked: false, manualOverride: false },
  { id: "asg-04", scheduleVersionId: "ver-demo-1", examId: "exam-ee102", subjectCode: "EE102", subjectName: "Digital Logic & Microprocessors", departmentCode: "EE", timeSlotId: "slot-02", slotDate: "2026-06-10", startTime: "14:00", endTime: "17:00", sessionLabel: "Afternoon", durationMinutes: 180, studentCount: 15, colorId: 2, locked: false, manualOverride: false },
  { id: "asg-05", scheduleVersionId: "ver-demo-1", examId: "exam-cs201", subjectCode: "CS201", subjectName: "Data Structures & Algorithms", departmentCode: "CS", timeSlotId: "slot-03", slotDate: "2026-06-11", startTime: "09:00", endTime: "12:00", sessionLabel: "Morning", durationMinutes: 180, studentCount: 18, colorId: 3, locked: false, manualOverride: false },
  { id: "asg-06", scheduleVersionId: "ver-demo-1", examId: "exam-ee201", subjectCode: "EE201", subjectName: "Signals and Linear Systems", departmentCode: "EE", timeSlotId: "slot-03", slotDate: "2026-06-11", startTime: "09:00", endTime: "12:00", sessionLabel: "Morning", durationMinutes: 180, studentCount: 12, colorId: 3, locked: false, manualOverride: false },
  { id: "asg-07", scheduleVersionId: "ver-demo-1", examId: "exam-cs202", subjectCode: "CS202", subjectName: "Computer Organization & Architecture", departmentCode: "CS", timeSlotId: "slot-04", slotDate: "2026-06-11", startTime: "14:00", endTime: "17:00", sessionLabel: "Afternoon", durationMinutes: 180, studentCount: 18, colorId: 4, locked: false, manualOverride: false },
  { id: "asg-08", scheduleVersionId: "ver-demo-1", examId: "exam-ee202", subjectCode: "EE202", subjectName: "Electromagnetic Fields & Waves", departmentCode: "EE", timeSlotId: "slot-04", slotDate: "2026-06-11", startTime: "14:00", endTime: "17:00", sessionLabel: "Afternoon", durationMinutes: 180, studentCount: 12, colorId: 4, locked: false, manualOverride: false },
  { id: "asg-09", scheduleVersionId: "ver-demo-1", examId: "exam-cs301", subjectCode: "CS301", subjectName: "Operating Systems & Concurrency", departmentCode: "CS", timeSlotId: "slot-05", slotDate: "2026-06-12", startTime: "09:00", endTime: "12:00", sessionLabel: "Morning", durationMinutes: 180, studentCount: 28, colorId: 5, locked: true, manualOverride: false },
  { id: "asg-10", scheduleVersionId: "ver-demo-1", examId: "exam-cs302", subjectCode: "CS302", subjectName: "Database Management Systems", departmentCode: "CS", timeSlotId: "slot-06", slotDate: "2026-06-12", startTime: "14:00", endTime: "17:00", sessionLabel: "Afternoon", durationMinutes: 180, studentCount: 22, colorId: 6, locked: false, manualOverride: false },
  { id: "asg-11", scheduleVersionId: "ver-demo-1", examId: "exam-cs303", subjectCode: "CS303", subjectName: "Computer Networks & Protocols", departmentCode: "CS", timeSlotId: "slot-07", slotDate: "2026-06-13", startTime: "09:00", endTime: "12:00", sessionLabel: "Morning", durationMinutes: 180, studentCount: 19, colorId: 7, locked: false, manualOverride: false },
  { id: "asg-12", scheduleVersionId: "ver-demo-1", examId: "exam-cs401", subjectCode: "CS401", subjectName: "Advanced Machine Learning Capstone", departmentCode: "CS", timeSlotId: "slot-08", slotDate: "2026-06-13", startTime: "14:00", endTime: "17:00", sessionLabel: "Afternoon", durationMinutes: 180, studentCount: 8, colorId: 8, locked: false, manualOverride: false },
];

export const mockScheduleVersions: ScheduleVersionSummary[] = [
  {
    id: "ver-demo-1",
    versionNumber: 1,
    status: "Published",
    scheduleRunId: "run-demo-1",
    assignmentCount: 12,
    hardViolationCount: 0,
    softScore: 0,
    rowVersion: 1,
    publishedAt: "2026-06-05T10:00:00Z",
    createdAt: "2026-06-05T09:30:00Z",
  },
];

export const mockScheduleVersionDetails: Record<string, ScheduleVersionDetail> = {
  "ver-demo-1": {
    ...mockScheduleVersions[0],
    validationReport: {
      valid: true,
      hardViolations: [],
      softPenaltyTotal: 0,
      softBreakdown: [],
    },
    assignments: initialAssignments,
  },
};

export let activeScheduleVersionDetail: ScheduleVersionDetail = mockScheduleVersionDetails["ver-demo-1"];

// Dynamic Schedule Run Generator State
let runSequence = 1;
let lastRunDetails: {
  runId: string;
  algorithm: string;
  colorsUsed: number;
  softScore: number;
  assignments: ExamAssignmentItem[];
} | null = null;

export function generateDynamicScheduleRun(payload?: { algorithm?: string }): {
  id: string;
  schedulingCycleId: string;
  algorithm: string;
  executionTimeMs: number;
  colorsUsed: number;
  isValid: boolean;
  softScore: number;
  status: string;
  validationReport: {
    valid: boolean;
    hardViolations: Array<{ message: string }>;
    softBreakdown: Array<{ rule: string; penalty: number; occurrences?: number }>;
  };
} {
  const algo = (payload?.algorithm || "dsatur").toLowerCase();
  runSequence++;
  const runId = `run-${algo}-${Date.now().toString().slice(-4)}`;

  let colorsUsed = 6;
  let executionTimeMs = 1.84;
  let softScore = 0;
  let softBreakdown: Array<{ rule: string; penalty: number; occurrences?: number }> = [];

  // Generate varied algorithm profiles
  if (algo === "dsatur") {
    colorsUsed = 6;
    executionTimeMs = parseFloat((1.35 + Math.random() * 0.75).toFixed(2));
    softScore = 0.0;
    softBreakdown = [];
  } else if (algo === "welsh_powell") {
    colorsUsed = 6;
    executionTimeMs = parseFloat((0.85 + Math.random() * 0.55).toFixed(2));
    softScore = parseFloat((8.0 + (runSequence % 3) * 3.5).toFixed(1));
    softBreakdown = [{ rule: "consecutive_exam_slots", penalty: softScore, occurrences: 1 + (runSequence % 2) }];
  } else {
    // Greedy algorithm
    colorsUsed = 7 + (runSequence % 2); // 7 or 8 colors
    executionTimeMs = parseFloat((0.45 + Math.random() * 0.35).toFixed(2));
    softScore = parseFloat((22.0 + (runSequence % 4) * 4.0).toFixed(1));
    softBreakdown = [
      { rule: "suboptimal_color_dispersion", penalty: 16.0, occurrences: 2 },
      { rule: "two_exams_same_day", penalty: softScore - 16.0, occurrences: 2 },
    ];
  }

  // Create varied exam assignments based on algorithm
  const slotList = mockTimeSlots;
  const newAssignments: ExamAssignmentItem[] = [];

  const subjectConfigs = [
    { code: "CS101", name: "Introduction to Programming", dept: "CS", count: 20 },
    { code: "EE101", name: "Linear Circuit Analysis", dept: "EE", count: 15 },
    { code: "CS102", name: "Discrete Mathematics", dept: "CS", count: 20 },
    { code: "EE102", name: "Digital Logic & Microprocessors", dept: "EE", count: 15 },
    { code: "CS201", name: "Data Structures & Algorithms", dept: "CS", count: 18 },
    { code: "EE201", name: "Signals and Linear Systems", dept: "EE", count: 12 },
    { code: "CS202", name: "Computer Organization & Architecture", dept: "CS", count: 18 },
    { code: "EE202", name: "Electromagnetic Fields & Waves", dept: "EE", count: 12 },
    { code: "CS301", name: "Operating Systems & Concurrency", dept: "CS", count: 28 }, // Hub
    { code: "CS302", name: "Database Management Systems", dept: "CS", count: 22 },
    { code: "CS303", name: "Computer Networks & Protocols", dept: "CS", count: 19 },
    { code: "CS401", name: "Advanced Machine Learning Capstone", dept: "CS", count: 8 }, // Isolated
  ];

  // Distinct mapping layouts by algorithm
  let slotMapping: number[];
  if (algo === "dsatur") {
    // DSATUR: Optimal pairs across 6 slots
    slotMapping = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5, 4];
  } else if (algo === "welsh_powell") {
    // Welsh-Powell: Degree-first ordering (CS301 Hub in slot 0, CS401 in slot 0)
    slotMapping = [4, 3, 2, 4, 1, 5, 2, 5, 0, 1, 3, 0];
  } else {
    // Greedy: Spreads across 7 or 8 slots
    slotMapping = [0, 1, 1, 2, 2, 3, 3, 5, 4, 5, 6, 7 % colorsUsed];
  }

  // Apply slight rotation based on runSequence for variety on repeat clicks
  const offset = runSequence % 2;

  subjectConfigs.forEach((sub, i) => {
    const rawSlotIdx = (slotMapping[i] + offset) % Math.min(colorsUsed, slotList.length);
    const slot = slotList[rawSlotIdx];
    newAssignments.push({
      id: `asg-gen-${algo}-${i}-${runSequence}`,
      scheduleVersionId: "",
      examId: `exam-${sub.code.toLowerCase()}`,
      subjectCode: sub.code,
      subjectName: sub.name,
      departmentCode: sub.dept,
      timeSlotId: slot.id,
      slotDate: slot.date,
      startTime: slot.startTime,
      endTime: slot.endTime,
      sessionLabel: slot.sessionLabel,
      durationMinutes: 180,
      studentCount: sub.count,
      colorId: rawSlotIdx + 1,
      locked: sub.code === "CS301",
      manualOverride: false,
    });
  });

  lastRunDetails = {
    runId,
    algorithm: algo,
    colorsUsed,
    softScore,
    assignments: newAssignments,
  };

  return {
    id: runId,
    schedulingCycleId: "cycle-demo-2026",
    algorithm: algo,
    executionTimeMs,
    colorsUsed,
    isValid: true,
    softScore,
    status: softScore === 0 ? "success" : "success_with_warnings",
    validationReport: {
      valid: true,
      hardViolations: [],
      softBreakdown,
    },
  };
}

export function saveRunAsCandidateVersion(runId?: string): ScheduleVersionDetail {
  const nextVer = mockScheduleVersions.length + 1;
  const newVerId = `ver-demo-${nextVer}`;
  const algo = lastRunDetails?.algorithm || "dsatur";
  const soft = lastRunDetails?.softScore ?? 0.0;
  const colors = lastRunDetails?.colorsUsed ?? 6;

  const assignments = (lastRunDetails?.assignments || initialAssignments).map((a) => ({
    ...a,
    scheduleVersionId: newVerId,
  }));

  const summary: ScheduleVersionSummary = {
    id: newVerId,
    versionNumber: nextVer,
    status: "Candidate",
    scheduleRunId: runId || lastRunDetails?.runId || `run-${algo}-saved`,
    assignmentCount: 12,
    hardViolationCount: 0,
    softScore: soft,
    rowVersion: 1,
    publishedAt: null,
    createdAt: new Date().toISOString(),
  };

  // Prepend so latest version is at the top of the version selector
  mockScheduleVersions.unshift(summary);

  const detail: ScheduleVersionDetail = {
    ...summary,
    validationReport: {
      valid: true,
      hardViolations: [],
      softPenaltyTotal: soft,
      softBreakdown: soft > 0 ? [{ rule: "consecutive_exam_slots", penalty: soft, occurrences: 2 }] : [],
    },
    assignments,
  };

  mockScheduleVersionDetails[newVerId] = detail;
  activeScheduleVersionDetail = detail;

  // Update cycle summary metrics
  mockCycleSummary.totalSlots = 18;
  mockCycleSummary.slotsUsed = colors;

  return detail;
}

export const mockCycleSummary: CycleSummaryReport = {
  cycleId: "cycle-demo-2026",
  cycleName: "June 2026 Academic Final Examinations",
  examStartDate: "2026-06-10",
  examEndDate: "2026-06-20",
  totalSubjects: 12,
  totalExams: 12,
  totalStudents: 50,
  totalEnrollments: 153,
  totalSlots: 18,
  slotsUsed: 6,
  graphVertices: 12,
  graphEdges: 20,
  averageDegree: 3.33,
  latestPublishedVersion: 1,
  latestPublishedAt: "2026-06-05T10:00:00Z",
};

export const mockGraphSummary = {
  vertexCount: 12,
  edgeCount: 20,
  density: 0.303,
  avgDegree: 3.33,
  maxDegree: 7,
  chromaticLowerBound: 4,
  isolatedVertices: 1,
};

export const mockRawGraph = {
  nodes: [
    { id: "sub-cs101", subjectCode: "CS101", subjectName: "Intro to Programming", departmentCode: "CS", degree: 3, color: 1 },
    { id: "sub-cs102", subjectCode: "CS102", subjectName: "Discrete Mathematics", departmentCode: "CS", degree: 4, color: 2 },
    { id: "sub-cs201", subjectCode: "CS201", subjectName: "Data Structures", departmentCode: "CS", degree: 5, color: 3 },
    { id: "sub-cs202", subjectCode: "CS202", subjectName: "Computer Architecture", departmentCode: "CS", degree: 4, color: 4 },
    { id: "sub-cs301", subjectCode: "CS301", subjectName: "Operating Systems (Hub)", departmentCode: "CS", degree: 7, color: 5 },
    { id: "sub-cs302", subjectCode: "CS302", subjectName: "Database Systems", departmentCode: "CS", degree: 5, color: 6 },
    { id: "sub-cs303", subjectCode: "CS303", subjectName: "Computer Networks", departmentCode: "CS", degree: 4, color: 7 },
    { id: "sub-cs401", subjectCode: "CS401", subjectName: "ML Capstone (Isolated)", departmentCode: "CS", degree: 0, color: 8 },
    { id: "sub-ee101", subjectCode: "EE101", subjectName: "Linear Circuits", departmentCode: "EE", degree: 3, color: 1 },
    { id: "sub-ee102", subjectCode: "EE102", subjectName: "Digital Logic", departmentCode: "EE", degree: 3, color: 2 },
    { id: "sub-ee201", subjectCode: "EE201", subjectName: "Signals & Systems", departmentCode: "EE", degree: 3, color: 3 },
    { id: "sub-ee202", subjectCode: "EE202", subjectName: "Electromagnetic Fields", departmentCode: "EE", degree: 2, color: 4 },
  ],
  edges: [
    { source: "sub-cs101", target: "sub-cs102", weight: 20 },
    { source: "sub-cs101", target: "sub-cs201", weight: 6 },
    { source: "sub-cs101", target: "sub-cs301", weight: 4 },
    { source: "sub-cs102", target: "sub-cs201", weight: 8 },
    { source: "sub-cs102", target: "sub-cs202", weight: 5 },
    { source: "sub-cs102", target: "sub-cs301", weight: 6 },
    { source: "sub-cs201", target: "sub-cs202", weight: 18 },
    { source: "sub-cs201", target: "sub-cs301", weight: 10 },
    { source: "sub-cs201", target: "sub-cs302", weight: 7 },
    { source: "sub-cs202", target: "sub-cs301", weight: 9 },
    { source: "sub-cs202", target: "sub-cs303", weight: 4 },
    { source: "sub-cs301", target: "sub-cs302", weight: 22 },
    { source: "sub-cs301", target: "sub-cs303", weight: 19 },
    { source: "sub-cs301", target: "sub-ee201", weight: 3 },
    { source: "sub-cs302", target: "sub-cs303", weight: 18 },
    { source: "sub-ee101", target: "sub-ee102", weight: 15 },
    { source: "sub-ee101", target: "sub-ee201", weight: 4 },
    { source: "sub-ee102", target: "sub-ee201", weight: 5 },
    { source: "sub-ee201", target: "sub-ee202", weight: 12 },
    { source: "sub-ee102", target: "sub-ee202", weight: 4 },
  ],
};

export const mockDistribution = {
  scheduleVersionId: "ver-demo-1",
  versionNumber: 1,
  byDate: [
    { date: "2026-06-10", examCount: 4, studentSessions: 70 },
    { date: "2026-06-11", examCount: 4, studentSessions: 60 },
    { date: "2026-06-12", examCount: 2, studentSessions: 50 },
    { date: "2026-06-13", examCount: 2, studentSessions: 27 },
  ],
  bySession: [
    { sessionLabel: "Morning (09:00)", examCount: 6, studentSessions: 112 },
    { sessionLabel: "Afternoon (14:00)", examCount: 6, studentSessions: 95 },
  ],
  multiExamDays: [
    { examsPerDay: 1, studentCount: 42 },
    { examsPerDay: 2, studentCount: 8 },
  ],
};

export const mockComparison = {
  cycleId: "cycle-demo-2026",
  graphSnapshotId: "snap-demo-01",
  graphVertices: 12,
  graphEdges: 20,
  algorithms: [
    {
      algorithm: "dsatur",
      colorsUsed: 6,
      executionTimeMs: 1.84,
      isValid: true,
      examsScheduled: 12,
      unscheduledCount: 0,
      largestClassSize: 2,
      smallestClassSize: 1,
      softScore: 0,
      scheduleRunId: "run-demo-dsatur",
    },
    {
      algorithm: "welsh_powell",
      colorsUsed: 6,
      executionTimeMs: 1.25,
      isValid: true,
      examsScheduled: 12,
      unscheduledCount: 0,
      largestClassSize: 2,
      smallestClassSize: 1,
      softScore: 10,
      scheduleRunId: "run-demo-wp",
    },
    {
      algorithm: "greedy",
      colorsUsed: 7,
      executionTimeMs: 0.72,
      isValid: true,
      examsScheduled: 12,
      unscheduledCount: 0,
      largestClassSize: 2,
      smallestClassSize: 1,
      softScore: 25,
      scheduleRunId: "run-demo-greedy",
    },
  ],
  notes: [
    "DSATUR found the optimal chromatic partitioning (6 colors) with 0 soft penalties.",
    "Welsh-Powell achieved 6 colors with minimal ordering dispersion.",
    "Greedy required 7 colors due to sub-optimal vertex ordering.",
  ],
};

export const mockUserProfile: UserProfile = {
  id: "usr-admin-demo",
  email: "admin@univ.edu",
  role: "admin",
  isActive: true,
  departmentId: "dept-cs",
  departmentName: "Department of Computer Science",
  studentId: null,
};

export const mockStudentTimetable: StudentTimetableResponse = {
  studentId: "stu-cs-001",
  studentNumber: "CS-001",
  studentName: "Synthetic Candidate CS-001",
  cycleId: "cycle-demo-2026",
  cycleName: "June 2026 Academic Final Examinations",
  scheduleVersionId: "ver-demo-1",
  versionNumber: 1,
  publishedAt: "2026-06-05T10:00:00Z",
  exams: [
    {
      subjectCode: "CS101",
      subjectName: "Introduction to Programming",
      departmentCode: "CS",
      examDate: "2026-06-10",
      startTime: "09:00",
      endTime: "12:00",
      durationMinutes: 180,
      sessionLabel: "Morning",
    },
    {
      subjectCode: "CS102",
      subjectName: "Discrete Mathematics",
      departmentCode: "CS",
      examDate: "2026-06-10",
      startTime: "14:00",
      endTime: "17:00",
      durationMinutes: 180,
      sessionLabel: "Afternoon",
    },
    {
      subjectCode: "CS201",
      subjectName: "Data Structures & Algorithms",
      departmentCode: "CS",
      examDate: "2026-06-11",
      startTime: "09:00",
      endTime: "12:00",
      durationMinutes: 180,
      sessionLabel: "Morning",
    },
  ],
};

export const mockAuditLogs: AuditLogItem[] = [
  {
    id: "log-1",
    actorId: "usr-admin-demo",
    actorEmail: "admin@univ.edu",
    action: "SCHEDULE_PUBLISH",
    entityType: "schedule_version",
    entityId: "ver-demo-1",
    timestamp: "2026-06-05T10:00:00Z",
  },
  {
    id: "log-2",
    actorId: "usr-admin-demo",
    actorEmail: "admin@univ.edu",
    action: "SCHEDULE_RUN",
    entityType: "schedule_run",
    entityId: "run-demo-1",
    timestamp: "2026-06-05T09:30:00Z",
  },
  {
    id: "log-3",
    actorId: "usr-admin-demo",
    actorEmail: "admin@univ.edu",
    action: "CYCLE_CREATE",
    entityType: "scheduling_cycle",
    entityId: "cycle-demo-2026",
    timestamp: "2026-06-01T08:00:00Z",
  },
];

// Initial mock enrollments for students in mockStudents across mockSubjects
export const mockEnrollments: Enrollment[] = [];

// Populate realistic initial enrollments
(function initEnrollments() {
  const cycleId = "cycle-demo-2026";
  // CS semester 1 (CS-001..CS-010) -> CS101, CS102
  for (let i = 0; i < 10; i++) {
    const s = mockStudents[i];
    mockEnrollments.push({
      id: `enr-${s.id}-sub-cs101`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-cs101",
      subjectCode: "CS101",
      subjectName: "Introduction to Programming",
      cycleId,
      status: "active",
    });
    mockEnrollments.push({
      id: `enr-${s.id}-sub-cs102`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-cs102",
      subjectCode: "CS102",
      subjectName: "Discrete Mathematics",
      cycleId,
      status: "active",
    });
  }
  // CS semester 2 (CS-011..CS-020) -> CS201, CS202
  for (let i = 10; i < 20; i++) {
    const s = mockStudents[i];
    mockEnrollments.push({
      id: `enr-${s.id}-sub-cs201`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-cs201",
      subjectCode: "CS201",
      subjectName: "Data Structures & Algorithms",
      cycleId,
      status: "active",
    });
    mockEnrollments.push({
      id: `enr-${s.id}-sub-cs202`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-cs202",
      subjectCode: "CS202",
      subjectName: "Computer Organization & Architecture",
      cycleId,
      status: "active",
    });
  }
  // CS semester 3 (CS-021..CS-030) -> CS301, CS302, CS303
  for (let i = 20; i < 30; i++) {
    const s = mockStudents[i];
    mockEnrollments.push({
      id: `enr-${s.id}-sub-cs301`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-cs301",
      subjectCode: "CS301",
      subjectName: "Operating Systems & Concurrency",
      cycleId,
      status: "active",
    });
    mockEnrollments.push({
      id: `enr-${s.id}-sub-cs302`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-cs302",
      subjectCode: "CS302",
      subjectName: "Database Management Systems",
      cycleId,
      status: "active",
    });
    mockEnrollments.push({
      id: `enr-${s.id}-sub-cs303`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-cs303",
      subjectCode: "CS303",
      subjectName: "Computer Networks & Protocols",
      cycleId,
      status: "active",
    });
  }
  // EE semester 1 (EE-001..EE-010) -> EE101, EE102
  for (let i = 30; i < 40; i++) {
    const s = mockStudents[i];
    mockEnrollments.push({
      id: `enr-${s.id}-sub-ee101`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-ee101",
      subjectCode: "EE101",
      subjectName: "Linear Circuit Analysis",
      cycleId,
      status: "active",
    });
    mockEnrollments.push({
      id: `enr-${s.id}-sub-ee102`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-ee102",
      subjectCode: "EE102",
      subjectName: "Digital Logic & Microprocessors",
      cycleId,
      status: "active",
    });
  }
  // EE semester 2 (EE-011..EE-020) -> EE201, EE202
  for (let i = 40; i < 50; i++) {
    const s = mockStudents[i];
    mockEnrollments.push({
      id: `enr-${s.id}-sub-ee201`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-ee201",
      subjectCode: "EE201",
      subjectName: "Signals and Linear Systems",
      cycleId,
      status: "active",
    });
    mockEnrollments.push({
      id: `enr-${s.id}-sub-ee202`,
      studentId: s.id,
      studentNumber: s.studentNumber,
      studentName: s.fullName,
      subjectId: "sub-ee202",
      subjectCode: "EE202",
      subjectName: "Electromagnetic Fields & Waves",
      cycleId,
      status: "active",
    });
  }
})();

export function addMockEnrollment(studentId: string, subjectId: string, cycleId?: string): Enrollment {
  const student = mockStudents.find((s) => s.id === studentId || s.studentNumber === studentId);
  const subject = mockSubjects.find((sub) => sub.id === subjectId || sub.subjectCode === subjectId);
  const cycle = mockCycles.find((c) => c.id === cycleId) || mockCycles[0];

  const newEnrollment: Enrollment = {
    id: `enr-${student?.id || studentId}-${subject?.id || subjectId}-${Date.now().toString().slice(-4)}`,
    studentId: student?.id || studentId,
    studentNumber: student?.studentNumber,
    studentName: student?.fullName,
    subjectId: subject?.id || subjectId,
    subjectCode: subject?.subjectCode,
    subjectName: subject?.subjectName,
    cycleId: cycle.id,
    status: "active",
  };

  mockEnrollments.unshift(newEnrollment);

  if (student) {
    student.enrollmentCount = (student.enrollmentCount || 0) + 1;
  }
  if (subject) {
    subject.enrollmentCount = (subject.enrollmentCount || 0) + 1;
  }

  return newEnrollment;
}

export function withdrawMockEnrollment(enrollmentId: string): Enrollment | null {
  const idx = mockEnrollments.findIndex((e) => e.id === enrollmentId);
  if (idx !== -1) {
    const enr = mockEnrollments[idx];
    enr.status = "withdrawn";
    const student = mockStudents.find((s) => s.id === enr.studentId);
    if (student && student.enrollmentCount && student.enrollmentCount > 0) {
      student.enrollmentCount -= 1;
    }
    const subject = mockSubjects.find((s) => s.id === enr.subjectId);
    if (subject && subject.enrollmentCount && subject.enrollmentCount > 0) {
      subject.enrollmentCount -= 1;
    }
    return enr;
  }
  return null;
}

export function addMockSubject(data: {
  subject_code?: string;
  subjectCode?: string;
  subject_name?: string;
  subjectName?: string;
  department_id?: string;
  departmentId?: string;
  semester?: number;
  credits?: number;
  default_duration_minutes?: number;
  defaultDurationMinutes?: number;
  initial_enrollment?: number;
  initialEnrollment?: number;
}): Subject {
  const code = (data.subjectCode || data.subject_code || "NEW101").toUpperCase();
  const name = data.subjectName || data.subject_name || "New Course";
  const deptId = data.departmentId || data.department_id || "dept-cs";
  const dept = mockDepartments.find((d) => d.id === deptId) || mockDepartments[0];
  const enrollCount = Number(data.initialEnrollment || data.initial_enrollment) || 20;

  const newSub: Subject = {
    id: `sub-${code.toLowerCase().replace(/[^a-z0-9]/g, "")}-${Date.now().toString().slice(-4)}`,
    subjectCode: code,
    subjectName: name,
    departmentId: dept.id,
    departmentCode: dept.code,
    semester: Number(data.semester) || 1,
    credits: Number(data.credits) || 3.0,
    defaultDurationMinutes: Number(data.defaultDurationMinutes || data.default_duration_minutes) || 180,
    status: "active",
    enrollmentCount: enrollCount,
    conflictDegree: Math.min(6, Math.max(1, Math.floor(enrollCount / 5))),
  };

  mockSubjects.unshift(newSub);
  return newSub;
}

export function updateMockSubjectEnrollment(subjectId: string, count: number): Subject | null {
  const sub = mockSubjects.find((s) => s.id === subjectId || s.subjectCode === subjectId);
  if (sub) {
    sub.enrollmentCount = count;
    sub.conflictDegree = Math.min(8, Math.max(1, Math.floor(count / 5)));
    return sub;
  }
  return null;
}

export function addMockStudent(data: {
  student_number?: string;
  studentNumber?: string;
  full_name?: string;
  fullName?: string;
  email?: string;
  department_id?: string;
  departmentId?: string;
  semester?: number;
}): Student {
  const num = (data.studentNumber || data.student_number || `S-${Date.now().toString().slice(-4)}`).toUpperCase();
  const name = data.fullName || data.full_name || "New Student";
  const deptId = data.departmentId || data.department_id || "dept-cs";
  const dept = mockDepartments.find((d) => d.id === deptId) || mockDepartments[0];

  const newStu: Student = {
    id: `stu-${num.toLowerCase().replace(/[^a-z0-9]/g, "")}-${Date.now().toString().slice(-4)}`,
    studentNumber: num,
    fullName: name,
    email: data.email || `${num.toLowerCase()}@university.edu`,
    departmentId: dept.id,
    departmentCode: dept.code,
    semester: Number(data.semester) || 1,
    status: "active",
    enrollmentCount: 0,
  };

  mockStudents.unshift(newStu);
  return newStu;
}
