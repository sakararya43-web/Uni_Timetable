import {
  mockCycles,
  mockAcademicYears,
  mockDepartments,
  mockSubjects,
  mockStudents,
  mockScheduleVersions,
  mockScheduleVersionDetails,
  activeScheduleVersionDetail,
  mockCycleSummary,
  mockGraphSummary,
  mockRawGraph,
  mockDistribution,
  mockComparison,
  mockUserProfile,
  mockStudentTimetable,
  mockAuditLogs,
  mockEnrollments,
  addMockEnrollment,
  withdrawMockEnrollment,
  addMockSubject,
  updateMockSubjectEnrollment,
  addMockStudent,
  generateDynamicScheduleRun,
  saveRunAsCandidateVersion,
  addMockCycle,
  generateMockSlotsForCycle,
  getMockSlotsForCycle,
  getMockSchedulesForCycle,
  buildMockGraphForCycle,
  getMockGraphForCycle,
  resetMockGraphForCycle,
} from "./mockData";

export interface ApiErrorDetail {
  field?: string;
  value?: string;
  issue: string;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    details: ApiErrorDetail[];
    requestId?: string;
  };
}

export class ApiError extends Error {
  public code: string;
  public details: ApiErrorDetail[];
  public requestId?: string;
  public status: number;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.error.message || "An unexpected API error occurred.");
    this.name = "ApiError";
    this.status = status;
    this.code = payload.error.code || "UNKNOWN_ERROR";
    this.details = payload.error.details || [];
    this.requestId = payload.error.requestId;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL || "";

function getOrigin(): string {
  if (typeof window !== "undefined" && window.location?.origin && window.location.origin !== "null") {
    return window.location.origin;
  }
  return "http://localhost:8000";
}

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

/**
 * Resolves fallback demonstration metadata when the backend API service is offline,
 * unseeded, unreachable, or running in standalone static frontend mode (e.g., Vercel previews).
 */
