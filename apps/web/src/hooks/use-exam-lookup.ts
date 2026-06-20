"use client";

import { useQuery } from "@tanstack/react-query";
import { catalogApi } from "@/lib/api";
import { formatLabel } from "@/lib/utils/format";
import { useAuthToken } from "@/providers/auth-provider";

export function useExamCatalog() {
  const token = useAuthToken();

  return useQuery({
    queryKey: ["catalog", "exams"],
    queryFn: () => catalogApi.listExams(token),
    enabled: Boolean(token),
    staleTime: 60 * 60 * 1000,
  });
}

export function useExamName(examId: string | null | undefined): string {
  const examsQuery = useExamCatalog();
  if (!examId) return "—";
  const exam = examsQuery.data?.find((item) => item.exam_id === examId);
  return exam?.exam_name ?? formatLabel(examId);
}
