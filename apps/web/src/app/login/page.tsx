"use client";

import { Suspense, useEffect } from "react";
import { useRouter } from "next/navigation";
import { LoginForm } from "@/components/auth/login-form";
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
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState label="Checking session..." />
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState label="Redirecting..." />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <Suspense fallback={<LoadingState label="Loading sign in..." />}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
