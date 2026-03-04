# GraphRAG-OMOP Dashboard - Overview

**Version:** 2.0 (Updated 2026-03-04)
**Status:** 🔄 Backend Complete ✅ | Frontend Pending 🔵

---

## 📋 Executive Summary

**Objective:** Create a visual dashboard for live demos to physicians, showing the automated process of converting clinical text into standardized OMOP concepts.

**Target Audience:** Physicians (non-technical users)
**Deployment:** Local (localhost) for demos
**Tech Stack:**
- **Backend:** FastAPI + Python pipeline (Phase 1 ✅ Complete)
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS (Pending)

**Key Features:**
- Clinical text input with pre-loaded examples
- Two-stage processing: concept extraction → OMOP mapping
- Comprehensive results table with all mapping details
- CSV export functionality
- Professional, medical-grade UI

---

## 🏗️ System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
│                    http://localhost:3000                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            FRONTEND (Next.js + TypeScript)                │  │
│  │  - Text input + example buttons                           │  │
│  │  - Backend status monitoring                              │  │
│  │  - Two-stage processing UI                                │  │
│  │  - Results table (visual, interactive)                    │  │
│  │  - CSV export                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↕ HTTP (fetch)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            BACKEND API (FastAPI) ✅ COMPLETE              │  │
│  │        http://localhost:8000                              │  │
│  │  - GET /health (server health check)                      │  │
│  │  - GET /status (grafo load status)                        │  │
│  │  - POST /phase1 (concept extraction via GPT-4)            │  │
│  │  - POST /phase2 (OMOP mapping via SapBERT + graph)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         PYTHON PIPELINE (Existing)                        │  │
│  │  - src/phase1: GPT-4 concept extraction                   │  │
│  │  - src/phase2: SapBERT semantic search                    │  │
│  │  - Graph traversal: Standard OMOP mapping                 │  │
│  │  - Returns: Structured JSON with scores + metadata        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoints (Backend)

#### `GET /health`
Simple health check, always returns `{"status": "ok"}`.

#### `GET /status`
Returns grafo loading status:
```json
{
  "grafo_loaded": true,
  "grafo_loading": false,
  "ready": true,
  "error": null
}
```

#### `POST /phase1` - Concept Extraction
**Input:** Clinical text
**Output:** List of extracted concepts with domains
```json
{
  "concepts": [
    {"text": "diabetes", "domain": "Condition", "value": null, "unit": null},
    {"text": "metformin", "domain": "Drug", "value": 500.0, "unit": "mg"}
  ]
}
```

#### `POST /phase2` - OMOP Mapping
**Input:** List of concepts from Phase 1
**Output:** Mappings to OMOP standard concepts with scores
```json
{
  "timestamp": "2026-03-04T13:06:07.980664",
  "stats": {
    "total": 2,
    "mapped_ok": 2,
    "needs_review": 0
  },
  "mappings": [
    {
      "input": "diabetes",
      "domain": "Condition",
      "match_name": "Diabetes mellitus",
      "match_id": 201820,
      "match_vocab": "SNOMED",
      "score": 0.969,
      "standard_name": "Diabetes mellitus",
      "standard_id": 201820,
      "standard_vocab": "SNOMED",
      "status": "OK",
      "note": null,
      "value": null,
      "unit": null
    }
  ]
}
```

---

## 📂 Project Structure

```
GraphRAG-OMOP/
├── backend/                            # ✅ COMPLETE
│   ├── main.py                         # FastAPI app
│   ├── schemas.py                      # Pydantic models
│   ├── config.py                       # Configuration
│   ├── routers/
│   │   ├── health.py                   # Health + status endpoints
│   │   ├── phase1.py                   # Concept extraction endpoint
│   │   └── phase2.py                   # OMOP mapping endpoint
│   ├── src/                            # Python pipeline (existing)
│   │   ├── phase1/                     # GPT-4 extraction
│   │   └── phase2/                     # SapBERT + graph
│   ├── data/                           # Embeddings + graph data
│   ├── venv/                           # Virtual environment
│   ├── requirements.txt                # Dependencies
│   ├── .env                            # API keys
│   ├── start.bat                       # Startup script
│   ├── README.md                       # Backend documentation
│   └── PHASE1_COMPLETED.md             # ✅ Implementation report
│
├── frontend/                           # 🔵 PENDING
│   ├── app/                            # Next.js App Router
│   │   ├── layout.tsx                  # Root layout
│   │   └── page.tsx                    # Main dashboard page
│   ├── components/                     # React components
│   │   ├── BackendStatusBanner.tsx     # Status monitoring
│   │   ├── InputSection.tsx            # Text input
│   │   ├── ProcessingStatus.tsx        # Loading states
│   │   ├── ExtractedConceptsPreview.tsx # Phase 1 preview
│   │   ├── ResultsTable.tsx            # Main results
│   │   ├── ConceptRow.tsx              # Table rows
│   │   ├── StatusBadge.tsx             # Status indicators
│   │   ├── ScoreBar.tsx                # Score visualization
│   │   └── ExportButton.tsx            # CSV export
│   ├── lib/
│   │   ├── types.ts                    # TypeScript interfaces
│   │   ├── api.ts                      # API client
│   │   └── csv-export.ts               # CSV generation
│   ├── public/examples/                # Pre-loaded clinical texts
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
└── context/                            # Documentation
    ├── DASHBOARD_PLAN.md               # This file (overview)
    ├── DASHBOARD_FRONTEND_PLAN.md      # Frontend implementation plan
    ├── PHASE1_COMPLETE.md              # Phase 1 (graph) history
    ├── PHASE2_PLAN.md                  # Phase 2 (embeddings) history
    └── PHASE3_PLAN.md                  # Phase 3 (extraction) history
```

