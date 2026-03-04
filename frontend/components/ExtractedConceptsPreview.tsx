/**
 * ExtractedConceptsPreview Component
 * Shows extracted concepts after Phase 1, before OMOP mapping
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { ExtractedConcept } from "@/lib/types";
import { DOMAIN_ICONS } from "@/lib/types";

interface ExtractedConceptsPreviewProps {
  concepts: ExtractedConcept[];
}

export function ExtractedConceptsPreview({ concepts }: ExtractedConceptsPreviewProps) {
  if (concepts.length === 0) return null;

  // Group by domain
  const grouped = concepts.reduce((acc, concept) => {
    if (!acc[concept.domain]) {
      acc[concept.domain] = [];
    }
    acc[concept.domain].push(concept);
    return acc;
  }, {} as Record<string, ExtractedConcept[]>);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Extracted Concepts</CardTitle>
        <CardDescription>
          {concepts.length} medical concept{concepts.length !== 1 ? "s" : ""} identified from the clinical text
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {Object.entries(grouped).map(([domain, domainConcepts]) => (
            <div key={domain}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{DOMAIN_ICONS[domain] || "📋"}</span>
                <span className="font-medium text-sm">{domain}</span>
                <Badge variant="secondary" className="ml-auto">
                  {domainConcepts.length}
                </Badge>
              </div>
              <div className="flex flex-wrap gap-2">
                {domainConcepts.map((concept, idx) => (
                  <Badge key={idx} variant="outline" className="px-3 py-1">
                    {concept.text}
                    {concept.value && concept.unit && (
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({concept.value} {concept.unit})
                      </span>
                    )}
                  </Badge>
                ))}
              </div>
              {Object.keys(grouped).indexOf(domain) < Object.keys(grouped).length - 1 && (
                <Separator className="mt-4" />
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
