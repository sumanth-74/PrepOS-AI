"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { useExams, useOnboardingMutations } from "@/hooks/use-onboarding";
import { useStudentContext } from "@/hooks/use-student-context";
import { formatLabel } from "@/lib/utils/format";

const STEPS = [
  { id: 1, title: "Exam" },
  { id: 2, title: "Target year" },
  { id: 3, title: "Study hours" },
  { id: 4, title: "Experience" },
  { id: 5, title: "Complete" },
] as const;

const examSchema = z.object({
  target_exam: z.string().min(1, "Select an exam"),
});

const yearSchema = z.object({
  target_year: z.coerce.number().min(2024).max(2040),
});

const hoursSchema = z.object({
  daily_study_hours: z.coerce.number().min(0.5).max(16),
});

const experienceSchema = z.object({
  experience_level: z.enum(["beginner", "intermediate", "advanced", "repeater"]),
});

export function OnboardingWizard() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [formError, setFormError] = useState<string | null>(null);
  const { profile, profileQuery } = useStudentContext();
  const examsQuery = useExams();
  const { updateProfileMutation, completeOnboardingMutation } = useOnboardingMutations();

  const examForm = useForm({
    resolver: zodResolver(examSchema),
    defaultValues: { target_exam: profile?.target_exam ?? "" },
  });

  const yearForm = useForm({
    resolver: zodResolver(yearSchema),
    defaultValues: { target_year: profile?.target_year ?? new Date().getFullYear() + 1 },
  });

  const hoursForm = useForm({
    resolver: zodResolver(hoursSchema),
    defaultValues: {
      daily_study_hours: profile?.daily_study_hours
        ? Number(profile.daily_study_hours)
        : 2,
    },
  });

  const experienceForm = useForm({
    resolver: zodResolver(experienceSchema),
    defaultValues: {
      experience_level: (profile?.experience_level as "beginner") ?? "beginner",
    },
  });

  if (profileQuery.isLoading || examsQuery.isLoading) {
    return <LoadingState label="Preparing onboarding..." />;
  }

  if (profileQuery.isError) {
    return (
      <ErrorState error={profileQuery.error} onRetry={() => void profileQuery.refetch()} />
    );
  }

  if (profile?.onboarding_completed) {
    router.replace("/student/dashboard");
    return <LoadingState label="Redirecting to dashboard..." />;
  }

  const activeExams = (examsQuery.data ?? []).filter((exam) => exam.status === "active");

  const goNext = async () => {
    setFormError(null);
    try {
      if (step === 1) {
        const values = await examForm.trigger();
        if (!values) return;
        await updateProfileMutation.mutateAsync({
          target_exam: examForm.getValues("target_exam"),
        });
        setStep(2);
      } else if (step === 2) {
        const values = await yearForm.trigger();
        if (!values) return;
        await updateProfileMutation.mutateAsync({
          target_year: yearForm.getValues("target_year"),
        });
        setStep(3);
      } else if (step === 3) {
        const values = await hoursForm.trigger();
        if (!values) return;
        await updateProfileMutation.mutateAsync({
          daily_study_hours: hoursForm.getValues("daily_study_hours"),
        });
        setStep(4);
      } else if (step === 4) {
        const values = await experienceForm.trigger();
        if (!values) return;
        await updateProfileMutation.mutateAsync({
          experience_level: experienceForm.getValues("experience_level"),
        });
        setStep(5);
      }
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Failed to save step");
    }
  };

  const completeOnboarding = async () => {
    setFormError(null);
    try {
      await completeOnboardingMutation.mutateAsync();
      router.replace("/student/dashboard");
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Failed to complete onboarding");
    }
  };

  const busy = updateProfileMutation.isPending || completeOnboardingMutation.isPending;

  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-900">Welcome to PrepOS</h1>
        <p className="mt-1 text-sm text-slate-600">
          Set up your preparation profile. This provisions your learning graph and twin.
        </p>
      </div>

      <ol className="mb-8 flex flex-wrap gap-2">
        {STEPS.map((item) => (
          <li
            key={item.id}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              item.id === step
                ? "bg-brand-700 text-white"
                : item.id < step
                  ? "bg-brand-100 text-brand-800"
                  : "bg-slate-100 text-slate-500"
            }`}
          >
            {item.id}. {item.title}
          </li>
        ))}
      </ol>

      <div className="card space-y-4">
        {step === 1 ? (
          <div className="space-y-3">
            <label className="label" htmlFor="target_exam">
              Target exam
            </label>
            <select id="target_exam" className="input" {...examForm.register("target_exam")}>
              <option value="">Select an exam</option>
              {activeExams.map((exam) => (
                <option key={exam.exam_id} value={exam.exam_id}>
                  {exam.exam_name}
                </option>
              ))}
            </select>
            {examForm.formState.errors.target_exam ? (
              <p className="text-xs text-red-600">
                {examForm.formState.errors.target_exam.message}
              </p>
            ) : null}
          </div>
        ) : null}

        {step === 2 ? (
          <div className="space-y-3">
            <label className="label" htmlFor="target_year">
              Target exam year
            </label>
            <input
              id="target_year"
              type="number"
              className="input"
              {...yearForm.register("target_year")}
            />
            {yearForm.formState.errors.target_year ? (
              <p className="text-xs text-red-600">
                {yearForm.formState.errors.target_year.message}
              </p>
            ) : null}
          </div>
        ) : null}

        {step === 3 ? (
          <div className="space-y-3">
            <label className="label" htmlFor="daily_study_hours">
              Daily study hours
            </label>
            <input
              id="daily_study_hours"
              type="number"
              step="0.5"
              min="0.5"
              max="16"
              className="input"
              {...hoursForm.register("daily_study_hours")}
            />
            {hoursForm.formState.errors.daily_study_hours ? (
              <p className="text-xs text-red-600">
                {hoursForm.formState.errors.daily_study_hours.message}
              </p>
            ) : null}
          </div>
        ) : null}

        {step === 4 ? (
          <div className="space-y-3">
            <label className="label" htmlFor="experience_level">
              Current preparation level
            </label>
            <select
              id="experience_level"
              className="input"
              {...experienceForm.register("experience_level")}
            >
              {(["beginner", "intermediate", "advanced", "repeater"] as const).map((level) => (
                <option key={level} value={level}>
                  {formatLabel(level)}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {step === 5 ? (
          <div className="space-y-2 text-sm text-slate-700">
            <p className="font-medium text-slate-900">Review your setup</p>
            <ul className="list-inside list-disc space-y-1">
              <li>Exam: {examForm.getValues("target_exam") || "—"}</li>
              <li>Target year: {yearForm.getValues("target_year")}</li>
              <li>Daily hours: {hoursForm.getValues("daily_study_hours")}</li>
              <li>Level: {formatLabel(experienceForm.getValues("experience_level"))}</li>
            </ul>
            <p className="pt-2 text-slate-600">
              Completing onboarding provisions your learning graph nodes and preparation twin.
            </p>
          </div>
        ) : null}

        {formError ? (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</p>
        ) : null}

        <div className="flex flex-wrap gap-3 pt-2">
          {step > 1 ? (
            <button
              type="button"
              className="btn-secondary"
              disabled={busy}
              onClick={() => setStep((current) => current - 1)}
            >
              Back
            </button>
          ) : null}
          {step < 5 ? (
            <button type="button" className="btn-primary" disabled={busy} onClick={() => void goNext()}>
              {busy ? "Saving..." : "Continue"}
            </button>
          ) : (
            <button
              type="button"
              className="btn-primary"
              disabled={busy}
              onClick={() => void completeOnboarding()}
            >
              {busy ? "Completing..." : "Complete onboarding"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
