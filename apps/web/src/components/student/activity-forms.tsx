"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, type UseFormRegister } from "react-hook-form";
import { z } from "zod";

import { useActivityMutations } from "@/hooks/use-activity-mutations";
import { useConceptLookup } from "@/hooks/use-concept-lookup";
import { useLearningGraph } from "@/hooks/use-student-queries";
import { useStudentContext } from "@/hooks/use-student-context";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { QueryBoundary } from "@/components/ui/query-boundary";

const studySessionSchema = z.object({
  concept_id: z.string().min(1, "Select a concept"),
  engaged_minutes: z.coerce.number().int().min(1).max(480),
});

const revisionSchema = z.object({
  concept_id: z.string().min(1, "Select a concept"),
  recall_grade: z.enum(["forgot", "hard", "good", "easy"]),
});

const assessmentSchema = z.object({
  concept_id: z.string().min(1, "Select a concept"),
  mcq_correct: z.enum(["true", "false"]),
  self_confidence: z.coerce.number().min(0).max(100).optional(),
});

const pyqSchema = z.object({
  concept_id: z.string().min(1, "Select a concept"),
  global_importance: z.coerce.number().min(0).max(100),
});

type StudySessionValues = z.infer<typeof studySessionSchema>;
type RevisionValues = z.infer<typeof revisionSchema>;
type AssessmentValues = z.infer<typeof assessmentSchema>;
type PyqValues = z.infer<typeof pyqSchema>;

type ConceptOption = { id: string; label: string };

function ConceptSelect<T extends { concept_id: string }>({
  concepts,
  register,
  error,
  selectId,
}: {
  concepts: ConceptOption[];
  register: UseFormRegister<T>;
  error?: string;
  selectId: string;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor={selectId}>
        Concept
      </label>
      <select id={selectId} className="input" {...register("concept_id" as never)}>
        <option value="">Select concept…</option>
        {concepts.map((c) => (
          <option key={c.id} value={c.id}>
            {c.label}
          </option>
        ))}
      </select>
      {error ? <p className="mt-1 text-sm text-red-600">{error}</p> : null}
    </div>
  );
}

function StudySessionForm({ concepts }: { concepts: ConceptOption[] }) {
  const { studySessionMutation } = useActivityMutations();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<StudySessionValues>({
    resolver: zodResolver(studySessionSchema),
    defaultValues: { engaged_minutes: 45 },
  });

  const onSubmit = handleSubmit(async (values) => {
    await studySessionMutation.mutateAsync(values);
    reset({ engaged_minutes: 45 });
  });

  return (
    <section className="card space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900">Study session</h2>
        <p className="text-sm text-slate-600">Log focused study time on a concept.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit}>
        <ConceptSelect
          concepts={concepts}
          register={register}
          error={errors.concept_id?.message}
          selectId="study-session-concept_id"
        />
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="engaged_minutes">
            Engaged minutes
          </label>
          <input id="engaged_minutes" type="number" className="input" {...register("engaged_minutes")} />
          {errors.engaged_minutes ? (
            <p className="mt-1 text-sm text-red-600">{errors.engaged_minutes.message}</p>
          ) : null}
        </div>
        <button type="submit" className="btn-primary" disabled={studySessionMutation.isPending}>
          {studySessionMutation.isPending ? "Submitting…" : "Log study session"}
        </button>
      </form>
    </section>
  );
}

function RevisionForm({ concepts }: { concepts: ConceptOption[] }) {
  const { revisionMutation } = useActivityMutations();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RevisionValues>({
    resolver: zodResolver(revisionSchema),
    defaultValues: { recall_grade: "good" },
  });

  const onSubmit = handleSubmit(async (values) => {
    await revisionMutation.mutateAsync(values);
    reset({ recall_grade: "good" });
  });

  return (
    <section className="card space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900">Revision</h2>
        <p className="text-sm text-slate-600">Record spaced-repetition recall for a concept.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit}>
        <ConceptSelect
          concepts={concepts}
          register={register}
          error={errors.concept_id?.message}
          selectId="revision-concept_id"
        />
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="recall_grade">
            Recall grade
          </label>
          <select id="recall_grade" className="input" {...register("recall_grade")}>
            <option value="forgot">Forgot</option>
            <option value="hard">Hard</option>
            <option value="good">Good</option>
            <option value="easy">Easy</option>
          </select>
        </div>
        <button type="submit" className="btn-primary" disabled={revisionMutation.isPending}>
          {revisionMutation.isPending ? "Submitting…" : "Log revision"}
        </button>
      </form>
    </section>
  );
}

