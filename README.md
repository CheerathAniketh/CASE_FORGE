# CaseForge - Case Study Generation Engine

A scalable, production-ready AI application that generates business case studies to help students build professional mindset.

**Status:** Phase 1 MVP - Ready for deployment

## 🎯 What It Does

CaseForge generates realistic, interactive business case studies on-the-fly using:
- **GROQ Mixtral AI** for fast case generation (100-500ms)
- **LangGraph** for intelligent workflow orchestration (generate → validate → refine)
- **PostgreSQL** for persistent, scalable data storage

## 🏗️ Architecture

### Tech Stack
- **Backend:** FastAPI (async Python)
- **LLM:** GROQ API (Mixtral 8x7b)
- **Workflows:** LangGraph
- **Database:** PostgreSQL + asyncpg
- **Auth:** JWT tokens
- **Logging:** Structured JSON logging
- **Deployment:** Docker + Railway

### Workflow Pipeline

```
1. Generate Case (GROQ)
   ↓
2. Validate Quality
   ↓
3. Refine if Needed (max 2 retries)
   ↓
4. Save to Database
   ↓
5. Return to User
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- GROQ API key (free at groq.com)

### Local Development

1. **Clone and setup:**
```bash
cd caseforge
cp .env.example .env
```

2. **Add your GROQ API key to .env:**
```
GROQ_API_KEY=your_api_key_here
```

3. **Start with Docker Compose:**
```bash
docker-compose up
```

The API will be available at `http://localhost:8000`

### Manual Setup (without Docker)

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/caseforge"
export GROQ_API_KEY="your_groq_api_key"
export SECRET_KEY="your-secret-key-min-32-chars"
```

4. **Run application:**
```bash
uvicorn main:app --reload
```

## 📚 API Usage

### 1. Login (Get JWT Token)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id": "s12345"}'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 2. Generate Case Study

```bash
curl -X POST http://localhost:8000/api/v1/case-studies/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "industry": "Technology",
    "complexity": "intermediate",
    "focus_area": "Digital Transformation",
    "time_limit_minutes": 60,
    "num_questions": 3
  }'
```

Response (example):
```json
{
  "uuid": "a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p",
  "title": "Disrupting the E-commerce Market",
  "industry": "Technology",
  "complexity": "intermediate",
  "case_data": {
    "problem_statement": "...",
    "discussion_questions": [...],
    "solution_framework": {...},
    ...
  },
  "created_at": "2026-05-10T15:57:58",
  "generation_time_ms": 1200,
  "tokens_used": 2500,
  "refinement_count": 1
}
```

### 3. Get User's Cases

```bash
curl http://localhost:8000/api/v1/case-studies/user/history \
  -H "Authorization: Bearer eyJhbGc..."
```

### 4. Get Single Case

```bash
curl http://localhost:8000/api/v1/case-studies/{uuid} \
  -H "Authorization: Bearer eyJhbGc..."
```

### 5. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

## 📁 Project Structure

```
caseforge/
├── app/
│   ├── core/              # Configuration & security
│   ├── database/          # Models & schemas
│   ├── workflows/         # LangGraph workflow logic
│   ├── services/          # Business logic
│   ├── api/v1/            # REST endpoints
│   ├── middleware/        # Error handlers
│   ├── utils/             # Helpers & prompts
│   ├── tools/             # LangGraph tools
│   └── llm/               # LLM prompts & templates
├── main.py                # FastAPI app entry
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── Dockerfile            # Container image
├── docker-compose.yml    # Local dev setup
└── README.md             # This file
```

## 🔄 Workflow Details

### Node 1: Generate
- Calls GROQ Mixtral 8x7b API
- Generates case study JSON
- Tracks tokens used

### Node 2: Validate
- Checks JSON parsing success
- Verifies required fields present
- Validates content length
- Scores overall quality (0-1)

### Node 3: Refine (if needed)
- Runs if validation score < 0.7
- Max 2 refinement attempts
- Uses validation errors as context
- Returns to validation after refining

### Node 4: Save
- Persists case to PostgreSQL
- Records generation time & tokens
- Returns final case with metadata

## 📊 Monitoring & Logging

### Structured JSON Logging
All events logged as JSON for easy parsing:
```json
{
  "timestamp": "2026-05-10T15:57:58.123456",
  "level": "INFO",
  "message": "case_generation_success",
  "user_id": 123,
  "case_uuid": "abc-123",
  "generation_time_ms": 1200,
  "tokens_used": 2500
}
```

### Log Levels
- Set via `LOG_LEVEL` env variable
- Options: DEBUG, INFO, WARNING, ERROR
- Default: INFO

## 🔐 Security

- **JWT Authentication:** All endpoints except `/api/v1/health` require JWT
- **Token Expiry:** 24 hours (configurable)
- **CORS:** Configurable allowed origins
- **Input Validation:** Pydantic schemas validate all inputs
- **Error Handling:** Generic error messages in production

## ⚡ Performance

- **Case Generation:** 1-5 seconds (depending on GROQ)
- **Validation:** <100ms
- **Database:** <50ms per query
- **Concurrent Users:** Designed for 1000-1500 simultaneous students
- **Token Usage:** ~2500 tokens per case (~$0.0002)

## 🌍 Deployment

### Railway (Recommended for MVP)
1. Push code to GitHub
2. Connect GitHub to Railway
3. Add environment variables
4. Deploy - Railway auto-scales

### Docker
```bash
docker build -t caseforge .
docker run -p 8000:8000 --env-file .env caseforge
```

### AWS ECS (Phase 2)
- Load Balancer (ALB)
- Auto-scaling groups (3-10 instances)
- RDS PostgreSQL (multi-AZ)
- CloudWatch monitoring

## 📈 Scaling Roadmap

### Phase 1 (Current)
✅ Single FastAPI instance
✅ PostgreSQL single instance
✅ GROQ integration
✅ LangGraph workflow
✅ JWT auth

### Phase 2 (Next)
📅 Redis caching
📅 Connection pooling
📅 Async queues (Celery)
📅 Advanced monitoring (Sentry)

### Phase 3 (Future)
📅 RAG + ChromaDB
📅 Analytics dashboard
📅 Multi-tenancy
📅 Advanced refinement

## 🐛 Debugging

### Enable SQL Logging
```bash
ECHO_SQL=true uvicorn main:app
```

### Enable Debug Logging
```bash
LOG_LEVEL=DEBUG uvicorn main:app
```

### Test GROQ Connection
```bash
curl http://localhost:8000/api/v1/health
```

## 📝 Environment Variables

| Variable | Example | Description |
|----------|---------|---|
| `GROQ_API_KEY` | `gsk_...` | GROQ API key |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `SECRET_KEY` | `your-secret-min-32-chars` | JWT signing key |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Debug mode |

See `.env.example` for all options.

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test locally
4. Push and create PR

## 📞 Support

For issues:
1. Check logs: `docker logs caseforge_api`
2. Verify `.env` is set up
3. Ensure PostgreSQL is running
4. Test `/api/v1/health` endpoint

## 📄 License

MIT

---

**Built with ❤️ for startup success**
