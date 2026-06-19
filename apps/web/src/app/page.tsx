"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { defaultPortalPath, normalizeRoles } from "@/lib/auth/roles";
import { useAuth } from "@/providers/auth-provider";
import { LoadingState } from "@/components/ui/loading-state";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated || !user) {
      router.replace("/login");
      return;
    }
    router.replace(defaultPortalPath(normalizeRoles(user.roles)));
  }, [isAuthenticated, isLoading, router, user]);

  return <LoadingState label="Redirecting..." />;
}
