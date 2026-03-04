/**
 * TypeScript interfaces for GraphRAG-OMOP Dashboard
 * Based on backend API response schemas
 */

// ============================================================================
// Phase 1: Concept Extraction Types
// ============================================================================

export interface ExtractedConcept {
  text: string;
  domain: string;
  value: number | null;
  unit: string | null;
}

export interface Phase1Request {
  text: string;
}

export interface Phase1Response {
  concepts: ExtractedConcept[];
}

// ============================================================================
// Phase 2: OMOP Mapping Types
// ============================================================================

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

export interface Phase2Request {
  concepts: ExtractedConcept[];
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

// ============================================================================
// Backend Status Types
// ============================================================================

export interface BackendStatus {
  grafo_loaded: boolean;
  grafo_loading: boolean;
  ready: boolean;
  error: string | null;
}

export interface HealthResponse {
  status: "ok" | "error";
}

// ============================================================================
// UI State Types
// ============================================================================

export type ProcessingStage = "idle" | "phase1" | "phase2" | "complete" | "error";

export interface ProcessingState {
  stage: ProcessingStage;
  error: string | null;
}

// ============================================================================
// Domain Icons Mapping
// ============================================================================

export const DOMAIN_ICONS: Record<string, string> = {
  Drug: "💊",
  Condition: "🩺",
  Measurement: "🔬",
  Procedure: "⚕️",
  Observation: "👁️",
  Device: "🔧",
};

export const DOMAIN_COLORS: Record<string, string> = {
  Drug: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  Condition: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  Measurement: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  Procedure: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  Observation: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  Device: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
};

// ============================================================================
// Helper Functions
// ============================================================================

export function getScoreColor(score: number): "success" | "warning" | "destructive" {
  if (score >= 0.9) return "success";
  if (score >= 0.6) return "warning";
  return "destructive";
}

export function getScoreLabel(score: number): string {
  if (score >= 0.9) return "High confidence";
  if (score >= 0.6) return "Medium confidence";
  return "Low confidence - needs review";
}
