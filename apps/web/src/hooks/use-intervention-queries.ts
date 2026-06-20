"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { mentorApi } from "@/lib/api";
import { toastError, toastSuccess } from "@/lib/toast";
import { useAuthStore } from "@/stores";

export function useMentorInterventionQueue(limit = 20) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["mentor-intervention-queue", limit],
    queryFn: () => mentorApi.interventionQueue(token!, limit),
    enabled: Boolean(token),
    retry: false,
  });
}

export function useMentorStudentInterventions(studentId: string, examId?: string) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["student-interventions", examId ?? "upsc_cse", studentId],
    queryFn: () => mentorApi.studentInterventions(token!, studentId, examId),
    enabled: Boolean(token && studentId),
    retry: false,
  });
}

export function useMentorInterventionMutations(studentId: string, examId?: string) {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const queryKey = ["student-interventions", examId ?? "upsc_cse", studentId];
  const queueKey = ["mentor-intervention-queue", 20];

  const generateMutation = useMutation({
    mutationFn: () => mentorApi.generateStudentInterventions(token!, studentId, examId),
    onSuccess: () => {
      toastSuccess("Interventions generated");
      void queryClient.invalidateQueries({ queryKey });
      void queryClient.invalidateQueries({ queryKey: queueKey });
    },
    onError: (error) => toastError(error),
  });

  const executeMutation = useMutation({
    mutationFn: (interventionId: string) => mentorApi.executeIntervention(token!, interventionId),
    onSuccess: () => {
      toastSuccess("Intervention started");
      void queryClient.invalidateQueries({ queryKey });
    },
    onError: (error) => toastError(error),
  });

  const completeMutation = useMutation({
    mutationFn: (interventionId: string) => mentorApi.completeIntervention(token!, interventionId),
    onSuccess: () => {
      toastSuccess("Intervention completed");
      void queryClient.invalidateQueries({ queryKey });
      void queryClient.invalidateQueries({ queryKey: queueKey });
    },
    onError: (error) => toastError(error),
  });

  return { generateMutation, executeMutation, completeMutation };
}
