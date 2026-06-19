"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { mentorApi } from "@/lib/api";
import { useAuthToken } from "@/providers/auth-provider";

export function useMentorDashboard() {
  const token = useAuthToken();
  return useQuery({
    queryKey: ["mentor", "dashboard"],
    queryFn: () => mentorApi.dashboard(token!),
    enabled: Boolean(token),
  });
}

export function useMentorQueue() {
  const token = useAuthToken();
  return useQuery({
    queryKey: ["mentor", "queue"],
    queryFn: () => mentorApi.queue(token!),
    enabled: Boolean(token),
  });
}

export function useMentorCase(caseId: string) {
  const token = useAuthToken();
  return useQuery({
    queryKey: ["mentor", "cases", caseId],
    queryFn: () => mentorApi.getCase(token!, caseId),
    enabled: Boolean(token && caseId),
  });
}

export function useMentorCaseMutations(caseId: string) {
  const queryClient = useQueryClient();
  const token = useAuthToken();
  const queryKey = ["mentor", "cases", caseId];

  const noteMutation = useMutation({
    mutationFn: (note: string) => mentorApi.addNote(token!, caseId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ["mentor", "queue"] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (resolutionReason: string) =>
      mentorApi.resolveCase(token!, caseId, resolutionReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ["mentor", "dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["mentor", "queue"] });
    },
  });

  return { noteMutation, resolveMutation };
}
