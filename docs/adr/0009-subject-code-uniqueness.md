# ADR-009: Subject Code Uniqueness Scope and Lookup Strategy

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Academic Data Team
- **Context:** PRD §17.4, FR-03, Appendix C Item 2

---

## Context and Problem Statement

Universities identify courses via alphanumeric codes (e.g., `CS101`, `MATH201`).
PRD §17.4 states "unique subject code within applicable academic scope". We must define whether subject codes are unique globally across the institution, unique per department, or unique per academic year.
Furthermore, CSV bulk import uses `subject_code` as the primary natural key when linking student enrollments.

## Decision

1. **Global Uniqueness of Subject Code:**
   - Every subject in the institutional catalog must have an institutionally unique `subject_code` (case-insensitive string, e.g. `CS301`).
   - Enforced by a database constraint:
     $$\text{UNIQUE}(\text{lower}(\text{subject\_code})) \quad \text{WHERE status = 'active'}$$
2. **Department Scoping:**
   - While subject codes are globally unique, every subject belongs to a specific `Department` and optional `Program`.
   - Department coordinators are restricted to managing subjects associated with their authorized `department_id`.
3. **Import Lookup:**
   - Enrollment CSV imports refer directly to `subject_code`. Global uniqueness eliminates ambiguity, ensuring an enrollment maps to exactly one course without requiring secondary department qualifiers.

## Consequences

### Positive
- Completely deterministic, zero-ambiguity course lookups in CSV imports and API queries.
- Prevents cross-departmental naming collisions.
- Matches standard university catalog practices.

### Negative
- Re-use of old codes for completely different subjects requires archiving the legacy subject first or using version suffixes (e.g., `CS301-A`).
