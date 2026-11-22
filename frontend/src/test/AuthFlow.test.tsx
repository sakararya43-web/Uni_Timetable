import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext";
import { LoginPage } from "../pages/LoginPage";
import { AppLayout } from "../components/layout/AppLayout";

describe("Authentication Flow: Login, Session & Logout", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("renders LoginPage and handles quick role presets", () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const emailInput = screen.getByPlaceholderText("registrar@university.edu") as HTMLInputElement;
    expect(emailInput.value).toBe("admin@university.edu");

    // Click Student preset
    const studentBtn = screen.getByRole("button", { name: /4\. Student/i });
    fireEvent.click(studentBtn);
    expect(emailInput.value).toBe("student@university.edu");

    // Click Coordinator preset
    const coordBtn = screen.getByRole("button", { name: /2\. Coordinator/i });
    fireEvent.click(coordBtn);
    expect(emailInput.value).toBe("coordinator@university.edu");
  });

  it("authenticates via LoginPage and navigates to operations console", async () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/overview" element={<div data-testid="overview-page">Overview Console</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole("button", { name: /sign in to operations/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId("overview-page")).toBeInTheDocument();
    });

    // Verify localStorage has persisted user
    const saved = localStorage.getItem("timetabling_auth_user");
    expect(saved).not.toBeNull();
    const parsed = JSON.parse(saved!);
    expect(parsed.role).toBe("admin");
  });

  it("redirects unauthenticated users in AppLayout to /login", async () => {
    render(
      <MemoryRouter initialEntries={["/overview"]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/overview"
              element={
                <AppLayout>
                  <div>Overview Content</div>
                </AppLayout>
              }
            />
            <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  it("renders authenticated user in AppLayout and successfully logs out on Sign Out click", async () => {
    // Pre-populate authenticated admin user in localStorage
    const demoAdmin = {
      id: "usr-admin-demo",
      email: "admin@university.edu",
      fullName: "Admin Registrar",
      role: "admin" as const,
      departmentId: "dept-cs",
    };
    localStorage.setItem("timetabling_auth_user", JSON.stringify(demoAdmin));
    localStorage.setItem("timetabling_token", "demo-token");

    render(
      <MemoryRouter initialEntries={["/overview"]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/overview"
              element={
                <AppLayout>
                  <div data-testid="overview-content">Protected Overview</div>
                </AppLayout>
              }
            />
            <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    // Verify user is visible in AppLayout sidebar
    await waitFor(() => {
      expect(screen.getByText("Admin Registrar")).toBeInTheDocument();
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    // Click Sign Out
    const signOutBtn = screen.getByTitle("Sign Out");
    fireEvent.click(signOutBtn);

    // Must navigate to /login and clear session
    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });

    expect(localStorage.getItem("timetabling_auth_user")).toBeNull();
  });
});
