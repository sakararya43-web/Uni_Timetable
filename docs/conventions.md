# Coding & Engineering Conventions

**Project:** University Examination Timetable Scheduling System  
**Document Version:** 1.0.0  
**Date:** 2026-11-21  
**Phase:** Phase 0 (Task P0.4)

---

## 1. Python Conventions (Backend)

The backend is built with Python 3.11+ using FastAPI, Pydantic v2, and SQLAlchemy 2.x.

### 1.1 Tooling & Linters
- **Formatter & Linter:** `ruff` is used for linting and formatting. Line length is capped at **100 characters**.
- **Alternative Formatter:** `black` compatible (target Python 3.11, line length 100).
- **Static Type Checking:** `mypy` with strict configuration:
  - `disallow_untyped_defs = true`
  - `disallow_incomplete_defs = true`
  - `check_untyped_defs = true`
  - `no_implicit_optional = true`
  - `warn_redundant_casts = true`
  - `warn_unused_ignores = true`
  - `warn_return_any = true`
  - `strict_equality = true`

### 1.2 Code Organization & Typing
- **Type Annotations:** All functions and methods must have complete type signatures for arguments and return types.
- **Pydantic v2:** Use `ConfigDict(from_attributes=True)` for ORM models. Validate types strictly; reject extra unexpected attributes on sensitive payloads.
- **SQLAlchemy 2.0 Style:** Use modern typed mapped attributes (`mapped_column`, `Mapped[T]`, `select()`). Never use legacy 1.x `query.filter()`.
- **Pure Algorithm Isolation:** Code inside `app/algorithms/` must **never import** from `app/api/`, `app/models/`, `app/services/`, or `sqlalchemy`. It operates purely on primitive Python data types (`dict`, `set`, `list`, `dataclass`).
- **Docstrings:** Use Google-style docstrings for public classes, services, and algorithms, including complexity notes ($O(V+E)$).

---

## 2. TypeScript & React Conventions (Frontend)

The frontend is built with React 18+, Vite, TypeScript (strict), and Tailwind CSS.

### 2.1 Tooling & Linters
- **TypeScript:** Strict mode enabled (`"strict": true`, `"noImplicitAny": true`, `"strictNullChecks": true`, `"noUnusedLocals": true`, `"noUnusedParameters": true`).
- **Linter:** ESLint with `@typescript-eslint/recommended`, `eslint-plugin-react-hooks`, and `eslint-plugin-jsx-a11y`.
- **Formatter:** Prettier with 2-space indentation, semi-colons, single quotes for JS/TS, and double quotes for JSX.

### 2.2 Component & Architectural Principles
- **Design Tokens & Aesthetic:** Restrained, functional, information-dense layout per PRD §16.1. Neutral palettes (`slate`/`zinc`), functional status colors (emerald for valid, amber for warning, rose for conflict/error, indigo for locked/selected). Avoid excessive decorative gradients or oversized novelty widgets.
- **Accessibility (A11y):** WCAG 2.1 AA baseline. Visible keyboard focus rings, semantic HTML elements, ARIA labels for icon buttons and custom controls, high color contrast, text/icon indicators (never color alone to communicate state).
- **State Management:**
  - TanStack Query (React Query) for server state caching, pagination, and invalidation.
  - React Context / Zustand for lightweight client session and active cycle state.
  - React Flow with Web Worker background layout computation for graph visualization.
- **Generated Types:** Consume OpenAPI-generated TypeScript schemas (`openapi-typescript`). Never manually write redundant API response interfaces.

---

## 3. Git Workflow & Commit Guidelines

### 3.1 Branching Strategy
We use **GitHub Flow** (or Trunk-Based Development with feature branches):
- Main branch: `main` (always deployable, protected branch).
- Feature branches: `feat/<feature-name>`, `fix/<bug-name>`, `phase-<N>-<task-id>`.
- Merging to `main` requires passing automated CI (linting, type checking, unit tests).

### 3.2 Commit Message Format
All commits follow the **Conventional Commits** specification:
```text
<type>(<scope>): <short description in imperative mood>

[optional detailed body explaining context and rationale]

[optional footer, e.g. Closes #123, Tasks: P2.1, P2.2]
```

**Allowed Types:**
- `feat`: A new user-facing feature or API capability.
- `fix`: A bug fix or defect resolution.
- `test`: Adding or refactoring unit, integration, or property-based tests.
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `perf`: A code change that improves performance or algorithmic runtime.
- `docs`: Documentation changes, ADRs, or guides.
- `chore`: Tooling, CI/CD, dependency updates, or configuration.

---

## 4. Definition of Done (DoD) Checklist (§35)

A task or feature branch is not considered complete until all items in the checklist below are satisfied:
1. **Validation:** Input payload validation handles missing, empty, out-of-range, and malformed inputs.
2. **Authorization:** Role and scope restrictions enforced by backend dependencies independently of UI state.
3. **Database Integrity:** Transactions protect atomic multi-step changes; foreign keys and constraints prevent inconsistent states.
4. **Error Handling:** Central error format returned with standard machine error codes and human-readable messages; no raw stack traces exposed.
5. **Audit Trail:** Relevant administrative or state-altering actions logged via `audit_service`.
6. **Automated Tests:** Unit and integration tests cover happy path, boundary cases, and negative paths; algorithm tests achieve >= 95% branch coverage.
7. **UI States:** Frontend components handle Loading, Empty, Error, and Permission-Denied states.
8. **Accessibility:** Keyboard navigable, ARIA labelled, WCAG AA contrast compliant.
9. **Documentation:** OpenAPI schema updated; complex logic documented in `docs/`.
