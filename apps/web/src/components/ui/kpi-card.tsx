import { MetricCard } from "@/components/design-system/card";

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "success" | "warning" | "danger";
}

const toneHint: Record<NonNullable<KpiCardProps["tone"]>, string | undefined> = {
  default: undefined,
  success: "↑ Positive trend",
  warning: "Needs attention",
  danger: "Critical",
};

export function KpiCard({ label, value, hint, tone = "default" }: KpiCardProps) {
  const trend =
    tone === "success"
      ? { value: toneHint.success!, positive: true }
      : tone === "warning" || tone === "danger"
        ? { value: toneHint[tone]!, positive: false }
        : undefined;

  return (
    <MetricCard
      label={label}
      value={value}
      hint={hint}
      trend={trend}
    />
  );
}
