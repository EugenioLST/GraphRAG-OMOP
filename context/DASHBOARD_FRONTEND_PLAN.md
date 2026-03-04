# Dashboard Frontend - Implementation Plan

**Version:** 2.0 (Updated 2026-03-04)
**Status:** 🔵 Ready to implement
**Backend Status:** ✅ Phase 1 Complete

---

## 📋 Overview

This document contains the **frontend-only** implementation plan for the GraphRAG-OMOP visual dashboard. Backend Phase 1 is already complete and documented in [`backend/PHASE1_COMPLETED.md`](../backend/PHASE1_COMPLETED.md).

**Goal:** Create a professional, medical-grade web interface for demonstrating the automated clinical text → OMOP standardization pipeline to physicians.

**Target Audience:** Physicians (non-technical users)
**Tech Stack:** Next.js 14 + TypeScript + Tailwind CSS
**Timeline:** 25-36 hours (~4-5 days)

---

## 🔌 Backend API Reference

The frontend will consume these endpoints:

### `GET /health`
**Purpose:** Server health check

**Response:**
```json
{
  "status": "ok"
}
```

---

### `GET /status`
**Purpose:** Check if grafo is loaded and ready

**Response:**
```json
{
  "grafo_loaded": true,
  "grafo_loading": false,
  "ready": true,
  "error": null
}
```

---

### `POST /phase1`
**Purpose:** Extract medical concepts from clinical text using GPT-4

**Request:**
```json
{
  "text": "Patient with diabetes treated with metformin 500mg"
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
      "value": 500.0,
      "unit": "mg"
    }
  ]
}
```

---

### `POST /phase2`
**Purpose:** Map extracted concepts to OMOP standard concepts

**Request:**
```json
{
  "concepts": [
    {"text": "diabetes", "domain": "Condition", "value": null, "unit": null},
    {"text": "metformin", "domain": "Drug", "value": 500.0, "unit": "mg"}
  ]
}
```

**Response:**
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
    },
    {
      "input": "metformin",
      "domain": "Drug",
      "match_name": "metformin",
      "match_id": 1503297,
      "match_vocab": "RxNorm",
      "score": 1.0,
      "standard_name": "metformin",
      "standard_id": 1503297,
      "standard_vocab": "RxNorm",
      "status": "OK",
      "note": null,
      "value": 500.0,
      "unit": "mg"
    }
  ]
}
```

---

## 🎯 Frontend Flow

```
User opens dashboard (localhost:3000)
         ↓
1. Check backend status (GET /status)
   - If grafo not loaded → show loading indicator
   - Poll until ready
         ↓
2. User inputs clinical text or selects example
         ↓
3. Click "Process" button
         ↓
4. Call POST /phase1 (extract concepts)
   - Show loading spinner
   - Display extracted concepts
         ↓
5. Automatically call POST /phase2 (map to OMOP)
   - Show loading spinner per concept
   - Display mappings in table
         ↓
6. User reviews results
   - View table with all details
   - Download CSV if needed
