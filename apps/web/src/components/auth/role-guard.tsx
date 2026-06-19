"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import type { AppRole } from "@/lib/types/api";
import { hasAnyRole } from "@/lib/auth/roles";
import { LoadingState } from "@/components/ui/loading-state";

interface RoleGuardProps {
  allowed: AppRole[];
  children: ReactNode;
  fallbackPath?: string;
}

export function RoleGuard({
  allowed,
  children,
  fallbackPath = "/login",
}: RoleGuardProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading, roles } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace(fallbackPath);
      return;
    }
    if (!hasAnyRole(roles, allowed)) {
      router.replace("/unauthorized");
    }
  }, [allowed, fallbackPath, isAuthenticated, isLoading, roles, router]);

  if (isLoading) {
    return <LoadingState label="Checking session..." />;
  }

  if (!isAuthenticated || !hasAnyRole(roles, allowed)) {
    return <LoadingState label="Redirecting..." />;
  }

  return children;
}
