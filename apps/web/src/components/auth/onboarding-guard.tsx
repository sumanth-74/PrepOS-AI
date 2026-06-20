"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { LoadingState } from "@/components/ui/loading-state";
import { useStudentContext } from "@/hooks/use-student-context";

export function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { profile, profileQuery } = useStudentContext();

  useEffect(() => {
    if (profileQuery.isLoading || !profile) return;
    if (!profile.onboarding_completed && !pathname.startsWith("/student/onboarding")) {
      router.replace("/student/onboarding");
    }
  }, [pathname, profile, profileQuery.isLoading, router]);

  if (profileQuery.isLoading) {
    return <LoadingState label="Loading your profile..." />;
  }

  if (profileQuery.isError) {
    return null;
  }

  if (profile && !profile.onboarding_completed) {
    return <LoadingState label="Redirecting to onboarding..." />;
  }

  return children;
}
