import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { GeneratePage } from "../pages/GeneratePage";
import { AlgorithmLabPage } from "../pages/AlgorithmLabPage";
import { TimetablePage } from "../pages/TimetablePage";
import { CyclesPage } from "../pages/CyclesPage";
import { GraphPage } from "../pages/GraphPage";
import { mockDepartments } from "../services/mockData";

describe("Phase 12: Scheduling Experience UI", () => {
  it("renders GeneratePage with algorithm choices and run options", () => {
    render(
      <BrowserRouter>
        <GeneratePage />
      </BrowserRouter>
    );
    expect(screen.getByText("Automated Timetable Generation Engine")).toBeInTheDocument();
    expect(screen.getByText("DSATUR (Primary)")).toBeInTheDocument();
    expect(screen.getByText("Welsh-Powell")).toBeInTheDocument();
    expect(screen.getByText("Greedy Coloring")).toBeInTheDocument();
    expect(screen.getByText("Preserve Locked Assignments")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate timetable/i })).toBeInTheDocument();
  });

  it("renders AlgorithmLabPage with heuristic honesty note and compare action", () => {
    render(
      <BrowserRouter>
        <AlgorithmLabPage />
      </BrowserRouter>
    );
    expect(screen.getByText("Algorithm Comparison Lab")).toBeInTheDocument();
    expect(screen.getByText("Algorithmic Heuristic Note & Theoretical Limits")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run comparison/i })).toBeInTheDocument();
  });

  it("renders TimetablePage with export buttons", () => {
    render(
      <BrowserRouter>
        <TimetablePage />
      </BrowserRouter>
    );
    expect(screen.getByText("Examination Timetable Grid")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /pdf/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /csv/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /print/i })).toBeInTheDocument();
  });

  it("renders CyclesPage and displays existing and newly created cycles", async () => {
    render(
      <BrowserRouter>
        <CyclesPage />
      </BrowserRouter>
    );
    expect(screen.getByText("Scheduling Cycles & Time Slots")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new scheduling cycle/i })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("June 2026 Academic Final Examinations")).toBeInTheDocument();
    });
  });

  it("renders GraphPage with prominent Create Conflict Graph button", async () => {
    render(
      <BrowserRouter>
        <GraphPage />
      </BrowserRouter>
    );
    expect(screen.getByText("Conflict Graph Visualizer G=(V,E)")).toBeInTheDocument();
    await waitFor(() => {
      const createButtons = screen.getAllByRole("button", { name: /create conflict graph/i });
      expect(createButtons.length).toBeGreaterThan(0);
    });
  });

  it("contains expanded list of academic departments", () => {
    expect(mockDepartments.length).toBeGreaterThanOrEqual(10);
    const codes = mockDepartments.map((d) => d.code);
    expect(codes).toContain("CS");
    expect(codes).toContain("EE");
    expect(codes).toContain("ME");
    expect(codes).toContain("CE");
    expect(codes).toContain("IT");
    expect(codes).toContain("AI");
  });
});
