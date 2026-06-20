"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  tenantSlug: string | null;
  tokenExpiresAt: number | null;
  setTokens: (
    accessToken: string,
    refreshToken: string,
    tenantSlug: string,
    expiresInSeconds?: number,
  ) => void;
  setTenantSlug: (tenantSlug: string) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      tenantSlug: null,
      tokenExpiresAt: null,
      setTokens: (accessToken, refreshToken, tenantSlug, expiresInSeconds) =>
        set({
          accessToken,
          refreshToken,
          tenantSlug,
          tokenExpiresAt:
            expiresInSeconds !== undefined
              ? Date.now() + expiresInSeconds * 1000
              : null,
        }),
      setTenantSlug: (tenantSlug) => set({ tenantSlug }),
      clear: () =>
        set({
          accessToken: null,
          refreshToken: null,
          tenantSlug: null,
          tokenExpiresAt: null,
        }),
    }),
    { name: "prepos-auth" },
  ),
);

interface UiState {
  sidebarOpen: boolean;
  examId: string | null;
  setSidebarOpen: (open: boolean) => void;
  setExamId: (examId: string | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  examId: null,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setExamId: (examId) => set({ examId }),
}));
