"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminAdoptionPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "adoption"],
    () => adminPlatformApi.adoption(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Product adoption"
      description="Feature usage, cohort activation, and engagement funnels."
      query={query}
      loadingLabel="Loading adoption metrics…"
      emptyTitle="No adoption data"
    />
  );
}
