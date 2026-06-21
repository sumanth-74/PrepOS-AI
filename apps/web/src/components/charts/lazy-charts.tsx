"use client";

import dynamic from "next/dynamic";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export const ReadinessSparkline = dynamic(
  () => import("@/components/charts/premium-charts").then((m) => m.ReadinessSparkline),
  { loading: () => <LoadingSkeleton rows={4} className="h-[120px]" />, ssr: false },
);

export const MiniBarChart = dynamic(
  () => import("@/components/charts/premium-charts").then((m) => m.MiniBarChart),
  { loading: () => <LoadingSkeleton rows={4} />, ssr: false },
);

export const SegmentHeatmap = dynamic(
  () => import("@/components/charts/premium-charts").then((m) => m.SegmentHeatmap),
  { loading: () => <LoadingSkeleton rows={3} />, ssr: false },
);

export const ReadinessRadar = dynamic(
  () => import("@/components/charts/premium-charts").then((m) => m.ReadinessRadar),
  { loading: () => <LoadingSkeleton rows={5} className="h-[200px]" />, ssr: false },
);
