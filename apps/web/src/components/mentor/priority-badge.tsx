import { StatusBadge } from "@/components/ui/status-badge";
import { formatScore } from "@/lib/utils/format";

interface PriorityBadgeProps {
  priorityScore: string;
}

export function PriorityBadge({ priorityScore }: PriorityBadgeProps) {
  const value = Number(priorityScore);
  let tone: "neutral" | "info" | "warning" | "danger" = "neutral";
  let label = "Low";

  if (value >= 80) {
    tone = "danger";
    label = "Critical";
  } else if (value >= 60) {
    tone = "warning";
    label = "High";
  } else if (value >= 40) {
    tone = "info";
    label = "Medium";
  }

  return (
    <StatusBadge
      label={`${label} · ${formatScore(priorityScore)}`}
      tone={tone}
    />
  );
}
