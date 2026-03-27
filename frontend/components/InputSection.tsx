/**
 * InputSection Component
 * Clinical text input area with example buttons
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Loader2, FileText, Trash2 } from "lucide-react";

interface InputSectionProps {
  value: string;
  onChange: (value: string) => void;
  onProcess: () => void;
  isProcessing: boolean;
  isDisabled: boolean;
  referenceDate: string;
  onReferenceDateChange: (date: string) => void;
}

const EXAMPLES = [
  {
    name: "Cardiac Case (English)",
    file: "/examples/example1.txt",
    description: "Heart failure with hypertension and diabetes",
  },
  {
    name: "Respiratory Case (Spanish)",
    file: "/examples/example2.txt",
    description: "Sore throat and fatigue - viral infection",
  },
  {
    name: "Diabetes Management (Mixed)",
    file: "/examples/example3.txt",
    description: "Poorly controlled T2DM - treatment adjustment",
  },
];

export function InputSection({
  value,
  onChange,
  onProcess,
  isProcessing,
  isDisabled,
  referenceDate,
  onReferenceDateChange,
}: InputSectionProps) {
  const [loadingExample, setLoadingExample] = useState<number | null>(null);

  const loadExample = async (exampleIndex: number) => {
    setLoadingExample(exampleIndex);
    try {
      const response = await fetch(EXAMPLES[exampleIndex].file);
      const text = await response.text();
      onChange(text);
    } catch (error) {
      console.error("Failed to load example:", error);
    } finally {
      setLoadingExample(null);
    }
  };

  const handleClear = () => {
    onChange("");
  };

  const canProcess = value.trim().length > 0 && !isDisabled && !isProcessing;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Clinical Text Input</CardTitle>
        <CardDescription>
          Enter clinical notes in English or Spanish, or try one of the examples below
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Textarea */}
        <div className="relative">
          <Textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Enter clinical text here... (e.g., 'Patient with diabetes treated with metformin 500mg...')"
            className="min-h-[200px] resize-y"
            disabled={isDisabled || isProcessing}
          />
          <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
            {value.length} characters
          </div>
        </div>

        {/* Reference Date (Optional) */}
        <div className="flex items-center gap-3">
          <label htmlFor="reference-date" className="text-sm font-medium whitespace-nowrap">
            Document date (optional):
          </label>
          <input
            id="reference-date"
            type="date"
            value={referenceDate}
            onChange={(e) => onReferenceDateChange(e.target.value)}
            disabled={isDisabled || isProcessing}
            className="flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          />
          {referenceDate && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onReferenceDateChange("")}
              disabled={isDisabled || isProcessing}
              className="h-8 px-2 text-xs"
            >
              Clear
            </Button>
          )}
          <span className="text-xs text-muted-foreground">
            If empty, auto-detected from text or today&apos;s date
          </span>
        </div>

        {/* Example Buttons */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Pre-loaded Examples:</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {EXAMPLES.map((example, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => loadExample(index)}
                disabled={isDisabled || isProcessing || loadingExample !== null}
                className="justify-start h-auto py-2 px-3"
              >
                {loadingExample === index ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin flex-shrink-0" />
                ) : (
                  <FileText className="mr-2 h-4 w-4 flex-shrink-0" />
                )}
                <div className="text-left">
                  <div className="font-medium text-xs">{example.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {example.description}
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={onProcess}
            disabled={!canProcess}
            className="flex-1"
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              "Process Text"
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleClear}
            disabled={value.length === 0 || isDisabled || isProcessing}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Clear
          </Button>
        </div>

        {isDisabled && (
          <p className="text-sm text-muted-foreground italic">
            Waiting for backend to be ready...
          </p>
        )}
      </CardContent>
    </Card>
  );
}
