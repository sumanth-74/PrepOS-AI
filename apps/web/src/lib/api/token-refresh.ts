import { authApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore } from "@/stores";

const AUTH_PATHS = new Set(["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"]);

let refreshPromise: Promise<string | null> | null = null;
let proactiveTimer: ReturnType<typeof setTimeout> | null = null;

export function isAuthPath(path: string): boolean {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return AUTH_PATHS.has(normalized);
}

export async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const { refreshToken, tenantSlug, setTokens, clear } = useAuthStore.getState();
    if (!refreshToken) {
      clear();
      return null;
    }

    try {
      const tokens = await authApi.refresh(refreshToken);
      setTokens(
        tokens.access_token,
        tokens.refresh_token,
        tenantSlug ?? "",
        tokens.expires_in,
      );
      scheduleProactiveRefresh(tokens.expires_in);
      return tokens.access_token;
    } catch (error) {
      if (error instanceof ApiError && error.isUnauthorized) {
        clear();
      }
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export function scheduleProactiveRefresh(expiresInSeconds: number): void {
  if (proactiveTimer) {
    clearTimeout(proactiveTimer);
    proactiveTimer = null;
  }

  if (expiresInSeconds <= 0) return;

  const refreshMs = Math.max((expiresInSeconds - 60) * 1000, 5_000);
  proactiveTimer = setTimeout(() => {
    void refreshAccessToken();
  }, refreshMs);
}

export function initProactiveRefreshFromStore(): void {
  const { tokenExpiresAt } = useAuthStore.getState();
  if (!tokenExpiresAt) return;
  const secondsLeft = Math.floor((tokenExpiresAt - Date.now()) / 1000);
  if (secondsLeft > 60) {
    scheduleProactiveRefresh(secondsLeft);
  } else if (secondsLeft > 0) {
    void refreshAccessToken();
  }
}
