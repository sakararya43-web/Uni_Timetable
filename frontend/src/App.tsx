import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./context/AuthContext";
import { AppLayout } from "./components/layout/AppLayout";
import { ErrorBoundary } from "./components/common/ErrorBoundary";

import { OverviewPage } from "./pages/OverviewPage";
import { CyclesPage } from "./pages/CyclesPage";
import { SubjectsPage } from "./pages/SubjectsPage";
import { StudentsPage } from "./pages/StudentsPage";
import { GraphPage } from "./pages/GraphPage";
import { GeneratePage } from "./pages/GeneratePage";
import { AlgorithmLabPage } from "./pages/AlgorithmLabPage";
import { TimetablePage } from "./pages/TimetablePage";
import { StudentTimetablePage } from "./pages/StudentTimetablePage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <ErrorBoundary>
            <Routes>
            <Route path="/login" element={<LoginPage />} />

            {/* Application Main Layout Routes */}
            <Route
              path="/"
              element={
                <AppLayout>
                  <OverviewPage />
                </AppLayout>
              }
            />
            <Route
              path="/cycles"
              element={
                <AppLayout>
                  <CyclesPage />
                </AppLayout>
              }
            />
            <Route
              path="/subjects"
              element={
                <AppLayout>
                  <SubjectsPage />
                </AppLayout>
              }
            />
            <Route
              path="/students"
              element={
                <AppLayout>
                  <StudentsPage />
                </AppLayout>
              }
            />
            <Route
              path="/graph"
              element={
                <AppLayout>
                  <GraphPage />
                </AppLayout>
              }
            />
            <Route
              path="/generate"
              element={
                <AppLayout>
                  <GeneratePage />
                </AppLayout>
              }
            />
            <Route
              path="/lab"
              element={
                <AppLayout>
                  <AlgorithmLabPage />
                </AppLayout>
              }
            />
            <Route
              path="/timetable"
              element={
                <AppLayout>
                  <TimetablePage />
                </AppLayout>
              }
            />
            <Route
              path="/student/timetable"
              element={
                <AppLayout>
                  <StudentTimetablePage />
                </AppLayout>
              }
            />
            <Route
              path="/student/info"
              element={<Navigate to="/student/timetable" replace />}
            />
            <Route
              path="/reports"
              element={
                <AppLayout>
                  <ReportsPage />
                </AppLayout>
              }
            />
            <Route
              path="/settings"
              element={
                <AppLayout>
                  <SettingsPage />
                </AppLayout>
              }
            />

            {/* 404 Fallback */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};
