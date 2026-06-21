"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminDisasterRecoveryPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "disaster-recovery"],
    () => adminPlatformApi.disasterRecovery(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Disaster recovery"
      description="Backup verification, RPO/RTO posture, and restore drills."
      query={query}
      loadingLabel="Loading disaster recovery status…"
      emptyTitle="No DR verification data"
    />
  );
}