function resolveMockData(endpoint: string, method = "GET", body?: unknown): unknown {
  const clean = endpoint.split("?")[0];

  // Authentication endpoints
  if (clean === "/api/v1/auth/me") {
    return { user: mockUserProfile };
  }
  if (clean === "/api/v1/auth/login" || clean === "/api/v1/auth/refresh") {
    return { success: true, token: "demo-bearer-token", user: mockUserProfile };
  }
  if (clean === "/api/v1/auth/logout") {
    return { success: true };
  }

  // Academic structure endpoints
  if (clean === "/api/v1/academic/years") {
    return mockAcademicYears;
  }
  if (clean === "/api/v1/academic/departments") {
    return mockDepartments;
  }
  if (clean === "/api/v1/subjects") {
    if (method === "POST") {
      const payload = typeof body === "string" ? JSON.parse(body || "{}") : (body || {});
      return addMockSubject(payload);
    }
    return mockSubjects;
  }
  if (clean.startsWith("/api/v1/subjects/") && (method === "PATCH" || method === "PUT")) {
    const id = clean.replace("/api/v1/subjects/", "");
    const payload = typeof body === "string" ? JSON.parse(body || "{}") : (body || {});
    if (payload.enrollmentCount !== undefined) {
      return updateMockSubjectEnrollment(id, Number(payload.enrollmentCount)) || mockSubjects[0];
    }
    return mockSubjects.find((s) => s.id === id) || mockSubjects[0];
  }
  if (clean === "/api/v1/students") {
    if (method === "POST") {
      const payload = typeof body === "string" ? JSON.parse(body || "{}") : (body || {});
      return addMockStudent(payload);
    }
    return mockStudents;
  }

  // Scheduling Cycles & Slots
  if (clean === "/api/v1/cycles") {
    if (method === "POST") {
      const payload = typeof body === "string" ? JSON.parse(body || "{}") : (body || {});
      return addMockCycle(payload);
    }
    return mockCycles;
  }
  if (clean.includes("/slots/generate")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/slots\/generate/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    return generateMockSlotsForCycle(cycleId);
  }
  if (clean.endsWith("/slots")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/slots/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    return getMockSlotsForCycle(cycleId);
  }

  // Dynamic Schedule Generation with algorithm variety (DSATUR, Welsh-Powell, Greedy)
  if (clean.includes("/generate")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/schedule\/generate/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : undefined;
    let payloadObj: { algorithm?: string } | undefined;
    if (typeof body === "string") {
      try {
        payloadObj = JSON.parse(body);
      } catch {
        payloadObj = undefined;
      }
    } else if (body && typeof body === "object") {
      payloadObj = body as { algorithm?: string };
    }
    return generateDynamicScheduleRun(payloadObj, cycleId);
  }

  // Save generated schedule run as candidate version (PRD Tasks P8.15, P8.16, P9.1)
  if (clean.includes("/schedule-runs") || clean.endsWith("/save")) {
    const runIdMatch = clean.match(/\/schedule-runs\/([^/]+)\/save/);
    const runId = runIdMatch ? runIdMatch[1] : undefined;
    return saveRunAsCandidateVersion(runId);
  }

  // Schedule Versions & Timetable Operations
  if (clean.includes("/publish")) {
    return { success: true, message: "Schedule version published successfully." };
  }
  if (clean.includes("/regenerate")) {
    return { id: "ver-demo-1", versionNumber: 2 };
  }
  if (clean.includes("/move/preview") || clean.includes("/move")) {
    return { valid: true, conflicts: [], candidateSlotId: "slot-02" };
  }
  if (clean.includes("/clone") || clean.includes("/lock") || clean.includes("/unlock")) {
    return activeScheduleVersionDetail;
  }
  if (clean.includes("/cycles/") && clean.endsWith("/schedules") && method === "GET") {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/schedules/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    return getMockSchedulesForCycle(cycleId);
  }
  if (clean.endsWith("/schedules") && method === "GET") {
    return mockScheduleVersions;
  }
  if (clean.includes("/schedules/")) {
    if (clean.includes("/reports/distribution")) {
      return mockDistribution;
    }
    const match = clean.match(/\/schedules\/([^/]+)$/);
    if (match && mockScheduleVersionDetails[match[1]]) {
      return mockScheduleVersionDetails[match[1]];
    }
    return activeScheduleVersionDetail;
  }

  // Conflict Graph
  if (clean.includes("/graph/build")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/graph\/build/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    return buildMockGraphForCycle(cycleId);
  }
  if (clean.includes("/graph/reset")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/graph\/reset/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    resetMockGraphForCycle(cycleId);
    return { success: true };
  }
  if (clean.includes("/graph/summary")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/graph\/summary/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    const graph = getMockGraphForCycle(cycleId);
    return graph ? graph.summary : mockGraphSummary;
  }
  if (clean.includes("/graph/data")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/graph\/data/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    const graph = getMockGraphForCycle(cycleId);
    return graph ? graph.data : mockRawGraph;
  }
  if (clean.endsWith("/graph")) {
    const cycleIdMatch = clean.match(/\/cycles\/([^/]+)\/graph/);
    const cycleId = cycleIdMatch ? cycleIdMatch[1] : "cycle-demo-2026";
    const graph = getMockGraphForCycle(cycleId) || buildMockGraphForCycle(cycleId);
    return { summary: graph.summary, data: graph.data };
  }

  // Algorithm Lab comparison
  if (clean.includes("/compare")) {
    return mockComparison;
  }

  // Reports & Analytics
  if (clean.includes("/reports/summary")) {
    return mockCycleSummary;
  }
  if (clean.includes("/reports/distribution")) {
    return mockDistribution;
  }

  // Enrollments CRUD & diagnostic
  if (clean.includes("/enrollments/validate")) {
    return { valid: true, errorCount: 0, warningCount: 0, errors: [] };
  }
  if (clean === "/api/v1/enrollments") {
    if (method === "POST") {
      const payload = typeof body === "string" ? JSON.parse(body || "{}") : (body || {});
      const stuId = payload.studentId || payload.student_id;
      const subId = payload.subjectId || payload.subject_id;
      const cycId = payload.cycleId || payload.cycle_id;
      return addMockEnrollment(stuId, subId, cycId);
    }
    const active = mockEnrollments.filter((e) => e.status !== "withdrawn");
    return {
      items: active,
      total: active.length,
      page: 1,
      pageSize: 100,
      totalPages: Math.max(1, Math.ceil(active.length / 100)),
      hasNext: false,
      hasPrev: false,
    };
  }
  if (clean.startsWith("/api/v1/enrollments/") && method === "DELETE") {
    const id = clean.replace("/api/v1/enrollments/", "");
    const withdrawn = withdrawMockEnrollment(id);
    return withdrawn || { id, status: "withdrawn" };
  }

  // User management & Audit Logs
  if (clean === "/api/v1/users") {
    return method === "POST" ? mockUserProfile : [mockUserProfile];
  }
  if (clean.includes("/audit-logs")) {
    return { total: mockAuditLogs.length, items: mockAuditLogs };
  }

  // Student Timetable Portal
  if (clean === "/api/v1/me/timetable") {
    return mockStudentTimetable;
  }

  // CSV Imports
  if (clean.includes("/imports/")) {
    return {
      batchId: "batch-demo-1",
      importType: "subjects",
      totalRows: 12,
      validRows: 12,
      invalidRows: 0,
      errors: [],
    };
  }

  // Developer demonstration controls
  if (clean.includes("/dev/seed-demo")) {
    return {
      success: true,
      message: "Demonstration dataset seeded successfully.",
      data: { departments: 2, subjects: 12, students: 50, enrollments_added: 153 },
    };
  }
  if (clean.includes("/dev/status")) {
    return { demoSeedingAllowed: true, status: "ready" };
  }

  return null;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = BASE_URL ? `${BASE_URL}${cleanEndpoint}` : `${getOrigin()}${cleanEndpoint}`;
  const method = (options.method || "GET").toUpperCase();

  try {
    const headers = new Headers(options.headers || {});
    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    // Include Anti-CSRF token on mutating requests if present
    const csrfToken = getCookie("csrf_token");
    if (csrfToken && ["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      headers.set("X-CSRF-Token", csrfToken);
    }

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Required for httpOnly auth cookies
    });

    const contentType = response.headers.get("content-type") || "";

    // Detect SPA fallback HTML rewrite (common when static host rewrites API routes to index.html)
    if (response.status === 200 && contentType.includes("text/html")) {
      const fallback = resolveMockData(cleanEndpoint, method, options.body);
      if (fallback !== null) {
        return fallback as T;
      }
    }

    if (!response.ok) {
      // Check if fallback data is available for this endpoint
      const fallback = resolveMockData(cleanEndpoint, method, options.body);
      if (fallback !== null) {
        return fallback as T;
      }

      let errorPayload: ApiErrorPayload;
      try {
        errorPayload = await response.json();
      } catch {
        errorPayload = {
          error: {
            code: `HTTP_${response.status}`,
            message: response.statusText || "Request failed with HTTP status " + response.status,
            details: [],
            requestId: response.headers.get("X-Request-ID") || undefined,
          },
        };
      }
      throw new ApiError(response.status, errorPayload);
    }

    // Handle empty bodies (204 No Content)
    if (response.status === 204) {
      return {} as T;
    }

    const json = await response.json();

    // If backend returns paginated object { items: [...] } for /cycles and an array is expected, unwrap it
    if (
      cleanEndpoint === "/api/v1/cycles" &&
      method === "GET" &&
      typeof json === "object" &&
      json !== null &&
      "items" in json &&
      Array.isArray((json as { items: unknown[] }).items)
    ) {
      return (json as { items: unknown[] }).items as T;
    }

    // If backend returns empty array for core entities on unseeded live databases, fallback to demo data
    if (Array.isArray(json) && json.length === 0) {
      // Do not fallback for cycle schedules, an empty array from backend legitimately means no schedules exist yet for this cycle
      if (cleanEndpoint.includes("/schedules")) {
        return [] as unknown as T;
      }
      const fallback = resolveMockData(cleanEndpoint, method, options.body);
      if (fallback !== null && Array.isArray(fallback) && fallback.length > 0) {
        return fallback as T;
      }
    }

    return json as T;
  } catch (error) {
    // If backend is unreachable or offline, transparently serve demonstration dataset
    const fallback = resolveMockData(cleanEndpoint, method, options.body);
    if (fallback !== null) {
      return fallback as T;
    }
    throw error;
  }
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  delete: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: "DELETE" }),
};
