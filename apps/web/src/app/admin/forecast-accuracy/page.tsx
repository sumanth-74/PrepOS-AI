"use client";

import { adminPlatformApi } from "@/lib/api";
import {
  AdminPlatformPage,
  useAdminPlatformQuery,
} from "@/components/admin/admin-platform-page";
import { useAuthStore } from "@/stores";

export default function AdminForecastAccuracyPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useAdminPlatformQuery(
    ["admin", "forecast-accuracy"],
    () => adminPlatformApi.forecastAccuracy(token!),
    Boolean(token),
  );

  return (
    <AdminPlatformPage
      title="Forecast accuracy"
      description="Predicted vs actual readiness and score calibration."
      query={query}
      loadingLabel="Loading forecast accuracy…"
      emptyTitle="No forecast accuracy records"
    />
  );
}
