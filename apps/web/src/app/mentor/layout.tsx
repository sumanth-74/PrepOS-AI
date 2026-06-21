"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { MentorShell } from "@/components/layout/mentor-nav";
import { WorkerStatusBanner } from "@/components/ui/worker-status-banner";

export default function MentorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allowed={["faculty", "institute_admin", "super_admin"]}>
      <MentorShell>
        <WorkerStatusBanner />
        {children}
      </MentorShell>
    </RoleGuard>
  );
}
