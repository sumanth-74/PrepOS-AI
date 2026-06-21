import { cn } from "@/lib/utils/cn";

interface PremiumCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  padding?: "sm" | "md" | "lg";
}

const paddingMap = {
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
};

export function PremiumCard({ children, className, glow = false, padding = "md" }: PremiumCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-surface shadow-soft transition-all duration-300 hover:shadow-card",
        glow && "shadow-glow border-growth-200/60 dark:border-growth-800/40",
        paddingMap[padding],
        className,
      )}
    >
      {children}
    </div>
  );
}

interface InsightCardProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  tone?: "default" | "success" | "warning" | "ai";
  className?: string;
}

const toneStyles = {
  default: "border-border",
  success: "border-growth-200 bg-growth-50/50 dark:border-growth-800 dark:bg-growth-950/30",
  warning: "border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/30",
  ai: "border-growth-300/50 bg-gradient-to-br from-growth-50/80 to-emerald-50/50 dark:from-growth-950/40 dark:to-emerald-950/20",
};

export function InsightCard({
  title,
  description,
  icon,
  action,
  tone = "default",
  className,
}: InsightCardProps) {
  return (
    <PremiumCard className={cn(toneStyles[tone], className)}>
      <div className="flex items-start gap-3">
        {icon ? (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-growth-100 text-growth-700 dark:bg-growth-900/50 dark:text-growth-300">
            {icon}
          </div>
        ) : null}
        <div className="min-w-0 flex-1">
          <h3 className="text-heading-sm text-foreground">{title}</h3>
          <p className="mt-1 text-sm text-foreground-muted">{description}</p>
          {action ? <div className="mt-3">{action}</div> : null}
        </div>
      </div>
    </PremiumCard>
  );
}

interface MetricCardProps {
  label: string;
  value: React.ReactNode;
  hint?: string;
  trend?: { value: string; positive?: boolean };
  icon?: React.ReactNode;
  className?: string;
}

export function MetricCard({ label, value, hint, trend, icon, className }: MetricCardProps) {
  return (
    <PremiumCard className={className}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="metric-label">{label}</p>
          <div className="mt-2 metric-value">{value}</div>
          {hint ? <p className="mt-1 text-xs text-foreground-subtle">{hint}</p> : null}
          {trend ? (
            <p
              className={cn(
                "mt-2 text-xs font-medium",
                trend.positive ? "text-growth-600" : "text-amber-600",
              )}
            >
              {trend.positive ? "↑" : "↓"} {trend.value}
            </p>
          ) : null}
        </div>
        {icon ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-surface-raised text-growth-600">
            {icon}
          </div>
        ) : null}
      </div>
    </PremiumCard>
  );
}

interface EmptyStatePremiumProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyStatePremium({ icon, title, description, action }: EmptyStatePremiumProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-surface-raised/50 px-6 py-16 text-center">
      {icon ? (
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-growth-100 text-growth-600 dark:bg-growth-900/40">
          {icon}
        </div>
      ) : null}
      <h3 className="text-heading-sm text-foreground">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-foreground-muted">{description}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}
