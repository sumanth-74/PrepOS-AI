"use client";

import Link from "next/link";
import {
  ArrowUpRight,
  Bot,
  HeartPulse,
  Shield,
  Sparkles,
  Upload,
} from "lucide-react";

import { OpsHealthDashboard } from "@/components/admin/ops-health-dashboard";
import { PlatformMaturityOverview } from "@/components/admin/platform-maturity-dashboard";
import { MiniBarChart } from "@/components/charts/lazy-charts";
import { PremiumCard } from "@/components/design-system/card";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/primitives";
import { PageHeader } from "@/components/ui/page-header";
import { FLAT_NAV } from "@/components/layout/admin-nav";

const QUICK_ACTIONS = [
  {
    href: "/admin/health",
    label: "Platform health",
    description: "Live system status",
    icon: <HeartPulse className="h-5 w-5" />,
  },
  {
    href: "/admin/knowledge",
    label: "Knowledge ops",
    description: "Upload & manage sources",
    icon: <Upload className="h-5 w-5" />,
  },
  {
    href: "/admin/approvals",
    label: "Agent approvals",
    description: "Review pending actions",
    icon: <Bot className="h-5 w-5" />,
  },
  {
    href: "/admin/platform-readiness",
    label: "Readiness score",
    description: "Production maturity",
    icon: <Shield className="h-5 w-5" />,
  },
];

const EXECUTIVE_METRICS = [
  { name: "Student adoption", value: 78 },
  { name: "Agent health", value: 92 },
  { name: "Forecast accuracy", value: 85 },
  { name: "Intervention ROI", value: 88 },
  { name: "Knowledge quality", value: 85 },
  { name: "Security posture", value: 88 },
];

export default function AdminHomePage() {
  return (
    <>
      <PageHeader
        eyebrow="Executive Overview"
        title="Platform command center"
        description="Institution health, AI operations, adoption, and security — at a glance."
      />

      <StaggerContainer className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {QUICK_ACTIONS.map((action) => (
          <StaggerItem key={action.href}>
            <Link href={action.href} className="block h-full">
              <PremiumCard className="group h-full transition-all hover:border-growth-300 hover:shadow-glow">
                <div className="flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-growth-100 text-growth-700 dark:bg-growth-900/50">
                    {action.icon}
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-foreground-subtle transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-growth-600" />
                </div>
                <p className="mt-4 font-semibold text-foreground">{action.label}</p>
                <p className="mt-1 text-sm text-foreground-muted">{action.description}</p>
              </PremiumCard>
            </Link>
          </StaggerItem>
        ))}
      </StaggerContainer>

      <div className="mb-8 grid gap-6 lg:grid-cols-3">
        <FadeIn className="lg:col-span-2">
          <PlatformMaturityOverview />
        </FadeIn>
        <FadeIn delay={0.1}>
          <PremiumCard className="h-full">
            <h2 className="text-heading-sm">Institution pulse</h2>
            <p className="mt-1 text-sm text-foreground-muted">Key platform indicators</p>
            <div className="mt-4">
              <MiniBarChart data={EXECUTIVE_METRICS} />
            </div>
          </PremiumCard>
        </FadeIn>
      </div>

      <FadeIn delay={0.15}>
        <PremiumCard>
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-growth-600" />
            <h2 className="text-heading-sm">Platform health snapshot</h2>
          </div>
          <OpsHealthDashboard />
        </PremiumCard>
      </FadeIn>

      <FadeIn delay={0.2} className="mt-8">
        <PremiumCard>
          <h2 className="text-heading-sm">All admin areas</h2>
          <p className="mt-1 text-sm text-foreground-muted">
            Navigate every operational surface from one place
          </p>
          <ul className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {FLAT_NAV.filter((item) => item.href !== "/admin").map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="flex items-center justify-between rounded-xl border border-border px-3 py-2.5 text-sm text-foreground-muted transition-colors hover:border-growth-300 hover:bg-growth-50/50 hover:text-growth-700 dark:hover:bg-growth-950/30"
                >
                  {item.label}
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </li>
            ))}
          </ul>
        </PremiumCard>
      </FadeIn>
    </>
  );
}
