/**
 * CSV Export Utility
 * Generates CSV files from OMOP mapping results
 */

import type { ConceptMapping } from "./types";

/**
 * Convert array of objects to CSV string
 */
export function generateCSV(mappings: ConceptMapping[]): string {
  if (mappings.length === 0) {
    return "";
  }

  // CSV Headers
  const headers = [
    "Input",
    "Domain",
    "Match Name",
    "Match ID",
    "Match Vocabulary",
    "Score",
    "Standard Name",
    "Standard ID",
    "Standard Vocabulary",
    "Status",
    "Note",
    "Value",
    "Unit",
  ];

  // CSV Rows
  const rows = mappings.map((m) => [
    escapeCSV(m.input),
    escapeCSV(m.domain),
    escapeCSV(m.match_name),
    m.match_id.toString(),
    escapeCSV(m.match_vocab),
    m.score.toFixed(3),
    escapeCSV(m.standard_name),
    m.standard_id.toString(),
    escapeCSV(m.standard_vocab),
    escapeCSV(m.status),
    escapeCSV(m.note || ""),
    m.value?.toString() || "",
    escapeCSV(m.unit || ""),
  ]);

  // Combine headers and rows
  const csvContent = [headers, ...rows]
    .map((row) => row.join(","))
    .join("\n");

  return csvContent;
}

/**
 * Escape special characters for CSV format
 */
function escapeCSV(value: string): string {
  if (!value) return "";

  // If value contains comma, newline, or quote, wrap in quotes and escape quotes
  if (value.includes(",") || value.includes("\n") || value.includes('"')) {
    return `"${value.replace(/"/g, '""')}"`;
  }

  return value;
}

/**
 * Download CSV file to user's computer
 */
export function downloadCSV(csv: string, filename: string): void {
  // Add BOM for Excel UTF-8 support
  const BOM = "\uFEFF";
  const csvWithBOM = BOM + csv;

  // Create blob
  const blob = new Blob([csvWithBOM], {
    type: "text/csv;charset=utf-8;",
  });

  // Create download link
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";

  // Trigger download
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Cleanup
  URL.revokeObjectURL(url);
}

/**
 * Generate filename with timestamp
 */
export function generateFilename(prefix: string = "omop-mappings"): string {
  const now = new Date();
  const timestamp = now
    .toISOString()
    .replace(/:/g, "-")
    .replace(/\..+/, "");
  return `${prefix}-${timestamp}.csv`;
}

/**
 * Export mappings to CSV file
 * Convenience function that combines all steps
 */
export function exportMappings(
  mappings: ConceptMapping[],
  filename?: string
): void {
  if (mappings.length === 0) {
    console.warn("No mappings to export");
    return;
  }

  const csv = generateCSV(mappings);
  const finalFilename = filename || generateFilename();
  downloadCSV(csv, finalFilename);
}
