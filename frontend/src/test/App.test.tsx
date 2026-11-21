import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { App } from "../App";

describe("Frontend Smoke Render Test", () => {
  it("renders the application layout and brand header", () => {
    render(<App />);
    expect(screen.getByText("ExamScheduler")).toBeInTheDocument();
    expect(screen.getByText("Overview Dashboard")).toBeInTheDocument();
    expect(screen.getByText("System Ready")).toBeInTheDocument();
  });
});
