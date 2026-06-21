import type { AppRole } from "@/lib/types/api";

const ROLES_COOKIE = "prepos-roles";
const AUTH_COOKIE = "prepos-authed";
const MAX_AGE_SECONDS = 60 * 60 * 24;

function writeCookie(name: string, value: string, maxAge: number): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; SameSite=Lax; max-age=${maxAge}`;
}

export function syncSessionCookies(roles: AppRole[]): void {
  writeCookie(ROLES_COOKIE, roles.join(","), MAX_AGE_SECONDS);
  writeCookie(AUTH_COOKIE, "1", MAX_AGE_SECONDS);
}

export function clearSessionCookies(): void {
  writeCookie(ROLES_COOKIE, "", 0);
  writeCookie(AUTH_COOKIE, "", 0);
}

export function readRolesFromCookie(cookieHeader: string | undefined): AppRole[] {
  if (!cookieHeader) return [];
  const match = cookieHeader
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${ROLES_COOKIE}=`));
  if (!match) return [];
  const raw = decodeURIComponent(match.slice(ROLES_COOKIE.length + 1));
  return raw
    .split(",")
    .filter(Boolean) as AppRole[];
}

export function isAuthedFromCookie(cookieHeader: string | undefined): boolean {
  if (!cookieHeader) return false;
  return cookieHeader
    .split(";")
    .map((part) => part.trim())
    .some((part) => part === `${AUTH_COOKIE}=1`);
}