---

## 📝 Implementation Status

### Phase 1: Backend API ✅ COMPLETE

**Status:** ✅ Implemented and tested (2026-03-04)
**Documentation:** [`backend/PHASE1_COMPLETED.md`](../backend/PHASE1_COMPLETED.md)

**What was built:**
- ✅ FastAPI server with async support
- ✅ CORS middleware configured for frontend
- ✅ Background grafo loading on startup (~30s)
- ✅ Health and status monitoring endpoints
- ✅ Two-stage processing endpoints (Phase 1 + Phase 2)
- ✅ Pydantic models for request/response validation
- ✅ Complete logging and error handling
- ✅ Startup script for Windows

**Endpoints tested:**
- ✅ `GET /health` → Returns 200 OK
- ✅ `GET /status` → Shows grafo load status
- ✅ `POST /phase1` → Extracts concepts from text (3 concepts in 5-10s)
- ✅ `POST /phase2` → Maps concepts to OMOP (3 mappings in 6-15s)

**Performance:**
- Startup time: ~30s (grafo loading)
- Phase 1 (extraction): 5-10s per query
- Phase 2 (mapping): 2-5s per concept
- Total user-facing time: 10-30s per analysis

---

### Phase 2: Frontend Dashboard 🔵 PENDING

**Status:** 🔵 Planned, ready to implement
**Documentation:** [`DASHBOARD_FRONTEND_PLAN.md`](DASHBOARD_FRONTEND_PLAN.md)

**What will be built:**
- 🔵 Next.js 14 app with TypeScript
- 🔵 Backend status monitoring UI
- 🔵 Clinical text input with 3 pre-loaded examples
- 🔵 Two-stage processing flow with loading states
- 🔵 Results table with sorting, filtering, expandable rows
- 🔵 CSV export functionality
- 🔵 Professional medical-grade UI design
- 🔵 Complete test coverage

**Timeline:** 28-38 hours (~4-5 days for 1 developer)

**Phases:**
1. Frontend Foundation (3-4h) - Setup Next.js + TypeScript + API client
2. Backend Status Check (2-3h) - Monitor grafo loading
3. Input Section (2-3h) - Text input + examples
4. Two-Stage Processing (3-4h) - Phase 1 → Phase 2 flow
5. Results Table Core (4-5h) - Main table with sorting/filtering
6. Results Table Details (3-4h) - Expandable rows + tooltips
7. CSV Export (2-3h) - Download functionality
8. Polish & UX (3-4h) - Animations, accessibility, keyboard shortcuts
9. Testing & Docs (4-5h) - Component tests + user documentation
10. Final Integration (2-3h) - End-to-end testing + demo prep

---

## 🎯 Success Criteria

### Technical Requirements

✅ **Backend (Complete):**
- FastAPI server starts in <5 seconds
- Grafo loads in <30 seconds
- `/phase1` + `/phase2` respond in <30 seconds combined
- CORS configured correctly
- Error handling robust

🔵 **Frontend (Pending):**
- Next.js dev server starts in <10 seconds
- Page loads in <3 seconds
- UI responsive on all screen sizes
- No console errors
- Smooth animations

🔵 **Integration (Pending):**
- End-to-end flow works seamlessly
- All 3 examples process correctly
- CSV export generates valid files
- Error states handled gracefully

### User Experience Requirements

🔵 **For Physicians (Non-Technical):**
- Interface is intuitive and self-explanatory
- Medical terminology is clear
- Results are visually scannable
- CSV export is straightforward
- No technical jargon exposed

🔵 **For Demo:**
- Demo runs in <5 minutes
- All features demonstrated clearly
- Professional appearance
- No obvious bugs
- Impressive visual impact

---

## 📚 Documentation

