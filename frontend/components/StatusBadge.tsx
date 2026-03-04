/**
 * StatusBadge Component
 * Displays mapping status (OK or REVIEW) with color coding
 */

import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertCircle } from "lucide-react";

interface StatusBadgeProps {
  status: "OK" | "REVIEW";
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const isOk = status === "OK";

  return (
    <Badge
      variant={isOk ? "default" : "secondary"}
      className={`flex items-center gap-1 ${className}`}
    >
      {isOk ? (
        <>
          <CheckCircle2 className="h-3 w-3" />
          <span>OK</span>
        </>
      ) : (
        <>
          <AlertCircle className="h-3 w-3" />
          <span>REVIEW</span>
        </>
      )}
    </Badge>
  );
}
