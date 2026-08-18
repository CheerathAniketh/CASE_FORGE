# CaseForge
 
**AI-Powered Case Study Generator for Professional Development**
 
Transform how students learn business strategy through dynamic, AI-generated case studies with intelligent evaluation and personalized feedback.
 
Built as part of the LMS platform at Sketch Brains.
 
---
 
## Status
 
**Backend: deployable.** Full generate → validate → evaluate → persist loop is verified end-to-end against a live Postgres database. Not yet live — see [What's Left](#whats-left) below.
 
---
 
## Overview
 
CaseForge is an intelligent case study generation platform built for educational institutions and corporate training. It uses **LangGraph state machines** and **LLMs** to create unique, realistic business scenarios on-demand — no templates, no repeats.
 
This backend is designed to be embedded into an existing LMS. It has **no built-in auth or frontend by design** — the LMS handles user identity and UI; this service just exposes a REST API.
 
---
 
## Features
 
### For Students
- Dynamic case generation — unique cases every time
- Multi-level difficulty: Beginner, Intermediate, Advanced
- AI-powered solution scoring across 5 dimensions
- Personalized, metric-anchored feedback
- Case history per user
- Industry variety: FinTech, Healthcare, E-commerce, SaaS, and more
### For Institutions
- API-first — built to sit behind an existing LMS, not stand alone
- No content management — cases generate automatically
- Real data tools baked into generation: market research, financial analysis, competitive intel
- Postgres-backed, ready for concurrent multi-user load
---
 
## Architecture
 
```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                       │
├─────────────────────────────────────────────────────────┤
│
├─ REST API Routes
│  ├─ POST /api/v1/cases/generate
│  ├─ POST /api/v1/solutions/evaluate
│  ├─ GET /api/v1/cases/{case_id}
│  ├─ GET /api/v1/users/{user_id}/cases
│  └─ GET /api/v1/health
│
├─ LangGraph State Machine (Workflow)
│  ├─ Node: generate_case (Groq LLM)
│  ├─ Node: validate_case (Quality checks)
│  ├─ Node: refine_case (Auto-improve if invalid, up to 2 retries)
│  └─ Node: save_case (Database persistence)
│
├─ Services & Tools
│  ├─ GroqService (LLM API wrapper)
│  ├─ WorkflowService (LangGraph executor)
│  ├─ CaseService (Business logic)
│  └─ Tools (Market research, Financial analysis, Competitive intel)
│
└─ Database (SQLAlchemy async + Supabase Postgres)
   ├─ case_studies (Generated cases)
   ├─ user_solutions (Student submissions)
   └─ users (User profiles — currently unused; user_id is passed in from the LMS as a plain int)
```
 
**Note on auth:** there is no JWT/session layer in this service. `user_id` is trusted as-is from the request body. This is intentional for now since the LMS is the auth boundary — if that assumption ever changes, this needs a real auth layer before going further.
 
---
 
## Tech Stack
 
| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI 0.104 |
| **Agentic AI** | LangGraph 0.0.15 |
| **LLM** | Groq — `openai/gpt-oss-120b` (Groq deprecated the old Llama models in 2026; set via `GROQ_MODEL` env var) |
| **Database** | SQLAlchemy (async) + Supabase Postgres, via Session Pooler |
| **Language** | Python 3.12 (do **not** use 3.14 — `asyncpg` and `pydantic-core` don't have compatible wheels yet) |
| **Async** | asyncio, uvicorn |
 
---
 
## Project Structure
 
```
caseforge/
├── main.py                          # FastAPI entry point
├── config.py                        # Settings from .env
├── graph.py                         # LangGraph state machine
├── requirements.txt                 # Dependencies
│
├── app/
│   ├── api/
│   │   └── routes.py               # REST endpoints
│   │
│   ├── services/
│   │   ├── groq.py                 # Groq API wrapper
│   │   ├── case.py                 # Case generation logic
│   │   └── workflow.py             # LangGraph executor
│   │
│   ├── workflows/
│   │   ├── state.py                # State definition
│   │   └── nodes.py                # Workflow nodes
│   │
│   ├── tools.py                    # Market research, financial analysis, etc.
│   ├── prompts.py                  # LLM prompts
│   ├── models.py                   # SQLAlchemy models
│   ├── db.py                       # Database setup
│   └── logger.py                   # Logging
│
└── scripts/
    └── init_db.py                  # One-time DB initialization
```
 
---
 
## Installation & Setup
 
### Prerequisites
- **Python 3.12** specifically (see Tech Stack note above)
- A Groq API key — free at [console.groq.com](https://console.groq.com)
- A Supabase project — free at [supabase.com](https://supabase.com)
### 1. Clone & set up the venv
```bash
git clone <this-repo>
cd CASE_FORGE
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
 
### 2. Configure environment
Create a `.env` file in the project root:
```
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=openai/gpt-oss-120b
DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<url-encoded-password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```
 
Get the `DATABASE_URL` from your Supabase project: **Connect → Direct (Connection string) tab → Session pooler**. If your DB password has special characters, URL-encode them (`@` → `%40`, etc.) or the connection string will fail to parse.
 
### 3. Run the server
```bash
python -m uvicorn main:app --reload
```
Server runs at `http://localhost:8000`. Tables are created automatically on startup via `init_db()` — no manual migration step needed for a fresh Supabase project.
 
API docs: `http://localhost:8000/docs`
 
---
 
## API Usage
 
### Generate a Case Study
```bash
curl -X POST http://localhost:8000/api/v1/cases/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "industry": "FinTech",
    "complexity": "beginner",
    "focus_area": "Product Strategy",
    "time_limit": 60
  }'
```
 
### Evaluate a Solution
```bash
curl -X POST http://localhost:8000/api/v1/solutions/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "case_id": 1,
    "solution": "Your proposed solution text here..."
  }'
```
 
### Get a Case
```bash
curl http://localhost:8000/api/v1/cases/1
```
 
### Get a User's Case History
```bash
curl http://localhost:8000/api/v1/users/1/cases
```
 
### Health Check
```bash
curl http://localhost:8000/api/v1/health
```
 
---
 
## LangGraph Workflow
 
```
START
  ↓
[GENERATE] - LLM creates raw case, using market/financial/competitive tools
  ↓
[VALIDATE] - Check quality & completeness
  ↓
  ├─ Valid?               → [SAVE] → END
  ├─ Invalid, retries left → [REFINE] → back to VALIDATE
  └─ Max retries hit       → [ERROR] → END
```
 
Verified in testing: `refinements_used: 0` on first-try generations against `gpt-oss-120b` — validation is passing cleanly without needing the refine loop.
 
---
 
## Database Schema
 
### case_studies
```sql
CREATE TABLE case_studies (
  id INTEGER PRIMARY KEY,
  uuid VARCHAR(36) UNIQUE,
  user_id INTEGER,
  title VARCHAR(200),
  industry VARCHAR(100),
  complexity complexitylevel,   -- Postgres enum: beginner / intermediate / advanced
  focus_area VARCHAR(200),
  case_data JSON,
  generation_time_ms INTEGER,
  tokens_used INTEGER,
  model_used VARCHAR(100),
  refinement_count INTEGER,
  created_at DATETIME
);
```
 
### user_solutions
```sql
CREATE TABLE user_solutions (
  id INTEGER PRIMARY KEY,
  uuid VARCHAR(36) UNIQUE,
  user_id INTEGER,
  case_id INTEGER,
  solution_text VARCHAR(5000),
  overall_score FLOAT,
  reasoning_score FLOAT,
  communication_score FLOAT,
  business_acumen_score FLOAT,
  feedback_data JSON,
  created_at DATETIME
);
```
 
---
 
## What's Left
 
This backend works end-to-end locally against production Postgres. Not yet done:
 
- [ ] **Deploy target** — not yet decided (Render / Railway / Fly / other). Blocks actual public deployment.
- [ ] **CORS lockdown** — `main.py` currently allows `allow_origins=["*"]`. Needs to be scoped to the LMS's actual domain before going live. Blocked on getting that domain.
- [ ] **DB session lifetime** — `get_db_session()` currently holds a Postgres connection open for the full request, including the multi-second Groq call. Fine at low volume; needs fixing (only open a session for the actual DB read/write, not the LLM call) before real concurrent load, given Supabase's pooler connection limits.
- [ ] **Async task queue (Redis)** — for handling 100–300 concurrent users without blocking on Groq in-request. Not started. Requested but scope not yet confirmed with team lead — likely a second phase after initial deploy, not a blocker for first launch.
- [ ] **Load testing (Locust)** — depends on the above being in place first.
- [ ] **Rate limiting** — none currently. Would likely ride on the same Redis instance as the task queue.
---
 
## Known Issues / Gotchas
 
- **Python 3.14 will not work.** `asyncpg` and `pydantic-core` (compiled dependencies) don't yet have 3.14 wheels — use 3.12.
- If you hit `ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'` on import, it means your Python patch version is 3.12.4+ and your `pydantic` is too old — this repo already pins `pydantic>=2.9.0` to avoid it, don't downgrade it.
- Supabase's **Session pooler** (port 5432) is what's configured here, not the Transaction pooler (6543) — the transaction pooler breaks asyncpg's default prepared-statement behavior with SQLAlchemy unless explicitly disabled.
- Cross-region latency is real: Supabase pooler region vs. server region adds a few seconds to DB round-trips. Worth picking a region close to wherever this actually deploys.
---
 
## Security
 
- Environment variables for secrets (never commit `.env`)
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy
- No auth layer — see Architecture note above; the LMS is the trust boundary
- Error handling without exposing internals
---
 
## Author
 
Built by Aniketh Cheerath — Sketch Brains
 
**Contact:** cheerathaniketh@gmail.com
 
---

## Changelog

### Aug 18, 2026
- **Redis caching (Upstash)** — wired `cache.py` into `POST /api/v1/cases/generate`. Uses a per-user idempotency guard (`case:{user_id}:{industry}:{complexity}:{focus_area}`, 10s TTL) to prevent duplicate case generation on double-submits, without caching case *content* — every unique request still generates a fresh case, preserving the "no repeats" guarantee.
- **Leaderboard endpoint** — exposed `LeaderboardService` via `GET /api/v1/leaderboard`, supporting `metric` (`average_score` / `total_solved` / `best_score` / `sum_score`) and `limit` query params. Computed live from `user_solutions` via SQLAlchemy aggregates — no caching layer on this yet.
- Switched local dev Redis from Valkey (system package) to Upstash (cloud REST API) to match production usage at ~300-user LMS scale, per team lead's direction. Local Valkey install is unused by the app now — kept around for local `redis-cli`-style debugging only.
- Fixed `GROQ_MODEL` — was still pointing at deprecated `llama-3.3-70b-versatile` in local `.env`, causing startup 404s. Confirmed working against `openai/gpt-oss-120b`.

**Still outstanding:** DB session lifetime issue (open Postgres connection held across the multi-second Groq call) — noted in "What's Left" above, becomes more urgent now that caching + leaderboard add more concurrent DB/API traffic per request cycle. No caching yet on leaderboard reads.

---
### Aug 18, 2026 (evening)
- **DB session lifetime fix** — the biggest concurrency risk flagged in "What's Left" is resolved. `WorkflowService` and `CaseService.evaluate_solution` no longer hold a Postgres session open across the multi-second Groq call. Sessions now open only immediately before/after Groq calls, for the actual DB read/write, then close right away. Verified via log timestamps: `db_session_opening` now fires only after `workflow_execution_complete`, not before the Groq call. `GET /cases/{id}` and `GET /users/{id}/cases` were left on request-scoped `Depends()` sessions since they have no slow external call in the middle — no change needed there.
- Fixed a stale hardcoded model name (`llama-3.3-70b-versatile`) in `WorkflowService`'s saved DB record — now reads from `settings.GROQ_MODEL` so `case_studies.model_used` accurately reflects what actually generated the case.
- Flagged `CaseService.generate_case` as likely dead code — `routes.py` calls `WorkflowService.generate_case_with_workflow()` instead, not this method. Left it functional (fixed to match the new session pattern) but needs confirming with the team before removing.
- Verified end-to-end: case generation, solution evaluation, and leaderboard all re-tested after the refactor — identical behavior from the API's perspective, connections just released faster under the hood.
- **Async task queue** — scoped out three approaches (FastAPI `BackgroundTasks`, RQ/arq + worker process on Upstash's Redis, or Upstash QStash). Holding off on building until scope is confirmed with team lead, per "What's Left" — the three options solve meaningfully different problems and building the wrong one wastes real time.

**Updated "What's Left" status:** DB session lifetime — ✅ done. Async task queue — still not started, now with a scoped decision pending from team lead.

---
 
## Resources
 
- [LangGraph Docs](https://python.langchain.com/docs/langgraph)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Groq API Docs](https://console.groq.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)


