import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { PublishScheduleModal } from "../components/timetable/PublishScheduleModal";
import { MoveExamModal } from "../components/timetable/MoveExamModal";
import { RegenerateModal } from "../components/timetable/RegenerateModal";
import { StudentTimetablePage } from "../pages/StudentTimetablePage";
import { ReportsPage } from "../pages/ReportsPage";
import { SettingsPage } from "../pages/SettingsPage";
import { ExamAssignmentItem, TimeSlot } from "../types/api";

const mockAssignment: ExamAssignmentItem = {
  id: "asgn-1",
  scheduleVersionId: "ver-1",
  examId: "exam-1",
  timeSlotId: "slot-1",
  colorId: 1,
  locked: false,
  manualOverride: false,
  subjectCode: "CS101",
  subjectName: "Introduction to Computer Science",
  departmentCode: "CS",
  durationMinutes: 180,
  slotDate: "2026-12-01",
  startTime: "09:00",
  endTime: "12:00",
  slotStartTime: "09:00",
  slotEndTime: "12:00",
  slotDurationMinutes: 180,
  slotIndex: 1,
  sessionLabel: "Morning",
};

const mockSlots: TimeSlot[] = [
  {
    id: "slot-1",
    schedulingCycleId: "cycle-1",
    date: "2026-12-01",
    startTime: "09:00",
    endTime: "12:00",
    durationMinutes: 180,
    sessionLabel: "Morning",
    slotIndex: 1,
    enabled: true,
  },
  {
    id: "slot-2",
    schedulingCycleId: "cycle-1",
    date: "2026-12-01",
    startTime: "14:00",
    endTime: "17:00",
    durationMinutes: 180,
    sessionLabel: "Afternoon",
    slotIndex: 2,
    enabled: true,
  },
];

describe("Phase 13: Timetable Editing, Publishing, Student & Reports UI", () => {
  it("renders PublishScheduleModal with confirmation checkbox and action button", () => {
    render(
      <PublishScheduleModal
        isOpen={true}
        onClose={vi.fn()}
        versionId="ver-1"
        versionNumber={1}
        cycleName="Fall 2026 Final Exams"
        onSuccess={vi.fn()}
      />
    );

    expect(screen.getByText("Publish Official Timetable: Version 1")).toBeInTheDocument();
    expect(screen.getByText(/Once published, this timetable version becomes strictly immutable/i)).toBeInTheDocument();
    expect(screen.getByText(/I confirm that I have reviewed the clash-free validation report/i)).toBeInTheDocument();
    const publishBtn = screen.getByRole("button", { name: /confirm & publish/i });
    expect(publishBtn).toBeInTheDocument();
    expect(publishBtn).toBeDisabled();
  });

  it("renders MoveExamModal with slot selector and dry-run preview check", () => {
    render(
      <MoveExamModal
        isOpen={true}
        onClose={vi.fn()}
        versionId="ver-1"
        assignment={mockAssignment}
        slots={mockSlots}
        onSuccess={vi.fn()}
      />
    );

    expect(screen.getByText("Move Examination: CS101")).toBeInTheDocument();
    expect(screen.getByText("Choose Destination Slot")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /preview move & check clashes/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /confirm move/i })).toBeInTheDocument();
  });

  it("renders RegenerateModal with mode selection and algorithm options", () => {
    render(
      <RegenerateModal
        isOpen={true}
        onClose={vi.fn()}
        versionId="ver-1"
        versionNumber={1}
        onSuccess={vi.fn()}
      />
    );

    expect(screen.getByText("Regenerate Schedule from Version 1")).toBeInTheDocument();
    expect(screen.getByText("Regeneration Mode")).toBeInTheDocument();
    expect(screen.getByText("Coloring Algorithm")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /regenerate schedule/i })).toBeInTheDocument();
  });

  it("renders StudentTimetablePage with navigation tabs", () => {
    render(
      <BrowserRouter>
        <StudentTimetablePage />
      </BrowserRouter>
    );

    expect(screen.getByText("Personal Examination Schedule")).toBeInTheDocument();
    expect(screen.getByText("OFFICIAL PUBLISHED")).toBeInTheDocument();
    expect(screen.getByText("My Examination Timetable")).toBeInTheDocument();
    expect(screen.getByText("Academic Information & Enrollments")).toBeInTheDocument();
  });

  it("renders ReportsPage with analytics header and export options", () => {
    render(
      <BrowserRouter>
        <ReportsPage />
      </BrowserRouter>
    );

    expect(screen.getByText("Institutional Analytics & Reports")).toBeInTheDocument();
    expect(
      screen.getByText(/Workload distributions, student density histograms/i)
    ).toBeInTheDocument();
  });

  it("renders SettingsPage with soft-constraint weights tab", () => {
    render(
      <BrowserRouter>
        <SettingsPage />
      </BrowserRouter>
    );

    expect(screen.getByText("Administration & System Preferences")).toBeInTheDocument();
    expect(screen.getByText("Soft-Constraint Penalty Weights")).toBeInTheDocument();
  });
});
