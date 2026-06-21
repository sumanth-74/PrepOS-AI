"use client";

import { PremiumShell } from "@/components/layout/premium-shell";
import { WorkerStatusBanner } from "@/components/ui/worker-status-banner";

const ADMIN_SECTIONS = [
  {
    title: "Overview",
    items: [{ href: "/admin", label: "Dashboard" }],
  },
  {
    title: "Copilot",
    items: [{ href: "/admin/copilot", label: "Copilot analytics" }],
  },
  {
    title: "Knowledge",
    items: [
      { href: "/admin/knowledge", label: "Knowledge ops" },
      { href: "/admin/rag-quality", label: "RAG quality" },
    ],
  },
  {
    title: "Current Affairs",
    items: [{ href: "/admin/current-affairs", label: "Articles" }],
  },
  {
    title: "PYQ",
    items: [{ href: "/admin/pyq", label: "PYQ operations" }],
  },
  {
    title: "Recommendations",
    items: [
      { href: "/admin/recommendations", label: "Analytics" },
      { href: "/admin/recommendation-effectiveness", label: "Effectiveness" },
      { href: "/admin/recommendation-validation", label: "Validation" },
    ],
  },
  {
    title: "Memory",
    items: [{ href: "/admin/memory", label: "Memory dashboard" }],
  },
  {
    title: "Planning",
    items: [{ href: "/admin/planning", label: "Planning ops" }],
  },
  {
    title: "Forecasting",
    items: [
      { href: "/admin/forecasting", label: "Forecasting ops" },
      { href: "/admin/forecast-accuracy", label: "Forecast accuracy" },
    ],
  },
  {
    title: "Interventions",
    items: [{ href: "/admin/interventions", label: "Interventions ops" }],
  },
  {
    title: "Cohorts",
    items: [{ href: "/admin/cohort", label: "Cohort intelligence" }],
  },
  {
    title: "Institution",
    items: [
      { href: "/admin/institution", label: "Institution dashboard" },
      { href: "/admin/institution/outcomes", label: "Outcomes" },
    ],
  },
  {
    title: "Agents",
    items: [{ href: "/admin/agents", label: "Orchestration" }],
  },
  {
    title: "AgentOps",
    items: [
      { href: "/admin/agent-traces", label: "Traces" },
      { href: "/admin/agent-evaluation", label: "Evaluation" },
      { href: "/admin/agent-costs", label: "Costs" },
      { href: "/admin/approvals", label: "Approvals" },
      { href: "/admin/agents/health", label: "Health" },
    ],
  },
  {
    title: "Security",
    items: [
      { href: "/admin/security", label: "Overview" },
      { href: "/admin/security/tenant-audit", label: "Tenant audit" },
      { href: "/admin/security/knowledge", label: "Knowledge security" },
      { href: "/admin/security/rate-limits", label: "Rate limits" },
    ],
  },
  {
    title: "Platform",
    items: [
      { href: "/admin/platform-readiness", label: "Readiness" },
      { href: "/admin/jobs", label: "Jobs" },
      { href: "/admin/evaluations", label: "Evaluations" },
      { href: "/admin/monitoring", label: "Monitoring" },
      { href: "/admin/disaster-recovery", label: "Disaster recovery" },
      { href: "/admin/adoption", label: "Adoption" },
      { href: "/admin/outcomes", label: "Outcomes" },
    ],
  },
  {
    title: "Monitoring",
    items: [{ href: "/admin/health", label: "Platform health" }],
  },
];

const FLAT_NAV = ADMIN_SECTIONS.flatMap((section) => section.items);

export function AdminShell({ children }: { children: React.ReactNode }) {
  return (
    <PremiumShell
      title="Executive Console"
      subtitle="Platform intelligence & operations"
      navSections={ADMIN_SECTIONS}
      showCopilotHint={false}
    >
      <WorkerStatusBanner />
      <div className="mx-auto max-w-7xl">{children}</div>
    </PremiumShell>
  );
}

export { ADMIN_SECTIONS, FLAT_NAV };
