"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { mentorApi, studentApi } from "@/lib/api";
import { toastError, toastSuccess } from "@/lib/toast";
import { useStudentContext } from "@/hooks/use-student-context";
import { useAuthStore } from "@/stores";

export function useGoalForecast(studentId?: string) {
  const { token, examId } = useStudentContext();
  return useQuery({
    queryKey: ["goal-forecast", examId, studentId ?? "self"],
    queryFn: () => studentApi.currentForecast(token!, examId ?? undefined),
    enabled: Boolean(token && examId && !studentId),
    retry: false,
  });
}

export function useForecastHistory(studentId?: string) {
  const { token, examId } = useStudentContext();
  return useQuery({
    queryKey: ["forecast-history", examId, studentId ?? "self"],
    queryFn: () => studentApi.forecastHistory(token!, examId ?? undefined),
    enabled: Boolean(token && examId && !studentId),
    retry: false,
  });
}

export function useForecastMutations() {
  const queryClient = useQueryClient();
  const { token, examId } = useStudentContext();
  const forecastKey = ["goal-forecast", examId, "self"];
  const historyKey = ["forecast-history", examId, "self"];

  const generateMutation = useMutation({
    mutationFn: () => studentApi.generateForecast(token!, examId ?? undefined),
    onSuccess: () => {
      toastSuccess("Goal forecast generated");
      void queryClient.invalidateQueries({ queryKey: forecastKey });
      void queryClient.invalidateQueries({ queryKey: historyKey });
    },
    onError: (error) => toastError(error),
  });

  const customScenarioMutation = useMutation({
    mutationFn: (weeklyMinutes: number) =>
      studentApi.simulateCustomScenario(token!, weeklyMinutes, examId ?? undefined),
    onSuccess: () => {
      toastSuccess("Custom scenario simulated");
      void queryClient.invalidateQueries({ queryKey: forecastKey });
    },
    onError: (error) => toastError(error),
  });

  return { generateMutation, customScenarioMutation };
}

export function useMentorStudentForecast(studentId: string, examId?: string) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["goal-forecast", examId ?? "upsc_cse", studentId],
    queryFn: () => mentorApi.studentForecast(token!, studentId, examId),
    enabled: Boolean(token && studentId),
    retry: false,
  });
}

export function useMentorForecastMutations(studentId: string, examId?: string) {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const queryKey = ["goal-forecast", examId ?? "upsc_cse", studentId];

  const simulateMutation = useMutation({
    mutationFn: () => mentorApi.simulateStudentForecast(token!, studentId, examId),
    onSuccess: () => {
      toastSuccess("Student forecast regenerated");
      void queryClient.invalidateQueries({ queryKey });
    },
    onError: (error) => toastError(error),
  });

  return { simulateMutation };
}
