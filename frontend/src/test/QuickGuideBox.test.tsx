import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QuickGuideBox } from "../components/common/QuickGuideBox";

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe("QuickGuideBox Component", () => {
  it("renders the guide box title and plain-english guide badge", () => {
    renderWithRouter(<QuickGuideBox />);

    expect(screen.getByText("How ExamScheduler Works")).toBeInTheDocument();
    expect(screen.getByText("Plain-English Guide")).toBeInTheDocument();
    expect(screen.getByText(/Everything you need to know about creating and viewing clash-free examination timetables/i)).toBeInTheDocument();
  });

  it("renders the 3-step overview by default with non-technical steps", () => {
    renderWithRouter(<QuickGuideBox />);

    expect(screen.getByText("3-Step Overview")).toBeInTheDocument();
    expect(screen.getByText("Input Courses & Students")).toBeInTheDocument();
    expect(screen.getByText("Click 'Generate'")).toBeInTheDocument();
    expect(screen.getByText("Review & Look Up Dates")).toBeInTheDocument();
    expect(screen.getByText(/Zero clashes guaranteed/i)).toBeInTheDocument();
  });

  it("switches to student guide tab and displays candidate instructions", () => {
    renderWithRouter(<QuickGuideBox />);

    const studentTab = screen.getByRole("button", { name: /for students/i });
    fireEvent.click(studentTab);

    expect(
      screen.getByText(/Finding Your Personalized Exam Schedule \(No Password Needed\)/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Enter Your Roll Number")).toBeInTheDocument();
    expect(screen.getByText("View & Print Hall Ticket")).toBeInTheDocument();
  });

  it("switches to staff guide tab and displays coordinator workflow", () => {
    renderWithRouter(<QuickGuideBox />);

    const staffTab = screen.getByRole("button", { name: /for exam coordinators/i });
    fireEvent.click(staffTab);

    expect(
      screen.getByText(/Exam Coordinator & Administrator Workflow/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Run Automated Schedule Generation:/i)).toBeInTheDocument();
    expect(screen.getByText(/Review on Grid & Publish:/i)).toBeInTheDocument();
  });

  it("triggers onSelectSampleStudent callback when a sample student button is clicked in student tab", () => {
    const handleSelectStudent = vi.fn();
    renderWithRouter(
      <QuickGuideBox onSelectSampleStudent={handleSelectStudent} />
    );

    // Switch to student tab
    const studentTab = screen.getByRole("button", { name: /for students/i });
    fireEvent.click(studentTab);

    const sampleBtn = screen.getByRole("button", { name: "STU-2024-001" });
    fireEvent.click(sampleBtn);

    expect(handleSelectStudent).toHaveBeenCalledWith("STU-2024-001");
  });

  it("toggles collapse and expand when toggle button is clicked", () => {
    renderWithRouter(<QuickGuideBox defaultExpanded={true} />);

    const toggleBtn = screen.getByRole("button", { name: /collapse guide box/i });
    expect(toggleBtn).toHaveAttribute("aria-expanded", "true");

    // Click collapse
    fireEvent.click(toggleBtn);
    expect(toggleBtn).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByText(/Quick summary:/i)).toBeInTheDocument();

    // Click expand
    fireEvent.click(toggleBtn);
    expect(toggleBtn).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Input Courses & Students")).toBeInTheDocument();
  });

  it("renders collapsed by default when defaultExpanded is false", () => {
    renderWithRouter(<QuickGuideBox defaultExpanded={false} variant="compact" />);

    expect(screen.getByText(/Quick summary:/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /expand guide box/i })).toBeInTheDocument();
  });
});
