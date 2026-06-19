"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { use } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { useMentorCase, useMentorCaseMutations } from "@/hooks/use-mentor-queries";
import { formatLabel } from "@/lib/utils/format";

const noteSchema = z.object({
  note: z.string().min(1, "Note is required"),
});

const resolveSchema = z.object({
  resolution_reason: z.string().min(1, "Resolution reason is required"),
});

type NoteFormValues = z.infer<typeof noteSchema>;
type ResolveFormValues = z.infer<typeof resolveSchema>;

export default function MentorCasePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const caseQuery = useMentorCase(id);
  const { noteMutation, resolveMutation } = useMentorCaseMutations(id);

  const noteForm = useForm<NoteFormValues>({
    resolver: zodResolver(noteSchema),
    defaultValues: { note: "" },
  });

  const resolveForm = useForm<ResolveFormValues>({
    resolver: zodResolver(resolveSchema),
    defaultValues: { resolution_reason: "" },
  });

  if (caseQuery.isLoading) {
    return <LoadingState label="Loading case..." />;
  }

  if (caseQuery.isError || !caseQuery.data) {
    return <ErrorState error={caseQuery.error} onRetry={() => void caseQuery.refetch()} />;
  }

  const mentorCase = caseQuery.data;

  return (
    <>
      <PageHeader
        title={`Case ${mentorCase.case_id}`}
        description={`Student ${mentorCase.student_id}`}
        actions={
          <button
            type="button"
            className="btn-secondary"
            onClick={() => router.push(`/mentor/student/${mentorCase.student_id}`)}
          >
            View student twin
          </button>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InfoCard label="Status" value={formatLabel(mentorCase.status)} />
        <InfoCard label="Priority" value={formatLabel(mentorCase.priority)} />
        <InfoCard label="Action" value={formatLabel(mentorCase.mentor_action_type)} />
        <InfoCard label="Escalation" value={formatLabel(mentorCase.escalation_level)} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <form
          className="card space-y-3"
          onSubmit={noteForm.handleSubmit(async (values) => {
            await noteMutation.mutateAsync(values.note);
            noteForm.reset();
          })}
        >
          <h2 className="text-sm font-semibold text-slate-900">Add note</h2>
          <textarea
            className="input min-h-28"
            {...noteForm.register("note")}
          />
          {noteForm.formState.errors.note ? (
            <p className="text-xs text-red-600">
              {noteForm.formState.errors.note.message}
            </p>
          ) : null}
          <button type="submit" className="btn-primary" disabled={noteMutation.isPending}>
            {noteMutation.isPending ? "Saving..." : "Add note"}
          </button>
        </form>

        <form
          className="card space-y-3"
          onSubmit={resolveForm.handleSubmit(async (values) => {
            await resolveMutation.mutateAsync(values.resolution_reason);
            router.push("/mentor/queue");
          })}
        >
          <h2 className="text-sm font-semibold text-slate-900">Resolve case</h2>
          <textarea
            className="input min-h-28"
            {...resolveForm.register("resolution_reason")}
          />
          {resolveForm.formState.errors.resolution_reason ? (
            <p className="text-xs text-red-600">
              {resolveForm.formState.errors.resolution_reason.message}
            </p>
          ) : null}
          <button type="submit" className="btn-primary" disabled={resolveMutation.isPending}>
            {resolveMutation.isPending ? "Resolving..." : "Resolve case"}
          </button>
        </form>
      </div>

      <section className="card mt-6">
        <h2 className="text-sm font-semibold text-slate-900">Notes</h2>
        {mentorCase.notes.length === 0 ? (
          <p className="mt-3 text-sm text-slate-600">No notes yet.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {mentorCase.notes.map((note) => (
              <li key={note.note_id} className="rounded-lg bg-slate-50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <StatusBadge label={note.mentor_id} />
                  <span className="text-xs text-slate-500">{note.created_at}</span>
                </div>
                <p className="mt-2 text-sm text-slate-700">{note.note}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-900">{value}</p>
    </div>
  );
}
