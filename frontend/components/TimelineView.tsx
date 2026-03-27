/**
 * TimelineView Component
 * Horizontal patient journey timeline showing clinical events distributed chronologically.
 * Pure CSS/Tailwind — no chart library dependency.
 */

"use client";

import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { ConceptMapping } from "@/lib/types";
import { DOMAIN_ICONS, DOMAIN_COLORS, DOMAIN_DOT_COLORS } from "@/lib/types";

interface TimelineViewProps {
  mappings: ConceptMapping[];
}

interface TimelineEvent {
  mapping: ConceptMapping;
  date: string;
  sortKey: string;
  displayDate: string;
}

interface DateGroup {
  events: TimelineEvent[];
  displayDate: string;
  sortKey: string;
}

// Reason: Dates come in variable granularity (YYYY, YYYY-MM, YYYY-MM-DD).
// We normalize them for sorting while preserving display labels.
function parseTimelineDate(dateStr: string): { sortKey: string; displayDate: string } {
  // Match YYYY only
  if (/^\d{4}$/.test(dateStr)) {
    return { sortKey: `${dateStr}-01-01`, displayDate: dateStr };
  }
  // Match YYYY-MM
  if (/^\d{4}-\d{2}$/.test(dateStr)) {
    const [year, month] = dateStr.split("-");
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return { sortKey: `${dateStr}-01`, displayDate: `${monthNames[parseInt(month) - 1]} ${year}` };
  }
  // Match YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const d = new Date(dateStr + "T00:00:00");
    const formatted = d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
    return { sortKey: dateStr, displayDate: formatted };
  }
  // Fallback
  return { sortKey: dateStr, displayDate: dateStr };
}

export function TimelineView({ mappings }: TimelineViewProps) {
  const { dateGroups, undatedMappings } = useMemo(() => {
    const dated: TimelineEvent[] = [];
    const undated: ConceptMapping[] = [];

    for (const m of mappings) {
      if (m.date) {
        const parsed = parseTimelineDate(m.date);
        dated.push({ mapping: m, date: m.date, ...parsed });
      } else {
        undated.push(m);
      }
    }

    // Group by date string
    const groups = new Map<string, DateGroup>();
    for (const event of dated) {
      const existing = groups.get(event.date);
      if (existing) {
        existing.events.push(event);
      } else {
        groups.set(event.date, {
          events: [event],
          displayDate: event.displayDate,
          sortKey: event.sortKey,
        });
      }
    }

    // Sort groups chronologically
    const sortedGroups = Array.from(groups.entries())
      .sort(([, a], [, b]) => a.sortKey.localeCompare(b.sortKey));

    return { dateGroups: sortedGroups, undatedMappings: undated };
  }, [mappings]);

  // Don't render if no events at all
  if (dateGroups.length === 0 && undatedMappings.length === 0) return null;

  // Collect unique domains present for legend
  const presentDomains = Array.from(new Set(mappings.map((m) => m.domain)));

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Patient Journey Timeline</CardTitle>
        <CardDescription>
          Temporal distribution of clinical events
          {undatedMappings.length > 0 &&
            ` (${undatedMappings.length} event${undatedMappings.length !== 1 ? "s" : ""} without date)`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          {/* Domain Legend */}
          <div className="flex flex-wrap gap-3 mb-6">
            {presentDomains.map((domain) => (
              <div key={domain} className="flex items-center gap-1.5 text-xs">
                <span
                  className={`inline-block w-2.5 h-2.5 rounded-full ${DOMAIN_DOT_COLORS[domain] || "bg-gray-400"}`}
                />
                <span>
                  {DOMAIN_ICONS[domain] || "📋"} {domain}
                </span>
              </div>
            ))}
          </div>

          {/* Timeline */}
          {dateGroups.length > 0 && (
            <div className="overflow-x-auto pb-4">
              <div className="flex items-center min-w-max" style={{ minHeight: "140px" }}>
                {/* Left line start */}
                <div className="w-6 h-px bg-border flex-shrink-0" />

                {dateGroups.map(([dateKey, group], groupIndex) => (
                  <div key={dateKey} className="flex items-center">
                    {/* Connector line between nodes */}
                    {groupIndex > 0 && (
                      <div className="w-16 md:w-24 h-px bg-border flex-shrink-0" />
                    )}

                    {/* Date node */}
                    <div className="flex flex-col items-center flex-shrink-0 px-2">
                      {/* Events stacked above the dot */}
                      <div className="flex flex-col gap-1 mb-2 items-center min-h-[60px] justify-end">
                        {group.events.map((event, eventIndex) => (
                          <Tooltip key={eventIndex}>
                            <TooltipTrigger asChild>
                              <div
                                className={`px-2 py-0.5 rounded-full text-xs font-medium cursor-default border-l-2 ${DOMAIN_COLORS[event.mapping.domain] || "bg-gray-100 text-gray-800"}`}
                                style={{ maxWidth: "180px" }}
                              >
                                <span className="truncate block">
                                  {event.mapping.standard_name || event.mapping.input}
                                </span>
                              </div>
                            </TooltipTrigger>
                            <TooltipContent side="top">
                              <div className="text-xs space-y-1 max-w-xs">
                                <p className="font-semibold">
                                  {DOMAIN_ICONS[event.mapping.domain] || ""} {event.mapping.input}
                                </p>
                                {event.mapping.original_text &&
                                  event.mapping.original_text !== event.mapping.input && (
                                    <p className="text-muted-foreground">
                                      Original: &quot;{event.mapping.original_text}&quot;
                                    </p>
                                  )}
                                {event.mapping.date_original && (
                                  <p className="text-muted-foreground">
                                    Temporal: &quot;{event.mapping.date_original}&quot;
                                  </p>
                                )}
                                <p>
                                  {event.mapping.domain} |{" "}
                                  {event.mapping.standard_vocab || "N/A"} |{" "}
                                  {event.mapping.score !== null
                                    ? `${(event.mapping.score * 100).toFixed(0)}%`
                                    : "N/A"}
                                </p>
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        ))}
                      </div>

                      {/* Dot on the timeline */}
                      <div className="w-3 h-3 rounded-full bg-foreground border-2 border-background z-10 flex-shrink-0" />

                      {/* Date label below */}
                      <div className="mt-2 text-xs text-muted-foreground whitespace-nowrap font-medium">
                        {group.displayDate}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Right arrow end */}
                <div className="w-8 h-px bg-border flex-shrink-0" />
                <div className="w-0 h-0 border-t-4 border-b-4 border-l-8 border-transparent border-l-border flex-shrink-0" />
              </div>
            </div>
          )}

          {/* No dated events message */}
          {dateGroups.length === 0 && (
            <p className="text-sm text-muted-foreground italic mb-4">
              No temporal information detected in the clinical text.
            </p>
          )}

          {/* Undated Events Section */}
          {undatedMappings.length > 0 && (
            <div className={dateGroups.length > 0 ? "mt-4 pt-4 border-t" : ""}>
              <p className="text-sm font-medium text-muted-foreground mb-3">
                Events without date information
              </p>
              <div className="flex flex-wrap gap-2">
                {undatedMappings.map((m, index) => (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      <div>
                        <Badge variant="outline" className="gap-1 cursor-default">
                          <span>{DOMAIN_ICONS[m.domain] || "📋"}</span>
                          <span>{m.standard_name || m.input}</span>
                        </Badge>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      <div className="text-xs space-y-1">
                        <p className="font-semibold">{m.input}</p>
                        <p>{m.domain} | {m.status}</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                ))}
              </div>
            </div>
          )}
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}
