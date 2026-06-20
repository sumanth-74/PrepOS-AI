"use client";

import { usePathname } from "next/navigation";

import { OnboardingGuard } from "@/components/auth/onboarding-guard";
import { RoleGuard } from "@/components/auth/role-guard";
import { StudentShell } from "@/components/layout/student-nav";

export default function StudentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isOnboarding = pathname.startsWith("/student/onboarding");

  return (
    <RoleGuard allowed={["student"]}>
      {isOnboarding ? (
        <div className="min-h-screen bg-slate-50 p-4 sm:p-6">{children}</div>
      ) : (
        <OnboardingGuard>
          <StudentShell>{children}</StudentShell>
        </OnboardingGuard>
      )}
    </RoleGuard>
  );
}
