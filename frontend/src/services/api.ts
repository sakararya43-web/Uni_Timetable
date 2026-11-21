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

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Include Anti-CSRF token on mutating requests if present
  const csrfToken = getCookie("csrf_token");
  if (csrfToken && options.method && ["POST", "PUT", "PATCH", "DELETE"].includes(options.method.toUpperCase())) {
    headers.set("X-CSRF-Token", csrfToken);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Required for httpOnly auth cookies
  });

  if (!response.ok) {
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

  return response.json();
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
