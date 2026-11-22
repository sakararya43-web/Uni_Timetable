/**
 * Core TypeScript definitions matching the backend REST API contract.
 * Tasks P11.1 - P11.14.
 */

export type Role = "admin" | "coordinator" | "faculty" | "student";
export type EntityStatus = "active" | "archived";
export type CycleStatus = "draft" | "generated" | "reviewed" | "published" | "archived";
export type ScheduleStatus = "Candidate" | "Reviewed" | "Published" | "Archived";
export type ScheduleRunStatus = "running" | "success" | "success_with_warnings" | "failed" | "infeasible";

export interface UserProfile {
  id: string;
  email: string;
  role: Role;
  isActive: boolean;
  departmentId?: string | null;
  departmentName?: string | null;
  studentId?: string | null;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  status: EntityStatus;
}

export interface Subject {
  id: string;
  subjectCode: string;
  subjectName: string;
  departmentId: string;
  departmentCode?: string;
  semester: number;
  credits: number;
  defaultDurationMinutes: number;
  status: EntityStatus;
  enrollmentCount?: number;
  conflictDegree?: number;
}

export interface Student {
  id: string;
  studentNumber: string;
  fullName: string;
  email: string;
  departmentId?: string | null;
  departmentCode?: string | null;
  semester: number;
  status: EntityStatus;
  enrollmentCount?: number;
}

export interface Enrollment {
  id: string;
  studentId: string;
  studentNumber?: string;
  studentName?: string;
  subjectId: string;
  subjectCode?: string;
  subjectName?: string;
  cycleId: string;
  status: "active" | "withdrawn";
}

export interface PaginatedEnrollmentsResponse {
  items: Enrollment[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface SessionConfig {
  label: string;
  startTime: string;
  endTime: string;
  enabled: boolean;
}

export interface CycleConfig {
  examDaysOfWeek: number[];
  sessions: SessionConfig[];
  holidays?: string[];
  maxExamsPerSession?: number;
  maxExamsPerDay?: number;
}

export interface SchedulingCycle {
  id: string;
  name: string;
  academicYearId: string;
  startDate: string;
  endDate: string;
  status: CycleStatus;
  timezone: string;
  graphStale: boolean;
  dataVersion: number;
  configurationJson: CycleConfig;
  createdAt: string;
}

export interface PaginatedCyclesResponse {
  items: SchedulingCycle[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export function unwrapCycles(data: SchedulingCycle[] | PaginatedCyclesResponse | unknown): SchedulingCycle[] {
  if (Array.isArray(data)) {
    return data as SchedulingCycle[];
  }
  if (
    data &&
    typeof data === "object" &&
    "items" in data &&
    Array.isArray((data as { items: unknown }).items)
  ) {
    return (data as { items: SchedulingCycle[] }).items;
  }
  return [];
}

export interface TimeSlot {
  id: string;
  schedulingCycleId: string;
  date: string;
  startTime: string;
  endTime: string;
  durationMinutes: number;
  sessionLabel: string;
  slotIndex: number;
  enabled: boolean;
  capacity?: number;
}

export interface CycleSummaryReport {
  cycleId: string;
  cycleName: string;
  examStartDate: string;
  examEndDate: string;
  totalSubjects: number;
  totalExams: number;
  totalStudents: number;
  totalEnrollments: number;
  totalSlots: number;
  slotsUsed: number;
  graphVertices: number;
  graphEdges: number;
  averageDegree: number;
  latestPublishedVersion?: number | null;
  latestPublishedAt?: string | null;
}

export interface ConflictGraphSnapshot {
  id: string;
  schedulingCycleId: string;
  version: number;
  vertexCount: number;
  edgeCount: number;
  density: number;
  avgDegree: number;
  maxDegree: number;
  chromaticLowerBound: number;
  createdAt: string;
}

export interface ScheduleVersionSummary {
  id: string;
  versionNumber: number;
  status: ScheduleStatus;
  scheduleRunId?: string | null;
  assignmentCount: number;
  hardViolationCount: number;
  softScore: number;
  rowVersion: number;
  publishedAt?: string | null;
  createdAt: string;
}

export interface EditHistoryItem {
  id: string;
  action: string;
  actorId?: string | null;
  createdAt: string;
  details?: Record<string, unknown> | null;
}

export interface ExamAssignmentItem {
  id: string;
  scheduleVersionId?: string;
  examId: string;
  subjectCode: string;
  subjectName: string;
  departmentCode?: string | null;
  timeSlotId: string;
  slotDate: string;
  startTime: string;
  endTime: string;
  slotStartTime?: string;
  slotEndTime?: string;
  slotDurationMinutes?: number;
  slotIndex?: number;
  sessionLabel: string;
  durationMinutes: number;
  studentCount?: number;
  colorId: number;
  locked: boolean;
  manualOverride: boolean;
}

export interface ScheduleVersionDetail extends ScheduleVersionSummary {
  assignments: ExamAssignmentItem[];
  editHistory?: EditHistoryItem[];
  validationReport: {
    valid: boolean;
    hardViolations: Array<{
      type: string;
      message: string;
      examIds: string[];
      sharedStudentCount?: number;
    }>;
    softPenaltyTotal: number;
    softBreakdown: Array<{
      rule: string;
      penalty: number;
      occurrences: number;
    }>;
  };
}

export interface StudentTimetableItem {
  subjectCode: string;
  subjectName: string;
  departmentCode?: string | null;
  examDate: string;
  startTime: string;
  endTime: string;
  durationMinutes: number;
  sessionLabel: string;
}

export interface StudentTimetableResponse {
  studentId: string;
  studentNumber: string;
  studentName: string;
  cycleId: string;
  cycleName: string;
  scheduleVersionId: string;
  versionNumber: number;
  publishedAt?: string | null;
  exams: StudentTimetableItem[];
}

export interface AuditLogItem {
  id: string;
  actorId?: string | null;
  actorEmail?: string | null;
  action: string;
  entityType: string;
  entityId?: string | null;
  beforeState?: Record<string, unknown> | null;
  afterState?: Record<string, unknown> | null;
  requestId?: string | null;
  timestamp: string;
}

export interface AuditLogResponse {
  total: number;
  items: AuditLogItem[];
}

export interface ImportPreviewResponse {
  batchId: string;
  importType: string;
  totalRows: number;
  validRows: number;
  invalidRows: number;
  errors: Array<{
    row: number;
    field?: string;
    message: string;
    suggestion?: string;
  }>;
}
