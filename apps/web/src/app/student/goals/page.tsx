"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { useGoal, useGoalMutations } from "@/hooks/use-student-queries";
import { formatPercent, formatScore } from "@/lib/utils/format";

const goalSchema = z.object({
  target_readiness_score: z.coerce.number().min(0).max(100),
  target_date: z.string().min(1, "Target date is required"),
  daily_capacity_minutes: z.coerce.number().min(15).max(720).optional(),
});

type GoalFormValues = z.infer<typeof goalSchema>;

export default function GoalsPage() {
  const goalQuery = useGoal();
  const { createMutation, updateMutation, examId } = useGoalMutations();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<GoalFormValues>({
    resolver: zodResolver(goalSchema),
    defaultValues: {
      target_readiness_score: 75,
      target_date: "",
      daily_capacity_minutes: 120,
    },
  });

  useEffect(() => {
    if (goalQuery.data) {
      reset({
        target_readiness_score: Number(goalQuery.data.target_readiness_score),
        target_date: goalQuery.data.target_date,
        daily_capacity_minutes: goalQuery.data.daily_capacity_minutes,
      });
    }
  }, [goalQuery.data, reset]);

  const onSubmit = handleSubmit(async (values) => {
    if (!examId) return;
    const payload = { exam_id: examId, ...values };
    try {
      if (goalQuery.data) {
        await updateMutation.mutateAsync(payload);
      } else {
        await createMutation.mutateAsync(payload);
      }
    } catch (error) {
      setError("root", {
        message: error instanceof Error ? error.message : "Failed to save goal",
      });
    }
  });

  if (goalQuery.isLoading) {
    return <LoadingState label="Loading goal..." />;
  }

  if (goalQuery.isError) {
    return <ErrorState error={goalQuery.error} onRetry={() => void goalQuery.refetch()} />;
  }

  return (
    <>
      <PageHeader
        title="Goals"
        description="Set your target readiness and track milestone progress."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={onSubmit} className="card space-y-4">
          <h2 className="text-sm font-semibold text-slate-900">
            {goalQuery.data ? "Update goal" : "Create goal"}
          </h2>

          <div>
            <label className="label" htmlFor="target_readiness_score">
              Target readiness score
            </label>
            <input
              id="target_readiness_score"
              type="number"
              className="input"
              {...register("target_readiness_score")}
            />
            {errors.target_readiness_score ? (
              <p className="mt-1 text-xs text-red-600">
                {errors.target_readiness_score.message}
              </p>
            ) : null}
          </div>

          <div>
            <label className="label" htmlFor="target_date">
              Target date
            </label>
            <input id="target_date" type="date" className="input" {...register("target_date")} />
            {errors.target_date ? (
              <p className="mt-1 text-xs text-red-600">{errors.target_date.message}</p>
            ) : null}
          </div>

          <div>
            <label className="label" htmlFor="daily_capacity_minutes">
              Daily capacity (minutes)
            </label>
            <input
              id="daily_capacity_minutes"
              type="number"
              className="input"
              {...register("daily_capacity_minutes")}
            />
          </div>

          {errors.root ? (
            <p className="text-sm text-red-600">{errors.root.message}</p>
          ) : null}

          <button type="submit" className="btn-primary" disabled={isSubmitting || !examId}>
            {isSubmitting ? "Saving..." : "Save goal"}
          </button>
        </form>

        {goalQuery.data ? (
          <section className="card space-y-4">
            <div>
              <p className="text-xs uppercase text-slate-500">Goal probability</p>
              <p className="text-2xl font-semibold text-brand-700">
                {formatPercent(goalQuery.data.goal_probability)}
              </p>
              {goalQuery.data.goal_likelihood ? (
                <StatusBadge label={goalQuery.data.goal_likelihood} tone="info" />
              ) : null}
            </div>

            {goalQuery.data.trajectory ? (
              <div className="grid gap-3 text-sm text-slate-700">
                <p>Required gain: {formatScore(goalQuery.data.trajectory.required_gain)}</p>
                <p>
                  Expected daily progress:{" "}
                  {formatScore(goalQuery.data.trajectory.expected_daily_progress)}
                </p>
                <p>
                  Expected weekly progress:{" "}
                  {formatScore(goalQuery.data.trajectory.expected_weekly_progress)}
                </p>
              </div>
            ) : null}

            {goalQuery.data.milestones.length > 0 ? (
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Milestones</h3>
                <ul className="mt-2 space-y-2 text-sm text-slate-700">
                  {goalQuery.data.milestones.map((milestone) => (
                    <li key={milestone.target_date} className="rounded-lg bg-slate-50 p-3">
                      <p>{milestone.target_date}</p>
                      <p>Readiness: {formatScore(milestone.target_readiness)}</p>
                      <p>Expected score: {formatScore(milestone.expected_score)}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        ) : (
          <EmptyState
            title="No goal set"
            description="Create a goal to unlock trajectory and milestone tracking."
          />
        )}
      </div>
    </>
  );
}
