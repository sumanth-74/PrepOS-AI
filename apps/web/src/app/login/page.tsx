"use client";

import { Suspense, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";

import { LoginForm } from "@/components/auth/login-form";
import { FadeIn } from "@/components/motion/primitives";
import { LoadingState } from "@/components/ui/loading-state";
import { defaultPortalPath, normalizeRoles } from "@/lib/auth/roles";
import { useAuth } from "@/providers/auth-provider";

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    if (isLoading || !isAuthenticated || !user) return;
    router.replace(defaultPortalPath(normalizeRoles(user.roles)));
  }, [isAuthenticated, isLoading, router, user]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-mesh">
        <LoadingState label="Checking session..." />
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-mesh">
        <LoadingState label="Redirecting..." />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 py-10">
      <div className="absolute inset-0 bg-gradient-mesh" />
      <div className="absolute -left-32 top-20 h-64 w-64 rounded-full bg-growth-400/20 blur-3xl" />
      <div className="absolute -right-32 bottom-20 h-64 w-64 rounded-full bg-emerald-400/15 blur-3xl" />

      <FadeIn className="relative mb-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-growth shadow-glow">
          <Sparkles className="h-7 w-7 text-white" />
        </div>
        <h1 className="text-display-sm gradient-text">PrepOS</h1>
        <p className="mt-2 text-sm text-foreground-muted">
          Your AI-powered UPSC learning companion
        </p>
      </FadeIn>

      <Suspense fallback={<LoadingState label="Loading sign in..." />}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
