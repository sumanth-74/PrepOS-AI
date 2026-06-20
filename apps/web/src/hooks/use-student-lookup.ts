"use client";

import { useQueries, useQuery } from "@tanstack/react-query";
import { studentApi } from "@/lib/api";
import { formatShortRef } from "@/lib/utils/format";
import { useExamName } from "@/hooks/use-exam-lookup";
import { useAuthToken } from "@/providers/auth-provider";

export function useStudentProfile(studentId: string | null | undefined) {
  const token = useAuthToken();

  return useQuery({
    queryKey: ["student", "profile", studentId],
    queryFn: () => studentApi.getProfile(token!, studentId!),
    enabled: Boolean(token && studentId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useStudentProfiles(studentIds: string[]) {
  const token = useAuthToken();
  const uniqueIds = [...new Set(studentIds.filter(Boolean))];

  return useQueries({
    queries: uniqueIds.map((studentId) => ({
      queryKey: ["student", "profile", studentId],
      queryFn: () => studentApi.getProfile(token!, studentId),
      enabled: Boolean(token),
      staleTime: 5 * 60 * 1000,
    })),
  });
}

export function buildStudentDisplayName(
  studentId: string,
  targetExam: string | null | undefined,
  examName: string,
): string {
  if (targetExam && examName !== "—") {
    return `Student · ${examName}`;
  }
  return formatShortRef(studentId, "Student");
}

export function useStudentDisplayName(studentId: string, targetExam?: string | null) {
  const examName = useExamName(targetExam);
  return buildStudentDisplayName(studentId, targetExam, examName);
}
