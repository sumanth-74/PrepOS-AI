"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { mentorApi, studentApi } from "@/lib/api";
import { toastMutationError, toastSuccess } from "@/lib/toast";
import { useStudentContext } from "@/hooks/use-student-context";
import { useAuthStore } from "@/stores";

export function useAdaptivePlan(studentId?: string) {
  const { token, examId } = useStudentContext();
  return useQuery({
    queryKey: ["adaptive-plan", examId, studentId ?? "self"],
    queryFn: () => studentApi.currentPlan(token!, examId ?? undefined),
    enabled: Boolean(token && examId && !studentId),
    retry: false,
  });
}

export function useAdaptivePlanMutations() {
  const queryClient = useQueryClient();
  const { token, examId } = useStudentContext();
  const queryKey = ["adaptive-plan", examId, "self"];

  const generateMutation = useMutation({
    mutationFn: (dailyMinutes?: number) =>
      studentApi.generatePlan(token!, examId ?? undefined, dailyMinutes),
    onSuccess: () => {
      toastSuccess("Weekly plan generated");
      void queryClient.invalidateQueries({ queryKey });
    },
    onError: (error) => toastMutationError(error),
  });

  const completeMutation = useMutation({
    mutationFn: (itemId: string) => studentApi.completeAdaptivePlanItem(token!, itemId),
    onSuccess: () => {
      toastSuccess("Plan item completed");
      void queryClient.invalidateQueries({ queryKey });
    },
    onError: (error) => toastMutationError(error),
  });

  return { generateMutation, completeMutation };
}

export function useMentorStudentPlan(studentId: string, examId?: string) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["adaptive-plan", examId ?? "upsc_cse", studentId],
    queryFn: () => mentorApi.studentPlan(token!, studentId, examId),
    enabled: Boolean(token && studentId),
    retry: false,
  });
}

export function useMentorPlanMutations(studentId: string, examId?: string) {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const queryKey = ["adaptive-plan", examId ?? "upsc_cse", studentId];

  const regenerateMutation = useMutation({
    mutationFn: () => mentorApi.regenerateStudentPlan(token!, studentId, examId),
    onSuccess: () => {
      toastSuccess("Student plan regenerated");
      void queryClient.invalidateQueries({ queryKey });
    },
    onError: (error) => toastMutationError(error),
  });

  return { regenerateMutation };
}
