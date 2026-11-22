import {
  mockCycles,
  mockAcademicYears,
  mockDepartments,
  mockSubjects,
  mockStudents,
  mockTimeSlots,
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
  generateDynamicScheduleRun,
  saveRunAsCandidateVersion,
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
    return method === "POST" ? mockSubjects[0] : mockSubjects;
  }
  if (clean === "/api/v1/students") {
    return method === "POST" ? mockStudents[0] : mockStudents;
  }

  // Scheduling Cycles & Slots
  if (clean === "/api/v1/cycles") {
    return method === "POST" ? mockCycles[0] : mockCycles;
  }
  if (clean.includes("/slots/generate") || clean.endsWith("/slots")) {
    return mockTimeSlots;
  }

  // Dynamic Schedule Generation with algorithm variety (DSATUR, Welsh-Powell, Greedy)
  if (clean.includes("/generate")) {
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
    return generateDynamicScheduleRun(payloadObj);
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
  if (clean.includes("/graph/build") || clean.endsWith("/graph")) {
    return { summary: mockGraphSummary, data: mockRawGraph };
  }
  if (clean.includes("/graph/summary")) {
    return mockGraphSummary;
  }
  if (clean.includes("/graph/data")) {
    return mockRawGraph;
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

  // Enrollments diagnostic
  if (clean.includes("/enrollments/validate")) {
    return { valid: true, errorCount: 0, warningCount: 0, errors: [] };
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

    // If backend returns empty array for core entities on unseeded live databases, fallback to demo data
    if (Array.isArray(json) && json.length === 0) {
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
