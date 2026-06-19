"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { studentApi } from "@/lib/api";
import { useAuthToken } from "@/providers/auth-provider";
import { useUiStore } from "@/stores";

export function useStudentContext() {
  const token = useAuthToken();
  const examId = useUiStore((state) => state.examId);
  const setExamId = useUiStore((state) => state.setExamId);

  const profileQuery = useQuery({
    queryKey: ["student", "profile"],
    queryFn: () => studentApi.profile(token!),
    enabled: Boolean(token),
  });

  useEffect(() => {
    const targetExam = profileQuery.data?.target_exam;
    if (targetExam && !examId) {
      setExamId(targetExam);
    }
  }, [examId, profileQuery.data?.target_exam, setExamId]);

  return {
    token,
    examId: examId ?? profileQuery.data?.target_exam ?? null,
    profile: profileQuery.data,
    profileQuery,
  };
}
