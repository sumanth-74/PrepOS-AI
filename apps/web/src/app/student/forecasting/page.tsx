"use client";

import { GoalForecastingView } from "@/components/forecasting/goal-forecasting-view";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import {
  useForecastHistory,
  useForecastMutations,
  useGoalForecast,
} from "@/hooks/use-forecasting-queries";
import { useStudentContext } from "@/hooks/use-student-context";
import { studentApi } from "@/lib/api";

export default function StudentForecastingPage() {
  const { examId, token } = useStudentContext();
  const forecastQuery = useGoalForecast();
  const historyQuery = useForecastHistory();
  const { generateMutation, customScenarioMutation } = useForecastMutations();

  return (
    <>
      <PageHeader
        title="Goal Forecasting"
        description="Deterministic readiness projection, goal probability, and what-if scenarios from twin, planning, and recommendation outcomes."
        actions={
          <button
            type="button"
            className="btn-primary"
            disabled={generateMutation.isPending}
            onClick={() => generateMutation.mutate()}
          >
            {generateMutation.isPending ? "Generating…" : "Generate forecast"}
          </button>
        }
      />
      <QueryBoundary
        query={forecastQuery}
        loadingLabel="Loading goal forecast..."
        emptyTitle="No goal forecast yet"
        emptyDescription="Generate a forecast to see readiness projection, probability, and scenario comparisons."
        isEmpty={() => false}
      >
        {(forecast) => (
          <GoalForecastingView
            forecast={forecast}
            history={historyQuery.data?.forecasts}
            generating={generateMutation.isPending}
            simulating={customScenarioMutation.isPending}
            onGenerate={() => generateMutation.mutate()}
            onSimulateCustom={(weeklyMinutes) => customScenarioMutation.mutate(weeklyMinutes)}
            onExplain={() => studentApi.explainForecast(token!, examId ?? undefined)}
          />
        )}
      </QueryBoundary>
    </>
  );
}
