import React from "react";
import { Link, useLocation } from "react-router-dom";
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
  GraduationCap
} from "lucide-react";

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isStudent = user?.role === "student";

  const staffNavItems = [
    { label: "Overview", path: "/", icon: LayoutDashboard },
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
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between shrink-0">
        <div>
          {/* Brand Header */}
          <div className="h-16 flex items-center px-6 border-b border-slate-200">
            <span className="font-semibold text-lg tracking-tight text-brand-600 flex items-center gap-2">
              <Calendar className="w-6 h-6 text-brand-600" />
              <span>ExamScheduler</span>
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-brand-600" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Session Footer */}
        <div className="p-4 border-t border-slate-200">
          <div className="flex items-center justify-between">
            <div className="overflow-hidden mr-2">
              <p className="text-sm font-medium text-slate-800 truncate">
                {user?.fullName || "Staff User"}
              </p>
              <p className="text-xs text-slate-500 capitalize">{user?.role || "Administrator"}</p>
            </div>
            <button
              onClick={() => logout()}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-600 rounded hover:bg-slate-100 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 overflow-y-auto flex flex-col">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0">
          <div className="text-sm text-slate-500">
            <span>University Examination System</span>
            <span className="mx-2">/</span>
            <span className="font-medium text-slate-800">
              {navItems.find((item) => item.path === location.pathname)?.label || "Dashboard"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              System Ready
            </span>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-8">{children}</div>
      </main>
    </div>
  );
};
