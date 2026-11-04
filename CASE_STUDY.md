# Case study: taking over a codebase that "almost works"

*November 2026. The project is my own academic project from 2025 (solar panel monitoring, FastAPI + React + Docker). I came back to it one year later and treated it the way I treat a client's repository: run what exists, find what is broken, prove each problem with a test, fix the cause, and leave notes. The sensor data is simulated; no client was involved.*

## Starting point

The README promised a one-command Docker setup, a text import for lines like `V:20.2V I:0.10A P:2.1W`, and CSV import. In practice:

| Check | Before |
|---|---|
| `pytest` | **Could not start**: collection error in `tests/test_mpp_endpoint.py` |
| Parser tests | **0 / 2 passing** |
| Text import shown in the README | Rejected with `400 No valid lines found in input text` |
| CSV import with `;` and a time column | Rows saved, but every measurement time replaced by the import time |
| Docker Compose | PostgreSQL started but never used; data written to a SQLite file inside the source folder, and that file committed to Git |

## What was wrong, and what I changed

**1. The test suite never ran.** `import app.models.sample` rebound the name `app` from the FastAPI application to the Python package, so `app.dependency_overrides` failed before any test started. Once that was fixed, the in-memory SQLite database was not shared between connections, so the tables did not exist during the test. *Fix*: import the models without rebinding `app`, and use a single shared connection (`StaticPool`) for the test database.

**2. Text import rejected its own documented format.** Half of `parse_text_samples` (plain `V,I` lines and `V:..V I:..A` lines) had ended up after the `return` of another function, `parse_xlsx_bytes`, where it could never run. `parse_text_samples` returned `None` for anything without a CSV header. *Fix*: move the block back where it belongs. *Proof*: a new API test posts the README example to `/api/import/text` and gets both rows back, with `P = V × I` when power is missing.

**3. CSV files with `;` lost their timestamps.** The `;` branch of `parse_csv_bytes` read V, I, P and T but ignored the `t`/`time`/`timestamp` column, so imported measurements were stamped with the time of the upload and time filters found nothing. *Fix*: read the time column. *Proof*: a parser test, and an API test that imports a file and finds its rows again with a `from`/`to` filter.

**4. Docker Compose did not use its own database.** The backend never received `DATABASE_URL`, so it fell back to SQLite inside the bind-mounted source folder, and `solar_monitoring.db` was tracked by Git. *Fix*: pass `DATABASE_URL` to the backend, start it only when PostgreSQL is healthy (`condition: service_healthy`), stop tracking the database file and ignore `*.db`, and correct the example environment file.

## Result

| Check | After |
|---|---|
| `pytest` | **6 / 6 passing** (2 existing tests repaired, 4 new tests that failed before the fixes) |
| Continuous integration | GitHub Actions runs the tests on Python 3.11 and validates `docker-compose.yml` on every push |
| Docker Compose | Backend wired to PostgreSQL; `docker compose config` valid |

Not verified here: a full `docker compose up` on this machine (Docker Desktop was not running). The CI job validates the Compose file; the containers themselves were last run on 26/10/2026 for the screenshots in the README.

## How I work on a repository like this

I reproduce each problem with a test before changing code, fix the cause rather than the symptom, keep each fix small enough to review, and write down what was wrong. I use Claude Code to speed up routine work (reading code, drafting tests), and I review and run every change myself.
