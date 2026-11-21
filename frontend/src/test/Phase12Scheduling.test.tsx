import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { GeneratePage } from "../pages/GeneratePage";
import { AlgorithmLabPage } from "../pages/AlgorithmLabPage";
import { TimetablePage } from "../pages/TimetablePage";

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
});
