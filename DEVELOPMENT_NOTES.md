# DEVELOPMENT_NOTES.md

---

## 1. Implementation walkthrough (what I built, and in what order)

1. **Project scaffold**
    - Created `app/` layout: `api/v1` (routers + models), `services/`, `utils/`, and `core/` for config.
    - Added `Dockerfile` and `docker-compose` for local dev and easy reproducibility.
    - Added pre-commit hooks (ruff, mypy) and pytest configuration.

2. **Input validation utility**
    - Implemented `validate_ipv4(ip: str) -> bool` using Python standard `ipaddress` module (robust and unambiguous vs.
      regex).

3. **Pydantic models**
    - `GeoResponse` (strict fields: ip, country, region, city, latitude, longitude, timezone, isp).
    - `ErrorResponse` for consistent error schemas.

4. **Service layer**
    - `get_geo_for_ip(ip: str) -> GeoResponse`:
        - Async `httpx.AsyncClient` call to third-party IP API (configurable via settings).
        - Handles request/network errors and returns meaningful `HTTPException`s (502 for upstream issues; 404 when
          provider returns `fail`).

5. **Endpoints**
    - `/api/v1/geo/{ip}` — validate input, call service, propagate errors properly.
    - `/api/v1/geo` — detect client IP (`request.client.host`), validate and reuse service code.
    - `/health` — simple liveness endpoint.
    - Focused on: explicit status codes (400, 404, 502, 500 for unexpected), clear docstrings, f-string logging, no
      over-catching of `HTTPException`.

6. **Settings**
    - `IPSettings` (Pydantic BaseSettings) to hold `IP_API_URL` and `IP_API_TIMEOUT` and allow env overrides.

7. **Testing**
    - Wrote async pytest tests for:
        - `/geo/{ip}`: success, invalid IP, not found/private IP, request error, timeout, malformed provider response.
        - `/geo` (client IP): same set of edge cases.
    - Tests mock `get_geo_for_ip` or mock `httpx.AsyncClient.get` as appropriate to avoid external requests.
    - Factored reusable fixtures (`make_request`, `fake_geo_response`) into test helpers.

8. **Refactoring & polishing**
    - Cleaned exception handling so `HTTPException` from service propagates naturally.
    - Added docstrings and type hints.
    - Improved tests (fixtures, parametrization) for maintainability.

---

## 2. Why I chose Third-Party API (ip-api.com) vs Local Database

**Choice made for this exercise:** **Third-party API integration** (example: `ip-api.com`, configurable via settings)

**Why (for the take-home):**

- Quick to integrate (no DB setup).
- `ip-api.com` provides rich returned fields (country, regionName, city, lat/lon, timezone, isp) without an API key,
  which is convenient for a demo submission.
- Keeps focus on API design, error handling, async usage, and testing, which are core evaluation points.

**Trade-offs:**

- **Third-party API (pros)**
    - Fast to implement.
    - No heavy infra setup.
    - Offloads database maintenance and geo updates.
- **Third-party API (cons)**
    - Network latency and dependency on external service availability.
    - Rate limits and potential costs at scale.
    - Data privacy considerations (sending client IPs externally).

- **Local DB (pros)**
    - Lower latency after local lookups.
    - More control over data / privacy.
    - No external rate limiting at runtime.
- **Local DB (cons)**
    - Requires setup (MaxMind DB, downloads, periodic updates).
    - More initial engineering effort (storage, update pipeline).
    - Candidate complexity might be outside time budget for take-home.

**Recommendation for production:**

- **Hybrid approach** (recommended):
    - Use a **local GeoIP database** (MaxMind GeoLite2 or commercial DB) as the primary source for lookups (privacy,
      speed).
    - Optionally **enrich or fallback** to a trusted third-party API for missing/outdated data or additional fields (
      ISP, timezone details) and for debugging.
    - Add caching and rate-limit/backoff when using third-party providers.

---

## 3. API design decisions

- **Endpoints**
    - `/api/v1/geo/{ip}` — explicit IP lookup (versioned).
    - `/api/v1/geo` — client IP lookup (simple UX for callers).
    - `/health` — liveness check.

