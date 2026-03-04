/**
 * SummaryStats Component
 * Displays high-level statistics about the mapping results
 */

"use client";

import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, AlertCircle, FileText } from "lucide-react";

interface SummaryStatsProps {
  total: number;
  mappedOk: number;
  needsReview: number;
}

export function SummaryStats({ total, mappedOk, needsReview }: SummaryStatsProps) {
  const okPercentage = total > 0 ? Math.round((mappedOk / total) * 100) : 0;
  const reviewPercentage = total > 0 ? Math.round((needsReview / total) * 100) : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Total */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Total Concepts
              </p>
              <p className="text-2xl font-bold">{total}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Mapped OK */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Mapped Successfully
              </p>
              <p className="text-2xl font-bold">
                {mappedOk}
                <span className="text-sm font-normal text-muted-foreground ml-2">
                  ({okPercentage}%)
                </span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Needs Review */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertCircle className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Needs Review
              </p>
              <p className="text-2xl font-bold">
                {needsReview}
                <span className="text-sm font-normal text-muted-foreground ml-2">
                  ({reviewPercentage}%)
                </span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
