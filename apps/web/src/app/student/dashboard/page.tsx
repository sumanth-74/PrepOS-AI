"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  Calendar,
  Compass,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { ReadinessSparkline } from "@/components/charts/lazy-charts";
import { Button } from "@/components/design-system/button";
import { InsightCard, MetricCard, PremiumCard } from "@/components/design-system/card";
import {
  AchievementBadges,
  ExamCountdownCard,
  GamificationStrip,
  LevelProgressBar,
  MotivationBanner,
  WeeklyWinsCard,
} from "@/components/gamification/gamification-ui";
import {
  AnimatedCounter,
  CelebrationBurst,
  ProgressRing,
} from "@/components/motion/metrics";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/primitives";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useStudentContext } from "@/hooks/use-student-context";
import {
  useRecommendations,
  useStudyPlan,
  useTwinDashboard,
} from "@/hooks/use-student-queries";
import { computeStudentGamification } from "@/lib/gamification/student-gamification";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

function MissionControlSkeleton() {
  return (
    <div className="space-y-6">
      <div className="skeleton h-52 rounded-3xl" />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton h-16 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton h-28 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

export default function StudentDashboardPage() {
  const { profile } = useStudentContext();
  const dashboardQuery = useTwinDashboard();
  const recommendationsQuery = useRecommendations();
  const studyPlanQuery = useStudyPlan();
  const [celebrate, setCelebrate] = useState(false);
  const [prevReadiness, setPrevReadiness] = useState<number | null>(null);

  const readinessNum = dashboardQuery.data ? Number(dashboardQuery.data.readiness_score ?? 0) : 0;

  useEffect(() => {
    if (dashboardQuery.data && prevReadiness !== null && readinessNum > prevReadiness) {
      setCelebrate(true);
    }
    if (dashboardQuery.data) setPrevReadiness(readinessNum);
  }, [dashboardQuery.data, readinessNum, prevReadiness]);

  return (
    <QueryBoundary
      query={dashboardQuery}
      loadingFallback={<MissionControlSkeleton />}
      loadingLabel="Loading mission control..."
      emptyTitle="Let's begin your UPSC journey"
      emptyDescription="Complete onboarding to activate your preparation twin and daily missions."
      emptyAction={{ label: "Start onboarding", href: "/student/onboarding" }}
      emptySecondaryAction={{ label: "Learn how PrepOS works", href: "/student/timeline" }}
    >
      {(data) => {
        const gamification = computeStudentGamification(data, profile?.target_year);
        const sparkData = [
          { label: "W-3", value: Math.max(readinessNum - 8, 0) },
          { label: "W-2", value: Math.max(readinessNum - 5, 0) },
          { label: "W-1", value: Math.max(readinessNum - 2, 0) },
          { label: "Now", value: readinessNum },
        ];
        const willClear =
          Number(data.goal_probability ?? 0) >= 55
            ? "On path to clearance"
            : Number(data.goal_probability ?? 0) >= 35
              ? "Building clearance potential"
              : "Focus needed for clearance";

        return (
          <div className="space-y-8">
            {/* 1. Hero + Today's Mission */}
            <FadeIn>
              <PremiumCard glow className="relative overflow-hidden border-growth-200/40 bg-gradient-hero p-0 text-white">
                <CelebrationBurst active={celebrate} onComplete={() => setCelebrate(false)} />
                <div className="relative grid gap-6 p-6 lg:grid-cols-[1fr_auto_auto] lg:p-8">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-widest text-white/80">
                      Mission Control
                    </p>
                    <h1 className="mt-2 text-display-sm text-white">Today&apos;s mission</h1>
                    <p className="mt-2 max-w-lg text-sm text-white/90">
                      {data.today_plan_count > 0
                        ? `Complete ${data.today_plan_count} planned items. ${willClear}.`
                        : "Log a study session to unlock today's personalized missions."}
                    </p>
                    <div className="mt-5 flex flex-wrap gap-3">
                      <Link href="/student/activities">
                        <Button className="bg-white text-growth-700 hover:bg-white/90">
                          Start today&apos;s session
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Link href="/student/study-plan">
                        <Button variant="secondary" className="border-white/30 bg-white/10 text-white hover:bg-white/20">
                          View study plan
                        </Button>
                      </Link>
                    </div>
                  </div>
                  <ProgressRing
                    value={readinessNum}
                    max={100}
                    size={130}
                    strokeWidth={10}
                    label="Readiness"
                    className="mx-auto text-white"
                  />
                  <ExamCountdownCard days={gamification.examCountdownDays} year={gamification.examYear} />
                </div>
              </PremiumCard>
            </FadeIn>

            {/* Gamification strip */}
            <GamificationStrip stats={gamification} />
            <LevelProgressBar stats={gamification} />

            {/* Core metrics */}
            <StaggerContainer className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StaggerItem>
                <MetricCard
                  label="Readiness"
                  value={<AnimatedCounter value={readinessNum} decimals={1} suffix="%" />}
                  trend={{ value: `+${gamification.weeklyReadinessDelta.toFixed(1)} this week`, positive: true }}
                  icon={<TrendingUp className="h-5 w-5" />}
                />
              </StaggerItem>
              <StaggerItem>
                <MetricCard label="Goal probability" value={formatPercent(data.goal_probability)} hint={willClear} icon={<Target className="h-5 w-5" />} />
              </StaggerItem>
              <StaggerItem>
                <MetricCard label="Expected score" value={formatScore(data.expected_score)} hint="Twin projection" icon={<Compass className="h-5 w-5" />} />
              </StaggerItem>
              <StaggerItem>
                <MetricCard
                  label="Today's plan"
                  value={`${data.today_plan_count} / ${data.weekly_plan_count}`}
                  hint={`${formatPercent(data.completion_rate)} completion`}
                  icon={<Calendar className="h-5 w-5" />}
                />
              </StaggerItem>
            </StaggerContainer>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* 2. Readiness trajectory */}
              <FadeIn delay={0.05} className="lg:col-span-2">
                <PremiumCard>
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h2 className="text-heading-sm">Readiness trajectory</h2>
                      <p className="text-sm text-foreground-muted">Am I improving?</p>
                    </div>
                    {data.on_track !== null ? (
                      <StatusBadge label={data.on_track ? "On track" : "Needs focus"} tone={data.on_track ? "success" : "warning"} />
                    ) : null}
                  </div>
                  <ReadinessSparkline data={sparkData} height={150} />
                  <div className="mt-4 grid gap-3 sm:grid-cols-3 text-sm">
                    <div>
                      <p className="text-foreground-muted">Gap to goal</p>
                      <p className="font-semibold">{formatScore(data.gap_to_goal)}</p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Projected readiness</p>
                      <p className="font-semibold">{formatScore(data.projected_readiness)}</p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Risk level</p>
                      <p className="font-semibold">{formatLabel(data.risk_level ?? "moderate")}</p>
                    </div>
                  </div>
                </PremiumCard>
              </FadeIn>

              {/* 3. Weekly progress + wins */}
              <FadeIn delay={0.1} className="space-y-4">
                <WeeklyWinsCard wins={gamification.weeklyWins} />
                <PremiumCard>
                  <h2 className="text-heading-sm">Weekly progress</h2>
                  <p className="mt-2 text-sm text-foreground-muted">{gamification.consistencyLabel}</p>
                  <p className="mt-3 text-2xl font-bold text-foreground">
                    {formatPercent(data.completion_rate)}
                  </p>
                  <p className="text-xs text-foreground-subtle">Plan completion rate</p>
                </PremiumCard>
              </FadeIn>
            </div>

            {/* 4. Focus concepts + 5. Recommended actions */}
            <div className="grid gap-6 lg:grid-cols-2">
              <QueryBoundary
                query={recommendationsQuery}
                loadingFallback={<div className="skeleton h-40 rounded-2xl" />}
                emptyTitle="Unlock focus concepts"
                emptyDescription="Log study activities and complete assessments to receive AI-ranked focus concepts."
                emptyAction={{ label: "Log activity", href: "/student/activities" }}
                emptySecondaryAction={{ label: "View learning graph", href: "/student/learning-graph" }}
                isEmpty={(recs) => recs.length === 0}
              >
                {(recs) => (
                  <PremiumCard>
                    <div className="mb-4 flex items-center justify-between">
                      <h2 className="text-heading-sm">Focus concepts</h2>
                      <Link href="/student/recommendations" className="text-sm text-growth-600 hover:underline">
                        View all
                      </Link>
                    </div>
                    <ul className="space-y-2">
                      {recs.slice(0, 4).map((item, i) => (
                        <li key={item.concept_id} className="flex gap-3 rounded-xl border border-border p-3 hover:border-growth-300">
                          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-growth-100 text-sm font-bold text-growth-700">
                            {i + 1}
                          </span>
                          <div>
                            <p className="font-medium">{item.concept_name}</p>
                            <p className="text-xs text-foreground-muted">
                              Impact {item.impact_score.toFixed(1)} · Gain +{item.estimated_readiness_gain.toFixed(1)}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </PremiumCard>
                )}
              </QueryBoundary>

              <QueryBoundary
                query={studyPlanQuery}
                loadingFallback={<div className="skeleton h-40 rounded-2xl" />}
                emptyTitle="Create your first study plan"
                emptyDescription="Set a goal and complete onboarding — PrepOS will generate a daily mission plan."
                emptyAction={{ label: "Set your goal", href: "/student/goals" }}
                emptySecondaryAction={{ label: "Complete onboarding", href: "/student/onboarding" }}
                isEmpty={(plan) => plan.daily_plan.length === 0}
              >
                {(plan) => (
                  <PremiumCard>
                    <h2 className="text-heading-sm">Recommended actions today</h2>
                    <ul className="mt-3 space-y-2">
                      {plan.daily_plan.slice(0, 5).map((item) => (
                        <li key={`${item.concept_id}-${item.activity_type}`} className="flex justify-between rounded-lg bg-surface-raised px-3 py-2 text-sm">
                          <span className="truncate capitalize text-foreground-muted">
                            {item.activity_type.replace(/_/g, " ")}
                          </span>
                          <span className="shrink-0 font-medium">{item.estimated_minutes}m</span>
                        </li>
                      ))}
                    </ul>
                    <Link href="/student/study-plan" className="mt-3 inline-block text-sm font-semibold text-growth-600 hover:underline">
                      Open full plan →
                    </Link>
                  </PremiumCard>
                )}
              </QueryBoundary>
            </div>

            {/* 6. Copilot insights + 7. Milestones + 8. Achievements + 9. Motivation */}
            <div className="grid gap-6 lg:grid-cols-2">
              <InsightCard
                tone="ai"
                title="Copilot insight"
                description={data.top_mentor_message ?? "Ask Copilot: What should I study next for maximum readiness gain?"}
                icon={<Sparkles className="h-5 w-5" />}
                action={
                  <p className="text-xs text-foreground-muted">
                    Tap the sparkle button — your AI coach knows your twin, goals, and weak areas.
                  </p>
                }
              />
              <PremiumCard>
                <h2 className="text-heading-sm">Upcoming milestones</h2>
                <div className="mt-4 space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-foreground-muted">Next milestone</span>
                    <span className="font-semibold">{data.next_milestone_date ?? "Set a goal"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-foreground-muted">Target readiness</span>
                    <span className="font-semibold">{formatScore(data.next_milestone_target)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-foreground-muted">Status</span>
                    <StatusBadge label={formatLabel(data.milestone_status)} tone={data.on_track ? "success" : "warning"} />
                  </div>
                </div>
              </PremiumCard>
            </div>

            <AchievementBadges badges={gamification.badges} />
            <MotivationBanner readiness={readinessNum} onTrack={data.on_track} />
          </div>
        );
      }}
    </QueryBoundary>
  );
}
