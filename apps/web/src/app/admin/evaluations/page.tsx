"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminEvaluationsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "evaluations"],
    () => adminPlatformApi.evaluations(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Evaluation platform"
      description="Human labels, golden sets, and model evaluation coverage."
      query={query}
      loadingLabel="Loading evaluations…"
      emptyTitle="No evaluation data"
    />
  );
}