```

**Key Difference from Original Plan:**
- Original plan had single `/process` endpoint
- New implementation requires **sequential calls**: `/phase1` → `/phase2`
- Frontend must handle two-stage processing with separate loading states

---

## 📦 Implementation Phases

---

## Phase 1: Frontend Foundation (Day 1)

**Goal:** Setup Next.js project with basic UI structure

**Time Estimate:** 3-4 hours

### Tasks

1. ✅ Create Next.js 14 app with TypeScript
   ```bash
   npx create-next-app@latest frontend --typescript --tailwind --app
   ```

2. ✅ Install dependencies
   ```bash
   npm install react-icons
   ```

3. ✅ Create TypeScript interfaces in `lib/types.ts`
   ```typescript
   // Phase 1 types
   export interface ExtractedConcept {
     text: string;
     domain: string;
     value: number | null;
     unit: string | null;
   }

   export interface Phase1Response {
     concepts: ExtractedConcept[];
   }

   // Phase 2 types
   export interface ConceptMapping {
     input: string;
     domain: string;
     match_name: string;
     match_id: number;
     match_vocab: string;
     score: number;
     standard_name: string;
     standard_id: number;
     standard_vocab: string;
     status: "OK" | "REVIEW";
     note: string | null;
     value: number | null;
     unit: string | null;
   }

   export interface Phase2Response {
     timestamp: string;
     stats: {
       total: number;
       mapped_ok: number;
       needs_review: number;
     };
     mappings: ConceptMapping[];
   }

   // Status types
   export interface BackendStatus {
     grafo_loaded: boolean;
     grafo_loading: boolean;
     ready: boolean;
     error: string | null;
   }
   ```

4. ✅ Create API client in `lib/api.ts`
   ```typescript
   const API_BASE_URL = 'http://localhost:8000';

   export async function checkBackendStatus(): Promise<BackendStatus> {
     const response = await fetch(`${API_BASE_URL}/status`);
     return response.json();
   }

   export async function extractConcepts(text: string): Promise<Phase1Response> {
     const response = await fetch(`${API_BASE_URL}/phase1`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ text })
     });
     return response.json();
   }

   export async function mapConcepts(concepts: ExtractedConcept[]): Promise<Phase2Response> {
     const response = await fetch(`${API_BASE_URL}/phase2`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ concepts })
     });
     return response.json();
   }
   ```

5. ✅ Create basic layout in `app/layout.tsx`
6. ✅ Create main page structure in `app/page.tsx`
7. ✅ Setup Tailwind config with medical-friendly colors
8. ✅ Test Next.js dev server starts

### Files to Create
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/tailwind.config.ts`
- `frontend/next.config.js`
- `frontend/app/layout.tsx` (~50 lines)
- `frontend/app/page.tsx` (~100 lines stub)
- `frontend/lib/types.ts` (~100 lines)
- `frontend/lib/api.ts` (~80 lines)

### Success Criteria
- ✅ Next.js dev server runs on localhost:3000
- ✅ Basic page layout renders
- ✅ TypeScript compilation works
- ✅ Tailwind CSS styling applies

---

## Phase 2: Backend Status Check (Day 1)

**Goal:** Implement grafo loading status check and display

**Time Estimate:** 2-3 hours

### Tasks

1. ✅ Create `components/BackendStatusBanner.tsx`
   - Poll `/status` endpoint every 2 seconds while loading
   - Show banner: "System loading... Please wait (~30 seconds)"
   - Show success banner when ready
   - Show error banner if loading fails

2. ✅ Integrate status banner in `app/page.tsx`
   - Display at top of page
   - Disable input section while not ready
   - Auto-hide success banner after 3 seconds

3. ✅ Handle error states
   - Network errors (backend not running)
   - Loading errors (grafo failed to load)
   - Clear error messages for users

### Files to Create
- `frontend/components/BackendStatusBanner.tsx` (~100 lines)

### Success Criteria
- ✅ Status banner displays on page load
- ✅ Polls backend until ready
- ✅ Handles backend offline gracefully
- ✅ Displays clear status messages

---

## Phase 3: Input Section (Day 2)

**Goal:** Build clinical text input area with examples

**Time Estimate:** 2-3 hours

### Tasks

1. ✅ Create `components/InputSection.tsx`
   - Large textarea for clinical text input
   - Character counter
   - Clear button

