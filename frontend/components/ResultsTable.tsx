/**
 * ResultsTable Component
 * Main table displaying all OMOP mapping results with sorting and filtering
 */

"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowUpDown, Filter, Download } from "lucide-react";
import { ConceptRow } from "./ConceptRow";
import type { ConceptMapping } from "@/lib/types";
import { exportMappings } from "@/lib/csv-export";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ResultsTableProps {
  mappings: ConceptMapping[];
}

type SortField = "input" | "domain" | "score" | "status";
type SortDirection = "asc" | "desc";

export function ResultsTable({ mappings }: ResultsTableProps) {
  const [sortField, setSortField] = useState<SortField>("score");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [domainFilter, setDomainFilter] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<Set<string>>(new Set());

  // Get unique domains and statuses
  const uniqueDomains = useMemo(() => {
    return Array.from(new Set(mappings.map((m) => m.domain)));
  }, [mappings]);

  const uniqueStatuses = useMemo(() => {
    return Array.from(new Set(mappings.map((m) => m.status)));
  }, [mappings]);

  // Apply filters and sorting
  const filteredAndSortedMappings = useMemo(() => {
    let filtered = [...mappings];

    // Apply domain filter
    if (domainFilter.size > 0) {
      filtered = filtered.filter((m) => domainFilter.has(m.domain));
    }

    // Apply status filter
    if (statusFilter.size > 0) {
      filtered = filtered.filter((m) => statusFilter.has(m.status));
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: string | number = a[sortField] ?? "";
      let bValue: string | number = b[sortField] ?? "";

      if (sortField === "score") {
        aValue = a.score ?? 0;
        bValue = b.score ?? 0;
      } else if (sortField === "input") {
        aValue = a.input.toLowerCase();
        bValue = b.input.toLowerCase();
      } else if (sortField === "domain") {
        aValue = a.domain;
        bValue = b.domain;
      } else if (sortField === "status") {
        aValue = a.status;
        bValue = b.status;
      }

      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [mappings, sortField, sortDirection, domainFilter, statusFilter]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const toggleDomainFilter = (domain: string) => {
    const newFilter = new Set(domainFilter);
    if (newFilter.has(domain)) {
      newFilter.delete(domain);
    } else {
      newFilter.add(domain);
    }
    setDomainFilter(newFilter);
  };

  const toggleStatusFilter = (status: string) => {
    const newFilter = new Set(statusFilter);
    if (newFilter.has(status)) {
      newFilter.delete(status);
    } else {
      newFilter.add(status);
    }
    setStatusFilter(newFilter);
  };

  const handleExport = () => {
    exportMappings(filteredAndSortedMappings);
  };

  if (mappings.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>OMOP Mapping Results</CardTitle>
            <CardDescription>
              {filteredAndSortedMappings.length} of {mappings.length} concept
              {mappings.length !== 1 ? "s" : ""} displayed
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {/* Domain Filter */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Filter className="mr-2 h-4 w-4" />
                  Domain
                  {domainFilter.size > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {domainFilter.size}
                    </Badge>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel>Filter by Domain</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {uniqueDomains.map((domain) => (
                  <DropdownMenuCheckboxItem
                    key={domain}
                    checked={domainFilter.has(domain)}
                    onCheckedChange={() => toggleDomainFilter(domain)}
                  >
                    {domain}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Status Filter */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Filter className="mr-2 h-4 w-4" />
                  Status
                  {statusFilter.size > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {statusFilter.size}
                    </Badge>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {uniqueStatuses.map((status) => (
                  <DropdownMenuCheckboxItem
                    key={status}
                    checked={statusFilter.has(status)}
                    onCheckedChange={() => toggleStatusFilter(status)}
                  >
                    {status}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Export Button */}
            <Button onClick={handleExport} size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8" />
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleSort("input")}
                    className="-ml-3"
                  >
                    Input Concept
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleSort("domain")}
                    className="-ml-3"
                  >
                    Domain
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleSort("score")}
                    className="-ml-3"
                  >
                    Score
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>Standard OMOP Concept</TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleSort("status")}
                    className="-ml-3"
                  >
                    Status
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSortedMappings.map((mapping, index) => (
                <ConceptRow key={index} mapping={mapping} />
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
