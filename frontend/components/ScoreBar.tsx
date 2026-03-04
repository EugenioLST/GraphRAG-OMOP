/**
 * ScoreBar Component
 * Visual representation of confidence score (0-1)
 */

import { Progress } from "@/components/ui/progress";
import { getScoreColor, getScoreLabel } from "@/lib/types";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ScoreBarProps {
  score: number;
  showLabel?: boolean;
  className?: string;
}

export function ScoreBar({ score, showLabel = true, className }: ScoreBarProps) {
  const percentage = Math.round(score * 100);
  const colorVariant = getScoreColor(score);
  const label = getScoreLabel(score);

  // Color classes based on score
  const progressColor =
    colorVariant === "success"
      ? "[&>div]:bg-green-500"
      : colorVariant === "warning"
      ? "[&>div]:bg-yellow-500"
      : "[&>div]:bg-red-500";

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex-1 min-w-[80px]">
            <Progress
              value={percentage}
              className={`h-2 ${progressColor}`}
            />
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs">{label}</p>
        </TooltipContent>
      </Tooltip>
      {showLabel && (
        <span className="text-sm font-medium tabular-nums w-12 text-right">
          {percentage}%
        </span>
      )}
    </div>
  );
}
