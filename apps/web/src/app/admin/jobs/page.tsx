"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminJobsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "jobs"],
    () => adminPlatformApi.jobs(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Background jobs"
      description="Celery task throughput, queue depth, and failure rates."
      query={query}
      loadingLabel="Loading job metrics…"
      emptyTitle="No job telemetry"
      emptyDescription="Job metrics appear once workers process tasks."
    />
  );
}
