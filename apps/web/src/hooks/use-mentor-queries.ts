"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { mentorApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { toastError, toastSuccess } from "@/lib/toast";
import type { MentorCaseResponse } from "@/lib/types/api";
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
    onMutate: async (note) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<MentorCaseResponse>(queryKey);
      if (previous) {
        queryClient.setQueryData<MentorCaseResponse>(queryKey, {
          ...previous,
          notes: [
            ...previous.notes,
            {
              note_id: `optimistic-${Date.now()}`,
              mentor_id: "You",
              note,
              created_at: new Date().toISOString(),
            },
          ],
        });
      }
      return { previous };
    },
    onSuccess: () => {
      toastSuccess("Note added");
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ["mentor", "queue"] });
    },
    onError: (error, _note, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      toastError(error instanceof ApiError ? error.message : "Failed to add note");
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (resolutionReason: string) =>
      mentorApi.resolveCase(token!, caseId, resolutionReason),
    onSuccess: () => {
      toastSuccess("Case resolved");
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ["mentor", "dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["mentor", "queue"] });
    },
    onError: (error) => {
      toastError(error instanceof ApiError ? error.message : "Failed to resolve case");
    },
  });

  return { noteMutation, resolveMutation };
}
