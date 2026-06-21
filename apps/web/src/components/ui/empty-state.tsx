import Link from "next/link";
import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/design-system/button";
import { cn } from "@/lib/utils/cn";

export interface EmptyStateAction {
  label: string;
  href: string;
  variant?: "primary" | "secondary";
}

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  primaryAction?: EmptyStateAction;
  secondaryAction?: EmptyStateAction;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  action,
  primaryAction,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[220px] flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-surface-raised/40 px-6 py-12 text-center",
        className,
      )}
    >
      {Icon ? (
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-growth-100 text-growth-600 dark:bg-growth-900/40">
          <Icon className="h-7 w-7" aria-hidden />
        </div>
      ) : null}
      <h3 className="text-heading-sm text-foreground">{title}</h3>
      {description ? (
        <p className="mt-2 max-w-md text-sm text-foreground-muted">{description}</p>
      ) : null}
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        {action}
        {primaryAction ? (
          <Link href={primaryAction.href}>
            <Button variant={primaryAction.variant ?? "primary"}>{primaryAction.label}</Button>
          </Link>
        ) : null}
        {secondaryAction ? (
          <Link href={secondaryAction.href}>
            <Button variant="secondary">{secondaryAction.label}</Button>
          </Link>
        ) : null}
      </div>
    </div>
  );
}