2. ✅ Create 3 example buttons with medical cases:

   **Example 1 (Cardiac - English):**
   ```
   A 58-year-old male with a history of hypertension and type 2 diabetes mellitus, treated with enalapril 10 mg/day and metformin 850 mg twice daily, presents with a 3-day history of chest pain, dyspnea on exertion, and lower extremity edema. Physical examination reveals blood pressure 150/95 mmHg, heart rate 92 bpm, oxygen saturation 94%, bilateral basal crackles, and bilateral pitting edema. An ECG, cardiac biomarkers, and chest X-ray are ordered, and intravenous furosemide 40 mg is administered for suspected decompensated heart failure.
   ```

   **Example 2 (Respiratory - Spanish):**
   ```
   Paciente mujer de 34 años que consulta por dolor de garganta y fatiga desde hace tres días. Refiere dificultad para tragar aunque puede comer y beber. No ha presentado fiebre alta, solo febrícula el primer día. En la exploración se observa faringe levemente eritematosa sin exudados evidentes. Se diagnostica probable infección viral y se recomienda hidratación, reposo y analgésicos según necesidad.
   ```

   **Example 3 (Diabetes - Mixed):**
   ```
   Patient with poorly controlled type 2 diabetes mellitus (HbA1c 9.2%) on metformin monotherapy. Blood glucose levels consistently elevated (fasting 180-220 mg/dL). Creatinine 1.1 mg/dL, eGFR 72 mL/min. Starting liraglutide 1.2 mg subcutaneous daily and increasing metformin to 1000 mg twice daily.
   ```

3. ✅ Create "Process" button
   - Disabled while backend not ready
   - Disabled while processing
   - Loading spinner when active

4. ✅ Add responsive design (mobile-friendly)

### Files to Create
- `frontend/components/InputSection.tsx` (~200 lines)
- `frontend/public/examples/example1.txt`
- `frontend/public/examples/example2.txt`
- `frontend/public/examples/example3.txt`

### Success Criteria
- ✅ Text area accepts input
- ✅ Example buttons populate text area
- ✅ UI is clean and professional
- ✅ Process button triggers API call
- ✅ Responsive on mobile/tablet/desktop

---

## Phase 4: Two-Stage Processing Flow (Day 2)

**Goal:** Implement sequential Phase 1 → Phase 2 processing with loading states

**Time Estimate:** 3-4 hours

### Tasks

1. ✅ Create `components/ProcessingStatus.tsx`
   - Show current stage: "Extracting concepts..." or "Mapping to OMOP..."
   - Progress indicator (Stage 1 of 2, Stage 2 of 2)
   - Estimated time remaining
   - Spinner animation

2. ✅ Implement processing logic in `app/page.tsx`
   ```typescript
   const handleProcess = async () => {
     try {
       // Stage 1: Extract concepts
       setProcessingStage('phase1');
       const phase1Result = await extractConcepts(inputText);
       setExtractedConcepts(phase1Result.concepts);

       // Stage 2: Map to OMOP
       setProcessingStage('phase2');
       const phase2Result = await mapConcepts(phase1Result.concepts);
       setMappings(phase2Result.mappings);
       setStats(phase2Result.stats);

       setProcessingStage('complete');
     } catch (error) {
       setProcessingStage('error');
       setError(error.message);
     }
   };
   ```

3. ✅ Create `components/ExtractedConceptsPreview.tsx`
   - Show extracted concepts after Phase 1
   - Display as chips/badges grouped by domain
   - Allow user to see what was extracted before mapping

4. ✅ Handle errors gracefully
   - Network errors
   - API errors (invalid text, timeout, etc.)
   - Display user-friendly error messages

### Files to Create
- `frontend/components/ProcessingStatus.tsx` (~150 lines)
- `frontend/components/ExtractedConceptsPreview.tsx` (~100 lines)

### Success Criteria
- ✅ Phase 1 loading state shows correctly
- ✅ Extracted concepts preview displays after Phase 1
- ✅ Phase 2 loading state shows correctly
- ✅ Error messages display clearly
- ✅ User understands current processing stage

---

## Phase 5: Results Table - Core (Day 3)

**Goal:** Build main results table showing all mappings

**Time Estimate:** 4-5 hours

### Tasks

1. ✅ Create `components/ResultsTable.tsx`
   - Table structure with columns:
     - Input concept
     - Domain (with icon)
     - Match info (name, ID, vocab, score)
     - Standard info (name, ID, vocab)
     - Status badge
   - Responsive design (horizontal scroll on mobile)

2. ✅ Create `components/ConceptRow.tsx` for individual rows
   - Display all mapping fields
   - Hover effects for better UX

3. ✅ Create `components/StatusBadge.tsx`
   - Green badge for "OK" status
   - Orange badge for "REVIEW" status
   - Clean, readable design

