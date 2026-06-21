"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { AdminShell } from "@/components/layout/admin-nav";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <AdminShell>{children}</AdminShell>
    </RoleGuard>
  );
}
