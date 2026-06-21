"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminOutcomesPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "outcomes"],
    () => adminPlatformApi.outcomes(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Learning outcomes"
      description="Aggregate readiness gains, goal attainment, and intervention impact."
      query={query}
      loadingLabel="Loading outcomes dashboard…"
      emptyTitle="No outcomes data"
    />
  );
}