4. ✅ Create `components/ScoreBar.tsx`
   - Visual score indicator (0-100% bar)
   - Color-coded: green (>90%), yellow (60-90%), red (<60%)

5. ✅ Domain Icons Mapping
   ```typescript
   const domainIcons = {
     Drug: '💊',
     Condition: '🩺',
     Measurement: '🔬',
     Procedure: '⚕️',
     Observation: '👁️',
     Device: '🔧'
   };
   ```

6. ✅ Add sorting capability (by score, domain, status)
7. ✅ Add filtering capability (by domain, status)

### Files to Create
- `frontend/components/ResultsTable.tsx` (~300 lines)
- `frontend/components/ConceptRow.tsx` (~200 lines)
- `frontend/components/StatusBadge.tsx` (~60 lines)
- `frontend/components/ScoreBar.tsx` (~80 lines)

### Success Criteria
- ✅ Table displays all concepts correctly
- ✅ Visual elements (badges, score bars) render beautifully
- ✅ Sorting and filtering work
- ✅ Responsive on different screen sizes
- ✅ Professional medical-grade appearance

---

## Phase 6: Results Table - Details (Day 3)

**Goal:** Add detailed information display

**Time Estimate:** 3-4 hours

### Tasks

1. ✅ Add expandable rows for additional details
   - Click row to expand
   - Show full details (all fields)

2. ✅ Display measurement values + units
   - Highlight value/unit fields when present
   - Example: "500 mg" next to metformin

3. ✅ Display review notes when status = REVIEW
   - Show note field prominently
   - Explain why manual review is needed

4. ✅ Add summary statistics card at top
   ```typescript
   {
     "Total Concepts": stats.total,
     "Mapped Successfully": stats.mapped_ok,
     "Needs Review": stats.needs_review
   }
   ```

5. ✅ Color coding for scores
   - Green: >90% (high confidence)
   - Yellow: 60-90% (medium confidence)
   - Orange: <60% (needs review)

6. ✅ Add tooltips for medical terms
   - SNOMED, RxNorm, LOINC explanations
   - Concept ID explanations

### Files to Modify
- `frontend/components/ResultsTable.tsx` (add summary stats)
- `frontend/components/ConceptRow.tsx` (add expandable detail)

### Files to Create
- `frontend/components/SummaryStats.tsx` (~100 lines)

### Success Criteria
- ✅ All data from JSON visible in UI
- ✅ Color coding helps identify issues
- ✅ Summary stats match backend response
- ✅ Expandable rows work smoothly
- ✅ Tooltips provide helpful context

---

## Phase 7: CSV Export (Day 4)

**Goal:** Implement CSV download functionality

**Time Estimate:** 2-3 hours

### Tasks

1. ✅ Create `lib/csv-export.ts` utility
   ```typescript
   export function generateCSV(mappings: ConceptMapping[]): string {
     const headers = [
       'Input',
       'Domain',
       'Match Name',
       'Match ID',
       'Match Vocabulary',
       'Score',
       'Standard Name',
       'Standard ID',
       'Standard Vocabulary',
       'Status',
       'Note',
       'Value',
       'Unit'
     ];

     const rows = mappings.map(m => [
       m.input,
       m.domain,
       m.match_name,
       m.match_id,
       m.match_vocab,
       m.score,
       m.standard_name,
       m.standard_id,
       m.standard_vocab,
       m.status,
       m.note || '',
       m.value || '',
       m.unit || ''
     ]);

     return [headers, ...rows]
       .map(row => row.map(cell => `"${cell}"`).join(','))
       .join('\n');
   }

   export function downloadCSV(csv: string, filename: string) {
     const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
     const link = document.createElement('a');
     link.href = URL.createObjectURL(blob);
     link.download = filename;
     link.click();
   }
   ```

2. ✅ Create `components/ExportButton.tsx`
   - Button with download icon
   - Generate filename with timestamp
   - Trigger CSV download

3. ✅ Test CSV opens correctly in Excel
   - UTF-8 encoding with BOM
   - Special characters handled
   - All columns visible

