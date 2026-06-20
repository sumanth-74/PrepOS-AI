"use client";

import { useQuery } from "@tanstack/react-query";

import { mentorApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export function useCohortSummary(examId?: string, refresh = false) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["cohort-summary", examId ?? "upsc_cse", refresh],
    queryFn: () => mentorApi.cohortSummary(token!, examId, refresh),
    enabled: Boolean(token),
    retry: false,
  });
}

export function useCohortStudents(examId?: string) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["cohort-students", examId ?? "upsc_cse"],
    queryFn: () => mentorApi.cohortStudents(token!, examId),
    enabled: Boolean(token),
    retry: false,
  });
}

export function useCohortRisks(examId?: string) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["cohort-risks", examId ?? "upsc_cse"],
    queryFn: () => mentorApi.cohortRisks(token!, examId),
    enabled: Boolean(token),
    retry: false,
  });
}

export function useCohortTrends(examId?: string, period = "weekly") {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["cohort-trends", examId ?? "upsc_cse", period],
    queryFn: () => mentorApi.cohortTrends(token!, examId, period),
    enabled: Boolean(token),
    retry: false,
  });
}
