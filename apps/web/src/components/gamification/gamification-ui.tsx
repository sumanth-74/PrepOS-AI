"use client";

import { motion } from "framer-motion";
import { Flame, Rocket, Star, Trophy, Zap } from "lucide-react";

import type { GamificationBadge, StudentGamification } from "@/lib/gamification/student-gamification";
import { cn } from "@/lib/utils/cn";
import { PremiumCard } from "@/components/design-system/card";

export function GamificationStrip({ stats }: { stats: StudentGamification }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <StatPill icon={<Flame className="h-4 w-4 text-orange-500" />} label="Streak" value={`${stats.streakDays} days`} />
      <StatPill icon={<Zap className="h-4 w-4 text-growth-500" />} label="Level" value={`L${stats.level}`} sub={`${stats.xp} XP`} />
      <StatPill icon={<Rocket className="h-4 w-4 text-blue-500" />} label="Momentum" value={`${stats.momentumScore}`} sub="score" />
      <StatPill
        icon={<Star className="h-4 w-4 text-amber-500" />}
        label="This week"
        value={`+${stats.weeklyReadinessDelta.toFixed(1)}`}
        sub="readiness"
      />
    </div>
  );
}

function StatPill({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3 shadow-soft">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface-raised">{icon}</div>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground-subtle">{label}</p>
        <p className="text-sm font-bold text-foreground">
          {value}
          {sub ? <span className="ml-1 text-xs font-normal text-foreground-muted">{sub}</span> : null}
        </p>
      </div>
    </div>
  );
}

export function LevelProgressBar({ stats }: { stats: StudentGamification }) {
  return (
    <PremiumCard padding="sm" className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-semibold text-foreground">Level {stats.level}</span>
        <span className="text-foreground-muted">{stats.xpToNextLevel} XP to next level</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-raised">
        <motion.div
          className="h-full rounded-full bg-gradient-growth"
          initial={{ width: 0 }}
          animate={{ width: `${stats.xpProgress}%` }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
    </PremiumCard>
  );
}

export function AchievementBadges({ badges }: { badges: GamificationBadge[] }) {
  const unlocked = badges.filter((b) => b.unlocked);
  const locked = badges.filter((b) => !b.unlocked);

  return (
    <PremiumCard>
      <div className="mb-4 flex items-center gap-2">
        <Trophy className="h-5 w-5 text-growth-600" />
        <h2 className="text-heading-sm">Achievements</h2>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {unlocked.map((badge) => (
          <BadgeCard key={badge.id} badge={badge} />
        ))}
        {locked.slice(0, Math.max(0, 4 - unlocked.length)).map((badge) => (
          <BadgeCard key={badge.id} badge={badge} muted />
        ))}
      </div>
    </PremiumCard>
  );
}

function BadgeCard({ badge, muted = false }: { badge: GamificationBadge; muted?: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "rounded-xl border p-3",
        muted
          ? "border-border bg-surface-raised/50 opacity-60"
          : "border-growth-200 bg-growth-50/50 dark:border-growth-800 dark:bg-growth-950/30",
      )}
    >
      <p className="text-lg">{badge.emoji}</p>
      <p className="mt-1 text-sm font-semibold text-foreground">{badge.title}</p>
      <p className="text-xs text-foreground-muted">{badge.description}</p>
    </motion.div>
  );
}

export function WeeklyWinsCard({ wins }: { wins: string[] }) {
  if (wins.length === 0) return null;
  return (
    <PremiumCard className="border-growth-200/50 bg-growth-50/30 dark:border-growth-800/40 dark:bg-growth-950/20">
      <h2 className="text-heading-sm">Weekly wins</h2>
      <ul className="mt-3 space-y-2">
        {wins.map((win) => (
          <li key={win} className="flex items-center gap-2 text-sm text-foreground">
            <span className="text-growth-600">✓</span>
            {win}
          </li>
        ))}
      </ul>
    </PremiumCard>
  );
}

export function ExamCountdownCard({ days, year }: { days: number | null; year: number | null }) {
  if (days === null) return null;
  return (
    <PremiumCard glow className="text-center">
      <p className="text-caption uppercase tracking-widest text-foreground-muted">Exam countdown</p>
      <p className="mt-2 text-display-sm font-bold text-foreground">{days}</p>
      <p className="text-sm text-foreground-muted">days until {year ?? "target"} attempt</p>
      <p className="mt-3 text-xs text-growth-700 dark:text-growth-400">
        {days > 180 ? "Build depth systematically" : days > 60 ? "Intensify revision cycles" : "Final sprint mode"}
      </p>
    </PremiumCard>
  );
}

export function MotivationBanner({ readiness, onTrack }: { readiness: number; onTrack: boolean | null }) {
  const message = onTrack
    ? "You're on track. Stay consistent — clearance is a compound effect."
    : readiness >= 50
      ? "Strong foundation. Focus on weak concepts for the next breakthrough."
      : "Every session counts. Small daily wins lead to exam success.";

  return (
    <div className="rounded-2xl border border-growth-200/60 bg-gradient-to-r from-growth-50 to-emerald-50 px-5 py-4 dark:border-growth-800/40 dark:from-growth-950/40 dark:to-emerald-950/20">
      <p className="text-sm font-medium text-growth-800 dark:text-growth-300">{message}</p>
    </div>
  );
}