### Files to Create
- `frontend/lib/csv-export.ts` (~100 lines)
- `frontend/components/ExportButton.tsx` (~80 lines)

### Success Criteria
- ✅ CSV downloads with correct filename
- ✅ All data included and properly formatted
- ✅ Opens correctly in Excel/Google Sheets
- ✅ Special characters handled (UTF-8 + BOM)

---

## Phase 8: Polish & UX Improvements (Day 4)

**Goal:** Refine UI for professional medical demo

**Time Estimate:** 3-4 hours

### Tasks

1. ✅ Add header with project branding
   - Logo/title: "GraphRAG-OMOP Dashboard"
   - Subtitle: "Clinical Text → OMOP Standardization"

2. ✅ Add footer with version info
   - Version number
   - Credits

3. ✅ Implement keyboard shortcuts
   - Enter to process
   - Esc to clear
   - Document shortcuts in UI

4. ✅ Add smooth animations
   - Fade in/out transitions
   - Smooth scrolling
   - Loading spinner animations

5. ✅ Improve error messages
   - User-friendly language
   - Suggested actions
   - No technical jargon

6. ✅ Add help/info tooltips throughout
   - Explain domains
   - Explain score meaning
   - Explain status badges

7. ✅ Test accessibility
   - Keyboard navigation
   - Screen reader compatibility
   - ARIA labels

8. ✅ Add favicon and page metadata

### Files to Modify
- `frontend/app/layout.tsx` (header/footer, metadata)
- `frontend/app/page.tsx` (keyboard shortcuts)
- All components (polish animations, accessibility)

### Success Criteria
- ✅ UI looks professional and polished
- ✅ Smooth animations enhance UX
- ✅ Keyboard shortcuts work
- ✅ Accessible to all users
- ✅ No obvious bugs or glitches

---

## Phase 9: Testing & Documentation (Day 5)

**Goal:** Comprehensive testing and user documentation

**Time Estimate:** 4-5 hours

### Tasks

**Component Tests (Jest + React Testing Library):**
1. ✅ Create `__tests__/InputSection.test.tsx`
   - Test input handling
   - Test example loading
   - Test process button

2. ✅ Create `__tests__/ResultsTable.test.tsx`
   - Test data rendering
   - Test sorting
   - Test filtering

3. ✅ Create `__tests__/csv-export.test.ts`
   - Test CSV generation
   - Test special characters

**Integration Tests:**
4. ✅ Test API communication (mocked backend)
5. ✅ Test full user flow (input → process → display)

**Documentation:**
6. ✅ Create `frontend/README.md`
   - Setup instructions
   - Running the app
   - Building for production

7. ✅ Create `DASHBOARD_SETUP.md` (root)
   - Complete setup guide (backend + frontend)
   - Prerequisites
   - Installation steps
   - Troubleshooting

8. ✅ Create `DASHBOARD_DEMO_GUIDE.md` (root)
   - Demo script for physicians
   - Example narratives
   - Q&A preparation

### Files to Create
- `frontend/__tests__/InputSection.test.tsx` (~100 lines)
- `frontend/__tests__/ResultsTable.test.tsx` (~120 lines)
- `frontend/__tests__/csv-export.test.ts` (~80 lines)
- `frontend/README.md` (~150 lines)
- `DASHBOARD_SETUP.md` (~250 lines)
- `DASHBOARD_DEMO_GUIDE.md` (~200 lines)

### Success Criteria
- ✅ All tests pass
- ✅ Test coverage >70%
- ✅ Documentation is clear and complete
- ✅ Demo script tested with real users

---

## Phase 10: Final Integration & Demo Prep (Day 5)

**Goal:** Final testing and demo preparation

**Time Estimate:** 2-3 hours

### Tasks

1. ✅ End-to-end testing with all 3 examples
2. ✅ Performance testing (measure load times)
3. ✅ Browser compatibility testing (Chrome, Firefox, Edge)
4. ✅ Create demo checklist
5. ✅ Practice demo run-through
6. ✅ Final polish and bug fixes

