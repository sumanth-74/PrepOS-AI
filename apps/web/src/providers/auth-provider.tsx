"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import {
  initProactiveRefreshFromStore,
  refreshAccessToken,
  scheduleProactiveRefresh,
} from "@/lib/api/token-refresh";
import {
  defaultPortalPath,
  isMentorRole,
  isStudentRole,
  normalizeRoles,
} from "@/lib/auth/roles";
import type { AppRole, LoginRequest, UserResponse } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

interface AuthContextValue {
  user: UserResponse | null;
  roles: AppRole[];
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { accessToken, refreshToken, setTokens, clear } = useAuthStore();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initProactiveRefreshFromStore();
  }, []);

  const refreshUser = useCallback(async () => {
    if (!accessToken) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.me(accessToken);
      setUser(me);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401 && refreshToken) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          try {
            const me = await authApi.me(newToken);
            setUser(me);
            return;
          } catch {
            // Fall through to clear session.
          }
        }
      }
      if (error instanceof ApiError && error.isUnauthorized) {
        clear();
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, refreshToken, clear]);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (payload: LoginRequest) => {
      const tokens = await authApi.login(payload);
      setTokens(
        tokens.access_token,
        tokens.refresh_token,
        payload.tenant_slug,
        tokens.expires_in,
      );
      scheduleProactiveRefresh(tokens.expires_in);
      const me = await authApi.me(tokens.access_token);
      setUser(me);
      const roles = normalizeRoles(me.roles);
      router.replace(defaultPortalPath(roles));
    },
    [router, setTokens],
  );

  const logout = useCallback(async () => {
    if (accessToken) {
      try {
        await authApi.logout(accessToken, refreshToken);
      } catch {
        // Ignore logout failures locally.
      }
    }
    clear();
    setUser(null);
    router.replace("/login");
  }, [accessToken, refreshToken, clear, router]);

  const roles = useMemo(
    () => (user ? normalizeRoles(user.roles) : []),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      roles,
      isLoading,
      isAuthenticated: Boolean(user && accessToken),
      login,
      logout,
      refreshUser,
    }),
    [user, roles, isLoading, accessToken, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function useAuthToken(): string | null {
  return useAuthStore((state) => state.accessToken);
}

export { isMentorRole, isStudentRole };
