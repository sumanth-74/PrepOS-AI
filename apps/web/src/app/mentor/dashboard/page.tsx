"use client";

import Link from "next/link";
import { AlertTriangle, ArrowUpRight, Target, Users, Zap } from "lucide-react";

import { SegmentHeatmap } from "@/components/charts/lazy-charts";
import { Button } from "@/components/design-system/button";
import { InsightCard, MetricCard, PremiumCard } from "@/components/design-system/card";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/primitives";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useMentorDashboard, useMentorQueue } from "@/hooks/use-mentor-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";

export default function MentorDashboardPage() {
  const dashboardQuery = useMentorDashboard();
  const queueQuery = useMentorQueue();

  return (
    <>
      <PageHeader
        eyebrow="Mentor Command Center"
        title="Who needs help right now?"
        description="At-risk students, intervention queue, forecast risks, and highest-ROI actions."
      />

      <QueryBoundary
        query={dashboardQuery}
        loadingLabel="Loading command center..."
        emptyTitle="Your command center is activating"
        emptyDescription="Students will appear here once they enter the mentor queue."
        emptyAction={{ label: "View queue", href: "/mentor/queue" }}
      >
        {(data) => (
          <div className="space-y-8">
            <StaggerContainer className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StaggerItem>
                <MetricCard
                  label="Open cases"
                  value={String(data.open_cases)}
                  icon={<Users className="h-5 w-5" />}
                />
              </StaggerItem>
              <StaggerItem>
                <MetricCard
                  label="Critical cases"
                  value={String(data.critical_cases)}
                  trend={data.critical_cases > 0 ? { value: "Immediate action", positive: false } : undefined}
                  icon={<AlertTriangle className="h-5 w-5" />}
                />
              </StaggerItem>
              <StaggerItem>
                <MetricCard label="Effectiveness" value={formatScore(data.mentor_effectiveness_score)} icon={<Target className="h-5 w-5" />} />
              </StaggerItem>
              <StaggerItem>
                <MetricCard label="Avg resolution" value={`${formatScore(data.average_resolution_time_hours)}h`} icon={<Zap className="h-5 w-5" />} />
              </StaggerItem>
            </StaggerContainer>

            <div className="grid gap-6 lg:grid-cols-3">
              <FadeIn className="lg:col-span-2">
                <PremiumCard glow>
                  <h2 className="text-heading-sm">Highest-ROI action</h2>
                  <p className="mt-3 text-xl font-bold text-growth-700 dark:text-growth-400">
                    {formatLabel(data.best_action ?? "Review critical queue")}
                  </p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2 text-sm">
                    <p>Best action ROI: {formatScore(data.best_action_effectiveness)}</p>
                    <p>Average action ROI: {formatScore(data.average_action_effectiveness)}</p>
                  </div>
                  <Link href="/mentor/queue" className="mt-4 inline-block">
                    <Button>Open intervention queue <ArrowUpRight className="h-4 w-4" /></Button>
                  </Link>
                </PremiumCard>
              </FadeIn>

              <FadeIn delay={0.1}>
                <SegmentHeatmap
                  cells={[
                    { label: "Critical", value: data.critical_cases },
                    { label: "Open", value: data.open_cases },
                    { label: "Effectiveness", value: Math.round(Number(data.mentor_effectiveness_score) || 0) },
                    { label: "ROI score", value: Math.round(Number(data.best_action_effectiveness) || 0) },
                  ]}
                />
              </FadeIn>
            </div>

            <QueryBoundary
              query={queueQuery}
              loadingFallback={<div className="skeleton h-48 rounded-2xl" />}
              emptyTitle="No students at risk"
              emptyDescription="Great work — your cohort is stable. Check back after the next assessment cycle."
              emptyAction={{ label: "View cohort", href: "/mentor/cohort" }}
              isEmpty={(items) => items.length === 0}
            >
              {(queue) => (
                <PremiumCard>
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-heading-sm">At-risk students</h2>
                    <Link href="/mentor/queue" className="text-sm text-growth-600 hover:underline">
                      Full queue
                    </Link>
                  </div>
                  <ul className="divide-y divide-border">
                    {queue.slice(0, 6).map((item) => (
                      <li key={item.case_id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                        <div>
                          <Link href={`/mentor/student/${item.student_id}`} className="font-medium text-foreground hover:text-growth-600">
                            Student {item.student_id.slice(0, 8)}…
                          </Link>
                          <p className="text-xs text-foreground-muted">{formatLabel(item.mentor_action)}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <StatusBadge label={formatLabel(item.escalation_level)} tone="warning" />
                          <Link href={`/mentor/student/${item.student_id}`}>
                            <Button variant="secondary" size="sm">Intervene</Button>
                          </Link>
                        </div>
                      </li>
                    ))}
                  </ul>
                </PremiumCard>
              )}
            </QueryBoundary>

            <div className="grid gap-4 sm:grid-cols-2">
              <InsightCard
                title="Forecast risks"
                description="Review students with declining goal probability before milestones slip."
                action={<Link href="/mentor/cohort" className="text-sm font-semibold text-growth-600 hover:underline">Cohort trends →</Link>}
              />
              <InsightCard
                title="Intervention command"
                description="Optimize interventions with highest historical effectiveness for your cohort."
                action={<Link href="/mentor/interventions" className="text-sm font-semibold text-growth-600 hover:underline">Interventions →</Link>}
              />
            </div>
          </div>
        )}
      </QueryBoundary>
    </>
  );
}
