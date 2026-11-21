import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Dialog } from "../components/ui/Dialog";
import { EmptyState } from "../components/ui/EmptyState";
import { StaleDataBanner } from "../components/common/StaleDataBanner";
import { ImportWizardModal } from "../components/imports/ImportWizardModal";

describe("Phase 11: Design System Primitives & Components", () => {
  it("renders Badge variants accurately with text", () => {
    render(
      <div>
        <Badge variant="success">Published</Badge>
        <Badge variant="warning">Stale</Badge>
        <Badge variant="danger">Clash</Badge>
      </div>
    );
    expect(screen.getByText("Published")).toBeInTheDocument();
    expect(screen.getByText("Stale")).toBeInTheDocument();
    expect(screen.getByText("Clash")).toBeInTheDocument();
  });

  it("renders Button with loading state and handles clicks", () => {
    const handleClick = vi.fn();
    const { rerender } = render(
      <Button variant="primary" onClick={handleClick}>
        Save Changes
      </Button>
    );

    const btn = screen.getByRole("button", { name: /save changes/i });
    expect(btn).toBeEnabled();
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);

    // Re-render with isLoading
    rerender(
      <Button variant="primary" isLoading onClick={handleClick}>
        Save Changes
      </Button>
    );
    expect(btn).toBeDisabled();
  });

  it("renders Input with label, placeholder, and inline error", () => {
    render(
      <Input
        label="Exam Code"
        placeholder="e.g. CS101"
        error="Invalid code format"
      />
    );
    expect(screen.getByText("Exam Code")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. CS101")).toBeInTheDocument();
    expect(screen.getByText("Invalid code format")).toBeInTheDocument();
  });

  it("renders Select dropdown with options", () => {
    const options = [
      { value: "dsatur", label: "DSATUR (Primary)" },
      { value: "welsh_powell", label: "Welsh-Powell" },
    ];
    render(<Select label="Algorithm" options={options} />);
    expect(screen.getByText("Algorithm")).toBeInTheDocument();
    expect(screen.getByText("DSATUR (Primary)")).toBeInTheDocument();
    expect(screen.getByText("Welsh-Powell")).toBeInTheDocument();
  });

  it("renders Dialog and triggers close callback on close click", () => {
    const handleClose = vi.fn();
    render(
      <Dialog isOpen={true} onClose={handleClose} title="Test Modal">
        <p>Modal body content</p>
      </Dialog>
    );
    expect(screen.getByText("Test Modal")).toBeInTheDocument();
    expect(screen.getByText("Modal body content")).toBeInTheDocument();

    const closeBtn = screen.getByLabelText("Close dialog");
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("renders StaleDataBanner and handles rebuild trigger", () => {
    const handleRebuild = vi.fn();
    render(
      <StaleDataBanner isStale={true} onRebuildGraph={handleRebuild} />
    );
    expect(
      screen.getByText(/data has been modified since the conflict graph was constructed/i)
    ).toBeInTheDocument();

    const rebuildBtn = screen.getByRole("button", { name: /rebuild graph/i });
    fireEvent.click(rebuildBtn);
    expect(handleRebuild).toHaveBeenCalledTimes(1);
  });

  it("renders EmptyState with action button", () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="No Subjects"
        description="Add subjects to start building your conflict graph."
        actionLabel="Create Subject"
        onAction={handleAction}
      />
    );
    expect(screen.getByText("No Subjects")).toBeInTheDocument();
    const actionBtn = screen.getByRole("button", { name: /create subject/i });
    fireEvent.click(actionBtn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it("renders ImportWizardModal with multi-step stepper", () => {
    render(<ImportWizardModal isOpen={true} onClose={vi.fn()} defaultType="subjects" />);
    expect(screen.getByText(/Import Academic Data/i)).toBeInTheDocument();
    expect(screen.getByText("1. Select & Template")).toBeInTheDocument();
    expect(screen.getByText("2. Upload CSV")).toBeInTheDocument();
    expect(screen.getByText("3. Validate & Commit")).toBeInTheDocument();
  });
});
