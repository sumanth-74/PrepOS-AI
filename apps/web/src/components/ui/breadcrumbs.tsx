"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LABEL_OVERRIDES: Record<string, string> = {
  admin: "Admin",
  student: "Student",
  mentor: "Mentor",
  faculty: "Faculty",
  "agent-costs": "Agent costs",
  "agent-traces": "Agent traces",
  "agent-evaluation": "Agent evaluation",
  "current-affairs": "Current affairs",
  "platform-readiness": "Platform readiness",
  "rag-quality": "RAG quality",
  "recommendation-effectiveness": "Recommendation effectiveness",
  "forecast-accuracy": "Forecast accuracy",
  "recommendation-validation": "Recommendation validation",
  "disaster-recovery": "Disaster recovery",
  "tenant-audit": "Tenant audit",
  "rate-limits": "Rate limits",
  dashboard: "Dashboard",
  "learning-graph": "Learning Graph",
  "study-plan": "Study Plan",
  "revision-queue": "Revision Queue",
};

function segmentLabel(segment: string): string {
  if (LABEL_OVERRIDES[segment]) return LABEL_OVERRIDES[segment];
  return segment
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function isDynamicSegment(segment: string): boolean {
  return /^[0-9a-f-]{8,}$/i.test(segment) || segment.startsWith("[");
}

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length <= 1) {
    return null;
  }

  const crumbs = segments.map((segment, index) => {
    const href = `/${segments.slice(0, index + 1).join("/")}`;
    const isLast = index === segments.length - 1;
    const linkable = !isLast && !isDynamicSegment(segment);
    return {
      href,
      label: segmentLabel(segment),
      isLast,
      linkable,
    };
  });

  return (
    <nav aria-label="Breadcrumb" className="text-sm text-foreground-muted">
      <ol className="flex flex-wrap items-center gap-1">
        {crumbs.map((crumb) => (
          <li key={crumb.href} className="flex items-center gap-1">
            {crumb.isLast ? (
              <span aria-current="page" className="font-medium text-foreground">
                {crumb.label}
              </span>
            ) : crumb.linkable ? (
              <Link href={crumb.href} className="hover:text-growth-600">
                {crumb.label}
              </Link>
            ) : (
              <span>{crumb.label}</span>
            )}
            {!crumb.isLast ? (
              <span aria-hidden="true" className="text-foreground-subtle">
                /
              </span>
            ) : null}
          </li>
        ))}
      </ol>
    </nav>
  );
}
