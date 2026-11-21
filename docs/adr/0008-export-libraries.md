# ADR-008: Document Generation Libraries (ReportLab and OpenPyXL)

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Backend Engineering Team
- **Context:** PRD §22, Appendix C Item 8, Item 11

---

## Context and Problem Statement

The system must export official examination timetables and analytical reports in PDF and spreadsheet formats for university administration, faculty distribution, and student personal downloads.
The libraries chosen must be:
- Native Python without requiring external system binaries (like headless Chrome or wkhtmltopdf) in production Docker images.
- Deterministic, high performance, and capable of clean multi-page pagination.
- Capable of formula-injection escaping.

## Decision

We adopt:
1. **ReportLab (`reportlab`) for PDF Generation:**
   - Standard, battle-tested Python PDF engine.
   - Operates entirely in-process without requiring heavy headless browser runtimes (Puppeteer, Playwright, or Weasyprint).
   - Enables fine-grained typography, printable headers, dynamic footers with "Page X of Y", watermarking ("DRAFT / NOT PUBLISHED"), and grid layouts.
2. **OpenPyXL (`openpyxl`) for Excel (XLSX) Generation:**
   - Native Python library with complete formatting, auto-filter, and multiple worksheet support.
   - Supports sanitized cell writes with formula injection protection (automatic prefixing of `'` on cells beginning with `=`, `+`, `-`, or `@`).
3. **Standard Python `csv` Module for CSV Exports:**
   - Built-in, high-performance streaming with RFC 4180 compliance and explicit UTF-8 BOM encoding option for seamless Microsoft Excel compatibility.

## Consequences

### Positive
- Keeps Docker container images lightweight (< 200MB base Python), avoiding gigabytes of browser dependencies.
- Very fast generation (< 100ms for student personal PDF, < 1s for institution-wide master PDF).
- Complete layout control for accessibility and greyscale printing.

### Negative
- ReportLab canvas and Platypus flowables require explicit programmatic layout code rather than HTML/CSS templates.
