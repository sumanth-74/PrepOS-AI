"use client";

import {
  GraduationCap,
  LayoutDashboard,
  ListChecks,
  Users,
  Zap,
} from "lucide-react";

import { PremiumShell, type NavSection } from "@/components/layout/premium-shell";

const MENTOR_NAV: NavSection[] = [
  {
    title: "Command Center",
    items: [
      { href: "/mentor/dashboard", label: "Dashboard", icon: <LayoutDashboard className="h-4 w-4" /> },
      { href: "/mentor/queue", label: "Student Queue", icon: <ListChecks className="h-4 w-4" /> },
    ],
  },
  {
    title: "Interventions",
    items: [
      { href: "/mentor/interventions", label: "Interventions", icon: <Zap className="h-4 w-4" /> },
      { href: "/mentor/cohort", label: "Cohort Intelligence", icon: <Users className="h-4 w-4" /> },
    ],
  },
  {
    title: "Faculty",
    items: [
      { href: "/faculty", label: "Faculty Workspace", icon: <GraduationCap className="h-4 w-4" /> },
    ],
  },
];

export function MentorShell({ children }: { children: React.ReactNode }) {
  return (
    <PremiumShell title="Mentor Command" subtitle="Guide every aspirant to success" navSections={MENTOR_NAV}>
      {children}
    </PremiumShell>
  );
}
