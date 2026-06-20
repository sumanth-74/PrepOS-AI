"use client";

import { AppShell } from "@/components/layout/app-shell";

const NAV_ITEMS = [
  { href: "/student/dashboard", label: "Dashboard" },
  { href: "/student/activities", label: "Log Activity" },
  { href: "/student/learning-graph", label: "Learning Graph" },
  { href: "/student/recommendations", label: "Recommendations" },
  { href: "/student/revision-queue", label: "Revision Queue" },
  { href: "/student/study-plan", label: "Study Plan" },
  { href: "/student/planning", label: "Adaptive Planning" },
  { href: "/student/forecasting", label: "Goal Forecasting" },
  { href: "/student/goals", label: "Goals" },
  { href: "/student/forecast", label: "Twin Forecast" },
];

export function StudentShell({ children }: { children: React.ReactNode }) {
  return (
    <AppShell title="Student Portal" navItems={NAV_ITEMS}>
      {children}
    </AppShell>
  );
}
