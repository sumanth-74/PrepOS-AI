"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { StudentShell } from "@/components/layout/student-nav";

export default function StudentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allowed={["student"]}>
      <StudentShell>{children}</StudentShell>
    </RoleGuard>
  );
}
