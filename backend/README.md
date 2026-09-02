# GraphRAG-OMOP Backend API

FastAPI backend for the GraphRAG-OMOP dashboard providing clinical concept extraction and OMOP standardization endpoints.

---

## 📋 Prerequisites

- Python 3.11+
- Virtual environment activated
- OpenAI API key
- OMOP embeddings generated

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# From backend/ directory
cd backend

# Activate virtual environment
call venv\Scripts\activate   # Windows
# or
source venv/bin/activate      # Linux/Mac

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Ensure `.env` file exists with:

```bash
OPENAI_API_KEY=sk-your-key-here
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
```

### 3. Verify Data Files

Check that these files exist:
- `data/embeddings/embeddings.npy`
- `data/embeddings/concept_id_to_index.pkl`
- `data/processed/nodes.csv`
- `data/processed/edges.csv`
- `data/processed/omop_graph.pkl`

If missing, generate embeddings:
```bash
python -m src.phase2.embeddings --max-concepts 100000
```

### 4. Start Server

**Option A: Using start.bat (Recommended for Windows)**
```bash
start.bat
```

**Option B: Manual start**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# o: python main.py
```

The server will start and automatically begin loading the grafo in the background (~15-30 seconds).

---

## 🌐 API Endpoints

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

### `GET /health`

**Purpose:** Liveness check

**Response:**
```json
{
  "status": "ok"
}
```

---

### `GET /status`

**Purpose:** Check system readiness

**Response (Loading):**
```json
{
  "grafo_loaded": false,
  "grafo_loading": true,
  "ready": false,
  "error": null
}
```

**Response (Ready):**
```json
{
  "grafo_loaded": true,
  "grafo_loading": false,
  "ready": true,
  "error": null
}
```

**Usage:** Frontend should poll this endpoint until `ready: true` before calling `/phase2`.

---

### `POST /phase1`

**Purpose:** Extract medical concepts from clinical text (GPT-4)

**Request:**
```json
{
  "text": "Patient with diabetes treated with metformin 850mg twice daily"
}
```

**Response:**
```json
{
  "concepts": [
    {
      "text": "diabetes",
      "domain": "Condition",
      "value": null,
      "unit": null
    },
    {
      "text": "metformin",
      "domain": "Drug",
      "value": 850,
      "unit": "mg"
    }
  ]
}
```

**Notes:**
- Does NOT require grafo to be loaded
- Calls OpenAI GPT-4 API
- Takes ~5-10 seconds depending on text length

**cURL Example:**
```bash
curl -X POST http://localhost:8000/phase1 \
  -H "Content-Type: application/json" \
  -d '{"text":"Patient with diabetes"}'
```

---

### `POST /phase2`

**Purpose:** Search OMOP and map concepts to standards

**Request:**
```json
{
  "concepts": [
    {
      "text": "diabetes",
      "domain": "Condition",
      "value": null,
      "unit": null
    },
    {
      "text": "metformin",
      "domain": "Drug",
      "value": null,
      "unit": null
    }
  ]
}
```

**Response:**
```json
{
  "timestamp": "2026-03-04T12:30:00.123456",
  "stats": {
    "total": 2,
    "mapped_ok": 2,
    "needs_review": 0
  },
  "mappings": [
    {
      "input": "diabetes",
      "domain": "Condition",
      "match_name": "Type 2 diabetes mellitus",
      "match_id": 201826,
      "match_vocab": "SNOMED",
      "score": 0.95,
      "standard_name": "Type 2 diabetes mellitus",
      "standard_id": 201826,
      "standard_vocab": "SNOMED",
      "status": "OK",
      "note": null,
      "value": null,
      "unit": null
    },
    {
      "input": "metformin",
      "domain": "Drug",
      "match_name": "Metformin",
      "match_id": 1503297,
      "match_vocab": "RxNorm",
      "score": 0.98,
      "standard_name": "Metformin",
      "standard_id": 1503297,
      "standard_vocab": "RxNorm",
      "status": "OK",
      "note": null,
      "value": null,
      "unit": null
    }
  ]
}
```

**Notes:**
- REQUIRES grafo to be loaded (check `/status` first)
- Returns 503 Service Unavailable if grafo not ready
- Takes ~2-5 seconds per concept

**cURL Example:**
```bash
curl -X POST http://localhost:8000/phase2 \
  -H "Content-Type: application/json" \
  -d '{"concepts":[{"text":"diabetes","domain":"Condition"}]}'
