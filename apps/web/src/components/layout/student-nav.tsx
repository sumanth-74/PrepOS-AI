"use client";

import {
  Activity,
  BarChart3,
  BookOpen,
  Calendar,
  Compass,
  GitBranch,
  LayoutDashboard,
  ListTodo,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { PremiumShell, type NavSection } from "@/components/layout/premium-shell";

const STUDENT_NAV: NavSection[] = [
  {
    title: "Mission Control",
    items: [
      { href: "/student/dashboard", label: "Dashboard", icon: <LayoutDashboard className="h-4 w-4" /> },
      { href: "/student/timeline", label: "Learning Timeline", icon: <Activity className="h-4 w-4" /> },
    ],
  },
  {
    title: "Learning",
    items: [
      { href: "/student/activities", label: "Log Activity", icon: <BookOpen className="h-4 w-4" /> },
      { href: "/student/learning-graph", label: "Learning Graph", icon: <GitBranch className="h-4 w-4" /> },
      { href: "/student/revision-queue", label: "Revision Queue", icon: <ListTodo className="h-4 w-4" /> },
      { href: "/student/study-plan", label: "Study Plan", icon: <Calendar className="h-4 w-4" /> },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { href: "/student/recommendations", label: "Recommendations", icon: <Sparkles className="h-4 w-4" /> },
      { href: "/student/planning", label: "Adaptive Planning", icon: <Compass className="h-4 w-4" /> },
      { href: "/student/forecasting", label: "Goal Forecasting", icon: <TrendingUp className="h-4 w-4" /> },
      { href: "/student/goals", label: "Goals", icon: <Target className="h-4 w-4" /> },
      { href: "/student/forecast", label: "Twin Forecast", icon: <BarChart3 className="h-4 w-4" /> },
    ],
  },
];

export function StudentShell({ children }: { children: React.ReactNode }) {
  return (
    <PremiumShell
      title="Student Companion"
      subtitle="Your path to UPSC success"
      navSections={STUDENT_NAV}
    >
      {children}
    </PremiumShell>
  );
}
