/**
 * BackendStatusBanner Component
 * Monitors backend status and displays loading/ready/error states
 */

"use client";

import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { checkBackendStatus } from "@/lib/api";
import type { BackendStatus } from "@/lib/types";

interface BackendStatusBannerProps {
  onStatusChange?: (status: BackendStatus) => void;
}

export function BackendStatusBanner({ onStatusChange }: BackendStatusBannerProps) {
  const [status, setStatus] = useState<BackendStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    const checkStatus = async () => {
      try {
        const backendStatus = await checkBackendStatus();
        setStatus(backendStatus);
        setError(null);
        onStatusChange?.(backendStatus);

        // Auto-hide banner after 3 seconds when ready
        if (backendStatus.ready && !backendStatus.error) {
          setTimeout(() => setIsVisible(false), 3000);
        }

        // Stop polling when ready or error
        if (backendStatus.ready || backendStatus.error) {
          if (intervalId) clearInterval(intervalId);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Backend is offline");
        setStatus(null);
      }
    };

    // Initial check
    checkStatus();

    // Poll every 2 seconds while loading
    if (!status?.ready) {
      intervalId = setInterval(checkStatus, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [status?.ready, onStatusChange]);

  // Don't show if explicitly hidden and ready
  if (!isVisible && status?.ready) {
    return null;
  }

  // Backend offline
  if (error || !status) {
    return (
      <Alert variant="destructive" className="mb-4">
        <XCircle className="h-4 w-4" />
        <AlertTitle>Backend Offline</AlertTitle>
        <AlertDescription>
          {error || "Cannot connect to backend. Please ensure the server is running on port 8000."}
        </AlertDescription>
      </Alert>
    );
  }

  // Loading grafo
  if (status.grafo_loading) {
    return (
      <Alert className="mb-4 border-blue-200 bg-blue-50">
        <Loader2 className="h-4 w-4 animate-spin" />
        <AlertTitle>System Loading</AlertTitle>
        <AlertDescription>
          Loading OMOP graph and embeddings... This may take up to 30 seconds.
        </AlertDescription>
      </Alert>
    );
  }

  // Error loading
  if (status.error) {
    return (
      <Alert variant="destructive" className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Loading Error</AlertTitle>
        <AlertDescription>{status.error}</AlertDescription>
      </Alert>
    );
  }

  // Ready!
  if (status.ready) {
    return (
      <Alert className="mb-4 border-green-200 bg-green-50">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <AlertTitle className="text-green-800">System Ready</AlertTitle>
        <AlertDescription className="text-green-700">
          All systems operational. You can now process clinical text.
        </AlertDescription>
      </Alert>
    );
  }

  return null;
}
