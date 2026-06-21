import type { TwinDashboardResponse } from "@/lib/types/api";

export interface StudentGamification {
  xp: number;
  level: number;
  xpToNextLevel: number;
  xpProgress: number;
  streakDays: number;
  momentumScore: number;
  weeklyReadinessDelta: number;
  badges: GamificationBadge[];
  weeklyWins: string[];
  examCountdownDays: number | null;
  examYear: number | null;
  consistencyLabel: string;
}

export interface GamificationBadge {
  id: string;
  emoji: string;
  title: string;
  description: string;
  unlocked: boolean;
}

function num(value: string | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function daysUntilExam(targetYear: number | null | undefined): number | null {
  if (!targetYear) return null;
  const examDate = new Date(`${targetYear}-05-31T00:00:00`);
  const now = new Date();
  const diff = examDate.getTime() - now.getTime();
  if (diff <= 0) return 0;
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

export function computeStudentGamification(
  dashboard: TwinDashboardResponse,
  targetYear?: number | null,
): StudentGamification {
  const readiness = num(dashboard.readiness_score);
  const completion = num(dashboard.completion_rate);
  const consistency = num(dashboard.consistency_score);
  const todayItems = dashboard.today_plan_count ?? 0;
  const weeklyItems = dashboard.weekly_plan_count ?? 0;

  const xp = Math.round(
    readiness * 12 + completion * 8 + consistency * 5 + todayItems * 40 + weeklyItems * 15,
  );
  const level = Math.max(1, Math.floor(xp / 800) + 1);
  const levelBase = (level - 1) * 800;
  const xpInLevel = xp - levelBase;
  const xpToNextLevel = 800 - xpInLevel;
  const xpProgress = Math.min(100, Math.round((xpInLevel / 800) * 100));

  const streakDays = Math.max(1, Math.round(consistency / 10) || Math.round(completion / 15) || 1);
  const weeklyDelta = num(dashboard.expected_weekly_progress) || Math.min(4.2, readiness * 0.05);
  const momentumScore = Math.min(
    100,
    Math.round(consistency * 0.4 + completion * 0.35 + readiness * 0.25),
  );

  const badges: GamificationBadge[] = [
    {
      id: "on-track",
      emoji: "🎯",
      title: "On Track",
      description: "Milestone trajectory aligned with your goal",
      unlocked: dashboard.on_track === true,
    },
    {
      id: "momentum",
      emoji: "🚀",
      title: "Momentum Builder",
      description: `Readiness +${weeklyDelta.toFixed(1)} projected this week`,
      unlocked: weeklyDelta >= 2,
    },
    {
      id: "consistency",
      emoji: "🔥",
      title: `${streakDays}-Day Streak`,
      description: "Consistent daily preparation rhythm",
      unlocked: streakDays >= 7,
    },
    {
      id: "high-performer",
      emoji: "⭐",
      title: "Top Performer",
      description: "Readiness in top aspirant tier",
      unlocked: readiness >= 65,
    },
    {
      id: "goal-clear",
      emoji: "🏆",
      title: "Clearance Path",
      description: "Goal probability above confidence threshold",
      unlocked: num(dashboard.goal_probability) >= 60,
    },
  ];

  const weeklyWins: string[] = [];
  if (completion >= 50) weeklyWins.push(`${Math.round(completion)}% plan completion`);
  if (todayItems > 0) weeklyWins.push(`${todayItems} missions scheduled today`);
  if (num(dashboard.goal_probability) > 0) {
    weeklyWins.push(`${num(dashboard.goal_probability).toFixed(0)}% goal probability`);
  }
  if (dashboard.recommendation_count > 0) {
    weeklyWins.push(`${dashboard.recommendation_count} AI recommendations active`);
  }

  return {
    xp,
    level,
    xpToNextLevel,
    xpProgress,
    streakDays,
    momentumScore,
    weeklyReadinessDelta: weeklyDelta,
    badges,
    weeklyWins,
    examCountdownDays: daysUntilExam(targetYear),
    examYear: targetYear ?? null,
    consistencyLabel:
      consistency >= 70 ? "Highly consistent" : consistency >= 40 ? "Building rhythm" : "Needs consistency",
  };
}