```

---

## 🧪 Testing

### Manual Testing Sequence

**1. Start server and check health**
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

**2. Check status (should be loading)**
```bash
curl http://localhost:8000/status
# Expected: {"grafo_loading":true,"ready":false}
```

**3. Wait for grafo to load (~15-30 seconds)**

**4. Check status again (should be ready)**
```bash
curl http://localhost:8000/status
# Expected: {"grafo_loaded":true,"ready":true}
```

**5. Test Phase 1**
```bash
curl -X POST http://localhost:8000/phase1 \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Patient with diabetes treated with metformin\"}"
# Should return concepts array
```

**6. Test Phase 2**
```bash
curl -X POST http://localhost:8000/phase2 \
  -H "Content-Type: application/json" \
  -d "{\"concepts\":[{\"text\":\"diabetes\",\"domain\":\"Condition\"}]}"
# Should return mappings array
```

---

## 🔧 Troubleshooting

### Server won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
call venv\Scripts\activate
pip install -r requirements.txt
```

---

### `/phase2` returns 503

**Error:** `System not ready. Grafo still loading.`

**Solution:** Wait for grafo to finish loading. Check `/status` until `ready: true`.

Grafo loading takes 15-30 seconds on first startup.

---

### OpenAI API errors

**Error:** `OPENAI_API_KEY not found`

**Solution:** Check `.env` file exists and contains valid API key.

---

### Embeddings not found

**Error:** `Embeddings file not found`

**Solution:** Generate embeddings first:
```bash
python -m src.phase2.embeddings --max-concepts 100000
```

This takes ~10-15 minutes for 100k concepts.

---

### CORS errors in frontend

**Error:** Browser blocks requests from frontend

**Solution:** Verify `FRONTEND_URL` in `.env` matches your frontend port (default: http://localhost:3000)

---

## 📁 Project Structure

```
backend/
├── main.py                     # FastAPI application (uvicorn main:app)
├── cli.py                      # Terminal CLI (no frontend needed)
├── config.py                   # Configuration settings (reads backend/.env)
├── schemas.py                  # API request/response schemas
├── routers/                    # health.py, phase1.py, phase2.py
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (copy from .env.example)
├── start.bat                   # Startup script (Windows)
├── README.md                   # This file
├── src/                        # Source code
│   ├── phase1/                 # GPT-4 extraction
│   └── phase2/                 # Semantic search (singleton retriever in phase2/main.py)
├── data/                       # Data files (NOT in git)
│   ├── source/                 # Athena CSVs
│   ├── embeddings/             # SapBERT embeddings + FAISS index
│   ├── processed/              # nodes.csv, edges.csv, omop_graph.pkl
│   └── output/                 # Pipeline outputs
└── venv/                       # Virtual environment
```

---

## 🐛 Development

### Run with auto-reload
```bash
uvicorn main:app --reload --port 8000
```

### View logs
Logs are printed to console. Look for:
- `🚀 FastAPI server starting...`
- `⏳ Starting grafo initialization...`
- `✅ Grafo initialization complete!`

### Access API docs
Open http://localhost:8000/docs for interactive Swagger UI.

---

## 🔗 Related Documentation

- Project README: [../README.md](../README.md)
- Handover: [../HANDOVER.md](../HANDOVER.md)

---

## 📝 Notes

- Server loads grafo automatically on startup
- First load takes 15-30 seconds
- Subsequent queries are fast (<5 seconds)
- Frontend should poll `/status` until ready
- Phase 1 works immediately (no grafo needed)
- Phase 2 requires grafo loaded

---

**Version:** 1.0.0
**Last Updated:** 2026-03-04
