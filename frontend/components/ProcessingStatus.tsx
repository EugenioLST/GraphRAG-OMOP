/**
 * ProcessingStatus Component
 * Shows current processing stage with progress indication
 */

"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Loader2 } from "lucide-react";
import type { ProcessingStage } from "@/lib/types";

interface ProcessingStatusProps {
  stage: ProcessingStage;
}

const STAGE_INFO = {
  idle: { label: "Ready", progress: 0, description: "" },
  phase1: {
    label: "Stage 1 of 2",
    progress: 25,
    description: "Extracting medical concepts using GPT-4...",
    estimatedTime: "~5-10 seconds",
  },
  phase2: {
    label: "Stage 2 of 2",
    progress: 60,
    description: "Mapping concepts to OMOP standards...",
    estimatedTime: "~5-15 seconds",
  },
  complete: {
    label: "Complete",
    progress: 100,
    description: "Processing completed successfully",
  },
  error: {
    label: "Error",
    progress: 0,
    description: "An error occurred during processing",
  },
};

export function ProcessingStatus({ stage }: ProcessingStatusProps) {
  if (stage === "idle" || stage === "complete") {
    return null;
  }

  const info = STAGE_INFO[stage];

  return (
    <Card className="border-blue-200 bg-blue-50">
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            <div className="flex-1">
              <p className="font-medium text-blue-900">{info.label}</p>
              <p className="text-sm text-blue-700">{info.description}</p>
            </div>
          </div>

          {/* Progress Bar */}
          <Progress value={info.progress} className="h-2" />

          {/* Estimated Time */}
          {"estimatedTime" in info && info.estimatedTime && (
            <p className="text-xs text-blue-600 text-right">
              Estimated time: {info.estimatedTime}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