### Completed Documentation

1. **Backend Implementation Report**
   - File: [`backend/PHASE1_COMPLETED.md`](../backend/PHASE1_COMPLETED.md)
   - Contains: Architecture, endpoints, testing results, performance metrics

2. **Backend API Documentation**
   - File: [`backend/README.md`](../backend/README.md)
   - Contains: Setup instructions, API reference, troubleshooting

3. **Frontend Implementation Plan**
   - File: [`DASHBOARD_FRONTEND_PLAN.md`](DASHBOARD_FRONTEND_PLAN.md)
   - Contains: Detailed 10-phase plan adapted to new backend API

### Pending Documentation

4. **Complete Setup Guide** (Phase 9 of Frontend)
   - File: `DASHBOARD_SETUP.md` (to be created)
   - Will contain: Prerequisites, backend setup, frontend setup, troubleshooting

5. **Demo Script for Physicians** (Phase 9 of Frontend)
   - File: `DASHBOARD_DEMO_GUIDE.md` (to be created)
   - Will contain: Demo checklist, example narratives, Q&A preparation

---

## 🚀 Quick Start

### Backend (Already Running)

```bash
cd backend
call venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Backend URL:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

### Frontend (To Be Implemented)

```bash
cd frontend
npm install
npm run dev
```

**Frontend URL:** http://localhost:3000

---

## ⏱️ Timeline Summary

| Phase | Description | Status | Time |
|-------|-------------|--------|------|
| **Backend** | FastAPI API wrapper | ✅ Complete | 4-6h |
| **Frontend** | Next.js dashboard | 🔵 Pending | 28-38h |
| **Total** | Full dashboard | 50% Done | 32-44h |

**Current Progress:** Backend complete, ready to start frontend implementation.

---

## 🔗 Related Documentation

### Backend (GraphRAG Pipeline)
- [Phase 1: Graph Construction](PHASE1_COMPLETE.md)
- [Phase 2: Semantic Search](PHASE2_PLAN.md)
- [Phase 3: Concept Extraction](PHASE3_PLAN.md)

### Dashboard
- [Backend Implementation](../backend/PHASE1_COMPLETED.md) ✅ Complete
- [Frontend Plan](DASHBOARD_FRONTEND_PLAN.md) 🔵 Ready to implement
- [Project Architecture](ARCHITECTURE.md)
- [Project Status](ACTUAL_FEATURE.md)

---

## 🎓 Key Design Decisions

### 1. Two-Stage API Design

**Decision:** Separate `/phase1` (extraction) and `/phase2` (mapping) endpoints instead of single `/process`

**Rationale:**
- Better separation of concerns
- Frontend can show intermediate results (extracted concepts)
- Independent error handling for each stage
- More flexible for future features

**Impact on Frontend:**
- Must implement sequential processing flow
- Two separate loading states
- Preview extracted concepts before mapping

---

### 2. Grafo Pre-loading on Startup

**Decision:** Load embeddings + graph on server startup (~30s) rather than on-demand

**Rationale:**
- Demo requires fast queries after initial load
- Acceptable one-time 30s wait
- Avoids repeated loading
- Better demo experience

**Impact on Frontend:**
- Must poll `/status` until `grafo_loaded = true`
- Show loading banner during startup
- Disable processing until ready

---

### 3. Sequential Phase 2 Processing

**Decision:** Process concepts one-by-one in Phase 2 instead of parallel

**Rationale:**
- Simpler implementation
- Acceptable performance for demo (3-7 concepts = 6-15s)
- Easier to debug
- No added complexity

**Impact on Frontend:**
- Single loading state for Phase 2
- Show total time estimate
- No per-concept progress needed

---

## ⚠️ Important Notes

1. **Backend is production-ready** for demo purposes (not for public deployment)
2. **Frontend must handle two-stage flow** (Phase 1 → Phase 2)
3. **CORS is pre-configured** for `http://localhost:3000`
4. **All testing done with real medical examples** (English + Spanish)
5. **Performance is acceptable for demo** (10-30s per query with 3-7 concepts)

---

## 📞 Next Steps

### Immediate Action
1. ✅ Backend Phase 1 complete
2. 📋 Review frontend plan: [`DASHBOARD_FRONTEND_PLAN.md`](DASHBOARD_FRONTEND_PLAN.md)
3. 🚀 Begin frontend implementation when ready
4. 📝 Follow 10-phase incremental approach

### Before Starting Frontend
- [ ] Confirm backend is running and all endpoints work
- [ ] Review frontend plan and approve approach
- [ ] Ensure Node.js 18+ installed
- [ ] Create Git branch: `feature/dashboard-frontend`

---

**Last Updated:** 2026-03-04
**Status:** Backend ✅ | Frontend 🔵 Pending