### Demo Checklist
- [ ] Backend server starts successfully
- [ ] Frontend dev server starts successfully
- [ ] Grafo loads and status shows "ready"
- [ ] All 3 examples load correctly
- [ ] Processing works for each example (Phase 1 + Phase 2)
- [ ] Results display correctly in table
- [ ] CSV export works
- [ ] No console errors
- [ ] Performance is acceptable (<30s total per query)

### Success Criteria
- ✅ Demo runs smoothly without errors
- ✅ All features work as expected
- ✅ Performance meets requirements
- ✅ Ready for physician demos

---

## 📊 Time Estimates Summary

| Phase | Description | Time | Dependencies |
|-------|-------------|------|--------------|
| 1 | Frontend Foundation | 3-4h | None |
| 2 | Backend Status Check | 2-3h | Phase 1 |
| 3 | Input Section | 2-3h | Phase 1 |
| 4 | Two-Stage Processing | 3-4h | Phase 1-3 |
| 5 | Results Table Core | 4-5h | Phase 1 |
| 6 | Results Table Details | 3-4h | Phase 5 |
| 7 | CSV Export | 2-3h | Phase 5-6 |
| 8 | Polish & UX | 3-4h | All above |
| 9 | Testing & Docs | 4-5h | All above |
| 10 | Final Integration | 2-3h | All above |

**Total Estimated Time:** 28-38 hours (~4-5 days for 1 developer)

---

## 🎨 Design System

### Color Palette (Medical Theme)

**Status Colors:**
- OK (Green): `#10B981` (Tailwind green-500)
- REVIEW (Orange): `#F59E0B` (Tailwind amber-500)
- Error (Red): `#EF4444` (Tailwind red-500)
- Info (Blue): `#3B82F6` (Tailwind blue-500)

**Score Colors:**
- High (>90%): Green `#10B981`
- Medium (60-90%): Yellow `#F59E0B`
- Low (<60%): Red `#EF4444`

**Backgrounds:**
- Page: `#F9FAFB` (gray-50)
- Card: `#FFFFFF` (white)
- Hover: `#F3F4F6` (gray-100)

### Typography
- Heading: text-2xl (24px)
- Subheading: text-lg (18px)
- Body: text-base (16px)
- Small: text-sm (14px)

---

## 🚀 Getting Started

### Frontend Setup

```bash
# Navigate to project root
cd GraphRAG-OMOP

# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --app

# Navigate to frontend
cd frontend

# Install additional deps
npm install react-icons

# Run dev server
npm run dev
```

**Frontend URL:** http://localhost:3000
**Backend URL:** http://localhost:8000

---

## ✅ Success Criteria

### Functional Requirements
- ✅ Frontend connects to backend successfully
- ✅ Backend status monitoring works
- ✅ Two-stage processing (Phase 1 → Phase 2) works seamlessly
- ✅ All 3 examples process correctly
- ✅ Results table displays all mapping details
- ✅ CSV export generates valid files
- ✅ Error states handled gracefully

### User Experience Requirements
- ✅ Interface is intuitive for non-technical physicians
- ✅ Medical terminology is clear
- ✅ Results are visually scannable
- ✅ CSV export is straightforward
- ✅ Professional appearance suitable for demos

### Performance Requirements
- ✅ Frontend loads in <3 seconds
- ✅ Phase 1 processing: <10 seconds
- ✅ Phase 2 processing: <15 seconds (for typical 3-7 concepts)
- ✅ Total user-facing time: 10-30 seconds per analysis

---

## 🔗 Related Documentation

- **Backend Status:** [`backend/PHASE1_COMPLETED.md`](../backend/PHASE1_COMPLETED.md)
- **Original Plan:** [`DASHBOARD_PLAN.md`](DASHBOARD_PLAN.md)
- **Setup Guide:** `DASHBOARD_SETUP.md` (to be created in Phase 9)
- **Demo Guide:** `DASHBOARD_DEMO_GUIDE.md` (to be created in Phase 9)

---

**End of Frontend Plan**
