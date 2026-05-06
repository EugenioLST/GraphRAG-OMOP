/**
 * Main Dashboard Page
 * GraphRAG-OMOP Clinical Text to OMOP Standardization
 */

"use client";

import { useState, useEffect } from "react";
import { BackendStatusBanner } from "@/components/BackendStatusBanner";
import { InputSection } from "@/components/InputSection";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { ExtractedConceptsPreview } from "@/components/ExtractedConceptsPreview";
import { SummaryStats } from "@/components/SummaryStats";
import { ResultsTable } from "@/components/ResultsTable";
import { TimelineView } from "@/components/TimelineView";
import { Separator } from "@/components/ui/separator";
import { extractConcepts, mapConcepts } from "@/lib/api";
import type {
  BackendStatus,
  ExtractedConcept,
  Phase2Response,
  ProcessingStage,
} from "@/lib/types";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

export default function DashboardPage() {
  // Backend status
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null);

  // Input
  const [inputText, setInputText] = useState("");
  const [referenceDate, setReferenceDate] = useState("");

  // Processing state
  const [processingStage, setProcessingStage] = useState<ProcessingStage>("idle");
  const [error, setError] = useState<string | null>(null);

  // Results
  const [extractedConcepts, setExtractedConcepts] = useState<ExtractedConcept[]>([]);
  const [mappingResults, setMappingResults] = useState<Phase2Response | null>(null);

  const isBackendReady = backendStatus?.ready ?? false;
  const isProcessing = processingStage === "phase1" || processingStage === "phase2";

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Enter: Process text (if conditions met)
      if (e.key === "Enter" && e.ctrlKey && inputText.trim() && isBackendReady && !isProcessing) {
        handleProcess();
      }
      // Escape: Clear input
      if (e.key === "Escape" && inputText.length > 0 && !isProcessing) {
        setInputText("");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [inputText, isBackendReady, isProcessing]);

  const handleProcess = async () => {
    if (!inputText.trim() || !isBackendReady || isProcessing) return;

    // Reset previous results
    setExtractedConcepts([]);
    setMappingResults(null);
    setError(null);

    try {
      // Phase 1: Extract concepts
      setProcessingStage("phase1");
      const phase1Result = await extractConcepts(inputText, referenceDate || undefined);
      setExtractedConcepts(phase1Result.concepts);

      // Short delay to show Phase 1 results
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Phase 2: Map to OMOP
      setProcessingStage("phase2");
      const phase2Result = await mapConcepts(phase1Result.concepts);
      setMappingResults(phase2Result);

      // Complete
      setProcessingStage("complete");
    } catch (err) {
      console.error("Processing error:", err);
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setProcessingStage("error");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                GraphRAG-OMOP Dashboard
              </h1>
              <p className="text-muted-foreground mt-1">
                Clinical Text → OMOP Standardization using Semantic Search
              </p>
            </div>
            <div className="text-right text-sm text-muted-foreground">
              <p>Powered by LLM + SapBERT</p>
              <p>OMOP CDM v5.4</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Keyboard Shortcuts Hint */}
          <div className="text-xs text-muted-foreground text-right">
            <span className="inline-flex items-center gap-1">
              💡 <kbd className="px-1.5 py-0.5 rounded bg-muted">Ctrl+Enter</kbd> to process,{" "}
              <kbd className="px-1.5 py-0.5 rounded bg-muted">Esc</kbd> to clear
            </span>
          </div>
          {/* Backend Status Banner */}
          <BackendStatusBanner onStatusChange={setBackendStatus} />

          {/* Input Section */}
          <InputSection
            value={inputText}
            onChange={setInputText}
            onProcess={handleProcess}
            isProcessing={isProcessing}
            isDisabled={!isBackendReady}
            referenceDate={referenceDate}
            onReferenceDateChange={setReferenceDate}
          />

          {/* Processing Status */}
          {(processingStage === "phase1" || processingStage === "phase2") && (
            <ProcessingStatus stage={processingStage} />
          )}

          {/* Error Display */}
          {processingStage === "error" && error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Processing Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Extracted Concepts Preview (after Phase 1) */}
          {extractedConcepts.length > 0 && (
            <>
              <Separator className="my-8" />
              <ExtractedConceptsPreview concepts={extractedConcepts} />
            </>
          )}

          {/* Results Section (after Phase 2) */}
          {mappingResults && (
            <>
              <Separator className="my-8" />

              {/* Summary Stats */}
              <SummaryStats
                total={mappingResults.stats.total}
                mappedOk={mappingResults.stats.mapped_ok}
                needsReview={mappingResults.stats.needs_review}
              />

              {/* Patient Journey Timeline */}
              <TimelineView mappings={mappingResults.mappings} />

              {/* Results Table */}
              <ResultsTable mappings={mappingResults.mappings} />
            </>
          )}

          {/* Empty State */}
          {processingStage === "idle" && !mappingResults && (
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-lg">
                Enter clinical text above or load an example to begin
              </p>
              <p className="text-sm mt-2">
                The system will extract medical concepts and map them to OMOP standards
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-12 py-6 text-center text-sm text-muted-foreground">
        <div className="container mx-auto px-4">
          <p>GraphRAG-OMOP Dashboard v1.0 | Built with Next.js + shadcn/ui</p>
          <p className="mt-1">
            Using SNOMED CT, RxNorm, LOINC, and other OMOP vocabularies
          </p>
        </div>
      </footer>
    </div>
  );
}
