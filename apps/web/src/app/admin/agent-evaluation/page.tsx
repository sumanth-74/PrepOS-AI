"use client";

import { adminAgentEvaluationApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminAgentEvaluationPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "agent-evaluation"],
    () => adminAgentEvaluationApi.dashboard(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Agent evaluation"
      description="Benchmark scores, regression suites, and quality gates for AI agents."
      query={query}
      loadingLabel="Loading agent evaluation metrics…"
      emptyTitle="No evaluation runs yet"
    />
  );
}
