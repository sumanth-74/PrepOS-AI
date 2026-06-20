"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { studentApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { invalidateStudentData } from "@/lib/query/invalidate-student-data";
import { toastError, toastSuccess } from "@/lib/toast";
import type {
  RecordAssessmentRequest,
  RecordPyqChangeRequest,
  RecordRevisionRequest,
  RecordStudySessionRequest,
} from "@/lib/types/api";
import { useStudentContext } from "@/hooks/use-student-context";

type OmitExamId<T> = Omit<T, "exam_id">;

export function useActivityMutations() {
  const queryClient = useQueryClient();
  const { token, examId } = useStudentContext();

  const onSuccess = (message: string) => {
    invalidateStudentData(queryClient);
    toastSuccess(message);
  };

  const onError = (error: unknown) => {
    toastError(error instanceof ApiError ? error.message : "Activity submission failed");
  };

  const requireExamId = (): string => {
    if (!examId) {
      throw new Error("Target exam is not set. Complete onboarding first.");
    }
    return examId;
  };

  const studySessionMutation = useMutation({
    mutationFn: (body: OmitExamId<RecordStudySessionRequest>) =>
      studentApi.submitStudySession(token!, { ...body, exam_id: requireExamId() }),
    onSuccess: () => onSuccess("Study session logged"),
    onError,
  });

  const revisionMutation = useMutation({
    mutationFn: (body: OmitExamId<RecordRevisionRequest>) =>
      studentApi.submitRevision(token!, { ...body, exam_id: requireExamId() }),
    onSuccess: () => onSuccess("Revision logged"),
    onError,
  });

  const assessmentMutation = useMutation({
    mutationFn: (body: OmitExamId<RecordAssessmentRequest>) =>
      studentApi.submitAssessment(token!, { ...body, exam_id: requireExamId() }),
    onSuccess: () => onSuccess("Assessment logged"),
    onError,
  });

  const pyqMutation = useMutation({
    mutationFn: (body: OmitExamId<RecordPyqChangeRequest>) =>
      studentApi.submitPyqChange(token!, { ...body, exam_id: requireExamId() }),
    onSuccess: () => onSuccess("PYQ importance updated"),
    onError,
  });

  return {
    studySessionMutation,
    revisionMutation,
    assessmentMutation,
    pyqMutation,
  };
}
