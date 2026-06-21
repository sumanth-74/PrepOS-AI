"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { studentApi, recommendationsApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { toastError, toastSuccess } from "@/lib/toast";
import type { GoalUpsertRequest, StudyPlanExecutionRequest } from "@/lib/types/api";
import { useStudentContext } from "@/hooks/use-student-context";

export function useTwinDashboard(studentId?: string) {
  const { token } = useStudentContext();
  return useQuery({
    queryKey: ["twin", "dashboard", studentId ?? "self"],
    queryFn: () => studentApi.twinDashboard(token!, studentId),
    enabled: Boolean(token),
  });
}

export function useTwin(studentId?: string) {
  const { token } = useStudentContext();
  return useQuery({
    queryKey: ["twin", "detail", studentId ?? "self"],
    queryFn: () => studentApi.twin(token!, studentId),
    enabled: Boolean(token),
  });
}

export function useRecommendations(studentId?: string, examIdOverride?: string | null) {
  const { token, examId: contextExamId } = useStudentContext();
  const examId = examIdOverride ?? contextExamId;
  return useQuery({
    queryKey: ["recommendations", "engine", studentId ?? "self", examId],
    queryFn: async () => {
      const response = studentId
        ? await recommendationsApi.mentor(token!, studentId, examId ?? undefined)
        : await recommendationsApi.student(token!, examId ?? undefined);
      return response.recommendations;
    },
    enabled: Boolean(token && (studentId ? examId : true)),
  });
}

export function useLearningGraph(studentId?: string) {
  const { token } = useStudentContext();
  return useQuery({
    queryKey: ["learning-graph", studentId ?? "self"],
    queryFn: () => studentApi.learningGraph(token!, studentId),
    enabled: Boolean(token),
  });
}

export function useReadiness(studentId?: string) {
  const { token } = useStudentContext();
  return useQuery({
    queryKey: ["learning-graph", "readiness", studentId ?? "self"],
    queryFn: () => studentApi.readiness(token!, studentId),
    enabled: Boolean(token),
  });
}

export function useRevisionQueue(studentId?: string) {
  const { token } = useStudentContext();
  return useQuery({
    queryKey: ["learning-graph", "revisions", studentId ?? "self"],
    queryFn: () => studentApi.revisionQueue(token!, studentId),
    enabled: Boolean(token),
  });
}

export function useStudyPlan(studentId?: string) {
  const { token, examId } = useStudentContext();
  return useQuery({
    queryKey: ["study-plan", examId, studentId ?? "self"],
    queryFn: () => studentApi.studyPlan(token!, examId ?? undefined, studentId),
    enabled: Boolean(token && examId),
  });
}

export function useStudyPlanMutations(studentId?: string) {
  const queryClient = useQueryClient();
  const { token, examId } = useStudentContext();
  const queryKey = ["study-plan", examId, studentId ?? "self"];

  const invalidate = () => queryClient.invalidateQueries({ queryKey });

  const completeMutation = useMutation({
    mutationFn: (body: StudyPlanExecutionRequest) =>
      studentApi.completePlanItem(token!, body, studentId),
    onMutate: async (body) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData(queryKey);
      queryClient.setQueryData(queryKey, (current: unknown) => {
        if (!current || typeof current !== "object") return current;
        const plan = current as {
          daily_plan: Array<{ concept_id: string; activity_type: string }>;
        };
        return {
          ...plan,
          daily_plan: plan.daily_plan.filter(
            (item) =>
              !(
                item.concept_id === body.concept_id &&
                item.activity_type === body.activity_type
              ),
          ),
        };
      });
      return { previous };
    },
    onError: (error, _body, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      toastError(error instanceof ApiError ? error.message : "Failed to complete plan item");
    },
    onSuccess: () => toastSuccess("Plan item completed"),
    onSettled: invalidate,
  });

  const skipMutation = useMutation({
    mutationFn: (body: StudyPlanExecutionRequest) =>
      studentApi.skipPlanItem(token!, body, studentId),
    onMutate: async (body) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData(queryKey);
      queryClient.setQueryData(queryKey, (current: unknown) => {
        if (!current || typeof current !== "object") return current;
        const plan = current as {
          daily_plan: Array<{ concept_id: string; activity_type: string }>;
        };
        return {
          ...plan,
          daily_plan: plan.daily_plan.filter(
            (item) =>
              !(
                item.concept_id === body.concept_id &&
                item.activity_type === body.activity_type
              ),
          ),
        };
      });
      return { previous };
    },
    onError: (error, _body, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      toastError(error instanceof ApiError ? error.message : "Failed to skip plan item");
    },
    onSuccess: () => toastSuccess("Plan item skipped"),
    onSettled: invalidate,
  });

  return { completeMutation, skipMutation, examId };
}

export function useGoal(studentId?: string) {
  const { token, examId } = useStudentContext();
  return useQuery({
    queryKey: ["goals", examId, studentId ?? "self"],
    queryFn: () => studentApi.getGoal(token!, examId!, studentId),
    enabled: Boolean(token && examId),
  });
}

export function useGoalMutations(studentId?: string) {
  const queryClient = useQueryClient();
  const { token, examId } = useStudentContext();
  const queryKey = ["goals", examId, studentId ?? "self"];

  const createMutation = useMutation({
    mutationFn: (body: GoalUpsertRequest) =>
      studentApi.createGoal(token!, body, studentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      toastSuccess("Goal created");
    },
    onError: (error) => {
      toastError(error instanceof ApiError ? error.message : "Failed to create goal");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (body: GoalUpsertRequest) =>
      studentApi.updateGoal(token!, body, studentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ["twin", "dashboard"] });
      toastSuccess("Goal updated");
    },
    onError: (error) => {
      toastError(error instanceof ApiError ? error.message : "Failed to update goal");
    },
  });

  return { createMutation, updateMutation, examId };
}
