"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { catalogApi, studentApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { invalidateStudentData } from "@/lib/query/invalidate-student-data";
import { toastError, toastSuccess } from "@/lib/toast";
import type { UpdateStudentGoalsRequest } from "@/lib/types/api";
import { useStudentContext } from "@/hooks/use-student-context";
import { useUiStore } from "@/stores";

export function useExams() {
  const { token } = useStudentContext();
  return useQuery({
    queryKey: ["catalog", "exams"],
    queryFn: () => catalogApi.listExams(token),
    enabled: Boolean(token),
  });
}

export function useOnboardingMutations() {
  const queryClient = useQueryClient();
  const { token, profile } = useStudentContext();
  const setExamId = useUiStore((state) => state.setExamId);

  const updateProfileMutation = useMutation({
    mutationFn: (body: UpdateStudentGoalsRequest) =>
      studentApi.updateProfile(token!, profile!.id, body),
    onSuccess: (data) => {
      queryClient.setQueryData(["student", "profile"], data);
      if (data.target_exam) {
        setExamId(data.target_exam);
      }
    },
    onError: (error) => {
      toastError(error instanceof ApiError ? error.message : "Failed to save onboarding step");
    },
  });

  const completeOnboardingMutation = useMutation({
    mutationFn: () => studentApi.completeOnboarding(token!),
    onSuccess: (data) => {
      queryClient.setQueryData(["student", "profile"], data.student);
      if (data.student.target_exam) {
        setExamId(data.student.target_exam);
      }
      invalidateStudentData(queryClient);
      toastSuccess("Onboarding complete. Your learning graph is provisioning.");
    },
    onError: (error) => {
      toastError(error instanceof ApiError ? error.message : "Failed to complete onboarding");
    },
  });

  return { updateProfileMutation, completeOnboardingMutation };
}
