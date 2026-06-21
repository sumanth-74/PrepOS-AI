"use client";

import Link from "next/link";
import {
  BookOpen,
  Calendar,
  Map,
  Newspaper,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";

import { SegmentHeatmap } from "@/components/charts/premium-charts";
import { EmptyStatePremium, InsightCard, MetricCard, PremiumCard } from "@/components/design-system/card";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/primitives";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { facultyApi } from "@/lib/api";
import { useAuthStore } from "@/stores";
import { useQuery } from "@tanstack/react-query";

export default function FacultyWorkspacePage() {
  const token = useAuthStore((state) => state.accessToken);
  const workspaceQuery = useQuery({
    queryKey: ["faculty", "workspace"],
    queryFn: () => facultyApi.workspace(token!),
    enabled: Boolean(token),
  });

  const cohortCells = [
    { label: "Active students", value: 124 },
    { label: "At-risk", value: 18 },
    { label: "On track", value: 89 },
    { label: "Needs revision", value: 34 },
  ];

  return (
    <>
      <PageHeader
        eyebrow="Faculty Workspace"
        title="Teaching intelligence center"
        description="Prioritize concepts, plan weekly teaching, and act on PYQ and current affairs signals."
      />

      <QueryBoundary
        query={workspaceQuery}
        loadingFallback={
          <div className="space-y-4">
            <div className="skeleton h-32 rounded-2xl" />
            <div className="grid gap-4 md:grid-cols-2">
              <div className="skeleton h-48 rounded-2xl" />
              <div className="skeleton h-48 rounded-2xl" />
            </div>
          </div>
        }
        loadingLabel="Loading faculty workspace…"
        emptyTitle="Building your teaching insights"
        emptyDescription="Faculty intelligence will populate as cohort activity grows."
        isEmpty={(data) => Object.keys(data).length === 0}
      >
        {(workspace) => (
          <div className="space-y-8">
            <StaggerContainer className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StaggerItem>
                <MetricCard
                  label="Teaching plans"
                  value={String(
                    (workspace.teaching_plans as Record<string, unknown>)?.count ?? "Active",
                  )}
                  icon={<Calendar className="h-5 w-5" />}
                />
              </StaggerItem>
              <StaggerItem>
                <MetricCard
                  label="Weak concepts"
                  value={String(
                    (workspace.weak_concepts as Record<string, unknown>)?.count ?? "—",
                  )}
                  icon={<Target className="h-5 w-5" />}
                />
              </StaggerItem>
              <StaggerItem>
                <MetricCard label="PYQ signals" value="14 trends" icon={<TrendingUp className="h-5 w-5" />} />
              </StaggerItem>
              <StaggerItem>
                <MetricCard label="Cohort size" value="124" icon={<Users className="h-5 w-5" />} />
              </StaggerItem>
            </StaggerContainer>

            <div className="grid gap-6 lg:grid-cols-2">
              <FadeIn>
                <InsightCard
                  tone="ai"
                  title="Teaching priorities this week"
                  description={String(
                    (workspace.teaching_plans as Record<string, unknown>)?.summary ??
                      "Focus on high-frequency PYQ topics with lowest cohort mastery.",
                  )}
                  icon={<BookOpen className="h-5 w-5" />}
                />
              </FadeIn>
              <FadeIn delay={0.1}>
                <InsightCard
                  title="Current affairs signals"
                  description="3 articles mapped to syllabus concepts need classroom discussion."
                  icon={<Newspaper className="h-5 w-5" />}
                  action={
                    <Link href="/admin/current-affairs" className="text-sm font-semibold text-growth-600 hover:underline">
                      Review articles →
                    </Link>
                  }
                />
              </FadeIn>
            </div>

            <FadeIn delay={0.15}>
              <PremiumCard>
                <div className="mb-4 flex items-center gap-2">
                  <Map className="h-5 w-5 text-growth-600" />
                  <h2 className="text-heading-sm">Concept weakness map</h2>
                </div>
                <SegmentHeatmap cells={cohortCells} />
              </PremiumCard>
            </FadeIn>

            <FadeIn delay={0.2}>
              <PremiumCard>
                <h2 className="text-heading-sm">Cohort insights</h2>
                <pre className="mt-3 max-h-64 overflow-auto rounded-xl bg-surface-raised p-4 text-xs text-foreground-muted">
                  {JSON.stringify(workspace.cohort_insights ?? {}, null, 2)}
                </pre>
              </PremiumCard>
            </FadeIn>
          </div>
        )}
      </QueryBoundary>

      {!workspaceQuery.isLoading && workspaceQuery.isError ? (
        <EmptyStatePremium
          title="Unable to load workspace"
          description="Check your connection and try again."
        />
      ) : null}
    </>
  );
}
