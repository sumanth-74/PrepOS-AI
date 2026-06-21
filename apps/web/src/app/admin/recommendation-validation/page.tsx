"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminRecommendationValidationPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "recommendation-validation"],
    () => adminPlatformApi.recommendationValidation(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Recommendation validation"
      description="Offline validation of recommendation engine quality and lift."
      query={query}
      loadingLabel="Loading validation metrics…"
      emptyTitle="No validation records"
    />
  );
}
