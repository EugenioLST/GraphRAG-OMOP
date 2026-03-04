/**
 * ConceptRow Component
 * Individual row in the results table with expandable details
 */

"use client";

import { useState } from "react";
import { TableCell, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { ScoreBar } from "./ScoreBar";
import type { ConceptMapping } from "@/lib/types";
import { DOMAIN_ICONS } from "@/lib/types";

interface ConceptRowProps {
  mapping: ConceptMapping;
}

export function ConceptRow({ mapping }: ConceptRowProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <>
      {/* Main Row */}
      <TableRow className="cursor-pointer hover:bg-muted/50" onClick={() => setIsExpanded(!isExpanded)}>
        <TableCell className="w-8">
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </TableCell>

        <TableCell className="font-medium">
          {mapping.input}
          {mapping.value && mapping.unit && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({mapping.value} {mapping.unit})
            </span>
          )}
        </TableCell>

        <TableCell>
          <Badge variant="outline" className="gap-1">
            <span>{DOMAIN_ICONS[mapping.domain] || "📋"}</span>
            <span>{mapping.domain}</span>
          </Badge>
        </TableCell>

        <TableCell>
          <ScoreBar score={mapping.score} />
        </TableCell>

        <TableCell>
          <div className="space-y-1">
            <p className="font-medium text-sm">{mapping.standard_name}</p>
            <p className="text-xs text-muted-foreground">
              {mapping.standard_vocab} {mapping.standard_id}
            </p>
          </div>
        </TableCell>

        <TableCell>
          <StatusBadge status={mapping.status} />
        </TableCell>
      </TableRow>

      {/* Expanded Details Row */}
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={6} className="bg-muted/30">
            <div className="py-4 px-6 space-y-4">
              <h4 className="font-semibold text-sm">Mapping Details</h4>

              <div className="grid grid-cols-2 gap-4 text-sm">
                {/* Match Information */}
                <div className="space-y-2">
                  <p className="font-medium text-muted-foreground">Best Match</p>
                  <div className="space-y-1">
                    <p><span className="font-medium">Name:</span> {mapping.match_name}</p>
                    <p><span className="font-medium">ID:</span> {mapping.match_id}</p>
                    <p><span className="font-medium">Vocabulary:</span> {mapping.match_vocab}</p>
                    <p><span className="font-medium">Score:</span> {(mapping.score * 100).toFixed(1)}%</p>
                  </div>
                </div>

                {/* Standard Concept */}
                <div className="space-y-2">
                  <p className="font-medium text-muted-foreground">Standard OMOP Concept</p>
                  <div className="space-y-1">
                    <p><span className="font-medium">Name:</span> {mapping.standard_name}</p>
                    <p><span className="font-medium">ID:</span> {mapping.standard_id}</p>
                    <p><span className="font-medium">Vocabulary:</span> {mapping.standard_vocab}</p>
                    <p><span className="font-medium">Domain:</span> {mapping.domain}</p>
                  </div>
                </div>
              </div>

              {/* Review Note */}
              {mapping.note && (
                <div className="pt-2 border-t">
                  <p className="font-medium text-sm text-muted-foreground mb-1">Note</p>
                  <p className="text-sm">{mapping.note}</p>
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