- **Versioning**
    - `API_V1_PREFIX = "/api/v1"` included so future versions can be added cleanly.

- **Response models**
    - Strict `GeoResponse` for successful responses.
    - Use `HTTPException` for errors with `ErrorResponse` schema in OpenAPI `responses` mapping (consistent error
      format).
    - I intentionally avoided unions in response models; instead, errors are returned as standard FastAPI error
      responses (`{"detail": ...}`) and the main response is always `GeoResponse` when status is 200. This keeps the
      OpenAPI contract simple and explicit.

- **Validation**
    - Validate IPv4 at the API layer using `ipaddress` module — accurate and deterministic.

- **Error handling**
    - Invalid client input → `400 Bad Request`.
    - Provider cannot locate / private range → `404 Not Found` (with provider message included).
    - Network/request failures → `502 Bad Gateway`.
    - Unexpected exceptions bubble up as `500` (but only in unexpected circumstances — not for provider "fail" states).

- **Logging**
    - Use structured logging (contextual messages, f-strings). In production, forward logs to a central system (
      ELK/Datadog).

---

## 4. Challenges & solutions

- **Testing async code & mocking `httpx.AsyncClient`**
    - Challenge: `httpx.AsyncClient.get` is a coroutine method and tests must not issue real HTTP requests.
    - Solution: monkeypatch the exact import path used by the endpoint (`app.api.v1.endpoints.get_geo_for_ip`) or patch
      `app.services.ip_geolocation.httpx.AsyncClient.get` to return an object with `.json()`; use `SimpleNamespace` or
      `GeoResponse` objects. Wrote async helpers/fixtures in tests.

- **Response validation errors in FastAPI**
    - Challenge: Returning an error model while `response_model` expects `GeoResponse` caused `ResponseValidationError`.
    - Solution: Use `HTTPException` to return proper HTTP error responses, and keep `response_model` for success only;
      document error responses in `responses` mapping.

- **Propagating HTTP errors**
    - Challenge: Overly broad `except Exception` blocks swallowed `HTTPException` from the service, producing 500
      instead of the intended code (e.g., 404).
    - Solution: Do not catch `HTTPException`; only catch network exceptions (`RequestError`, `TimeoutException`) at the
      endpoint level and let service-raised `HTTPException`s propagate.

- **Client IP detection behind proxies**
    - Challenge: `request.client.host` may be a container/private address during local testing and might not represent
      real client IP in production behind proxies/load balancers.
    - Solution: Initially use `request.client.host` (sufficient for this test). For production, add support for
      `X-Forwarded-For` with caution (only trust when coming from known proxies) — documented as next steps.

---

## 5. Production readiness — things I would implement next (priority list)

1. **Local GeoIP DB fallback** — integrate MaxMind GeoIP2 (local DB) as the primary lookup with periodic updates; use
   third-party API as fallback/enrichment.
2. **Caching layer** — cache frequent lookups (Redis) to reduce external calls and latency.
3. **Rate limiting & backoff** — protect upstream provider, and implement retries with exponential backoff for transient
   failures.
4. **Centralized logging & metrics** — structured logs and metrics (Prometheus + Grafana) for latency, error rates, and
   request volume.
5. **Tracing / distributed tracing** — OpenTelemetry for tracing external API calls and request flows.
6. **Secrets & config management** — use environment variables / secret store for API keys if needed (Azure Key Vault).
7. **CI/CD pipeline** — GitHub Actions to run linting (ruff), mypy, tests, and deliver container images.
8. **Integration tests / contract tests** — add integration tests that run in CI with mocks for third-party APIs and
   lightweight e2e checks.
9. **Security review / input sanitization** — ensure headers and forwarded IP handling are safe; consider rate limiting
   per client IP.
10. **Health & readiness checks** — expand health endpoint to check downstream dependencies and readiness probes for
    Kubernetes.
11. **OpenAPI polishing** — add examples & clear response schemas for all error codes so reviewers/users can test
    easily.

---

## 6. How to run (short quickstart)

- Build & run with Docker (local dev):

```bash
docker-compose up --build
# then visit http://localhost:8000/docs for interactive API docs
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q

pre-commit run --all-files
```
