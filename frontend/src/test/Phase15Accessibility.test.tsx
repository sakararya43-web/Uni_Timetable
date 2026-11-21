import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Dialog } from "../components/ui/Dialog";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

describe("Phase 15: Accessibility & Semantic Compliance Audits", () => {
  it("renders accessible Dialog with role, aria-labelledby, and accessible close button", () => {
    render(
      <Dialog
        isOpen={true}
        onClose={vi.fn()}
        title="Accessible Confirmation Dialog"
        description="Detailed accessible description for screen readers."
      >
        <p>Dialog body content</p>
      </Dialog>
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "dialog-title");

    const closeBtn = screen.getByLabelText("Close dialog");
    expect(closeBtn).toBeInTheDocument();
  });

  it("renders accessible Button with disabled and aria attributes", () => {
    render(
      <Button variant="primary" disabled aria-label="Submit Form Action">
        Submit
      </Button>
    );

    const btn = screen.getByRole("button", { name: /submit form action/i });
    expect(btn).toBeInTheDocument();
    expect(btn).toBeDisabled();
  });

  it("renders accessible Input with associated label and required indicator", () => {
    render(
      <Input
        label="Examination Title"
        id="exam-title-input"
        required
        placeholder="Enter course name..."
      />
    );

    const input = screen.getByLabelText(/examination title/i);
    expect(input).toBeInTheDocument();
    expect(input).toBeRequired();
  });
});
