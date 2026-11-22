import React from "react";
import { Link, useLocation, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  LayoutDashboard,
  CalendarDays,
  BookOpen,
  Users,
  Network,
  Sparkles,
  FlaskConical,
  Calendar,
  BarChart3,
  Settings,
  LogOut,
  GraduationCap,
  Globe,
  ExternalLink,
} from "lucide-react";

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      navigate("/login", { replace: true });
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--color-paper)]">
        <div className="flex items-center gap-2 text-xs font-mono text-[var(--color-muted)]">
          <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] animate-ping" />
          <span>Verifying session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const isStudent = user?.role === "student";

  const staffNavItems = [
    { label: "Overview", path: "/overview", icon: LayoutDashboard },
    { label: "Scheduling Cycles", path: "/cycles", icon: CalendarDays },
    { label: "Subjects", path: "/subjects", icon: BookOpen },
    { label: "Students & Enrollments", path: "/students", icon: Users },
    { label: "Conflict Graph", path: "/graph", icon: Network },
    { label: "Generate Schedule", path: "/generate", icon: Sparkles },
    { label: "Algorithm Lab", path: "/lab", icon: FlaskConical },
    { label: "Timetable Grid", path: "/timetable", icon: Calendar },
    { label: "Reports & Analytics", path: "/reports", icon: BarChart3 },
    { label: "Settings", path: "/settings", icon: Settings },
  ];

  const studentNavItems = [
    { label: "My Timetable", path: "/student/timetable", icon: Calendar },
    { label: "Academic Info", path: "/student/info", icon: GraduationCap },
  ];

  const navItems = isStudent ? studentNavItems : staffNavItems;

  return (
    <div className="flex h-screen bg-[var(--color-paper)] text-[var(--color-ink)] font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-[var(--color-rule)] bg-white flex flex-col justify-between shrink-0">
        <div>
          {/* Brand Header */}
          <div className="h-16 flex items-center justify-between px-6 border-b border-[var(--color-rule)]">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded border border-[var(--color-ink)] flex items-center justify-center bg-[var(--color-paper-2)]">
                <GraduationCap className="w-4 h-4 text-[var(--color-accent)]" />
              </div>
              <div>
                <span className="font-display font-normal text-lg tracking-tight text-[var(--color-ink)] block leading-tight">
                  ExamScheduler
                </span>
                <span className="text-[10px] font-mono text-[var(--color-muted)]">
                  Academic Registry
                </span>
              </div>
            </Link>
          </div>

          {/* Quick Portal Switcher Banner */}
          <div className="px-3 pt-3">
            <Link
              to="/"
              className="flex items-center justify-between px-3 py-2 text-xs font-mono text-[var(--color-muted)] rounded border border-dashed border-[var(--color-rule)] hover:border-[var(--color-ink)] hover:text-[var(--color-ink)] bg-[var(--color-paper)] transition-colors"
              title="Return to Public Landing & Schedule Portal"
            >
              <span className="flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                <span>Public Portal</span>
              </span>
              <ExternalLink className="w-3 h-3 text-[var(--color-muted)]" />
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path === "/overview" && location.pathname === "/");
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 text-xs font-medium rounded transition-colors ${
                    isActive
                      ? "bg-[var(--color-paper-2)] text-[var(--color-accent)] border-l-2 border-[var(--color-accent)] font-semibold"
                      : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper)] hover:text-[var(--color-ink)]"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-[var(--color-accent)]" : "text-[var(--color-muted)]"}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Session Footer */}
        <div className="p-4 border-t border-[var(--color-rule)] bg-[var(--color-paper)]">
          <div className="flex items-center justify-between">
            <div className="overflow-hidden mr-2">
              <p className="text-xs font-medium text-[var(--color-ink)] truncate font-sans">
                {user?.fullName || "Staff Registrar"}
              </p>
              <p className="text-[11px] text-[var(--color-muted)] font-mono capitalize">
                {user?.role || "Administrator"}
              </p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              aria-label="Sign Out"
              className="p-1.5 text-[var(--color-muted)] hover:text-[var(--color-error)] rounded hover:bg-white transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 overflow-y-auto flex flex-col">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-[var(--color-rule)] bg-white px-8 flex items-center justify-between shrink-0">
          <div className="text-xs text-[var(--color-muted)] font-mono flex items-center gap-2">
            <span>University Registry</span>
            <span>/</span>
            <span className="font-semibold text-[var(--color-ink)] font-sans">
              {navItems.find((item) => item.path === location.pathname)?.label || "Operations"}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="text-xs font-mono text-[var(--color-muted)] hover:text-[var(--color-accent)] flex items-center gap-1 transition-colors"
            >
              <Globe className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Landing Page</span>
            </Link>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono bg-emerald-50 text-emerald-800 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
              System Ready
            </span>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-8 bg-[var(--color-paper)]">{children}</div>
      </main>
    </div>
  );
};
