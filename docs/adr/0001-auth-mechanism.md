# ADR-001: Authentication Mechanism

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, System Engineering Team
- **Context:** PRD §7, §23, Appendix C Item 1

---

## Context and Problem Statement

The application requires secure user authentication for administrative staff, faculty, department coordinators, and students. We must select the token transmission and storage mechanism for browser-based API communication that balances security against Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF), while maintaining clean API ergonomics and ease of automated integration testing.

The two primary architectural patterns are:
1. **JSON Web Tokens (JWT) stored in client `localStorage`/`sessionStorage` and transmitted via the `Authorization: Bearer <token>` header.**
2. **JWT stored in `httpOnly`, `Secure`, `SameSite=Lax` cookies, combined with CSRF double-submit protection for state-mutating requests.**

## Decision

We adopt a **hybrid approach with strict defaults**:
1. **Primary Web Client (Browser):** Authentication tokens are issued as `httpOnly`, `Secure`, `SameSite=Lax` cookies.
   - The cookie is named `access_token`.
   - JavaScript running in the browser cannot read this cookie, providing strong mitigation against token theft via XSS.
   - For state-mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`), a separate anti-CSRF token is issued in a readable cookie (`csrf_token`) and must be echoed in the `X-CSRF-Token` request header.
2. **Programmatic / API Client Support:** The backend authentication middleware inspects the `Authorization: Bearer <token>` header first. If present, it validates the bearer token; if absent, it falls back to extracting the token from the `httpOnly` cookie.
3. **Token Structure & Lifetime:**
   - Tokens are signed using asymmetric Ed25519 or symmetric HMAC-SHA256 (`HS256`) with a cryptographically random secret key of at least 256 bits loaded exclusively from environment variables.
   - Short access token lifetime: 15 to 60 minutes.
   - Refresh token rotation mechanism for extended administrative sessions, tracked in a server-side revocable token family store.

## Consequences

### Positive
- Client-side XSS vulnerabilities cannot exfiltrate authentication tokens from document cookies.
- Single API architecture supports both browser frontend and automated testing / CLI tools seamlessly.
- Explicit CSRF protection protects all state-changing operations.

### Negative
- Requires maintaining anti-CSRF middleware on the backend and an interceptor on the frontend API client.
- Cross-origin development environments require explicit CORS origin matching and `credentials: "include"`. Wildcard `*` origins are strictly disallowed.
