interface StatusBadgeProps {
  label: string;
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
}

const toneClasses: Record<NonNullable<StatusBadgeProps["tone"]>, string> = {
  neutral: "bg-surface-raised text-foreground-muted",
  info: "bg-growth-100 text-growth-800 dark:bg-growth-900/50 dark:text-growth-300",
  success: "bg-growth-100 text-growth-800 dark:bg-growth-900/50 dark:text-growth-300",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300",
  danger: "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300",
};

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${toneClasses[tone]}`}
    >
      {label}
    </span>
  );
}