function AssessmentForm({ concepts }: { concepts: ConceptOption[] }) {
  const { assessmentMutation } = useActivityMutations();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AssessmentValues>({ resolver: zodResolver(assessmentSchema) });

  const onSubmit = handleSubmit(async (values) => {
    await assessmentMutation.mutateAsync({
      concept_id: values.concept_id,
      mcq_correct: values.mcq_correct === "true",
      self_confidence: values.self_confidence,
    });
    reset({ mcq_correct: "false" });
  });

  return (
    <section className="card space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900">Assessment</h2>
        <p className="text-sm text-slate-600">Submit MCQ attempt results for a concept.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit}>
        <ConceptSelect
          concepts={concepts}
          register={register}
          error={errors.concept_id?.message}
          selectId="assessment-concept_id"
        />
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="mcq_correct">
            MCQ result
          </label>
          <select id="mcq_correct" className="input" {...register("mcq_correct")}>
            <option value="true">Correct</option>
            <option value="false">Incorrect</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="self_confidence">
            Self confidence (0–100, optional)
          </label>
          <input id="self_confidence" type="number" className="input" {...register("self_confidence")} />
        </div>
        <button type="submit" className="btn-primary" disabled={assessmentMutation.isPending}>
          {assessmentMutation.isPending ? "Submitting…" : "Log assessment"}
        </button>
      </form>
    </section>
  );
}

function PyqForm({ concepts }: { concepts: ConceptOption[] }) {
  const { pyqMutation } = useActivityMutations();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PyqValues>({ resolver: zodResolver(pyqSchema) });

  const onSubmit = handleSubmit(async (values) => {
    await pyqMutation.mutateAsync(values);
    reset({ global_importance: 50 });
  });

  return (
    <section className="card space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900">PYQ update</h2>
        <p className="text-sm text-slate-600">Update global PYQ importance for a concept.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit}>
        <ConceptSelect
          concepts={concepts}
          register={register}
          error={errors.concept_id?.message}
          selectId="pyq-concept_id"
        />
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="global_importance">
            Global importance (0–100)
          </label>
          <input
            id="global_importance"
            type="number"
            className="input"
            defaultValue={50}
            {...register("global_importance")}
          />
          {errors.global_importance ? (
            <p className="mt-1 text-sm text-red-600">{errors.global_importance.message}</p>
          ) : null}
        </div>
        <button type="submit" className="btn-primary" disabled={pyqMutation.isPending}>
          {pyqMutation.isPending ? "Submitting…" : "Update PYQ importance"}
        </button>
      </form>
    </section>
  );
}

function ActivityFormsContent() {
  const { profile, examId } = useStudentContext();
  const graphQuery = useLearningGraph();
  const { getConceptInfo } = useConceptLookup(examId);

  return (
    <QueryBoundary
      query={graphQuery}
      loadingFallback={<LoadingSkeleton rows={6} />}
      loadingLabel="Loading concepts..."
      emptyTitle="No concepts in learning graph"
      emptyDescription="Complete onboarding and wait for your syllabus graph to load before logging activities."
      emptyAction={{ label: "Complete onboarding", href: "/student/onboarding" }}
      isEmpty={(data) => data.nodes.length === 0}
    >
      {(graph) => {
        if (!profile?.id) {
          return (
            <EmptyState
              title="Student profile unavailable"
              description="Sign in as a student to log activities."
            />
          );
        }

        const concepts = graph.nodes.map((node) => {
          const info = getConceptInfo(node.concept_id);
          return {
            id: node.concept_id,
            label: info ? `${info.name} · ${info.path}` : "Loading concept…",
          };
        });

        return (
          <div className="grid gap-6 lg:grid-cols-2">
            <StudySessionForm concepts={concepts} />
            <RevisionForm concepts={concepts} />
            <AssessmentForm concepts={concepts} />
            <PyqForm concepts={concepts} />
          </div>
        );
      }}
    </QueryBoundary>
  );
}

export function ActivityForms() {
  return <ActivityFormsContent />;
}
