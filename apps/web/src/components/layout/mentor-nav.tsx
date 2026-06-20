"use client";

import { AppShell } from "@/components/layout/app-shell";

const NAV_ITEMS = [
  { href: "/mentor/dashboard", label: "Dashboard" },
  { href: "/mentor/queue", label: "Queue" },
  { href: "/mentor/interventions", label: "Interventions" },
  { href: "/mentor/cohort", label: "Cohort" },
];

export function MentorShell({ children }: { children: React.ReactNode }) {
  return (
    <AppShell title="Mentor Portal" navItems={NAV_ITEMS}>
      {children}
    </AppShell>
  );
}
