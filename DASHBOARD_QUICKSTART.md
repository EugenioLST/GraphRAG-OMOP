# GraphRAG-OMOP Dashboard - Quick Start

Complete guide to run the full dashboard (backend + frontend).

## ⚡ Quick Start

```bash
# Terminal 1: Backend
cd backend
start.bat

# Terminal 2: Frontend
cd frontend
npm install  # First time only
npm run dev

# Open: http://localhost:3000
```

## What Happens

1. **Backend starts** (~30 seconds) - Loads embeddings + OMOP graph
2. **Frontend loads** - Dashboard opens at localhost:3000
3. **"System Ready"** - Banner appears when backend is loaded
4. **Try example** - Click "Cardiac Case" button
5. **Process** - Click "Process Text" or `Ctrl+Enter`
6. **See results** - Phase 1 extraction → Phase 2 mapping → Full table

## Testing

### Example 1: Cardiac Case (English)
- Extracts: hypertension, diabetes, enalapril, metformin, chest pain, furosemide
- Processing time: ~15-20 seconds total

### Example 2: Respiratory (Spanish)
- Extracts: dolor de garganta, fatiga, febrícula
- Maps Spanish → English OMOP standards

### Example 3: Diabetes (Mixed)
- Extracts: diabetes, metformin (1000mg), liraglutide (1.2mg), HbA1c (9.2%)
- Includes measurements with values

## Features to Try

- ✅ Sort table by clicking column headers
- ✅ Filter by domain (Drug, Condition, etc.)
- ✅ Click rows to see full details
- ✅ Export CSV with all results
- ✅ Use `Ctrl+Enter` to process, `Esc` to clear

## Troubleshooting

### Backend offline?
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --port 8000 --reload
```

### Missing npm packages?
```bash
cd frontend
npm install
```

### Port already in use?
```bash
# Kill process on port 8000 or 3000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Performance

| Stage | Time | Notes |
|-------|------|-------|
| Backend startup | ~30s | First time loading |
| Frontend startup | <5s | Next.js compilation |
| Phase 1 (Extract) | 5-10s | GPT-4 API call |
| Phase 2 (Map) | 10-15s | SapBERT + graph |
| **Total** | **15-25s** | Per query |

## Documentation

- Backend API docs: http://localhost:8000/docs
- Backend status: `backend/PHASE1_COMPLETED.md`
- Frontend plan: `context/DASHBOARD_FRONTEND_PLAN.md`
- Architecture: `context/DASHBOARD_PLAN.md`

## Success Checklist

- [ ] Backend starts without errors
- [ ] Frontend shows at localhost:3000
- [ ] "System Ready" banner appears
- [ ] Example 1 processes successfully
- [ ] Results table displays with all fields
- [ ] CSV export downloads file
- [ ] Keyboard shortcuts work

---

**Status:** ✅ Fully Functional | 🎯 Ready for Demos

**Enjoy!** 🎉
