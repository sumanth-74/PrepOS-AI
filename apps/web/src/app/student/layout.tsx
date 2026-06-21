"use client";

import { usePathname } from "next/navigation";

import { OnboardingGuard } from "@/components/auth/onboarding-guard";
import { RoleGuard } from "@/components/auth/role-guard";
import { StudentShell } from "@/components/layout/student-nav";
import { WorkerStatusBanner } from "@/components/ui/worker-status-banner";

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
        <div className="min-h-screen bg-surface bg-gradient-mesh p-4 sm:p-6">{children}</div>
      ) : (
        <OnboardingGuard>
          <StudentShell>
            <WorkerStatusBanner />
            {children}
          </StudentShell>
        </OnboardingGuard>
      )}
    </RoleGuard>
  );
}
