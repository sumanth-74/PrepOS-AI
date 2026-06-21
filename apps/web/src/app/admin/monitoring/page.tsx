"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminMonitoringPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "monitoring"],
    () => adminPlatformApi.monitoring(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Platform monitoring"
      description="SLOs, alert thresholds, and observability rollups."
      query={query}
      loadingLabel="Loading monitoring dashboard…"
      emptyTitle="No monitoring data"
    />
  );
}
