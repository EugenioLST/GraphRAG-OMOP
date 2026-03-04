/**
 * API Client for GraphRAG-OMOP Backend
 * Connects to FastAPI backend at http://localhost:8000
 */

import type {
  BackendStatus,
  HealthResponse,
  Phase1Request,
  Phase1Response,
  Phase2Request,
  Phase2Response,
  ExtractedConcept,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// Error Handling
// ============================================================================

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `API Error: ${response.statusText}`,
      response.status,
      errorData
    );
  }
  return response.json();
}

// ============================================================================
// Health & Status Endpoints
// ============================================================================

/**
 * Check if backend is running
 * GET /health
 */
export async function checkHealth(): Promise<HealthResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    return handleResponse<HealthResponse>(response);
  } catch (error) {
    console.error("Health check failed:", error);
    throw new ApiError("Backend is not available. Please ensure the server is running.");
  }
}

/**
 * Check if grafo is loaded and system is ready
 * GET /status
 */
export async function checkBackendStatus(): Promise<BackendStatus> {
  const response = await fetch(`${API_BASE_URL}/status`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  return handleResponse<BackendStatus>(response);
}

// ============================================================================
// Phase 1: Concept Extraction
// ============================================================================

/**
 * Extract medical concepts from clinical text using GPT-4
 * POST /phase1
 *
 * @param text - Clinical text in any language
 * @returns Extracted concepts with domains
 */
export async function extractConcepts(text: string): Promise<Phase1Response> {
  if (!text || text.trim().length === 0) {
    throw new ApiError("Clinical text cannot be empty");
  }

  const request: Phase1Request = { text };

  const response = await fetch(`${API_BASE_URL}/phase1`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  return handleResponse<Phase1Response>(response);
}

// ============================================================================
// Phase 2: OMOP Mapping
// ============================================================================

/**
 * Map extracted concepts to OMOP standard concepts
 * POST /phase2
 *
 * @param concepts - Concepts extracted from Phase 1
 * @returns Mappings to OMOP standards with scores
 */
export async function mapConcepts(concepts: ExtractedConcept[]): Promise<Phase2Response> {
  if (!concepts || concepts.length === 0) {
    throw new ApiError("No concepts to map");
  }

  const request: Phase2Request = { concepts };

  const response = await fetch(`${API_BASE_URL}/phase2`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  return handleResponse<Phase2Response>(response);
}

// ============================================================================
// Combined Processing
// ============================================================================

/**
 * Process clinical text through both phases
 * Convenience function that calls Phase 1 → Phase 2
 *
 * @param text - Clinical text
 * @returns Final mappings to OMOP standards
 */
export async function processText(text: string): Promise<{
  phase1: Phase1Response;
  phase2: Phase2Response;
}> {
  // Phase 1: Extract concepts
  const phase1 = await extractConcepts(text);

  // Phase 2: Map to OMOP
  const phase2 = await mapConcepts(phase1.concepts);

  return { phase1, phase2 };
}

// ============================================================================
// Polling Helper
// ============================================================================

/**
 * Poll backend status until grafo is loaded
 *
 * @param onUpdate - Callback for status updates
 * @param interval - Polling interval in ms (default: 2000)
 * @param maxAttempts - Maximum polling attempts (default: 30)
 */
export async function pollUntilReady(
  onUpdate?: (status: BackendStatus) => void,
  interval: number = 2000,
  maxAttempts: number = 30
): Promise<BackendStatus> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const status = await checkBackendStatus();
    onUpdate?.(status);

    if (status.ready) {
      return status;
    }

    if (status.error) {
      throw new ApiError(`Backend error: ${status.error}`);
    }

    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  throw new ApiError("Backend failed to load within timeout period");
}
